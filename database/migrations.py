"""Database schema migrations.

Contains discrete forward-only migration steps. To add a new migration:
1. Write _migration_<n>(cursor)
2. Increment CURRENT_SCHEMA_VERSION
3. Add mapping in MIGRATIONS dict

Migrations must be idempotent if partially applied (SQLite auto-commits DDL).
"""

from __future__ import annotations

import logging

logger = logging.getLogger(__name__)

CURRENT_SCHEMA_VERSION = 4


def _migration_1(cursor):
    logger.info("Applying migration 1: initial schema")
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS products (
            product_id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            price REAL NOT NULL,
            stock_quantity INTEGER NOT NULL CHECK (stock_quantity >= 0)
        )
    """)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS customers (
            customer_id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            phone_number TEXT CHECK (LENGTH(phone_number) = 10),
            address TEXT
        )
    """)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS invoices (
            invoice_id INTEGER PRIMARY KEY AUTOINCREMENT,
            customer_id INTEGER NOT NULL,
            invoice_date TEXT NOT NULL,
            discount REAL DEFAULT 0,
            tax REAL DEFAULT 0,
            total_amount REAL NOT NULL,
            FOREIGN KEY (customer_id) REFERENCES customers(customer_id)
        )
    """)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS invoice_items (
            item_id INTEGER PRIMARY KEY AUTOINCREMENT,
            invoice_id INTEGER NOT NULL,
            product_id INTEGER NOT NULL,
            quantity INTEGER NOT NULL CHECK (quantity > 0),
            unit_price REAL NOT NULL CHECK (unit_price >= 0),
            FOREIGN KEY (invoice_id) REFERENCES invoices(invoice_id) ON DELETE CASCADE,
            FOREIGN KEY (product_id) REFERENCES products(product_id)
        )
    """)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            user_id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL,
            role TEXT NOT NULL DEFAULT 'Admin',
            must_change_password INTEGER NOT NULL DEFAULT 0
        )
    """)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS license (
            id INTEGER PRIMARY KEY,
            trial_start TEXT,
            product_pin TEXT,
            trial_days INTEGER
        )
    """)
    cursor.execute("SELECT COUNT(*) FROM license")
    if cursor.fetchone()[0] == 0:
        cursor.execute("INSERT INTO license (id, trial_start, product_pin, trial_days) VALUES (1, DATE('now'), '', 14)")
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS settings (
            id INTEGER PRIMARY KEY,
            wholesale_number TEXT,
            wholesale_name TEXT,
            wholesale_address TEXT
        )
    """)
    cursor.execute("SELECT COUNT(*) FROM settings")
    if cursor.fetchone()[0] == 0:
        cursor.execute(
            "INSERT INTO settings (id, wholesale_number, wholesale_name, wholesale_address) "
            "VALUES (1, '', 'Wholesale Name Here', '')"
        )
    cursor.execute("PRAGMA table_info(settings)")
    settings_cols = [c[1] for c in cursor.fetchall()]
    if "wholesale_name" not in settings_cols:
        cursor.execute("ALTER TABLE settings ADD COLUMN wholesale_name TEXT")
        cursor.execute("UPDATE settings SET wholesale_name='Wholesale Name Here' WHERE id=1")
    if "wholesale_address" not in settings_cols:
        cursor.execute("ALTER TABLE settings ADD COLUMN wholesale_address TEXT")
        cursor.execute("UPDATE settings SET wholesale_address='' WHERE id=1")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_invoices_customer_id ON invoices(customer_id)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_items_invoice_id ON invoice_items(invoice_id)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_items_product_id ON invoice_items(product_id)")
    cursor.execute("PRAGMA table_info(users)")
    user_cols = [c[1] for c in cursor.fetchall()]
    if "must_change_password" not in user_cols:
        cursor.execute("ALTER TABLE users ADD COLUMN must_change_password INTEGER NOT NULL DEFAULT 0")


def _migration_2(cursor):
    logger.info("Applying migration 2: add backup_directory column to settings")
    cursor.execute("PRAGMA table_info(settings)")
    cols = [c[1] for c in cursor.fetchall()]
    if "backup_directory" not in cols:
        cursor.execute("ALTER TABLE settings ADD COLUMN backup_directory TEXT")
        # Initialize column with empty string
        cursor.execute("UPDATE settings SET backup_directory='' WHERE id=1")


def _migration_3(cursor):
    logger.info("Applying migration 3: add retention_count column to settings")
    cursor.execute("PRAGMA table_info(settings)")
    cols = [c[1] for c in cursor.fetchall()]
    if "retention_count" not in cols:
        cursor.execute("ALTER TABLE settings ADD COLUMN retention_count INTEGER")
        cursor.execute("UPDATE settings SET retention_count=10 WHERE id=1")


def _migration_4(cursor):
    logger.info("Applying migration 4: add activity_log table")
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS activity_log (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp TEXT NOT NULL,
            username TEXT,
            action_type TEXT NOT NULL,
            details TEXT
        )
    """)
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_activity_timestamp ON activity_log(timestamp)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_activity_user ON activity_log(username)")


MIGRATIONS = {1: _migration_1, 2: _migration_2, 3: _migration_3, 4: _migration_4}

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


# --- post-migration baseline data checks --- #


def _ensure_settings_row(cursor):
    """Ensure there is a settings row with id=1, adding sensible defaults if missing.
    Safe to run repeatedly and on older schemas (will only use existing columns).
    """
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='settings'")
    if cursor.fetchone() is None:
        return
    # Does row id=1 exist?
    try:
        cursor.execute("SELECT COUNT(*) FROM settings WHERE id=1")
        if cursor.fetchone()[0] > 0:
            # Also ensure default values exist for newer columns if NULL
            cursor.execute("PRAGMA table_info(settings)")
            cols = [c[1] for c in cursor.fetchall()]
            if "backup_directory" in cols:
                cursor.execute("UPDATE settings SET backup_directory=COALESCE(backup_directory, '') WHERE id=1")
            if "retention_count" in cols:
                cursor.execute("UPDATE settings SET retention_count=COALESCE(retention_count, 10) WHERE id=1")
            return
    except Exception:
        # If SELECT failed due to schema oddities, just return
        return
    # Insert a new row with available columns
    cursor.execute("PRAGMA table_info(settings)")
    cols = [c[1] for c in cursor.fetchall()]
    defaults = {
        "id": 1,
        "wholesale_number": "",
        "wholesale_name": "Wholesale Name Here",
        "wholesale_address": "",
        "backup_directory": "",
        "retention_count": 10,
    }
    present_cols = [c for c in defaults.keys() if c in cols]
    columns_sql = ",".join(present_cols)
    placeholders = ",".join(["?"] * len(present_cols))
    values = [defaults[c] for c in present_cols]
    if present_cols:
        cursor.execute(f"INSERT INTO settings ({columns_sql}) VALUES ({placeholders})", values)


def run_migrations(cursor):
    current = _get_schema_version(cursor)
    target = CURRENT_SCHEMA_VERSION
    if current > target:
        raise RuntimeError(f"Database schema version {current} is newer than supported {target}. Upgrade application.")
    for version in sorted(MIGRATIONS.keys()):
        if version > current and version <= target:
            MIGRATIONS[version](cursor)
            _set_schema_version(cursor, version)
            logger.info("Schema upgraded to version %s", version)
    # Always ensure baseline data after migrations (or when already up to date)
    _ensure_settings_row(cursor)


def get_current_schema_version(cursor) -> int:
    return _get_schema_version(cursor)
