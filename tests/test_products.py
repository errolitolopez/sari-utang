"""Product list, search, paging, add and edit."""

from conftest import add_product, error


def test_add_product_cleans_the_name(client):
    product = add_product(client, "  Coke   Mismo ", 2000, "bottle")
    assert product == {"id": product["id"], "name": "Coke Mismo", "price": 2000, "unit": "bottle"}


def test_add_product_rules(client):
    def post(**fields):
        return client.post("/api/products", json={"name": "Milo", "price": 1200, "unit": "sachet", **fields})

    assert error(post(name=" ")) == "Name is required."
    assert "too long" in error(post(name="x" * 101))
    assert error(post(price=0)) == "Price must be more than P0."
    assert error(post(price=True)) == "Price must be more than P0."
    assert error(post(price="12")) == "Price must be more than P0."
    assert error(post(price=100_000_01)) == "Price is too high (max P100,000)."
    assert error(post(unit="barrel")) == "Choose a unit from the list."
    assert post(price=100_000_00).status_code == 201


def test_same_name_allowed_once_per_unit(client):
    add_product(client, "Coke Mismo", 2000, "bottle")
    add_product(client, "coke mismo", 23000, "box")
    response = client.post("/api/products", json={"name": "COKE MISMO", "price": 100, "unit": "bottle"})
    assert response.status_code == 409
    assert error(response) == "COKE MISMO per bottle is already in the list."


def test_list_is_a_to_z(client):
    add_product(client, "Milo", 1200, "sachet")
    add_product(client, "asin", 1500, "pack")
    names = [p["name"] for p in client.get("/api/products").get_json()["products"]]
    assert names == ["asin", "Milo"]


def test_paging_and_search(client):
    for number in range(25):
        add_product(client, f"Item {number:02d}", 100, "pc")
    add_product(client, "Coke 1.5L", 7500, "bottle")

    data = client.get("/api/products?page=3&per_page=10").get_json()
    assert data["pages"] == 3 and data["total"] == 26 and data["all_count"] == 26
    found = client.get("/api/products?page=1&q=coke").get_json()
    assert [p["name"] for p in found["products"]] == ["Coke 1.5L"]
    assert found["all_count"] == 26


def test_per_page_is_capped(client):
    add_product(client)
    assert client.get("/api/products?page=1&per_page=5000").get_json()["per_page"] == 100


def test_update_product(client):
    product = add_product(client, "Milo", 1200, "sachet")
    response = client.put(f"/api/products/{product['id']}",
                          json={"name": "Milo 3in1", "price": 1300, "unit": "sachet"})
    assert response.status_code == 200
    assert response.get_json()["product"]["price"] == 1300


def test_update_missing_product(client):
    response = client.put("/api/products/999", json={"name": "A", "price": 100, "unit": "pc"})
    assert response.status_code == 404
    assert error(response) == "Product not found."


def test_update_to_a_taken_name_and_unit(client):
    add_product(client, "Milo", 1200, "sachet")
    other = add_product(client, "Kopiko", 1000, "sachet")
    response = client.put(f"/api/products/{other['id']}",
                          json={"name": "milo", "price": 1000, "unit": "sachet"})
    assert response.status_code == 409


def test_products_page_renders_the_unit_choices(client):
    from sari_utang import config
    text = next(iter(config.load_units().values()))  # the store's own units.json is used
    assert text in client.get("/products").get_data(as_text=True)
