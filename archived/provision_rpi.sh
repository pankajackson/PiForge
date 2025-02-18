#!/bin/bash

set -e

# Directories and file paths
download_dir="./images"
mkdir -p "$download_dir"
raspios_lite_img="$download_dir/raspios_lite_armhf_latest.img"
raspios_lite_img_url="https://downloads.raspberrypi.com/raspios_lite_armhf_latest"
raspios_lite_img_xz="$download_dir/raspios_lite_armhf_latest.img.xz"
root_partition_mount="/tmp/pi_flash/root"
post_boot_script="./post-boot.sh"

# Ensure required commands are available
for cmd in wget xz lsblk dd grep awk cp systemctl sudo mount; do
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
        if ! xzcat "$raspios_lite_img_xz" | sudo dd of="$flash_device" bs=4M status=progress conv=fsync; then
            echo "Error during image flashing."
            exit 1
        fi
    else
        sudo dd if="$raspios_lite_img" of="$flash_device" bs=4M status=progress conv=fsync
    fi

    sync
    echo "Installation complete! You can now eject the microSD card."
}

# Function to copy post-boot script and systemd unit file
setup_post_boot_script() {
    echo "Copying post-boot.sh script to the root partition..."

    if [ ! -f "$post_boot_script" ]; then
        echo "Error: $post_boot_script not found."
        exit 1
    fi

    # Mount the root partition of the flashed device
    mkdir -p "$root_partition_mount"
    sudo mount "${flash_device}2" "$root_partition_mount"

    # Copy the post-boot.sh script to the root partition
    sudo cp "$post_boot_script" "$root_partition_mount/post-boot.sh"

    # Make the script executable
    sudo chmod +x "$root_partition_mount/post-boot.sh"

    echo "Post-boot script copied successfully!"

    # Check if the systemd service unit file exists
    if [ ! -f "./postboot.service" ]; then
        echo "Error: postboot.service not found."
        exit 1
    fi

    # Copy the systemd service file to the root partition
    sudo cp ./postboot.service "$root_partition_mount/etc/systemd/system/postboot.service"

    # Enable the systemd service by creating a symlink
    sudo ln -s "/etc/systemd/system/postboot.service" "$root_partition_mount/etc/systemd/system/multi-user.target.wants/postboot.service"

    # Unmount the root partition
    sudo umount "$root_partition_mount"

    echo "Systemd service created and enabled."
}

# Main script execution
download_image
select_device
flash_device

# setup post boot script
setup_post_boot_script

echo "Provisioning complete! Raspberry Pi is ready. Insert the SD card and boot up."
