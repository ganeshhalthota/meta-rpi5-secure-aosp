# Build SELinux Policy — Precompiled Policy

- **URL:** https://source.android.com/docs/security/features/selinux/build#precompiled-policy
- **Publisher:** Android Open Source Project (Google)
- **BibTeX key:** `selinux_build_precompiled`
- **Accessed:** January 2026

---

## Overview

Describes how Android's SELinux policy is built and split between platform and vendor, with
a focus on precompiled policy loading to reduce boot time.

## Architecture (Android 8.0+)

Policy splits into components built independently:

| Location | Content |
|----------|---------|
| `system/sepolicy/public` | Platform sepolicy API (stable, versioned) |
| `system/sepolicy/private` | Platform-only (vendor-invisible) |
| `BOARD_SEPOLICY_DIRS` | Vendor sepolicy |
| `BOARD_ODM_SEPOLICY_DIRS` | ODM sepolicy (Android 9+) |
| `SYSTEM_EXT_PUBLIC_SEPOLICY_DIRS` | system_ext API (Android 11+) |
| `PRODUCT_PUBLIC_SEPOLICY_DIRS` | Product API (Android 11+) |

## Build Steps (Android 8.0+)

1. Convert policies to SELinux Common Intermediate Language (CIL)
2. Version public policy as part of vendor policy
3. Create mapping files linking platform and vendor components
4. Combine mapping, platform, and vendor policy; compile to binary

## Precompiled Policy

Before `init` enables SELinux, it compiles CIL files from all partitions — typically 1–2 seconds.

To optimise, CIL files are precompiled at build time and stored at:
- `/vendor/etc/selinux/precompiled_sepolicy`
- `/odm/etc/selinux/precompiled_sepolicy`

Along with SHA256 hashes of input files.

### Runtime Loading Logic

At boot, `init` compares SHA256 hashes of current input files against stored hashes:
- **Match**: loads precompiled policy (fast path)
- **Mismatch**: compiles on-device, uses result (fallback)

All conditions must be met for precompiled policy:
- Platform SHA256 hashes match between system and partition
- `system_ext` hashes either absent on both or match
- `product` hashes either absent on both or match

Implementation: `system/core/init/selinux.cpp`

## Android 7.x (Legacy)

Device customisation via `BOARD_SEPOLICY_DIRS`. All policy fragments merged into monolithic
files in root directory. Required rebuilding `boot.img` or `system.img` for any policy change.

## Source Files

| Path | Purpose |
|------|---------|
| `external/selinux` | Host utilities: `libselinux`, `libsepol`, `checkpolicy` |
| `system/sepolicy` | Core Android SELinux configs, contexts, build logic |
