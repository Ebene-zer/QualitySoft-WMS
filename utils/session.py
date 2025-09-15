"""Simple in-process session context for current authenticated user.

Avoids threading complexity; sufficient for single-user desktop app.
"""

_current_username = None
_current_role = None


def set_current_user(username: str, role: str):
    global _current_username, _current_role
    _current_username = username
    _current_role = role


def get_current_username() -> str | None:
    return _current_username


def get_current_role() -> str | None:
    return _current_role
