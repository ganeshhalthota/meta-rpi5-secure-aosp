# Test Cases — SD Card Image Validation

Two image sets are under test:

| Image Set | Config | Partition Scheme | Signing | Build Variant | AVB Policy | SELinux | FDE |
|-----------|--------|-----------------|---------|---------------|------------|---------|-----|
| **Unsigned** | `rpi5_uboot_aosp.yaml` | MBR | Disabled | `eng` | `fail_open` | `permissive` | Disabled |
| **Signed** | `rpi5_uboot_aosp_signed.yaml` | GPT | Enabled | `user` | `fail_closed` | `enforcing` | Enabled |

Serial console: `115200 8N1` on `/dev/ttyACM0`.
SD card device on host: `/dev/sdc` — partitions are `/dev/sdc1`, `/dev/sdc3`, `/dev/sdc5`, `/dev/sdc6`, `/dev/sdc7`, `/dev/sdc8`.

> **Warning:** Always unmount the SD card from the RPi before connecting to the host reader. Confirm `/dev/sdc` is the SD card with `lsblk` before any write command.

---

## Section 0 — Pre-Flash Setup

Flash commands for reference (run on host before each test section):

```bash
# Unsigned image
sudo dd if=work/sdcard/rpi5-uboot-aosp.img of=/dev/sdc bs=4M status=progress conv=fsync

# Signed image
sudo dd if=work/sdcard/rpi5-uboot-aosp-signed.img of=/dev/sdc bs=4M status=progress conv=fsync

# After flashing, trigger partition table re-read
sudo partprobe /dev/sdc
```

Mount helpers used throughout:

```bash
# Mount boot partition (FAT32, p1)
sudo mkdir -p /mnt/rpi5boot && sudo mount /dev/sdc1 /mnt/rpi5boot

# Mount system partition (ext4, p5) — read-only
sudo mkdir -p /mnt/rpi5system && sudo mount -o ro /dev/sdc5 /mnt/rpi5system

# Unmount
sudo umount /mnt/rpi5boot
sudo umount /mnt/rpi5system
```

---

## Section 1 — Boot Baseline

### TC-BOOT-001: Unsigned image boots to Android

**Image set:** Unsigned
**Goal:** Full boot chain completes without AVB verification.

Steps:

1. Flash unsigned image. Insert SD card into RPi5 and power on.
2. Open serial console: `screen /dev/ttyACM0 115200`
3. Observe U-Boot output until Android is visible on HDMI.

Files / output to verify:

- Serial line: `=== Android U-Boot Boot Script ===`
- Serial line: `Booting Android...`
- No lines matching `avb init` or `AVB:` present anywhere in U-Boot output.
- Android home screen visible on HDMI.

---

### TC-BOOT-002: Signed image boots to Android

**Image set:** Signed
**Goal:** AVB verification passes and Android boots.

Steps:

1. Flash signed image. Insert SD card into RPi5 and power on.
2. Open serial console.

Files / output to verify:

- Serial line: `=== Android U-Boot Boot Script (AVB) ===`
- Serial line: `AVB: Verification PASSED`
- Serial line: `Booting Android with AVB verification...`
- Android home screen visible on HDMI.

---

### TC-BOOT-003: Boot partition contains correct files

**Image set:** Both
**Goal:** Each image's p1 contains the expected boot files and the correct boot script variant.

Steps (run on host with SD card in reader, before inserting into RPi5):

```bash
sudo mount /dev/sdc1 /mnt/rpi5boot
ls -lh /mnt/rpi5boot/
sudo umount /mnt/rpi5boot
```

Files to verify — **Unsigned image p1**:

| File | Expected |
|------|----------|
| `boot.scr` | Present — compiled from `boot.cmd` (non-AVB) |
| `u-boot.bin` | Present |
| `config.txt` | Present |
| `Image` | Present — Android kernel |
| `ramdisk.img` | Present — Android ramdisk |
| `boot_avb.scr` | **Must not be present** |

Files to verify — **Signed image p1**:

