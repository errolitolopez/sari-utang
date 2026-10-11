"""Rules for a debt (several items) and a payment."""

from sari_utang.domain.money import (
    MAX_PRICE, is_whole_number, line_amount, parse_quantity,
)
from sari_utang.domain.products import MAX_NAME_LENGTH
from sari_utang.domain.text import clean_text
from sari_utang.errors import ValidationError

MAX_ITEMS = 50
MAX_UTANG_TOTAL = 1_000_000_00  # P1,000,000.00 in centavos
MAX_TENDERED = 1_000_000_00  # P1,000,000.00 in centavos, catches typos
MAX_NOTE_LENGTH = 200
KINDS = ("utang", "payment")


def check_note(value, what="Note"):
    note = clean_text(value)
    if len(note) > MAX_NOTE_LENGTH:
        raise ValidationError(f"{what} is too long (max {MAX_NOTE_LENGTH} characters).")
    return note


def make_item(raw, number, find_product):
    """Check one item of a debt and return it as a dict.

    An item is either a product from the list: {"product_id": 3, "quantity": 2}
    or typed in by hand:                        {"name": "Yelo", "price": 500, "quantity": 1}

    find_product: a function, product id -> the product (name, unit, price) or None.
    """
    if not isinstance(raw, dict):
        raise ValidationError(f"Item {number} is not valid.")

    quantity = parse_quantity(raw.get("quantity"))
    if quantity is None:
        raise ValidationError(f"Item {number}: quantity must be more than 0 (up to 3 decimals).")

    if raw.get("product_id") is not None:
        product_id = raw["product_id"]
        product = find_product(product_id) if is_whole_number(product_id) else None
        if product is None:
            raise ValidationError(f"Item {number}: product not found. Refresh the page and try again.")
        name, unit, price = product["name"], product["unit"], product["price"]
    else:
        product_id, unit = None, None
        name = clean_text(raw.get("name", ""))
        price = raw.get("price")
        if not name or len(name) > MAX_NAME_LENGTH:
            raise ValidationError(f"Item {number}: name is required (max {MAX_NAME_LENGTH} characters).")
        if not is_whole_number(price) or not 0 < price <= MAX_PRICE:
            raise ValidationError(f"Item {number}: price must be more than P0 (max P100,000).")

    amount = line_amount(price, quantity)
    if amount <= 0:
        raise ValidationError(f"Item {number}: quantity is too small, the amount would be P0.")

    return {
        "product_id": product_id,
        "name": name,
        "unit": unit,
        "price": price,
        "quantity": float(quantity),
        "amount": amount,
    }


def check_items(raw_items, find_product):
    """All items of a debt, checked first so nothing is saved if one of them is wrong.

    Returns (items, total). The total is always computed here, never taken from the page.
    """
    if not isinstance(raw_items, list) or not raw_items:
        raise ValidationError("Add at least one item.")
    if len(raw_items) > MAX_ITEMS:
        raise ValidationError(f"Too many items (max {MAX_ITEMS}).")
    items = [make_item(raw, number, find_product) for number, raw in enumerate(raw_items, start=1)]
    total = sum(item["amount"] for item in items)
    if total > MAX_UTANG_TOTAL:
        raise ValidationError("Total is too high (max P1,000,000).")
    return items, total


def split_payment(amount, balance, customer_name):
    """What a payment does. Returns (paid, change, tendered).

    A payment lowers the balance and can be partial. If the customer hands over more than
    the debt, it counts as paid in full: only the debt is recorded as paid, and the
    extra is the change. tendered (the cash received) is kept only when there was change.
    """
    if not is_whole_number(amount) or amount <= 0:
        raise ValidationError("Amount must be more than P0.")
    if amount > MAX_TENDERED:
        raise ValidationError("Amount is too high (max P1,000,000).")
    if balance <= 0:
        raise ValidationError(f"{customer_name} has no debt to pay.")
    paid = min(amount, balance)
    change = amount - paid
    return paid, change, amount if change > 0 else None
