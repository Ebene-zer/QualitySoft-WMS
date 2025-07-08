#Import the necessary libraries/frameworks
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QLineEdit, QPushButton, QListWidget, QMessageBox, QHBoxLayout
)

from database.db_handler import get_db_connection
from models.product import Product

#Product View Class
class ProductView(QWidget):
    def __init__(self):
        super().__init__()
        # Tab style
        self.setStyleSheet(self.get_stylesheet())

        self.layout = QVBoxLayout() #Set Layout

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

        # Enter key support
        self.stock_input.returnPressed.connect(self.add_product)

        # Add Product Button
        add_button = QPushButton("Add Product")
        add_button.clicked.connect(self.add_product)
        self.layout.addWidget(add_button)

        # Product List
        self.product_list = QListWidget()
        self.layout.addWidget(self.product_list)

        #Set Button Layout
        button_layout = QHBoxLayout()

        # Update Product Button
        update_button = QPushButton("Update Selected")
        update_button.clicked.connect(self.update_product)
        button_layout.addWidget(update_button)

        # Delete Product Button
        delete_button = QPushButton("Delete Selected")
        delete_button.clicked.connect(self.delete_product)
        button_layout.addWidget(delete_button)

        self.layout.addLayout(button_layout)
        self.setLayout(self.layout)

        self.load_products()

#Product View Style
    def get_stylesheet(self):
        return """
        QWidget {
            background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
                        stop:0 #eef2f3, stop:1 #8e9eab);
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            font-size: 14px;
            color: #2c3e50;
        }
        QLabel {
            font-weight: 600;
            margin: 4px 0;
        }
        QLineEdit {
            background-color: white;
            border: 1px solid #999;
            border-radius: 6px;
            padding: 6px;
        }
        QLineEdit:focus {
            border: 2px solid #2980b9;
        }
        QPushButton {
            background-color: #2980b9;
            color: white;
            border: none;
            border-radius: 8px;
            padding: 8px 16px;
            margin-top: 8px;
        }
        QPushButton:hover {
            background-color: #3498db;
        }
        QListWidget {
            background-color: white;
            border: 1px solid #999;
            border-radius: 6px;
            padding: 6px;
            max-height: 200px;
        }
        """

    #Load Products Method
    def load_products(self):
        self.product_list.clear()
        products = Product.get_all_products()
        for p in products:
            self.product_list.addItem(f"{p.product_id} | {p.name} | GHS {p.price:.2f} | {p.stock_quantity}")

    #Act upon a click on Add Product Button
    def add_product(self):
        name = self.name_input.text().strip()
        try:
            price = float(self.price_input.text())
            stock = int(self.stock_input.text())
        except ValueError:
            QMessageBox.warning(self, "Input Error", "Enter valid price and stock quantity.")
            return

        if not name:
            QMessageBox.warning(self, "Input Error", "Product name cannot be empty.")
            return

        #Call add_product method from the Product Class and pass the entered values
        Product.add_product(name, price, stock)
        QMessageBox.information(self, "Success", "Product added.")
        self.clear_inputs()
        self.load_products()

    # Populate fields with product details for editing
    # def populate_product_fields(self, item):
    #     # Defensive: Ensure item has expected format
    #     text = item.text()
    #     if " (" not in text:
    #         QMessageBox.warning(self, "Error", "Selected item format is invalid.")
    #         return
    #     name = text.split(" (" )[0]
    #     connection = get_db_connection()
    #     cursor = connection.cursor()
    #     cursor.execute("SELECT name, price, stock)quantity FROM products WHERE username = ?", (name,))
    #     product = cursor.fetchone()
    #     connection.close()
    #     if product:
    #         self.name_input.setText(product[0])
    #         self.price_input.setText(product[1])
    #         self.stock_input.setText(product[2])
    #     else:
    #         QMessageBox.warning(self, "Error", f"User '{name}' not found in database.")



    #Act upon a click on Update Product
    def update_product(self):
        selected_item = self.product_list.currentItem()
        if not selected_item:
            QMessageBox.warning(self, "Select Product", "Please select a product to update.")
            return

        product_text = selected_item.text()
        product_id = int(product_text.split(" | ")[0])

        name = self.name_input.text().strip()
        try:
            price = float(self.price_input.text())
            stock = int(self.stock_input.text())
        except ValueError:
            QMessageBox.warning(self, "Input Error", "Enter valid price and stock quantity.")
            return

        if not name:
            QMessageBox.warning(self, "Input Error", "Product name cannot be empty.")
            return

        #Call update_product from Product Class and Pass values
        Product.update_product(product_id, name, price, stock)
        QMessageBox.information(self, "Success", "Product updated.")
        self.clear_inputs()
        self.load_products()


    # Act upon a click on Delete product
    def delete_product(self):
        selected_item = self.product_list.currentItem()
        if not selected_item:
            QMessageBox.warning(self, "No Selection", "Select a product to delete.")
            return

        product_id = int(selected_item.text().split(" | ")[0])
        confirm = QMessageBox.question(self, "Confirm Delete", "Are you sure you want to delete this product?")
        if confirm == QMessageBox.StandardButton.Yes:
            Product.delete_product(product_id)
            QMessageBox.information(self, "Deleted", "Product deleted.")
            self.load_products()

#Clear Input Fields
    def clear_inputs(self):
        self.name_input.clear()
        self.price_input.clear()
        self.stock_input.clear()
