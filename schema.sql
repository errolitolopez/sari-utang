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
-- A mistake is voided, not deleted: voided_at is set and the row no longer counts
-- in balances, but it stays in the history.
CREATE TABLE IF NOT EXISTS transactions (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    customer_id INTEGER NOT NULL REFERENCES customers (id),
    type        TEXT NOT NULL CHECK (type IN ('utang', 'payment')),
    amount      INTEGER NOT NULL CHECK (amount > 0),
    note        TEXT,
    date        TEXT NOT NULL DEFAULT (datetime('now', 'localtime')),
    voided_at   TEXT,
    void_reason TEXT
);

-- Items sold in the store. price is in centavos, like transactions.amount,
-- and is the price for one unit (e.g. P20.00 per pc, P65.00 per kg).
CREATE TABLE IF NOT EXISTS products (
    id    INTEGER PRIMARY KEY AUTOINCREMENT,
    name  TEXT NOT NULL,
    price INTEGER NOT NULL CHECK (price > 0),
    unit  TEXT NOT NULL DEFAULT 'pc'
);

-- What was bought in each utang. Name, unit and price are copied from the product
-- at that moment, so changing a product's price later doesn't change old utang.
-- product_id is empty for items typed in by hand ("other item").
CREATE TABLE IF NOT EXISTS transaction_items (
    id             INTEGER PRIMARY KEY AUTOINCREMENT,
    transaction_id INTEGER NOT NULL REFERENCES transactions (id),
    product_id     INTEGER REFERENCES products (id),
    name           TEXT NOT NULL,
    unit           TEXT,
    price          INTEGER NOT NULL CHECK (price > 0),
    quantity       REAL NOT NULL CHECK (quantity > 0),
    amount         INTEGER NOT NULL CHECK (amount > 0)
);
