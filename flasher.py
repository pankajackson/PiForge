#!/usr/bin/env python3

from pathlib import Path
from utilities.system import ensure_commands_available
from utilities.devices import mount_device, unmount_device, select_device
from utilities.image import select_image, download_image
from utilities.config import get_config
from modules.firstrun import generate_firstrun_script, setup_firstrun
from modules.flasher import flash_device
from modules.postboot import setup_post_flash_actions

boot_mount = Path("/tmp/pi_flash/boot")
root_mount = Path("/tmp/pi_flash/root")


def main() -> None:
    ensure_commands_available(["wget", "xz", "dd", "mount", "umount"])
    download_dir = Path("./images")
    download_dir.mkdir(exist_ok=True)
    image = select_image()
    device = select_device()
    img_path = download_image(image, download_dir)
    unmount_device(device)
    flash_device(img_path, device)
    mount_device(f"{device}1", boot_mount)
    mount_device(f"{device}2", root_mount)
    full_configs = get_config()
    fr_script = generate_firstrun_script(**full_configs)
    setup_firstrun(
        script=fr_script,
        script_dir=boot_mount,
    )
    setup_post_flash_actions(root_mount=root_mount, boot_mount=boot_mount)
    unmount_device(device)
    print("✅ Raspberry Pi is ready. Insert the SD card and boot up!")


if __name__ == "__main__":
    main()
