# AVBTOOL — Android Verified Boot Tool (GitHub Mirror)

- **URL:** https://github.com/jcrutchvt10/AVBTOOL
- **Author:** jcrutchvt10 (GitHub mirror of AOSP `platform/external/avb`)
- **Language:** C (42.1%), C++ (37.0%), Python (19.1%)
- **License:** MIT
- **BibTeX key:** `avbtool_github`
- **Accessed:** February 2026

---

## Overview

Mirror/fork of the Android Verified Boot 2.0 (AVB) tools repository. Contains `avbtool`,
`libavb`, and related components for verified boot image manipulation.

## Key Components

| Path | Purpose |
|------|---------|
| `libavb/` | Core verification library (portable) |
| `libavb_ab/` | A/B slot management for bootloaders |
| `libavb_atx/` | Android Things public key validation extension |
| `libavb_user/` | Userspace verification operations |
| `avbtool` | Python CLI for image manipulation |
| `boot_control/` | Boot slot control HAL implementation |

## `avbtool` Key Operations

- Generate `vbmeta.img` with specified algorithm and signing key
- Add hash footer to partition images (`boot`, `dtbo`)
- Create hashtree structures with optional Forward Error Correction (FEC)
- Manage A/B slot metadata in `misc` partition
- Verify signed images

## Build Integration

| Variable | Purpose |
|----------|---------|
| `BOARD_AVB_ENABLE` | Activates verified boot in AOSP build |
| `BOARD_AVB_ALGORITHM` | Signing algorithm (e.g. `SHA256_RSA4096`) |
| `BOARD_AVB_ROLLBACK_INDEX` | Anti-rollback counter |

## Relevance

Used as a reference and tool during AVB signing integration. For authoritative source see
the canonical AOSP repository:
`https://android.googlesource.com/platform/external/avb/`
