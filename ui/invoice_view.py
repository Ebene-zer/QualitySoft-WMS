from PyQt6.QtCore import QEvent, QObject, Qt, pyqtSignal
from PyQt6.QtGui import QDoubleValidator, QIntValidator
from PyQt6.QtWidgets import (
    QComboBox,
    QCompleter,
    QHBoxLayout,
    QHeaderView,
    QLabel,
    QLineEdit,
    QMessageBox,
    QPushButton,
    QSizePolicy,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)

from models.customer import Customer
from models.invoice import Invoice
from models.product import Product
from utils.activity_log import log_action
from utils.session import get_current_username
from utils.ui_common import format_money, format_money_value


class SelectAllOnFocus(QObject):
    def eventFilter(self, obj, event):
        if event.type() == QEvent.Type.FocusIn:
            obj.selectAll()
        return False


class InvoiceView(QWidget):
    invoice_created = pyqtSignal()

    def __init__(self):
        super().__init__()
        self.setStyleSheet(self.get_stylesheet())
        self.layout = QVBoxLayout()

        focus_filter = SelectAllOnFocus()

        # Customer Dropdown
        self.customer_dropdown = QComboBox()
        self.customer_dropdown.setEditable(True)
        self.customer_completer = QCompleter()
        self.customer_completer.setCaseSensitivity(Qt.CaseSensitivity.CaseInsensitive)
        self.customer_completer.setFilterMode(Qt.MatchFlag.MatchContains)
        self.customer_completer.setCompletionMode(QCompleter.CompletionMode.PopupCompletion)
        self.customer_dropdown.setCompleter(self.customer_completer)
        self.customer_dropdown.lineEdit().installEventFilter(focus_filter)
        self.customer_dropdown.currentIndexChanged.connect(self._select_all_customer)

        # Product Dropdown
        self.product_dropdown = QComboBox()
        self.product_dropdown.setEditable(True)
        self.product_completer = QCompleter()
        self.product_completer.setCaseSensitivity(Qt.CaseSensitivity.CaseInsensitive)
        self.product_completer.setFilterMode(Qt.MatchFlag.MatchContains)
        self.product_completer.setCompletionMode(QCompleter.CompletionMode.PopupCompletion)
        self.product_dropdown.setCompleter(self.product_completer)
        self.product_dropdown.lineEdit().installEventFilter(focus_filter)
        self.product_dropdown.currentIndexChanged.connect(self._select_all_product)
        # Equal halves: let it expand within its half
        self.product_dropdown.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        # Optional: avoid over-expanding
        # self.product_dropdown.setMaximumWidth(600)

        # Quantity Input
        self.quantity_input = QLineEdit()
        self.quantity_input.setPlaceholderText("Quantity")
        # Only positive integers for quantity
        self.quantity_input.setValidator(QIntValidator(1, 1_000_000_000, self))
        # Equal halves: let it expand within its half
        self.quantity_input.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        # Enter key support
        self.quantity_input.returnPressed.connect(self.add_item_to_invoice)

        # --- Layout: Row 1 (Customer), Row 2 (Product | Quantity) ---
        # Row 1: Customer label + dropdown (stacked vertically)
        row1 = QVBoxLayout()
        row1.addWidget(QLabel("Select Customer:"))
        row1.addWidget(self.customer_dropdown)
        self.layout.addLayout(row1)

        # Row 2: Left = Product (label + dropdown), Right = Quantity input
        row2 = QHBoxLayout()
        row2.setSpacing(16)  # base spacing
        left_col = QVBoxLayout()
        prod_label = QLabel("Select Product:")
        left_col.addWidget(prod_label)
        left_col.addWidget(self.product_dropdown)
        right_col = QVBoxLayout()
        # Add vertical spacing equal to the product label height so the quantity
        # field aligns horizontally with the product dropdown
        try:
            right_col.addSpacing(prod_label.sizeHint().height() + 6)
        except Exception:
            right_col.addSpacing(20)
        right_col.addWidget(self.quantity_input)
        # Equal halves: no asymmetric margins and equal stretch
        right_col.setContentsMargins(0, 0, 0, 0)
        row2.addLayout(left_col, 1)
        row2.addLayout(right_col, 1)
        self.layout.addLayout(row2)

        # Add Item, Update, and Delete Buttons
        button_layout = QHBoxLayout()
        add_item_button = QPushButton("Add to Invoice")
        add_item_button.clicked.connect(self.add_item_to_invoice)
        button_layout.addWidget(add_item_button)
        update_item_button = QPushButton("Update Selected")
        update_item_button.clicked.connect(self.update_selected_item)
        button_layout.addWidget(update_item_button)
        delete_item_button = QPushButton("Delete Selected")
        delete_item_button.clicked.connect(self.delete_selected_item)
        button_layout.addWidget(delete_item_button)
        self.layout.addLayout(button_layout)

        # Invoice Items Table
        self.invoice_items_table = QTableWidget()
        self.invoice_items_table.setColumnCount(4)
        self.invoice_items_table.setHorizontalHeaderLabels(["Product", "Quantity", "Unit Price (GH¢)", "Total (GH¢)"])
        self.invoice_items_table.setSelectionBehavior(self.invoice_items_table.SelectionBehavior.SelectRows)
        self.invoice_items_table.setEditTriggers(self.invoice_items_table.EditTrigger.NoEditTriggers)
        self.invoice_items_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.invoice_items_table.itemSelectionChanged.connect(self.populate_fields_from_selection)
        self.layout.addWidget(self.invoice_items_table)

        # Discount and Tax Inputs
        self.discount_input = QLineEdit()
        self.discount_input.setPlaceholderText("Discount (GH¢)")
        # Currency: non-negative with up to 2 decimals
        discount_validator = QDoubleValidator(0.0, 1_000_000_000.0, 2, self)
        discount_validator.setNotation(QDoubleValidator.Notation.StandardNotation)
        self.discount_input.setValidator(discount_validator)
        self.discount_input.textChanged.connect(self.handle_discount_input)

        self.tax_input = QLineEdit()
        self.tax_input.setPlaceholderText("Tax (GH¢)")
        tax_validator = QDoubleValidator(0.0, 1_000_000_000.0, 2, self)
        tax_validator.setNotation(QDoubleValidator.Notation.StandardNotation)
        self.tax_input.setValidator(tax_validator)
        self.tax_input.textChanged.connect(self.handle_tax_input)

        # Revert: place Discount and Tax on separate rows
        self.layout.addWidget(self.discount_input)
        self.layout.addWidget(self.tax_input)

        # Total Label
        self.total_label = QLabel()
        # Use rich text so label and amount have distinct styles
        self.total_label.setTextFormat(Qt.TextFormat.RichText)
        self.total_label.setText(
            f"<b>Total:</b> <span style='font-family:Segoe UI; font-size:14px;'>{format_money(0)}</span>"
        )
        self.layout.addWidget(self.total_label)

        # Save Invoice Button
        save_invoice_button = QPushButton("Save Invoice")
        save_invoice_button.clicked.connect(self.save_invoice)
        self.layout.addWidget(save_invoice_button)

        self.setLayout(self.layout)

        self.items = []
        self.load_customers()
        self.load_products()
        self.load_invoice_items_table()

    def get_stylesheet(self):
        return """
        QWidget {
            background-color: #f0f2f5;
            font-family: 'Segoe UI', sans-serif;
            font-size: 14px;
            color: #333;
        }
        QLabel {
            font-weight: 600;
            margin: 4px 0;
        }
        QLineEdit, QComboBox {
            background-color: white;
            border: 1px solid #ccc;
            border-radius: 6px;
            padding: 7px;
        }
        QLineEdit:focus, QComboBox:focus {
            border: 2px solid #3498db;
        }
        QPushButton {
            background-color: #21618C;
            color: white;
            border: none;
            border-radius: 6px;
            padding: 8px 16px;
            margin-top: 8px;
        }
        QPushButton:hover {
            background-color: #3498db;
        }
        QListWidget {
            background-color: white;
            border: 1px solid #ccc;
            border-radius: 6px;
            padding: 6px;
            max-height: 140px;
        }
        QTableWidget {
            background-color: white; /* match ReceiptView */
            border: 1px solid #ccc;
            border-radius: 6px;
            padding: 6px;
            max-height: 220px; /* slightly constrained like ReceiptView */
        }
        /* Make table header text bold black without background color */
        QHeaderView::section {
            font-weight: 700;
            color: #000000;
            padding: 6px 8px;
        }
        """

    def load_customers(self):
        # Bulk refresh without extra signals/repains
        dd = self.customer_dropdown
        dd.blockSignals(True)
        dd.setUpdatesEnabled(False)
        try:
            dd.clear()
            customers = Customer.get_all_customers()
            names = [f"{c.name} - {c.phone_number}" for c in customers]
            if names:
                dd.addItems(names)
            # Keep completer bound to the same model; no need to reset filter/completion modes
            self.customer_completer.setModel(dd.model())
        finally:
            dd.blockSignals(False)
            dd.setUpdatesEnabled(True)

    def load_products(self):
        dd = self.product_dropdown
        dd.blockSignals(True)
        dd.setUpdatesEnabled(False)
        try:
            dd.clear()
            products = Product.get_all_products()
            names = [f"{p.product_id} - {p.name} ({format_money(p.price)})" for p in products]
            if names:
                dd.addItems(names)
            self.product_completer.setModel(dd.model())
        finally:
            dd.blockSignals(False)
            dd.setUpdatesEnabled(True)

    def load_invoice_items_table(self):
        tbl = self.invoice_items_table
        prev_sorting = tbl.isSortingEnabled()
        # Reduce UI work during bulk load
        tbl.setSortingEnabled(False)
        tbl.setUpdatesEnabled(False)
        tbl.blockSignals(True)

        tbl.setRowCount(len(self.items))
        for row_idx, item in enumerate(self.items):
            tbl.setItem(row_idx, 0, QTableWidgetItem(item["product_name"]))
            tbl.setItem(row_idx, 1, QTableWidgetItem(str(item["quantity"])))
            tbl.setItem(row_idx, 2, QTableWidgetItem(format_money_value(item["unit_price"])))
            tbl.setItem(row_idx, 3, QTableWidgetItem(format_money_value(item["quantity"] * item["unit_price"])))

        # Restore UI updates and signals
        tbl.blockSignals(False)
        tbl.setUpdatesEnabled(True)
        tbl.setSortingEnabled(prev_sorting)

    # Helpers for incremental updates (avoid full reloads)
    def _find_row_by_product_name(self, product_name: str) -> int:
        for row in range(self.invoice_items_table.rowCount()):
            it = self.invoice_items_table.item(row, 0)
            if it and it.text() == product_name:
                return row
        return -1

    def _append_invoice_row(self, product_name: str, quantity: int, unit_price: float):
        row = self.invoice_items_table.rowCount()
        self.invoice_items_table.setRowCount(row + 1)
        self.invoice_items_table.setItem(row, 0, QTableWidgetItem(product_name))
        self.invoice_items_table.setItem(row, 1, QTableWidgetItem(str(quantity)))
        self.invoice_items_table.setItem(row, 2, QTableWidgetItem(format_money_value(unit_price)))
        self.invoice_items_table.setItem(row, 3, QTableWidgetItem(format_money_value(quantity * unit_price)))

    def _set_invoice_row(self, row: int, quantity: int, unit_price: float):
        self.invoice_items_table.setItem(row, 1, QTableWidgetItem(str(quantity)))
        self.invoice_items_table.setItem(row, 2, QTableWidgetItem(format_money_value(unit_price)))
        self.invoice_items_table.setItem(row, 3, QTableWidgetItem(format_money_value(quantity * unit_price)))

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

        # Consider quantities already added to the current invoice for this product
        existing_qty = sum(it["quantity"] for it in self.items if it["product_id"] == product_id)
        if existing_qty + quantity > product.stock_quantity:
            QMessageBox.warning(
                self,
                "Low Stock",
                f"Only {product.stock_quantity - existing_qty} additional units available "
                f"(already added: {existing_qty}).",
            )
            return

        # If product already in invoice items, merge quantities instead of adding duplicate rows
        merged = False
        for it in self.items:
            if it["product_id"] == product_id:
                it["quantity"] += quantity
                merged = True
                break

        if not merged:
            self.items.append(
                {
                    "product_id": product.product_id,
                    "quantity": quantity,
                    "unit_price": product.price,
                    "product_name": product.name,  # Store product name for display
                }
            )
            # Incremental UI update: append a row
            self._append_invoice_row(product.name, quantity, product.price)
        else:
            # Incremental UI update: update existing row for this product
            row = self._find_row_by_product_name(product.name)
            if row != -1:
                new_qty = existing_qty + quantity
                self._set_invoice_row(row, new_qty, product.price)
            else:
                # Fallback if not found
                self.load_invoice_items_table()

        self.update_total()
        self.quantity_input.clear()

    def update_selected_item(self):
        selected = self.invoice_items_table.currentRow()
        if selected == -1:
            QMessageBox.warning(self, "Select Item", "Please select an item to update.")
            return
        try:
            quantity = int(self.quantity_input.text())
        except ValueError:
            QMessageBox.warning(self, "Input Error", "Enter a valid quantity.")
            return
        product_name = self.invoice_items_table.item(selected, 0).text()
        # Find the item to update
        target = None
        for item in self.items:
            if item["product_name"] == product_name:
                target = item
                break
        if not target:
            QMessageBox.warning(self, "Error", "Selected item not found in invoice items.")
            return

        product = Product.get_product_by_id(target["product_id"])
        if product is None:
            QMessageBox.warning(self, "Error", "Product not found.")
            return

        # Compute quantity reserved by other lines for same product
        other_reserved = sum(
            it["quantity"] for it in self.items if it["product_id"] == target["product_id"] and it is not target
        )
        if other_reserved + quantity > product.stock_quantity:
            QMessageBox.warning(
                self,
                "Low Stock",
                f"Only {product.stock_quantity - other_reserved} units available for this product "
                f"(others reserved: {other_reserved}).",
            )
            return

        target["quantity"] = quantity
        # Incremental UI update: set values in the selected row
        self._set_invoice_row(selected, quantity, target["unit_price"])
        self.update_total()
        self.quantity_input.clear()

    def delete_selected_item(self):
        selected = self.invoice_items_table.currentRow()
        if selected == -1:
            QMessageBox.warning(self, "Select Item", "Please select an item to delete.")
            return
        product_name = self.invoice_items_table.item(selected, 0).text()
        self.items = [item for item in self.items if item["product_name"] != product_name]
        # Incremental UI update: remove the selected row
        self.invoice_items_table.removeRow(selected)
        self.update_total()
        self.quantity_input.clear()

    def update_total(self):
        subtotal = sum(item["quantity"] * item["unit_price"] for item in self.items)
        try:
            discount = float(self.discount_input.text() or 0)
        except ValueError:
            discount = 0.0
        try:
            tax = float(self.tax_input.text() or 0)
        except ValueError:
            tax = 0.0
        total = subtotal - discount + tax
        # Update using rich-text so description and value have different styles
        self.total_label.setText(
            f"<b>Total:</b> <span style='font-family:Segoe UI; font-size:14px;'>{format_money(total)}</span>"
        )

    def save_invoice(self):
        if not self.items:
            QMessageBox.warning(self, "Input Error", "Add at least one item.")
            return

        customer_text = self.customer_dropdown.currentText()
        if not customer_text:
            QMessageBox.warning(self, "Input Error", "Select a customer.")
            return

        # The dropdown shows customers as "Name - phone_number". Match against that
        # composite string first, then fall back to name-only or fuzzy matches to
        # handle user-typed input.
        customers = Customer.get_all_customers()
        customer = None
        # Exact composite match: "Name - phone"
        for c in customers:
            composite = f"{c.name} - {c.phone_number}"
            if composite == customer_text:
                customer = c
                break

        # If no exact composite match, try name-only (user may have selected/typed just the name)
        if not customer:
            name_part = customer_text.split(" - ")[0].strip()
            for c in customers:
                if c.name == name_part:
                    customer = c
                    break

        # As a last resort, try a case-insensitive contains match against the composite
        if not customer:
            ct_lower = customer_text.lower()
            for c in customers:
                composite = f"{c.name} - {c.phone_number}"
                if ct_lower in composite.lower():
                    customer = c
                    break

        if not customer:
            QMessageBox.warning(self, "Input Error", "Selected customer not found.")
            return
        customer_id = customer.customer_id
        try:
            discount = float(self.discount_input.text() or 0)
        except ValueError:
            QMessageBox.warning(self, "Input Error", "Enter a valid discount value.")
            return
        try:
            tax = float(self.tax_input.text() or 0)
        except ValueError:
            QMessageBox.warning(self, "Input Error", "Enter a valid tax value.")
            return
        try:
            invoice_id = Invoice.create_invoice(customer_id, self.items, discount, tax)
        except ValueError as e:
            # Model-level validation (e.g., insufficient stock) failed
            QMessageBox.warning(self, "Save Error", str(e))
            return
        except Exception as e:
            QMessageBox.critical(self, "Error", f"An unexpected error occurred while saving the invoice:\n{e}")
            return

        QMessageBox.information(self, "Success", f"Invoice #{invoice_id} created.")
        try:
            total_val = sum(it["quantity"] * it["unit_price"] for it in self.items)
            log_action(
                get_current_username(),
                "INVOICE_CREATE",
                f"invoice_id={invoice_id} total={total_val:.2f} items={len(self.items)}",
            )
        except Exception:
            pass
        self.reset_invoice_form()
        self.invoice_created.emit()

    def reset_invoice_form(self):
        self.invoice_items_table.setRowCount(0)
        self.discount_input.clear()
        self.tax_input.clear()
        self.total_label.setText(
            f"<b>Total:</b> <span style='font-family:Segoe UI; font-size:14px;'>{format_money(0)}</span>"
        )
        self.items = []
        self.load_products()
        self.load_customers()
        self.load_invoice_items_table()

    def populate_fields_from_selection(self):
        selected = self.invoice_items_table.currentRow()
        if selected == -1:
            self.product_dropdown.setCurrentIndex(0)
            self.quantity_input.clear()
            return
        product_name = self.invoice_items_table.item(selected, 0).text()
        quantity = self.invoice_items_table.item(selected, 1).text()
        # Set product dropdown to match, but do not overwrite text
        self.product_dropdown.setCurrentText(product_name)
        self.product_dropdown.lineEdit().selectAll()
        self.quantity_input.setText(quantity)

    def _select_all_customer(self):
        # Only select all if there is a value, and do not set text (prevents clearing)
        if self.customer_dropdown.currentText():
            self.customer_dropdown.lineEdit().selectAll()

    def _select_all_product(self):
        # Only select all if there is a value, and do not set a text (prevents clearing)
        if self.product_dropdown.currentText():
            self.product_dropdown.lineEdit().selectAll()

    def handle_discount_input(self):
        text = self.discount_input.text()
        try:
            float(text) if text else 0.0
            self.discount_input.setStyleSheet("")
        except ValueError:
            self.discount_input.setStyleSheet("background-color: #ffcccc;")

    def handle_tax_input(self):
        text = self.tax_input.text()
        try:
            float(text) if text else 0.0
            self.tax_input.setStyleSheet("")
        except ValueError:
            self.tax_input.setStyleSheet("background-color: #ffcccc;")
