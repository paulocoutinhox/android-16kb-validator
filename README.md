<p align="center">
    <a href="https://github.com/paulo-coutinho/android-16kb-validator" target="_blank" rel="noopener noreferrer">
        <img width="250" src="extras/images/logo.png" alt="Android 16KB Validator Logo">
    </a>
</p>

## About

Android 16KB Page Size Validator.

A Python tool to validate 16KB page size alignment compliance for Android native libraries (.so files) inside APK, AAB packages, or standalone .so files.

Starting with Android 15, devices can use a 16KB page size instead of the traditional 4KB. Native libraries must be properly aligned to work on these devices. This tool helps you verify if your app is ready for 16KB page size support.

## Background

Android devices traditionally use a 4KB memory page size, but newer devices with Android 15+ can use 16KB pages for better performance. For your app to run on these devices, all native libraries (`.so` files) in 64-bit architectures (`arm64-v8a` and `x86_64`) must have their LOAD segments aligned to at least 16KB (16384 bytes).

**Key Points:**
- Only **64-bit architectures** (`arm64-v8a` and `x86_64`) need 16KB alignment
- 32-bit architectures (`armeabi-v7a` and `x86`) continue to use 4KB pages
- Alignment must be a **power of 2** (4096, 16384, 65536, etc.)
- Modern build tools (AGP 8.3+, NDK r27+) handle this automatically

## Requirements

- Python 3.10 or higher
- `readelf` or `llvm-readelf` tool (usually available via binutils package)

### Installing readelf

**macOS:**
```bash
brew install binutils
# readelf will be at: /opt/homebrew/bin/readelf
# or: /opt/homebrew/Cellar/binutils/<version>/bin/readelf
```

**Linux:**
```bash
# Debian/Ubuntu
sudo apt-get install binutils

# Fedora/RHEL
sudo dnf install binutils

# Arch Linux
sudo pacman -S binutils
```

**Windows:**
```bash
# Using MSYS2
pacman -S mingw-w64-x86_64-binutils
```

## Installation

```bash
git clone https://github.com/paulo-coutinho/android-16kb-validator.git
cd android-16kb-validator
```

No external dependencies required! The tool uses only Python standard library.

## Usage

### Basic Syntax

```bash
python3 main.py --package <path-to-apk-aab-or-so> --readelf <path-to-readelf> --out <output-csv>
```

### Options

- `--package`: Path to `.apk`, `.aab`, or `.so` file to validate
- `--readelf`: Path to `readelf` or `llvm-readelf` executable
- `--out`: Output CSV file path (default: `align-readelf.csv`)

### Example 1: Validate an APK (Compliant)

```bash
python3 main.py --package com.apk --readelf /opt/homebrew/Cellar/binutils/2.45/bin/readelf --out out.csv
```

**Output:**
```
Summary (last LOAD per .so - 64-bit only):
- .../lib/arm64-v8a/libandroidx.graphics.path.so -> 16384 -> COMPLIANT (16384 bytes)
- .../lib/arm64-v8a/libc++_shared.so -> 16384 -> COMPLIANT (16384 bytes)
- .../lib/arm64-v8a/libdatastore_shared_counter.so -> 16384 -> COMPLIANT (16384 bytes)
- .../lib/arm64-v8a/libjniPdfium.so -> 16384 -> COMPLIANT (16384 bytes)
- .../lib/arm64-v8a/libmodpdfium.so -> 16384 -> COMPLIANT (16384 bytes)
- .../lib/arm64-v8a/libubook.so -> 16384 -> COMPLIANT (16384 bytes)
- .../lib/x86_64/libandroidx.graphics.path.so -> 16384 -> COMPLIANT (16384 bytes)
- .../lib/x86_64/libc++_shared.so -> 16384 -> COMPLIANT (16384 bytes)
- .../lib/x86_64/libdatastore_shared_counter.so -> 16384 -> COMPLIANT (16384 bytes)
- .../lib/x86_64/libjniPdfium.so -> 16384 -> COMPLIANT (16384 bytes)
- .../lib/x86_64/libmodpdfium.so -> 16384 -> COMPLIANT (16384 bytes)
- .../lib/x86_64/libubook.so -> 16384 -> COMPLIANT (16384 bytes)
csv: /path/to/out.csv
```

