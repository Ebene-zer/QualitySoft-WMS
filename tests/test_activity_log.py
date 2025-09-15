import os

import pytest

from database.db_handler import get_db_connection
from models.product import Product
from utils.activity_log import fetch_recent, log_action
from utils.session import set_current_user

# Ensure test DB variable (db fixture will override path each test)
os.environ["WMS_DB_NAME"] = "test_wholesale.db"

pytestmark = [pytest.mark.usefixtures("qapp")]


def _count_activity(action_type: str) -> int:
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("SELECT COUNT(*) FROM activity_log WHERE action_type=?", (action_type,))
    n = cur.fetchone()[0]
    conn.close()
    return n


class TestActivityLog:
    def test_activity_log_direct_logging(self):
        before = _count_activity("TEST_EVENT")
        log_action("tester", "TEST_EVENT", "some details")
        after = _count_activity("TEST_EVENT")
        assert after == before + 1
        rows = fetch_recent(5)
        assert any(r[2] == "TEST_EVENT" and r[1] == "tester" for r in rows)

    def test_product_add_creates_log_entry(self):
        set_current_user("admin", "Admin")
        before = _count_activity("PRODUCT_ADD")
        Product.add_product("LogTestItem", 9.99, 5)
        assert _count_activity("PRODUCT_ADD") == before + 1
        rows = fetch_recent(10)
        assert any("LogTestItem" in r[3] for r in rows), rows

    def test_activity_log_widget_displays_entries(self):
        # Create a couple entries
        log_action("alice", "WIDGET_TEST", "first")
        log_action("bob", "WIDGET_TEST", "second")
        from ui.more import ActivityLogWidget  # import here so UI classes already loaded

        widget = ActivityLogWidget()
        # Expect at least the two rows we just added to appear (order newest first)
        row_count = widget.table.rowCount()
        assert row_count >= 2
        # Collect action column values
        actions = [widget.table.item(i, 2).text() for i in range(row_count)]
        assert "WIDGET_TEST" in actions

    def test_more_dropdown_contains_activity_log_for_admin(self):
        from ui.more import MoreDropdown

        md = MoreDropdown(user_role="Admin")
        items = [md.dropdown.itemText(i) for i in range(md.dropdown.count())]
        assert "Activity Log" in items

    def test_more_dropdown_excludes_activity_log_for_manager(self):
        from ui.more import MoreDropdown

        md = MoreDropdown(user_role="Manager")
        items = [md.dropdown.itemText(i) for i in range(md.dropdown.count())]
        assert "Activity Log" not in items
