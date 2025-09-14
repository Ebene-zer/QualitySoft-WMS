import os
from unittest.mock import MagicMock, patch

import pytest
from PyQt6.QtWidgets import QWidget

# Ensure test database is used for isolation
os.environ["WMS_DB_NAME"] = "test_wholesale.db"

# Patch all view classes to QWidget before importing MainWindow
with (
    patch("ui.main_window.ProductView", side_effect=lambda: QWidget()),
    patch("ui.main_window.CustomerView", side_effect=lambda: QWidget()),
    patch("ui.main_window.InvoiceView", side_effect=lambda: QWidget()),
    patch("ui.main_window.ReceiptView", side_effect=lambda: QWidget()),
    patch("ui.main_window.UserView", side_effect=lambda: QWidget()),
    patch("ui.login_window.LoginWindow", MagicMock()),
):
    from ui.main_window import MainWindow

pytestmark = [pytest.mark.usefixtures("qapp")]  # ensure QApplication from conftest


class TestMainWindow:
    def test_nav_buttons_and_switch_view(self):
        window = MainWindow("testuser", "Admin")
        assert window.windowTitle() == "QualitySoft WMS"
        assert len(window.nav_buttons) == 7
        for i in range(5):
            window.switch_view(i)
            assert window.stacked_widget.currentIndex() == i

    def test_nav_buttons_for_non_admin(self):
        window = MainWindow("testuser", "staff")
        assert len(window.nav_buttons) == 5

    def test_logout(self):
        window = MainWindow("testuser", "Admin")
        window.close = MagicMock()
        window.logout()
        window.close.assert_called_once()
