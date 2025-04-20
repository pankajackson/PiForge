from pathlib import Path
from utilities.users import generate_userconf, get_user


def create_user(
    boot_mount: Path, username: str | None = None, password: str | None = None
):
    if username is None:
        username, _, _, _ = get_user()
    if password is None:
        password = "raspberry"
    userconf_path = boot_mount / "userconf"
    userconf_content = generate_userconf(username, password)
    userconf_path.write_text(userconf_content)
    print("✅ userconf file created to skip Pi first-boot setup wizard.")
