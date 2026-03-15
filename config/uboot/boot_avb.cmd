# U-Boot boot script for Android on RPi5 (with AVB 2.0)
# Compiled to boot_avb.scr via: mkimage -C none -A arm64 -T script -d boot_avb.cmd boot_avb.scr

echo "=== Android U-Boot Boot Script (AVB) ==="

# 1. AVB Initialization and Verification
# U-Boot must be built with CONFIG_AVB_VERIFY=y
echo "Initializing AVB..."
avb init 0

echo "Verifying partitions..."
avb verify

if test $avb_result -eq 0; then
    echo "AVB: Verification PASSED"
else
    echo "AVB: Verification FAILED (result=${avb_result})"
    echo "Halting system."
    reset
fi

# 2. Load Android kernel from FAT32 (mmc 0:1 = p1)
echo "Loading kernel Image..."
fatload mmc 0:1 ${kernel_addr_r} Image

# 3. Load Android ramdisk
echo "Loading ramdisk..."
fatload mmc 0:1 ${ramdisk_addr_r} ramdisk.img

# 4. Set Android kernel command line
# ${avb_bootargs} is automatically populated by 'avb verify'
# It contains dm-verity parameters required to mount system/vendor.
setenv bootargs "${bootargs} root=/dev/ram0 rootwait androidboot.hardware=rpi5 androidboot.selinux=permissive ${avb_bootargs}"

# 5. Boot Android
echo "Booting Android with dm-verity..."
booti ${kernel_addr_r} ${ramdisk_addr_r}:${filesize} ${fdt_addr}