| File | Expected |
|------|----------|
| `boot.scr` | Present — compiled from `boot_avb.cmd` (AVB script written as `boot.scr`) |
| `u-boot.bin` | Present |
| `config.txt` | Present |
| `Image` | Present |
| `ramdisk.img` | Present |

---

## Section 2 — Partition Layout

### TC-PART-001: Unsigned image uses MBR partition scheme

**Image set:** Unsigned
**Goal:** Partition table type and sizes match `config/sdcard/uboot_aosp.yaml`.

```bash
sudo parted /dev/sdc print
```

Expected output:

```bash
Partition Table: msdos
Number  Start    End      Size     Type      File system  Flags
 1      ...      ...      128MiB   primary   fat32        boot
 3      ...      ...      (remaining space)  logical   ext4
 5      ...      ...      3072MiB  logical   ext4
 6      ...      ...      384MiB   logical   ext4
 7      ...      ...      16MiB    logical   ext4
```

Verify:

- Table type is `msdos` (not `gpt`).
- p8 does **not** exist.

---

### TC-PART-002: Signed image uses GPT partition scheme

**Image set:** Signed
**Goal:** Partition table type, sizes, and vbmeta partition match `config/sdcard/uboot_aosp_signed.yaml`.

```bash
sudo parted /dev/sdc print
```

Expected output:

```bash
Partition Table: gpt
Number  Start    End      Size     File system  Name      Flags
 1      ...      ...      128MiB   fat32        boot      boot
 3      ...      ...      (remaining space)  ext4   userdata
 5      ...      ...      3072MiB  ext4         system
 6      ...      ...      384MiB   ext4         vendor
 7      ...      ...      16MiB    ext4         metadata
 8      ...      ...      4MiB                  vbmeta
```

Verify:

- Table type is `gpt`.
- p8 (vbmeta) is present, 4 MiB, raw (no filesystem label).

---

### TC-PART-003: Partition numbers match fstab

**Image set:** Both
**Goal:** Android `fstab.rpi5` references the same partition numbers as the SD card layout.

```bash
sudo mount -o ro /dev/sdc5 /mnt/rpi5system
cat /mnt/rpi5system/etc/fstab.rpi5
sudo umount /mnt/rpi5system
```

Expected entries in `fstab.rpi5`:

| Mount point | Block device |
|-------------|-------------|
| `/system` | `mmcblk0p5` |
| `/vendor` | `mmcblk0p6` |
| `/metadata` | `mmcblk0p7` |
| `/data` | `mmcblk0p3` |

---

## Section 3 — AVB Verification (Signed Image)

### TC-AVB-001: vbmeta partition contains valid AVB header

**Image set:** Signed
**Goal:** p8 holds a parseable vbmeta image with the expected signing algorithm.

```bash
sudo dd if=/dev/sdc8 of=/tmp/vbmeta.img bs=4M count=1
avbtool info_image --image /tmp/vbmeta.img
```

Expected `avbtool` output:

```bash
Footer version:           1.0
Image size:               ...
Original image size:      ...
VBMeta offset:            0
VBMeta size:              ...
--
Minimum libavb version:   1.0
Header Block:             ...
Authentication Block:     ...
Auxiliary Block:          ...
Algorithm:                SHA256_RSA4096
Rollback Index:           0
...
```

Verify:

- `Algorithm: SHA256_RSA4096` matches `avb.sign_algorithm` in config.
- No parse errors — `avbtool` exits 0.

---

### TC-AVB-002: vbmeta chains to system and vendor partitions

**Image set:** Signed
**Goal:** vbmeta descriptors cover both `system` and `vendor`.

```bash
avbtool info_image --image /tmp/vbmeta.img
# (reuse /tmp/vbmeta.img from TC-AVB-001)
```

Expected — descriptors section must include entries for both:

```bash
    Hash Tree Descriptor:
      ...
      Partition Name:        system
    Hash Tree Descriptor:
      ...
      Partition Name:        vendor
```

Verify:

- Both `system` and `vendor` partition descriptors present.
- Rollback index is a non-negative integer.

