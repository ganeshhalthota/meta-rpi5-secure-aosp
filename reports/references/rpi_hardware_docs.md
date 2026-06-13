# Raspberry Pi Hardware Documentation

- **URL:** https://www.raspberrypi.com/documentation/computers/raspberry-pi.html
- **Publisher:** Raspberry Pi Ltd
- **BibTeX key:** `rpi_hardware_docs`
- **Accessed:** October 2025

---

## Overview

Official documentation covering the complete Raspberry Pi product lineup: SBCs, keyboard
computers, Zero series, Compute Modules, and Pico microcontrollers.

## Raspberry Pi 5 Key Specs

- SoC: BCM2712 (Broadcom)
- CPU: Quad-core ARM Cortex-A76, AArch64
- RAM: up to 16 GB (RPi 5)
- GPIO: 40-pin header
- Connectivity: Wi-Fi, Bluetooth, USB-C power
- Video: dual micro-HDMI

## Thermal Management

All RPi models perform thermal management to avoid overheating. Hard temperature limit: **85°C**.
Progressive throttling begins as temperature approaches this threshold.

RPi5 supports an optional active cooling solution with automatic fan speed management.

## Compliance

PCBs meet UL94-V0 flammability standards.

## Compute Module Series

Industrial-focused boards without onboard connectors; require separate carrier boards.
Available in DDR2 SODIMM and high-density connector form factors.

## Pico / Microcontroller Boards

RP2040 and RP2350-based boards running MicroPython or C/C++. Not Linux-based.
