# RPi5 Secure AOSP Builder - Development Guide

This document describes the Docker-based workflow for building AOSP for Raspberry Pi 5.

## Quick Start

### Prerequisites

- Docker installed and running
- User added to `docker` group (or use `sudo`)
- At least 200GB free disk space

### Basic Usage

The `docker_run.sh` script is the primary entrypoint. It automatically manages the Docker container, verifying that the appropriate image is built (using the SHA256 of the Dockerfile), and routes everything inside appropriately.

By default, when `--config` is not provided, `docker_run.sh` now injects:
`--config config/rpi5_uboot_aosp.yaml`
so the standard flow includes U-Boot integration (boot script/config + U-Boot SD layout).

```bash
# 1. Sync sources (U-Boot + AOSP)
./docker_run.sh --stage sync

# 2. Apply patches (includes local U-Boot patch set)
./docker_run.sh --stage patch

# 3. Build everything
./docker_run.sh --stage build

# 4. Generate SD card image
./docker_run.sh --stage sdcard

# Or run all stages at once
./docker_run.sh --stage all

# To force plain AOSP (no U-Boot SD config), override config explicitly
./docker_run.sh --stage all --config config/rpi5_aosp.yaml
```

## Available Commands

```bash
# Interactive shell
./docker_run.sh --shell

# Sync operations
./docker_run.sh --stage sync              # Sync both U-Boot and AOSP
./docker_run.sh --stage sync --code uboot # Sync only U-Boot
./docker_run.sh --stage sync --code aosp  # Sync only AOSP

# Build operations
./docker_run.sh --stage build             # Build both U-Boot and AOSP
./docker_run.sh --stage build --code uboot# Build only U-Boot
./docker_run.sh --stage build --code aosp # Build only AOSP

# SD card image
./docker_run.sh --stage sdcard            # Generate bootable SD card image

# Tests (inside Docker; no host Python toolchain required)
./docker_run.sh --pytest                  # Run all repo tests under tests/
./docker_run.sh --pytest -q tests/test_main.py  # Run selected tests/options

# Complete workflow
./docker_run.sh --stage all               # Run sync + patch + build + sdcard

# Cleanup
rm -rf work/sdcard/*.img                  # Remove generated images
rm -rf work/                              # Remove entire workspace (WARNING: destructive)

# Advanced
# Any unhandled argument is evaluated by the Python application:
./docker_run.sh --help
./docker_run.sh --build-binary            # Build PyInstaller binary
```

## Configurable Build/Security Modes

The builder supports per-run overrides with this precedence:
`CLI option > config YAML value > built-in default`.

No-flag behavior keeps safe defaults (`userdebug`, `permissive`, no boot-state override, and config-driven signing).

```bash
# Build variant override (eng/userdebug/user)
./docker_run.sh --stage build --code aosp --build-variant user

# SELinux mode override in generated U-Boot boot script
./docker_run.sh --stage build --code uboot --selinux-mode enforcing

# Per-run signing override without editing config files
./docker_run.sh --stage sdcard --code aosp --signing enabled

# AVB policy and test boot state (requires explicit insecure opt-in for fail_open/orange)
./docker_run.sh --stage build --avb-fail-policy fail_open --allow-insecure-boot-state
./docker_run.sh --stage build --boot-state-override orange --allow-insecure-boot-state

# Optional cmdline profile toggle
./docker_run.sh --stage build --cmdline-profile production

# Encryption mode (disabled/fde/fbe); fbe requires signed + fail-closed AVB profile
./docker_run.sh --stage build --config config/rpi5_uboot_aosp_signed.yaml --encryption-mode fde
./docker_run.sh --stage build --config config/rpi5_uboot_aosp_signed.yaml --encryption-mode fbe
```

### FBE (File-Based Encryption)

`encryption.mode: fbe` enables Android File-Based Encryption on the `userdata` partition. Prerequisites:
- Signing must be enabled (`sdcard.enable_signing: true`)
- AVB fail policy must be `fail_closed`
- SD-card config must contain `userdata` and `metadata` partitions

When `fbe` is active, the pipeline passes `RPI5_ENABLE_FBE=true` to the AOSP build, which selects `fstab.rpi5.fbe` with `fileencryption=aes-256-xts:aes-256-cts:v2` and `keydirectory=/metadata/vold/metadata_encryption` on the `userdata` entry.

**First-boot note:** vold initialises FBE on the first boot after flashing. This takes several minutes while keys are generated and the `dm-default-key` device is set up over `userdata`. Do not power-cycle during this window. After completion, `getprop ro.crypto.type` returns `file` and `getprop ro.crypto.state` returns `encrypted`.

**Rollback:** Set `encryption.mode: disabled` in the config and reflash from a clean image. Once vold has encrypted `userdata`, reverting without a reflash is not possible.
```

## Recommended Config Profiles

Use explicit config profiles to avoid mixing secure and insecure settings:

- `config/rpi5_uboot_aosp.yaml` (insecure/dev profile)
  - `sdcard.enable_signing: false`
  - `aosp.build_variant: userdebug`
  - `boot.selinux_mode: permissive`
  - `boot.state_override: orange`
  - `avb.uboot_fail_policy: fail_open`
  - `boot.cmdline_profile: debug`
  - `encryption.mode: disabled`
- `config/rpi5_uboot_aosp_signed.yaml` (secure/prod profile)
  - `sdcard.enable_signing: true`
  - `aosp.build_variant: user`
  - `boot.selinux_mode: enforcing`
  - `boot.state_override: none`
  - `avb.uboot_fail_policy: fail_closed`
  - `boot.cmdline_profile: production`
  - `encryption.mode: fbe` (set to `disabled` to build without encryption)

Build commands:

```bash
# Insecure/dev
./docker_run.sh --stage all --config config/rpi5_uboot_aosp.yaml

# Secure/prod
./docker_run.sh --stage all --config config/rpi5_uboot_aosp_signed.yaml
```

## Environment Variables

The following environment variables are automatically set when running via `docker_run.sh`:

- `HOST_UID`: Your user ID (for file ownership)
- `HOST_GID`: Your group ID (for file ownership)
- `HOST_USER`: Your username
- `SUDO_USER`: Set to your username (for sudo operations)
- `XDG_CACHE_HOME`: Cache directory
- `GOPATH`: Go workspace
- `GOCACHE`: Go build cache

## Advanced Usage

### Compiling and passing custom tags

```bash
# Inside the container shell, you can:
./docker_run.sh --shell

cd /workspace
source .venv/bin/activate
python3 /opt/src/meta_rpi5_secure_aosp/main.py --help
```

### Building PyInstaller Binary

```bash
# Build standalone binary
./docker_run.sh --build-binary

# The binary will be in dist/rpi5-build
```

## Troubleshooting

### Container Already Running

```bash
# The script automatically cleans up, but if needed:
docker stop rpi_build
docker rm rpi_build
```

### Permission Issues

```bash
# The script passes your UID/GID to the container
# Files should be owned by your user
# If not, check that HOST_USER is set correctly
```

### Disk Space

```bash
# Check disk usage
df -h work/

# Clean up old builds
rm -rf work/sdcard/*.img

# Nuclear option (removes everything)
rm -rf work/
```

### Python Dependencies

```bash
# Recreate virtual environment
rm -rf work/.venv
./docker_run.sh --shell  # Will recreate venv automatically
```
