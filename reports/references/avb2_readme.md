# Android Verified Boot 2.0 — Official README (android16-release)

- **URL:** https://android.googlesource.com/platform/external/avb/+/android16-release/README.md
- **Publisher:** Android Open Source Project (Google)
- **BibTeX key:** `avb2_readme`
- **Accessed:** February 2026

---

## Overview

Official README for Android Verified Boot 2.0 (AVB). The system "assures the end user of
the integrity of the software running on a device."

## The VBMeta Structure

Central data structure: the **VBMeta struct**, which "contains a number of descriptors (and
other metadata) and all of this data is cryptographically signed."

Descriptors are used for:
- Image hashes (e.g. `boot`)
- Image hashtree metadata (e.g. `system`, `vendor`)
- Chained partitions

The `vbmeta` partition holds hashes for `boot` and root hash/salt for `system`/`vendor`.
The bootloader verifies these using the embedded public key in VBMeta.

## Rollback Protection

Prevents downgrading to older (potentially vulnerable) software versions using rollback
index counters stored in tamper-evident storage.

## A/B Support

Supports A/B device configurations for seamless OTA updates between two system partitions.

## Libraries and Tools

| Component | Purpose |
|-----------|---------|
| `libavb/` | Core verification library (portable across architectures) |
| `libavb_ab/` | A/B slot management for bootloaders |
| `libavb_atx/` | Android Things extension (public key validation) |
| `libavb_user/` | Userspace verification operations |
| `avbtool` | Python CLI for image manipulation |
| `boot_control/` | Boot slot control HAL |

## Build Integration Variables

| Variable | Purpose |
|----------|---------|
| `BOARD_AVB_ENABLE` | Activates verified boot |
| `BOARD_AVB_ALGORITHM` | Specifies signing algorithm |
| `BOARD_AVB_ROLLBACK_INDEX` | Sets anti-rollback counter |

## Device Integration Requirements

- Locked / unlocked mode support
- Tamper-evident storage for rollback indexes and verification state
- Named persistent values for rollback index storage
- Specific bootflow handling for recovery and dm-verity errors
