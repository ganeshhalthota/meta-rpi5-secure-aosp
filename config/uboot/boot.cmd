# U-Boot boot script for Android on RPi5
# Compiled to boot.scr via: mkimage -C none -A arm64 -T script -d boot.cmd boot.scr

echo "=== Android U-Boot Boot Script ==="

# Load Android kernel from FAT32 (mmc 0:1 = p1)
echo "Loading kernel Image..."
fatload mmc 0:1 ${kernel_addr_r} Image


# Load Android ramdisk
echo "Loading ramdisk..."
fatload mmc 0:1 ${ramdisk_addr_r} ramdisk.img

# Set Android kernel command line (matches BOARD_KERNEL_CMDLINE in BoardConfig.mk)
# Append Android-specific parameters to the firmware-provided bootargs.
# The RPi firmware sets ${bootargs} with critical parameters like:
#   numa=fake=8, vc_mem.mem_base/size, coherent_pool, pci=pcie_bus_safe, etc.
# We must NOT replace them — only append our Android-specific ones.
setenv bootargs "${bootargs} root=/dev/ram0 rootwait androidboot.hardware=rpi5 androidboot.selinux=__SELINUX_MODE__ __CMDLINE_PROFILE_ARGS__ __BOOT_STATE_ARGS__ __ENCRYPTION_ARGS__"

# Boot Android (AArch64 kernel + ramdisk + firmware-provided FDT)
# IMPORTANT: Use ${fdt_addr} — the DTB the RPi firmware already prepared in memory
# (with bcm2712d0, vc4-kms-v3d, cma, dwc2 overlays applied).
# Do NOT load bcm2712-rpi-5-b.dtb from disk — that raw DTB lacks the overlays
# and causes an SError in bcm2712_pinconf_set (brcmuart_init) at boot.
echo "Booting Android..."
booti ${kernel_addr_r} ${ramdisk_addr_r}:${filesize} ${fdt_addr}
