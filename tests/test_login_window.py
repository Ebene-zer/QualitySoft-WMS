import os
import sys
import unittest
from unittest.mock import patch
from PyQt6.QtWidgets import QApplication
from testes.base_test import BaseTestCase

SKIP_GUI = os.environ.get("SKIP_GUI_TESTS") == "1"

# Ensure test database is used for isolation
os.environ["WMS_DB_NAME"] = "test_wholesale.db"

# Ensure QApplication exists for widget tests
app = QApplication.instance() or QApplication(sys.argv)

with patch('ui.main_window.MainWindow', autospec=True):
    from ui.login_window import LoginWindow

@unittest.skipIf(SKIP_GUI, "Skipping GUI tests in headless mode")
class TestLoginWindow(BaseTestCase):
    @patch('ui.login_window.QMessageBox')
    @patch('ui.login_window.User')
    def test_successful_login(self, mock_user, mock_msgbox):
        mock_user.authenticate.return_value = "Admin"
        window = LoginWindow()
        window.username_input.setText("testuser")
        window.password_input.setText("testpass")
        window.role_combo.setCurrentText("Admin")
        window.authenticate()
        self.assertTrue(hasattr(window, "main_window"))
        window.main_window.show.assert_called_once()
        self.assertFalse(mock_msgbox.warning.called)

    @patch('ui.login_window.QMessageBox')
    @patch('ui.login_window.User')
    def test_failed_login(self, mock_user, mock_msgbox):
        mock_user.authenticate.return_value = None
        window = LoginWindow()
        window.username_input.setText("wronguser")
        window.password_input.setText("wrongpass")
        window.role_combo.setCurrentText("Admin")
        window.authenticate()
        self.assertTrue(mock_msgbox.warning.called)

if __name__ == '__main__':
    unittest.main()