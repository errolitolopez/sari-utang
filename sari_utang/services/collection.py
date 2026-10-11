"""Who to collect from (Singilin) and the dashboard summary."""

from datetime import date

from sari_utang import config
from sari_utang.domain.collection import collection_list
from sari_utang.services.base import Service
from sari_utang.services.presenters import recent_json

TOP_BALANCES = 5
RECENT_TRANSACTIONS = 5


class CollectionService(Service):
    def owing(self):
        """Everyone who owes, longest waiting first."""
        return collection_list(self.transactions.active_with_customers(), date.today())

    def singilin(self):
        return {"customers": self.owing(), "overdue_days": config.load_settings()["overdue_days"]}

    def dashboard(self):
        balances = self.customers.with_balances()
        with_utang = [row for row in balances if row["balance"] > 0]

        overdue_days = config.load_settings()["overdue_days"]
        overdue = [c for c in self.owing() if c["days"] >= overdue_days]

        return {
            "overdue_days": overdue_days,
            "overdue_count": len(overdue),
            "total_outstanding": sum(row["balance"] for row in with_utang),
            "customer_count": len(balances),
            "customers_with_utang": len(with_utang),
            "top_balances": [dict(row) for row in with_utang[:TOP_BALANCES]],
            "recent_transactions": [
                recent_json(row) for row in self.transactions.recent(RECENT_TRANSACTIONS)
            ],
        }
