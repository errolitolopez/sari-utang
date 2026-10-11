"""Who owes, and how long their oldest unpaid utang has been waiting."""

from datetime import date


def collection_list(rows, today):
    """Everyone who owes, with how long their oldest unpaid utang has been waiting.

    rows: the customers' transactions that are not voided, oldest first, each with
    customer_id, type, amount, date, name and phone.

    Payments pay off the oldest utang first. So for each customer we add up all
    their payments, then go through their utang from oldest to newest, crossing
    off each one the payments fully cover. The first one left is the oldest unpaid.
    """
    customers = {}  # customer id -> what we know about them
    for row in rows:
        c = customers.setdefault(row["customer_id"], {
            "id": row["customer_id"], "name": row["name"], "phone": row["phone"],
            "utang": [], "paid": 0, "last_payment": None,
        })
        if row["type"] == "utang":
            c["utang"].append(row)
        else:
            c["paid"] += row["amount"]
            c["last_payment"] = row["date"]  # rows are oldest first, so the last one wins

    result = []
    for c in customers.values():
        balance = sum(u["amount"] for u in c["utang"]) - c["paid"]
        if balance <= 0:
            continue

        left_to_cover = c["paid"]
        unpaid_since = None
        for u in c["utang"]:
            if left_to_cover >= u["amount"]:
                left_to_cover -= u["amount"]  # fully paid
            else:
                unpaid_since = u["date"]  # oldest utang not fully paid yet
                break

        since_day = date.fromisoformat(unpaid_since[:10])  # "2026-10-10 10:15:22" -> 2026-10-10
        result.append({
            "id": c["id"],
            "name": c["name"],
            "phone": c["phone"],
            "balance": balance,
            "unpaid_since": unpaid_since,
            "days": (today - since_day).days,
            "last_payment": c["last_payment"],
        })

    result.sort(key=lambda c: (-c["days"], -c["balance"]))  # longest waiting first
    return result
