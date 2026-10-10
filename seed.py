"""Sample data for trying out the app: common sari-sari products, customers, utang and payments.

Run with: flask --app app seed
          flask --app app seed --products-only

Safe to run again: products (same name + unit) and customers (same name) that
already exist are skipped. The database is backed up first.
"""

import os
import shutil
from datetime import datetime
from decimal import Decimal

import click
from flask import current_app
from flask.cli import with_appcontext

from db import get_db

# (name, price in pesos, unit). Prices are typical, adjust them in the Products page.
PRODUCTS = [
    # Drinks
    ("Coke Mismo", 20, "bottle"),
    ("Coke Mismo", 230, "box"),  # same product, sold per box of 12
    ("Royal Mismo", 20, "bottle"),
    ("Sprite Mismo", 20, "bottle"),
    ("Coke 1.5L", 75, "bottle"),
    ("C2 Green Tea", 20, "bottle"),
    ("Nature's Spring 500ml", 15, "bottle"),
    ("Red Horse 500ml", 65, "bottle"),
    ("San Miguel Pale Pilsen", 55, "bottle"),
    # Coffee, milk
    ("Nescafe 3in1 Original", 9, "sachet"),
    ("Kopiko Brown", 10, "sachet"),
    ("Great Taste White", 10, "sachet"),
    ("Milo", 12, "sachet"),
    ("Bear Brand Swak", 12, "sachet"),
    ("Alaska Evap", 38, "can"),
    # Noodles, canned goods
    ("Lucky Me Pancit Canton", 17, "pack"),
    ("Lucky Me Beef Mami", 14, "pack"),
    ("Payless Xtra Big", 16, "pack"),
    ("Nissin Cup Noodles", 30, "pc"),
    ("Ligo Sardines", 28, "can"),
    ("555 Sardines", 24, "can"),
    ("Century Tuna Flakes", 38, "can"),
    ("Argentina Corned Beef", 40, "can"),
    ("Purefoods Vienna Sausage", 35, "can"),
    # Rice, cooking
    ("Bigas Dinorado", 60, "kg"),
    ("Bigas Sinandomeng", 52, "kg"),
    ("Asukal Puti", 90, "kg"),
    ("Asukal Pula", 80, "kg"),
    ("Itlog", 9, "pc"),
    ("Mantika", 20, "pack"),
    ("Toyo Silver Swan", 6, "sachet"),
    ("Suka Datu Puti", 5, "sachet"),
    ("Patis", 6, "sachet"),
    ("Asin", 15, "pack"),
    ("Magic Sarap", 5, "sachet"),
    # Snacks, bread
    ("Skyflakes", 9, "pack"),
    ("Fita", 9, "pack"),
    ("Piattos", 18, "pack"),
    ("Nova", 18, "pack"),
    ("Boy Bawang", 10, "pack"),
    ("Pandesal", 3, "pc"),
    # Household, personal care
    ("Safeguard", 30, "pc"),
    ("Surf Bar", 15, "pc"),
    ("Tide Powder", 10, "sachet"),
    ("Downy", 8, "sachet"),
    ("Sunsilk Shampoo", 7, "sachet"),
    ("Colgate", 10, "sachet"),
    ("Yelo", 5, "pc"),
]

# Sample customers and their history. Each entry: (days ago, kind, details)
#   ("utang", [(product name, unit, quantity), ...], note)
#   ("payment", cash received in pesos, note)    -> more than the utang gives sukli
#   ("void", reason)                              -> voids the entry just before it
CUSTOMERS = [
    ("Aling Nena", "0917 123 4567", [
        (70, "utang", [("Bigas Dinorado", "kg", 2), ("Itlog", "pc", 6)], None),
        (45, "utang", [("Lucky Me Pancit Canton", "pack", 4), ("Coke Mismo", "bottle", 2)], "merienda"),
        (30, "payment", 174, None),  # pays off the oldest utang; the 45-day one is still unpaid
        (10, "utang", [("Mantika", "pack", 1), ("Toyo Silver Swan", "sachet", 2)], None),
    ]),
    ("Mang Tonyo", "0918 555 0101", [
        (50, "utang", [("Red Horse 500ml", "bottle", 3), ("Boy Bawang", "pack", 2)], None),
        (5, "payment", 500, "may sukli"),  # pays in full with sukli
        (2, "utang", [("San Miguel Pale Pilsen", "bottle", 2)], None),
    ]),
    ("Kuya Jun", "0927 222 3344", [
        (35, "utang", [("Argentina Corned Beef", "can", 2), ("Bigas Sinandomeng", "kg", 3)], None),
    ]),
    ("Ate Liza", None, [
        (20, "utang", [("Bear Brand Swak", "sachet", 5), ("Pandesal", "pc", 10)], None),
        (8, "utang", [("Tide Powder", "sachet", 3), ("Downy", "sachet", 3)], None),
        (3, "payment", 50, None),  # partial
    ]),
    ("Lola Carmen", "0999 876 5432", [
        (1, "utang", [("Asukal Puti", "kg", 1), ("Nescafe 3in1 Original", "sachet", 5)], None),
    ]),
    ("Bong", None, [
        (40, "utang", [("Coke Mismo", "box", 2)], None),
        (40, "void", "maling quantity"),  # entered by mistake
        (12, "utang", [("Coke Mismo", "bottle", 2), ("Piattos", "pack", 1)], None),
    ]),
    ("Marites", "0905 111 2222", [
        (60, "utang", [("Century Tuna Flakes", "can", 3), ("Bigas Dinorado", "kg", 1)], None),
        (15, "payment", 174, "bayad lahat"),  # paid in full, not in Singilin
    ]),
    ("Dodong", None, []),  # no utang yet
]


