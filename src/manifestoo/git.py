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


def _get_new_manifest_files(branch: str, current_branch: str) -> List[str]:
    command_new = ["git", "diff", "--name-only", "--diff-filter", "A", branch, current_branch]
    new_files = subprocess.check_output(command_new).decode().split()
    return [f for f in new_files if f.endswith("/__manifest__.py")]


def get_branch_new_addons(branch: str, addons_dirs: List[Path]) -> List[str]:
    return _get_branch_addons_by(_get_new_manifest_files, branch, addons_dirs)


def _get_modified_files(branch: str, current_branch: str) -> List[str]:
    command_modified = ["git", "diff", "--name-only", branch, current_branch]
    return subprocess.check_output(command_modified).decode().split()


def get_branch_modified_addons(branch: str, addons_dirs: List[Path]) -> List[str]:
    return _get_branch_addons_by(_get_modified_files, branch, addons_dirs)


def _get_branch_addons_by(method, branch: str, addons_dirs: List[Path]) -> List[str]:
    check_branch_exists(branch)
    current_branch = get_current_branch()
    modified = method(branch, current_branch)
    addons = set()
    for file_name in modified:
        prefix = next(
            (str(p) for p in addons_dirs if file_name.startswith(str(p))), None
        )
        if prefix:
            addon_file = re.sub(prefix, "", file_name)
            folder = re.sub("/.*", "", re.sub("^/", "", addon_file))
            addons.add(folder)
    return list(addons)
