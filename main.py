#!/usr/bin/env python3
# validate 16kb alignment inside android apk/aab or a single .so by parsing readelf/llvm-readelf program headers

import argparse
import csv
import os
import re
import shutil
import subprocess
import sys
import tempfile
import zipfile
from pathlib import Path


def is_supported_input(path: Path) -> bool:
    return path.suffix.lower() in {".apk", ".aab", ".so"}


def extract_package(pkg: Path, dest: Path) -> None:
    with zipfile.ZipFile(pkg, "r") as z:
        z.extractall(dest)


def iter_so_files(root: Path):
    for p in root.rglob("*.so"):
        yield p


def run_cmd(cmd: list[str]) -> str:
    try:
        out = subprocess.check_output(cmd, stderr=subprocess.STDOUT)
        return out.decode("utf-8", errors="ignore")
    except subprocess.CalledProcessError as e:
        return e.output.decode("utf-8", errors="ignore")


def run_readelf(readelf_path: Path, so_path: Path) -> str:
    return run_cmd([str(readelf_path), "-lW", str(so_path)])


def readelf_header(readelf_path: Path, so_path: Path) -> str:
    return run_cmd([str(readelf_path), "-hW", str(so_path)])


def parse_load_aligns(text: str):
    lines = text.splitlines()
    has_table_header = any(("Type" in ln and "Align" in ln) for ln in lines)
    loads = []

    def last_num_token(s: str) -> str | None:
        toks = [t for t in re.split(r"\s+", s.strip()) if t]
        nums = [t for t in toks if re.fullmatch(r"(?:0x[0-9a-fA-F]+|\d+)", t)]
        return nums[-1] if nums else None

    i = 0
    while i < len(lines):
        ln = lines[i]
        if re.search(r"^\s*LOAD\b", ln):
            align_tok = None
            if has_table_header:
                align_tok = last_num_token(ln)
            if not align_tok:
                for j in range(1, 6):
                    if i + j >= len(lines):
                        break
                    nxt = lines[i + j]
                    m = re.search(r"Align(?:\s*[:=])?\s*(0x[0-9a-fA-F]+|\d+)", nxt)
                    if m:
                        align_tok = m.group(1)
                        break
                if not align_tok and i + 1 < len(lines):
                    align_tok = last_num_token(lines[i + 1])
            loads.append((ln, align_tok or ""))
        i += 1
    return loads


def align_to_int(align_token: str) -> int | None:
    if not align_token:
        return None
    try:
        return (
            int(align_token, 16)
            if align_token.lower().startswith("0x")
            else int(align_token)
        )
    except ValueError:
        return None


def is_power_of_2(n: int) -> bool:
    return n > 0 and (n & (n - 1)) == 0


def detect_64bit_arch_from_path(path: str) -> bool:
    return "/arm64-v8a/" in path or "/x86_64/" in path


def detect_64bit_arch_from_header(header_text: str) -> bool:
    # checks elf class and machine
    cls = None
    mach = None
    for ln in header_text.splitlines():
        if "Class:" in ln:
            cls = ln.split(":", 1)[1].strip()
        if "Machine:" in ln:
            mach = ln.split(":", 1)[1].strip()
    if cls and "ELF64" not in cls:
        return False
    if not mach:
        return "ELF64" in (cls or "")
    m = mach.lower()
    return (
        ("aarch64" in m)
        or ("x86-64" in m)
        or ("amd x86-64" in m)
        or ("advanced micro devices x86-64" in m)
    )


