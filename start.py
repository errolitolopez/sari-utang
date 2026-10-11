"""Start Sari Utang for everyday use.

    python start.py                      with a window (run.bat): asks for a PIN the first time
    pythonw start.py --background --open  no window (desktop shortcut): starts, then opens the browser
    pythonw start.py --background         no window (auto-start when the computer turns on)
    pythonw start.py --stop               stops the app running in the background

Every start:
  1. Creates or updates the database tables (existing data is kept).
  2. Asks for a PIN if none is set yet (press Enter for 0000). Not in background mode:
     there is no window to type in, so run.bat must be used once first.
  3. Backs up the database to backups/ (keeps the last 30).
  4. Starts the app with Waitress, a server made for daily use
     (flask run is only for development), reachable from phones on the same Wi-Fi.
If the app is already running, it isn't started twice (with --open the browser still opens).

Auto-update (see updater.py): before starting, and every few hours while running, the newest
version is pulled from GitHub; if there was one, the app restarts itself with the new code.
"""

import argparse
import getpass
import logging
import os
import signal
import socket
import sqlite3
import subprocess
import sys
import threading
import time
import webbrowser
from datetime import datetime

import updater

# app.py and the sari_utang package are imported inside main(), after the auto-update,
# so a freshly pulled version is the one that runs.

PORT = 5000
KEEP_BACKUPS = 30
APP_DIR = os.path.dirname(os.path.abspath(__file__))
BACKUP_DIR = os.path.join(APP_DIR, "backups")
LOG_FILE = os.path.join(APP_DIR, "logs", "sari-utang.log")
INSTANCE_DIR = os.path.join(APP_DIR, "instance")  # the database, secret key, PIN
PID_FILE = os.path.join(INSTANCE_DIR, "server.pid")  # which process to stop
LOCAL_URL = f"http://127.0.0.1:{PORT}"
UPDATE_CHECK_HOURS = 6
RESTARTED = "SARI_UTANG_RESTARTED"  # set when the app restarted itself after an update
server = None  # the running Waitress server, so a restart can let go of the port


def notify(message):
    """Show a message. In background mode on Windows there is no window, so use a popup."""
    print(message)
    if os.name == "nt" and (sys.stdout is None or not sys.stdout.isatty()):
        import ctypes
        ctypes.windll.user32.MessageBoxW(0, message, "Sari Utang", 0x40)  # 0x40 = info icon


def is_running():
    """True if something already answers on the app's port (the app is already running)."""
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.settimeout(0.5)
        return s.connect_ex(("127.0.0.1", PORT)) == 0


def log_to_file():
    """Background mode has no window: send messages and errors to logs/sari-utang.log."""
    os.makedirs(os.path.dirname(LOG_FILE), exist_ok=True)
    if os.path.exists(LOG_FILE) and os.path.getsize(LOG_FILE) > 1_000_000:
        os.replace(LOG_FILE, LOG_FILE + ".old")  # keep the log small: one old copy only
    log = open(LOG_FILE, "a", encoding="utf-8", buffering=1)
    sys.stdout = sys.stderr = log
    logging.basicConfig(stream=log, level=logging.INFO, format="%(asctime)s %(message)s")
    print(f"\n--- {datetime.now():%Y-%m-%d %H:%M:%S} starting in the background ---")


def ask_for_pin():
    """Ask until a valid PIN is typed. Empty means 0000."""
    from sari_utang.domain.pin import is_valid_pin

    while True:
        pin = getpass.getpass("No PIN set yet. Enter a 4 to 6 digit PIN (press Enter for 0000): ").strip()
        if not pin:
            print("Using the default PIN 0000. Change it later by running change-pin.bat")
            return "0000"
        if is_valid_pin(pin):
            if getpass.getpass("Type the PIN again: ").strip() == pin:
                return pin
            print("The two PINs are different. Try again.")
        else:
            print("The PIN must be 4 to 6 digits.")


def backup_database(database):
    """Copy the database to backups/sari_utang-YYYY-MM-DD_HHMMSS.db and keep the last 30."""
    os.makedirs(BACKUP_DIR, exist_ok=True)
    stamp = datetime.now().strftime("%Y-%m-%d_%H%M%S")
    target = os.path.join(BACKUP_DIR, f"sari_utang-{stamp}.db")
    # sqlite3's backup() makes a safe, complete copy even of a database in use.
    with sqlite3.connect(database) as source, sqlite3.connect(target) as copy:
        source.backup(copy)

    backups = sorted(f for f in os.listdir(BACKUP_DIR) if f.startswith("sari_utang-") and f.endswith(".db"))
    for old in backups[:-KEEP_BACKUPS]:
        os.remove(os.path.join(BACKUP_DIR, old))
    return target


