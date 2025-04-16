#!/usr/bin/env python3

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


def get_user():
    # Use SUDO_USER if available; fallback to current user
    real_user = os.environ.get("SUDO_USER") or os.getlogin()
    home_dir = Path(f"/home/{real_user}") if real_user != "root" else Path.home()
    ssh_dir = home_dir / ".ssh"
    ssh_pub_key_path = ssh_dir / "id_rsa.pub"
    ssh_pub_key = ""
    if ssh_pub_key_path.exists():
        ssh_pub_key = ssh_pub_key_path.read_text().strip()
    return real_user, home_dir, ssh_dir, ssh_pub_key


def ensure_symlink(source, target):
    if target.exists() or target.is_symlink():
        if target.is_symlink():
            # If it's already the correct symlink, do nothing
            if os.readlink(target) == source:
                return
            else:
                target.unlink()  # Remove wrong symlink
        else:
            raise FileExistsError(f"{target} already exists and is not a symlink")

    os.symlink(source, target)


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


def mount_device(device: str, mount_point: str, retry_count: int = 3) -> bool:
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


def generate_userconf(username: str, password: str) -> str:
    result = subprocess.run(
        ["openssl", "passwd", "-6", password],
        stdout=subprocess.PIPE,
        text=True,
        check=True,
    )
    return f"{username}:{result.stdout.strip()}"


def setup_post_flash_actions(device: str) -> None:
    boot_mount = Path("/tmp/pi_flash/boot")
    root_mount = Path("/tmp/pi_flash/root")
    scripts_src = Path("resources/scripts")
    systemd_service_src = Path("resources/services/postboot.service")
    username, home, user_ssh_dir, ssh_pub_key = get_user()

    # Ensure required files exist
    if not scripts_src.exists():
        sys.exit(f"Error: {scripts_src} not found.")
    if not systemd_service_src.exists():
        sys.exit(f"Error: {systemd_service_src} not found.")

    # Mount partitions of the Raspberry Pi
    boot_mount.mkdir(parents=True, exist_ok=True)
    root_mount.mkdir(parents=True, exist_ok=True)
    mount_device(f"{device}1", str(boot_mount))
    mount_device(f"{device}2", str(root_mount))

    # 1. Copy post-boot scripts
    scripts_dest = root_mount / "post-boot"
    shutil.copytree(scripts_src, scripts_dest, dirs_exist_ok=True)

    # Make all scripts executable
    for root, dirs, files in os.walk(scripts_dest):
        for file in files:
            (Path(root) / file).chmod(0o755)

    # 2. Setup systemd service
    systemd_dir = root_mount / "etc/systemd/system"
    wants_dir = systemd_dir / "multi-user.target.wants"
    service_target = systemd_dir / "postboot.service"
    symlink_target = wants_dir / "postboot.service"

    # 3. Disable Pi first-boot wizard by creating userconf in /boot
    userconf_path = boot_mount / "userconf"
    userconf_content = generate_userconf(username, "123")
    userconf_path.write_text(userconf_content)
    print("✅ userconf file created to skip Pi first-boot setup wizard.")

    # 4. Enable ssh
    (boot_mount / "ssh").touch()
    print("✅ ssh file created to enable ssh.")

    # 5. Enable passwordless ssh access
    # Get your current user's home directory
    pubkey_files = ["id_rsa.pub", "id_ed25519.pub", "id_ecdsa.pub", "id_dsa.pub"]

    public_key = None
    for key_file in pubkey_files:
        key_path = user_ssh_dir / key_file
        if key_path.exists():
            public_key = key_path.read_text().strip()
            print(f"Using SSH key: {key_file}")
            break

    if public_key is None:
        raise FileNotFoundError("No public SSH key found in ~/.ssh")

    # Write the key into the Pi's image
    ssh_dir = root_mount / "home" / username / ".ssh"
    ssh_dir.mkdir(parents=True, exist_ok=True)

    authorized_keys = ssh_dir / "authorized_keys"
    authorized_keys.write_text(public_key + "\n")

    authorized_keys.chmod(0o600)
    ssh_dir.chmod(0o700)
    subprocess.run(["chown", "-R", f"{username}:{username}", str(ssh_dir)], check=True)
    print("✅ SSH key written to image.")

    # 6. Setup Wifi
    wpa_supplicant = boot_mount / "wpa_supplicant.conf"
    WIFI_SSID = "JACKSON_PRIVATE_NETWORK"
    WIFI_PASSWORD = "secret_pass"
    wpa_supplicant.write_text(f"""country=IN
    ctrl_interface=DIR=/var/run/wpa_supplicant GROUP=netdev
    update_config=1

    network={{
        ssid="{WIFI_SSID}"
        psk="{WIFI_PASSWORD}"
    }}
    """)

    # Ensure directories exist
    systemd_dir.mkdir(parents=True, exist_ok=True)
    wants_dir.mkdir(parents=True, exist_ok=True)

    # Copy the service file
    shutil.copy(systemd_service_src, service_target)

    # Symlink it to enable the service
    if not symlink_target.exists():
        ensure_symlink("/etc/systemd/system/postboot.service", symlink_target)

    # Unmount and done
    unmount_device(device)
    print("✅ post-boot scripts and systemd service installed successfully.")


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
