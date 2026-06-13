# Download and Build Trusty TEE for Android

- **URL:** https://source.android.com/docs/security/features/trusty/download-and-build
- **Publisher:** Android Open Source Project (Google)
- **BibTeX key:** `trusty_download_build`
- **Accessed:** February 2026

---

## Overview

Guide for downloading, building, and testing the Trusty Trusted Execution Environment (TEE)
hosted in AOSP.

## Kernel Branches

| Branch | Trusty Version |
|--------|---------------|
| `android-trusty-4.4` | Kernel 4.4 |
| `android-trusty-4.9` | Kernel 4.9 |
| `android-trusty-4.14` | Kernel 4.14 |

## Build: Generic ARM64 Image

```bash
mkdir trusty
# (repo init + sync steps)
./trusty/vendor/google/aosp/scripts/build.py generic-arm64
```

Build artifacts in `build-root/build-generic-arm64/`.
Primary output: `lk.bin` — TEE image with all compiled applications.

## Build: QEMU (for testing)

### Prerequisites
```bash
sudo apt install libpixman-1-dev libstdc++-8-dev pkg-config libglib2.0-dev libusb-1.0-0-dev
```

### Build
```bash
trusty/vendor/google/aosp/scripts/build.py qemu-generic-arm64-test-debug
```

### Run Tests
```bash
# Port activation test
build-root/build-qemu-generic-arm64-test-debug/run \
  --headless --boot-test "com.android.ipc-unittest.ctrl"

# With kernel debug output
build-root/build-qemu-generic-arm64-test-debug/run-qemu \
  --boot-test "com.android.ipc-unittest.ctrl" --headless --verbose
```

## Build Android for Trusty

```bash
mkdir android && cd android
repo init -u https://android.googlesource.com/platform/manifest -b main
repo sync -j32
source build/envsetup.sh
lunch qemu_trusty_arm64-userdebug
m
```

## Installation

`lk.bin` must be assembled into a firmware image and flashed per board-specific documentation.
