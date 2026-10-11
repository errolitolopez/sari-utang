"""Customer list, search, paging and adding a customer."""

from conftest import add_customer, add_payment, add_utang, add_product, error


def test_add_customer_cleans_the_name(client):
    customer = add_customer(client, "  Aling   Nena ", " 0917 123 4567 ")
    assert customer["name"] == "Aling Nena"
    assert customer["phone"] == "0917 123 4567"
    assert customer["balance"] == 0


def test_add_customer_without_phone_saves_none(client):
    assert add_customer(client)["phone"] is None


def test_add_customer_rules(client):
    assert error(client.post("/api/customers", json={"name": "  "})) == "Name is required."
    long_name = client.post("/api/customers", json={"name": "x" * 101})
    assert long_name.status_code == 400
    assert "too long" in error(long_name)
    bad_phone = client.post("/api/customers", json={"name": "Jun", "phone": "abc"})
    assert bad_phone.status_code == 400
    assert "Phone can only have" in error(bad_phone)


def test_same_name_in_any_capitals_is_a_conflict(client):
    add_customer(client, "Aling Nena")
    response = client.post("/api/customers", json={"name": "ALING NENA"})
    assert response.status_code == 409
    assert error(response) == "ALING NENA is already in the list."


def test_list_puts_highest_utang_first(client):
    low = add_customer(client, "Ben")
    high = add_customer(client, "Carla")
    add_customer(client, "Ana")
    product = add_product(client, price=1000, unit="pc")
    add_utang(client, low["id"], [{"product_id": product["id"], "quantity": 1}])
    add_utang(client, high["id"], [{"product_id": product["id"], "quantity": 5}])

    customers = client.get("/api/customers").get_json()["customers"]
    assert [c["name"] for c in customers] == ["Carla", "Ben", "Ana"]
    assert [c["balance"] for c in customers] == [5000, 1000, 0]


def test_paging_and_search(client):
    for number in range(25):
        add_customer(client, f"Customer {number:02d}")
    add_customer(client, "Nena", "0917 000 1111")

    data = client.get("/api/customers?page=2&per_page=10").get_json()
    assert data["page"] == 2 and data["pages"] == 3 and data["total"] == 26
    assert len(data["customers"]) == 10
    assert data["all_count"] == 26 and data["with_utang_count"] == 0

    by_phone = client.get("/api/customers?page=1&q=0917").get_json()
    assert [c["name"] for c in by_phone["customers"]] == ["Nena"]
    assert by_phone["total"] == 1 and by_phone["all_count"] == 26


def test_page_past_the_end_goes_to_the_last_page(client):
    add_customer(client)
    data = client.get("/api/customers?page=9&per_page=20").get_json()
    assert data["page"] == 1


def test_search_treats_percent_as_text(client):
    add_customer(client, "50% Off")
    add_customer(client, "Other")
    found = client.get("/api/customers?page=1&q=50%25").get_json()
    assert [c["name"] for c in found["customers"]] == ["50% Off"]


def test_customer_page_404_for_missing_customer(client):
    assert client.get("/customers/999").status_code == 404
    customer = add_customer(client)
    assert client.get(f"/customers/{customer['id']}").status_code == 200


def test_balance_ignores_voided_entries(client):
    customer = add_customer(client)
    product = add_product(client, price=1000, unit="pc")
    transaction = add_utang(client, customer["id"], [{"product_id": product["id"], "quantity": 2}])
    add_payment(client, customer["id"], 500)
    assert client.get("/api/customers").get_json()["customers"][0]["balance"] == 1500
    client.post(f"/api/transactions/{transaction['id']}/void", json={})  # blocked: part paid
    assert client.get("/api/customers").get_json()["customers"][0]["balance"] == 1500
