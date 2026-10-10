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
"""

import argparse
import getpass
import logging
import os
import signal
import socket
import sqlite3
import sys
import threading
import webbrowser
from datetime import datetime

from waitress import serve

import db
from app import app

PORT = 5000
KEEP_BACKUPS = 30
APP_DIR = os.path.dirname(os.path.abspath(__file__))
BACKUP_DIR = os.path.join(APP_DIR, "backups")
LOG_FILE = os.path.join(APP_DIR, "logs", "sari-utang.log")
PID_FILE = os.path.join(app.instance_path, "server.pid")  # which process to stop
LOCAL_URL = f"http://127.0.0.1:{PORT}"


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
    while True:
        pin = getpass.getpass("No PIN set yet. Enter a 4 to 6 digit PIN (press Enter for 0000): ").strip()
        if not pin:
            print("Using the default PIN 0000. Change it later by running change-pin.bat")
            return "0000"
        if db.is_valid_pin(pin):
            if getpass.getpass("Type the PIN again: ").strip() == pin:
                return pin
            print("The two PINs are different. Try again.")
        else:
            print("The PIN must be 4 to 6 digits.")


def backup_database():
    """Copy the database to backups/sari_utang-YYYY-MM-DD_HHMMSS.db and keep the last 30."""
    os.makedirs(BACKUP_DIR, exist_ok=True)
    stamp = datetime.now().strftime("%Y-%m-%d_%H%M%S")
    target = os.path.join(BACKUP_DIR, f"sari_utang-{stamp}.db")
    # sqlite3's backup() makes a safe, complete copy even of a database in use.
    with sqlite3.connect(app.config["DATABASE"]) as source, sqlite3.connect(target) as copy:
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

    if is_running():
        print(f"Sari Utang is already running: {LOCAL_URL}")
        if args.open:
            webbrowser.open(LOCAL_URL)
        elif not args.background:
            print("Close the other Sari Utang window first, or open the address above.")
        return

    with app.app_context():
        db.init_db()
        if db.get_setting("pin_hash") is None:
            if args.background:
                notify("No PIN is set yet. Double-click run.bat once to set the PIN.")
                return
            db.set_pin(ask_for_pin())

    backup = backup_database()
    address = wifi_address()

    os.makedirs(app.instance_path, exist_ok=True)
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
    try:
        serve(app, host="0.0.0.0", port=PORT, threads=4)
    finally:
        remove_pid_file()


if __name__ == "__main__":
    main()
