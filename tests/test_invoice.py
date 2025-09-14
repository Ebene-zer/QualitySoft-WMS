import pytest
from models.invoice import Invoice
from models.product import Product
from models.customer import Customer
from database.db_handler import get_db_connection

@pytest.fixture()
def seed_invoice_env():
    # Seed customer and products, return ids.
    Customer.add_customer("Alice", "0123456789", "Wonderland")
    Product.add_product("Soap", 2.5, 100)
    Product.add_product("Brush", 1.0, 50)
    conn = get_db_connection(); cur = conn.cursor()
    cur.execute("SELECT customer_id FROM customers LIMIT 1"); customer_id = cur.fetchone()[0]
    cur.execute("SELECT product_id FROM products ORDER BY product_id"); product_ids = [r[0] for r in cur.fetchall()]
    conn.close()
    return customer_id, product_ids


def test_create_invoice_success_and_stock_reduction(seed_invoice_env):
    customer_id, product_ids = seed_invoice_env
    items = [
        {"product_id": product_ids[0], "quantity": 10, "unit_price": 2.5},
        {"product_id": product_ids[1], "quantity": 5, "unit_price": 1.0},
    ]
    invoice_id = Invoice.create_invoice(customer_id, items, discount=2.5, tax=1.0)
    assert isinstance(invoice_id, int)
    # Verify stock decreased
    conn = get_db_connection(); cur = conn.cursor()
    cur.execute("SELECT stock_quantity FROM products WHERE product_id=?", (product_ids[0],))
    stock_after = cur.fetchone()[0]
    conn.close()
    assert stock_after == 90


def test_create_invoice_product_not_found(seed_invoice_env):
    customer_id, _ = seed_invoice_env
    items = [{"product_id": 999999, "quantity": 1, "unit_price": 9.0}]
    with pytest.raises(ValueError):
        Invoice.create_invoice(customer_id, items)


def test_create_invoice_insufficient_stock(seed_invoice_env):
    customer_id, product_ids = seed_invoice_env
    items = [{"product_id": product_ids[0], "quantity": 1000, "unit_price": 2.5}]
    with pytest.raises(ValueError):
        Invoice.create_invoice(customer_id, items)


def test_update_invoice_adjusts_stock(seed_invoice_env):
    customer_id, product_ids = seed_invoice_env
    orig_items = [{"product_id": product_ids[0], "quantity": 5, "unit_price": 2.5}]
    invoice_id = Invoice.create_invoice(customer_id, orig_items)
    conn = get_db_connection(); cur = conn.cursor()
    cur.execute("SELECT stock_quantity FROM products WHERE product_id=?", (product_ids[0],))
    stock_after_create = cur.fetchone()[0]
    new_items = [
        {"product_id": product_ids[0], "quantity": 2, "unit_price": 2.5},
        {"product_id": product_ids[1], "quantity": 3, "unit_price": 1.0},
    ]
    Invoice.update_invoice(invoice_id, customer_id, new_items, discount=1.0, tax=0.5)
    cur.execute("SELECT stock_quantity FROM products WHERE product_id=?", (product_ids[0],))
    stock_after_update_p1 = cur.fetchone()[0]
    cur.execute("SELECT stock_quantity FROM products WHERE product_id=?", (product_ids[1],))
    stock_after_update_p2 = cur.fetchone()[0]
    conn.close()
    assert stock_after_update_p1 == stock_after_create + 3
    assert stock_after_update_p2 == 50 - 3


def test_delete_invoice_restores_stock(seed_invoice_env):
    customer_id, product_ids = seed_invoice_env
    items = [{"product_id": product_ids[0], "quantity": 4, "unit_price": 2.5}]
    invoice_id = Invoice.create_invoice(customer_id, items)
    conn = get_db_connection(); cur = conn.cursor()
    cur.execute("SELECT stock_quantity FROM products WHERE product_id=?", (product_ids[0],))
    after_create = cur.fetchone()[0]
    assert after_create == 96
    conn.close()
    Invoice.delete_invoice(invoice_id)
    conn = get_db_connection(); cur = conn.cursor()
    cur.execute("SELECT stock_quantity FROM products WHERE product_id=?", (product_ids[0],))
    after_delete = cur.fetchone()[0]
    conn.close()
    assert after_delete == 100


def test_get_all_and_get_by_id(seed_invoice_env):
    customer_id, product_ids = seed_invoice_env
    items = [{"product_id": product_ids[0], "quantity": 1, "unit_price": 2.5}]
    invoice_id = Invoice.create_invoice(customer_id, items, discount=0.0, tax=0.0)
    invoices = Invoice.get_all_invoices()
    assert any(inv.invoice_id == invoice_id for inv in invoices)
    invoice = Invoice.get_invoice_by_id(invoice_id)
    assert invoice["invoice_id"] == invoice_id
    assert len(invoice["items"]) == 1


def test_create_invoice_with_duplicate_product_lines(seed_invoice_env):
    customer_id, product_ids = seed_invoice_env
    pid = product_ids[0]
    items = [
        {"product_id": pid, "quantity": 5, "unit_price": 2.5},
        {"product_id": pid, "quantity": 7, "unit_price": 2.5},
    ]
    invoice_id = Invoice.create_invoice(customer_id, items)
    assert isinstance(invoice_id, int)
    conn = get_db_connection(); cur = conn.cursor()
    cur.execute("SELECT stock_quantity FROM products WHERE product_id=?", (pid,))
    remaining = cur.fetchone()[0]
    conn.close()
    assert remaining == 100 - 12


def test_create_invoice_duplicate_lines_insufficient_stock(seed_invoice_env):
    customer_id, product_ids = seed_invoice_env
    pid = product_ids[0]
    items = [
        {"product_id": pid, "quantity": 60, "unit_price": 2.5},
        {"product_id": pid, "quantity": 50, "unit_price": 2.5},
    ]
    with pytest.raises(ValueError):
        Invoice.create_invoice(customer_id, items)
    conn = get_db_connection(); cur = conn.cursor()
    cur.execute("SELECT stock_quantity FROM products WHERE product_id=?", (pid,))
    remaining = cur.fetchone()[0]
    conn.close()
    assert remaining == 100
