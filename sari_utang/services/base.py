"""What every service shares."""

from sari_utang.repositories import (
    CustomerRepository, ProductRepository, SettingsRepository, TransactionRepository,
)


class Service:
    """A use case runs inside one service method: it checks the request, changes data through
    the repositories, and commits only when everything worked. On an error (sari_utang.errors)
    it stops, and nothing it changed is saved."""

    def __init__(self, db):
        self.db = db
        self.customers = CustomerRepository(db)
        self.products = ProductRepository(db)
        self.transactions = TransactionRepository(db)
        self.settings = SettingsRepository(db)

    def commit(self):
        self.db.commit()
