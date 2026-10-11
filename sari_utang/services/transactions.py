"""A customer's history, adding a debt or payment, and voiding one."""

from sari_utang.domain.money import is_whole_number
from sari_utang.domain.utang import KINDS, check_items, check_note, split_payment
from sari_utang.errors import NotFoundError, ValidationError
from sari_utang.services.base import Service
from sari_utang.services.customers import CustomerService
from sari_utang.services.presenters import customer_json, item_json, transaction_json


class TransactionService(Service):
    def history(self, customer_id):
        """The customer with their balance, and all their transactions with items."""
        customer = CustomerService(self.db).require(customer_id)

        # Put each item under its transaction.
        items_by_transaction = {}
        for item in self.transactions.items_for_customer(customer_id):
            items_by_transaction.setdefault(item["transaction_id"], []).append(item_json(item))
        transactions = [
            transaction_json(row, items_by_transaction.get(row["id"], []))
            for row in self.transactions.for_customer(customer_id)
        ]
        return {"customer": customer_json(customer), "transactions": transactions}

    def add(self, data):
        """Add a debt or a payment for a customer. Returns the JSON answer."""
        kind = data.get("type")
        if kind not in KINDS:
            raise ValidationError('type must be "utang" or "payment".')

        customer_id = data.get("customer_id")
        customer = self.customers.get_with_balance(customer_id) if is_whole_number(customer_id) else None
        if customer is None:
            raise NotFoundError("Customer not found.")

        note = check_note(data.get("note"))
        if kind == "utang":
            return self.add_utang(customer, data.get("items"), note)
        return self.add_payment(customer, data.get("amount"), note)

    def add_utang(self, customer, raw_items, note):
        items, total = check_items(raw_items, self.products.get)
        transaction_id = self.transactions.create_utang(customer["id"], total, note or None, items)
        self.commit()  # the transaction and its items are saved together
        return {"transaction": {"id": transaction_id, "amount": total, "items": items}}

    def add_payment(self, customer, amount, note):
        paid, change, tendered = split_payment(amount, customer["balance"], customer["name"])
        transaction_id = self.transactions.create_payment(customer["id"], paid, note or None, tendered)
        self.commit()
        return {
            "transaction": {"id": transaction_id, "amount": paid, "tendered": tendered},
            "change": change,
            "balance": customer["balance"] - paid,
        }

    def void(self, transaction_id, data):
        """Cancel a debt or payment entered by mistake. It stays in the history, crossed out."""
        transaction = self.transactions.get(transaction_id)
        if transaction is None:
            raise NotFoundError("Transaction not found.")
        if transaction["voided_at"] is not None:
            raise ValidationError("This is already voided.")

        reason = check_note(data.get("reason"), what="Reason")

        # Voiding a debt lowers the balance. If part of it was already paid, the
        # balance would go below zero, so the payment has to be voided first.
        customer = self.customers.get_with_balance(transaction["customer_id"])
        if transaction["type"] == "utang" and customer["balance"] - transaction["amount"] < 0:
            raise ValidationError(
                "Part of this debt was already paid. Void the payment first, then this debt."
            )

        self.transactions.void(transaction_id, reason or None)
        self.commit()

        change = -transaction["amount"] if transaction["type"] == "utang" else transaction["amount"]
        return {"ok": True, "balance": customer["balance"] + change}
