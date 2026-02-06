# RPi5 Secure AOSP Builder - Docker Workflow

This document describes the improved Docker-based workflow for building AOSP for Raspberry Pi 5.

## Quick Start

### Prerequisites

- Docker installed and running
- User added to `docker` group (or use `sudo`)
- At least 200GB free disk space

### Basic Usage

```bash
# 1. Sync sources (U-Boot + AOSP)
make sync

# 2. Build everything
make build

# 3. Generate SD card image
make sdcard

# Or run all stages at once
make all
```

## Available Commands

### Using Makefile

```bash
# Interactive shell
make shell

# Sync operations
make sync              # Sync both U-Boot and AOSP
make sync-uboot        # Sync only U-Boot
make sync-aosp         # Sync only AOSP

# Build operations
make build             # Build both U-Boot and AOSP
make build-uboot       # Build only U-Boot
make build-aosp        # Build only AOSP

# SD card image
make sdcard            # Generate bootable SD card image

# Complete workflow
make all               # Run sync + build + sdcard

# Cleanup
make clean             # Remove generated images
make clean-all         # Remove entire workspace (WARNING: destructive)

# Advanced
make run CMD='ls -la'  # Run custom command in container
make binary            # Build PyInstaller binary
```

### Using Scripts Directly

```bash
# Interactive shell
./docker_run_improved.sh --shell

# Run specific stages
./docker_run_improved.sh /opt/run_src_improved.sh --stage sync
./docker_run_improved.sh /opt/run_src_improved.sh --stage build
./docker_run_improved.sh /opt/run_src_improved.sh --stage sdcard

# Run with specific code selection
./docker_run_improved.sh /opt/run_src_improved.sh --stage sync --code aosp
./docker_run_improved.sh /opt/run_src_improved.sh --stage build --code uboot

# Run custom commands
./docker_run_improved.sh python3 --version
./docker_run_improved.sh ls -la /workspace
```

## Architecture

### File Structure

```
.
├── docker_run_improved.sh    # Main Docker wrapper script
├── run_src_improved.sh       # Container entrypoint for Python builder
├── Makefile                  # Convenient make targets
├── src/
│   └── meta_rpi5_secure_aosp/
│       ├── main.py           # Python builder
│       └── image_builder.py  # SD card image builder
└── work/                     # Workspace (mounted in container)
    ├── .venv/                # Python virtual environment
    ├── .cache/               # Build caches
    ├── u-boot/               # U-Boot source
    ├── rpi5-aosp/            # AOSP source
    └── sdcard/               # Generated images
```

### How It Works

1. **docker_run.sh**:
   - Cleans up any existing containers
   - Creates new container with proper mounts and privileges
   - Sets up Python virtual environment
   - Executes command or starts interactive shell
   - Automatically cleans up on exit

2. **run_src.sh**:
   - Sets up environment variables
   - Activates Python virtual environment
   - Executes the Python builder with arguments

3. **Makefile**:
   - Provides convenient shortcuts
   - Wraps docker_run.sh calls
   - Makes common operations simple

## Environment Variables

The following environment variables are automatically set:

- `HOST_UID`: Your user ID (for file ownership)
- `HOST_GID`: Your group ID (for file ownership)
- `HOST_USER`: Your username
- `SUDO_USER`: Set to your username (for sudo operations)
- `XDG_CACHE_HOME`: Cache directory
- `GOPATH`: Go workspace
- `GOCACHE`: Go build cache

## Advanced Usage

### Custom Commands

```bash
# Run any command in the container
make run CMD='bash -c "cd /workspace && ls -la"'

# Or using the script directly
./docker_run_improved.sh bash -c "cd /workspace && ls -la"
```

### Debugging

```bash
# Start interactive shell
make shell

# Inside the shell, you can:
cd /workspace
source .venv/bin/activate
python3 /opt/src/meta_rpi5_secure_aosp/main.py --help
```

### Building PyInstaller Binary

```bash
# Build standalone binary
make binary

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
make clean

# Nuclear option (removes everything)
make clean-all
```

### Python Dependencies

```bash
# Recreate virtual environment
rm -rf work/.venv
make shell  # Will recreate venv automatically
```
