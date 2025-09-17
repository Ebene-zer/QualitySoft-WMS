import os
from unittest.mock import patch

import pytest

SKIP_GUI = os.environ.get("SKIP_GUI_TESTS") == "1"

# Ensure a test database is used for isolation
os.environ["WMS_DB_NAME"] = "test_wholesale.db"


with patch("ui.main_window.MainWindow", autospec=True):
    from ui.login_window import LoginWindow

pytestmark = [
    pytest.mark.usefixtures("qapp"),
    pytest.mark.skipif(SKIP_GUI, reason="Skipping GUI tests in headless mode"),
]


class TestLoginWindow:
    @patch("ui.login_window.QMessageBox")
    @patch("ui.login_window.User")
    def test_successful_login(self, mock_user, mock_msgbox):
        mock_user.authenticate.return_value = "Admin"
        window = LoginWindow()
        window.username_input.setText("testuser")
        window.password_input.setText("testpass")
        window.role_combo.setCurrentText("Admin")
        window.authenticate()
        assert hasattr(window, "main_window")
        window.main_window.show.assert_called_once()
        assert not mock_msgbox.warning.called

    @patch("ui.login_window.QMessageBox")
    @patch("ui.login_window.User")
    def test_failed_login(self, mock_user, mock_msgbox):
        mock_user.authenticate.return_value = None
        window = LoginWindow()
        window.username_input.setText("wronguser")
        window.password_input.setText("wrongpass")
        window.role_combo.setCurrentText("Admin")
        window.authenticate()
        assert mock_msgbox.warning.called
