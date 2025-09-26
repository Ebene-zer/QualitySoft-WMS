"""Simplified database schema migrations (squashed for first release).

Since no production release existed, previous incremental migrations were
consolidated into a single baseline migration (version 1).

Tables created:
  - products
  - customers
  - invoices
  - invoice_items
  - users (with must_change_password)
  - settings (with backup + retention + receipt + low stock columns)
  - activity_log

License / activation tables and columns were removed for the FREE edition.

If future changes are needed, add new forward-only migrations starting at
_migration_2 and bump CURRENT_SCHEMA_VERSION accordingly.
"""

from __future__ import annotations

import logging

logger = logging.getLogger(__name__)

CURRENT_SCHEMA_VERSION = 1


def _migration_1(cursor):
    logger.info("Applying squashed migration 1: create core tables")
    # Products
    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS products (
            product_id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            price REAL NOT NULL,
            stock_quantity INTEGER NOT NULL CHECK (stock_quantity >= 0)
        )
        """
    )
    # Customers
    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS customers (
            customer_id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            phone_number TEXT CHECK (LENGTH(phone_number) = 10),
            address TEXT
        )
        """
    )
    # Invoices
    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS invoices (
            invoice_id INTEGER PRIMARY KEY AUTOINCREMENT,
            customer_id INTEGER NOT NULL,
            invoice_date TEXT NOT NULL,
            discount REAL DEFAULT 0,
            tax REAL DEFAULT 0,
            total_amount REAL NOT NULL,
            FOREIGN KEY (customer_id) REFERENCES customers(customer_id)
        )
        """
    )
    # Invoice items
    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS invoice_items (
            item_id INTEGER PRIMARY KEY AUTOINCREMENT,
            invoice_id INTEGER NOT NULL,
            product_id INTEGER NOT NULL,
            quantity INTEGER NOT NULL CHECK (quantity > 0),
            unit_price REAL NOT NULL CHECK (unit_price >= 0),
            FOREIGN KEY (invoice_id) REFERENCES invoices(invoice_id) ON DELETE CASCADE,
            FOREIGN KEY (product_id) REFERENCES products(product_id)
        )
        """
    )
    # Users
    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS users (
            user_id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL,
            role TEXT NOT NULL DEFAULT 'Admin',
            must_change_password INTEGER NOT NULL DEFAULT 0
        )
        """
    )
    # Settings (includes consolidated columns from prior migrations)
    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS settings (
            id INTEGER PRIMARY KEY,
            wholesale_number TEXT,
            wholesale_name TEXT,
            wholesale_address TEXT,
            backup_directory TEXT,
            retention_count INTEGER,
            receipt_thank_you TEXT,
            receipt_notes TEXT,
            low_stock_threshold INTEGER
        )
        """
    )
    # Seed settings row if missing
    cursor.execute("SELECT COUNT(*) FROM settings WHERE id=1")
    if cursor.fetchone()[0] == 0:
        cursor.execute(
            """
            INSERT INTO settings (
                id, wholesale_number, wholesale_name, wholesale_address,
                backup_directory, retention_count, receipt_thank_you, receipt_notes, low_stock_threshold
            ) VALUES (1, '', 'Wholesale Name Here', '', '', 10, 'Thank you for buying from us!', '', 10)
            """
        )
    # Activity log
    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS activity_log (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp TEXT NOT NULL,
            username TEXT,
            action_type TEXT NOT NULL,
            details TEXT
        )
        """
    )
    # Indexes
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_invoices_customer_id ON invoices(customer_id)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_invoices_invoice_date ON invoices(invoice_date)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_items_invoice_id ON invoice_items(invoice_id)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_items_product_id ON invoice_items(product_id)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_activity_timestamp ON activity_log(timestamp)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_activity_user ON activity_log(username)")
    # Optional unique constraints for data integrity
    try:
        cursor.execute("CREATE UNIQUE INDEX IF NOT EXISTS idx_products_name_unique ON products(name COLLATE NOCASE)")
    except Exception:
        pass
    try:
        cursor.execute(
            # Wrapped to satisfy line length (ruff E501)
            "CREATE UNIQUE INDEX IF NOT EXISTS idx_customers_name_phone_unique "
            "ON customers(name COLLATE NOCASE, phone_number)"
        )
    except Exception:
        pass


MIGRATIONS = {1: _migration_1}

# --- schema_version helpers --- #

def _schema_table_exists(cursor) -> bool:
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='schema_version'")
    return cursor.fetchone() is not None


def _get_schema_version(cursor) -> int:
    if not _schema_table_exists(cursor):
        return 0
    cursor.execute("SELECT version FROM schema_version LIMIT 1")
    row = cursor.fetchone()
    return row[0] if row else 0


def _set_schema_version(cursor, version: int):
    if not _schema_table_exists(cursor):
        cursor.execute("CREATE TABLE schema_version (version INTEGER NOT NULL)")
        cursor.execute("INSERT INTO schema_version (version) VALUES (?)", (version,))
    else:
        cursor.execute("UPDATE schema_version SET version=?", (version,))


def run_migrations(cursor):
    current = _get_schema_version(cursor)
    target = CURRENT_SCHEMA_VERSION
    if current > target:
        raise RuntimeError(
            f"Database schema version {current} is newer than supported {target}. Upgrade application."
        )
    if current < target:
        # Apply only migration_1 (squashed) if fresh or outdated
        _migration_1(cursor)
        _set_schema_version(cursor, 1)
        logger.info("Schema initialized (squashed) at version 1")
    else:
        logger.info("Schema already at current version %s", target)


def get_current_schema_version(cursor) -> int:
    return _get_schema_version(cursor)
