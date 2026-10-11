"""Rules for reading a products Excel file: the columns, prices and units of each row."""

import re
from decimal import Decimal

from sari_utang.domain.money import MAX_PRICE
from sari_utang.domain.products import MAX_NAME_LENGTH
from sari_utang.domain.text import clean_text

COLUMNS = ["name", "price", "unit"]
MAX_IMPORT_ROWS = 5000


def parse_import_price(value):
    """A price cell -> centavos, or None if it isn't valid.

    Excel usually gives a number (20.5). A cell typed as text can look like
    "20", "20.50" or "₱1,234.50".
    """
    if isinstance(value, bool) or value is None:
        return None
    if isinstance(value, (int, float)):
        amount = Decimal(str(value))
    else:
        cleaned = str(value).replace("₱", "").replace("P", "").replace(",", "").strip()
        if not re.fullmatch(r"\d+(\.\d+)?", cleaned):
            return None
        amount = Decimal(cleaned)
    if not amount.is_finite() or amount.as_tuple().exponent < -2:
        return None  # more than 2 decimals, e.g. 20.555
    centavos = int(amount * 100)
    return centavos if 0 < centavos <= MAX_PRICE else None


def cell_text(value):
    """A cell as text: None -> "", 555 (a number) -> "555", 12.0 -> "12"."""
    if value is None:
        return ""
    if isinstance(value, float) and value.is_integer():
        value = int(value)
    return str(value)


def check_header(header_cells):
    """An error text when the first row isn't name, price, unit; otherwise None."""
    header = [cell_text(cell).strip().lower() for cell in header_cells][:3]
    if header != COLUMNS:
        return f"The first row must be: {', '.join(COLUMNS)}"
    return None


def check_rows(rows, units):
    """Check every row after the header. Returns (products, errors).

    rows: the cells of each row, starting at line 2 of the file.
    units: the unit keys from config/units.json.
    Nothing is saved here; if errors is not empty, the import is cancelled.
    """
    units_lower = {u.lower(): u for u in units}  # "KG" in the file -> "kg"
    products, errors, seen = [], [], set()
    for line_number, row in enumerate(rows, start=2):
        row = (tuple(row) + (None, None, None))[:3]
        if all(cell_text(cell).strip() == "" for cell in row):
            continue  # skip empty rows
        if len(products) + len(errors) >= MAX_IMPORT_ROWS:
            errors.append(f"Too many rows (max {MAX_IMPORT_ROWS}).")
            break
        name = clean_text(cell_text(row[0]))
        price = parse_import_price(row[1])
        unit = units_lower.get(cell_text(row[2]).strip().lower())

        problems = []
        if not name or len(name) > MAX_NAME_LENGTH:
            problems.append(f"name is required (max {MAX_NAME_LENGTH} characters)")
        if cell_text(row[1]).strip() == "":
            problems.append("price is empty")
        elif price is None:
            problems.append(f'price "{cell_text(row[1])}" is not valid (e.g. 20 or 20.50, max 100,000)')
        if cell_text(row[2]).strip() == "":
            problems.append("unit is empty")
        elif unit is None:
            problems.append(f'unit "{cell_text(row[2])}" is not in config/units.json')
        key = (name.lower(), unit)
        if not problems and key in seen:
            problems.append(f"{name} per {unit} is already in the file above")
        seen.add(key)

        if problems:
            errors.append(f"Row {line_number}: " + "; ".join(problems))
        else:
            products.append({"name": name, "price": price, "unit": unit})

    if not products and not errors:
        errors.append("The file has no products.")
    return products, errors