def to_centavos(pesos):
    return int(Decimal(str(pesos)) * 100)


def backup_database():
    """Copy the database next to it, e.g. instance/sari_utang.backup-20261010-110500.db"""
    path = current_app.config["DATABASE"]
    if not os.path.exists(path):
        return None
    stamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    backup = path.replace(".db", f".backup-{stamp}.db")
    shutil.copyfile(path, backup)
    return backup


def add_products(db):
    added = 0
    for name, price, unit in PRODUCTS:
        exists = db.execute(
            "SELECT 1 FROM products WHERE name = ? COLLATE NOCASE AND unit = ?", (name, unit)
        ).fetchone()
        if not exists:
            db.execute(
                "INSERT INTO products (name, price, unit) VALUES (?, ?, ?)",
                (name, to_centavos(price), unit),
            )
            added += 1
    return added


def balance_of(db, customer_id):
    row = db.execute(
        """
        SELECT COALESCE(SUM(CASE WHEN type = 'utang' THEN amount ELSE -amount END), 0)
        FROM transactions WHERE customer_id = ? AND voided_at IS NULL
        """,
        (customer_id,),
    ).fetchone()
    return row[0]


def add_customers(db):
    from app import line_amount  # imported here to avoid a circular import

    added = 0
    for name, phone, history in CUSTOMERS:
        if db.execute("SELECT 1 FROM customers WHERE name = ? COLLATE NOCASE", (name,)).fetchone():
            continue  # already there, don't add their history twice
        customer_id = db.execute(
            "INSERT INTO customers (name, phone) VALUES (?, ?)", (name, phone)
        ).lastrowid
        added += 1

        last_id = None
        for days_ago, kind, *details in history:
            when = f"datetime('now', 'localtime', '-{days_ago} days')"
            if kind == "utang":
                items, note = details
                rows = []
                for product_name, unit, quantity in items:
                    product = db.execute(
                        "SELECT id, name, unit, price FROM products WHERE name = ? AND unit = ?",
                        (product_name, unit),
                    ).fetchone()
                    qty = Decimal(str(quantity))
                    rows.append((product["id"], product["name"], product["unit"], product["price"],
                                 float(qty), line_amount(product["price"], qty)))
                total = sum(r[5] for r in rows)
                last_id = db.execute(
                    f"INSERT INTO transactions (customer_id, type, amount, note, date) "
                    f"VALUES (?, 'utang', ?, ?, {when})",
                    (customer_id, total, note),
                ).lastrowid
                db.executemany(
                    "INSERT INTO transaction_items "
                    "(transaction_id, product_id, name, unit, price, quantity, amount) "
                    "VALUES (?, ?, ?, ?, ?, ?, ?)",
                    [(last_id, *r) for r in rows],
                )
            elif kind == "payment":
                cash, note = details
                cash = to_centavos(cash)
                paid = min(cash, balance_of(db, customer_id))
                last_id = db.execute(
                    f"INSERT INTO transactions (customer_id, type, amount, note, tendered, date) "
                    f"VALUES (?, 'payment', ?, ?, ?, {when})",
                    (customer_id, paid, note, cash if cash > paid else None),
                ).lastrowid
            elif kind == "void":
                (reason,) = details
                db.execute(
                    f"UPDATE transactions SET voided_at = {when}, void_reason = ? WHERE id = ?",
                    (reason, last_id),
                )
    return added


@click.command("seed")
@click.option("--products-only", is_flag=True, help="Only add the sample products.")
@with_appcontext
def seed_command(products_only):
    """Add sample products, customers, utang and payments for trying out the app."""
    backup = backup_database()
    if backup:
        click.echo(f"Backup saved: {backup}")

    db = get_db()
    products = add_products(db)
    customers = 0 if products_only else add_customers(db)
    db.commit()

    click.echo(f"Added {products} products and {customers} customers (existing ones were skipped).")
