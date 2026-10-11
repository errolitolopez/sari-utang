"""How things are sent to the browser (the JSON shapes the pages expect)."""


def customer_json(row):
    return {"id": row["id"], "name": row["name"], "phone": row["phone"], "balance": row["balance"]}


def product_json(row):
    return {"id": row["id"], "name": row["name"], "price": row["price"], "unit": row["unit"]}


def item_json(row):
    return {
        "transaction_id": row["transaction_id"],
        "product_id": row["product_id"],
        "name": row["name"],
        "unit": row["unit"],
        "price": row["price"],
        "quantity": row["quantity"],
        "amount": row["amount"],
    }


def transaction_json(row, items):
    """One debt or payment of the customer's history, with its items (payments have none)."""
    return {
        "id": row["id"],
        "type": row["type"],
        "amount": row["amount"],
        "note": row["note"],
        "date": row["date"],
        "voided_at": row["voided_at"],
        "void_reason": row["void_reason"],
        "tendered": row["tendered"],
        "items": items,
    }


def recent_json(row):
    """A line of the dashboard's recent transactions."""
    return {
        "id": row["id"],
        "type": row["type"],
        "amount": row["amount"],
        "note": row["note"],
        "date": row["date"],
        "customer_id": row["customer_id"],
        "customer_name": row["customer_name"],
    }
