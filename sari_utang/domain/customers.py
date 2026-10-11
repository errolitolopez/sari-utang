"""Rules for customers: name and phone."""

import re

from sari_utang.domain.text import clean_text
from sari_utang.errors import ValidationError

MAX_NAME_LENGTH = 100
PHONE_PATTERN = re.compile(r"[0-9+\- ]{7,20}")


def check_customer(name, phone):
    """The cleaned (name, phone). The phone is None when there is none."""
    name = clean_text(name)
    phone = str(phone or "").strip()
    if not name:
        raise ValidationError("Name is required.")
    if len(name) > MAX_NAME_LENGTH:
        raise ValidationError(f"Name is too long (max {MAX_NAME_LENGTH} characters).")
    if phone and not PHONE_PATTERN.fullmatch(phone):
        raise ValidationError("Phone can only have numbers, spaces, + and - (7 to 20 characters).")
    return name, phone or None
