from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QPushButton, QLineEdit, QLabel, QListWidget, QMessageBox, QHBoxLayout
)
from PyQt6.QtGui import QPalette, QBrush, QPixmap
from PyQt6.QtCore import Qt, QSize
from models.product import Product

class ProductView(QWidget):
    def __init__(self):
        super().__init__()
        self.set_background_image("bg_images/image1.png")

        self.layout = QVBoxLayout()

        # Input fields
        self.name_input = QLineEdit()
        self.name_input.setPlaceholderText("Product Name")
        self.layout.addWidget(self.name_input)

        self.price_input = QLineEdit()
        self.price_input.setPlaceholderText("Price")
        self.layout.addWidget(self.price_input)

        self.stock_input = QLineEdit()
        self.stock_input.setPlaceholderText("Stock Quantity")
        self.layout.addWidget(self.stock_input)

        # Add Product Button
        add_button = QPushButton("Add Product")
        add_button.clicked.connect(self.add_product)
        self.layout.addWidget(add_button)

        # Product List
        self.product_list = QListWidget()
        self.layout.addWidget(self.product_list)

        # Update / Delete Buttons
        button_layout = QHBoxLayout()

        update_button = QPushButton("Update Selected")
        update_button.clicked.connect(self.update_product)
        button_layout.addWidget(update_button)

        delete_button = QPushButton("Delete Selected")
        delete_button.clicked.connect(self.delete_product)
        button_layout.addWidget(delete_button)

        self.layout.addLayout(button_layout)

        self.setLayout(self.layout)

        self.load_products()

    def set_background_image(self, image_path):
        palette = QPalette()
        pixmap = QPixmap(image_path)
        if not pixmap.isNull():
            scaled_pixmap = pixmap.scaled(self.size(), Qt.AspectRatioMode.IgnoreAspectRatio)
            palette.setBrush(QPalette.ColorRole.Window, QBrush(scaled_pixmap))
            self.setPalette(palette)

    def add_product(self):
        name = self.name_input.text().strip()
        try:
            price = float(self.price_input.text().strip())
            stock = int(self.stock_input.text().strip())
        except ValueError:
            QMessageBox.warning(self, "Input Error", "Enter valid numbers for price and stock.")
            return

        if not name:
            QMessageBox.warning(self, "Input Error", "Product name cannot be empty.")
            return

        Product.add_product(name, price, stock)
        QMessageBox.information(self, "Success", "Product added.")
        self.load_products()
        self.name_input.clear()
        self.price_input.clear()
        self.stock_input.clear()

    def load_products(self):
        self.product_list.clear()
        products = Product.get_all_products()
        for product in products:
            self.product_list.addItem(f"{product.product_id}. {product.name} - GHS {product.price} (Stock: {product.stock_quantity})")

    def update_product(self):
        selected_item = self.product_list.currentItem()
        if not selected_item:
            QMessageBox.warning(self, "Select Product", "Please select a product to update.")
            return

        product_text = selected_item.text()
        product_id = int(product_text.split(".")[0])

        name = self.name_input.text().strip()
        try:
            price = float(self.price_input.text().strip())
            stock = int(self.stock_input.text().strip())
        except ValueError:
            QMessageBox.warning(self, "Input Error", "Enter valid numbers for price and stock.")
            return

        if not name:
            QMessageBox.warning(self, "Input Error", "Product name cannot be empty.")
            return

        Product.update_product(product_id, name, price, stock)
        QMessageBox.information(self, "Success", "Product updated.")
        self.load_products()

    def delete_product(self):
        selected_item = self.product_list.currentItem()
        if not selected_item:
            QMessageBox.warning(self, "Select Product", "Please select a product to delete.")
            return

        product_text = selected_item.text()
        product_id = int(product_text.split(".")[0])

        confirm = QMessageBox.question(self, "Confirm Delete", "Are you sure you want to delete this product?")
        if confirm == QMessageBox.StandardButton.Yes:
            Product.delete_product(product_id)
            QMessageBox.information(self, "Deleted", "Product deleted.")
            self.load_products()
