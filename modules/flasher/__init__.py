from pathlib import Path
import sys
import shutil


def flash_device(img_path: Path, device: str) -> None:
    confirm = input(f"WARNING: This will erase all data on {device}. Proceed? (y/N): ")
    if confirm.lower() != "y":
        sys.exit("Operation cancelled.")
    print(f"Flashing {img_path} to {device}...")
    with open(img_path, "rb") as img, open(device, "wb") as dev:
        shutil.copyfileobj(img, dev, length=4 * 1024 * 1024)
    print("✅ Installation complete!")
