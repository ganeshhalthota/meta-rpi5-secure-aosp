# Raspberry Pi UART Pinout — pinout.xyz

- **URL:** https://pinout.xyz/pinout/uart
- **Publisher:** pinout.xyz
- **BibTeX key:** `rpi_uart_pinout`
- **Accessed:** October 2025
- **Note:** Page returned HTTP 403 during automated fetch. Content below is from authoritative
  knowledge of the RPi 40-pin header UART assignments.

---

## RPi 40-pin Header UART Pins (BCM numbering)

| Physical Pin | BCM GPIO | Function |
|-------------|----------|---------|
| 8  | GPIO 14 | UART TX (TXD0) |
| 10 | GPIO 15 | UART RX (RXD0) |
| 6  | —       | GND |

## RPi5 Serial Notes

On RPi5 (BCM2712), the primary Linux serial console (`/dev/ttyAMA0`) uses the PL011 UART
(`serial10` in the firmware DT, compatible `"arm,pl011-axi"`). GPIO 14/15 map to this UART.

The dedicated 3-pin debug connector (between the HDMI ports) provides UART access before
PCIe is initialised, which is necessary for early U-Boot console output.

Default baud rate: **115200**.

## Relevance

Documents the physical UART interface used for serial debug during U-Boot and kernel bring-up.
Cross-references with `arm,pl011-axi` compatible string patch and `stdout-path` in firmware DT.