---

### TC-AVB-003: AVB verification fails with wrong public key

**Image set:** Signed
**Goal:** `fail_closed` policy rejects a signed image when U-Boot has a different key compiled in.

Preparation (on host):

1. Generate a second AVB keypair:

   ```bash
   openssl genrsa -out /tmp/avb_test_key.pem 4096
   python3 avbtool extract_public_key --key /tmp/avb_test_key.pem --output /tmp/avb_test_pubkey.bin
   ```

2. Patch `common/avb_verify.c` in the U-Boot tree to embed `/tmp/avb_test_pubkey.bin`.
3. Rebuild U-Boot binary only.
4. Mount p1 and replace `u-boot.bin`:

   ```bash
   sudo mount /dev/sdc1 /mnt/rpi5boot
   sudo cp work/u-boot-rpi5/u-boot.bin /mnt/rpi5boot/u-boot.bin
   sudo umount /mnt/rpi5boot
   ```

5. Insert SD card into RPi5 and boot.

Serial output to verify:

- `AVB: Verification FAILED`
- `Fail-closed policy: resetting`
- No kernel load (`booti` line must **not** appear).
- Device resets and loops — does not reach Android.

---

### TC-AVB-004: Tampered system partition triggers AVB failure

**Image set:** Signed
**Goal:** A single corrupted block in p5 (system) causes AVB to reject the image.

> Start from a clean flash (TC-REG-001 must have passed first).

Corrupt one block in the middle of system (p5):

```bash
# Write 512 zero bytes at block offset 10000 within p5
sudo dd if=/dev/zero of=/dev/sdc5 bs=512 count=1 seek=10000 conv=notrunc
sudo sync
```

Insert SD card into RPi5 and boot. Serial output to verify:
- `AVB: Verification FAILED`
- `Fail-closed policy: resetting`
- No `booti` line in U-Boot output.

---

### TC-AVB-005: Tampered vendor partition triggers AVB failure

**Image set:** Signed
**Goal:** Same as TC-AVB-004 for p6 (vendor).

> Start from a clean flash.

```bash
sudo dd if=/dev/zero of=/dev/sdc6 bs=512 count=1 seek=500 conv=notrunc
sudo sync
```

Insert SD card into RPi5 and boot. Serial output to verify:
- `AVB: Verification FAILED`
- `Fail-closed policy: resetting`

---

### TC-AVB-006: Corrupted vbmeta header causes immediate reject

**Image set:** Signed
**Goal:** Zeroing the vbmeta magic/header causes AVB to reject early.

> Start from a clean flash.

```bash
# Overwrite first 256 bytes of vbmeta partition (p8)
sudo dd if=/dev/zero of=/dev/sdc8 bs=1 count=256 conv=notrunc
sudo sync
```

Insert SD card into RPi5 and boot. Serial output to verify:
- `Verifying partitions...`
- `AVB: Verification FAILED`
- `Fail-closed policy: resetting`
- Device resets immediately — kernel never loads.

---

### TC-AVB-007: Unsigned image does not perform AVB verification

**Image set:** Unsigned
**Goal:** AVB commands are absent from the unsigned boot path.

Steps:
1. Boot the unsigned image; capture full U-Boot serial output.

Serial output to verify:
- `=== Android U-Boot Boot Script ===` present.
- **None** of these lines appear: `avb init`, `avb verify`, `AVB: Verification`, `Initializing AVB`, `Verifying partitions`.
- Execution jumps directly from `Loading kernel Image...` → `Booting Android...` → `booti`.

---

### TC-AVB-008: fail_open policy allows degraded boot on AVB init failure

**Image set:** Requires a third image (AVB boot script + `fail_open` + no vbmeta partition)
**Goal:** `fail_open` permits a degraded boot and sets `orange` state in bootargs.

> See prior discussion: this test requires a dedicated `rpi5_uboot_aosp_avb_debug.yaml` config. Not runnable with the current two images.

