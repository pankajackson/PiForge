import subprocess
import sys
from pathlib import Path


def is_device_mounted(device: str) -> bool:
    """Check if a device is mounted."""
    result = subprocess.run(["mount"], capture_output=True, text=True)
    return any(device in line for line in result.stdout.splitlines())


def unmount_device(device: str, retry_count=3) -> bool:
    """Unmount the device safely if it is mounted."""
    if not is_device_mounted(device):
        # print(f"{device} is not mounted. Skipping unmount.")
        return True  # No need to unmount

    for attempt in range(retry_count):
        try:
            # Get all mounted partitions related to the device
            result = subprocess.run(["mount"], capture_output=True, text=True)
            mounted_partitions = [
                line.split()[0] for line in result.stdout.splitlines() if device in line
            ]

            if not mounted_partitions:
                print(f"{device} is not mounted. Skipping unmount.")
                return True

            # Unmount each partition
            for partition in mounted_partitions:
                subprocess.run(["sudo", "umount", "-l", partition], check=True)
                print(f"Unmounted {partition} successfully.")

            return True  # Successfully unmounted, exit function

        except subprocess.CalledProcessError:
            print(
                f"Failed to unmount {device}. Retrying ({attempt + 1}/{retry_count})..."
            )

    print(f"Error: Failed to unmount {device} after {retry_count} attempts. Exiting.")
    sys.exit(1)  # Exit after all retries fail


def mount_device(device: str, mount_point: Path, retry_count: int = 3) -> bool:
    mount_point.mkdir(parents=True, exist_ok=True)
    for attempt in range(1, retry_count + 1):
        try:
            if is_device_mounted(device):
                print(f"{device} is already mounted.")
                return True

            subprocess.run(["sudo", "mount", device, mount_point], check=True)
            print(f"Mounted {device} to {mount_point}.")
            return True

        except subprocess.CalledProcessError:
            print(
                f"Attempt {attempt}/{retry_count} failed to mount {device}. Retrying..."
            )

    print(f"Error: Failed to mount {device} after {retry_count} attempts.")
    return False


def list_removable_devices() -> list[str]:
    devices: list[str] = []
    try:
        result = subprocess.run(
            ["lsblk", "-dpno", "NAME,TRAN"], capture_output=True, text=True, check=True
        )
        for line in result.stdout.strip().split("\n"):
            parts = line.split()
            if len(parts) == 2 and parts[1] == "usb":
                devices.append(parts[0])
    except subprocess.CalledProcessError:
        sys.exit("Error: Failed to retrieve storage device information.")

    return devices


def select_device() -> str:
    devices = list_removable_devices()
    if not devices:
        sys.exit("No removable storage devices found!")

    print("Available devices:")
    for idx, device in enumerate(devices, start=1):
        print(f"{idx}. {device}")

    while True:
        choice = input("Select a device: ")
        if choice.isdigit() and 1 <= int(choice) <= len(devices):
            return devices[int(choice) - 1]
        print("Invalid selection. Try again.")
