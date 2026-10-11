"""Data access: every SQL query lives in these classes. Each takes the database connection;
none of them commits (the service decides when the work is done)."""

from sari_utang.repositories.customers import CustomerRepository
from sari_utang.repositories.products import ProductRepository
from sari_utang.repositories.settings import SettingsRepository
from sari_utang.repositories.transactions import TransactionRepository

__all__ = ["CustomerRepository", "ProductRepository", "SettingsRepository", "TransactionRepository"]
