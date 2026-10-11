"""Every page opens when logged in, and the static files are served."""

import pytest

from conftest import add_customer

PAGES = ["/dashboard", "/customers", "/products", "/singilin"]


def test_login_page_opens(anonymous):
    html = anonymous.get("/login").get_data(as_text=True)
    assert "login-form" in html
    assert "css/glass.css" in html


@pytest.mark.parametrize("path", PAGES)
def test_pages_open_when_logged_in(client, path):
    response = client.get(path)
    assert response.status_code == 200
    assert "js/theme.js" in response.get_data(as_text=True)


def test_navbar_marks_the_current_page(client):
    html = client.get("/products").get_data(as_text=True)
    products_link = html[html.index('href="/products"') - 80:html.index('href="/products"')]
    assert "active" in products_link


def test_customer_and_invoice_pages_open(client):
    customer = add_customer(client)
    assert client.get(f"/customers/{customer['id']}").status_code == 200
    assert client.get(f"/customers/{customer['id']}/invoice").status_code == 200


@pytest.mark.parametrize("path", [
    "/static/css/glass.css", "/static/js/common.js", "/static/js/theme.js", "/static/manifest.json",
    "/favicon.ico",
])
def test_static_files_are_served(anonymous, path):
    assert anonymous.get(path).status_code == 200
