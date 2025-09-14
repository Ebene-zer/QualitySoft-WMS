import os
import sys
import unittest
from unittest.mock import patch, MagicMock

from tests.base_test import BaseTestCase

os.environ["WMS_DB_NAME"] = "test_wholesale.db"

from database.db_handler import initialize_database, get_db_connection
from models.invoice import Invoice
from models.product import Product
from models.customer import Customer
from ui.more import MoreDropdown, GraphWidget, SalesReportWidget
from ui.receipt_view import ReceiptView


class TestInvoicePDFExportUnit(BaseTestCase):
    def test_invoice_export_receipt_to_pdf_calls_build(self):
        formatted = {
            "invoice_number": 1,
            "invoice_date": "15/01/2025 10:00:00",
            "customer_name": "Alice",
            "customer_number": "0551112222",
            "wholesale_contact": "0550000000",
            "wholesale_address": "Accra",
            "items": [["Soap", "2", "10.00", "20.00"]],
            "total_items": 2,
            "discount": "0.00",
            "tax": "0.00",
            "total": "20.00"
        }
        with patch('reportlab.platypus.SimpleDocTemplate') as mock_doc:
            mock_instance = MagicMock()
            mock_doc.return_value = mock_instance
            Invoice.export_receipt_to_pdf(formatted, "dummy.pdf")
            mock_instance.build.assert_called_once()

class TestMoreDropdownBehavior(BaseTestCase):
    def test_dropdown_options_admin(self):
        widget = MoreDropdown(user_role='Admin')
        items = [widget.dropdown.itemText(i) for i in range(widget.dropdown.count())]
        self.assertIn('Sales Report', items)
        self.assertIn('Graph', items)
        self.assertIsInstance(widget.current_widget, SalesReportWidget)

    def test_dropdown_options_manager(self):
        widget = MoreDropdown(user_role='Manager')
        items = [widget.dropdown.itemText(i) for i in range(widget.dropdown.count())]
        self.assertIn('Sales Report', items)
        self.assertNotIn('Graph', items)
        self.assertIsInstance(widget.current_widget, SalesReportWidget)

class TestGraphWidget(BaseTestCase):
    def setUp(self):
        super().setUp()
        initialize_database()
        # Seed data
        Customer.add_customer("Cust", "0551234567", "Addr")
        Product.add_product("Item", 5.0, 500)
        conn = get_db_connection(); cur = conn.cursor(); cur.execute("SELECT customer_id FROM customers LIMIT 1"); cid = cur.fetchone()[0]
        Product.add_product("Item2", 3.0, 500)
        cur.execute("SELECT product_id FROM products WHERE name='Item'"); pid = cur.fetchone()[0]
        # Create a few invoices then manipulate dates
        inv_ids = []
        for _ in range(3):
            inv_ids.append(Invoice.create_invoice(cid, [{"product_id": pid, "quantity": 1, "unit_price": 5.0}]))
        # Set dates across months / years
        dates = ["2024-12-31 09:00:00", "2025-01-15 10:00:00", "2025-02-20 11:00:00"]
        for inv_id, dt in zip(inv_ids, dates):
            cur.execute("UPDATE invoices SET invoice_date=? WHERE invoice_id=?", (dt, inv_id))
        conn.commit(); conn.close()

    def test_graph_widget_bar_and_line(self):
        gw = GraphWidget()
        with patch.object(gw.canvas, 'draw') as mock_draw:
            # Bar chart monthly
            gw.type_box.setCurrentText('Bar Chart')
            gw.period_box.setCurrentText('Monthly')
            gw.show_graph()
            self.assertTrue(mock_draw.called)
            self.assertEqual(len(gw.figure.axes), 1)
            bar_count = len(gw.figure.axes[0].patches)
            self.assertGreaterEqual(bar_count, 3)
            mock_draw.reset_mock()
            # Line chart yearly
            gw.type_box.setCurrentText('Line Chart')
            gw.period_box.setCurrentText('Yearly')
            gw.show_graph()
            self.assertTrue(mock_draw.called)
            self.assertEqual(len(gw.figure.axes), 1)
            # For line chart, expect at least 2 years (2024, 2025)
            self.assertGreaterEqual(len(gw.figure.axes[0].lines), 1)

class TestReceiptViewExportAndPrint(BaseTestCase):
    def setUp(self):
        super().setUp()
        initialize_database()
        # Minimal invoice setup
        Customer.add_customer("Alice", "0551234567", "Addr")
        Product.add_product("Soap", 2.5, 100)
        conn = get_db_connection(); cur = conn.cursor(); cur.execute("SELECT customer_id FROM customers LIMIT 1"); self.cid = cur.fetchone()[0]
        cur.execute("SELECT product_id FROM products WHERE name='Soap'"); pid = cur.fetchone()[0]
        self.invoice_id = Invoice.create_invoice(self.cid, [{"product_id": pid, "quantity": 2, "unit_price": 2.5}])
        conn.close()

    @patch('ui.receipt_view.QMessageBox')
    @patch('ui.receipt_view.QFileDialog.getSaveFileName', return_value=("test_receipt.pdf", ""))
    @patch('ui.receipt_view.Invoice.export_receipt_to_pdf')
    def test_export_to_pdf_flow(self, mock_export, mock_dialog, mock_msg):
        view = ReceiptView()
        view.load_invoices()
        view.invoice_dropdown.setCurrentIndex(0)
        view.export_to_pdf()
        mock_export.assert_called_once()
        mock_msg.information.assert_called_once()

    @patch('ui.receipt_view.webbrowser.open')
    @patch('ui.receipt_view.Invoice.export_receipt_to_pdf')
    @patch('ui.receipt_view.QMessageBox')
    def test_print_receipt_flow(self, mock_msg, mock_export, mock_open):
        view = ReceiptView()
        view.load_invoices()
        view.invoice_dropdown.setCurrentIndex(0)
        view.print_receipt()
        mock_export.assert_called_once()
        mock_open.assert_called_once()

if __name__ == '__main__':
    unittest.main()
