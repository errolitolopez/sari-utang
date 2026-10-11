"""The products table."""

from sari_utang.repositories.base import Repository

ORDER = "ORDER BY name COLLATE NOCASE, price"


class ProductRepository(Repository):
    def get(self, product_id):
        """The product, or None."""
        return self.one("SELECT id, name, unit, price FROM products WHERE id = ?", (product_id,))

    def all_products(self):
        return self.all(f"SELECT id, name, price, unit FROM products {ORDER}")

    def count(self):
        return self.value("SELECT COUNT(*) FROM products")

    def count_matching(self, pattern):
        return self.value("SELECT COUNT(*) FROM products WHERE name LIKE ? ESCAPE '\\'", (pattern,))

    def search_page(self, pattern, limit, offset):
        """One page of the products whose name matches the LIKE pattern."""
        return self.all(
            f"SELECT id, name, price, unit FROM products WHERE name LIKE ? ESCAPE '\\' {ORDER} "
            "LIMIT ? OFFSET ?",
            (pattern, limit, offset),
        )

    def find(self, name, unit):
        """The product with this name (any capitals) and unit, or None."""
        return self.one(
            "SELECT id, price FROM products WHERE name = ? COLLATE NOCASE AND unit = ?", (name, unit)
        )

    def taken(self, name, unit, except_id=None):
        """True if another product already has this name AND unit.

        The same name with a different unit is allowed, e.g. Coke Mismo per pc and per box.
        except_id: when editing, the product being edited doesn't count as "another".
        """
        row = self.one(
            "SELECT 1 FROM products WHERE name = ? COLLATE NOCASE AND unit = ? AND id != ?",
            (name, unit, except_id or 0),
        )
        return row is not None

    def create(self, name, price, unit):
        return self.execute(
            "INSERT INTO products (name, price, unit) VALUES (?, ?, ?)", (name, price, unit)
        ).lastrowid

    def update(self, product_id, name, price, unit):
        self.execute(
            "UPDATE products SET name = ?, price = ?, unit = ? WHERE id = ?",
            (name, price, unit, product_id),
        )

    def update_price(self, product_id, price):
        self.execute("UPDATE products SET price = ? WHERE id = ?", (price, product_id))
