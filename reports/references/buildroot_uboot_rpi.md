# Buildroot and U-Boot on Raspberry Pi

- **URL:** https://casan.se/blog/linux/buildroot-and-u-boot-on-raspberry-pi/
- **Publisher:** casan.se (personal/technical blog)
- **BibTeX key:** `buildroot_uboot_rpi`
- **Accessed:** October 2025

---

## Overview

Guide demonstrating Buildroot with U-Boot on Raspberry Pi 4, enabling kernel loading through
U-Boot without repeatedly flashing the SD card. Consolidates information from multiple
incomplete sources.

**Prerequisites:** Serial console connection, TFTP server (for network boot)

## Building the Image

```bash
git clone https://github.com/buildroot/buildroot.git
cd buildroot
make raspberrypi4_64_defconfig
make menuconfig
```

Key menuconfig settings:
- Enable U-Boot under "Bootloaders"
- Set U-Boot board defconfig to `rpi_4` (without `_defconfig` suffix)

Config file changes:
- `board/raspberrypi/config_4_64bit.txt`: change `kernel=Image` → `kernel=u-boot.bin`
- `board/raspberrypi/post-image.sh`: add `FILES+=( "Image" )`

```bash
make
```

Flash: `dd` the resulting `output/images/sdcard.img` to SD card.

## U-Boot Boot Commands

### SD card boot
```bash
fatload mmc 0 ${kernel_addr_r} Image
booti ${kernel_addr_r} - ${fdt_addr}
```

### Network (TFTP) boot
```bash
setenv serverip '10.0.0.1'
setenv ipaddr '10.0.0.101'
tftp ${kernel_addr_r} Image
booti ${kernel_addr_r} - ${fdt_addr}
```

### Automate boot selection
```bash
setenv netboot 'dhcp ${kernel_addr_r} ${netboot_filename}; booti ${kernel_addr_r} - ${fdt_addr}'
setenv sdboot 'fatload mmc 0 ${kernel_addr_r} Image; booti ${kernel_addr_r} - ${fdt_addr}'
setenv bootcmd 'run sdboot'
saveenv
```
