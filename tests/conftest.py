import os

import pytest

from database.db_handler import get_db_connection, initialize_database


@pytest.fixture(scope="session")
def qapp():
    # Single QApplication for all GUI tests.
    from PyQt6.QtWidgets import QApplication

    os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
    app = QApplication.instance() or QApplication([])
    yield app


@pytest.fixture(scope="function", autouse=True)
def db(tmp_path):
    # Per-test isolated SQLite DB (autouse so individual tests need not request it).
    test_db = tmp_path / "test.db"
    os.environ["WMS_DB_NAME"] = str(test_db)
    initialize_database()
    yield
    # Optional cleanup (not strictly needed since a fresh file is used each test)
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        for table in ["invoice_items", "invoices", "products", "customers", "users"]:
            try:
                cur.execute(f"DELETE FROM {table}")
            except Exception:
                pass
        conn.commit()
        conn.close()
    except Exception:
        pass
