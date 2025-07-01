
import unittest
from unittest.mock import patch, MagicMock
from PyQt6.QtWidgets import QApplication
import sys

# Ensure QApplication exists for widget tests
app = QApplication.instance() or QApplication(sys.argv)

with patch('ui.main_window.MainWindow', autospec=True):
    from ui.login_window import LoginWindow

class TestLoginWindow(unittest.TestCase):
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
        window.username_input.setText("baduser")
        window.password_input.setText("badpass")
        window.role_combo.setCurrentText("Admin")
        window.authenticate()
        mock_msgbox.warning.assert_called_with(window, "Login Failed", "Invalid username or password.")

    @patch('ui.login_window.QMessageBox')
    @patch('ui.login_window.User')
    def test_role_mismatch(self, mock_user, mock_msgbox):
        mock_user.authenticate.return_value = "Manager"
        window = LoginWindow()
        window.username_input.setText("testuser")
        window.password_input.setText("testpass")
        window.role_combo.setCurrentText("Admin")
        window.authenticate()
        mock_msgbox.warning.assert_called_with(window, "Access Denied", "This account belongs to a Manager, not Admin.")

    @patch('ui.login_window.QMessageBox')
    def test_missing_fields(self, mock_msgbox):
        window = LoginWindow()
        window.username_input.setText("")
        window.password_input.setText("")
        window.authenticate()
        mock_msgbox.warning.assert_called_with(window, "Missing Info", "Please fill in both username and password.")

if __name__ == '__main__':
    unittest.main()