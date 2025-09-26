import logging
import os
import sqlite3
from pathlib import Path

from . import migrations

DB_ENV_KEY = "WMS_DB_NAME"
DEFAULT_DB_FILENAME = "wholesale.db"

logger = logging.getLogger(__name__)


def _default_db_path() -> str:
    """Return a user-writable default database path.

    Priority:
      1. Respect TRADIA_DATA_DIR if set (for portability/testing)
      2. Documents/tradia/data/wholesale.db
    """
    base = os.getenv("TRADIA_DATA_DIR")
    if base:
        base_path = Path(base).expanduser().resolve()
    else:
        base_path = Path.home() / "Documents" / "tradia" / "data"
    try:
        base_path.mkdir(parents=True, exist_ok=True)
    except Exception:
        # As a last resort, fall back to current working directory
        return DEFAULT_DB_FILENAME
    return str(base_path / DEFAULT_DB_FILENAME)


def get_db_connection(db_name=None):
    if not db_name:
        # Environment override takes precedence
        env_db = os.environ.get(DB_ENV_KEY)
        db_name = env_db if env_db else _default_db_path()
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
    """Return the current schema version stored in the database (0 if uninitialized)."""
    conn = get_db_connection()
    cur = conn.cursor()
    try:
        return migrations.get_current_schema_version(cur)
    finally:
        conn.close()
