import shutil
import os
import sys


def ensure_commands_available(commands: list[str]) -> None:
    for cmd in commands:
        if not shutil.which(cmd):
            sys.exit(
                f"Error: Required command '{cmd}' is missing. Install it and try again."
            )

def ensure_symlink(source, target):
    if target.exists() or target.is_symlink():
        if target.is_symlink():
            # If it's already the correct symlink, do nothing
            if os.readlink(target) == source:
                return
            else:
                target.unlink()  # Remove wrong symlink
        else:
            raise FileExistsError(f"{target} already exists and is not a symlink")

    os.symlink(source, target)
