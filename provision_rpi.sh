#!/bin/bash

set -e

# Directories and file paths
download_dir="./images"
mkdir -p "$download_dir"
raspios_lite_img="$download_dir/raspios_lite_armhf_latest.img"
raspios_lite_img_url="https://downloads.raspberrypi.com/raspios_lite_armhf_latest"
raspios_lite_img_xz="$download_dir/raspios_lite_armhf_latest.img.xz"

# Ensure required commands are available
for cmd in wget xz lsblk dd grep awk; do
    if ! command -v "$cmd" &>/dev/null; then
        echo "Error: Required command '$cmd' is missing. Install it and try again."
        exit 1
    fi
done

# Function to download and extract the OS image
download_image() {
    if [ -f "$raspios_lite_img" ]; then
        echo "Using cached $raspios_lite_img"
        return
    fi

    echo "Downloading Raspberry Pi OS Lite..."
    wget -O "$raspios_lite_img_xz" "$raspios_lite_img_url" || {
        echo "Download failed"
        exit 1
    }

    echo "Decompressing the image..."
    xz -d "$raspios_lite_img_xz" || {
        echo "Decompression failed"
        exit 1
    }

    rm -f "$raspios_lite_img_xz"
    echo "Download and decompression complete: $raspios_lite_img"
}

# Function to select a device
select_device() {
    echo "Detecting removable storage devices..."

    # Get removable devices (excluding root/system disks)
    mapfile -t supported_devices < <(lsblk -dpno NAME,TRAN | awk '$2 == "usb" {print $1}')

    if [ ${#supported_devices[@]} -eq 0 ]; then
        echo "No removable storage devices found!"
        exit 1
    fi

    echo "Available devices:"
    select flash_device in "${supported_devices[@]}"; do
        if [[ -n "$flash_device" ]]; then
            echo "Selected device: $flash_device"
            break
        else
            echo "Invalid selection. Try again."
        fi
    done
}

# Function to flash the OS image
flash_device() {
    read -rp "WARNING: This will erase all data on $flash_device. Proceed? (y/N): " confirm
    if [[ ! "$confirm" =~ ^[Yy]$ ]]; then
        echo "Operation cancelled."
        exit 1
    fi

    echo "Unmounting partitions on $flash_device..."
    sudo umount "${flash_device}"* || true

    echo "Flashing $raspios_lite_img to $flash_device..."

    # Stream decompression directly into dd to avoid unnecessary disk writes
    if [[ -f "$raspios_lite_img_xz" ]]; then
        xzcat "$raspios_lite_img_xz" | sudo dd of="$flash_device" bs=4M status=progress conv=fsync
    else
        sudo dd if="$raspios_lite_img" of="$flash_device" bs=4M status=progress conv=fsync
    fi

    sync
    echo "Installation complete! You can now eject the microSD card."
}

# Main script execution
download_image
select_device
flash_device
