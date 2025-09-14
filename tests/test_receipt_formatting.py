import os
import pytest
from datetime import datetime
from models.invoice import Invoice

os.environ["WMS_DB_NAME"] = "test_wholesale.db"

class TestInvoiceReceiptFormatting:
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
        assert formatted["invoice_number"] == 123
        assert formatted["total_items"] == 3
        assert formatted["discount"] == "5.00"
        assert formatted["tax"] == "2.50"
        assert formatted["total"] == "97.50"
        assert formatted["wholesale_address"] == "Accra"
        assert formatted["wholesale_contact"] == "0551234567"
        assert "15/01/2025" in formatted["invoice_date"]

    def test_format_receipt_handles_unknown_date(self):
        invoice_dict = {"invoice_id": 1, "invoice_date": "BADDATE", "customer_name": "Bob", "items": [], "discount":0, "tax":0, "total_amount":0}
        formatted = Invoice.format_receipt_data(invoice_dict)
        assert formatted["invoice_date"] == "BADDATE"
