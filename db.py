"""Database helpers: open/close the SQLite connection and CLI setup commands."""

import sqlite3

import click
from flask import current_app, g
from flask.cli import with_appcontext
from werkzeug.security import generate_password_hash


def get_db():
    """Return the database connection for the current request (opened once per request)."""
    if "db" not in g:
        g.db = sqlite3.connect(current_app.config["DATABASE"])
        g.db.row_factory = sqlite3.Row  # rows behave like dicts: row["name"]
        g.db.execute("PRAGMA foreign_keys = ON")
    return g.db


def close_db(error=None):
    db = g.pop("db", None)
    if db is not None:
        db.close()


def get_setting(key):
    row = get_db().execute("SELECT value FROM settings WHERE key = ?", (key,)).fetchone()
    return row["value"] if row else None


@click.command("init-db")
@with_appcontext
def init_db_command():
    """Create the tables (safe to run again, existing data is kept)."""
    db = get_db()
    with current_app.open_resource("schema.sql") as f:
        db.executescript(f.read().decode("utf8"))
    add_missing_columns(db)
    click.echo("Database ready.")


def add_missing_columns(db):
    """Update tables made by an older version of schema.sql.

    CREATE TABLE IF NOT EXISTS skips tables that already exist, so new columns
    have to be added here for databases created before the column existed.
    """
    product_columns = [row["name"] for row in db.execute("PRAGMA table_info(products)")]
    if "unit" not in product_columns:
        db.execute("ALTER TABLE products ADD COLUMN unit TEXT NOT NULL DEFAULT 'pc'")
    db.commit()


@click.command("set-pin")
@with_appcontext
@click.password_option("--pin", prompt="New PIN", help="4 to 6 digits.")
def set_pin_command(pin):
    """Set or change the login PIN."""
    if not (pin.isdigit() and 4 <= len(pin) <= 6):
        raise click.BadParameter("PIN must be 4 to 6 digits.")
    db = get_db()
    # Only the hash is saved, never the PIN itself.
    db.execute(
        "INSERT INTO settings (key, value) VALUES ('pin_hash', ?) "
        "ON CONFLICT (key) DO UPDATE SET value = excluded.value",
        (generate_password_hash(pin),),
    )
    db.commit()
    click.echo("PIN saved.")


def init_app(app):
    """Register the database helpers with the Flask app."""
    app.teardown_appcontext(close_db)
    app.cli.add_command(init_db_command)
    app.cli.add_command(set_pin_command)
