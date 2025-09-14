import unittest
from models.invoice import Invoice
from models.product import Product
from models.customer import Customer
from database.db_handler import get_db_connection, initialize_database
from tests.base_test import BaseTestCase

class TestInvoice(BaseTestCase):
    def setUp(self):
        super().setUp()
        initialize_database()
        # Seed a customer
        Customer.add_customer("Alice", "0123456789", "Wonderland")
        # Seed products
        Product.add_product("Soap", 2.5, 100)
        Product.add_product("Brush", 1.0, 50)
        conn = get_db_connection(); cur = conn.cursor()
        cur.execute("SELECT customer_id FROM customers LIMIT 1"); self.customer_id = cur.fetchone()[0]
        cur.execute("SELECT product_id FROM products ORDER BY product_id"); rows = cur.fetchall(); self.product_ids = [r[0] for r in rows]
        conn.close()

    def test_create_invoice_success_and_stock_reduction(self):
        items = [
            {"product_id": self.product_ids[0], "quantity": 10, "unit_price": 2.5},
            {"product_id": self.product_ids[1], "quantity": 5, "unit_price": 1.0},
        ]
        invoice_id = Invoice.create_invoice(self.customer_id, items, discount=2.5, tax=1.0)
        self.assertIsInstance(invoice_id, int)
        # Verify stock decreased
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute("SELECT stock_quantity FROM products WHERE product_id=?", (self.product_ids[0],))
        stock_after = cur.fetchone()[0]
        self.assertEqual(stock_after, 90)
        conn.close()

    def test_create_invoice_product_not_found(self):
        # Use a non-existent product id (very large number)
        items = [{"product_id": 999999, "quantity": 1, "unit_price": 9.0}]
        with self.assertRaises(ValueError):
            Invoice.create_invoice(self.customer_id, items)

    def test_create_invoice_insufficient_stock(self):
        # Request more than available
        items = [{"product_id": self.product_ids[0], "quantity": 1000, "unit_price": 2.5}]
        with self.assertRaises(ValueError):
            Invoice.create_invoice(self.customer_id, items)

    def test_update_invoice_adjusts_stock(self):
        # Create original invoice
        orig_items = [
            {"product_id": self.product_ids[0], "quantity": 5, "unit_price": 2.5},
        ]
        invoice_id = Invoice.create_invoice(self.customer_id, orig_items)
        # Capture stock after original
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute("SELECT stock_quantity FROM products WHERE product_id=?", (self.product_ids[0],))
        stock_after_create = cur.fetchone()[0]
        # Update invoice with different quantities
        new_items = [
            {"product_id": self.product_ids[0], "quantity": 2, "unit_price": 2.5},
            {"product_id": self.product_ids[1], "quantity": 3, "unit_price": 1.0},
        ]
        Invoice.update_invoice(invoice_id, self.customer_id, new_items, discount=1.0, tax=0.5)
        # Verify stock restored for removed qty (5 -> 2 means +3 back) and decremented for added new product
        cur.execute("SELECT stock_quantity FROM products WHERE product_id=?", (self.product_ids[0],))
        stock_after_update_p1 = cur.fetchone()[0]
        cur.execute("SELECT stock_quantity FROM products WHERE product_id=?", (self.product_ids[1],))
        stock_after_update_p2 = cur.fetchone()[0]
        conn.close()
        self.assertEqual(stock_after_create + 3, stock_after_update_p1)
        self.assertEqual(50 - 3, stock_after_update_p2)

    def test_delete_invoice_restores_stock(self):
        items = [{"product_id": self.product_ids[0], "quantity": 4, "unit_price": 2.5}]
        invoice_id = Invoice.create_invoice(self.customer_id, items)
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute("SELECT stock_quantity FROM products WHERE product_id=?", (self.product_ids[0],))
        after_create = cur.fetchone()[0]
        self.assertEqual(after_create, 96)
        conn.close()
        # Delete
        Invoice.delete_invoice(invoice_id)
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute("SELECT stock_quantity FROM products WHERE product_id=?", (self.product_ids[0],))
        after_delete = cur.fetchone()[0]
        conn.close()
        self.assertEqual(after_delete, 100)

    def test_get_all_and_get_by_id(self):
        items = [{"product_id": self.product_ids[0], "quantity": 1, "unit_price": 2.5}]
        invoice_id = Invoice.create_invoice(self.customer_id, items, discount=0.0, tax=0.0)
        invoices = Invoice.get_all_invoices()
        self.assertTrue(any(inv.invoice_id == invoice_id for inv in invoices))
        invoice = Invoice.get_invoice_by_id(invoice_id)
        self.assertEqual(invoice["invoice_id"], invoice_id)
        self.assertEqual(len(invoice["items"]), 1)

    def test_create_invoice_with_duplicate_product_lines(self):
        # Two lines for same product should aggregate to 12 and reduce stock once by 12
        pid = self.product_ids[0]
        items = [
            {"product_id": pid, "quantity": 5, "unit_price": 2.5},
            {"product_id": pid, "quantity": 7, "unit_price": 2.5},
        ]
        invoice_id = Invoice.create_invoice(self.customer_id, items)
        self.assertIsInstance(invoice_id, int)
        conn = get_db_connection(); cur = conn.cursor()
        cur.execute("SELECT stock_quantity FROM products WHERE product_id=?", (pid,))
        remaining = cur.fetchone()[0]
        conn.close()
        self.assertEqual(100 - 12, remaining)

    def test_create_invoice_duplicate_lines_insufficient_stock(self):
        pid = self.product_ids[0]
        items = [
            {"product_id": pid, "quantity": 60, "unit_price": 2.5},
            {"product_id": pid, "quantity": 50, "unit_price": 2.5},  # total 110 > 100
        ]
        with self.assertRaises(ValueError):
            Invoice.create_invoice(self.customer_id, items)
        # Ensure stock unchanged after failure
        conn = get_db_connection(); cur = conn.cursor()
        cur.execute("SELECT stock_quantity FROM products WHERE product_id=?", (pid,))
        remaining = cur.fetchone()[0]
        conn.close()
        self.assertEqual(100, remaining)

if __name__ == '__main__':
    unittest.main()