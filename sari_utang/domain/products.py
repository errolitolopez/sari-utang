"""Rules for products: name, price (centavos) and unit."""

from sari_utang.domain.money import MAX_PRICE, is_whole_number
from sari_utang.domain.text import clean_text
from sari_utang.errors import ValidationError

MAX_NAME_LENGTH = 100


def check_product(name, price, unit, units, current_unit=None):
    """The cleaned product {"name", "price", "unit"}.

    units: the unit keys from config/units.json.
    current_unit: when editing, the product's saved unit is still allowed even if
    it was removed from config/units.json, so the product can be saved unchanged.
    """
    name = clean_text(name)
    if not name:
        raise ValidationError("Name is required.")
    if len(name) > MAX_NAME_LENGTH:
        raise ValidationError(f"Name is too long (max {MAX_NAME_LENGTH} characters).")
    if not is_whole_number(price) or price <= 0:
        raise ValidationError("Price must be more than P0.")
    if price > MAX_PRICE:
        raise ValidationError("Price is too high (max P100,000).")
    if not isinstance(unit, str) or (unit not in units and unit != current_unit):
        raise ValidationError("Choose a unit from the list.")
    return {"name": name, "price": price, "unit": unit}
