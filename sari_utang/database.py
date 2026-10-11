"""The SQLite database: one connection per request, creating and upgrading the tables,
and the init-db command."""

import sqlite3

import click
from flask import current_app, g
from flask.cli import with_appcontext


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


def init_db():
    """Create the tables (safe to run again, existing data is kept)."""
    db = get_db()
    with current_app.open_resource("schema.sql") as f:
        db.executescript(f.read().decode("utf8"))
    add_missing_columns(db)


@click.command("init-db")
@with_appcontext
def init_db_command():
    """Create the tables (safe to run again, existing data is kept)."""
    init_db()
    click.echo("Database ready.")


def add_missing_columns(db):
    """Update tables made by an older version of schema.sql.

    CREATE TABLE IF NOT EXISTS skips tables that already exist, so new columns
    have to be added here for databases created before the column existed.
    """
    product_columns = [row["name"] for row in db.execute("PRAGMA table_info(products)")]
    if "unit" not in product_columns:
        db.execute("ALTER TABLE products ADD COLUMN unit TEXT NOT NULL DEFAULT 'pc'")

    transaction_columns = [row["name"] for row in db.execute("PRAGMA table_info(transactions)")]
    if "voided_at" not in transaction_columns:
        db.execute("ALTER TABLE transactions ADD COLUMN voided_at TEXT")
    if "void_reason" not in transaction_columns:
        db.execute("ALTER TABLE transactions ADD COLUMN void_reason TEXT")
    if "tendered" not in transaction_columns:
        db.execute("ALTER TABLE transactions ADD COLUMN tendered INTEGER")
    db.commit()


def init_app(app):
    """Register the database helpers with the Flask app."""
    app.teardown_appcontext(close_db)
    app.cli.add_command(init_db_command)
