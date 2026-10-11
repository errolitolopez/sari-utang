"""An invoice: only the utang that is still unpaid, as a page, as text and as a file name."""

import re
from decimal import Decimal
from urllib.parse import quote

from sari_utang.domain.money import peso, qty

MAX_FILENAME_LENGTH = 80


def unpaid_entries(rows):
    """The utang that is still unpaid, and the date of the last payment (or None).

    rows: one customer's transactions that are not voided, oldest first.

    Payments pay off the oldest utang first (same rule as the Singilin list):
    - an utang fully covered by payments is left out,
    - an utang partly covered is shown with how much was already paid on it,
    - newer utang are shown in full.
    """
    payments = [r for r in rows if r["type"] == "payment"]
    paid_left = sum(p["amount"] for p in payments)  # payments not yet applied to an utang

    entries = []
    for row in rows:
        if row["type"] != "utang":
            continue
        if paid_left >= row["amount"]:
            paid_left -= row["amount"]  # fully paid: not on the invoice
            continue
        paid = paid_left  # 0, or part of this utang that was already paid
        paid_left = 0
        entries.append(dict(row, items=[], paid=paid, remaining=row["amount"] - paid))

    return entries, (payments[-1]["date"] if payments else None)


def build_invoice(entries, last_payment):
    """The entries (with their items) plus totals and the quantity bought per product."""
    # Total quantity and amount per product (same name + unit), e.g. 6 bottle Coke Mismo.
    products = {}
    for entry in entries:
        for item in entry["items"]:
            key = (item["name"], item["unit"])
            total = products.setdefault(
                key, {"name": item["name"], "unit": item["unit"], "quantity": Decimal("0"), "amount": 0}
            )
            total["quantity"] += Decimal(str(item["quantity"]))
            total["amount"] += item["amount"]

    total_utang = sum(e["amount"] for e in entries)
    partly_paid = sum(e["paid"] for e in entries)
    return {
        "entries": entries,
        "products": sorted(products.values(), key=lambda p: -p["amount"]),
        "total_utang": total_utang,
        "partly_paid": partly_paid,
        "balance": total_utang - partly_paid,
        "last_payment": last_payment,
    }


def describe_item(item):
    """"2 bottle Coke Mismo", or "3 × Yelo" for typed-in items (no unit)."""
    quantity = qty(item["quantity"])
    return f"{quantity} {item['unit']} {item['name']}" if item["unit"] else f"{quantity} × {item['name']}"


def invoice_text(store_name, customer_name, invoice, today):
    """Plain-text version for copying into Messenger/Viber or sending by SMS."""
    lines = [store_name, f"Utang ni {customer_name} (as of {today})", ""]
    if not invoice["entries"]:
        return "\n".join(lines + ["Walang utang. Bayad na lahat."])
    for entry in invoice["entries"]:
        items = ", ".join(describe_item(i) for i in entry["items"]) or "Utang"
        lines.append(f"{entry['date'][:10]}  {items}: {peso(entry['amount'])}")
        if entry["paid"]:
            lines.append(f"   bayad na -{peso(entry['paid'])}, natitira {peso(entry['remaining'])}")
    lines += ["", f"Total utang: {peso(invoice['total_utang'])}"]
    if invoice["partly_paid"]:
        lines.append(f"Bayad na (partial): -{peso(invoice['partly_paid'])}")
    lines.append(f"Balance: {peso(invoice['balance'])}")
    return "\n".join(lines)


def sms_link(phone, text):
    """An sms: link that opens the phone's messages with the invoice text, or None without a phone."""
    if not phone:
        return None
    return f"sms:{re.sub(r'[^0-9+]', '', phone)}?body={quote(text)}"


def safe_filename(name, fallback):
    """A customer name that is safe as a file name on phones and Windows.

    Removes characters like / \\ : * ? " < > | that file names can't have.
    """
    cleaned = re.sub(r'[\\/:*?"<>|\x00-\x1f]', "", name).strip(" .")
    return cleaned[:MAX_FILENAME_LENGTH] or fallback


def unique_filename(base, used_names):
    """base + ".pdf", or "base (2).pdf" ... when the name is taken. used_names holds lower-case names.

    Two names can become the same after cleaning (e.g. "Jun?" and "Jun").
    """
    filename, number = f"{base}.pdf", 2
    while filename.lower() in used_names:
        filename, number = f"{base} ({number}).pdf", number + 1
    used_names.add(filename.lower())
    return filename