Serial output to verify (once third image exists):
- `AVB: Initialization FAILED`
- `WARNING: Continuing boot with fail_open policy`
- `Booting Android with AVB fail_open fallback...`
- Kernel loads successfully (degraded boot, not blocked).

`/proc/cmdline` to verify (from Android):
```
androidboot.verifiedbootstate=orange androidboot.vbmeta.device_state=unlocked
```

---

## Section 4 — Boot State and Kernel Command Line

### TC-CMDLINE-001: Unsigned image sets orange verified boot state

**Image set:** Unsigned
**Goal:** `state_override: orange` is rendered into bootargs.

From Android over ADB:
```bash
adb shell cat /proc/cmdline
```

Exact strings to verify in cmdline:
```
androidboot.verifiedbootstate=orange androidboot.vbmeta.device_state=unlocked
```

These are produced by `boot_state_args` in `main.py:127`.

---

### TC-CMDLINE-002: Signed image carries AVB-driven verified boot state

**Image set:** Signed
**Goal:** `state_override: none` leaves boot state to AVB (`green` on successful verify).

```bash
adb shell cat /proc/cmdline
```

Exact strings to verify:
- `androidboot.verifiedbootstate=green` present (set by `avb verify` via `${avb_bootargs}`).
- `androidboot.vbmeta.device_state=locked` present.
- `androidboot.vbmeta.device_state=unlocked` **must not** appear.

---

### TC-CMDLINE-003: Unsigned image uses debug cmdline profile

**Image set:** Unsigned
**Goal:** `cmdline_profile: debug` renders `ignore_loglevel loglevel=7` into bootargs.

```bash
adb shell cat /proc/cmdline
```

Exact strings to verify (from `main.py:131`):
```
ignore_loglevel loglevel=7
```

---

### TC-CMDLINE-004: Signed image uses production cmdline profile

**Image set:** Signed
**Goal:** `cmdline_profile: production` renders `quiet loglevel=4` into bootargs.

```bash
adb shell cat /proc/cmdline
```

Exact strings to verify (from `main.py:132`):
```
quiet loglevel=4
```

Verify `ignore_loglevel` and `loglevel=7` are **absent**.

---

### TC-CMDLINE-005: Boot partition UUID propagated to bootargs

**Image set:** Signed (GPT provides stable partition UUIDs)
**Goal:** `androidboot.boot_part_uuid` is populated from `part uuid mmc 0:1`.

Step 1 — query UUID from host before booting:
```bash
sudo blkid /dev/sdc1
# Note the UUID value (PARTUUID on GPT)
```

Step 2 — check U-Boot serial output during boot:
- Line present: `part uuid mmc 0:1 boot_part_uuid` succeeds.
- No line: `WARNING: Failed to query boot partition UUID`.

Step 3 — verify in Android:
```bash
adb shell cat /proc/cmdline | tr ' ' '\n' | grep boot_part_uuid
```

Expected: `androidboot.boot_part_uuid=<uuid-matching-step-1>`

---

## Section 5 — SELinux Mode

### TC-SELINUX-001: Unsigned image boots with SELinux permissive

**Image set:** Unsigned

Verify cmdline before boot (host, from boot partition):
```bash
sudo mount /dev/sdc1 /mnt/rpi5boot
# The generated boot script (plain text before mkimage compiles it) is NOT
# readable post-compile; verify at runtime instead.
sudo umount /mnt/rpi5boot
```

Verify at runtime:
```bash
adb shell cat /proc/cmdline | tr ' ' '\n' | grep selinux
# Expected: androidboot.selinux=permissive

adb shell getenforce
# Expected: Permissive

adb shell cat /sys/fs/selinux/enforce
# Expected: 0
```

---

### TC-SELINUX-002: Signed image boots with SELinux enforcing

**Image set:** Signed

```bash
adb shell cat /proc/cmdline | tr ' ' '\n' | grep selinux
# Expected: androidboot.selinux=enforcing

adb shell getenforce
# Expected: Enforcing

adb shell cat /sys/fs/selinux/enforce
# Expected: 1
```

---

