"""Products import/export as an Excel file."""

from sari_utang import config, excel
from sari_utang.domain.product_import import check_header, check_rows
from sari_utang.errors import ValidationError
from sari_utang.services.base import Service

MAX_SHOWN_ERRORS = 20


class ProductExcelService(Service):
    def export(self):
        """All products as an Excel file in bytes."""
        return excel.products_workbook(self.products.all_products(), list(config.load_units()))

    def read(self, raw_bytes):
        """Check every row of an uploaded Excel file. Returns the products, or raises ValidationError
        listing the rows to fix. Nothing is saved here."""
        try:
            rows = excel.read_products_sheet(raw_bytes)
        except ValueError:
            self.fail(["This is not an Excel .xlsx file. In Excel, use Save As → Excel Workbook (.xlsx)."])
        header_error = check_header(rows[0] if rows else ())
        if header_error:
            self.fail([header_error])
        products, errors = check_rows(rows[1:], config.load_units())
        if errors:
            self.fail(errors)
        return products

    @staticmethod
    def fail(errors):
        raise ValidationError("Nothing was imported.", errors=errors[:MAX_SHOWN_ERRORS],
                              error_count=len(errors))

    def import_file(self, raw_bytes):
        """Add new products and update prices of existing ones (same name + unit).

        All or nothing: if any row has a problem, nothing is saved.
        Products that are not in the file are left as they are.
        """
        if not raw_bytes:
            self.fail(["Choose an Excel (.xlsx) file."])
        added = updated = unchanged = 0
        for product in self.read(raw_bytes):
            existing = self.products.find(product["name"], product["unit"])
            if existing is None:
                self.products.create(product["name"], product["price"], product["unit"])
                added += 1
            elif existing["price"] != product["price"]:
                self.products.update_price(existing["id"], product["price"])
                updated += 1
            else:
                unchanged += 1
        self.commit()  # everything is saved together
        return {"added": added, "updated": updated, "unchanged": unchanged}
