import os
from unittest.mock import patch

import pytest
from PyQt6.QtWidgets import QWidget

os.environ["WMS_DB_NAME"] = "test_wholesale.db"

# Patch heavy views before importing LoginWindow
with (
    patch("ui.main_window.ProductView", side_effect=lambda: QWidget()),
    patch("ui.main_window.CustomerView", side_effect=lambda: QWidget()),
    patch("ui.main_window.InvoiceView", side_effect=lambda: QWidget()),
    patch("ui.main_window.ReceiptView", side_effect=lambda: QWidget()),
    patch("ui.main_window.UserView", side_effect=lambda: QWidget()),
):
    from ui.login_window import LoginWindow

pytestmark = [pytest.mark.usefixtures("qapp")]


class TestPasswordChangeFlow:
    @patch("ui.login_window.User")
    @patch("ui.login_window.PasswordChangeDialog")
    def test_password_change_required_and_completed(self, mock_pwd_dialog, mock_user):
        # Simulate valid authentication and must change password
        mock_user.authenticate.return_value = "Admin"
        mock_user.get_must_change_password.return_value = True

        # Simulate dialog accepted
        instance = mock_pwd_dialog.return_value
        instance.exec.return_value = 1  # QDialog.Accepted

        window = LoginWindow()
        window.username_input.setText("admin")
        window.password_input.setText("temp")
        window.role_combo.setCurrentText("Admin")
        window.authenticate()

        # Main window should be created after password change accepted
        assert hasattr(window, "main_window")
        assert mock_pwd_dialog.called
        mock_user.change_password.assert_not_called()  # change handled inside dialog mock; not invoked directly here

    @patch("ui.login_window.User")
    @patch("ui.login_window.PasswordChangeDialog")
    @patch("ui.login_window.QMessageBox")
    def test_password_change_required_cancelled(self, mock_msg, mock_pwd_dialog, mock_user):
        mock_user.authenticate.return_value = "Admin"
        mock_user.get_must_change_password.return_value = True
        # Simulate dialog rejected
        instance = mock_pwd_dialog.return_value
        instance.exec.return_value = 0  # Rejected

        window = LoginWindow()
        window.username_input.setText("admin")
        window.password_input.setText("temp")
        window.role_combo.setCurrentText("Admin")
        window.authenticate()

        # Should NOT proceed to main window
        assert not hasattr(window, "main_window")
        mock_msg.information.assert_called()  # cancellation notice

    @patch("ui.login_window.User")
    @patch("ui.login_window.PasswordChangeDialog")
    def test_no_password_change_required(self, mock_pwd_dialog, mock_user):
        mock_user.authenticate.return_value = "Admin"
        mock_user.get_must_change_password.return_value = False

        window = LoginWindow()
        window.username_input.setText("admin")
        window.password_input.setText("temp")
        window.role_combo.setCurrentText("Admin")
        window.authenticate()

        assert hasattr(window, "main_window")
        mock_pwd_dialog.assert_not_called()
