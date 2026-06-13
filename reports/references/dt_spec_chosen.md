# Devicetree Specification — Chapter 3: Device Node Requirements

- **URL:** https://devicetree-specification.readthedocs.io/en/latest/chapter3-devicenodes.html
- **Publisher:** Devicetree.org
- **BibTeX key:** `dt_spec_chosen`
- **Accessed:** October 2025

---

## Overview

Defines mandatory and optional nodes in a valid devicetree, including the `/chosen` node
which carries runtime parameters set by system firmware.

## Relevance to the pl011-axi Patch

The RPi5 firmware-provided DT sets:
```
/chosen {
    stdout-path = "serial10:115200n8";
};
```
`stdout-path` instructs the bootloader (U-Boot) to use `serial10` as the boot console.
`serial10` has `compatible = "arm,pl011-axi"`. Without that compatible string in U-Boot's
`pl01x_serial_id[]` match table, U-Boot cannot bind the node, and no serial output appears.

## `/chosen` Node

- **Purpose:** Specifies runtime parameters rather than actual hardware devices.
- **`stdout-path` property:**
  - Type: string
  - Optional, but recommended.
  - Full DT path (or alias) to the device used for boot console output.
  - A colon `:` in the value terminates the path; remainder is device-specific parameters
    (e.g. baud rate).
  - When `stdin-path` is absent, `stdout-path` is also assumed to define the input device.
  - Legacy variant: `linux,stdout-path` (deprecated).

## Core Node Requirements

Every valid DT must contain:
- Root node (`/`) with `#address-cells`, `#size-cells`, `model`, `compatible`
- `/cpus` node
- At least one `/memory` node

## `/aliases` Node

Provides shorthand references to device paths. Alias names: lowercase letters, digits, dashes
(1–31 characters).

## `/reserved-memory` Node

Designates memory regions excluded from normal OS use. `no-map` and `reusable` are mutually
exclusive properties.
