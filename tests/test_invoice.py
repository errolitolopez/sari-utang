"""Invoice page, text, PDF and the ZIP of all invoices."""

import io
import zipfile

from conftest import add_customer, add_payment, add_product, add_utang


def customer_with_utang(client, name="Aling Nena", phone=None):
    customer = add_customer(client, name, phone)
    coke = add_product(client, f"Coke for {name}", 2000, "bottle")
    add_utang(client, customer["id"], [{"product_id": coke["id"], "quantity": 3}])
    return customer


def test_invoice_page_lists_only_unpaid_utang(client):
    customer = add_customer(client)
    first = add_product(client, "Asin", 1000, "pack")
    second = add_product(client, "Itlog", 900, "pc")
    add_utang(client, customer["id"], [{"product_id": first["id"], "quantity": 1}])
    add_utang(client, customer["id"], [{"product_id": second["id"], "quantity": 4}])
    add_payment(client, customer["id"], 1500)  # pays Asin, 500 of Itlog

    html = client.get(f"/customers/{customer['id']}/invoice").get_data(as_text=True)
    assert "Itlog" in html
    assert "Asin" not in html
    assert "₱31.00" in html  # 3600 - 500 left
    assert "already paid" in html


def test_invoice_page_when_all_paid(client):
    customer = add_customer(client)
    html = client.get(f"/customers/{customer['id']}/invoice").get_data(as_text=True)
    assert "No credit. All paid." in html


def test_invoice_sms_link_needs_a_phone(client):
    with_phone = customer_with_utang(client, "Ben", "0917 123 4567")
    without_phone = customer_with_utang(client, "Carla")
    assert "sms:09171234567?body=" in client.get(f"/customers/{with_phone['id']}/invoice").get_data(as_text=True)
    assert "sms:" not in client.get(f"/customers/{without_phone['id']}/invoice").get_data(as_text=True)


def test_invoice_404(client):
    assert client.get("/customers/999/invoice").status_code == 404
    assert client.get("/customers/999/invoice.pdf").status_code == 404


def test_invoice_pdf(client):
    customer = customer_with_utang(client, "Jun/Ben?")
    response = client.get(f"/customers/{customer['id']}/invoice.pdf")
    assert response.status_code == 200
    assert response.mimetype == "application/pdf"
    assert response.data.startswith(b"%PDF")
    assert "JunBen.pdf" in response.headers["Content-Disposition"]


def test_zip_has_one_pdf_per_customer_with_unique_names(client):
    customer_with_utang(client, "Jun?")
    customer_with_utang(client, "Jun")
    add_customer(client, "Clean")

    response = client.get("/singilin/invoices.zip")
    assert response.mimetype == "application/zip"
    names = sorted(zipfile.ZipFile(io.BytesIO(response.data)).namelist())
    assert names == ["Jun (2).pdf", "Jun.pdf"]


def test_zip_with_nobody_is_404(client):
    add_customer(client, "Clean")
    assert client.get("/singilin/invoices.zip").status_code == 404
    customer_with_utang(client)
    assert client.get("/singilin/invoices.zip?min_days=30").status_code == 404