### TC-SELINUX-003: Critical system services start under enforcing mode

**Image set:** Signed

```bash
# Check for blocking AVC denials in early boot
adb shell dmesg | grep "avc: denied"

# Check key service states
adb shell getprop init.svc.surfaceflinger   # Expected: running
adb shell getprop init.svc.audioserver      # Expected: running
adb shell getprop init.svc.vold             # Expected: running

# Scan logcat for denial loops on critical processes
adb shell logcat -d -s "auditd" | grep "avc: denied" | head -20
```

Pass criteria: no service in a crash-restart loop attributable to a SELinux denial; `surfaceflinger`, `audioserver`, `vold` all report `running`.

---

## Section 6 — Build Variant

### TC-VARIANT-001: Unsigned image is an eng build

**Image set:** Unsigned

```bash
adb shell getprop ro.build.type
# Expected: eng

adb shell getprop ro.debuggable
# Expected: 1

adb root
# Expected: restarting adbd as root
```

---

### TC-VARIANT-002: Signed image is a user build

**Image set:** Signed

```bash
adb shell getprop ro.build.type
# Expected: user

adb shell getprop ro.debuggable
# Expected: 0

adb root
# Expected: adbd cannot run as root in production builds
```

---

## Section 7 — Full-Disk Encryption (FDE)

### TC-FDE-001: Unsigned image boots without FDE

**Image set:** Unsigned

Verify userdata partition is plain ext4 before boot:
```bash
sudo blkid /dev/sdc3
# Expected: TYPE="ext4"  — no dm-crypt indications
```

Verify at runtime:
```bash
adb shell getprop ro.crypto.state
# Expected: unencrypted

adb shell getprop ro.crypto.type
# Expected: (empty or "none")
```

Verify `androidboot.fde_mode` is absent from cmdline:
```bash
adb shell cat /proc/cmdline | tr ' ' '\n' | grep fde
# Expected: (no output)
```

---

### TC-FDE-002: Signed image triggers FDE on first boot

**Image set:** Signed (fresh flash — userdata must be unencrypted at start)

Before flashing, confirm `/dev/sdc3` is plain ext4:
```bash
sudo blkid /dev/sdc3
# Expected: TYPE="ext4"
```

Verify `androidboot.fde_mode=enabled` in cmdline (from `main.py:138`):
```bash
adb shell cat /proc/cmdline | tr ' ' '\n' | grep fde
# Expected: androidboot.fde_mode=enabled
```

After first-boot encryption cycle completes:
```bash
adb shell getprop ro.crypto.state
# Expected: encrypted

adb shell getprop ro.crypto.type
# Expected: block
```

Remove SD card and verify from host that `/dev/sdc3` now has a dm-crypt header:
```bash
sudo cryptsetup isLuks /dev/sdc3; echo $?
# Note: Android FDE uses its own format (not LUKS), so isLuks may return 1.
# Instead check blkid — the raw partition should no longer show TYPE="ext4".
sudo blkid /dev/sdc3
# Expected: TYPE absent or crypto_LUKS / unknown — not plain ext4
```

---

### TC-FDE-003: Encrypted userdata persists across reboot

**Image set:** Signed (run after TC-FDE-002 completes)

Steps:
1. Write a test file to `/data`:
   ```bash
   adb shell "echo 'fde-test' > /data/local/tmp/fde_marker.txt"
   ```
2. Reboot:
   ```bash
   adb reboot
   ```
3. Wait for boot to complete; reconnect adb.
4. Verify:
   ```bash
   adb shell cat /data/local/tmp/fde_marker.txt
   # Expected: fde-test

   adb shell getprop ro.crypto.state
   # Expected: encrypted
   ```

Pass criteria: file readable after reboot; no re-encryption prompt; `ro.crypto.state` still `encrypted`.

---

## Section 8 — Regression

### TC-REG-001: Known-good signed build boots successfully (control case)

**Image set:** Signed
**Goal:** Unmodified signed image meets all TC-BOOT-002 criteria. Run this before any tamper test.

