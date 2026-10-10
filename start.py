"""Start Sari Utang for everyday use (Windows: run.bat calls this).

Every start:
  1. Creates or updates the database tables (existing data is kept).
  2. Asks for a PIN if none is set yet (press Enter for 0000).
  3. Backs up the database to backups/ (keeps the last 30).
  4. Starts the app with Waitress, a server made for daily use
     (flask run is only for development), reachable from phones on the same Wi-Fi.
"""

import getpass
import os
import socket
import sqlite3
import sys
from datetime import datetime

from waitress import serve

import db
from app import app

PORT = 5000
KEEP_BACKUPS = 30
BACKUP_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "backups")


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


def main():
    sys.stdout.reconfigure(line_buffering=True)  # show messages right away, even in a log
    with app.app_context():
        db.init_db()
        if db.get_setting("pin_hash") is None:
            db.set_pin(ask_for_pin())

    backup = backup_database()
    address = wifi_address()

    print()
    print("=" * 60)
    print("  Sari Utang is running. Keep this window open.")
    print()
    print(f"  On this computer:  http://127.0.0.1:{PORT}")
    if address:
        print(f"  On your phone:     http://{address}:{PORT}")
        print("                     (same Wi-Fi as this computer)")
    print()
    print(f"  Backup saved: {backup}")
    print("  To stop: close this window.")
    print("=" * 60)
    print()

    serve(app, host="0.0.0.0", port=PORT, threads=4)


if __name__ == "__main__":
    main()
