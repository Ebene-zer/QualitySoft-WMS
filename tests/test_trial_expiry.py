import os
import unittest
from datetime import datetime, timedelta
os.environ["WMS_DB_NAME"] = "test_wholesale.db"
from database.db_handler import initialize_database, get_db_connection
from utils.license_manager import (
    generate_product_pin,
    set_product_pin,
    check_product_pin,
    is_trial_expired,
    set_license_field,
)
from tests.base_test import BaseTestCase

class TestLicenseManager(BaseTestCase):
    def setUp(self):
        super().setUp()
        initialize_database()
        # Reset license baseline
        conn = get_db_connection()
        cur = conn.cursor()
        today_iso = datetime.now().strftime("%Y-%m-%d")
        cur.execute("UPDATE license SET trial_start=?, product_pin='', trial_days=14 WHERE id=1", (today_iso,))
        conn.commit()
        conn.close()

    def test_generate_product_pin_length_and_charset(self):
        pin = generate_product_pin(12)
        self.assertEqual(len(pin), 12)
        self.assertTrue(all(c.isupper() or c.isdigit() for c in pin))

    def test_set_and_check_product_pin(self):
        pin = generate_product_pin(8)
        set_product_pin(pin)
        self.assertTrue(check_product_pin(pin))
        self.assertFalse(check_product_pin("WRONGPIN"))

    def test_is_trial_expired_false_with_recent_start_iso(self):
        self.assertFalse(is_trial_expired())

    def test_is_trial_expired_true_after_days_elapsed_iso(self):
        # Move start 30 days back and keep trial_days 14
        past = (datetime.now() - timedelta(days=30)).strftime("%Y-%m-%d")
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute("UPDATE license SET trial_start=? WHERE id=1", (past,))
        conn.commit(); conn.close()
        self.assertTrue(is_trial_expired())

    def test_is_trial_expired_day_month_year_format(self):
        # Use alternative format supported
        past = (datetime.now() - timedelta(days=10)).strftime("%d/%m/%Y")
        conn = get_db_connection(); cur = conn.cursor()
        cur.execute("UPDATE license SET trial_start=?, trial_days=14 WHERE id=1", (past,))
        conn.commit(); conn.close()
        self.assertFalse(is_trial_expired())
        # Advance beyond limit
        past2 = (datetime.now() - timedelta(days=20)).strftime("%d/%m/%Y")
        conn = get_db_connection(); cur = conn.cursor()
        cur.execute("UPDATE license SET trial_start=? WHERE id=1", (past2,))
        conn.commit(); conn.close()
        self.assertTrue(is_trial_expired())

    def test_is_trial_expired_invalid_date_treated_expired(self):
        conn = get_db_connection(); cur = conn.cursor()
        cur.execute("UPDATE license SET trial_start='INVALID', trial_days=14 WHERE id=1")
        conn.commit(); conn.close()
        self.assertTrue(is_trial_expired())

if __name__ == '__main__':
    unittest.main()
