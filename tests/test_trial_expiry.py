import os
import pytest
from datetime import datetime, timedelta
from database.db_handler import get_db_connection
from utils.license_manager import (
    generate_product_pin,
    set_product_pin,
    check_product_pin,
    is_trial_expired,
)

os.environ["WMS_DB_NAME"] = "test_wholesale.db"

@pytest.fixture(autouse=True)
def reset_license():
    """Reset license row before each test."""
    conn = get_db_connection(); cur = conn.cursor()
    today_iso = datetime.now().strftime("%Y-%m-%d")
    cur.execute("UPDATE license SET trial_start=?, product_pin='', trial_days=14 WHERE id=1", (today_iso,))
    conn.commit(); conn.close()
    yield

class TestLicenseManager:
    def test_generate_product_pin_length_and_charset(self):
        pin = generate_product_pin(12)
        assert len(pin) == 12
        assert all(c.isupper() or c.isdigit() for c in pin)

    def test_set_and_check_product_pin(self):
        pin = generate_product_pin(8)
        set_product_pin(pin)
        assert check_product_pin(pin) is True
        assert check_product_pin("WRONGPIN") is False

    def test_is_trial_expired_false_with_recent_start_iso(self):
        assert is_trial_expired() is False

    def test_is_trial_expired_true_after_days_elapsed_iso(self):
        past = (datetime.now() - timedelta(days=30)).strftime("%Y-%m-%d")
        conn = get_db_connection(); cur = conn.cursor()
        cur.execute("UPDATE license SET trial_start=? WHERE id=1", (past,))
        conn.commit(); conn.close()
        assert is_trial_expired() is True

    def test_is_trial_expired_day_month_year_format(self):
        past = (datetime.now() - timedelta(days=10)).strftime("%d/%m/%Y")
        conn = get_db_connection(); cur = conn.cursor()
        cur.execute("UPDATE license SET trial_start=?, trial_days=14 WHERE id=1", (past,))
        conn.commit(); conn.close()
        assert is_trial_expired() is False
        past2 = (datetime.now() - timedelta(days=20)).strftime("%d/%m/%Y")
        conn = get_db_connection(); cur = conn.cursor()
        cur.execute("UPDATE license SET trial_start=? WHERE id=1", (past2,))
        conn.commit(); conn.close()
        assert is_trial_expired() is True

    def test_is_trial_expired_invalid_date_treated_expired(self):
        conn = get_db_connection(); cur = conn.cursor()
        cur.execute("UPDATE license SET trial_start='INVALID', trial_days=14 WHERE id=1")
        conn.commit(); conn.close()
        assert is_trial_expired() is True
