import unittest
from unittest.mock import patch, MagicMock
from models.invoice import Invoice

class TestInvoice(unittest.TestCase):
    @patch('models.invoice.get_db_connection')
    @patch('models.invoice.Product')
    def test_create_invoice_success(self, mock_product, mock_get_db):
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_conn.cursor.return_value = mock_cursor
        mock_cursor.lastrowid = 1
        mock_get_db.return_value = mock_conn

        mock_product.get_product_by_id.return_value = MagicMock(stock_quantity=10)
        items = [{'product_id': 1, 'quantity': 2, 'unit_price': 5.0}]
        invoice_id = Invoice.create_invoice(1, items, discount=1.0, tax=0.5)
        self.assertEqual(invoice_id, 1)
        mock_conn.commit.assert_called_once()
        mock_conn.close.assert_called_once()

    @patch('models.invoice.get_db_connection')
    @patch('models.invoice.Product')
    def test_create_invoice_product_not_found(self, mock_product, mock_get_db):
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_conn.cursor.return_value = mock_cursor
        mock_cursor.lastrowid = 1
        mock_get_db.return_value = mock_conn

        mock_product.get_product_by_id.return_value = None
        items = [{'product_id': 1, 'quantity': 2, 'unit_price': 5.0}]
        with self.assertRaises(ValueError):
            Invoice.create_invoice(1, items)

    @patch('models.invoice.get_db_connection')
    @patch('models.invoice.Product')
    def test_create_invoice_insufficient_stock(self, mock_product, mock_get_db):
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_conn.cursor.return_value = mock_cursor
        mock_cursor.lastrowid = 1
        mock_get_db.return_value = mock_conn

        mock_product.get_product_by_id.return_value = MagicMock(stock_quantity=1)
        items = [{'product_id': 1, 'quantity': 2, 'unit_price': 5.0}]
        with self.assertRaises(ValueError):
            Invoice.create_invoice(1, items)

    @patch('models.invoice.get_db_connection')
    @patch('models.invoice.Product')
    def test_update_invoice_success(self, mock_product, mock_get_db):
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_conn.cursor.return_value = mock_cursor
        mock_cursor.fetchall.return_value = [(1, 2)]
        mock_get_db.return_value = mock_conn

        mock_product.get_product_by_id.return_value = MagicMock(stock_quantity=10)
        items = [{'product_id': 1, 'quantity': 2, 'unit_price': 5.0}]
        Invoice.update_invoice(1, 1, items)
        mock_conn.commit.assert_called_once()
        mock_conn.close.assert_called_once()

    @patch('models.invoice.get_db_connection')
    @patch('models.invoice.Product')
    def test_delete_invoice_success(self, mock_product, mock_get_db):
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_conn.cursor.return_value = mock_cursor
        mock_cursor.fetchall.return_value = [(1, 2)]
        mock_get_db.return_value = mock_conn

        mock_product.get_product_by_id.return_value = MagicMock(stock_quantity=10)
        Invoice.delete_invoice(1)
        mock_conn.commit.assert_called_once()
        mock_conn.close.assert_called_once()

    @patch('models.invoice.get_db_connection')
    def test_get_all_invoices(self, mock_get_db):
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_conn.cursor.return_value = mock_cursor
        mock_cursor.fetchall.return_value = [
            (1, 'John Doe', 100.0),
            (2, 'Jane Smith', 200.0)
        ]
        mock_get_db.return_value = mock_conn

        invoices = Invoice.get_all_invoices()
        self.assertEqual(len(invoices), 2)
        self.assertEqual(invoices[0].invoice_id, 1)
        self.assertEqual(invoices[1].customer_name, 'Jane Smith')

    @patch('models.invoice.get_db_connection')
    def test_get_invoice_by_id_found(self, mock_get_db):
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_conn.cursor.return_value = mock_cursor
        # First fetchone for invoice, then fetchall for items
        mock_cursor.fetchone.side_effect = [
            (1, 'John Doe', '2024-01-01', 0.0, 0.0, 100.0)
        ]
        mock_cursor.fetchall.return_value = [
            ('Product A', 2, 5.0),
            ('Product B', 1, 10.0)
        ]
        mock_get_db.return_value = mock_conn

        invoice = Invoice.get_invoice_by_id(1)
        self.assertEqual(invoice['invoice_id'], 1)
        self.assertEqual(len(invoice['items']), 2)

    @patch('models.invoice.get_db_connection')
    def test_get_invoice_by_id_not_found(self, mock_get_db):
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_conn.cursor.return_value = mock_cursor
        mock_cursor.fetchone.return_value = None
        mock_get_db.return_value = mock_conn

        invoice = Invoice.get_invoice_by_id(1)
        self.assertIsNone(invoice)

if __name__ == '__main__':
    unittest.main()