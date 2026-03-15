#!/bin/bash

################################################################################
# Script: fix_gpt_header.sh
# Description: Moves GPT header to the end of SD card after flashing with
#              BalenaEtcher. This fixes the backup GPT header location when
#              an image is flashed to a larger SD card.
# Usage:
#   Linux:  sudo ./fix_gpt_header.sh /dev/sdX
#   macOS:  sudo ./fix_gpt_header.sh /dev/diskX
# Compatibility: Linux and macOS
################################################################################

set -e  # Exit on error

# Detect OS
OS_TYPE=$(uname -s)

# Color codes for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to print colored messages
print_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Function to check if running as root
check_root() {
    if [ "$EUID" -ne 0 ]; then
        print_error "This script must be run as root (use sudo)"
        exit 1
    fi
}

# Function to check if gdisk is installed
check_gdisk() {
    if ! command -v gdisk &> /dev/null; then
        print_error "gdisk is not installed"
        if [ "$OS_TYPE" = "Darwin" ]; then
            print_info "Install it using: brew install gptfdisk"
        else
            print_info "Install it using: sudo apt-get install gdisk"
        fi
        exit 1
    fi
}

# Function to validate device path
validate_device() {
    local device=$1

    # Check if device exists
    if [ ! -b "$device" ] && [ ! -c "$device" ]; then
        print_error "Device $device does not exist or is not a block device"
        exit 1
    fi

    # Check if it's a partition (should be whole disk)
    # Linux: /dev/sdb1, macOS: /dev/disk2s1
    if [[ "$device" =~ [0-9]$ ]] || [[ "$device" =~ s[0-9]+$ ]]; then
        print_warning "Device appears to be a partition ($device)"
        if [ "$OS_TYPE" = "Darwin" ]; then
            print_warning "You should specify the whole disk (e.g., /dev/disk2 instead of /dev/disk2s1)"
        else
            print_warning "You should specify the whole disk (e.g., /dev/sdb instead of /dev/sdb1)"
        fi
        read -p "Continue anyway? (y/N): " -n 1 -r
        echo
        if [[ ! $REPLY =~ ^[Yy]$ ]]; then
            print_info "Aborted by user"
            exit 0
        fi
    fi
}

# Function to check if device is mounted
check_mounted() {
    local device=$1

    if mount | grep -q "^${device}"; then
        print_warning "One or more partitions on $device are currently mounted"
        print_info "Mounted partitions:"
        mount | grep "^${device}" | awk '{print "  " $1 " on " $3}'
        echo
        print_warning "It's recommended to unmount all partitions before proceeding"
        read -p "Do you want to continue anyway? (y/N): " -n 1 -r
        echo
        if [[ ! $REPLY =~ ^[Yy]$ ]]; then
            print_info "Aborted by user"
            exit 0
        fi
    fi
}

# Function to display device information
show_device_info() {
    local device=$1

    print_info "Device information for $device:"

    if [ "$OS_TYPE" = "Darwin" ]; then
        # macOS: use diskutil
        if command -v diskutil &> /dev/null; then
            diskutil info "$device" 2>/dev/null | grep -E "(Disk Size|Device / Media Name)" | sed 's/^/  /' || true
        fi
    else
        # Linux: use /sys/block
        if [ -f "/sys/block/$(basename $device)/size" ]; then
            local sectors=$(cat /sys/block/$(basename $device)/size)
            local size_gb=$(echo "scale=2; $sectors * 512 / 1024 / 1024 / 1024" | bc)
            echo "  Size: ${size_gb} GB (${sectors} sectors)"
        fi

        # Get device model if available
        if [ -f "/sys/block/$(basename $device)/device/model" ]; then
            local model=$(cat /sys/block/$(basename $device)/device/model | tr -d ' ')
            echo "  Model: $model"
        fi
    fi

    echo
}

# Function to fix GPT header using gdisk
fix_gpt_header() {
    local device=$1

    print_info "Moving GPT header to end of $device..."
    print_warning "This operation will modify the partition table"
    echo

    # Show current GPT status
    print_info "Current GPT status:"
    gdisk -l "$device" 2>&1 | grep -E "(GPT:|backup|Problem)" || true
    echo

    # Confirm before proceeding
    read -p "Proceed with fixing GPT header? (y/N): " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        print_info "Aborted by user"
        exit 0
    fi

    print_info "Executing gdisk commands..."

    # Use gdisk to fix the GPT header
    # Commands:
    # x - enter expert mode
    # e - relocate backup GPT data structures to the end of the disk
    # w - write table to disk and exit
    # y - confirm write
    echo -e "x\ne\nw\ny\n" | gdisk "$device" > /dev/null 2>&1

    if [ $? -eq 0 ]; then
        print_success "GPT header successfully moved to end of disk"
    else
        print_error "Failed to move GPT header"
        exit 1
    fi
}

# Function to verify the fix
verify_fix() {
    local device=$1

    print_info "Verifying GPT structure..."

    # Check for GPT problems
    local gpt_check=$(gdisk -l "$device" 2>&1)

    if echo "$gpt_check" | grep -qi "problem"; then
        print_warning "GPT verification found issues:"
        echo "$gpt_check" | grep -i "problem"
        return 1
    else
        print_success "GPT structure verified successfully"
        echo
        print_info "Updated GPT status:"
        echo "$gpt_check" | grep -E "(GPT:|backup)" || true
        return 0
    fi
}

# Main script execution
main() {
    echo "=========================================="
    echo "  GPT Header Fix Script"
    echo "=========================================="
    echo

    # Check if device argument is provided
    if [ $# -eq 0 ]; then
        print_error "No device specified"
        echo
        if [ "$OS_TYPE" = "Darwin" ]; then
            echo "Usage: sudo $0 /dev/diskX"
            echo
            echo "Example: sudo $0 /dev/disk2"
            echo
            print_info "Use 'diskutil list' to find your SD card device"
        else
            echo "Usage: sudo $0 /dev/sdX"
            echo
            echo "Example: sudo $0 /dev/sdb"
            echo
            print_info "Use 'lsblk' or 'fdisk -l' to find your SD card device"
        fi
        echo
        print_warning "Make sure to specify the correct device!"
        print_warning "Using the wrong device could damage your system!"
        echo
        exit 1
    fi

    local device=$1

    # Perform checks
    check_root
    check_gdisk
    validate_device "$device"

    # Show device information
    show_device_info "$device"

    # Check if mounted
    check_mounted "$device"

    # Fix GPT header
    fix_gpt_header "$device"

    # Verify the fix
    echo
    verify_fix "$device"

    echo
    print_success "Operation completed successfully!"
    print_info "You can now safely remove the SD card"
    echo
}

# Run main function
main "$@"
