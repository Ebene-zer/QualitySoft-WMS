"""Application settings access helpers.

Provides safe readers for optional settings fields with sensible defaults,
so UI and features can consume settings without dealing with schema errors.
"""

from __future__ import annotations

import sqlite3

from database.db_handler import get_db_connection

DEFAULT_LOW_STOCK_THRESHOLD = 10


def get_low_stock_threshold() -> int:
    """Return configured low-stock threshold, defaulting to 10 if unavailable.

    Handles cases where the settings table/column may not exist yet.
    """
    conn = get_db_connection()
    try:
        cur = conn.cursor()
        try:
            cur.execute("SELECT low_stock_threshold FROM settings WHERE id=1")
            row = cur.fetchone()
            if not row:
                return DEFAULT_LOW_STOCK_THRESHOLD
            try:
                val = int(row[0]) if row[0] is not None else DEFAULT_LOW_STOCK_THRESHOLD
                return val if val >= 0 else DEFAULT_LOW_STOCK_THRESHOLD
            except Exception:
                return DEFAULT_LOW_STOCK_THRESHOLD
        except sqlite3.OperationalError:
            # Column/table missing; return default
            return DEFAULT_LOW_STOCK_THRESHOLD
    finally:
        conn.close()
