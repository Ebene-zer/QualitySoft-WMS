import os
import pytest
from database.db_handler import initialize_database, get_db_connection

@pytest.fixture(scope="session")
def qapp():
    # Single QApplication for all GUI tests.
    from PyQt6.QtWidgets import QApplication
    os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
    app = QApplication.instance() or QApplication([])
    yield app

@pytest.fixture(scope="function")
def db(tmp_path):
    # Per-test isolated SQLite DB.
    test_db = tmp_path / "test.db"
    os.environ["WMS_DB_NAME"] = str(test_db)
    initialize_database()
    yield
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        for table in ["invoice_items", "invoices", "products", "customers", "users"]:
            try:
                cur.execute(f"DELETE FROM {table}")
            except Exception:
                pass
        conn.commit(); conn.close()
    except Exception:
        pass

# Automatically ensure DB fixture runs for every test (so individual tests don't need to request db explicitly)
@pytest.fixture(autouse=True)
def _auto_db(db):
    yield

@pytest.fixture()
def log():
    def _log(message: str):
        print(f"[TEST LOG] {message}")
    return _log

@pytest.fixture()
def seed_customer():
    from models.customer import Customer
    Customer.add_customer("Alice", "0123456789", "Wonderland")
    return Customer.get_all_customers()[0]
