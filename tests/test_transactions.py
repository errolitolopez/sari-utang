"""Add utang, add payment, void, and the customer history."""

import pytest

from conftest import add_customer, add_payment, add_product, add_utang, error


@pytest.fixture
def customer(client):
    return add_customer(client)


@pytest.fixture
def coke(client):
    return add_product(client, "Coke Mismo", 2000, "bottle")


def balance_of(client, customer_id):
    customers = client.get("/api/customers").get_json()["customers"]
    return next(c["balance"] for c in customers if c["id"] == customer_id)


def test_utang_from_products_and_typed_items(client, customer, coke):
    transaction = add_utang(client, customer["id"], [
        {"product_id": coke["id"], "quantity": 2},
        {"name": "Yelo", "price": 500, "quantity": 0.5},
    ], note="  para   bukas ")
    assert transaction["amount"] == 4250  # 2 x 2000 + 0.5 x 500 = 4250
    assert transaction["items"][1]["unit"] is None
    assert balance_of(client, customer["id"]) == 4250

    history = client.get(f"/api/customers/{customer['id']}/transactions").get_json()
    assert history["customer"]["balance"] == 4250
    entry = history["transactions"][0]
    assert entry["note"] == "para bukas"
    assert [i["name"] for i in entry["items"]] == ["Coke Mismo", "Yelo"]


def test_item_keeps_the_price_at_the_time(client, customer, coke):
    add_utang(client, customer["id"], [{"product_id": coke["id"], "quantity": 1}])
    client.put(f"/api/products/{coke['id']}", json={"name": "Coke Mismo", "price": 2500, "unit": "bottle"})
    item = client.get(f"/api/customers/{customer['id']}/transactions").get_json()["transactions"][0]["items"][0]
    assert item["price"] == 2000


def test_utang_rules(client, customer, coke):
    def post(**fields):
        return client.post("/api/transactions", json={"type": "utang", "customer_id": customer["id"], **fields})

    assert error(post(items=[])) == "Add at least one item."
    assert "Too many items" in error(post(items=[{"product_id": coke["id"], "quantity": 1}] * 51))
    assert "quantity must be more than 0" in error(post(items=[{"product_id": coke["id"], "quantity": 0}]))
    assert "quantity must be more than 0" in error(post(items=[{"product_id": coke["id"], "quantity": 0.0001}]))
    assert "product not found" in error(post(items=[{"product_id": 999, "quantity": 1}]))
    assert "name is required" in error(post(items=[{"name": "", "price": 100, "quantity": 1}]))
    assert "price must be more than P0" in error(post(items=[{"name": "A", "price": 0, "quantity": 1}]))
    assert "Total is too high" in error(post(items=[{"name": "A", "price": 100_000_00, "quantity": 11}]))
    assert "Note is too long" in error(post(items=[{"name": "A", "price": 100, "quantity": 1}], note="x" * 201))
    assert error(post(items=[{"name": "A", "price": 100, "quantity": 1}, {"name": "", "price": 1, "quantity": 1}])
                 ).startswith("Item 2")
    assert balance_of(client, customer["id"]) == 0  # nothing saved


def test_type_and_customer_are_checked(client, customer):
    assert error(client.post("/api/transactions", json={"type": "gift"})) == 'type must be "utang" or "payment".'
    response = client.post("/api/transactions", json={"type": "payment", "customer_id": 999, "amount": 100})
    assert response.status_code == 404
    assert error(response) == "Customer not found."


def test_partial_payment(client, customer, coke):
    add_utang(client, customer["id"], [{"product_id": coke["id"], "quantity": 5}])
    result = add_payment(client, customer["id"], 3000)
    assert result["transaction"]["amount"] == 3000
    assert result["transaction"]["tendered"] is None
    assert result["change"] == 0 and result["balance"] == 7000


def test_payment_over_the_balance_gives_sukli(client, customer, coke):
    add_utang(client, customer["id"], [{"product_id": coke["id"], "quantity": 1}])
    result = add_payment(client, customer["id"], 5000)
    assert result["transaction"]["amount"] == 2000
    assert result["transaction"]["tendered"] == 5000
    assert result["change"] == 3000 and result["balance"] == 0


def test_payment_rules(client, customer, coke):
    def pay(amount):
        return client.post("/api/transactions", json={"type": "payment", "customer_id": customer["id"],
                                                      "amount": amount})

    assert error(pay(100)) == f"{customer['name']} has no utang to pay."
    add_utang(client, customer["id"], [{"product_id": coke["id"], "quantity": 1}])
    assert error(pay(0)) == "Amount must be more than P0."
    assert error(pay(True)) == "Amount must be more than P0."
    assert error(pay(1_000_000_01)) == "Amount is too high (max P1,000,000)."


def test_void_utang_and_payment(client, customer, coke):
    utang = add_utang(client, customer["id"], [{"product_id": coke["id"], "quantity": 5}])
    payment = add_payment(client, customer["id"], 3000)["transaction"]

    blocked = client.post(f"/api/transactions/{utang['id']}/void", json={})
    assert blocked.status_code == 400
    assert error(blocked).startswith("Part of this utang was already paid.")

    response = client.post(f"/api/transactions/{payment['id']}/void", json={"reason": " nagkamali "})
    assert response.get_json() == {"ok": True, "balance": 10000}
    response = client.post(f"/api/transactions/{utang['id']}/void", json={})
    assert response.get_json()["balance"] == 0

    history = client.get(f"/api/customers/{customer['id']}/transactions").get_json()["transactions"]
    voided = next(t for t in history if t["id"] == payment["id"])
    assert voided["void_reason"] == "nagkamali" and voided["voided_at"]


def test_void_errors(client, customer, coke):
    assert client.post("/api/transactions/999/void", json={}).status_code == 404
    utang = add_utang(client, customer["id"], [{"product_id": coke["id"], "quantity": 1}])
    assert client.post(f"/api/transactions/{utang['id']}/void", json={}).status_code == 200
    assert error(client.post(f"/api/transactions/{utang['id']}/void", json={})) == "This is already voided."


def test_history_of_missing_customer(client):
    response = client.get("/api/customers/999/transactions")
    assert response.status_code == 404
    assert error(response) == "Customer not found."
