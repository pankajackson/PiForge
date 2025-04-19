import os
from pathlib import Path
from .script import install_post_boot_service, enable_post_boot_service
from .ssh import enable_ssh, setup_password_less_auth
from .user import create_user

current_dir = Path(os.path.dirname(os.path.abspath(__file__)))


def setup_post_flash_actions(root_mount: Path, boot_mount: Path, *args, **kwargs) -> None:
    install_post_boot_service(root_mount, **kwargs)
    enable_post_boot_service(root_mount)
    # enable_ssh(boot_mount)
    # setup_password_less_auth(boot_mount)
    # create_user(boot_mount)
    print("✅ Post boot Provisioning complete!")