### Example 2: Validate an AAB (Non-Compliant)

```bash
python3 main.py --package sem.aab --readelf /opt/homebrew/Cellar/binutils/2.45/bin/readelf --out out.csv
```

**Output:**
```
Summary (last LOAD per .so - 64-bit only):
- .../base/lib/arm64-v8a/libc++_shared.so -> 4096 -> NOT COMPLIANT (4096 bytes)
- .../base/lib/arm64-v8a/libjniPdfium.so -> 4096 -> NOT COMPLIANT (4096 bytes)
- .../base/lib/arm64-v8a/libmodpdfium.so -> 4096 -> NOT COMPLIANT (4096 bytes)
- .../base/lib/arm64-v8a/libubook.so -> 4096 -> NOT COMPLIANT (4096 bytes)
- .../base/lib/x86_64/libc++_shared.so -> 4096 -> NOT COMPLIANT (4096 bytes)
- .../base/lib/x86_64/libjniPdfium.so -> 4096 -> NOT COMPLIANT (4096 bytes)
- .../base/lib/x86_64/libmodpdfium.so -> 4096 -> NOT COMPLIANT (4096 bytes)
- .../base/lib/x86_64/libubook.so -> 4096 -> NOT COMPLIANT (4096 bytes)
csv: /path/to/out.csv
```

### Example 3: Validate a Single .so File (Compliant)

```bash
python3 main.py --package com.so --readelf /opt/homebrew/Cellar/binutils/2.45/bin/readelf --out out.csv
```

**Output:**
```
Summary (last LOAD per .so - 64-bit only):
- /path/to/com.so -> 16384 -> COMPLIANT (16384 bytes)
csv: /path/to/out.csv
```

### Example 4: Validate a Single .so File (Non-Compliant)

```bash
python3 main.py --package sem.so --readelf /opt/homebrew/Cellar/binutils/2.45/bin/readelf --out out.csv
```

**Output:**
```
Summary (last LOAD per .so - 64-bit only):
- /path/to/sem.so -> 4096 -> NOT COMPLIANT (4096 bytes)
csv: /path/to/out.csv
```

### Example 5: Validate 32-bit Library

```bash
python3 main.py --package sem-armv7.so --readelf /opt/homebrew/Cellar/binutils/2.45/bin/readelf --out out.csv
```

**Output:**
```
Summary (last LOAD per .so - 64-bit only):
no 64-bit .so files found
csv: /path/to/out.csv
```

### Example 6: Invalid Alignment Detection

```bash
python3 main.py --package old-lib.aab --readelf /opt/homebrew/Cellar/binutils/2.45/bin/readelf --out out.csv
```

**Output:**
```
Summary (last LOAD per .so - 64-bit only):
- .../lib/arm64-v8a/libandroidx.graphics.path.so -> 40912 -> INVALID ALIGNMENT (40912 bytes - not a power of 2)
- .../lib/arm64-v8a/libc++_shared.so -> 1350696 -> INVALID ALIGNMENT (1350696 bytes - not a power of 2)
- .../lib/arm64-v8a/libdatastore_shared_counter.so -> 37928 -> INVALID ALIGNMENT (37928 bytes - not a power of 2)
csv: /path/to/out.csv
```

## Status Indicators

The tool uses color-coded output for easy visual identification:

| Status | Color | Meaning |
|--------|-------|---------|
| ✅ **COMPLIANT** | 🟢 Green | Alignment is ≥ 16KB and is a power of 2 |
| ❌ **NOT COMPLIANT** | 🔴 Red | Alignment is 4KB (valid but not 16KB ready) |
| ⚠️ **INVALID ALIGNMENT** | 🔴 Red | Alignment is not a power of 2 (corrupted or parsing error) |
| ❓ **UNKNOWN** | 🟡 Yellow | Could not determine alignment |

