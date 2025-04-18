import os
from pathlib import Path
import subprocess
# import crypt
import random
import string
from passlib.hash import sha256_crypt


def get_user():
    # Use SUDO_USER if available; fallback to current user
    real_user = os.environ.get("SUDO_USER") or os.getlogin()
    home_dir = Path(f"/home/{real_user}") if real_user != "root" else Path.home()
    ssh_dir = home_dir / ".ssh"

    pubkey_files = ["id_rsa.pub", "id_ed25519.pub", "id_ecdsa.pub", "id_dsa.pub"]

    ssh_pub_key = None
    for key_file in pubkey_files:
        key_path = ssh_dir / key_file
        if key_path.exists():
            ssh_pub_key = key_path.read_text().strip()
            print(f"Using SSH key: {key_file}")
            break

    return real_user, home_dir, ssh_dir, ssh_pub_key


def generate_userconf(username: str, password: str) -> str:
    result = subprocess.run(
        ["openssl", "passwd", "-6", password],
        stdout=subprocess.PIPE,
        text=True,
        check=True,
    )
    return f"{username}:{result.stdout.strip()}"


def generate_encrypted_password(password: str, salt: str | None = None) -> str:
    if not salt:
        # Raspberry Pi 5 once used ""5dToro4/mP"
        salt = "".join(random.choices(string.ascii_letters + string.digits, k=8))

    return sha256_crypt.using(salt=salt, rounds=5000).hash(password)
