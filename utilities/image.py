import subprocess
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
