"""Collections list (who to collect from) and the dashboard summary."""

from datetime import date, timedelta

from conftest import add_customer, add_payment, add_product, add_utang, set_date


def days_ago(days):
    return (date.today() - timedelta(days=days)).isoformat() + " 10:00:00"


def credit(client, customer, price, days):
    product = add_product(client, f"Item {customer['id']}-{price}-{days}", price, "pc")
    transaction = add_utang(client, customer["id"], [{"product_id": product["id"], "quantity": 1}])
    set_date(transaction["id"], days_ago(days))
    return transaction


def test_longest_waiting_first(client):
    new = add_customer(client, "New")
    old = add_customer(client, "Old")
    add_customer(client, "Clean")
    credit(client, new, 1000, 3)
    credit(client, old, 500, 40)

    data = client.get("/api/singilin").get_json()
    assert data["overdue_days"] == 30
    assert [(c["name"], c["days"]) for c in data["customers"]] == [("Old", 40), ("New", 3)]


def test_payments_pay_the_oldest_utang_first(client):
    customer = add_customer(client)
    credit(client, customer, 1000, 40)
    credit(client, customer, 2000, 10)
    payment = add_payment(client, customer["id"], 1000)["transaction"]
    set_date(payment["id"], days_ago(5))

    row = client.get("/api/singilin").get_json()["customers"][0]
    assert row["days"] == 10  # the 40-day credit is fully paid
    assert row["balance"] == 2000
    assert row["last_payment"] == days_ago(5)


def test_paid_customers_are_left_out(client):
    customer = add_customer(client)
    credit(client, customer, 1000, 10)
    add_payment(client, customer["id"], 1000)
    assert client.get("/api/singilin").get_json()["customers"] == []


def test_dashboard_summary(client):
    old = add_customer(client, "Old")
    new = add_customer(client, "New")
    add_customer(client, "Clean")
    credit(client, old, 1000, 40)
    credit(client, new, 3000, 1)

    data = client.get("/api/dashboard").get_json()
    assert data["total_outstanding"] == 4000
    assert data["customer_count"] == 3 and data["customers_with_utang"] == 2
    assert data["overdue_count"] == 1
    assert [c["name"] for c in data["top_balances"]] == ["New", "Old"]
    assert len(data["recent_transactions"]) == 2
    assert data["recent_transactions"][0]["customer_name"] == "New"


def test_singilin_page_needs_login(anonymous, client):
    assert anonymous.get("/singilin").status_code == 302
    assert client.get("/singilin").status_code == 200
