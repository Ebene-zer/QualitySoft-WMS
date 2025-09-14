import random
import string
from datetime import datetime, timedelta

from database.db_handler import get_db_connection

# Allowed columns for license updates to avoid SQL injection via field parameter
_ALLOWED_LICENSE_FIELDS = {"trial_start", "product_pin", "trial_days"}


def get_license_row():
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("SELECT trial_start, product_pin, trial_days FROM license WHERE id=1")
    row = cur.fetchone()
    conn.close()
    return row


def set_license_field(field, value):
    if field not in _ALLOWED_LICENSE_FIELDS:
        raise ValueError(f"Invalid license field: {field}")
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute(f"UPDATE license SET {field}=? WHERE id=1", (value,))
    conn.commit()
    conn.close()


def is_trial_expired():
    trial_start, _, trial_days = get_license_row()
    # Support both Day/Month/Year and ISO Year-Month-Day stored formats for backward compatibility
    start_date = None
    for fmt in ("%d/%m/%Y", "%Y-%m-%d"):
        try:
            start_date = datetime.strptime(trial_start, fmt)
            break
        except Exception:
            continue
    if start_date is None:
        # If parsing fails, treat as expired to be safe
        return True
    return (datetime.now() - start_date).days >= int(trial_days)


def generate_product_pin(length=8):
    return "".join(random.choices(string.ascii_uppercase + string.digits, k=length))


def set_product_pin(pin):
    set_license_field("product_pin", pin)


def check_product_pin(pin):
    _, product_pin, _ = get_license_row()
    return pin == product_pin


def set_trial_expiry(minutes=5):
    # Set trial_start to now minus trial_days (in minutes)
    conn = get_db_connection()
    cur = conn.cursor()
    # Set trial_start to 5 minutes ago
    expiry_time = datetime.now() - timedelta(minutes=minutes)
    # Store trial_start in Day/Month/Year format
    trial_start = expiry_time.strftime("%d/%m/%Y")
    cur.execute("UPDATE license SET trial_start=? WHERE id=1", (trial_start,))
    conn.commit()
    conn.close()
