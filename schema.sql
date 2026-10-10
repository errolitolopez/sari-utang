-- Database tables for sari-utang.
-- Run with: flask --app app init-db

-- Simple key/value settings, e.g. the hashed login PIN.
CREATE TABLE IF NOT EXISTS settings (
    key   TEXT PRIMARY KEY,
    value TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS customers (
    id    INTEGER PRIMARY KEY AUTOINCREMENT,
    name  TEXT NOT NULL,
    phone TEXT
);

-- Every utang and every payment is one row.
-- amount is stored in centavos (P12.50 = 1250) so sums never have rounding errors.
CREATE TABLE IF NOT EXISTS transactions (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    customer_id INTEGER NOT NULL REFERENCES customers (id),
    type        TEXT NOT NULL CHECK (type IN ('utang', 'payment')),
    amount      INTEGER NOT NULL CHECK (amount > 0),
    note        TEXT,
    date        TEXT NOT NULL DEFAULT (datetime('now', 'localtime'))
);

-- Items sold in the store. price is in centavos, like transactions.amount.
CREATE TABLE IF NOT EXISTS products (
    id    INTEGER PRIMARY KEY AUTOINCREMENT,
    name  TEXT NOT NULL,
    price INTEGER NOT NULL CHECK (price > 0)
);
