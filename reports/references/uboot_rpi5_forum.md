# U-Boot for Raspberry Pi 5 — Raspberry Pi Forums

- **URL:** https://forums.raspberrypi.com/viewtopic.php?t=369150
- **Thread started:** April 16, 2024 (AlenHazard)
- **BibTeX key:** `uboot_rpi5_forum`
- **Accessed:** October 2025

---

## Overview

Forum thread discussing availability and implementation of U-Boot bootloader support for the
Raspberry Pi 5, spanning April 2024 to February 2025.

## Key Findings

### Release Status

Initial U-Boot support for Raspberry Pi 5 was integrated into the official U-Boot codebase on
January 23, 2024. Version v2024.04 contains these patches. Support remains incomplete.

### Limitations in Early Versions

- No USB boot capability
- No NVMe boot support
- No network/Ethernet support
- Incomplete PCIe driver support

> "basic support these integrated patches (and thus v2024.04) doesn't e.g. allow to boot from
> USB or NVMe due to missing driver support in U-Boot."

### Debug Interface / Serial Console

Standard GPIO serial ports (14 & 15) require the PCIe bus to be online. Debug output requires
the dedicated 3-pin debug connector between the HDMI ports (earlycon).
This is relevant context for the `arm,pl011-axi` compatible string patch: U-Boot must bind
`serial10` (the `stdout-path` target in the firmware DT) to get any console output.

### Hardware Variants

16 GB and 2 GB RAM variants of RPi5 may require specific device tree files (`d0` dts files)
to function correctly with U-Boot.

### Development Status

PCIe support for the RP1 interface circuit is the blocking issue for full peripheral support.
Pending Linux kernel patch series (v4 → v5) must be accepted upstream before U-Boot can
implement USB/NVMe boot.
