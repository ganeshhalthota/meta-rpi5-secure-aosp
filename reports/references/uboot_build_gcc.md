# U-Boot: Building with GCC — Official Documentation

- **URL:** https://docs.u-boot.org/en/latest/build/gcc.html
- **Publisher:** U-Boot Project (docs.u-boot.org)
- **BibTeX key:** `uboot_build_gcc`
- **Accessed:** October 2025

---

## Overview

Official guide for compiling U-Boot using GCC. Covers dependency installation, board
configuration, and cross-compilation procedures across Linux distributions.

## Dependencies

### Debian/Ubuntu
```bash
sudo apt-get install gcc gcc-aarch64-linux-gnu
sudo apt-get install bc bison build-essential coccinelle device-tree-compiler \
  dfu-util efitools flex gdisk graphviz imagemagick libgnutls28-dev \
  libguestfs-tools libncurses-dev libpython3-dev libsdl2-dev libssl-dev \
  lz4 lzma lzma-alone openssl pkg-config python3 python3-asteval \
  python3-coverage python3-filelock python3-pkg-resources \
  python3-pycryptodome python3-pyelftools python3-pytest \
  python3-pytest-xdist python3-sphinxcontrib.apidoc \
  python3-sphinx-rtd-theme python3-subunit python3-testtools \
  python3-venv swig uuid-dev
```

### SUSE
```bash
sudo zypper install gcc cross-aarch64-gcc10
zypper install bc bison flex gcc libopenssl-devel libSDL2-devel make \
  ncurses-devel python3-devel python3-pytest swig
```

### Alpine Linux
```bash
apk add alpine-sdk bc bison dtc flex gnutls-dev linux-headers ncurses-dev \
  openssl-dev py3-elftools py3-setuptools python3-dev swig util-linux-dev
```

## Configuration

Board configuration files follow the naming pattern `<board>_defconfig`:
```bash
make odroid-c2_defconfig
make menuconfig   # interactive adjustment
```

## Building

### Cross-compilation (AArch64)
```bash
CROSS_COMPILE=aarch64-linux-gnu- make -j$(nproc)
```

### Out-of-tree build
```bash
make O=/tmp/build distclean
make O=/tmp/build <board>_defconfig
make O=/tmp/build
```

### Devicetree compiler
```bash
DTC=/usr/bin/dtc make
```

### Useful flags
| Flag | Effect |
|------|--------|
| `O=<dir>` | Output directory for generated files |
| `V=1` | Verbose build output |
| `NO_LTO=1` | Disable link-time optimisation for faster builds |

## Common Targets
- `clean` — removes generated files, keeps configuration
- `mrproper` — removes all generated files and configuration
