"""Git-based package information"""

import logging
import shutil
import subprocess
import tempfile
from typing import Tuple

from lubed import OBSCredentials, Package, Timestamp


def package_was_updated(
    last_check: Timestamp,
    package: Package,
    credentials: OBSCredentials,
    api_url: str = "",
    gitserver_url: str = "https://src.opensuse.org",
) -> Tuple[bool, bool]:
    """Check if a git-managed OBS package was updated since a known timestamp.

    The OBS package is considered updated if the last commit is newer than the known
    timestamp. To obtain the author time of the last commit, the last commit in the
    repository is cloned to a temporary directory.

    :param last_check: Unix timestamp of the last check
    :param package: OBS package to check
    :param credentials: Not used, just for API compatibility
    :param api_url: Not used, just for API compatibility
    :param gitserver_url: Base URL of the git server, defaults to https://src.opensuse.org
    :return: Tuple (bool, bool)
        - package_updated: True if package was updated, False otherwise
        - err: True if an error occured during the check, False otherwise

    """
    del credentials, api_url  # not used

    newer, err = False, True

    if not shutil.which("git"):
        raise RuntimeError(
            "'git' not found. Please check that it's available in $PATH."
        )

    with tempfile.TemporaryDirectory() as tempdir:
        repo_dir = _shallow_clone(gitserver_url, package, tempdir)
        if not repo_dir:
            return newer, err

        if _last_commit_time(repo_dir) > last_check:
            newer, err = True, False
        else:
            newer, err = False, False

    return newer, err


def _shallow_clone(gitserver_url: str, package: Package, working_directory):
    """Shallow clone a package."""

    # Project: SUSE:SLFO:Main uses slfo-main branch in pool/<package>
    branch = package.project.replace("SUSE:", "").replace(":", "-").lower()
    git_url = f"{gitserver_url}/pool/{package.name}"
    cmd = [
        "git",
        "clone",
        "--depth=1",
        f"--branch={branch}",
        git_url,
    ]
    completed = subprocess.run(
        cmd,
        cwd=working_directory,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.PIPE,
        encoding="utf-8",
        check=False,
    )
    if completed.returncode == 0:
        return f"{working_directory}/{package.name}"

    logging.error("Could not clone '%s'.", git_url)
    return ""


def _last_commit_time(repo_dir: str) -> Timestamp:
    # %at is for author time
    cmd = ["git", "log", "-1", "--format=%at"]
    completed = subprocess.run(
        cmd,
        cwd=repo_dir,
        stdout=subprocess.PIPE,
        env={"GIT_PAGER": ""},
        encoding="utf-8",
        check=False,
    )
    if completed.returncode == 0:
        return int(completed.stdout.strip())
    return -1
