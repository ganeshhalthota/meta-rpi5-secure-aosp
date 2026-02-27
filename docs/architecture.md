# Architecture Documentation

## Introduction

This document describes the architecture of the `meta-rpi5-secure-aosp` project. This project provides a tool called `rpi5-build` to build a secure AOSP (Android Open Source Project) image for the Raspberry Pi 5. The tool is designed to be flexible and allows users to select which parts of the image to build and which stages to run.

## Motivation

The main motivation for this project is to provide a simple and automated way to build a secure AOSP image for the Raspberry Pi 5. Building AOSP for a new device can be a complex and time-consuming process. This project aims to simplify this process by providing a single tool that automates all the necessary steps, from syncing the source code to generating the final SD card image. The "secure" aspect comes from the integration of Android Verified Boot (AVB), which ensures the integrity of the software on the device.

## Design

The project is designed as a command-line tool that orchestrates a series of stages to produce a final SD card image. The design is modular, allowing for future extensions and modifications.

### High-Level Design (HLD)

The `rpi5-build` tool operates in several distinct stages. The user can choose to run all stages sequentially or run a specific stage. The following diagram illustrates the high-level workflow:

```mermaid
graph TD
    A[Start] --> B{Stage Selection};
    B --> C[Sync];
    C --> D[Patch];
    D --> E[Build];
    E --> F[Sign];
    F --> G[SD Card Image];
    G --> H[End];

    subgraph "Stages"
        C
        D
        E
        F
        G
    end
```

- **Sync:** Synchronises the source code for U-Boot and AOSP from their respective repositories.
- **Patch:** Applies git patch files (`.patch`) to the U-Boot and/or AOSP source trees. Patches are stored under `patches/uboot/` and `patches/aosp/<project>/` and applied with `git am --3way`.
- **Build:** Compiles the U-Boot and AOSP source code to produce boot, system, and vendor images.
- **Sign:** Signs the generated images using Android Verified Boot (AVB) to ensure their integrity.
- **SD Card Image:** Generates a bootable SD card image containing all the necessary partitions and images.

### Low-Level Design (LLD)

#### Package Structure

```text
src/meta_rpi5_secure_aosp/
├── main.py          # CLI entry point and pipeline orchestration
├── context.py       # BuildContext dataclass — shared state for all stages
├── stages/          # One module per pipeline stage
│   ├── __init__.py
│   ├── sync.py      # Stage: clone / repo-sync source trees
│   ├── patch.py     # Stage: apply git patches to uboot and/or aosp
│   ├── build.py     # Stage: compile uboot and/or aosp
│   ├── sign.py      # Stage: AVB-sign partition images
│   └── sdcard.py    # Stage: assemble the SD-card image
└── utils/           # Reusable utilities with no pipeline knowledge
    ├── __init__.py
    ├── avb.py        # AvbTool — wraps avbtool commands
    └── disk_image.py # DiskImage — low-level disk image construction
```

#### Module Responsibilities

- **`main.py`**: Defines the `click` CLI, resolves which stages and code targets are active, constructs a `BuildContext`, and calls each stage module in order:
  ```
  sync → patch → build → sign → sdcard
  ```

- **`context.py`**: Defines the `BuildContext` dataclass that carries all shared state (workspace paths, flags, the shell-runner callable, the Rich console) and is passed to every stage `run()` function.

- **`stages/sync.py`**: Clones or updates the U-Boot git repository and initialises / syncs the AOSP repo manifest.

- **`stages/patch.py`**: Discovers `.patch` files under `patches/uboot/` and `patches/aosp/<project>/`, dry-runs each with `git apply --check`, then applies them with `git am --3way`.

- **`stages/build.py`**: Cross-compiles U-Boot for `rpi_arm64_defconfig` and builds the AOSP `aosp_rpi5_car` lunch target.

- **`stages/sign.py`**: Uses `AvbTool` to add AVB hash footers to each partition image, append vbmeta sidecars, and produce a combined `vbmeta.img`.

