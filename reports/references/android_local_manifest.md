# Android Local Manifest for Raspberry Pi (AOSP 16)

- **URL:** https://github.com/ganeshhalthota/android_local_manifest
- **Author:** ganeshhalthota
- **BibTeX key:** `android_local_manifest`
- **Accessed:** October 2025

---

## Overview

Device-specific configuration repository for building AOSP Android 16 on Raspberry Pi 4 and
Raspberry Pi 5. Forked from the raspberry-vanilla organisation.

## Key Files

| File | Purpose |
|------|---------|
| `manifest_brcm_rpi.xml` | Device-specific manifest |
| `manifest_utilities.xml` | Utility components manifest |
| `remove_projects.xml` | Projects excluded from build |
| `README.md` | Build instructions |

## Build Requirements

- Ubuntu 22.04 LTS
- Additional packages: `dosfstools e2fsprogs fdisk kpartx mtools rsync`

## Build Process

1. Establish Android build environment
2. Install required packages
3. Init repo with Android 16.0.0_r4 source
4. Sync source (`--depth=1` optional for shallow clone)
5. Configure build environment (`source build/envsetup.sh`)
6. Select device (`rpi4` or `rpi5`) and UI variant (tablet / TV / Automotive)
7. Compile `bootimage`, `systemimage`, `vendorimage`
8. Generate flashable image using platform script

## Supported Build Targets

- Raspberry Pi 4 and Raspberry Pi 5
- Tablet UI, Android TV, Android Automotive