## CSV Output

The tool generates a detailed CSV file with the following columns:

| Column | Description |
|--------|-------------|
| `Filename` | Full path to the .so file |
| `LineText` | Raw LOAD segment line from readelf output |
| `Align` | Alignment value as string (hex or decimal) |
| `AlignInt` | Alignment value as integer |
| `Compliant` | Compliance status: `16kb`, `not-16kb`, `invalid`, or `unknown` |

## How to Fix Non-Compliant Libraries

If your validation shows non-compliant libraries, here are the recommended solutions:

### 1. Update Build Tools (Recommended)

Ensure you're using modern versions that automatically handle 16KB alignment:

```gradle
// build.gradle.kts or build.gradle
android {
    compileSdk = 35 // Android 15 or higher

    defaultConfig {
        minSdk = 21
        targetSdk = 35
    }
}

// Use Android Gradle Plugin 8.3.0 or higher
// settings.gradle.kts or settings.gradle
pluginManagement {
    plugins {
        id("com.android.application") version "8.7.0"
    }
}
```

### 2. Update NDK Version

Use NDK r27 or higher, which includes 16KB alignment support:

```gradle
android {
    ndkVersion = "27.0.12077973" // or higher
}
```

### 3. Manual CMake Configuration (if needed)

If using older tools, you can manually set alignment in CMakeLists.txt:

```cmake
# For arm64-v8a
if(ANDROID_ABI STREQUAL "arm64-v8a")
    set(CMAKE_SHARED_LINKER_FLAGS "${CMAKE_SHARED_LINKER_FLAGS} -Wl,-z,max-page-size=16384")
endif()

# For x86_64
if(ANDROID_ABI STREQUAL "x86_64")
    set(CMAKE_SHARED_LINKER_FLAGS "${CMAKE_SHARED_LINKER_FLAGS} -Wl,-z,max-page-size=16384")
endif()
```

### 4. Manual ndk-build Configuration

In `Android.mk`:

```makefile
ifeq ($(TARGET_ARCH_ABI),arm64-v8a)
    LOCAL_LDFLAGS += -Wl,-z,max-page-size=16384
endif

ifeq ($(TARGET_ARCH_ABI),x86_64)
    LOCAL_LDFLAGS += -Wl,-z,max-page-size=16384
endif
```

### 5. Third-Party Libraries

For third-party prebuilt `.so` files:
- Contact the library vendor for 16KB-aligned versions
- Rebuild from source with proper alignment flags
- Consider alternative libraries with 16KB support

## Architecture Detection

The tool automatically detects 64-bit architectures using two methods:

1. **Path-based detection**: Checks if the path contains `/arm64-v8a/` or `/x86_64/`
2. **ELF header analysis**: Falls back to parsing ELF headers for standalone `.so` files

Only 64-bit libraries are validated since 32-bit architectures don't require 16KB alignment.

## Troubleshooting

### "error: --readelf must point to an executable readelf/llvm-readelf"

Make sure the readelf path is correct and executable:

```bash
# Find readelf
which readelf

# Or on macOS with Homebrew
find /opt/homebrew -name readelf
```

### "no 64-bit .so files found"

This means:
- Your package only contains 32-bit libraries (armeabi-v7a, x86)
- No native libraries were found in the package
- The package might be corrupted

### Invalid Alignment Values

If you see alignment values that aren't powers of 2 (like 40912, 1350696):
- This could indicate a parsing issue
- Try using `llvm-readelf` instead of GNU `readelf`
- Check if the `.so` file is corrupted
- The file might have been built with non-standard tools

## References

- [Android 16KB Page Sizes](https://developer.android.com/guide/practices/page-sizes)
- [Support 16KB Page Sizes](https://developer.android.com/ndk/guides/16kb-page-sizes)
- [ELF Alignment](https://refspecs.linuxfoundation.org/elf/elf.pdf)

## License

[MIT](http://opensource.org/licenses/MIT)

Copyright (c) 2024-2025, Paulo Coutinho
