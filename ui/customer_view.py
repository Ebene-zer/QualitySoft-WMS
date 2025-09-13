from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QLineEdit, QPushButton, QMessageBox, QHBoxLayout, QTableWidget, QTableWidgetItem
)
from models.customer import Customer


class CustomerView(QWidget):
    def __init__(self):
        super().__init__()
        self.setStyleSheet(self.get_stylesheet())

        self.layout = QVBoxLayout()

        # Input fields
        self.name_input = QLineEdit()
        self.name_input.setPlaceholderText("Customer Name")
        self.layout.addWidget(self.name_input)

        self.phone_input = QLineEdit()
        self.phone_input.setPlaceholderText("Phone Number")
        self.phone_input.setMaxLength(10)  # Limit to 10 digits
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

        # Customer Table
        self.customer_table = QTableWidget()
        self.customer_table.setColumnCount(4)
        self.customer_table.setHorizontalHeaderLabels(["ID", "Name", "Phone", "Address"])
        self.customer_table.setSelectionBehavior(self.customer_table.SelectionBehavior.SelectRows)
        self.customer_table.setEditTriggers(self.customer_table.EditTrigger.NoEditTriggers)
        self.customer_table.itemSelectionChanged.connect(self.populate_fields_from_selection)
        self.layout.addWidget(self.customer_table)

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

    #Customer View Style
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

    #Load added customers
    def load_customers(self):
        self.customer_table.setRowCount(0)
        customers = Customer.get_all_customers()
        for row_idx, customer in enumerate(customers):
            self.customer_table.insertRow(row_idx)
            self.customer_table.setItem(row_idx, 0, QTableWidgetItem(str(customer.customer_id)))
            self.customer_table.setItem(row_idx, 1, QTableWidgetItem(customer.name))
            self.customer_table.setItem(row_idx, 2, QTableWidgetItem(customer.phone_number))
            self.customer_table.setItem(row_idx, 3, QTableWidgetItem(customer.address))


    # Act upon a click on Add Customer Button
    def add_customer(self):
        name = self.name_input.text().strip()
        phone_number = self.phone_input.text().strip()
        address = self.address_input.text().strip()

        if not name:
            QMessageBox.warning(self, "Input Error", "Customer name is required.")
            return
        if not address:
            QMessageBox.warning(self, "Input Error", "Address is required.")
            return
        if not (phone_number.isdigit() and len(phone_number) == 10):
            QMessageBox.warning(self, "Input Error", "Phone number must be 10 digits.")
            return

        try:
            Customer.add_customer(name, phone_number, address)
            QMessageBox.information(self, "Success", "Customer added.")
            self.load_customers()
            self.clear_inputs()
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to add customer:\n{e}")



    # Act upon a click on Update Customer button
    def update_customer(self):
        customer_id = self.get_selected_customer_id()
        if customer_id is None:
            QMessageBox.warning(self, "Selection Error", "Select a customer to update.")
            return

        name = self.name_input.text().strip()
        phone_number = self.phone_input.text().strip()
        address = self.address_input.text().strip()

        if not name:
            QMessageBox.warning(self, "Input Error", "Customer name is required.")
            return
        if not address:
            QMessageBox.warning(self, "Input Error", "Address is required.")
            return
        if not (phone_number.isdigit() and len(phone_number) == 10):
            QMessageBox.warning(self, "Input Error", "Phone number must be 10 digits")
            return

        try:
            Customer.update_customer(customer_id, name, phone_number, address)
            QMessageBox.information(self, "Success", "Customer details updated.")
            self.load_customers()
            self.clear_inputs()
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to update customer:\n{e}")


    # Act upon a click on Delete Customer Button
    def delete_customer(self):
        customer_id = self.get_selected_customer_id()
        if customer_id is None:
            QMessageBox.warning(self, "Selection Error", "Select a valid customer to delete.")
            return

        reply = QMessageBox.question(
            self, "Confirm Delete",
            f"Are you sure you want to delete customer {customer_id}?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        if reply == QMessageBox.StandardButton.Yes:
            Customer.delete_customer(customer_id)
            QMessageBox.information(self, "Deleted", "Customer deleted.")
            self.load_customers()


    def get_selected_customer_id(self):
        selected = self.customer_table.currentRow()
        if selected == -1:
            return None
        return int(self.customer_table.item(selected, 0).text())

   #Clear Input after usage
    def clear_inputs(self):
        self.name_input.clear()
        self.phone_input.clear()
        self.address_input.clear()
        # no details label — keep inputs cleared

    def populate_fields_from_selection(self):
        selected = self.customer_table.currentRow()
        if selected == -1:
            self.clear_inputs()
            return
        self.name_input.setText(self.customer_table.item(selected, 1).text())
        self.phone_input.setText(self.customer_table.item(selected, 2).text())
        self.address_input.setText(self.customer_table.item(selected, 3).text())
        # previous implementation: no extra details label
