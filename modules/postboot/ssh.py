from pathlib import Path
import subprocess
from utilities.users import get_user


def enable_ssh(boot_mount: Path):
    (boot_mount / "ssh").touch()
    print("✅ ssh file created to enable ssh.")


def setup_password_less_auth(root_mount: Path):
    username, home, user_ssh_dir, ssh_pub_key = get_user()

    # Write the key into the Pi's image
    if ssh_pub_key is not None:

        ssh_dir = root_mount / "home" / username / ".ssh"
        ssh_dir.mkdir(parents=True, exist_ok=True)

        authorized_keys = ssh_dir / "authorized_keys"
        authorized_keys.write_text(ssh_pub_key + "\n")

        authorized_keys.chmod(0o600)
        ssh_dir.chmod(0o700)
        subprocess.run(
            ["chown", "-R", f"{username}:{username}", str(ssh_dir)], check=True
        )
        print("✅ SSH key written to image.")
        return True
    else:
        print("⚠️  No SSH key found. skipping password less auth setup")
        return False
