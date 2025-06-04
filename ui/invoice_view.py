#Import Framework and Library
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QPushButton, QLineEdit, QLabel, QListWidget, QMessageBox, QComboBox, QCompleter
)
from PyQt6.QtCore import Qt, QObject, QEvent
from models.customer import Customer
from models.product import Product
from models.invoice import Invoice


class SelectAllOnFocus(QObject):
    def eventFilter(self, obj, event):
        if event.type() == QEvent.Type.FocusIn:
            obj.selectAll()
        return False

#Invoice View Class
class InvoiceView(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Prepare Invoice") #Tab name
        self.setStyleSheet(self.get_stylesheet())
        self.layout = QVBoxLayout()

        # Customer Dropdown
        self.customer_dropdown = QComboBox()
        self.customer_dropdown.setEditable(True)
        self.customer_completer = QCompleter()
        self.customer_completer.setCaseSensitivity(Qt.CaseSensitivity.CaseInsensitive)
        self.customer_dropdown.setCompleter(self.customer_completer)
        self.layout.addWidget(QLabel("Select Customer:"))
        self.layout.addWidget(self.customer_dropdown)

        # Product Dropdown
        self.product_dropdown = QComboBox()
        self.product_dropdown.setEditable(True)
        self.product_completer = QCompleter()
        self.product_completer.setCaseSensitivity(Qt.CaseSensitivity.CaseInsensitive)
        self.product_dropdown.setCompleter(self.product_completer)
        self.layout.addWidget(QLabel("Select Product:"))
        self.layout.addWidget(self.product_dropdown)

        # Install select-all-on-focus
        focus_filter = SelectAllOnFocus()
        self.customer_dropdown.lineEdit().installEventFilter(focus_filter)
        self.product_dropdown.lineEdit().installEventFilter(focus_filter)

        # Quantity Input
        self.quantity_input = QLineEdit()
        self.quantity_input.setPlaceholderText("Quantity")
        self.layout.addWidget(self.quantity_input)

        # Add Item Button
        add_item_button = QPushButton("Add to Invoice")
        add_item_button.clicked.connect(self.add_item_to_invoice)
        self.layout.addWidget(add_item_button)

        # Invoice Items List
        self.invoice_items_list = QListWidget()
        self.layout.addWidget(self.invoice_items_list)

        # Discount and Tax Inputs
        self.discount_input = QLineEdit()
        self.discount_input.setPlaceholderText("Discount (GH)")
        self.layout.addWidget(self.discount_input)

        self.tax_input = QLineEdit()
        self.tax_input.setPlaceholderText("Tax (GH)")
        self.layout.addWidget(self.tax_input)

        # Total Label
        self.total_label = QLabel("Total: GHS 0.00")
        self.layout.addWidget(self.total_label)

        # Save Invoice Button
        save_invoice_button = QPushButton("Save Invoice")
        save_invoice_button.clicked.connect(self.save_invoice)
        self.layout.addWidget(save_invoice_button)

        self.setLayout(self.layout)

        self.items = []
        self.load_customers()
        self.load_products()


#Invoice  View Style
    def get_stylesheet(self):
        return """
        QWidget {
            background: qlineargradient(spread:pad, x1:0, y1:0, x2:1, y2:1,
                        stop:0 #f5f7fa, stop:1 #c3cfe2);
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            font-size: 14px;
            color: #333333;
        }
        QLabel {
            font-weight: 600;
            margin: 4px 0;
        }
        QLineEdit, QComboBox {
            background-color: white;
            border: 1px solid #aaa;
            border-radius: 6px;
            padding: 6px;
        }
        QLineEdit:focus, QComboBox:focus {
            border: 2px solid #409EFF;
        }
        QPushButton {
            background-color: #409EFF;
            color: white;
            border: none;
            border-radius: 8px;
            padding: 8px 16px;
            margin-top: 8px;
        }
        QPushButton:hover {
            background-color: #66b1ff;
        }
        QListWidget {
            background-color: white;
            border: 1px solid #aaa;
            border-radius: 6px;
            padding: 6px;
            max-height: 120px;
        }
        """

#Load all Customers
    def load_customers(self):
        self.customer_dropdown.clear()
        customers = Customer.get_all_customers()
        names = [f"{c.customer_id} - {c.name}" for c in customers]
        self.customer_dropdown.addItems(names)
        self.customer_completer.setModel(self.customer_dropdown.model())

#Load available Products
    def load_products(self):
        self.product_dropdown.clear()
        products = Product.get_all_products()
        names = [f"{p.product_id} - {p.name} (GH {p.price})" for p in products]
        self.product_dropdown.addItems(names)
        self.product_completer.setModel(self.product_dropdown.model())


# Act upon a click on Add to Invoice Button
    def add_item_to_invoice(self):
        if self.product_dropdown.currentIndex() == -1:
            QMessageBox.warning(self, "Input Error", "Select a product.")
            return
        try:
            quantity = int(self.quantity_input.text())
        except ValueError:
            QMessageBox.warning(self, "Input Error", "Enter a valid quantity.")
            return

        product_text = self.product_dropdown.currentText()
        product_id = int(product_text.split(" - ")[0])
        product = Product.get_product_by_id(product_id)

        if quantity > product.stock_quantity:
            QMessageBox.warning(self, "Stock Error", f"Only {product.stock_quantity} units available.")
            return

        self.items.append({
            "product_id": product.product_id,
            "quantity": quantity,
            "unit_price": product.price
        })

        self.invoice_items_list.addItem(f"{product.name} x {quantity} @ GH {product.price}")
        self.update_total()
        self.quantity_input.clear()


#Update total upon each add
    def update_total(self):
        subtotal = sum(item['quantity'] * item['unit_price'] for item in self.items)
        discount = float(self.discount_input.text() or 0)
        tax = float(self.tax_input.text() or 0)
        total = subtotal - discount + tax
        self.total_label.setText(f"Total: GH {total:.2f}")


# Act upon a click on Save Invoice Button
    def save_invoice(self):
        if not self.items:
            QMessageBox.warning(self, "Input Error", "Add at least one item.")
            return

        customer_text = self.customer_dropdown.currentText()
        if not customer_text:
            QMessageBox.warning(self, "Input Error", "Select a customer.")
            return

        customer_id = int(customer_text.split(" - ")[0])
        discount = float(self.discount_input.text() or 0)
        tax = float(self.tax_input.text() or 0)
        invoice_id = Invoice.create_invoice(customer_id, self.items, discount, tax)
        QMessageBox.information(self, "Success", f"Invoice #{invoice_id} created.")
        Invoice.print_receipt(invoice_id)
        self.reset_invoice_form()


#Take Invoice Form Back to Default State After each Save
    def reset_invoice_form(self):
        self.invoice_items_list.clear()
        self.discount_input.clear()
        self.tax_input.clear()
        self.total_label.setText("Total: GHS 0.00")
        self.items = []
        self.load_products()
        self.load_customers()
