import os
import unittest
from datetime import datetime
from models.invoice import Invoice
from testes.base_test import BaseTestCase

os.environ["WMS_DB_NAME"] = "test_wholesale.db"

class TestInvoiceReceiptFormatting(BaseTestCase):
    def test_format_receipt_data_basic(self):
        invoice_dict = {
            "invoice_id": 123,
            "invoice_date": datetime(2025, 1, 15, 14, 30, 5).strftime("%Y-%m-%d %H:%M:%S"),
            "customer_name": "Alice",
            "customer_number": "0244000000",
            "discount": 5.0,
            "tax": 2.5,
            "total_amount": 97.5,
            "items": [
                {"product_name": "Soap", "quantity": 2, "unit_price": 10.0},
                {"product_name": "Brush", "quantity": 1, "unit_price": 5.0}
            ]
        }
        formatted = Invoice.format_receipt_data(invoice_dict, wholesale_number="0551234567", wholesale_address="Accra")
        self.assertEqual(formatted["invoice_number"], 123)
        self.assertEqual(formatted["total_items"], 3)
        self.assertEqual(formatted["discount"], "5.00")
        self.assertEqual(formatted["tax"], "2.50")
        self.assertEqual(formatted["total"], "97.50")
        self.assertEqual(formatted["wholesale_address"], "Accra")
        self.assertEqual(formatted["wholesale_contact"], "0551234567")
        # Ensure date formatted to d/m/Y
        self.assertIn("15/01/2025", formatted["invoice_date"])  # includes time

    def test_format_receipt_handles_unknown_date(self):
        invoice_dict = {"invoice_id": 1, "invoice_date": "BADDATE", "customer_name": "Bob", "items": [], "discount":0, "tax":0, "total_amount":0}
        formatted = Invoice.format_receipt_data(invoice_dict)
        self.assertEqual(formatted["invoice_date"], "BADDATE")

if __name__ == '__main__':
    unittest.main()

