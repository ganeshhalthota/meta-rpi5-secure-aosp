# U-Boot Serial PL01x Driver — drivers/serial/serial_pl01x.c

- **URL:** https://source.denx.de/u-boot/u-boot/-/blob/master/drivers/serial/serial_pl01x.c
- **Raw:** https://source.denx.de/u-boot/u-boot/-/raw/master/drivers/serial/serial_pl01x.c
- **Repository:** U-Boot (DENX GitLab, master branch)
- **License:** GPL-2.0+
- **BibTeX key:** `uboot_serial_pl01x`
- **Accessed:** October 2025

---

## Overview

Implements U-Boot DM serial operations for ARM PrimeCell PL010 and PL011 UART controllers.
This is the file modified by patch
`0001-serial-pl01x-add-arm-pl011-axi-compatible-for-RPi5.patch`.

## Architecture

Supports two modes:

| Mode | Condition | Description |
|------|-----------|-------------|
| Legacy | `!CONFIG_IS_ENABLED(DM_SERIAL)` | Direct register access, static config |
| Driver Model | `CONFIG_IS_ENABLED(DM_SERIAL)` | Device tree integration, dynamic platform data |

## Key Functions

| Function | Purpose |
|----------|---------|
| `pl01x_putc()` | Transmit a character (waits for FIFO space) |
| `pl01x_getc()` | Receive a character (polls FIFO, handles error flags) |
| `pl01x_generic_setbrg()` | Baud rate configuration (type-specific divisor calculations) |
| `pl01x_serial_probe()` | Device initialisation |
| `_debug_uart_init()` | Early debug console support |

## Compatible String Match Table (`pl01x_serial_id[]`)

Before the patch the table contained only:
```c
{.compatible = "arm,pl011", .data = TYPE_PL011},
{.compatible = "arm,pl010", .data = TYPE_PL010},
```

After the patch (`0001-serial-pl01x-add-arm-pl011-axi-compatible-for-RPi5.patch`):
```c
{.compatible = "arm,pl011-axi", .data = TYPE_PL011},   /* added for RPi5 */
{.compatible = "arm,pl011",     .data = TYPE_PL011},
{.compatible = "arm,pl010",     .data = TYPE_PL010},
```

The RPi5 firmware DT uses `"arm,pl011-axi"` for `serial10` (the `stdout-path` target).
Without the new entry U-Boot cannot bind the UART node, and no console output appears.
