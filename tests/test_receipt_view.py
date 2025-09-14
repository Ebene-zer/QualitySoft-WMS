import os
import unittest
from unittest.mock import patch, MagicMock
from PyQt6.QtWidgets import QApplication
import sys

# Ensure test database is used for isolation
os.environ["WMS_DB_NAME"] = "test_wholesale.db"

# Import the classes to test
from ui.receipt_view import SelectAllOnFocus, ReceiptView
from tests.base_test import BaseTestCase

app = QApplication(sys.argv)  # Needed for QWidget tests

class TestSelectAllOnFocus(unittest.TestCase):
    def test_eventFilter_focus_in(self):
        obj = MagicMock()
        event = MagicMock()
        event.type.return_value = 8  # QEvent.Type.FocusIn
        filter = SelectAllOnFocus()
        result = filter.eventFilter(obj, event)
        obj.selectAll.assert_called_once()
        self.assertFalse(result)

class TestReceiptView(BaseTestCase):
    def setUp(self):
        super().setUp()
        self.view = ReceiptView()

    @patch('ui.receipt_view.Invoice')
    def test_load_invoices(self, mock_invoice):
        mock_invoice.get_all_invoices.return_value = [
            MagicMock(invoice_id=1, customer_name='John', total_amount=100.0)
        ]
        self.view.load_invoices()
        self.assertEqual(self.view.invoice_dropdown.count(), 1)

    @patch('ui.receipt_view.QMessageBox')
    @patch('ui.receipt_view.Invoice')
    def test_show_receipt_no_invoice_selected(self, mock_invoice, mock_msgbox):
        self.view.invoice_dropdown.currentIndex = MagicMock(return_value=-1)
        self.view.show_receipt()
        mock_msgbox.warning.assert_called_once()

    @patch('ui.receipt_view.QMessageBox')
    @patch('ui.receipt_view.Invoice')
    def test_show_receipt_invoice_not_found(self, mock_invoice, mock_msgbox):
        self.view.invoice_dropdown.currentIndex = MagicMock(return_value=0)
        self.view.invoice_dropdown.currentText = MagicMock(return_value="1 - John - GHS 100.00")
        mock_invoice.get_invoice_by_id.return_value = None
        self.view.show_receipt()
        mock_msgbox.warning.assert_called_once()

    @patch('ui.receipt_view.QMessageBox')
    @patch('ui.receipt_view.QFileDialog.getSaveFileName', return_value=('test.pdf', ''))
    @patch('ui.receipt_view.Invoice')
    def test_export_to_pdf_success(self, mock_invoice, mock_file_dialog, mock_msgbox):
        self.view.invoice_dropdown.currentIndex = MagicMock(return_value=0)
        self.view.invoice_dropdown.currentText = MagicMock(return_value="1 - John - GHS 100.00")
        mock_invoice.get_invoice_by_id.return_value = {
            "invoice_id": 1,
            "date": "2024-01-01",
            "customer_name": "John",
            "items": [{"product_name": "A", "quantity": 2, "unit_price": 10.0}],
            "discount": 0,
            "tax": 0,
            "total_amount": 20.0
        }
        self.view.export_to_pdf()
        mock_msgbox.information.assert_called_once()

    @patch('ui.receipt_view.QMessageBox')
    @patch('ui.receipt_view.Invoice')
    def test_print_receipt_no_invoice_selected(self, mock_invoice, mock_msgbox):
        self.view.invoice_dropdown.currentIndex = MagicMock(return_value=-1)
        self.view.print_receipt()
        mock_msgbox.warning.assert_called_once()

if __name__ == '__main__':
    unittest.main()