```bash
sudo dd if=work/sdcard/rpi5-uboot-aosp-signed.img of=/dev/sdc bs=4M status=progress conv=fsync
sudo partprobe /dev/sdc
```

Insert into RPi5 and verify every item in TC-BOOT-002.

---

### TC-REG-002: Known-good unsigned build boots successfully (control case)

**Image set:** Unsigned

```bash
sudo dd if=work/sdcard/rpi5-uboot-aosp.img of=/dev/sdc bs=4M status=progress conv=fsync
sudo partprobe /dev/sdc
```

Insert into RPi5 and verify every item in TC-BOOT-001.

---

## Test Execution Matrix

| TC ID | Image Set | Category | Hardware Required | SD Device | Evidence to Capture |
|-------|-----------|----------|-----------------|-----------|---------------------|
| TC-BOOT-001 | Unsigned | Boot | RPi5 | — | Serial log |
| TC-BOOT-002 | Signed | Boot | RPi5 | — | Serial log |
| TC-BOOT-003 | Both | Boot | No (host) | `/dev/sdc1` | `ls /mnt/rpi5boot/` |
| TC-PART-001 | Unsigned | Partition Layout | No (host) | `/dev/sdc` | `parted /dev/sdc print` |
| TC-PART-002 | Signed | Partition Layout | No (host) | `/dev/sdc` | `parted /dev/sdc print` |
| TC-PART-003 | Both | Partition Layout | No (host) | `/dev/sdc5` | `cat fstab.rpi5` |
| TC-AVB-001 | Signed | AVB | No (host) | `/dev/sdc8` | `avbtool info_image` output |
| TC-AVB-002 | Signed | AVB | No (host) | `/dev/sdc8` | `avbtool info_image` output |
| TC-AVB-003 | Signed | AVB | RPi5 | `/dev/sdc1` | Serial log |
| TC-AVB-004 | Signed | AVB | RPi5 | `/dev/sdc5` | Serial log |
| TC-AVB-005 | Signed | AVB | RPi5 | `/dev/sdc6` | Serial log |
| TC-AVB-006 | Signed | AVB | RPi5 | `/dev/sdc8` | Serial log |
| TC-AVB-007 | Unsigned | AVB | RPi5 | — | Serial log |
| TC-AVB-008 | Third image | AVB | RPi5 | — | Serial log + `/proc/cmdline` |
| TC-CMDLINE-001 | Unsigned | Cmdline | RPi5 | — | `/proc/cmdline` |
| TC-CMDLINE-002 | Signed | Cmdline | RPi5 | — | `/proc/cmdline` |
| TC-CMDLINE-003 | Unsigned | Cmdline | RPi5 | — | `/proc/cmdline` |
| TC-CMDLINE-004 | Signed | Cmdline | RPi5 | — | `/proc/cmdline` |
| TC-CMDLINE-005 | Signed | Cmdline | RPi5 | `/dev/sdc1` | `blkid` + `/proc/cmdline` |
| TC-SELINUX-001 | Unsigned | SELinux | RPi5 | — | `getenforce`, `/proc/cmdline` |
| TC-SELINUX-002 | Signed | SELinux | RPi5 | — | `getenforce`, `/proc/cmdline` |
| TC-SELINUX-003 | Signed | SELinux | RPi5 | — | `dmesg`, `logcat`, `getprop` |
| TC-VARIANT-001 | Unsigned | Build Variant | RPi5 | — | `getprop` |
| TC-VARIANT-002 | Signed | Build Variant | RPi5 | — | `getprop`, `adb root` |
| TC-FDE-001 | Unsigned | FDE | RPi5 | `/dev/sdc3` | `blkid`, `getprop` |
| TC-FDE-002 | Signed | FDE | RPi5 | `/dev/sdc3` | `blkid`, `getprop` |
| TC-FDE-003 | Signed | FDE | RPi5 | — | `getprop`, file read |
| TC-REG-001 | Signed | Regression | RPi5 | — | Serial log |
| TC-REG-002 | Unsigned | Regression | RPi5 | — | Serial log |
