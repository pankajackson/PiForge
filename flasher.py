import os
import time
import shutil
import subprocess
import sys
from pathlib import Path
from dataclasses import dataclass
from enum import Enum


class OSFlavor(Enum):
    RASPBERRY_PI_OS = "raspios"
    ARCH_LINUX_ARM = "archlinuxarm"


class ImageArch(Enum):
    ARM64 = "_arm64"
    ARM32 = "_armhf"


class ImageType(Enum):
    DESKTOP = ""
    LITE = "_lite"
    FULL = "_full"
    BASE = "_base"  # For Arch Linux ARM


@dataclass
class Image:
    flavor: OSFlavor
    arch: ImageArch
    type: ImageType
    name: str
    file: str
    xz_file: str
    tar_file: str
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


def mount_device(device: str, retry_count=3) -> tuple[Path, Path]:
    """Mount the boot and root partitions of a device with retries."""
    boot_partition = f"{device}1" if device.startswith("/dev/sd") else f"{device}p1"
    root_partition = f"{device}2" if device.startswith("/dev/sd") else f"{device}p2"
    boot_mount = Path("/tmp/pi_flash/boot")
    root_mount = Path("/tmp/pi_flash/root")

    # Ensure mount points exist
    boot_mount.mkdir(parents=True, exist_ok=True)
    root_mount.mkdir(parents=True, exist_ok=True)

    for attempt in range(1, retry_count + 1):
        try:
            if not is_device_mounted(boot_partition):
                subprocess.run(
                    ["sudo", "mount", boot_partition, str(boot_mount)], check=True
                )

            if not is_device_mounted(root_partition):
                subprocess.run(
                    ["sudo", "mount", root_partition, str(root_mount)], check=True
                )

            return boot_mount, root_mount
        except subprocess.CalledProcessError:
            print(
                f"Attempt {attempt}/{retry_count}: Failed to mount {device}. Retrying..."
            )
            time.sleep(2)

    sys.exit(f"Error: Failed to mount '{device}' after {retry_count} attempts.")


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
                subprocess.run(["sudo", "umount", "-f", partition], check=True)
                print(f"Unmounted {partition} successfully.")

            return True  # Successfully unmounted, exit function

        except subprocess.CalledProcessError:
            print(
                f"Failed to unmount {device}. Retrying ({attempt + 1}/{retry_count})..."
            )

    print(f"Error: Failed to unmount {device} after {retry_count} attempts. Exiting.")
    sys.exit(1)  # Exit after all retries fail


def select_image(
    os_flavor: OSFlavor | None = None,
    img_arch: ImageArch | None = None,
    img_type: ImageType | None = None,
) -> Image:
    while not os_flavor:
        available_os = list(OSFlavor.__members__.keys())
        for idx, os_name in enumerate(available_os):
            print(f"{idx + 1}. {os_name}")
        print("Please select an OS flavor:")
        try:
            selected_os = int(input()) - 1
            os_flavor = OSFlavor[available_os[selected_os]]
        except (ValueError, IndexError):
            print("Invalid OS selection. Try again.")
            continue

    while not img_arch:
        available_arch = list(ImageArch.__members__.keys())
        for idx, arch in enumerate(available_arch):
            print(f"{idx + 1}. {arch}")
        print("Please select an image architecture:")
        try:
            selected_arch = int(input()) - 1
            img_arch = ImageArch[available_arch[selected_arch]]
        except (ValueError, IndexError):
            print("Invalid image architecture. Try again.")
            continue

    img_type = ImageType.BASE if os_flavor == OSFlavor.ARCH_LINUX_ARM else img_type
    while not img_type:
        available_types = list(ImageType.__members__.keys())
        for idx, type_name in enumerate(available_types):
            print(f"{idx + 1}. {type_name}")
        print("Please select an image type:")
        try:
            selected_type = int(input()) - 1
            img_type = ImageType[available_types[selected_type]]
        except (ValueError, IndexError):
            print("Invalid image type. Try again.")
            continue

    img_name = f"{os_flavor.value}{img_type.value}{img_arch.value}_latest"
    img_file = f"{img_name}.img"
    img_xz_file = f"{img_name}.img.xz"
    img_tar_file = f"{img_name}.tar.gz"

    # Define URLs based on OS selection
    if os_flavor == OSFlavor.RASPBERRY_PI_OS:
        img_url = f"https://downloads.raspberrypi.com/{img_name}"
    else:
        # Arch Linux ARM URL structure (assuming AArch64 for Raspberry Pi 4/5)
        if img_arch == ImageArch.ARM64:
            img_url = "https://archlinuxarm.org/os/ArchLinuxARM-aarch64-latest.tar.gz"
        else:
            img_url = "https://archlinuxarm.org/os/ArchLinuxARM-rpi-latest.tar.gz"

    return Image(
        flavor=os_flavor,
        arch=img_arch,
        type=img_type,
        name=img_name,
        file=img_file,
        xz_file=img_xz_file,
        tar_file=img_tar_file,
        url=img_url,
    )


