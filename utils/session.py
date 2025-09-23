"""Simple in-process session context for current authenticated user.

Avoids threading complexity; sufficient for single-user desktop app.
"""

_current_username = None
_current_role = None

# Session-scoped UX flags
_low_stock_alert_shown = False
_welcome_greeting_shown = False


def set_current_user(username: str, role: str):
    global _current_username, _current_role
    _current_username = username
    _current_role = role


def get_current_username() -> str | None:
    return _current_username


def get_current_role() -> str | None:
    return _current_role


# Low stock alert visibility control (per app session)


def get_low_stock_alert_shown() -> bool:
    return _low_stock_alert_shown


def set_low_stock_alert_shown(shown: bool = True):
    global _low_stock_alert_shown
    _low_stock_alert_shown = shown


# Welcome greeting visibility control (per app session)


def get_welcome_shown() -> bool:
    return _welcome_greeting_shown


def set_welcome_shown(shown: bool = True):
    global _welcome_greeting_shown
    _welcome_greeting_shown = shown
