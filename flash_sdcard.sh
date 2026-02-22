#!/bin/bash

IMG_PATH=$1
DEVICE="$2"

if [[ -z "$IMG_PATH" ]]; then
    echo "Usage: $0 <path_to_image> [<device>]"
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
echo "Flashing complete. You can now safely eject the SD card."
