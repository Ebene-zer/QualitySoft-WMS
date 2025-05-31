from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QPushButton, QLineEdit, QLabel, QListWidget, QMessageBox,
    QHBoxLayout, QComboBox, QCompleter
)
from PyQt6.QtGui import QPalette, QBrush, QPixmap
from PyQt6.QtCore import QSize, Qt
from models.customer import Customer
from models.product import Product
from models.invoice import Invoice

class InvoiceView(QWidget):
    def __init__(self):
        super().__init__()
        self.set_background_image("bg_images/image1.png")

        self.layout = QVBoxLayout()

        # Customer Dropdown
        self.customer_dropdown = QComboBox()
        self.customer_dropdown.setEditable(True)
        customer_completer = QCompleter()
        customer_completer.setCaseSensitivity(Qt.CaseSensitivity.CaseInsensitive)
        self.customer_dropdown.setCompleter(customer_completer)
        self.load_customers()
        self.layout.addWidget(QLabel("Select Customer:"))
        self.layout.addWidget(self.customer_dropdown)

        # Product Dropdown
        self.product_dropdown = QComboBox()
        self.product_dropdown.setEditable(True)
        product_completer = QCompleter()
        product_completer.setCaseSensitivity(Qt.CaseSensitivity.CaseInsensitive)
        self.product_dropdown.setCompleter(product_completer)
        self.load_products()
        self.layout.addWidget(QLabel("Select Product:"))
        self.layout.addWidget(self.product_dropdown)

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
        self.discount_input.setPlaceholderText("Discount (GHS)")
        self.layout.addWidget(self.discount_input)

        self.tax_input = QLineEdit()
        self.tax_input.setPlaceholderText("Tax (GHS)")
        self.layout.addWidget(self.tax_input)

        # Total Display
        self.total_label = QLabel("Total: GHS 0.00")
        self.layout.addWidget(self.total_label)

        # Save Invoice Button
        save_invoice_button = QPushButton("Save Invoice")
        save_invoice_button.clicked.connect(self.save_invoice)
        self.layout.addWidget(save_invoice_button)

        self.setLayout(self.layout)

        self.items = []

    def set_background_image(self, image_path):
        palette = QPalette()
        pixmap = QPixmap(image_path)
        if not pixmap.isNull():
            scaled_pixmap = pixmap.scaled(self.size(), Qt.AspectRatioMode.IgnoreAspectRatio)
            palette.setBrush(QPalette.ColorRole.Window, QBrush(scaled_pixmap))
            self.setPalette(palette)

    def load_customers(self):
        self.customer_dropdown.clear()
        customers = Customer.get_all_customers()
        customer_names = [f"{c.customer_id} - {c.name}" for c in customers]
        self.customer_dropdown.addItems(customer_names)
        self.customer_dropdown.completer().setModel(self.customer_dropdown.model())


    def load_products(self):
        self.product_dropdown.clear()
        products = Product.get_all_products()
        product_names = [f"{p.product_id} - {p.name}" for p in products]
        self.product_dropdown.addItems(product_names)
        self.product_dropdown.completer().setModel(self.product_dropdown.model())


    def add_item_to_invoice(self):
        if self.product_dropdown.currentIndex() == -1:
            QMessageBox.warning(self, "Input Error", "Select a product.")
            return

        try:
            quantity = int(self.quantity_input.text().strip())
        except ValueError:
            QMessageBox.warning(self, "Input Error", "Enter a valid quantity.")
            return

        product_text = self.product_dropdown.currentText()
        product_id = int(product_text.split(" - ")[0])
        product = Product.get_product_by_id(product_id)

        if quantity > product.stock_quantity:
            QMessageBox.warning(self, "Stock Error", f"Only {product.stock_quantity} units of {product.name} available.")
            return

        self.items.append({
            "product_id": product.product_id,
            "quantity": quantity,
            "unit_price": product.price
        })

        self.invoice_items_list.addItem(f"{product.name} x {quantity} @ GHS {product.price}")
        self.update_total()
        self.quantity_input.clear()

    def update_total(self):
        subtotal = sum(item['quantity'] * item['unit_price'] for item in self.items)
        try:
            discount = float(self.discount_input.text()) if self.discount_input.text() else 0.0
            tax = float(self.tax_input.text()) if self.tax_input.text() else 0.0
        except ValueError:
            discount, tax = 0.0, 0.0

        total = subtotal - discount + tax
        self.total_label.setText(f"Total: GHS {total:.2f}")

    def save_invoice(self):
        if not self.items:
            QMessageBox.warning(self, "Input Error", "Add at least one item to the invoice.")
            return

        customer_text = self.customer_dropdown.currentText()
        if not customer_text:
            QMessageBox.warning(self, "Input Error", "Select a customer.")
            return

        customer_id = int(customer_text.split(" - ")[0])

        try:
            discount = float(self.discount_input.text()) if self.discount_input.text() else 0.0
            tax = float(self.tax_input.text()) if self.tax_input.text() else 0.0
        except ValueError:
            QMessageBox.warning(self, "Input Error", "Enter valid numbers for discount and tax.")
            return

        try:
            invoice_id = Invoice.create_invoice(customer_id, self.items, discount, tax)
            QMessageBox.information(self, "Success", f"Invoice #{invoice_id} created successfully.")
            Invoice.print_receipt(invoice_id)
            self.reset_invoice_form()
        except ValueError as e:
            QMessageBox.warning(self, "Error", str(e))

    def reset_invoice_form(self):
        self.invoice_items_list.clear()
        self.discount_input.clear()
        self.tax_input.clear()
        self.total_label.setText("Total: GHS 0.00")
        self.items = []
        self.load_products()
        self.load_customers()
