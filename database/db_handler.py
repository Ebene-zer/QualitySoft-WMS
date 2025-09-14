import logging
import os
import sqlite3

from . import migrations

DB_ENV_KEY = "WMS_DB_NAME"
DEFAULT_DB_FILENAME = "wholesale.db"

logger = logging.getLogger(__name__)


def get_db_connection(db_name=None):
    if db_name is None:
        db_name = os.environ.get(DB_ENV_KEY, DEFAULT_DB_FILENAME)
    conn = sqlite3.connect(db_name, timeout=10)
    try:
        conn.execute("PRAGMA foreign_keys = ON")
    except Exception:
        conn.close()
        raise
    return conn


def initialize_database():
    """Create / migrate database schema to the current version."""
    conn = get_db_connection()
    cur = conn.cursor()
    try:
        migrations.run_migrations(cur)
        conn.commit()
    except Exception as e:
        conn.rollback()
        logger.error("Database initialization failed: %s", e)
        raise
    finally:
        conn.close()


def get_schema_version():
    """Return current schema version stored in the database (0 if uninitialized)."""
    conn = get_db_connection()
    cur = conn.cursor()
    try:
        return migrations.get_current_schema_version(cur)
    finally:
        conn.close()
