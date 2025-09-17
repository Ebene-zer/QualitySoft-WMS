import os

import pytest

from database.db_handler import get_db_connection, initialize_database

os.environ["WMS_DB_NAME"] = "test_wholesale.db"

pytestmark = [pytest.mark.usefixtures("qapp")]


def _get_retention_from_db():
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("PRAGMA table_info(settings)")
    cols = [c[1] for c in cur.fetchall()]
    assert "retention_count" in cols, "retention_count column missing after migration"
    cur.execute("SELECT retention_count FROM settings WHERE id=1")
    row = cur.fetchone()
    conn.close()
    return row[0]


def test_settings_dialog_retention_save(db):
    # Patch QMessageBox to avoid modal dialogs blocking the test
    from unittest.mock import patch

    with patch("ui.settings_dialog.QMessageBox"):
        # Lazy import to ensure patches/fixtures active
        from ui.settings_dialog import SettingsDialog

        initialize_database()
        dlg = SettingsDialog()
        # Change retention value
        dlg.retention_spin.setValue(7)
        dlg.wholesale_name_edit.setText("Shop")
        dlg.wholesale_edit.setText("0551234567")
        dlg.wholesale_address_edit.setText("Loc 1")
        dlg.save_wholesale_number()
        assert _get_retention_from_db() == 7


def test_settings_dialog_last_backup_label_updates(db):
    import tempfile
    from unittest.mock import patch

    from utils.backup import perform_backup, update_backup_directory

    # Patch QMessageBox to avoid any accidental modal dialogs during dialog init/refresh
    with patch("ui.settings_dialog.QMessageBox"):
        from ui.settings_dialog import SettingsDialog

        with tempfile.TemporaryDirectory() as tmp:
            update_backup_directory(tmp)
            dlg = SettingsDialog()
            dlg.refresh_backup_status()
            # Initially should be Never
            assert "Never" in dlg.last_backup_label.text()
            perform_backup()
            dlg.refresh_backup_status()
            assert "Never" not in dlg.last_backup_label.text()


def test_migrations_added_columns(db):
    initialize_database()
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("PRAGMA table_info(settings)")
    cols = {c[1] for c in cur.fetchall()}
    conn.close()
    assert {"backup_directory", "retention_count"}.issubset(cols)
