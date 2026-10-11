"""Login, logout, lockout and page protection."""

from conftest import PIN


def test_pages_send_anonymous_users_to_login(anonymous):
    for path in ("/dashboard", "/customers", "/products", "/singilin"):
        response = anonymous.get(path)
        assert response.status_code == 302
        assert response.headers["Location"].endswith("/login")


def test_api_answers_401_when_not_logged_in(anonymous):
    response = anonymous.get("/api/customers")
    assert response.status_code == 401
    assert response.get_json()["error"] == "Please log in."


def test_login_with_the_pin(anonymous):
    assert anonymous.post("/api/login", json={"pin": PIN}).status_code == 200
    assert anonymous.get("/api/customers").status_code == 200
    assert anonymous.get("/").headers["Location"].endswith("/dashboard")


def test_wrong_pin(anonymous):
    response = anonymous.post("/api/login", json={"pin": "9999"})
    assert response.status_code == 401
    assert response.get_json()["error"] == "Wrong PIN."


def test_five_wrong_pins_lock_the_device(anonymous):
    for _ in range(5):
        anonymous.post("/api/login", json={"pin": "9999"})
    response = anonymous.post("/api/login", json={"pin": PIN})
    assert response.status_code == 429
    assert "Too many wrong PINs" in response.get_json()["error"]


def test_logout(client):
    assert client.post("/api/logout").status_code == 200
    assert client.get("/api/customers").status_code == 401
