import os
import shutil
from pathlib import Path
from jinja2 import Environment, FileSystemLoader

current_dir = Path(os.path.dirname(os.path.abspath(__file__)))


def generate_firstrun_script(
    hostname: str,
    new_user: str,
    password_hash: str,
    ssh_public_key: str,
    wifi_country: str,
    wifi_ssid: str,
    wifi_psk: str,
    timezone: str,
):
    env = Environment(loader=FileSystemLoader(current_dir))
    template = env.get_template("firstrun.sh.j2")

    config = {
        "hostname": hostname,
        "new_user": new_user,
        "password_hash": password_hash,
        "ssh_public_key": ssh_public_key,
        "wifi_country": wifi_country,
        "wifi_ssid": wifi_ssid,
        "wifi_psk": wifi_psk,
        "timezone": timezone,
    }

    rendered_script = template.render(config)
    return rendered_script


def setup_firstrun(script: str, script_dir: Path) -> None:

    script_file_name = "firstrun.sh"
    output_script_path = script_dir / script_file_name

    with open(output_script_path, "w") as f:
        f.write(script)
    output_script_path.chmod(0o755)
    shutil.copyfile(current_dir / "cmdline.txt", script_dir / "cmdline.txt")

    print("✅ First boot actions complete!")
