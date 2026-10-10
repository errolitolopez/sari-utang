# sari-utang

A web app for keeping the pautang (utang) list of a sari-sari store — a digital version of the listahan notebook.

Built with Python (Flask), SQLite, vanilla JavaScript and Bootstrap 5.

## Features

- PIN login (stays logged in for 30 days; 5 wrong PINs locks that device out for 5 minutes)
- Dashboard: total utang, customers with utang, biggest balances, recent transactions
- Customer (suki) list with balances, search by name or phone, add customers
- Customer page: balance and full history; tap a customer to open it, tap a history entry to see its items, quantities, prices and note
- Add utang: pick products and quantities (e.g. 2 bottle, 0.5 kg), add items not in the list, optional note
- Record payments (bayad): full or partial, optional note. Paying more than the utang counts as paid in full and shows the sukli (change)
- Singilin list: everyone who owes, longest-waiting first, with filters (7+, 15+, 30+ days). "Matagal" (default 30 days) is set in [config/settings.json](#settings-configsettingsjson) and shown on the Dashboard
- Void an utang or payment entered by mistake: it stays in the history crossed out (with the reason) and no longer counts
- Product list with price per unit (pc, box, kg, ml, oz, ... — see [Configuration](#configuration)): search, add, tap to edit. The same product can be listed once per unit (e.g. Coke Mismo per pc and per box)

### Planned

- Put it online

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
  "box": "box",
  "kg": "kg (kilo)",
  "tali": "tali (bundle)"
}
```

- The **key** (`"kg"`) is what gets saved with each product and shown in the list (`₱65.00 / kg`).
- The **text** (`"kg (kilo)"`) is only what the dropdown shows. It can be changed anytime.
- The **first** unit is the default for new products.
- Removing a unit is safe: products that use it keep it, and can still be edited.

### Settings (`config/settings.json`)

```json
{
  "overdue_days": 30
}
```

- `overdue_days` (1 to 365): an utang unpaid this many days or more counts as "matagal". Those customers are red in the Singilin list and counted on the Dashboard. Edit and refresh, no restart needed.

## Project structure

```
app.py             routes: pages and /api endpoints
db.py              database connection + init-db / set-pin commands
schema.sql         tables: settings, customers, transactions, transaction_items, products
config/units.json  units for products (editable)
config/settings.json  settings like overdue_days (editable)
templates/         HTML pages (Bootstrap)
static/js/         page scripts (fetch the API)
instance/          database and secret key (private, not in git)
```

## API

| Method | Route | Purpose |
|--------|-------|---------|
| POST | `/api/login` | Log in with `{"pin": "1234"}` |
| POST | `/api/logout` | Log out |
| GET | `/api/dashboard` | Summary numbers for the dashboard (includes `overdue_count`) |
| GET | `/api/collect` | Everyone who owes, with `days` their oldest unpaid utang has waited (payments pay off the oldest utang first) |
| GET | `/api/customers` | All customers with their balances |
| POST | `/api/customers` | Add a customer: `{"name": "Mang Tonyo", "phone": "0917 123 4567"}` |
| GET | `/api/products` | All products |
| POST | `/api/products` | Add a product: `{"name": "Coke Mismo", "price": 2000, "unit": "bottle"}` |
| PUT | `/api/products/<id>` | Change a product's name, price or unit (same body as POST) |
| GET | `/api/customers/<id>/transactions` | One customer with their balance and history (with items) |
| POST | `/api/transactions` | Add an utang or a payment (see below) |
| POST | `/api/transactions/<id>/void` | Void an utang or payment entered by mistake |

Adding an utang — the server computes every amount and the total from the product prices:

```json
{
  "type": "utang",
  "customer_id": 1,
  "items": [
    {"product_id": 3, "quantity": 2},
    {"product_id": 5, "quantity": 0.5},
    {"name": "Yelo", "price": 500, "quantity": 1}
  ],
  "note": "for the party"
}
```

Quantities can have up to 3 decimals. Each item's name, unit and price are copied when saved, so changing a product's price later doesn't change old utang.

Voiding: `POST /api/transactions/<id>/void` with an optional `{"reason": "maling quantity"}`. An utang can't be voided if that would make the balance negative (void the payment first).

Recording a payment (amount in centavos = the cash received):

```json
{"type": "payment", "customer_id": 1, "amount": 50000, "note": "GCash"}
```

If the amount is more than the utang, only the utang is recorded as paid (balance becomes ₱0), the cash received is saved as `tendered`, and the response has the sukli: `{"change": 15000, ...}`.

Amounts are in centavos (`1250` = ₱12.50).
