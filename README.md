# Raspberry Pi Provisioner

This repository provides an easy-to-use script to **download, flash, and provision a flash drive** with the latest **Raspberry Pi OS Lite** for setting up a Raspberry Pi 5, specifically for **home automation services**.

### Features

- **Downloads** and **decompresses** the latest Raspberry Pi OS Lite image.
- **Automatically detects** supported block devices (e.g., SD cards, USB drives, NVMe drives).
- **Flashes the OS image** to the selected block device (e.g., microSD card or USB drive).
- **Configures** the Raspberry Pi 5 for home automation tasks.

### Requirements

- A **Raspberry Pi 5** device.
- A **flash drive** or **microSD card** for the Raspberry Pi.
- A **Linux-based machine** (e.g., Ubuntu, Arch Linux) to run the script.
- **wget**, **xz**, **lsblk**, and **dd** utilities installed.

---

## Installation

1. Clone the repository to your local machine:

```bash
git clone https://github.com/your-username/raspberry-pi-home-automation-flash.git
cd raspberry-pi-home-automation-flash
```

2. Make the script executable:

```bash
chmod +x provision_rpi.sh
```

---

## Usage

### Step 1: Run the Script

Execute the script to flash the Raspberry Pi OS Lite image to your device.

```bash
./provision_rpi.sh
```

### Step 2: Follow the Interactive Prompts

- **Step 1:** The script will first check if the required image (`raspios_lite_armhf_latest.img`) is already downloaded.
- **Step 2:** If not, the script will download and decompress the latest Raspberry Pi OS Lite image for you.
- **Step 3:** The script will list available storage devices, such as microSD cards, USB flash drives, and NVMe drives, and ask you to select the device to flash.
- **Step 4:** The script will then **unmount** any existing partitions on the device and **flash** the OS image to the selected device.

> **WARNING:** This process will erase all data on the selected device!

---

## Supported Devices

The script automatically detects removable storage devices connected to your machine. These include:

- **SD cards** (e.g., `/dev/mmcblkX`).
- **USB flash drives** (e.g., `/dev/sdX`).
- **NVMe drives** (e.g., `/dev/nvmeXnY`).

Make sure that the device you select is a removable block device and that it is not your system disk.

---

## Troubleshooting

- **No supported devices found:**  
  Ensure that your flash drive or microSD card is properly connected to your machine. The script lists only removable storage devices, so make sure you aren't trying to select your system disk.

- **Script not working on your OS:**  
  The script is designed for **Linux-based systems**. Make sure you have the necessary utilities installed:
- `wget`
- `xz`
- `lsblk`
- `dd`

If any of these commands are missing, the script will not function properly. You can install them using your system's package manager.

---

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

---

### Contributors

- **Your Name** – _Author and Maintainer_
- **Contributions welcome!** Feel free to fork the repository and submit pull requests.

---

### Contact

For any questions or issues, please open an issue on this repository.
