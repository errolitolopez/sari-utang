"""The transactions (credit and payments) and the items of each credit."""

from sari_utang.repositories.base import Repository


class TransactionRepository(Repository):
    def get(self, transaction_id):
        return self.one(
            "SELECT id, customer_id, type, amount, voided_at FROM transactions WHERE id = ?",
            (transaction_id,),
        )

    def active_with_customers(self):
        """Every transaction that is not voided, oldest first, with the customer's name and phone."""
        return self.all(
            """
            SELECT t.customer_id, t.type, t.amount, t.date, c.name, c.phone
            FROM transactions t
            JOIN customers c ON c.id = t.customer_id
            WHERE t.voided_at IS NULL
            ORDER BY t.date, t.id
            """
        )

    def recent(self, limit):
        """The newest transactions that are not voided, with the customer's name."""
        return self.all(
            """
            SELECT t.id, t.type, t.amount, t.note, t.date, t.customer_id, c.name AS customer_name
            FROM transactions t
            JOIN customers c ON c.id = t.customer_id
            WHERE t.voided_at IS NULL
            ORDER BY t.date DESC, t.id DESC
            LIMIT ?
            """,
            (limit,),
        )

    def for_customer(self, customer_id):
        """All of one customer's transactions (voided too), newest first."""
        return self.all(
            """
            SELECT id, type, amount, note, date, voided_at, void_reason, tendered FROM transactions
            WHERE customer_id = ?
            ORDER BY date DESC, id DESC
            """,
            (customer_id,),
        )

    def items_for_customer(self, customer_id):
        """The items of all of one customer's credit."""
        return self.all(
            """
            SELECT i.transaction_id, i.product_id, i.name, i.unit, i.price, i.quantity, i.amount
            FROM transaction_items i
            JOIN transactions t ON t.id = i.transaction_id
            WHERE t.customer_id = ?
            ORDER BY i.id
            """,
            (customer_id,),
        )

    def active_for_customer(self, customer_id):
        """One customer's transactions that are not voided, oldest first."""
        return self.all(
            """
            SELECT id, type, amount, note, date FROM transactions
            WHERE customer_id = ? AND voided_at IS NULL
            ORDER BY date, id
            """,
            (customer_id,),
        )

    def items_of(self, transaction_ids):
        """The items of these transactions."""
        placeholders = ",".join("?" * len(transaction_ids))
        return self.all(
            f"SELECT transaction_id, name, unit, price, quantity, amount FROM transaction_items "
            f"WHERE transaction_id IN ({placeholders}) ORDER BY id",
            list(transaction_ids),
        )

    def create_utang(self, customer_id, total, note, items):
        """Save a credit and its items together. Returns the new transaction's id."""
        transaction_id = self.execute(
            "INSERT INTO transactions (customer_id, type, amount, note) VALUES (?, 'utang', ?, ?)",
            (customer_id, total, note),
        ).lastrowid
        self.db.executemany(
            """
            INSERT INTO transaction_items
                (transaction_id, product_id, name, unit, price, quantity, amount)
            VALUES (:transaction_id, :product_id, :name, :unit, :price, :quantity, :amount)
            """,
            [{**item, "transaction_id": transaction_id} for item in items],
        )
        return transaction_id

    def create_payment(self, customer_id, amount, note, tendered):
        return self.execute(
            "INSERT INTO transactions (customer_id, type, amount, note, tendered) "
            "VALUES (?, 'payment', ?, ?, ?)",
            (customer_id, amount, note, tendered),
        ).lastrowid

    def void(self, transaction_id, reason):
        self.execute(
            "UPDATE transactions SET voided_at = datetime('now', 'localtime'), void_reason = ? "
            "WHERE id = ?",
            (reason, transaction_id),
        )
