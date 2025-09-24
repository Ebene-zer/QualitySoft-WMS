import tempfile
import webbrowser

from PyQt6.QtCore import QEvent, QObject, Qt
from PyQt6.QtWidgets import (
    QComboBox,
    QCompleter,
    QFileDialog,
    QHeaderView,
    QLabel,
    QMessageBox,
    QPushButton,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)

from database.db_handler import get_db_connection
from models.invoice import Invoice
from utils.ui_common import format_money

try:
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
        # Set once to avoid resetting on every reload
        self.invoice_completer.setFilterMode(Qt.MatchFlag.MatchContains)
        self.invoice_completer.setCompletionMode(QCompleter.CompletionMode.PopupCompletion)
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
        # Set header resize behavior once
        self.receipt_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)

        self.print_button = QPushButton("Print Receipt")
        self.print_button.clicked.connect(self.print_receipt)
        self.layout.addWidget(self.print_button)

        self.export_pdf_button = QPushButton("Export to PDF")
        self.export_pdf_button.clicked.connect(self.export_to_pdf)
        self.layout.addWidget(self.export_pdf_button)

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
        dd = self.invoice_dropdown
        dd.blockSignals(True)
        dd.setUpdatesEnabled(False)
        try:
            dd.clear()
            invoices = Invoice.get_all_invoices()
            # Show newly created invoices at the top
            invoices = sorted(invoices, key=lambda inv: getattr(inv, "invoice_id", 0), reverse=True)
            invoice_strs = [
                f"{inv.invoice_id} - {inv.customer_name} - {format_money(inv.total_amount)}" for inv in invoices
            ]
            if invoice_strs:
                dd.addItems(invoice_strs)
            # Keep completer bound to dropdown model
            self.invoice_completer.setModel(dd.model())
        finally:
            dd.blockSignals(False)
            dd.setUpdatesEnabled(True)

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
        if hasattr(self, "details_label"):
            self.layout.removeWidget(self.details_label)
            self.details_label.deleteLater()
        # Use rich text so the description (label) and actual data have different font styles
        details_html = (
            f"<span style='font-weight:700; color:#222;'>Customer Name:</span> "
            f"<span style='font-family:Segoe UI; font-size:13px; color:#333;'>{formatted['customer_name']}</span>"
            f" &nbsp;|&nbsp; <span style='font-weight:700; color:#222;'>Number:</span> "
            f"<span style='font-family:Segoe UI; font-size:13px; color:#333;'>{formatted['customer_number']}</span>"
            f" &nbsp;|&nbsp; <span style='font-weight:700; color:#222;'>Total:</span> "
            f"<span style='font-family:Segoe UI; font-size:13px; color:#333;'>GH¢ {formatted['total']}</span>"
        )
        self.details_label = QLabel(details_html)
        # Use Qt enum for text format
        self.details_label.setTextFormat(Qt.TextFormat.RichText)
        self.layout.insertWidget(3, self.details_label)

        # Efficiently populate table
        tbl = self.receipt_table
        tbl.setUpdatesEnabled(False)
        tbl.blockSignals(True)
        items = formatted["items"]
        tbl.setRowCount(len(items))
        for row, item in enumerate(items):
            prod = QTableWidgetItem(item[0])
            prod.setFlags(Qt.ItemFlag.ItemIsSelectable | Qt.ItemFlag.ItemIsEnabled)
            tbl.setItem(row, 0, prod)
            qty = QTableWidgetItem(item[1])
            qty.setFlags(Qt.ItemFlag.ItemIsSelectable | Qt.ItemFlag.ItemIsEnabled)
            tbl.setItem(row, 1, qty)
            price = QTableWidgetItem(format_money(item[2]))
            price.setFlags(Qt.ItemFlag.ItemIsSelectable | Qt.ItemFlag.ItemIsEnabled)
            tbl.setItem(row, 2, price)
            total = QTableWidgetItem(format_money(item[3]))
            total.setFlags(Qt.ItemFlag.ItemIsSelectable | Qt.ItemFlag.ItemIsEnabled)
            tbl.setItem(row, 3, total)
        tbl.blockSignals(False)
        tbl.setUpdatesEnabled(True)

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
