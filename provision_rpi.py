import os
import subprocess
import sys
import shutil

download_dir = "./images"
os.makedirs(download_dir, exist_ok=True)

raspios_lite_img = os.path.join(download_dir, "raspios_lite_armhf_latest.img")
raspios_lite_img_url = "https://downloads.raspberrypi.com/raspios_lite_armhf_latest"
raspios_lite_img_xz = os.path.join(download_dir, "raspios_lite_armhf_latest.img.xz")
root_partition_mount = "/tmp/pi_flash/root"
post_boot_script = "./post-boot.sh"

required_cmds = [
    "wget",
    "xz",
    "lsblk",
    "dd",
    "grep",
    "awk",
    "cp",
    "systemctl",
    "sudo",
    "mount",
]


def check_commands():
    for cmd in required_cmds:
        if not shutil.which(cmd):
            print(
                f"Error: Required command '{cmd}' is missing. Install it and try again."
            )
            sys.exit(1)


def run_command(command, check=True):
    try:
        subprocess.run(command, shell=True, check=check)
    except subprocess.CalledProcessError as e:
        print(f"Error executing command: {e}")
        sys.exit(1)


def download_image():
    if os.path.isfile(raspios_lite_img):
        print(f"Using cached {raspios_lite_img}")
        return

    print("Downloading Raspberry Pi OS Lite...")
    run_command(f"wget -O {raspios_lite_img_xz} {raspios_lite_img_url}")

    print("Decompressing the image...")
    run_command(f"xz -d {raspios_lite_img_xz}")

    os.remove(raspios_lite_img_xz)
    print(f"Download and decompression complete: {raspios_lite_img}")


def select_device():
    print("Detecting removable storage devices...")
    result = subprocess.run(
        "lsblk -dpno NAME,TRAN | awk '$2 == \"usb\" {print $1}'",
        shell=True,
        capture_output=True,
        text=True,
    )
    devices = result.stdout.strip().split("\n")

    if not devices or devices == [""]:
        print("No removable storage devices found!")
        sys.exit(1)

    print("Available devices:")
    for i, dev in enumerate(devices, 1):
        print(f"{i}. {dev}")

    while True:
        choice = input("Select a device by number: ")
        if choice.isdigit() and 1 <= int(choice) <= len(devices):
            return devices[int(choice) - 1]
        print("Invalid selection. Try again.")


def flash_device(flash_device):
    confirm = (
        input(f"WARNING: This will erase all data on {flash_device}. Proceed? (y/N): ")
        .strip()
        .lower()
    )
    if confirm != "y":
        print("Operation cancelled.")
        sys.exit(1)

    print(f"Unmounting partitions on {flash_device}...")
    run_command(f"sudo umount {flash_device}*", check=False)

    print(f"Flashing {raspios_lite_img} to {flash_device}...")
    run_command(
        f"sudo dd if={raspios_lite_img} of={flash_device} bs=4M status=progress conv=fsync"
    )
    run_command("sync")
    print("Installation complete! You can now eject the microSD card.")


def setup_post_boot_script(flash_device):
    print("Copying post-boot.sh script to the root partition...")
    if not os.path.isfile(post_boot_script):
        print(f"Error: {post_boot_script} not found.")
        sys.exit(1)

    os.makedirs(root_partition_mount, exist_ok=True)
    run_command(f"sudo mount {flash_device}2 {root_partition_mount}")

    run_command(f"sudo cp {post_boot_script} {root_partition_mount}/post-boot.sh")
    run_command(f"sudo chmod +x {root_partition_mount}/post-boot.sh")

    print("Post-boot script copied successfully!")

    if not os.path.isfile("./postboot.service"):
        print("Error: postboot.service not found.")
        sys.exit(1)

    run_command(
        f"sudo cp ./postboot.service {root_partition_mount}/etc/systemd/system/postboot.service"
    )
    run_command(
        f"sudo ln -s /etc/systemd/system/postboot.service {root_partition_mount}/etc/systemd/system/multi-user.target.wants/postboot.service"
    )

    run_command(f"sudo umount {root_partition_mount}")
    print("Systemd service created and enabled.")


if __name__ == "__main__":
    check_commands()
    download_image()
    device = select_device()
    flash_device(device)
    setup_post_boot_script(device)
    print(
        "Provisioning complete! Raspberry Pi is ready. Insert the SD card and boot up."
    )