def wifi_address():
    """This computer's address on the Wi-Fi, e.g. 192.168.1.17 (nothing is sent anywhere)."""
    with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as s:
        try:
            s.connect(("192.168.0.1", 80))  # only picks the network card, no data is sent
            return s.getsockname()[0]
        except OSError:
            return None


def stop():
    """Stop the app that was started in the background (desktop "Stop" shortcut)."""
    pid = None
    if os.path.exists(PID_FILE):
        with open(PID_FILE) as f:
            pid = int(f.read().strip() or 0) or None
    if pid is None or not is_running():
        if os.path.exists(PID_FILE):
            os.remove(PID_FILE)  # left over from a crash or a restart
        notify("Sari Utang is not running.")
        return
    try:
        os.kill(pid, signal.SIGTERM)  # on Windows this ends the process
    except OSError:
        pass
    os.remove(PID_FILE)
    notify("Sari Utang stopped.")


def remove_pid_file():
    if os.path.exists(PID_FILE):
        os.remove(PID_FILE)


def restart(background):
    """Start again with the newly pulled code."""
    print("Restarting with the new version...")
    env = dict(os.environ, **{RESTARTED: "1"})
    command = [sys.executable] + sys.argv
    if os.name != "nt":
        os.execve(sys.executable, command, env)  # replace this process with the new code
    if server is not None:
        server.close()  # let go of the port so the new copy can use it
    if background:
        # No window: start the new copy, then end this one.
        subprocess.Popen(command, cwd=APP_DIR, env=env,
                         creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0))
        os._exit(0)
    # With a window (run.bat): run the new copy in the same window and wait for it.
    # Restarting from run.bat instead would be unsafe: Windows reads a .bat file while
    # running it, and the update may have just changed run.bat.
    os._exit(subprocess.call(command, cwd=APP_DIR, env=env))


def keep_updating(background):
    """While the app runs, check for a new version every few hours (the laptop may stay on)."""
    while True:
        time.sleep(UPDATE_CHECK_HOURS * 3600)
        if updater.update():
            restart(background)


def wait_for_old_version_to_stop():
    """After an update restart, the old copy may still be letting go of the port."""
    for _ in range(40):
        if not is_running():
            return True
        time.sleep(0.5)
    return False


def main():
    parser = argparse.ArgumentParser(description="Start Sari Utang.")
    parser.add_argument("--background", action="store_true", help="no window; messages go to logs/")
    parser.add_argument("--open", action="store_true", help="open the app in the browser")
    parser.add_argument("--stop", action="store_true", help="stop the app running in the background")
    args = parser.parse_args()

    if args.stop:
        stop()
        return

    if args.background or sys.stdout is None:  # pythonw has no window to print to
        log_to_file()
    else:
        sys.stdout.reconfigure(line_buffering=True)  # show messages right away

    restarted = os.environ.pop(RESTARTED, None) == "1"
    if restarted:
        wait_for_old_version_to_stop()
    elif not is_running() and updater.update():
        restart(args.background)  # run the code that was just pulled

    from waitress.server import create_server

    from app import app
    from sari_utang.database import get_db, init_db
    from sari_utang.services import AuthService

    if is_running():
        print(f"Sari Utang is already running: {LOCAL_URL}")
        if args.open:
            webbrowser.open(LOCAL_URL)
        elif not args.background:
            print("Close the other Sari Utang window first, or open the address above.")
        return

    with app.app_context():
        init_db()
        auth = AuthService(get_db())
        if not auth.has_pin():
            if args.background:
                notify("No PIN is set yet. Double-click run.bat once to set the PIN.")
                return
            auth.set_pin(ask_for_pin())

    backup = backup_database(app.config["DATABASE"])
    address = wifi_address()

    os.makedirs(INSTANCE_DIR, exist_ok=True)
    with open(PID_FILE, "w") as f:
        f.write(str(os.getpid()))

    print()
    print("=" * 60)
    if args.background:
        print("  Sari Utang is running in the background.")
    else:
        print("  Sari Utang is running. Keep this window open.")
    print()
    print(f"  On this computer:  {LOCAL_URL}")
    if address:
        print(f"  On your phone:     http://{address}:{PORT}")
        print("                     (same Wi-Fi as this computer)")
    print()
    print(f"  Backup saved: {backup}")
    print("  To stop: " + ("use the \"Stop Sari Utang\" shortcut." if args.background else "close this window."))
    print("=" * 60)
    print()

    if args.open:
        threading.Timer(1.5, webbrowser.open, [LOCAL_URL]).start()  # after the server is up
    threading.Thread(target=keep_updating, args=(args.background,), daemon=True).start()
    try:
        global server
        server = create_server(app, host="0.0.0.0", port=PORT, threads=4)
        server.run()
    finally:
        remove_pid_file()


if __name__ == "__main__":
    main()
