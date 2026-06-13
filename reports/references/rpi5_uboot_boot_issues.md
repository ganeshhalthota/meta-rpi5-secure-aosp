# RPi5 U-Boot Boot Issues (Splash Screen Hang) — Raspberry Pi Forums

- **URL:** https://forums.raspberrypi.com/viewtopic.php?t=387528
- **BibTeX key:** `rpi5_uboot_boot_issues`
- **Accessed:** October 2025

---

## Thread Overview

Users reported Raspberry Pi 5 hanging at the U-Boot splash screen (black screen with logo)
across multiple U-Boot versions: 2024.04, 2025.04, and master branch.

## Critical Fix

**Set `CONFIG_BOOTDELAY=-2`** in U-Boot configuration. This resolved the hang for multiple
users and allowed boot to progress past the splash screen.

## Workaround for Full Feature Support

Since mainline U-Boot lacked full RPi5 support at time of these posts:

- **Fork:** `https://github.com/xen-troops/u-boot/tree/rpi5-2024.04-xt`
- Provided Ethernet and networking support needed for TFTP boot

## Recommended Build Configuration

| Component | Config |
|-----------|--------|
| U-Boot defconfig | `bcm2711_defconfig` (not `bcm2712_defconfig` — caused kernel panics) |
| Linux kernel branch | 6.10 with `bcm2712_defconfig` |
| Kernel toolchain | 64-bit ARM (`aarch64-linux-gnu-`) |
| Rootfs toolchain | 32-bit (Busybox) |

## Status Notes

As of May 2025, full mainline RPi5 U-Boot support remained incomplete, with PCIe, USB, and
Ethernet initialisation pending in mainline versions.
