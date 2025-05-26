from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QPushButton, QLineEdit, QLabel, QListWidget, QMessageBox, QHBoxLayout
)
from PyQt6.QtGui import QPalette, QBrush, QPixmap
from PyQt6.QtCore import QSize, Qt

from models.customer import Customer


class CustomerWindow(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Customer Management")

        # Allow resizing and maximization
        self.resize(800, 600)
        self.setMinimumSize(600, 400)

        self.set_background_image("bg_images/customer1.jpeg")

        self.layout = QVBoxLayout()

        # Input fields
        self.name_input = QLineEdit()
        self.name_input.setPlaceholderText("Customer Name")
        self.layout.addWidget(self.name_input)

        self.phone_input = QLineEdit()
        self.phone_input.setPlaceholderText("Phone Number")
        self.layout.addWidget(self.phone_input)

        self.address_input = QLineEdit()
        self.address_input.setPlaceholderText("Address")
        self.layout.addWidget(self.address_input)

        # Add customer button
        add_button = QPushButton("Add Customer")
        add_button.clicked.connect(self.add_customer)
        self.layout.addWidget(add_button)

        # Customer list
        self.customer_list = QListWidget()
        self.layout.addWidget(self.customer_list)

        # Buttons for update and delete
        button_layout = QHBoxLayout()

        update_button = QPushButton("Update Selected")
        update_button.clicked.connect(self.update_customer)
        button_layout.addWidget(update_button)

        delete_button = QPushButton("Delete Selected")
        delete_button.clicked.connect(self.delete_customer)
        button_layout.addWidget(delete_button)

        self.layout.addLayout(button_layout)

        # Load existing customers into list
        self.load_customers()

        self.setLayout(self.layout)

    def set_background_image(self, image_path):
        palette = QPalette()
        pixmap = QPixmap(image_path)
        if not pixmap.isNull():
            scaled_pixmap = pixmap.scaled(self.size(), Qt.AspectRatioMode.IgnoreAspectRatio)
            palette.setBrush(QPalette.ColorRole.Window, QBrush(scaled_pixmap))
            self.setPalette(palette)

    def add_customer(self):
        name = self.name_input.text().strip()
        phone = self.phone_input.text().strip()
        address = self.address_input.text().strip()

        if not name:
            QMessageBox.warning(self, "Input Error", "Customer name cannot be empty.")
            return

        Customer.add_customer(name, phone, address)
        QMessageBox.information(self, "Success", "Customer added.")
        self.load_customers()
        self.name_input.clear()
        self.phone_input.clear()
        self.address_input.clear()

    def load_customers(self):
        self.customer_list.clear()
        customers = Customer.get_all_customers()
        for customer in customers:
            self.customer_list.addItem(f"{customer.customer_id}. {customer.name} | {customer.phone_number} | {customer.address}")

    def update_customer(self):
        selected_item = self.customer_list.currentItem()
        if not selected_item:
            QMessageBox.warning(self, "Select Customer", "Please select a customer to update.")
            return

        customer_text = selected_item.text()
        customer_id = int(customer_text.split(".")[0])

        name = self.name_input.text().strip()
        phone = self.phone_input.text().strip()
        address = self.address_input.text().strip()

        if not name:
            QMessageBox.warning(self, "Input Error", "Customer name cannot be empty.")
            return

        Customer.update_customer(customer_id, name, phone, address)
        QMessageBox.information(self, "Success", "Customer updated.")
        self.load_customers()

    def delete_customer(self):
        selected_item = self.customer_list.currentItem()
        if not selected_item:
            QMessageBox.warning(self, "Select Customer", "Please select a customer to delete.")
            return

        customer_text = selected_item.text()
        customer_id = int(customer_text.split(".")[0])

        confirm = QMessageBox.question(self, "Confirm Delete", "Are you sure you want to delete this customer?")
        if confirm == QMessageBox.StandardButton.Yes:
            Customer.delete_customer(customer_id)
            QMessageBox.information(self, "Deleted", "Customer deleted.")
            self.load_customers()
