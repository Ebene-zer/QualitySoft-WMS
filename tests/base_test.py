import os
import unittest
from database.db_handler import get_db_connection, initialize_database

class BaseTestCase(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls._original_db_name = os.environ.get("WMS_DB_NAME")
        print("[TEST LOG] Starting test class:", cls.__name__)

    @classmethod
    def tearDownClass(cls):
        # Restore original env var so running app afterwards uses real DB
        if cls._original_db_name is not None:
            os.environ["WMS_DB_NAME"] = cls._original_db_name
        else:
            os.environ.pop("WMS_DB_NAME", None)
        print("[TEST LOG] Finished test class:", cls.__name__)

    def setUp(self):
        super().setUp()
        # Set test database for isolation
        os.environ["WMS_DB_NAME"] = "test_wholesale.db"
        # Ensure database schema exists for each test run
        initialize_database()
        self.log("Setup: test database initialized.")
        self.log("Test started.")

    def tearDown(self):
        self.log("Test finished. Running cleanup...")
        # Clean up all tables after each test (extend as needed)
        conn = get_db_connection()
        cur = conn.cursor()
        # Clean main data tables; keep license/settings persistent for license tests (reset selectively there)
        for table in ["invoice_items", "invoices", "products", "customers", "users"]:
            try:
                cur.execute(f"DELETE FROM {table}")
            except Exception:
                pass
        conn.commit()
        conn.close()
        self.log("Teardown: test tables cleaned.")
        super().tearDown()

    def assertDictContains(self, d, keys):
        for key in keys:
            self.assertIn(key, d, f"Missing key: {key}")

    def assertListNotEmpty(self, lst):
        self.assertTrue(len(lst) > 0, "List is empty!")

    def log(self, message):
        print(f"[TEST LOG] {message}")
