"""The product list: search, add and edit."""

from sari_utang import config
from sari_utang.domain.paging import page_numbers
from sari_utang.domain.products import check_product
from sari_utang.domain.text import like_pattern
from sari_utang.errors import ConflictError, NotFoundError
from sari_utang.services.base import Service
from sari_utang.services.presenters import product_json


class ProductService(Service):
    def units(self):
        """The units from config/units.json (key -> text for the dropdown)."""
        return config.load_units()

    def list(self, page=None, per_page=20, query=""):
        """Products, A-Z.

        Without a page: all products (the utang form searches all of them).
        With a page: one page of the products whose name has the query.
        """
        if page is None:
            return {"products": [product_json(row) for row in self.products.all_products()]}

        pattern = like_pattern(query)
        total = self.products.count_matching(pattern)
        page, per_page, pages, offset = page_numbers(total, page, per_page)
        rows = self.products.search_page(pattern, per_page, offset)
        return {
            "products": [product_json(row) for row in rows],
            "page": page, "per_page": per_page, "pages": pages, "total": total,
            "all_count": self.products.count(),
        }

    def clean_fields(self, data, current_unit=None, product_id=None):
        product = check_product(
            data.get("name", ""), data.get("price"), data.get("unit"), self.units(), current_unit
        )
        if self.products.taken(product["name"], product["unit"], except_id=product_id):
            raise ConflictError(f"{product['name']} per {product['unit']} is already in the list.")
        return product

    def create(self, data):
        product = self.clean_fields(data)
        product_id = self.products.create(product["name"], product["price"], product["unit"])
        self.commit()
        return {"id": product_id, **product}

    def update(self, product_id, data):
        saved = self.products.get(product_id)
        if saved is None:
            raise NotFoundError("Product not found.")
        product = self.clean_fields(data, current_unit=saved["unit"], product_id=product_id)
        self.products.update(product_id, product["name"], product["price"], product["unit"])
        self.commit()
        return {"id": product_id, **product}
