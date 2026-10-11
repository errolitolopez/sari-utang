"""The invoice of a customer: page, PDF, and the ZIP of everyone's PDFs."""

import io
import zipfile
from datetime import date

from sari_utang import config
from sari_utang.domain.invoices import (
    build_invoice, invoice_text, safe_filename, sms_link, unique_filename, unpaid_entries,
)
from sari_utang.errors import NotFoundError
from sari_utang.invoice_pdf import invoice_pdf_bytes
from sari_utang.services.base import Service
from sari_utang.services.collection import CollectionService
from sari_utang.services.customers import CustomerService


class InvoiceService(Service):
    def invoice(self, customer_id):
        """Only the utang that is still unpaid, with items. Voided entries are left out."""
        entries, last_payment = unpaid_entries(self.transactions.active_for_customer(customer_id))
        by_id = {entry["id"]: entry for entry in entries}
        if by_id:
            for item in self.transactions.items_of(list(by_id)):
                by_id[item["transaction_id"]]["items"].append(dict(item))
        return build_invoice(entries, last_payment)

    def exists(self, customer_id):
        return CustomerService(self.db).exists(customer_id)

    def page(self, customer_id):
        """Everything the invoice page shows."""
        customer = CustomerService(self.db).require(customer_id)
        store_name = config.load_settings()["store_name"]
        invoice = self.invoice(customer_id)
        today = date.today().isoformat()
        text = invoice_text(store_name, customer["name"], invoice, today)
        return {
            "store_name": store_name,
            "customer": customer,
            "invoice": invoice,
            "today": today,
            "text": text,
            "sms_link": sms_link(customer["phone"], text),
        }

    def pdf(self, customer_id):
        """The invoice as a PDF. Returns (bytes, file name)."""
        customer = CustomerService(self.db).require(customer_id)
        today = date.today().isoformat()
        pdf = invoice_pdf_bytes(
            config.load_settings()["store_name"], customer, self.invoice(customer_id), today
        )
        return pdf, safe_filename(customer["name"], f"customer-{customer_id}") + ".pdf"

    def zip_of_all(self, min_days=0):
        """One PDF invoice per customer with utang, named after the customer, in one ZIP.

        min_days: only customers whose oldest unpaid utang is that many days old.
        Returns (bytes, file name).
        """
        owing = [c for c in CollectionService(self.db).owing() if c["days"] >= min_days]
        if not owing:
            raise NotFoundError("No customers with utang for this filter.")

        store_name = config.load_settings()["store_name"]
        today = date.today().isoformat()
        used_names = set()
        buffer = io.BytesIO()
        with zipfile.ZipFile(buffer, "w", zipfile.ZIP_DEFLATED) as archive:
            for row in owing:
                customer = self.customers.get_with_balance(row["id"])
                pdf = invoice_pdf_bytes(store_name, customer, self.invoice(row["id"]), today)
                base = safe_filename(customer["name"], f"customer-{customer['id']}")
                archive.writestr(unique_filename(base, used_names), pdf)
        return buffer.getvalue(), f"invoices-{today}.zip"
