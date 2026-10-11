"""App settings that aren't business rules: where things are stored, sessions, and the store's
own config files (config/settings.json and config/units.json)."""

import json
import os
import secrets
import shutil
from datetime import timedelta

from sari_utang.domain.store_config import check_settings, check_units

MAX_UPLOAD_MB = 2

# config/ sits next to app.py, outside the package, so git ignores the store's own copies.
PROJECT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CONFIG_DIR = os.path.join(PROJECT_DIR, "config")
SETTINGS_FILE = os.path.join(CONFIG_DIR, "settings.json")
SETTINGS_EXAMPLE_FILE = os.path.join(CONFIG_DIR, "settings.example.json")
UNITS_FILE = os.path.join(CONFIG_DIR, "units.json")


def configure(app, test_config=None):
    """Set the database path, secret key and cookie settings on the Flask app."""
    # The instance/ folder holds private files (database, secret key). It is not committed to git.
    os.makedirs(app.instance_path, exist_ok=True)
    # SARI_UTANG_DATABASE lets the tests use a throwaway database.
    app.config["DATABASE"] = os.environ.get(
        "SARI_UTANG_DATABASE", os.path.join(app.instance_path, "sari_utang.db")
    )
    # Stay logged in for 30 days so the PIN isn't asked every time.
    app.config["PERMANENT_SESSION_LIFETIME"] = timedelta(days=30)
    app.config["SESSION_COOKIE_SAMESITE"] = "Lax"
    # Largest upload accepted (e.g. a products Excel file). Bigger requests get "413 Too Large".
    app.config["MAX_CONTENT_LENGTH"] = MAX_UPLOAD_MB * 1024 * 1024
    app.secret_key = load_secret_key(app.instance_path)
    ensure_config_files()
    if test_config:
        app.config.update(test_config)


def load_secret_key(instance_path):
    """The secret key signs the login cookie. Create one the first time and reuse it after."""
    path = os.path.join(instance_path, "secret_key")
    if not os.path.exists(path):
        with open(path, "w") as f:
            f.write(secrets.token_hex(32))
    with open(path) as f:
        return f.read().strip()


def ensure_config_files():
    """config/settings.json and config/units.json are this store's own copies, not in git.

    The first time, they are copied from the *.example.json files that come with the app.
    Because git ignores them, editing them (store name, units) never blocks an update.
    """
    for name in ("settings", "units"):
        path = os.path.join(CONFIG_DIR, f"{name}.json")
        if not os.path.exists(path):
            shutil.copyfile(os.path.join(CONFIG_DIR, f"{name}.example.json"), path)


def load_settings():
    """Read config/settings.json. Read every time, so edits show up on the next refresh.

    overdue_days: a credit unpaid for this many days or more counts as "overdue".
    store_name:   shown at the top of invoices (optional).
    """
    # Start from the example's values, so a setting added in a newer version
    # still has a value even if this store's settings.json doesn't have it yet.
    with open(SETTINGS_EXAMPLE_FILE, encoding="utf8") as f:
        settings = json.load(f)
    with open(SETTINGS_FILE, encoding="utf8") as f:
        own = json.load(f)
    return check_settings(settings, own, SETTINGS_FILE)


def load_units():
    """Read the units (what one "price" buys) from config/units.json.

    The file is read every time, so edits show up on the next page refresh.
    Format: {"kg": "kg (kilogram)", ...} -> the key is saved with the product,
    the text is shown in the dropdown. The first unit is the default.
    """
    with open(UNITS_FILE, encoding="utf8") as f:
        units = json.load(f)
    return check_units(units, UNITS_FILE)
