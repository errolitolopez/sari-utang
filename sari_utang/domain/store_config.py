"""Rules for the store's config files (settings.json and units.json)."""

MAX_STORE_NAME_LENGTH = 60
MAX_OVERDUE_DAYS = 365


def check_settings(settings, own, path):
    """The example settings updated with the store's own, or ValueError if a value is wrong."""
    if not isinstance(own, dict):
        raise ValueError(f'{path} must look like {{"overdue_days": 30}}')
    settings.update(own)
    days = settings.get("overdue_days")
    if not isinstance(days, int) or isinstance(days, bool) or not 1 <= days <= MAX_OVERDUE_DAYS:
        raise ValueError(f'{path} must look like {{"overdue_days": 30}} (1 to {MAX_OVERDUE_DAYS})')
    store_name = settings.setdefault("store_name", "Sari-Sari Store")
    if not isinstance(store_name, str) or not 0 < len(store_name.strip()) <= MAX_STORE_NAME_LENGTH:
        raise ValueError(f'{path}: "store_name" must be text, 1 to {MAX_STORE_NAME_LENGTH} characters')
    return settings


def check_units(units, path):
    """The units as they are, or ValueError if the file doesn't look like {"pc": "pc (piraso)"}."""
    valid = (
        isinstance(units, dict)
        and units
        and all(isinstance(k, str) and k.strip() and isinstance(v, str) for k, v in units.items())
    )
    if not valid:
        raise ValueError(f'{path} must look like {{"pc": "pc (piraso)", "kg": "kg (kilo)"}}')
    return units
