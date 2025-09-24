from __future__ import annotations

from datetime import date, datetime, timedelta

__all__ = ["period_bounds", "normalize_kind"]


def _to_date(d: date | datetime) -> date:
    """Return a date from a date or datetime (drop time)."""
    if isinstance(d, datetime):
        return d.date()
    return d


def _iso(d: date) -> str:
    return d.strftime("%Y-%m-%d")


def normalize_kind(kind: str) -> str:
    """Normalize a period kind string to snake_case keywords.

    Examples:
    - "This Month" -> "this_month"
    - "last-7-days" -> "last_7_days"
    - "Week to Date" -> "week_to_date"
    """
    k = kind.strip().lower().replace("-", "_").replace(" ", "_")
    # collapse duplicate underscores
    while "__" in k:
        k = k.replace("__", "_")
    return k


def period_bounds(today: date | datetime, kind: str) -> tuple[str, str]:
    """Return start/end (end-exclusive) ISO dates for a given reporting period.

    Args:
        today: The anchor day for calculations (typically date.today()).
        kind: Period keyword, case-insensitive. Supported kinds:
            - today, yesterday
            - this_week, last_week, week_to_date
            - this_month, last_month, month_to_date
            - this_quarter, last_quarter, quarter_to_date
            - this_year, last_year, year_to_date
            - last_7_days, last_30_days, last_90_days

    Returns:
        (start_iso, end_iso_exclusive) as YYYY-MM-DD strings.

    Notes:
        - Weeks start on Monday (ISO-8601).
        - "last_X_days" includes today (e.g., last_7_days is 7 days ending today).
        - End is exclusive so it can be used directly in SQL: date >= start AND date < end.
    """
    d = _to_date(today)
    k = normalize_kind(kind)

    # Helpers
    def start_of_week(x: date) -> date:
        return x - timedelta(days=x.weekday())  # Monday

    def start_of_month(x: date) -> date:
        return x.replace(day=1)

    def start_of_next_month(x: date) -> date:
        if x.month == 12:
            return date(x.year + 1, 1, 1)
        return date(x.year, x.month + 1, 1)

    def start_of_quarter(x: date) -> date:
        q_start_month = 3 * ((x.month - 1) // 3) + 1
        return date(x.year, q_start_month, 1)

    def start_of_next_quarter(x: date) -> date:
        q_start = start_of_quarter(x)
        # add 3 months
        m = q_start.month + 3
        y = q_start.year + (m - 1) // 12
        m = ((m - 1) % 12) + 1
        return date(y, m, 1)

    def start_of_year(x: date) -> date:
        return date(x.year, 1, 1)

    def start_of_next_year(x: date) -> date:
        return date(x.year + 1, 1, 1)

    # Routing
    if k == "today":
        start = d
        end = d + timedelta(days=1)
    elif k == "yesterday":
        start = d - timedelta(days=1)
        end = d
    elif k == "this_week":
        start = start_of_week(d)
        end = start + timedelta(days=7)
    elif k == "last_week":
        end = start_of_week(d)
        start = end - timedelta(days=7)
    elif k == "week_to_date":
        start = start_of_week(d)
        end = d + timedelta(days=1)
    elif k == "this_month":
        start = start_of_month(d)
        end = start_of_next_month(d)
    elif k == "last_month":
        first_this = start_of_month(d)
        end = first_this
        # previous month start
        end_prev = first_this - timedelta(days=1)
        start = start_of_month(end_prev)
    elif k == "month_to_date":
        start = start_of_month(d)
        end = d + timedelta(days=1)
    elif k == "this_quarter":
        start = start_of_quarter(d)
        end = start_of_next_quarter(d)
    elif k == "last_quarter":
        first_this_q = start_of_quarter(d)
        end = first_this_q
        start = start_of_quarter(first_this_q - timedelta(days=1))
    elif k == "quarter_to_date":
        start = start_of_quarter(d)
        end = d + timedelta(days=1)
    elif k == "this_year":
        start = start_of_year(d)
        end = start_of_next_year(d)
    elif k == "last_year":
        end = start_of_year(d)
        start = start_of_year(date(d.year - 1, 1, 1))
    elif k == "year_to_date":
        start = start_of_year(d)
        end = d + timedelta(days=1)
    elif k == "last_7_days":
        start = d - timedelta(days=6)
        end = d + timedelta(days=1)
    elif k == "last_30_days":
        start = d - timedelta(days=29)
        end = d + timedelta(days=1)
    elif k == "last_90_days":
        start = d - timedelta(days=89)
        end = d + timedelta(days=1)
    else:
        raise ValueError(f"Unsupported period kind '{kind}'. See period_bounds.__doc__ for supported kinds.")

    return _iso(start), _iso(end)
