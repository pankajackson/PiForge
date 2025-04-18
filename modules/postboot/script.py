import os
import sys
import shutil
from pathlib import Path
from utilities.users import get_user
from utilities.system import ensure_symlink


def get_service_path(root_mount: Path):
    current_dir = Path(os.path.dirname(os.path.abspath(__file__)))

    scripts_src = current_dir / "resources" / "scripts"
    systemd_service_src = current_dir / "resources" / "services" / "postboot.service"

    systemd_dir = root_mount / "etc/systemd/system"
    wants_dir = systemd_dir / "multi-user.target.wants"
    service_target = systemd_dir / "postboot.service"
    symlink_target = wants_dir / "postboot.service"

    return (
        scripts_src,
        systemd_service_src,
        systemd_dir,
        wants_dir,
        service_target,
        symlink_target,
    )


def install_script(root_mount: Path):
    (scripts_src, systemd_service_src, _, _, _, _) = get_service_path(root_mount)
    # Ensure required files exist
    if not scripts_src.exists():
        sys.exit(f"Error: {scripts_src} not found.")
    if not systemd_service_src.exists():
        sys.exit(f"Error: {systemd_service_src} not found.")

    # 1. Copy post-boot scripts
    scripts_dest = root_mount / "post-boot"
    shutil.copytree(scripts_src, scripts_dest, dirs_exist_ok=True)

    # Make all scripts executable
    for root, dirs, files in os.walk(scripts_dest):
        for file in files:
            (Path(root) / file).chmod(0o755)


def install_post_boot_service(root_mount: Path):
    (_, systemd_service_src, systemd_dir, _, service_target, _) = get_service_path(
        root_mount
    )

    install_script(root_mount)
    systemd_dir.mkdir(parents=True, exist_ok=True)
    shutil.copy(systemd_service_src, service_target)


def enable_post_boot_service(root_mount: Path):
    (_, _, _, wants_dir, _, symlink_target) = get_service_path(root_mount)
    wants_dir.mkdir(parents=True, exist_ok=True)
    if not symlink_target.exists():
        ensure_symlink("/etc/systemd/system/postboot.service", symlink_target)
