"""Backup utilities for the Tradia application.

Features:
- Determine and create backup directory (configurable in settings.backup_directory)
- Perform consistent SQLite backup via backup API
- Retention policy using settings.retention_count (fallback 10)
- Helpers: list_backups, get_last_backup_time, needs_backup
"""

from __future__ import annotations

import datetime as _dt
import logging
import os
import sqlite3
from pathlib import Path

from database.db_handler import get_db_connection
from utils.branding import APP_SLUG

logger = logging.getLogger(__name__)

# Use filesystem-friendly slug for default location, e.g., ~/Documents/tradia/backups
DEFAULT_RELATIVE_BACKUP_PATH = os.path.join("Documents", APP_SLUG, "backups")
BACKUP_FILENAME_PREFIX = "backup_"  # backup_YYYYmmdd_HHMMSS.db
DEFAULT_RETENTION_FALLBACK = 10

# ---------- Settings access ---------- #


def _settings_columns():
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("PRAGMA table_info(settings)")
    cols = [c[1] for c in cur.fetchall()]
    conn.close()
    return cols


def _get_settings():
    """Safely fetch backup settings.

    Returns (backup_directory, retention_count) or (None, None) if the settings
    table/row isn't available yet. This prevents crashes when the database
    hasn't been initialized (e.g., during tests pointing to a non-existent DB).
    """
    conn = get_db_connection()
    try:
        cur = conn.cursor()
        try:
            cur.execute("SELECT backup_directory, retention_count FROM settings WHERE id=1")
            row = cur.fetchone()
            return row if row else (None, None)
        except sqlite3.OperationalError:
            # settings table is missing; fall back to defaults
            return (None, None)
    finally:
        conn.close()


def get_configured_backup_dir() -> str | None:
    backup_dir, _ = _get_settings()
    if not backup_dir:
        return None
    backup_dir_str = str(backup_dir).strip()
    return backup_dir_str or None


def get_default_backup_dir() -> str:
    home = os.path.expanduser("~")
    return os.path.join(home, DEFAULT_RELATIVE_BACKUP_PATH)


def resolve_backup_dir() -> str:
    path = get_configured_backup_dir() or get_default_backup_dir()
    os.makedirs(path, exist_ok=True)
    return path


def _get_retention_count() -> int:
    _, retention = _get_settings()
    try:
        val = int(retention) if retention is not None else DEFAULT_RETENTION_FALLBACK
        return val if val > 0 else DEFAULT_RETENTION_FALLBACK
    except Exception:
        return DEFAULT_RETENTION_FALLBACK


def update_backup_directory(new_dir: str):
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("UPDATE settings SET backup_directory=? WHERE id=1", (new_dir.strip(),))
    conn.commit()
    conn.close()


def update_retention_count(new_count: int):
    if new_count <= 0:
        raise ValueError("Retention count must be positive")
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("UPDATE settings SET retention_count=? WHERE id=1", (new_count,))
    conn.commit()
    conn.close()


# ---------- Backup core ---------- #


def _get_database_path() -> str:
    """Return the actual on-disk path of the main SQLite database.

    Primary: ask SQLite for the attached main DB path via PRAGMA database_list
    using the same connection logic as the app. This guarantees consistency with
    env overrides and default path computation.

    Fallbacks mirror db_handler defaults: respect WMS_DB_NAME, else
    Documents/tradia/data/wholesale.db (or TRADIA_DATA_DIR if set).
    """
    try:
        conn = get_db_connection()
        try:
            row = conn.execute("PRAGMA database_list").fetchone()
            if row and len(row) >= 3 and row[2]:
                return row[2]
        finally:
            conn.close()
    except Exception:
        pass
    # Fallbacks
    from database.db_handler import DB_ENV_KEY, DEFAULT_DB_FILENAME

    env_path = os.environ.get(DB_ENV_KEY)
    if env_path:
        return env_path
    base = os.getenv("TRADIA_DATA_DIR")
    base_path = Path(base).expanduser().resolve() if base else (Path.home() / "Documents" / APP_SLUG / "data")
    return str(base_path / DEFAULT_DB_FILENAME)


def list_backups(directory: str | None = None) -> list[str]:
    directory = directory or resolve_backup_dir()
    if not os.path.isdir(directory):
        return []
    backups: list[str] = []
    for name in os.listdir(directory):
        if name.startswith(BACKUP_FILENAME_PREFIX) and name.endswith(".db"):
            backups.append(os.path.join(directory, name))
    backups.sort(key=lambda p: os.path.getmtime(p))
    return backups


def get_last_backup_time(directory: str | None = None) -> _dt.datetime | None:
    backups = list_backups(directory)
    if not backups:
        return None
    latest = backups[-1]
    try:
        return _dt.datetime.fromtimestamp(os.path.getmtime(latest))
    except Exception:
        return None


def _enforce_retention(directory: str, retention: int):
    backups = list_backups(directory)
    if len(backups) <= retention:
        return
    # Remove oldest extra backups
    to_remove = backups[: len(backups) - retention]
    for path in to_remove:
        try:
            os.remove(path)
            logger.info("Deleted old backup: %s", path)
        except Exception as e:
            logger.warning("Failed deleting backup %s: %s", path, e)


def perform_backup(retention: int | None = None) -> str:
    backup_dir = resolve_backup_dir()
    db_path = _get_database_path()
    if not os.path.exists(db_path):
        raise FileNotFoundError(f"Database file not found: {db_path}")

    # Use microseconds to avoid collisions when creating multiple backups in the same second
    now = _dt.datetime.now()
    timestamp = now.strftime("%Y%m%d_%H%M%S_%f")
    backup_name = f"{BACKUP_FILENAME_PREFIX}{timestamp}.db"
    backup_path = os.path.join(backup_dir, backup_name)

    # Fallback uniqueness guard: if path exists, add a numeric suffix
    if os.path.exists(backup_path):
        idx = 1
        base, ext = os.path.splitext(backup_path)
        while os.path.exists(f"{base}_{idx}{ext}"):
            idx += 1
        backup_path = f"{base}_{idx}{ext}"

    source = sqlite3.connect(db_path, timeout=10)
    try:
        dest = sqlite3.connect(backup_path, timeout=10)
        try:
            source.backup(dest)
            dest.commit()
        finally:
            dest.close()
    finally:
        source.close()

    if os.path.getsize(backup_path) == 0:
        try:
            os.remove(backup_path)
        except Exception:
            pass
        raise RuntimeError("Backup created but file size was 0 bytes (removed).")

    logger.info("Backup created: %s", backup_path)
    if retention is None:
        retention = _get_retention_count()
    _enforce_retention(backup_dir, retention)
    return backup_path


def needs_backup(hours: int = 24) -> bool:
    last = get_last_backup_time()
    if last is None:
        return True
    return (_dt.datetime.now() - last).total_seconds() >= hours * 3600
