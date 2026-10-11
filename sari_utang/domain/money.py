"""Amounts and quantities. Money is whole centavos (P12.50 = 1250) so sums have no rounding errors."""

from decimal import ROUND_HALF_UP, Decimal

MAX_PRICE = 100_000_00  # P100,000.00 in centavos, catches typos like an extra zero
MAX_QUANTITY = Decimal("10000")
MAX_DECIMALS = 3  # 0.125 kg


def peso(centavos):
    """1250 -> "₱12.50" """
    return f"₱{centavos / 100:,.2f}"


def qty(quantity):
    """2.0 -> "2", 0.5 -> "0.5" """
    return f"{Decimal(str(quantity)).normalize():f}"


def is_whole_number(value):
    """True for an int. bool is a kind of int in Python, so True/False are ruled out."""
    return isinstance(value, int) and not isinstance(value, bool)


def parse_quantity(value):
    """A quantity like 2 or 0.5 as a Decimal, or None if it isn't valid.

    Decimal is used instead of float so 0.1 + 0.2 is exactly 0.3 when computing amounts.
    """
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        return None
    quantity = Decimal(str(value))
    if not quantity.is_finite() or quantity <= 0 or quantity > MAX_QUANTITY:
        return None
    if quantity.as_tuple().exponent < -MAX_DECIMALS:
        return None
    return quantity


def line_amount(price, quantity):
    """price (centavos) x quantity, rounded to the nearest centavo (.5 rounds up)."""
    return int((price * quantity).quantize(Decimal("1"), rounding=ROUND_HALF_UP))
