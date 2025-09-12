import tempfile
import webbrowser
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QLabel, QTableWidget, QTableWidgetItem,
    QPushButton, QMessageBox, QComboBox, QCompleter, QFileDialog
)

from PyQt6.QtCore import Qt, QObject, QEvent


from models.invoice import Invoice
from database.db_handler import get_db_connection


try:
    from PyQt6.QtPdfWidgets import QPdfView
    from PyQt6.QtPdf import QPdfDocument
    HAS_QPDFVIEW = True
except ImportError:
    HAS_QPDFVIEW = False
class SelectAllOnFocus(QObject):
    def eventFilter(self, obj, event):
        if event.type() == QEvent.Type.FocusIn:
            obj.selectAll()
        return False

class ReceiptView(QWidget):
    def __init__(self):
        super().__init__()
        self.setStyleSheet(self.get_stylesheet())
        self.layout = QVBoxLayout()

        focus_filter = SelectAllOnFocus()


        self.invoice_dropdown = QComboBox()
        self.invoice_dropdown.setEditable(True)
        self.invoice_completer = QCompleter()
        self.invoice_completer.setCaseSensitivity(Qt.CaseSensitivity.CaseInsensitive)
        self.invoice_dropdown.setCompleter(self.invoice_completer)
        self.invoice_dropdown.lineEdit().installEventFilter(focus_filter)
        self.invoice_dropdown.lineEdit().returnPressed.connect(self.show_receipt)
        self.layout.addWidget(QLabel("Select Invoice:"))
        self.layout.addWidget(self.invoice_dropdown)


        self.show_receipt_button = QPushButton("Load Invoice")
        self.show_receipt_button.clicked.connect(self.show_receipt)
        self.layout.addWidget(self.show_receipt_button)

        self.receipt_table = QTableWidget()
        self.receipt_table.setColumnCount(4)
        self.receipt_table.setHorizontalHeaderLabels(["Product", "Qty", "Unit Price", "Total"])
        self.layout.addWidget(self.receipt_table)

        self.export_pdf_button = QPushButton("Export to PDF")
        self.export_pdf_button.clicked.connect(self.export_to_pdf)
        self.layout.addWidget(self.export_pdf_button)

        self.print_button = QPushButton("Print Receipt")
        self.print_button.clicked.connect(self.print_receipt)
        self.layout.addWidget(self.print_button)

        self.setLayout(self.layout)
        self.load_invoices()

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
            margin: 6px 0;
        }
        QComboBox {
            background-color: white;
            border: 1px solid #ccc;
            border-radius: 6px;
            padding: 7px;
        }
        QComboBox:focus {
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
        QTableWidget {
            background-color: white;
            border: 1px solid #ccc;
            border-radius: 6px;
            padding: 6px;
            max-height: 220px;
        }
        """

    def load_invoices(self):
        self.invoice_dropdown.clear()
        invoices = Invoice.get_all_invoices()
        # Show newly created invoices at the top
        invoices = sorted(invoices, key=lambda inv: getattr(inv, 'invoice_id', 0), reverse=True)
        invoice_strs = [f"{inv.invoice_id} - {inv.customer_name} - GH¢ {inv.total_amount:,.2f}" for inv in invoices]
        self.invoice_dropdown.addItems(invoice_strs)
        self.invoice_completer.setModel(self.invoice_dropdown.model())

    def get_wholesale_number(self):
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute("SELECT wholesale_number FROM settings WHERE id=1")
        result = cur.fetchone()
        conn.close()
        return result[0] if result and result[0] else "N/A"

    def show_receipt(self):
        self.receipt_table.setRowCount(0)
        if self.invoice_dropdown.currentIndex() == -1:
            QMessageBox.warning(self, "Input Error", "Select an invoice first.")
            return

        invoice_text = self.invoice_dropdown.currentText()
        invoice_id = int(invoice_text.split(" - ")[0])
        invoice = Invoice.get_invoice_by_id(invoice_id)
        if not invoice:
            QMessageBox.warning(self, "Load Error", "Invoice not found.")
            return

        wholesale_number = self.get_wholesale_number()
        formatted = Invoice.format_receipt_data(invoice, wholesale_number)

        # Remove previous details if any
        if hasattr(self, 'details_label'):
            self.layout.removeWidget(self.details_label)
            self.details_label.deleteLater()
        self.details_label = QLabel(f"Customer Number: {formatted['customer_number']} | {formatted['wholesale_contact']} | Total Items: {formatted['total_items']}")
        self.layout.insertWidget(3, self.details_label)

        for item in formatted["items"]:
            row = self.receipt_table.rowCount()
            self.receipt_table.insertRow(row)
            item_product = QTableWidgetItem(item[0])
            item_product.setFlags(Qt.ItemFlag.ItemIsSelectable | Qt.ItemFlag.ItemIsEnabled)
            self.receipt_table.setItem(row, 0, item_product)
            item_qty = QTableWidgetItem(item[1])
            item_qty.setFlags(Qt.ItemFlag.ItemIsSelectable | Qt.ItemFlag.ItemIsEnabled)
            self.receipt_table.setItem(row, 1, item_qty)
            item_price = QTableWidgetItem(f"GH¢ {item[2]}")
            item_price.setFlags(Qt.ItemFlag.ItemIsSelectable | Qt.ItemFlag.ItemIsEnabled)
            self.receipt_table.setItem(row, 2, item_price)
            item_total = QTableWidgetItem(f"GH¢ {item[3]}")
            item_total.setFlags(Qt.ItemFlag.ItemIsSelectable | Qt.ItemFlag.ItemIsEnabled)
            self.receipt_table.setItem(row, 3, item_total)

    def export_to_pdf(self):
        if self.invoice_dropdown.currentIndex() == -1:
            QMessageBox.warning(self, "Export Error", "Please load an invoice first.")
            return
        invoice_text = self.invoice_dropdown.currentText()
        invoice_id = int(invoice_text.split(" - ")[0])
        default_filename = f"receipt_{invoice_id}.pdf"
        file_path, _ = QFileDialog.getSaveFileName(self, "Save Invoice as PDF", default_filename, "PDF Files (*.pdf)")
        if not file_path:
            return
        invoice = Invoice.get_invoice_by_id(invoice_id)
        if not invoice:
            QMessageBox.warning(self, "Export Error", "Invoice not found.")
            return
        wholesale_number = self.get_wholesale_number()
        formatted = Invoice.format_receipt_data(invoice, wholesale_number)
        Invoice.export_receipt_to_pdf(formatted, file_path)
        QMessageBox.information(self, "Export Complete", f"Receipt saved to {file_path}")

    def print_receipt(self):
        if self.invoice_dropdown.currentIndex() == -1:
            QMessageBox.warning(self, "Print Error", "Please load a receipt first.")
            return
        invoice_text = self.invoice_dropdown.currentText()
        invoice_id = int(invoice_text.split(" - ")[0])
        invoice = Invoice.get_invoice_by_id(invoice_id)
        if not invoice:
            QMessageBox.warning(self, "Print Error", "Invoice not found.")
            return
        wholesale_number = self.get_wholesale_number()
        formatted = Invoice.format_receipt_data(invoice, wholesale_number)
        with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp:
            tmp_path = tmp.name
        Invoice.export_receipt_to_pdf(formatted, tmp_path)
        webbrowser.open(tmp_path)
