# U-Boot boot script for Android on RPi5 (with AVB 2.0)
# Compiled to boot_avb.scr via: mkimage -C none -A arm64 -T script -d boot_avb.cmd boot_avb.scr

echo "=== Android U-Boot Boot Script (AVB) ==="

# Build-time default; runtime override is possible by setting avb_fail_policy env var.
# Valid values: fail_closed, fail_open
if test -z "${avb_fail_policy}"; then
    setenv avb_fail_policy "__AVB_FAIL_POLICY__"
    echo "Setting AVB policy to default: fail_closed"
else
    echo "Loading AVB policy"
fi
echo "AVB fail policy: ${avb_fail_policy}"

# Clear AVB args from any previous runs
setenv avb_bootargs
setenv avb_bootargs_fallback
setenv bootdev_bootarg

# 1. AVB Initialization and Verification
# U-Boot must be built with CONFIG_AVB_VERIFY=y, CONFIG_CMD_AVB=y, CONFIG_LIBAVB=y
echo "Initializing AVB..."
if test -z "${avb_bootargs_fallback}" && avb init 0; then
    echo "Verifying partitions..."
else
    if test -z "${avb_bootargs_fallback}"; then
        echo "AVB: Initialization FAILED"
        if test "${avb_fail_policy}" = "fail_open"; then
            echo "WARNING: Continuing boot with fail_open policy"
            setenv avb_bootargs_fallback "androidboot.verifiedbootstate=orange androidboot.vbmeta.device_state=unlocked"
        else
            echo "Fail-closed policy: resetting"
            reset
        fi
    fi
fi

if test -z "${avb_bootargs_fallback}"; then
    if avb verify; then
        echo "AVB: Verification PASSED"
    else
        echo "AVB: Verification FAILED"
        if test "${avb_fail_policy}" = "fail_open"; then
            echo "WARNING: Continuing boot with fail_open policy"
            setenv avb_bootargs_fallback "androidboot.verifiedbootstate=orange androidboot.vbmeta.device_state=unlocked"
        else
            echo "Fail-closed policy: resetting"
            reset
        fi
    fi
fi

# 2. Load Android kernel from FAT32 (mmc 0:1 = p1)
echo "Loading kernel Image..."
fatload mmc 0:1 ${kernel_addr_r} Image
if test $? -ne 0; then
    echo "ERROR: Failed to load kernel"
    reset
fi

# 3. Load Android ramdisk
echo "Loading ramdisk..."
fatload mmc 0:1 ${ramdisk_addr_r} ramdisk.img
if test $? -ne 0; then
    echo "ERROR: Failed to load ramdisk"
    reset
fi

# 4. Set Android kernel command line
# ${avb_bootargs} is populated by 'avb verify' on success.
# For fail_open, add explicit fallback state args.
# Expose kernel-boot-partition UUID so first-stage init can identify boot device
# and create /dev/block/by-name/<partition> symlinks consistently on GPT layouts.
if part uuid mmc 0:1 boot_part_uuid; then
    setenv bootdev_bootarg "androidboot.boot_part_uuid=${boot_part_uuid}"
else
    echo "WARNING: Failed to query boot partition UUID (mmc 0:1)"
fi
setenv bootargs "${bootargs} root=/dev/ram0 rootwait androidboot.hardware=rpi5 androidboot.selinux=permissive ${bootdev_bootarg} ${avb_bootargs} ${avb_bootargs_fallback}"

# 5. Boot Android
if test -z "${avb_bootargs_fallback}"; then
    echo "Booting Android with AVB verification..."
else
    echo "Booting Android with AVB fail_open fallback..."
fi
booti ${kernel_addr_r} ${ramdisk_addr_r}:${filesize} ${fdt_addr}
