import os
import unittest
from unittest.mock import patch, MagicMock
from PyQt6.QtWidgets import QApplication, QWidget
import sys
from database.db_handler import initialize_database

# Ensure test database is used for isolation
os.environ["WMS_DB_NAME"] = "test_wholesale.db"
# Initialize the test database schema
initialize_database()

# Patch all view classes to QWidget before importing MainWindow
with patch('ui.main_window.ProductView', side_effect=lambda: QWidget()), \
     patch('ui.main_window.CustomerView', side_effect=lambda: QWidget()), \
     patch('ui.main_window.InvoiceView', side_effect=lambda: QWidget()), \
     patch('ui.main_window.ReceiptView', side_effect=lambda: QWidget()), \
     patch('ui.main_window.UserView', side_effect=lambda: QWidget()), \
     patch('ui.login_window.LoginWindow', MagicMock()):
    from ui.main_window import MainWindow

class TestMainWindow(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = QApplication(sys.argv)

    def test_nav_buttons_and_switch_view(self):
        window = MainWindow('testuser', 'Admin')
        self.assertEqual(window.windowTitle(), "QualitySoft WMS")
        # Current implementation builds 7 buttons for Admin (More, Products, Customers, Invoice, Receipts, Users, Settings) + Logout not counted because not appended to nav_buttons
        self.assertEqual(len(window.nav_buttons), 7)
        # Switch among the first 5 stack indices (0..4). Users view index is 5
        for i in range(5):
            window.switch_view(i)
            self.assertEqual(window.stacked_widget.currentIndex(), i)

    def test_nav_buttons_for_non_admin(self):
        window = MainWindow('testuser', 'staff')
        # Non-admin gets: More, Products, Customers, Invoice, Receipts (5 buttons)
        self.assertEqual(len(window.nav_buttons), 5)

    def test_logout(self):
        window = MainWindow('testuser', 'Admin')
        window.close = MagicMock()
        window.logout()
        window.close.assert_called_once()

if __name__ == '__main__':
    unittest.main()