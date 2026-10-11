"""Shared test setup: a throwaway database, emptied and reseeded before each test.

Run with: .venv/bin/pytest
"""

import os
import sqlite3
import tempfile

import pytest

# The app reads its database path from SARI_UTANG_DATABASE when it is imported.
_DB_DIR = tempfile.mkdtemp(prefix="sari-utang-tests-")
os.environ["SARI_UTANG_DATABASE"] = os.path.join(_DB_DIR, "test.db")

from app import app as flask_app  # noqa: E402  (must come after setting the database path)

PIN = "1234"


def reset_database():
    """Empty every table, then create the tables and the PIN again."""
    connection = sqlite3.connect(os.environ["SARI_UTANG_DATABASE"])
    tables = [row[0] for row in connection.execute(
        "SELECT name FROM sqlite_master WHERE type = 'table' AND name NOT LIKE 'sqlite_%'")]
    connection.execute("PRAGMA foreign_keys = OFF")
    for table in tables:
        connection.execute(f"DELETE FROM {table}")
    if connection.execute("SELECT 1 FROM sqlite_master WHERE name = 'sqlite_sequence'").fetchone():
        connection.execute("DELETE FROM sqlite_sequence")
    connection.commit()
    connection.close()
    runner = flask_app.test_cli_runner()
    assert runner.invoke(args=["init-db"]).exit_code == 0
    assert runner.invoke(args=["set-pin", "--pin", PIN]).exit_code == 0


def reset_login_throttle():
    """Forget wrong-PIN counts from earlier tests."""
    import app as app_module
    throttle = getattr(app_module, "failed_logins", None)
    if throttle is not None:
        throttle.clear()
    for extension in flask_app.extensions.values():
        if hasattr(extension, "reset"):
            extension.reset()


@pytest.fixture(autouse=True)
def fresh_database():
    reset_database()
    reset_login_throttle()
    yield


@pytest.fixture
def anonymous():
    """A test client that is not logged in."""
    return flask_app.test_client()


@pytest.fixture
def client():
    """A test client logged in with the PIN."""
    test_client = flask_app.test_client()
    response = test_client.post("/api/login", json={"pin": PIN})
    assert response.status_code == 200, response.get_json()
    return test_client


def add_customer(client, name="Aling Nena", phone=None):
    """Add a customer through the API. Returns the customer dict."""
    response = client.post("/api/customers", json={"name": name, "phone": phone})
    assert response.status_code == 201, response.get_json()
    return response.get_json()["customer"]


def add_product(client, name="Coke Mismo", price=2000, unit="bottle"):
    response = client.post("/api/products", json={"name": name, "price": price, "unit": unit})
    assert response.status_code == 201, response.get_json()
    return response.get_json()["product"]


def add_utang(client, customer_id, items, note=""):
    response = client.post("/api/transactions", json={
        "type": "utang", "customer_id": customer_id, "items": items, "note": note,
    })
    assert response.status_code == 201, response.get_json()
    return response.get_json()["transaction"]


def add_payment(client, customer_id, amount):
    response = client.post("/api/transactions", json={
        "type": "payment", "customer_id": customer_id, "amount": amount,
    })
    assert response.status_code == 201, response.get_json()
    return response.get_json()


def set_date(transaction_id, date_text):
    """Move a transaction to another day ("2026-09-01 10:00:00"), to test waiting days."""
    connection = sqlite3.connect(os.environ["SARI_UTANG_DATABASE"])
    connection.execute("UPDATE transactions SET date = ? WHERE id = ?", (date_text, transaction_id))
    connection.commit()
    connection.close()


def error(response):
    return response.get_json()["error"]
