from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QPushButton, QLineEdit, QLabel, QListWidget,
    QMessageBox, QHBoxLayout
)
from PyQt6.QtCore import Qt
from models.customer import Customer


class CustomerView(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Customer Management")
        self.setStyleSheet(self.get_stylesheet())
        self.setMinimumSize(600, 400)

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

        # Enter key support
        self.address_input.returnPressed.connect(self.add_customer)

        # Add Customer Button
        add_button = QPushButton("Add Customer")
        add_button.clicked.connect(self.add_customer)
        self.layout.addWidget(add_button)

        # Customer List
        self.customer_list = QListWidget()
        self.layout.addWidget(self.customer_list)

        # Set Button Layout
        button_layout = QHBoxLayout()

        # Update Customer Button
        update_button = QPushButton("Update Selected")
        update_button.clicked.connect(self.update_customer)
        button_layout.addWidget(update_button)

        # Delete Customer Button
        delete_button = QPushButton("Delete Selected")
        delete_button.clicked.connect(self.delete_customer)
        button_layout.addWidget(delete_button)

        self.layout.addLayout(button_layout)

        self.setLayout(self.layout)
        self.load_customers()

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

    def load_customers(self):
        self.customer_list.clear()
        customers = Customer.get_all_customers()
        for c in customers:
            self.customer_list.addItem(f"{c.customer_id} - {c.name} | {c.phone} | {c.address}")

    def add_customer(self):
        name = self.name_input.text().strip()
        phone = self.phone_input.text().strip()
        address = self.address_input.text().strip()

        if not name:
            QMessageBox.warning(self, "Input Error", "Customer name is required.")
            return

        try:
            Customer.add_customer(name, phone, address)
            QMessageBox.information(self, "Success", "Customer added.")
            self.load_customers()
            self.clear_inputs()
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to add customer:\n{e}")

    def update_customer(self):
        customer_id = self.get_selected_customer_id()
        if customer_id is None:
            QMessageBox.warning(self, "Selection Error", "Select a valid customer to update.")
            return

        name = self.name_input.text().strip()
        phone = self.phone_input.text().strip()
        address = self.address_input.text().strip()

        if not name:
            QMessageBox.warning(self, "Input Error", "Customer name is required.")
            return

        Customer.update_customer(customer_id, name, phone, address)
        QMessageBox.information(self, "Success", "Customer updated.")
        self.load_customers()
        self.clear_inputs()

    def delete_customer(self):
        customer_id = self.get_selected_customer_id()
        if customer_id is None:
            QMessageBox.warning(self, "Selection Error", "Select a valid customer to delete.")
            return

        reply = QMessageBox.question(
            self, "Confirm Delete",
            f"Are you sure you want to delete customer #{customer_id}?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        if reply == QMessageBox.StandardButton.Yes:
            Customer.delete_customer(customer_id)
            QMessageBox.information(self, "Deleted", "Customer deleted.")
            self.load_customers()

    def get_selected_customer_id(self):
        selected = self.customer_list.currentItem()
        if not selected:
            return None
        text = selected.text()
        parts = text.split(" - ")
        if len(parts) < 2:
            return None
        try:
            return int(parts[0])
        except ValueError:
            return None

    def clear_inputs(self):
        self.name_input.clear()
        self.phone_input.clear()
        self.address_input.clear()