def download_image(image: Image, download_dir: Path) -> Path:
    img_path = download_dir / image.file
    img_xz_path = download_dir / image.xz_file
    img_tar_path = download_dir / (image.tar_file)

    if img_path.exists() or img_tar_path.exists():
        img = img_path if img_path.exists() else img_tar_path
        print(f"Using cached {img}")
        return img

    print(f"Downloading {image.name}...")
    subprocess.run(
        [
            "wget",
            "-O",
            str(
                img_xz_path
                if image.flavor == OSFlavor.RASPBERRY_PI_OS
                else img_tar_path
            ),
            image.url,
        ],
        check=True,
    )

    if image.flavor == OSFlavor.RASPBERRY_PI_OS:
        print("Decompressing the image...")
        subprocess.run(["xz", "-d", str(img_xz_path)], check=True)
        return img_path
    else:
        return img_tar_path  # Arch Linux ARM uses tar.gz


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


def flash_device(img_path: Path, device: str, os_flavor: OSFlavor) -> None:
    confirm = input(f"WARNING: This will erase all data on {device}. Proceed? (y/N): ")
    if confirm.lower() != "y":
        sys.exit("Operation cancelled.")

    unmount_device(device)

    if os_flavor == OSFlavor.RASPBERRY_PI_OS:
        print(f"Flashing {img_path} to {device}...")
        subprocess.run(
            [
                "sudo",
                "dd",
                f"if={img_path}",
                f"of={device}",
                "bs=4M",
                "status=progress",
            ],
            check=True,
        )
        print("Installation complete!")
    else:
        print("Flashing Arch Linux ARM...")

        # Clear any existing partition table
        subprocess.run(["sudo", "sgdisk", "--zap-all", device], check=True)
        time.sleep(2)  # Give some time for the system to recognize changes

        # Create partitions
        subprocess.run(
            ["sudo", "sgdisk", "-n", "1:1MiB:+512MiB", "-t", "1:ef00", device],
            check=True,
        )  # Boot partition (EFI System Partition)
        subprocess.run(
            ["sudo", "sgdisk", "-n", "2:0:0", "-t", "2:8300", device], check=True
        )  # Root partition (Linux Filesystem)

        # Reload partition table
        subprocess.run(["sudo", "partprobe", device], check=True)
        time.sleep(2)

        # Format partitions
        boot_partition = f"{device}1" if device.startswith("/dev/sd") else f"{device}p1"
        root_partition = f"{device}2" if device.startswith("/dev/sd") else f"{device}p2"

        subprocess.run(
            ["sudo", "mkfs.vfat", "-F32", boot_partition], check=True
        )  # Format boot partition as FAT32
        subprocess.run(
            ["sudo", "mkfs.ext4", "-F", root_partition], check=True
        )  # Format root partition as ext4

        # Mount partitions and extract image
        boot_dir, root_dir = mount_device(device)
        subprocess.run(["tar", "-xzf", str(img_path), "-C", str(root_dir)], check=True)

        # Copy boot files
        shutil.copytree(root_dir / "boot", boot_dir, dirs_exist_ok=True)

        # Unmount the device
        unmount_device(device)

        print("Arch Linux ARM installation complete!")


def setup_post_flash_actions(device: str) -> None:
    root_partition = f"{device}2" if device.startswith("/dev/sd") else f"{device}p2"
    root_mount = Path("/tmp/pi_flash/root")
    post_boot_script = Path("resources/post-boot.sh")
    systemd_service = Path("resources/postboot.service")

    # Setup postboot script
    if not post_boot_script.exists():
        sys.exit(f"Error: {post_boot_script} not found.")

    root_mount.mkdir(parents=True, exist_ok=True)
    subprocess.run(["sudo", "mount", root_partition, str(root_mount)], check=True)
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
    ensure_commands_available(["wget", "xz", "dd", "mount", "umount", "tar", "parted"])

    download_dir = Path("./images")
    download_dir.mkdir(exist_ok=True)

    image = select_image()
    device = select_device()

    img_path = download_image(image, download_dir)

    flash_device(img_path, device, image.flavor)

    if image.flavor == OSFlavor.RASPBERRY_PI_OS:
        setup_post_flash_actions(device)

    print("Flashing completed successfully!")


if __name__ == "__main__":
    main()
