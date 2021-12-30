import re
import subprocess
from pathlib import Path
from typing import List


class BranchNotFound(Exception):
    pass


def get_current_branch() -> str:
    command_current = ["git", "rev-parse", "--abbrev-ref", "HEAD"]
    return subprocess.check_output(command_current).strip().decode()


def check_branch_exists(branch: str) -> None:
    try:
        command_check = ["git", "rev-parse", "--verify", branch]
        subprocess.check_output(command_check)
    except subprocess.CalledProcessError:
        raise BranchNotFound(f"Cannot find branch {branch}. Aborting.")


def get_branch_modified_addons(branch: str, addons_dirs: List[Path]) -> List[str]:
    check_branch_exists(branch)
    current_branch = get_current_branch()
    command_modified = ["git", "diff", "--name-only", branch, current_branch]
    modified_files = subprocess.check_output(command_modified).decode().split()
    modified_addons = set()
    for file_name in modified_files:
        prefix = next(
            (str(p) for p in addons_dirs if file_name.startswith(str(p))), None
        )
        if prefix:
            addon_file = re.sub(prefix, "", file_name)
            folder = re.sub("/.*", "", re.sub("^/", "", addon_file))
            modified_addons.add(folder)
    return list(modified_addons)
