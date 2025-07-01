
import os
import unittest
from unittest.mock import patch, MagicMock
from PyQt6.QtWidgets import QApplication, QWidget
import sys



with patch.dict('sys.modules', {
    'ui.product_view': MagicMock(),
    'ui.customer_view': MagicMock(),
    'ui.invoice_view': MagicMock(),
    'ui.receipt_view': MagicMock(),
    'ui.user_view': MagicMock(),
    'ui.login_window': MagicMock(),
}):
    from ui.main_window import MainWindow

class TestMainWindow(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = QApplication(sys.argv)

    @patch('ui.main_window.UserView', side_effect=lambda: QWidget())
    @patch('ui.main_window.ReceiptView', side_effect=lambda: QWidget())
    @patch('ui.main_window.InvoiceView', side_effect=lambda: QWidget())
    @patch('ui.main_window.CustomerView', side_effect=lambda: QWidget())
    @patch('ui.main_window.ProductView', side_effect=lambda: QWidget())
    def test_nav_buttons_and_switch_view(self, mock_product, mock_customer, mock_invoice, mock_receipt, mock_user):
        window = MainWindow('testuser', 'Admin')
        self.assertEqual(window.windowTitle(), "QUALITYSOFT WHOLESALE MANAGEMENT SYSTEM")
        self.assertEqual(len(window.nav_buttons), 5)
        for i in range(5):
            window.switch_view(i)
            self.assertEqual(window.stacked_widget.currentIndex(), i)

    @patch('ui.main_window.UserView', side_effect=lambda: QWidget())
    @patch('ui.main_window.ReceiptView', side_effect=lambda: QWidget())
    @patch('ui.main_window.InvoiceView', side_effect=lambda: QWidget())
    @patch('ui.main_window.CustomerView', side_effect=lambda: QWidget())
    @patch('ui.main_window.ProductView', side_effect=lambda: QWidget())
    def test_nav_buttons_for_non_admin(self, mock_product, mock_customer, mock_invoice, mock_receipt, mock_user):
        window = MainWindow('testuser', 'staff')
        self.assertEqual(len(window.nav_buttons), 4)

    @patch('ui.login_window.LoginWindow')
    @patch('ui.main_window.UserView', side_effect=lambda: QWidget())
    @patch('ui.main_window.ReceiptView', side_effect=lambda: QWidget())
    @patch('ui.main_window.InvoiceView', side_effect=lambda: QWidget())
    @patch('ui.main_window.CustomerView', side_effect=lambda: QWidget())
    @patch('ui.main_window.ProductView', side_effect=lambda: QWidget())
    def test_logout(self, mock_product, mock_customer, mock_invoice, mock_receipt, mock_user, mock_login):
        window = MainWindow('testuser', 'Admin')
        window.close = MagicMock()
        window.logout()
        mock_login.assert_called_once()
        window.close.assert_called_once()

if __name__ == '__main__':
    unittest.main()