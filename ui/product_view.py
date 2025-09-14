from PyQt6.QtWidgets import (
    QHBoxLayout,
    QLineEdit,
    QMessageBox,
    QPushButton,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)

from models.product import Product


# Product View Class
class ProductView(QWidget):
    def __init__(self):
        super().__init__()
        # Tab style
        self.setStyleSheet(self.get_stylesheet())

        self.layout = QVBoxLayout()  # Set Layout

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

        # Product Table (replaces product_list)
        self.product_table = QTableWidget()
        self.product_table.setColumnCount(4)
        self.product_table.setHorizontalHeaderLabels(["ID", "Name", "Price", "Stock"])
        self.product_table.setSelectionBehavior(self.product_table.SelectionBehavior.SelectRows)
        self.product_table.setEditTriggers(self.product_table.EditTrigger.NoEditTriggers)
        self.product_table.itemSelectionChanged.connect(self.populate_fields_from_selection)
        self.layout.addWidget(self.product_table)

        # Set Button Layout
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
        self.show_low_stock_alert()

    # Product View Style
    def get_stylesheet(self):
        return """
        QWidget {
            background: interlinear(x1:0, y1:0, x2:1, y2:1,
                        stop:0 #eef2f3, stop:1 #8e9eab);
            font-family: 'Segue UI', Tahoma, Geneva, Verdana, sans-serif;
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
            background-color: #21618C;
            color: white;
            border: none;
            border-radius: 8px;
            padding: 8px 16px;
            margin-top: 8px;
        }
        QPushButton:hover {
            background-color: #3498db;
        }
        QTableWidget {
            background-color: white;
            border: 1px solid #999;
            border-radius: 6px;
            padding: 6px;
            max-height: 200px;
        }
        """

    # Load Products Method
    def load_products(self):
        self.product_table.setRowCount(0)
        products = Product.get_all_products()
        for row_idx, product in enumerate(products):
            self.product_table.insertRow(row_idx)
            self.product_table.setItem(row_idx, 0, QTableWidgetItem(str(product.product_id)))
            self.product_table.setItem(row_idx, 1, QTableWidgetItem(product.name))
            self.product_table.setItem(row_idx, 2, QTableWidgetItem(str(product.price)))
            self.product_table.setItem(row_idx, 3, QTableWidgetItem(str(product.stock_quantity)))

    # Act upon a click on Add Product Button
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

        # Call add_product method from the Product Class and pass the entered values
        Product.add_product(name, price, stock)
        QMessageBox.information(self, "Success", "Product added.")
        self.clear_inputs()
        self.load_products()
        self.show_low_stock_alert()

    # Act upon a click on Update Product
    def update_product(self):
        selected = self.product_table.currentRow()
        if selected == -1:
            QMessageBox.warning(self, "Select Product", "Please select a product to update.")
            return
        product_id = int(self.product_table.item(selected, 0).text())
        name = self.name_input.text().strip()
        try:
            price = float(self.price_input.text())
            stock = int(self.stock_input.text())
        except ValueError:
            QMessageBox.warning(self, "Input Error", "Enter valid price and stock quantity.")
            return
        Product.update_product(product_id, name, price, stock)
        QMessageBox.information(self, "Success", "Product updated.")
        self.clear_inputs()
        self.load_products()

    # Act upon a click on Delete product
    def delete_product(self):
        selected = self.product_table.currentRow()
        if selected == -1:
            QMessageBox.warning(self, "Select Product", "Please select a product to delete.")
            return
        product_id = int(self.product_table.item(selected, 0).text())
        reply = QMessageBox.question(
            self,
            "Confirm Delete",
            "Are you sure you want to delete this product?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
        )
        if reply == QMessageBox.StandardButton.Yes:
            Product.delete_product(product_id)
            QMessageBox.information(self, "Success", "Product deleted.")
            self.clear_inputs()
            self.load_products()

    # Clear Input Fields
    def clear_inputs(self):
        self.name_input.clear()
        self.price_input.clear()
        self.stock_input.clear()

    def populate_fields_from_selection(self):
        selected = self.product_table.currentRow()
        if selected == -1:
            self.clear_inputs()
            return
        self.name_input.setText(self.product_table.item(selected, 1).text())
        self.price_input.setText(self.product_table.item(selected, 2).text())
        self.stock_input.setText(self.product_table.item(selected, 3).text())

    def show_low_stock_alert(self):
        low_stock_products = Product.get_products_below_stock(10)
        if low_stock_products:
            product_names = ", ".join([f"{p.name} (Stock: {p.stock_quantity})" for p in low_stock_products])
            QMessageBox.warning(
                self, "Low Stock Alert", f"The following products have low stock quantity:\n{product_names}"
            )
