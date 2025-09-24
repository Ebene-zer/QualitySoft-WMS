from PyQt6.QtCore import QRegularExpression
from PyQt6.QtGui import QRegularExpressionValidator
from PyQt6.QtWidgets import (
    QHBoxLayout,
    QHeaderView,
    QLineEdit,
    QMessageBox,
    QPushButton,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)

from models.customer import Customer
from ui.customer_history_dialog import CustomerHistoryDialog
from utils.ui_common import (
    SEARCH_PLACEHOLDER_CUSTOMERS,
    SEARCH_TOOLTIP_CUSTOMERS,
    create_top_actions_row,
)


class CustomerView(QWidget):
    def __init__(self):
        super().__init__()
        self.setStyleSheet(self.get_stylesheet())

        self.layout = QVBoxLayout()

        # Input fields in a single row
        inputs_row = QHBoxLayout()
        inputs_row.setSpacing(10)

        self.name_input = QLineEdit()
        self.name_input.setPlaceholderText("Customer Name")
        self.name_input.setMinimumWidth(240)
        inputs_row.addWidget(self.name_input, 1)

        self.phone_input = QLineEdit()
        self.phone_input.setPlaceholderText("Phone Number")
        self.phone_input.setMaxLength(10)  # Limit to 10 digits
        # Enforce digits-only and up to 10 digits
        self.phone_input.setValidator(QRegularExpressionValidator(QRegularExpression(r"^\d{0,10}$"), self))
        self.phone_input.setFixedWidth(160)
        inputs_row.addWidget(self.phone_input)

        self.address_input = QLineEdit()
        self.address_input.setPlaceholderText("Address")
        self.address_input.setMinimumWidth(260)
        inputs_row.addWidget(self.address_input, 1)

        # Enter key support
        self.address_input.returnPressed.connect(self.add_customer)

        self.layout.addLayout(inputs_row)

        # Add Customer Button and Search (same row)
        top_actions, self.search_input, self.search_timer, add_button = create_top_actions_row(
            self,
            "Add Customer",
            self.add_customer,
            SEARCH_PLACEHOLDER_CUSTOMERS,
            SEARCH_TOOLTIP_CUSTOMERS,
            lambda: self.filter_customers(self.search_input.text()),
        )
        self.layout.addLayout(top_actions)

        # Customer Table
        self.customer_table = QTableWidget()
        self.customer_table.setColumnCount(4)
        self.customer_table.setHorizontalHeaderLabels(["ID", "Name", "Phone", "Address"])
        self.customer_table.setSelectionBehavior(self.customer_table.SelectionBehavior.SelectRows)
        self.customer_table.setEditTriggers(self.customer_table.EditTrigger.NoEditTriggers)
        # Set header resize behavior once to avoid repeated auto-resizes
        self.customer_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
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

        # View History Button
        history_button = QPushButton("View History")
        history_button.clicked.connect(self.view_history)
        button_layout.addWidget(history_button)

        self.layout.addLayout(button_layout)

        self.setLayout(self.layout)
        self.load_customers()

    # Customer View Style
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

    # Load added customers
    def load_customers(self):
        tbl = self.customer_table
        prev_sorting = tbl.isSortingEnabled()
        # Reduce UI work during bulk load
        tbl.setSortingEnabled(False)
        tbl.setUpdatesEnabled(False)
        tbl.blockSignals(True)

        customers = Customer.get_all_customers()
        tbl.setRowCount(len(customers))
        for row_idx, customer in enumerate(customers):
            tbl.setItem(row_idx, 0, QTableWidgetItem(str(customer.customer_id)))
            tbl.setItem(row_idx, 1, QTableWidgetItem(customer.name))
            tbl.setItem(row_idx, 2, QTableWidgetItem(customer.phone_number))
            tbl.setItem(row_idx, 3, QTableWidgetItem(customer.address))

        # Restore UI updates and signals
        tbl.blockSignals(False)
        tbl.setUpdatesEnabled(True)
        tbl.setSortingEnabled(prev_sorting)

        # Re-apply current filter
        self.filter_customers(self.search_input.text())

    # Helpers for incremental updates
    def _find_customer_row(self, customer_id: int) -> int:
        for row in range(self.customer_table.rowCount()):
            item = self.customer_table.item(row, 0)
            if item and item.text() == str(customer_id):
                return row
        return -1

    def _append_customer_row(self, customer_id: int, name: str, phone: str, address: str):
        row_idx = self.customer_table.rowCount()
        self.customer_table.setRowCount(row_idx + 1)
        self.customer_table.setItem(row_idx, 0, QTableWidgetItem(str(customer_id)))
        self.customer_table.setItem(row_idx, 1, QTableWidgetItem(name))
        self.customer_table.setItem(row_idx, 2, QTableWidgetItem(phone))
        self.customer_table.setItem(row_idx, 3, QTableWidgetItem(address))

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
            new_id = Customer.add_customer(name, phone_number, address)
        except ValueError as e:
            # Duplicate (name, phone) or validation errors from model
            QMessageBox.warning(self, "Cannot Add Customer", str(e))
            return
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to add customer:\n{e}")
            return
        QMessageBox.information(self, "Success", "Customer added.")
        # Incremental UI update instead of full reload
        self._append_customer_row(new_id, name, phone_number, address)
        self.filter_customers(self.search_input.text())
        self.clear_inputs()

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
        except ValueError as e:
            # Duplicate (name, phone) or validation errors from model
            QMessageBox.warning(self, "Cannot Update Customer", str(e))
            return
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to update customer:\n{e}")
            return
        QMessageBox.information(self, "Success", "Customer details updated.")
        # Incremental UI update
        row = self.customer_table.currentRow()
        self.customer_table.setItem(row, 1, QTableWidgetItem(name))
        self.customer_table.setItem(row, 2, QTableWidgetItem(phone_number))
        self.customer_table.setItem(row, 3, QTableWidgetItem(address))
        self.filter_customers(self.search_input.text())
        self.clear_inputs()

    # Act upon a click on Delete Customer Button
    def delete_customer(self):
        customer_id = self.get_selected_customer_id()
        if customer_id is None:
            QMessageBox.warning(self, "Selection Error", "Select a valid customer to delete.")
            return

        reply = QMessageBox.question(
            self,
            "Confirm Delete",
            f"Are you sure you want to delete customer {customer_id}?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
        )
        if reply == QMessageBox.StandardButton.Yes:
            try:
                Customer.delete_customer(customer_id)
            except Exception as e:
                QMessageBox.critical(
                    self,
                    "Delete Failed",
                    "Could not delete customer. They may have existing invoices linked to them.\n" + str(e),
                )
                return
            QMessageBox.information(self, "Deleted", "Customer deleted.")
            # Incremental UI update
            row = self.customer_table.currentRow()
            if row != -1:
                self.customer_table.removeRow(row)
            self.clear_inputs()

    def get_selected_customer_id(self):
        selected = self.customer_table.currentRow()
        if selected == -1:
            return None
        return int(self.customer_table.item(selected, 0).text())

    # Clear Input after usage
    def clear_inputs(self):
        self.name_input.clear()
        self.phone_input.clear()
        self.address_input.clear()

    def populate_fields_from_selection(self):
        selected = self.customer_table.currentRow()
        if selected == -1:
            self.clear_inputs()
            return
        self.name_input.setText(self.customer_table.item(selected, 1).text())
        self.phone_input.setText(self.customer_table.item(selected, 2).text())
        self.address_input.setText(self.customer_table.item(selected, 3).text())
        # previous implementation: no extra details label

    def view_history(self):
        """Show recent invoices for the selected customer using a dedicated dialog."""
        customer_id = self.get_selected_customer_id()
        if customer_id is None:
            QMessageBox.information(self, "Purchase History", "Select a customer to view history.")
            return
        # Get name for dialog title
        selected = self.customer_table.currentRow()
        customer_name = self.customer_table.item(selected, 1).text() if selected != -1 else str(customer_id)
        try:
            dlg = CustomerHistoryDialog(self, customer_id, customer_name)
            dlg.exec()
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to open purchase history:\n{e}")
            return

    def filter_customers(self, text: str):
        """Filter customer table rows by text across all columns (case-insensitive)."""
        text = (text or "").strip().lower()
        for row in range(self.customer_table.rowCount()):
            if not text:
                self.customer_table.setRowHidden(row, False)
                continue
            match = False
            for col in range(self.customer_table.columnCount()):
                item = self.customer_table.item(row, col)
                if item and text in item.text().lower():
                    match = True
                    break
            self.customer_table.setRowHidden(row, not match)

    def on_customer_search_text_changed(self, _text: str):
        # Restart debounce timer
        if self.search_timer.isActive():
            self.search_timer.stop()
        self.search_timer.start()