def main():
    parser = argparse.ArgumentParser(
        description="validate 16kb alignment compliance inside apk/aab or a single .so"
    )
    parser.add_argument("--package", required=True, help="path to .apk, .aab, or .so")
    parser.add_argument(
        "--readelf", required=True, help="path to readelf or llvm-readelf executable"
    )
    parser.add_argument("--out", default="align-readelf.csv", help="csv output path")
    args = parser.parse_args()

    pkg = Path(args.package).resolve()
    readelf = Path(args.readelf).resolve()
    out_csv = Path(args.out).resolve()

    if not pkg.exists() or not is_supported_input(pkg):
        print(
            "error: --package must point to an existing .apk, .aab, or .so",
            file=sys.stderr,
        )
        sys.exit(1)
    if not readelf.exists() or not os.access(readelf, os.X_OK):
        print(
            "error: --readelf must point to an executable readelf/llvm-readelf",
            file=sys.stderr,
        )
        sys.exit(1)

    tmpdir = None
    so_paths: list[Path] = []
    try:
        if pkg.suffix.lower() in (".apk", ".aab"):
            tmpdir = Path(tempfile.mkdtemp(prefix="apk_aab_align_"))
            extract_package(pkg, tmpdir)
            so_paths = list(iter_so_files(tmpdir))
        else:
            so_paths = [pkg]

        rows = []
        last_align_per_so: dict[str, int | None] = {}
        arch64_map: dict[str, bool] = {}

        for so in so_paths:
            txt = run_readelf(readelf, so)
            parsed = parse_load_aligns(txt)

            # arch detection: prefer folder hint; fallback to elf header
            is64 = detect_64bit_arch_from_path(str(so))
            if not is64:
                hdr = readelf_header(readelf, so)
                is64 = detect_64bit_arch_from_header(hdr)
            arch64_map[str(so)] = is64

            for line_text, align_tok in parsed:
                ai = align_to_int(align_tok)
                rows.append(
                    {
                        "Filename": str(so),
                        "LineText": line_text.strip(),
                        "Align": align_tok,
                        "AlignInt": ai if ai is not None else "",
                    }
                )
            if parsed:
                _, last_tok = parsed[-1]
                last_align_per_so[str(so)] = align_to_int(last_tok)

        with out_csv.open("w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(
                f, fieldnames=["Filename", "LineText", "Align", "AlignInt", "Compliant"]
            )
            writer.writeheader()
            for r in rows:
                ai = r["AlignInt"] if isinstance(r["AlignInt"], int) else None
                compliant = "unknown"
                if ai is not None:
                    if is_power_of_2(ai) and ai >= 16384:
                        compliant = "16kb"
                    elif is_power_of_2(ai) and ai >= 4096:
                        compliant = "not-16kb"
                    else:
                        compliant = "invalid"
                writer.writerow(
                    {
                        "Filename": r["Filename"],
                        "LineText": r["LineText"],
                        "Align": r["Align"],
                        "AlignInt": r["AlignInt"],
                        "Compliant": compliant,
                    }
                )

        print("Summary (last LOAD per .so - 64-bit only):")
        GREEN = "\033[92m"
        RED = "\033[91m"
        YELLOW = "\033[93m"
        RESET = "\033[0m"

        any_so_64 = False
        for so_path, ai in sorted(last_align_per_so.items()):
            if not arch64_map.get(so_path, False):
                continue
            any_so_64 = True
            if ai is None:
                status = "UNKNOWN"
                color = YELLOW
            elif not is_power_of_2(ai):
                status = f"INVALID ALIGNMENT ({ai} bytes - not a power of 2)"
                color = RED
            elif ai >= 16384:
                status = f"COMPLIANT ({ai} bytes)"
                color = GREEN
            elif ai >= 4096:
                status = f"NOT COMPLIANT ({ai} bytes)"
                color = RED
            else:
                status = f"INVALID ALIGNMENT ({ai} bytes)"
                color = RED
            print(
                f'- {so_path} -> {ai if ai is not None else "?"} -> {color}{status}{RESET}'
            )
        if not any_so_64:
            print("no 64-bit .so files found")

        print(f"csv: {out_csv}")
    finally:
        if tmpdir:
            shutil.rmtree(tmpdir, ignore_errors=True)


if __name__ == "__main__":
    main()
