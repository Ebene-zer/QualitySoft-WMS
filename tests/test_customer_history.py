from unittest.mock import patch

from models.customer import Customer
from models.invoice import Invoice
from models.product import Product
from ui.customer_history_dialog import CustomerHistoryDialog
from ui.customer_view import CustomerView


def _get_customer_id_by_name(name: str) -> int:
    for c in Customer.get_all_customers():
        if c.name == name:
            return c.customer_id
    raise AssertionError("Customer not found")


def _get_product_id_by_name(name: str) -> int:
    for p in Product.get_all_products():
        if p.name == name:
            return p.product_id
    raise AssertionError("Product not found")


def test_view_history_opens_dialog(qapp):
    # Arrange
    Customer.add_customer("Alice", "0123456789", "Wonderland")
    Product.add_product("Widget", 5.0, 10)
    customer_id = _get_customer_id_by_name("Alice")
    product_id = _get_product_id_by_name("Widget")

    Invoice.create_invoice(
        customer_id,
        items=[{"product_id": product_id, "quantity": 2, "unit_price": 5.0}],
        discount=0.0,
        tax=0.0,
    )

    view = CustomerView()

    # Select the customer row in the table
    selected_row = None
    for r in range(view.customer_table.rowCount()):
        if view.customer_table.item(r, 1).text() == "Alice":
            selected_row = r
            break
    assert selected_row is not None
    view.customer_table.setCurrentCell(selected_row, 0)

    # Patch the dialog to verify it is invoked
    opened = {"called": False, "cid": None, "cname": None}

    class FakeDialog:
        def __init__(self, parent, cid, cname):
            opened["called"] = True
            opened["cid"] = cid
            opened["cname"] = cname

        def exec(self):
            return 0

    with patch("ui.customer_view.CustomerHistoryDialog", FakeDialog):
        view.view_history()

    assert opened["called"] is True
    assert opened["cid"] == customer_id
    assert opened["cname"] == "Alice"


def test_history_dialog_export_pdf_only(qapp, tmp_path):
    # Prepare minimal dataset
    Customer.add_customer("Bob", "9876543210", "Dreamland")
    Product.add_product("Gadget", 3.0, 5)
    cid = _get_customer_id_by_name("Bob")
    pid = _get_product_id_by_name("Gadget")
    Invoice.create_invoice(
        cid,
        items=[{"product_id": pid, "quantity": 1, "unit_price": 3.0}],
        discount=0.0,
        tax=0.0,
    )

    # Create real dialog and export only PDF now
    dlg = CustomerHistoryDialog(None, cid, "Bob")

    pdf_path = tmp_path / "history.pdf"
    dlg.export_pdf_to(str(pdf_path))
    assert pdf_path.exists() and pdf_path.stat().st_size > 0
