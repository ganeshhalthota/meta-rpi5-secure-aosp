# AOSP Build Requirements

- **URL:** https://source.android.com/docs/setup/start/requirements
- **Publisher:** Android Open Source Project (Google)
- **BibTeX key:** `aosp_requirements`
- **Accessed:** October 2025

---

## Overview

Prerequisites for developing AOSP versions 9.0 and later. macOS is no longer supported
for Android OS development (deprecated June 22, 2021).

## Hardware Requirements

| Resource | Minimum |
|----------|---------|
| Architecture | 64-bit x86 |
| Storage | 400 GB free (250 GB checkout + 150 GB build) |
| RAM | 64 GB (Google uses 72-core / 64 GB machines; ~40 min full build) |

## OS Requirements

- Any 64-bit Linux distribution with glibc 2.17+
- Ubuntu 18.04+ required for Android 11 and higher

## Required Packages

```bash
sudo apt-get install git-core gnupg flex bison build-essential zip curl zlib1g-dev \
  libc6-dev-i386 x11proto-core-dev libx11-dev lib32z1-dev libgl1-mesa-dev \
  libxml2-utils xsltproc unzip fontconfig
```

## Repo Tool

The latest Android release includes prebuilt OpenJDK, Make, and Python 3.

```bash
sudo apt-get update
sudo apt-get install repo
repo version   # should be 2.4 or higher
```

## Key Terminology

| Term | Meaning |
|------|---------|
| Git | Version control for local operations |
| Repo | Python wrapper around Git for multi-repo management |
| Manifest | XML file specifying Git project locations within AOSP |

## Output Directory

Override the default `out/` directory with the `OUT_DIR` environment variable.
