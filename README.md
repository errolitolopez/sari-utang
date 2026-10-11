# sari-utang

A web app for keeping the credit (debt) list of a small neighborhood store (a sari-sari store) — a digital version of the paper notebook.

Built with Python (Flask), SQLite, vanilla JavaScript and Bootstrap 5.

## Features

- PIN login (stays logged in for 30 days; 5 wrong PINs locks that device out for 5 minutes)
- Dashboard: total debt, customers with debt, biggest balances, recent transactions
- Products import/export as Excel (.xlsx): export (with a unit dropdown), edit prices, import back. New name + unit is added, same name + unit gets its price updated, nothing is deleted. All or nothing: a file with a bad row imports nothing and lists the rows to fix
- Customer list: highest debt first, paged (20 per page), search by name or phone, add customers
- Customer page: balance and full history; tap a customer to open it, tap a history entry to see its items, quantities, prices and note
- Add debt: pick products, set quantities with − / + buttons or type them (e.g. 2 bottle, 0.5 kg), add items not in the list, optional note
- Record payments: full or partial, optional note. Paying more than the debt counts as paid in full and shows the change
- Invoice per customer: only the unpaid debt (items, qty × price). Payments pay off the oldest debt first: fully paid debts are left out, a partly paid one shows "already paid" and what's left. Optional summary by product, total, balance. Download as PDF (A6 receipt), print, copy as text, or send by SMS Print / save as PDF, copy as text for Messenger/Viber, or send by SMS
- Batch export: on the Collections page, download a ZIP with one PDF invoice per customer (file name = customer name, e.g. `Aling Nena.pdf`), following the selected filter
- Collections list: everyone who owes, longest-waiting first, with filters (7+, 15+, 30+ days). "Overdue" (default 30 days) is set in [config/settings.json](#settings-configsettingsjson) and shown on the Dashboard
- Void a debt or payment entered by mistake: it stays in the history crossed out (with the reason) and no longer counts
- Product list with price per unit (pc, box, kg, ml, oz, ... — see [Configuration](#configuration)): paged (20 per page), search, add, tap to edit. The same product can be listed once per unit (e.g. Coke Mismo per pc and per box)

### Planned

- Put it online

## Getting started

Requires Python 3.10+.

### Everyday use (the store's computer)

- **Windows:** see [SETUP-WINDOWS.md](SETUP-WINDOWS.md) — `run.bat` the first time (sets the PIN), then `create-shortcuts.bat` for Desktop icons that run it in the background (no window).
- **Linux/Mac:** `pip install -r requirements.txt` in a virtual environment, then `python start.py`.

`start.py` (`--background` = no window, logs to `logs/`; `--open` = open the browser; `--stop` = stop it) auto-updates from GitHub (`updater.py`: `git pull --ff-only` at start and every 6 hours, then restarts itself; skipped if offline or files were edited locally; off with `"auto_update": false`), updates the database, asks for a PIN the first time, backs up the database to `backups/` (last 30 kept), and serves the app with Waitress on port 5000 for phones on the same Wi-Fi.

### Quick start (development)

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

### Sample data (for trying it out)

```bash
flask --app app seed                  # ~50 common sari-sari products + 8 customers with debt/payments
flask --app app seed --products-only  # only the products
```

The database is backed up first (`instance/sari_utang.backup-<date>.db`). Running it again skips products and customers that already exist. To start clean, stop the app, delete `instance/sari_utang.db` and run `./run.sh`.

To open it from a phone on the same Wi-Fi, use `./run.sh phone` (or `flask --app app run --host 0.0.0.0`, never with `--debug`) and visit `http://<your-computer-ip>:5000`.

## Configuration

`config/settings.json` and `config/units.json` are each store's own files and are **not in git**. On first start they are copied from `config/settings.example.json` and `config/units.example.json`, so editing them never blocks an update (`git pull`). Settings missing from `settings.json` (e.g. added in a newer version) use the value from the example file.

### Units (`config/units.json`)

The units in the product form's **Per** dropdown. Edit the file and refresh the page, no restart needed.

```json
{
  "pc": "pc (piece)",
  "box": "box",
  "kg": "kg (kilogram)",
  "bundle": "bundle"
}
```

- The **key** (`"kg"`) is what gets saved with each product and shown in the list (`₱65.00 / kg`).
- The **text** (`"kg (kilogram)"`) is only what the dropdown shows. It can be changed anytime.
- The **first** unit is the default for new products.
- Removing a unit is safe: products that use it keep it, and can still be edited.

### Settings (`config/settings.json`)

```json
{
  "store_name": "Sari-Sari Store",
  "overdue_days": 30,
  "auto_update": true
}
```

- `store_name`: shown at the top of invoices.
- `auto_update` (true/false): pull the newest version from GitHub at start and every 6 hours (only for copies installed with `git clone`).
- `overdue_days` (1 to 365): a debt unpaid this many days or more counts as "overdue". Those customers are red in the Collections list and counted on the Dashboard. Edit and refresh, no restart needed.

## Tests

```bash
.venv/bin/pip install -r requirements-dev.txt
.venv/bin/pytest
```

The tests use a throwaway database (`SARI_UTANG_DATABASE`), so your own data is not touched.

## Project structure

```
app.py             entry point: creates the app (flask --app app run)
sari_utang/        the app, in layers (each only uses the ones below it)
  web/             Flask blueprints: pages and /api endpoints, login check
  services/        use cases: rules, ownership checks, commit
  repositories/    all SQL, one class per table
  domain/          rules with no Flask or SQL: cleaning input, amounts, who owes what
  errors.py        typed errors (ValidationError, NotFoundError, ...) turned into JSON answers
  config.py        paths, sessions, reading config/settings.json and units.json
  database.py      database connection + init-db command
  cli.py           set-pin command
  seed.py          sample products, customers, debt and payments (flask --app app seed)
  excel.py         products .xlsx import/export (openpyxl)
  invoice_pdf.py   invoice PDFs (fpdf2), A6 receipt layout
  fonts/           DejaVu Sans font for PDFs (has the ₱ sign), with its license
  schema.sql       tables: settings, customers, transactions, transaction_items, products
  templates/       HTML pages (Bootstrap)
  static/          page scripts (js/), theme and glass look (css/glass.css), icons
tests/             pytest tests (.venv/bin/pytest)
updater.py         auto-update from GitHub (git pull --ff-only), used by start.py
start.py           everyday start: database, PIN, backup, Waitress server
run.bat            Windows: first-time setup / start with a window
reinstall.bat      Windows: fresh app files + packages, keeps instance/, backups/, config/*.json
create-shortcuts.bat  Windows: Desktop icons "Sari Utang" (background + browser) and "Stop Sari Utang"
windows/           helpers: make-shortcut.ps1 (shortcuts, auto-start), setup.bat (.venv + packages for run.bat / reinstall.bat)
config/*.example.json  default settings and units (in git)
config/settings.json, units.json  this store's own copies (made on first start, not in git, editable)
instance/          database and secret key (private, not in git)
```

## API

| Method | Route | Purpose |
|--------|-------|---------|
| POST | `/api/login` | Log in with `{"pin": "1234"}` |
| POST | `/api/logout` | Log out |
| GET | `/api/dashboard` | Summary numbers for the dashboard (includes `overdue_count`) |
| GET | `/products/export.xlsx` | All products as Excel (`name`, `price` in pesos, `unit`) |
| POST | `/api/products/import` | Upload an .xlsx (`file`): adds new products, updates prices of existing ones |
| GET | `/customers/<id>/invoice.pdf` | One customer's invoice as PDF |
| GET | `/singilin/invoices.zip?min_days=30` | ZIP of PDF invoices, one per customer with debt (optional `min_days` filter) |
| GET | `/api/singilin` | Everyone who owes, with `days` their oldest unpaid debt has waited (payments pay off the oldest debt first) |
| GET | `/api/customers` | Customers with their balances, highest debt first; paged with `?page=1&per_page=20&q=nena` |
| POST | `/api/customers` | Add a customer: `{"name": "Mang Tonyo", "phone": "0917 123 4567"}` |
| GET | `/api/products` | All products, or one page with `?page=1&per_page=20&q=coke` (returns `page`, `pages`, `total`) |
| POST | `/api/products` | Add a product: `{"name": "Coke Mismo", "price": 2000, "unit": "bottle"}` |
| PUT | `/api/products/<id>` | Change a product's name, price or unit (same body as POST) |
| GET | `/api/customers/<id>/transactions` | One customer with their balance and history (with items) |
| POST | `/api/transactions` | Add a debt or a payment (see below) |
| POST | `/api/transactions/<id>/void` | Void a debt or payment entered by mistake |

Adding a debt — the server computes every amount and the total from the product prices:

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

Quantities can have up to 3 decimals. Each item's name, unit and price are copied when saved, so changing a product's price later doesn't change old debt.

Voiding: `POST /api/transactions/<id>/void` with an optional `{"reason": "maling quantity"}`. A debt can't be voided if that would make the balance negative (void the payment first).

Recording a payment (amount in centavos = the cash received):

```json
{"type": "payment", "customer_id": 1, "amount": 50000, "note": "GCash"}
```

If the amount is more than the debt, only the debt is recorded as paid (balance becomes ₱0), the cash received is saved as `tendered`, and the response has the change: `{"change": 15000, ...}`.

Amounts are in centavos (`1250` = ₱12.50).
