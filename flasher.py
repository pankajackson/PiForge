import os
import shutil
import subprocess
import sys
from pathlib import Path
from dataclasses import dataclass
from enum import Enum


class ImageArch(Enum):
    ARM64 = "_arm64"
    ARM32 = "_armhf"


class ImageType(Enum):
    DESKTOP = ""
    LITE = "_lite"
    FULL = "_full"


@dataclass
class Image:
    arch: ImageArch
    type: ImageType
    name: str
    file: str
    xz_file: str
    url: str


def ensure_commands_available(commands: list[str]) -> None:
    for cmd in commands:
        if not shutil.which(cmd):
            sys.exit(
                f"Error: Required command '{cmd}' is missing. Install it and try again."
            )


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


def select_image(
    img_arch: ImageArch | None = None,
    img_type: ImageType | None = None,
) -> Image:
    while not img_arch:
        available_arch = list(ImageArch.__members__.keys())
        for idx, arch in enumerate(available_arch):
            print(f"{idx + 1}. {arch}")
        print("Please select an image architecture:")
        try:
            selected_arch = int(input()) - 1  # Adjust for 1-based index
            img_arch = ImageArch[available_arch[selected_arch]]
        except (ValueError, IndexError):
            print("Invalid image architecture. Please try again.")
            continue

    while not img_type:
        available_type = list(ImageType.__members__.keys())
        for idx, type in enumerate(available_type):
            print(f"{idx + 1}. {type}")
        print("Please select an image type:")
        try:
            selected_type = int(input()) - 1  # Adjust for 1-based index
            img_type = ImageType[available_type[selected_type]]
        except (ValueError, IndexError):
            print("Invalid image type. Please try again.")
            continue
    img_name = f"raspios{img_type.value}{img_arch.value}_latest"
    img_file = f"{img_name}.img"
    img_xz_file = f"{img_name}.img.xz"
    img_url = f"https://downloads.raspberrypi.com/{img_name}"
    os_image = Image(
        arch=img_arch,
        type=img_type,
        name=img_name,
        file=img_file,
        xz_file=img_xz_file,
        url=img_url,
    )
    return os_image


def download_image(image: Image, download_dir: Path) -> Path:
    img_path = download_dir / image.file
    img_xz_path = download_dir / image.xz_file

    if img_path.exists():
        print(f"Using cached {img_path}")
        return img_path

    print("Downloading Raspberry Pi OS Lite...")
    subprocess.run(["wget", "-O", str(img_xz_path), image.url], check=True)

    print("Decompressing the image...")
    subprocess.run(["xz", "-d", str(img_xz_path)], check=True)
    print(f"Download and decompression complete: {img_path}")

    return img_path


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


def flash_device(img_path: Path, device: str) -> None:
    confirm = input(f"WARNING: This will erase all data on {device}. Proceed? (y/N): ")
    if confirm.lower() != "y":
        sys.exit("Operation cancelled.")
    unmount_device(device)
    print(f"Flashing {img_path} to {device}...")
    with open(img_path, "rb") as img, open(device, "wb") as dev:
        shutil.copyfileobj(img, dev, length=4 * 1024 * 1024)
    print("Installation complete!")


def setup_post_flash_actions(device: str) -> None:
    root_mount = Path("/tmp/pi_flash/root")
    post_boot_script = Path("resources/post-boot.sh")
    systemd_service = Path("resources/postboot.service")

    # Setup postboot script
    if not post_boot_script.exists():
        sys.exit(f"Error: {post_boot_script} not found.")

    root_mount.mkdir(parents=True, exist_ok=True)
    subprocess.run(["sudo", "mount", f"{device}2", str(root_mount)], check=True)
    shutil.copy(post_boot_script, root_mount / "post-boot.sh")
    (root_mount / "post-boot.sh").chmod(0o755)

    # Setup systemd service
    if not systemd_service.exists():
        sys.exit(f"Error: {systemd_service} not found.")

    shutil.copy(systemd_service, root_mount / "etc/systemd/system/postboot.service")
    os.symlink(
        "/etc/systemd/system/postboot.service",
        root_mount / "etc/systemd/system/multi-user.target.wants/postboot.service",
    )
    unmount_device(device)
    print("Post-boot script and systemd service setup complete.")


def main() -> None:
    ensure_commands_available(["wget", "xz", "dd", "mount", "umount"])
    download_dir = Path("./images")
    download_dir.mkdir(exist_ok=True)
    image = select_image()
    device = select_device()
    img_path = download_image(image, download_dir)
    flash_device(img_path, device)
    setup_post_flash_actions(device)
    print(
        "Provisioning complete! Raspberry Pi is ready. Insert the SD card and boot up."
    )


if __name__ == "__main__":
    main()
