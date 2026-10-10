#!/usr/bin/env bash
# Start sari-utang. Sets everything up the first time.
#
#   ./run.sh          run on this computer only (http://127.0.0.1:5000)
#   ./run.sh phone    also reachable from phones on the same Wi-Fi

set -e
cd "$(dirname "$0")"

# 1. Virtual environment + dependencies (only installs when requirements.txt changes)
if [ ! -d .venv ]; then
  echo "Creating virtual environment..."
  python3 -m venv .venv
fi
if [ ! -f .venv/.installed ] || [ requirements.txt -nt .venv/.installed ]; then
  echo "Installing dependencies..."
  .venv/bin/pip install -q -r requirements.txt
  touch .venv/.installed
fi

# 2. Database (safe to run every time, existing data is kept)
.venv/bin/flask --app app init-db

# 3. Ask for a PIN if none is set yet
has_pin=$(.venv/bin/python -c "
import sqlite3
row = sqlite3.connect('instance/sari_utang.db').execute(
    \"SELECT 1 FROM settings WHERE key = 'pin_hash'\").fetchone()
print('yes' if row else 'no')
")
if [ "$has_pin" = "no" ]; then
  read -r -s -p "No PIN set yet. Enter a 4 to 6 digit PIN (leave empty for 0000): " pin || true
  echo
  if [ -z "$pin" ]; then
    pin="0000"
    echo "Using the default PIN 0000. Change it with: .venv/bin/flask --app app set-pin"
  fi
  .venv/bin/flask --app app set-pin --pin "$pin"
fi

# 4. Start the app
if [ "$1" = "phone" ]; then
  ip=$(hostname -I 2>/dev/null | awk '{print $1}')
  echo "Open on your phone: http://${ip:-<your-computer-ip>}:5000"
  # No --debug here: the debugger must never be reachable from other devices.
  exec .venv/bin/flask --app app run --host 0.0.0.0
else
  exec .venv/bin/flask --app app run --debug
fi
