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
