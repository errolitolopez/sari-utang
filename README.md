# sari-utang

A web app for keeping the pautang (utang) list of a sari-sari store — a digital version of the listahan notebook.

Built with Python (Flask), SQLite, vanilla JavaScript and Bootstrap 5.

## Features

- PIN login (stays logged in for 30 days; 5 wrong PINs locks that device out for 5 minutes)
- Dashboard: total utang, customers with utang, biggest balances, recent transactions
- Customer (suki) list with balances, search by name or phone, add customers
- Product list with price per unit (pc, kg, ml, oz, ... — see [Configuration](#configuration)): search, add, tap to edit

### Planned

- Customer history page
- Record utang entries per customer (items, amount, date)
- Record payments, full or partial

## Getting started

Requires Python 3.10+.

### Quick start

```bash
./run.sh          # run on this computer: http://127.0.0.1:5000
./run.sh phone    # also open it from a phone on the same Wi-Fi
```

The first run creates the virtual environment, installs Flask, creates the database and asks for a PIN (press Enter for the default `0000`). After that it just starts the app.

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

## Configuration

### Units (`config/units.json`)

The units in the product form's **Per** dropdown. Edit the file and refresh the page, no restart needed.

```json
{
  "pc": "pc (piraso)",
  "kg": "kg (kilo)",
  "tali": "tali (bundle)"
}
```

- The **key** (`"kg"`) is what gets saved with each product and shown in the list (`₱65.00 / kg`).
- The **text** (`"kg (kilo)"`) is only what the dropdown shows. It can be changed anytime.
- The **first** unit is the default for new products.
- Removing a unit is safe: products that use it keep it, and can still be edited.

## Project structure

```
app.py             routes: pages and /api endpoints
db.py              database connection + init-db / set-pin commands
schema.sql         tables: settings, customers, transactions, products
config/units.json  units for products (editable)
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
| GET | `/api/customers` | All customers with their balances |
| POST | `/api/customers` | Add a customer: `{"name": "Mang Tonyo", "phone": "0917 123 4567"}` |
| GET | `/api/products` | All products |
| POST | `/api/products` | Add a product: `{"name": "Coke Mismo", "price": 2000, "unit": "bottle"}` |
| PUT | `/api/products/<id>` | Change a product's name, price or unit (same body as POST) |

Amounts are in centavos (`1250` = ₱12.50).
