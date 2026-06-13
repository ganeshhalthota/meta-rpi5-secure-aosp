# Secure Boot on RPi 4 Model B — Raspberry Pi Forums

- **URL:** https://forums.raspberrypi.com/viewtopic.php?t=344770
- **Author:** syedelec (question), cleverca22 (answer)
- **Date:** Wed Dec 28, 2022
- **BibTeX key:** `rpi_secure_boot_forum`
- **Accessed:** October 2025

---

## Thread Overview

Q&A on implementing secure boot on RPi4 Model B using Yocto and U-Boot with `SIGNED_BOOT=1`.

## Key Technical Clarifications (cleverca22)

### Hardware Variants
- **BCM2711B0**: supports HMAC verification only
- **BCM2711 B1 / C0**: supports RSA with four hard-coded ROM keys

### Development Key Revocation
`revoke_devkey=1` disables one RSA key; subsequently only RPF-approved binaries are accepted.

### `.sig` File
`bootcode4.bin` within the EEPROM is already signed by RPF's RSA keys. The `.sig` file
format is correct — it contains the RSA signature, not just SHA256.

### Recovery Limitations
Only `recovery.bin` can interpret `program_pubkey` and `program_jtag_lock` flags.
`BOOT_ORDER` controls only where `start4.elf` loads from, not recovery mode programming.

### GPIO Numbers
Numbers referenced in config are BCM GPIO numbers, not physical pin numbers.
Setting `program_rpiboot_gpio=6` references BCM GPIO 6, not pin 6.

### Downgrade Compatibility
Bootloader versions 2022-11-25 and newer use key1 and support secure boot — they remain
flashable after key revocation.

## Relevance
Documents the OTP-based secure boot locking mechanism on BCM2711 (RPi4). Provides context
for understanding differences vs. BCM2712 (RPi5) and AVB2-based approach used in this project.