- **`stages/sdcard.py`**: Resolves signed vs. unsigned image paths and delegates to `DiskImage` to assemble the final SD card image.

- **`utils/avb.py`** (`AvbTool`): Wraps `avbtool` invocations (`add_hash_footer`, `append_vbmeta_image`, `make_vbmeta_image`). Locates the binary from the AOSP build output or `$PATH`.

- **`utils/disk_image.py`** (`DiskImage`): Handles all low-level disk image mechanics — allocating the image file, partitioning with `parted`, loop-mounting with `losetup`/`kpartx`, copying images with `dd`, creating filesystems, copying extra files, and cleanup.

#### Stage Interaction Diagram

```mermaid
graph LR
    main["main.py\n(CLI + orchestration)"] --> ctx["BuildContext\n(context.py)"]
    ctx --> sync["stages/sync.py"]
    ctx --> patch["stages/patch.py"]
    ctx --> build["stages/build.py"]
    ctx --> sign["stages/sign.py"]
    ctx --> sdcard["stages/sdcard.py"]
    sign --> avb["utils/avb.py\nAvbTool"]
    sdcard --> di["utils/disk_image.py\nDiskImage"]
```

#### SD Card Image Creation

```mermaid
graph TD
    A[Start Image Creation] --> B[Create Empty Image File];
    B --> C[Create Partition Table];
    C --> D{Loop Over Partitions};
    D --> E[Create Partition];
    E --> F{Image Available?};
    F -- Yes --> G[Copy Image to Partition via dd];
    F -- No --> H[Create Filesystem];
    G --> I[Next Partition];
    H --> I;
    I --> D;
    D -- Done --> J[Map Loop Device];
    J --> K[Copy Extra Files];
    K --> L[Cleanup Loop Device];
    L --> M[End Image Creation];
```

#### Patch Directory Layout

```text
patches/
├── uboot/                        # Patches applied to u-boot/
│   ├── 0001-some-fix.patch
│   └── 0002-another-fix.patch
└── aosp/                         # Patches applied to rpi5-aosp/
    ├── device_brcm_rpi5/         # Subdirectory name = project path in rpi5-aosp/
    │   └── 0001-car-config.patch
    └── kernel_rpi/
        └── 0001-driver-fix.patch
```

Patches within each directory are applied in alphabetical order using `git am --3way`.

### Container & Workspace Architecture

#### File Structure

```text
.
├── scripts/
│   ├── docker_run.sh         # Main Docker wrapper script & entrypoint
│   ├── run_src.sh            # Container entrypoint for Python builder
│   └── flash_sdcard.sh       # Helper to flash the generated image to an SD card
├── patches/                  # Git patch files for uboot and aosp
│   ├── uboot/
│   └── aosp/
├── src/
│   └── meta_rpi5_secure_aosp/
│       ├── main.py           # CLI entry point
│       ├── context.py        # BuildContext dataclass
│       ├── stages/           # Pipeline stage modules
│       └── utils/            # Reusable utility modules
└── work/                     # Workspace (mounted in container)
    ├── .venv/                # Python virtual environment
    ├── .cache/               # Build caches
    ├── u-boot/               # U-Boot source
    ├── rpi5-aosp/            # AOSP source
    └── sdcard/               # Generated images
```

#### How It Works

1. **`scripts/docker_run.sh`**:
   - Computes the SHA256 hash of the Dockerfile.
   - Checks if an image with `rpi5-<sha256>` exists. If not, it builds it.
   - Cleans up any existing containers running for the workspace.
   - Creates a new container with proper mounts and privileges.
   - Sets up Python virtual environment if it doesn't already exist.
   - Executes the Python app through `scripts/run_src.sh` or starts an interactive shell.
   - Automatically cleans up on exit.

2. **`scripts/run_src.sh`**:
   - Sets up environment variables.
   - Activates Python virtual environment.
   - Executes the Python builder with arguments.

3. **`scripts/flash_sdcard.sh`**:
   - Helper script to flash the generated SD card image to a physical SD card device.
