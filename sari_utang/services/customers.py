"""The customer list and adding a customer."""

from sari_utang.domain.customers import check_customer
from sari_utang.domain.paging import page_numbers
from sari_utang.domain.text import like_pattern
from sari_utang.errors import ConflictError, NotFoundError
from sari_utang.services.base import Service
from sari_utang.services.presenters import customer_json


class CustomerService(Service):
    def require(self, customer_id):
        """The customer with their balance, or NotFoundError."""
        customer = self.customers.get_with_balance(customer_id)
        if customer is None:
            raise NotFoundError("Customer not found.")
        return customer

    def exists(self, customer_id):
        return self.customers.get_with_balance(customer_id) is not None

    def list(self, page=None, per_page=20, query=""):
        """Customers with their balance, highest utang first (then A-Z).

        Without a page: all customers.
        With a page: one page of the customers whose name or phone has the query.
        """
        if page is None:
            return {"customers": [customer_json(row) for row in self.customers.with_balances()]}

        pattern = like_pattern(query)
        total = self.customers.count_matching(pattern)
        page, per_page, pages, offset = page_numbers(total, page, per_page)
        rows = self.customers.search_page(pattern, per_page, offset)
        return {
            "customers": [customer_json(row) for row in rows],
            "page": page, "per_page": per_page, "pages": pages, "total": total,
            # For the "10 total · 7 may utang" line (all customers, not just this search).
            "all_count": self.customers.count(),
            "with_utang_count": self.customers.count_with_utang(),
        }

    def create(self, data):
        name, phone = check_customer(data.get("name", ""), data.get("phone"))
        # Two customers with the same name would be confusing in the list.
        if self.customers.name_taken(name):
            raise ConflictError(f"{name} is already in the list.")
        customer_id = self.customers.create(name, phone)
        self.commit()
        return {"id": customer_id, "name": name, "phone": phone, "balance": 0}
