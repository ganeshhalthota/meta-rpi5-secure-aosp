#!/bin/bash

# Flash SD card image and optionally fix GPT + expand userdata partition
# Usage: ./flash_sdcard.sh <path_to_image> [<device>] [--skip-expand]

IMG_PATH=$1
DEVICE=""
SKIP_EXPAND=false

# Parse arguments
shift
while [[ $# -gt 0 ]]; do
    case $1 in
        --skip-expand)
            SKIP_EXPAND=true
            shift
            ;;
        *)
            if [[ -z "$DEVICE" ]]; then
                DEVICE=$1
            fi
            shift
            ;;
    esac
done

if [[ -z "$IMG_PATH" ]]; then
    echo "Usage: $0 <path_to_image> [<device>] [--skip-expand]"
    echo ""
    echo "Options:"
    echo "  --skip-expand    Skip GPT repair and userdata expansion (raw flash only)"
    echo ""
    echo "If <device> is not provided, the script will try to auto-detect it."
    exit 1
fi

if [[ -z "$DEVICE" ]]; then
    echo "Attempting to auto-detect SD card reader..."

    # lsblk columns: NAME, RM (removable), TRAN (transport type)
    mapfile -t devices_info < <(lsblk -d -n -p -o NAME,RM,TRAN)

    declare -a candidates
    for info in "${devices_info[@]}"; do
        # Split info into parts
        read -r name rm tran <<< "$info"

        # Add removable devices (RM=1) that are sd or mmc to candidates
        if [[ "$rm" == "1" && ("$tran" == "sd" || "$tran" == "mmc") ]]; then
            candidates+=("$name")
        fi
    done

    if [ ${#candidates[@]} -eq 0 ]; then
        echo "No suitable SD card reader found. Please specify the device manually."
        echo "Usage: $0 <path_to_image> <device>"
        exit 1
    elif [ ${#candidates[@]} -eq 1 ]; then
        DEVICE=${candidates[0]}
        read -p "Detected device: $DEVICE. Continue? (y/N) " -n 1 -r
        echo
        if [[ ! $REPLY =~ ^[Yy]$ ]]; then
            echo "Aborting."
            exit 1
        fi
    else
        echo "Multiple possible devices found. Please select one:"
        select opt in "${candidates[@]}"; do
            if [[ -n "$opt" ]]; then
                DEVICE=$opt
                break
            else
                echo "Invalid selection. Please try again."
            fi
        done
    fi
fi

if [[ -z "$DEVICE" ]]; then
    echo "Error: DEVICE variable is not set and could not be auto-detected."
    exit 1
fi

if ! [ -b "$DEVICE" ]; then
    echo "Error: $DEVICE is not a block device."
    exit 1
fi

# Flash the image
echo "=========================================="
echo "Flashing image to $DEVICE..."
echo "=========================================="

if command -v pv >/dev/null 2>&1; then
    echo "Using pv to show progress..."
    # pv will show a progress bar, ETA, and transfer rate.
    time pv "$IMG_PATH" | sudo dd of="$DEVICE" bs=8M conv=fsync oflag=direct iflag=fullblock
else
    echo "pv not found, using dd's built-in progress."
    echo "For a better experience, install 'pv' (e.g., 'sudo apt install pv')."
    time sudo dd if="$IMG_PATH" of="$DEVICE" bs=8M status=progress conv=fsync oflag=direct iflag=fullblock
fi

sync
echo "Flashing complete."

# GPT repair and userdata expansion
if [[ "$SKIP_EXPAND" == false ]]; then
    echo ""
    echo "=========================================="
    echo "Fixing GPT and expanding userdata..."
    echo "=========================================="

    # Check if sgdisk is available
    if ! command -v sgdisk >/dev/null 2>&1; then
        echo "Error: sgdisk not found. Please install gdisk package:"
        echo "  sudo apt install gdisk"
        echo ""
        echo "You can manually fix the GPT later using:"
        echo "  sudo sgdisk --move-second-header $DEVICE"
        echo "  sudo ./scripts/fix_gpt.sh $DEVICE"
        exit 1
    fi

    # Step 1: Move backup GPT to the end of the physical disk
    echo ""
    echo "Step 1: Relocating backup GPT to end of disk..."
    if sudo sgdisk --move-second-header "$DEVICE"; then
        echo "✓ Backup GPT relocated successfully"
    else
        echo "✗ Failed to relocate backup GPT"
        exit 1
    fi

    # Step 2: Expand userdata partition (p3) to fill remaining space
    echo ""
    echo "Step 2: Expanding userdata partition (p3)..."

    # Get the start sector of partition 3
    START=$(sudo sgdisk -i 3 "$DEVICE" | grep "First sector" | awk '{print $3}')

    if [[ -z "$START" ]]; then
        echo "✗ Failed to get start sector of partition 3"
        exit 1
    fi

    echo "  Current start sector: $START"

    # Delete partition 3
    if sudo sgdisk -d 3 "$DEVICE" >/dev/null 2>&1; then
        echo "  ✓ Deleted partition 3"
    else
        echo "  ✗ Failed to delete partition 3"
        exit 1
    fi

    # Recreate partition 3 from same start to end of disk (0 = fill)
    if sudo sgdisk -n 3:"${START}":0 -t 3:8300 -c 3:userdata "$DEVICE" >/dev/null 2>&1; then
        echo "  ✓ Recreated partition 3 to fill disk"
    else
        echo "  ✗ Failed to recreate partition 3"
        exit 1
    fi

    # Inform kernel of partition table changes
    echo ""
    echo "Step 3: Updating kernel partition table..."
    sudo partprobe "$DEVICE" 2>/dev/null || sudo blockdev --rereadpt "$DEVICE" 2>/dev/null
    sleep 2

    # Step 4: Resize the ext4 filesystem
    echo ""
    echo "Step 4: Resizing ext4 filesystem on ${DEVICE}3..."

    # Check filesystem first
    if sudo e2fsck -f -y "${DEVICE}3" >/dev/null 2>&1; then
        echo "  ✓ Filesystem check passed"
    else
        echo "  ⚠ Filesystem check had issues (may be normal for new filesystem)"
    fi

    # Resize filesystem to fill partition
    if sudo resize2fs "${DEVICE}3" >/dev/null 2>&1; then
        echo "  ✓ Filesystem resized successfully"
    else
        echo "  ✗ Failed to resize filesystem"
        exit 1
    fi

    echo ""
    echo "=========================================="
    echo "✓ GPT repair and userdata expansion complete!"
    echo "=========================================="

    # Show final partition layout
    echo ""
    echo "Final partition layout:"
    sudo sgdisk -p "$DEVICE" 2>/dev/null | grep -E "^Number|^   [0-9]"

else
    echo ""
    echo "Skipping GPT repair and userdata expansion (--skip-expand flag used)."
    echo "To fix GPT and expand userdata later, run:"
    echo "  sudo ./scripts/fix_gpt.sh $DEVICE"
fi

echo ""
echo "You can now safely eject the SD card."
