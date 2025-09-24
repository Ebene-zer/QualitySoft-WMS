from PyQt6.QtGui import QDoubleValidator, QIntValidator
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

from models.product import Product
from utils.app_settings import get_low_stock_threshold
from utils.session import get_low_stock_alert_shown, set_low_stock_alert_shown
from utils.ui_common import (
    SEARCH_PLACEHOLDER_PRODUCTS,
    SEARCH_TOOLTIP_PRODUCTS,
    create_top_actions_row,
)


# Product View Class
class ProductView(QWidget):
    def __init__(self, on_low_stock_status_changed=None):
        super().__init__()
        self._on_low_stock_status_changed = on_low_stock_status_changed
        # Tab style
        self.setStyleSheet(self.get_stylesheet())

        self.layout = QVBoxLayout()  # Set Layout

        # Input fields in a single row
        inputs_row = QHBoxLayout()
        inputs_row.setSpacing(10)

        self.name_input = QLineEdit()
        self.name_input.setPlaceholderText("Product Name")
        # Let name stretch to occupy remaining space
        self.name_input.setMinimumWidth(240)
        inputs_row.addWidget(self.name_input, 1)

        self.price_input = QLineEdit()
        self.price_input.setPlaceholderText("Price")
        # Allow only positive currency values with up to 2 decimals
        price_validator = QDoubleValidator(0.0, 1_000_000_000.0, 2, self)
        price_validator.setNotation(QDoubleValidator.Notation.StandardNotation)
        self.price_input.setValidator(price_validator)
        # Reasonable width for price
        self.price_input.setFixedWidth(130)
        inputs_row.addWidget(self.price_input)

        self.stock_input = QLineEdit()
        self.stock_input.setPlaceholderText("Stock Quantity")
        # Allow only non-negative integers
        self.stock_input.setValidator(QIntValidator(0, 1_000_000_000, self))
        # Reasonable width for stock
        self.stock_input.setFixedWidth(150)
        inputs_row.addWidget(self.stock_input)

        # Enter key support
        self.stock_input.returnPressed.connect(self.add_product)

        self.layout.addLayout(inputs_row)

        # Add Product Button and Search (same row)
        # Reuse shared helper to build the top actions row with debounced search
        top_actions, self.search_input, self.search_timer, add_button = create_top_actions_row(
            self,
            "Add Product",
            self.add_product,
            SEARCH_PLACEHOLDER_PRODUCTS,
            SEARCH_TOOLTIP_PRODUCTS,
            lambda: self.filter_products(self.search_input.text()),
        )
        self.layout.addLayout(top_actions)

        # Product Table (replaces product_list)
        self.product_table = QTableWidget()
        self.product_table.setColumnCount(4)
        self.product_table.setHorizontalHeaderLabels(["ID", "Name", "Price (GH¢)", "Stock"])
        self.product_table.setSelectionBehavior(self.product_table.SelectionBehavior.SelectRows)
        self.product_table.setEditTriggers(self.product_table.EditTrigger.NoEditTriggers)
        # Set header resize behavior once to avoid repeated auto-resizes
        self.product_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
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
        # Initialize badge once per session on first load (no popup)
        self.update_low_stock_badge()

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
        tbl = self.product_table
        prev_sorting = tbl.isSortingEnabled()
        # Reduce UI work during bulk load
        tbl.setSortingEnabled(False)
        tbl.setUpdatesEnabled(False)
        tbl.blockSignals(True)

        products = Product.get_all_products()
        tbl.setRowCount(len(products))
        for row_idx, product in enumerate(products):
            tbl.setItem(row_idx, 0, QTableWidgetItem(str(product.product_id)))
            tbl.setItem(row_idx, 1, QTableWidgetItem(product.name))
            tbl.setItem(row_idx, 2, QTableWidgetItem(f"{product.price:,.2f}"))
            tbl.setItem(row_idx, 3, QTableWidgetItem(str(product.stock_quantity)))

        # Restore UI updates and signals
        tbl.blockSignals(False)
        tbl.setUpdatesEnabled(True)
        tbl.setSortingEnabled(prev_sorting)

        # Re-apply current filter (if any)
        self.filter_products(self.search_input.text())
        # Update badge after reload
        self.update_low_stock_badge()

    # Helpers for incremental updates
    def _find_product_row(self, product_id: int) -> int:
        for row in range(self.product_table.rowCount()):
            item = self.product_table.item(row, 0)
            if item and item.text() == str(product_id):
                return row
        return -1

    def _append_product_row(self, product_id: int, name: str, price: float, stock: int):
        row_idx = self.product_table.rowCount()
        self.product_table.setRowCount(row_idx + 1)
        self.product_table.setItem(row_idx, 0, QTableWidgetItem(str(product_id)))
        self.product_table.setItem(row_idx, 1, QTableWidgetItem(name))
        self.product_table.setItem(row_idx, 2, QTableWidgetItem(f"{price:,.2f}"))
        self.product_table.setItem(row_idx, 3, QTableWidgetItem(str(stock)))

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
        try:
            new_id = Product.add_product(name, price, stock)
        except ValueError as e:
            QMessageBox.warning(self, "Cannot Add Product", str(e))
            return
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to add product:\n{e}")
            return
        QMessageBox.information(self, "Success", "Product added.")
        # Incremental UI update
        self._append_product_row(new_id, name, price, stock)
        self.filter_products(self.search_input.text())
        self.clear_inputs()
        # Refresh badge instead of showing a popup
        self.update_low_stock_badge()

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
        try:
            Product.update_product(product_id, name, price, stock)
        except ValueError as e:
            QMessageBox.warning(self, "Cannot Update Product", str(e))
            return
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to update product:\n{e}")
            return
        QMessageBox.information(self, "Success", "Product updated.")
        # Incremental UI update
        self.product_table.setItem(selected, 1, QTableWidgetItem(name))
        self.product_table.setItem(selected, 2, QTableWidgetItem(f"{price:,.2f}"))
        self.product_table.setItem(selected, 3, QTableWidgetItem(str(stock)))
        self.filter_products(self.search_input.text())
        self.clear_inputs()
        # Refresh badge (no popup)
        self.update_low_stock_badge()

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
            try:
                Product.delete_product(product_id)
            except Exception as e:
                # Likely foreign key constraint (product referenced in invoices)
                QMessageBox.critical(
                    self,
                    "Delete Failed",
                    f"Could not delete product. It may be referenced by existing invoices.\n{e}",
                )
                return
            QMessageBox.information(self, "Success", "Product deleted.")
            # Incremental UI update
            self.product_table.removeRow(selected)
            self.clear_inputs()
            self.filter_products(self.search_input.text())
            # Refresh badge (no popup)
            self.update_low_stock_badge()

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
        price_text = self.product_table.item(selected, 2).text()
        try:
            # Strip thousands separators only; headers carry currency symbol
            price_numeric = price_text.replace(",", "").strip()
        except Exception:
            price_numeric = price_text
        self.price_input.setText(price_numeric)
        self.stock_input.setText(self.product_table.item(selected, 3).text())

    def update_low_stock_badge(self):
        """Compute low-stock count and notify parent via callback. Shows once per session initially."""
        try:
            threshold = get_low_stock_threshold()
            low_stock_products = Product.get_products_below_stock(threshold)
            count = len(low_stock_products)
            if callable(self._on_low_stock_status_changed):
                self._on_low_stock_status_changed(count)
            # Mark that we have handled the initial alert once per session
            if not get_low_stock_alert_shown():
                set_low_stock_alert_shown(True)
        except Exception:
            # Ignore errors to avoid blocking UI
            pass

    def filter_products(self, text: str):
        """Filter table rows by search text across all columns (case-insensitive)."""
        text = (text or "").strip().lower()
        for row in range(self.product_table.rowCount()):
            if not text:
                self.product_table.setRowHidden(row, False)
                continue
            # Check all visible columns
            match = False
            for col in range(self.product_table.columnCount()):
                item = self.product_table.item(row, col)
                if item and text in item.text().lower():
                    match = True
                    break
            self.product_table.setRowHidden(row, not match)
