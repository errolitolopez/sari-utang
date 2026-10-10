"""Auto-update: get the newest version of Sari Utang from GitHub (git pull).

Used by start.py when the app starts, and every few hours while it runs.
Only uses Python's standard library, so it works before the app itself is loaded.

Safe by design:
  - only a clean "fast-forward" update (git merge --ff-only); never overwrites local edits
  - no internet, local edits, or git not installed -> skip and keep the current version
  - never asks for a password (it would get stuck with no window to type in)
  - the utang data (instance/) and backups/ are not in git, so they are never touched
Turn it off with "auto_update": false in config/settings.json.
"""

import json
import os
import shutil
import subprocess
import sys

APP_DIR = os.path.dirname(os.path.abspath(__file__))
SETTINGS_FILE = os.path.join(APP_DIR, "config", "settings.json")
NETWORK_TIMEOUT = 60  # seconds for git fetch / pip install


def auto_update_enabled():
    try:
        with open(SETTINGS_FILE, encoding="utf-8") as f:
            return json.load(f).get("auto_update", True) is not False
    except (OSError, ValueError, AttributeError):
        return True  # a broken settings file is reported by the app itself


def run(*command, timeout=NETWORK_TIMEOUT):
    """Run a command in the app folder. Returns (ok, output). No window pops up on Windows."""
    env = dict(os.environ, GIT_TERMINAL_PROMPT="0")  # fail instead of asking for a password
    no_window = getattr(subprocess, "CREATE_NO_WINDOW", 0)
    try:
        result = subprocess.run(
            command, cwd=APP_DIR, env=env, capture_output=True, text=True,
            timeout=timeout, creationflags=no_window,
        )
    except (OSError, subprocess.TimeoutExpired) as error:
        return False, str(error)
    return result.returncode == 0, (result.stdout + result.stderr).strip()


def update():
    """Pull the newest version if there is one. Returns True if the code changed."""
    if not auto_update_enabled():
        return False
    if not os.path.isdir(os.path.join(APP_DIR, ".git")) or shutil.which("git") is None:
        return False  # not installed with git clone (e.g. copied from a ZIP)

    ok, output = run("git", "fetch", "--quiet")
    if not ok:
        print(f"Update check skipped (no internet or no access to GitHub): {output}")
        return False

    ok, current = run("git", "rev-parse", "HEAD")
    ok_upstream, newest = run("git", "rev-parse", "@{upstream}")
    if not (ok and ok_upstream) or current == newest:
        return False  # already the newest version
    ok, behind = run("git", "rev-list", "--count", "HEAD..@{upstream}")
    if not ok or behind == "0":
        return False  # this copy has its own commits; leave it alone

    ok, output = run("git", "merge", "--ff-only", "@{upstream}")
    if not ok:
        print(f"Update skipped: files in the app folder were changed here. Details:\n{output}")
        return False
    print(f"Updated Sari Utang to the newest version ({newest[:7]}).")

    # New Python packages? Install them before the new code starts.
    ok, changed = run("git", "diff", "--name-only", current, newest, "--", "requirements.txt")
    if ok and changed:
        ok, output = run(sys.executable, "-m", "pip", "install", "--disable-pip-version-check",
                         "-q", "-r", "requirements.txt", timeout=10 * NETWORK_TIMEOUT)
        print("Installed new packages." if ok else f"Could not install new packages:\n{output}")
        if ok:
            # run.bat compares with this copy to know the packages are installed
            installed = os.path.join(APP_DIR, ".venv", "installed-requirements.txt")
            if os.path.isdir(os.path.dirname(installed)):
                shutil.copyfile(os.path.join(APP_DIR, "requirements.txt"), installed)
    return True
