import os
import sys
import unittest
from unittest.mock import patch, MagicMock
from PyQt6.QtWidgets import QApplication
from database.db_handler import get_db_connection, initialize_database
from tests.base_test import BaseTestCase

os.environ["WMS_DB_NAME"] = "test_wholesale.db"

# Ensure a QApplication
app = QApplication.instance() or QApplication(sys.argv)

from ui.settings_dialog import SettingsDialog

class TestSettingsDialog(BaseTestCase):
    def setUp(self):
        super().setUp()
        initialize_database()

    @patch('ui.settings_dialog.QMessageBox')
    def test_load_and_save_valid(self, mock_msg):
        dlg = SettingsDialog()
        dlg.wholesale_name_edit.setText("MyStore")
        dlg.wholesale_edit.setText("0551234567")
        dlg.wholesale_address_edit.setText("Accra Road")
        dlg.save_wholesale_number()
        conn = get_db_connection(); cur = conn.cursor()
        cur.execute("SELECT wholesale_number, wholesale_name, wholesale_address FROM settings WHERE id=1")
        row = cur.fetchone(); conn.close()
        self.assertEqual(row[0], '0551234567')
        self.assertEqual(row[1], 'MyStore')
        self.assertEqual(row[2], 'Accra Road')
        mock_msg.information.assert_called_once()

    @patch('ui.settings_dialog.QMessageBox')
    def test_invalid_inputs(self, mock_msg):
        dlg = SettingsDialog()
        # Invalid number
        dlg.wholesale_name_edit.setText("Name")
        dlg.wholesale_edit.setText("ABC")
        dlg.wholesale_address_edit.setText("Loc")
        dlg.save_wholesale_number()
        self.assertTrue(mock_msg.warning.called)
        mock_msg.warning.reset_mock()
        # Empty name
        dlg.wholesale_edit.setText("0551112222")
        dlg.wholesale_name_edit.setText("")
        dlg.save_wholesale_number()
        self.assertTrue(mock_msg.warning.called)
        mock_msg.warning.reset_mock()
        # Empty address
        dlg.wholesale_name_edit.setText("Name")
        dlg.wholesale_address_edit.setText("")
        dlg.save_wholesale_number()
        self.assertTrue(mock_msg.warning.called)

if __name__ == '__main__':
    unittest.main()
