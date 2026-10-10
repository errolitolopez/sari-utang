# sari-utang

A web app for keeping the pautang (utang) list of a sari-sari store — a digital version of the listahan notebook.

Built with Python (Flask), SQLite, vanilla JavaScript and Bootstrap 5.

## Features

- PIN login (stays logged in for 30 days; 5 wrong PINs locks that device out for 5 minutes)
- Dashboard: total utang, customers with utang, biggest balances, recent transactions

### Planned

- Customer (suki) list
- Record utang entries per customer (items, amount, date)
- Record payments, full or partial
- Search customers

## Getting started

Requires Python 3.10+.

### Quick start

```bash
./run.sh          # run on this computer: http://127.0.0.1:5000
./run.sh phone    # also open it from a phone on the same Wi-Fi
```

The first run creates the virtual environment, installs Flask, creates the database and asks for a PIN. After that it just starts the app.

### Manual steps

```bash
# 1. Create a virtual environment and install Flask
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

# 2. Create the database (stored in instance/sari_utang.db)
flask --app app init-db

# 3. Set the login PIN (4 to 6 digits). Run again anytime to change it.
flask --app app set-pin

# 4. Start the app
flask --app app run --debug
```

Open http://127.0.0.1:5000 and log in with your PIN.

To open it from a phone on the same Wi-Fi, use `./run.sh phone` (or `flask --app app run --host 0.0.0.0`, never with `--debug`) and visit `http://<your-computer-ip>:5000`.

## Project structure

```
app.py             routes: pages and /api endpoints
db.py              database connection + init-db / set-pin commands
schema.sql         tables: settings, customers, transactions
templates/         HTML pages (Bootstrap)
static/js/         page scripts (fetch the API)
instance/          database and secret key (private, not in git)
```

## API

| Method | Route | Purpose |
|--------|-------|---------|
| POST | `/api/login` | Log in with `{"pin": "1234"}` |
| POST | `/api/logout` | Log out |
| GET | `/api/dashboard` | Summary numbers for the dashboard |

Amounts are in centavos (`1250` = ₱12.50).
