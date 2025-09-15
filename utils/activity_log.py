"""Activity logging utilities for auditing user actions.

Table: activity_log(id, timestamp, username, action_type, details)
Added via migration 4.
"""

from __future__ import annotations

from datetime import datetime

from database.db_handler import get_db_connection


def log_action(username: str | None, action_type: str, details: str = ""):
    """Insert an action record. Username may be None (system events)."""
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute(
        """INSERT INTO activity_log(timestamp, username, action_type, details)
            VALUES(?, ?, ?, ?)""",
        (datetime.now().strftime("%Y-%m-%d %H:%M:%S"), username, action_type, details[:500]),
    )
    conn.commit()
    conn.close()


def fetch_recent(limit: int = 200) -> list[tuple]:
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute(
        """SELECT timestamp, COALESCE(username,'(system)'), action_type, details
               FROM activity_log ORDER BY id DESC LIMIT ?""",
        (limit,),
    )
    rows = cur.fetchall()
    conn.close()
    return rows
