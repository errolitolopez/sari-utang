"""The customers table, with each customer's balance."""

from sari_utang.repositories.base import Repository

# Voided transactions are left out of every balance.
BALANCES_SQL = """
    SELECT c.id, c.name, c.phone,
           COALESCE(SUM(CASE WHEN t.type = 'utang' THEN t.amount ELSE -t.amount END), 0)
               AS balance
    FROM customers c
    LEFT JOIN transactions t ON t.customer_id = c.id AND t.voided_at IS NULL
"""
# Highest utang first, then A-Z.
BALANCE_ORDER = "balance DESC, c.name COLLATE NOCASE"
SEARCH_WHERE = "WHERE (c.name LIKE ? ESCAPE '\\' OR c.phone LIKE ? ESCAPE '\\')"


class CustomerRepository(Repository):
    def with_balances(self):
        """All customers with their balance (total utang - total payments, in centavos)."""
        return self.all(f"{BALANCES_SQL} GROUP BY c.id ORDER BY {BALANCE_ORDER}")

    def get_with_balance(self, customer_id):
        """One customer with their balance, or None if there is no such customer."""
        return self.one(f"{BALANCES_SQL} WHERE c.id = ? GROUP BY c.id", (customer_id,))

    def count(self):
        return self.value("SELECT COUNT(*) FROM customers")

    def count_with_utang(self):
        return self.value(f"SELECT COUNT(*) FROM ({BALANCES_SQL} GROUP BY c.id HAVING balance > 0)")

    def count_matching(self, pattern):
        """How many customers have the LIKE pattern in their name or phone."""
        return self.value(f"SELECT COUNT(*) FROM customers c {SEARCH_WHERE}", (pattern, pattern))

    def search_page(self, pattern, limit, offset):
        """One page of the customers whose name or phone matches the LIKE pattern."""
        return self.all(
            f"{BALANCES_SQL} {SEARCH_WHERE} GROUP BY c.id ORDER BY {BALANCE_ORDER} LIMIT ? OFFSET ?",
            (pattern, pattern, limit, offset),
        )

    def name_taken(self, name):
        """True if a customer already has this name (any capitals)."""
        return self.one("SELECT 1 FROM customers WHERE name = ? COLLATE NOCASE", (name,)) is not None

    def create(self, name, phone):
        return self.execute("INSERT INTO customers (name, phone) VALUES (?, ?)", (name, phone)).lastrowid
