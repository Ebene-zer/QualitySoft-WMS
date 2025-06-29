from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QLabel, QListWidget, QPushButton, QMessageBox, QComboBox, QCompleter
)
from PyQt6.QtGui import QPainter, QFont
from PyQt6.QtPrintSupport import QPrinter, QPrintPreviewDialog
from PyQt6.QtCore import Qt, QObject, QEvent
from models.invoice import Invoice


class SelectAllOnFocus(QObject):
    def eventFilter(self, obj, event):
        if event.type() == QEvent.Type.FocusIn:
            obj.selectAll()
        return False


class ReceiptView(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("View Receipt")
        self.setStyleSheet(self.get_stylesheet())
        self.layout = QVBoxLayout()

        focus_filter = SelectAllOnFocus()

        # Invoice Dropdown
        self.invoice_dropdown = QComboBox()
        self.invoice_dropdown.setEditable(True)
        self.invoice_completer = QCompleter()
        self.invoice_completer.setCaseSensitivity(Qt.CaseSensitivity.CaseInsensitive)
        self.invoice_dropdown.setCompleter(self.invoice_completer)
        self.invoice_dropdown.lineEdit().installEventFilter(focus_filter)
        self.layout.addWidget(QLabel("Select Invoice:"))
        self.layout.addWidget(self.invoice_dropdown)

        # Show button
        self.show_receipt_button = QPushButton("📑 Load Receipt")
        self.show_receipt_button.clicked.connect(self.show_receipt)
        self.layout.addWidget(self.show_receipt_button)

        # Receipt List
        self.receipt_list = QListWidget()
        self.layout.addWidget(self.receipt_list)

        # Export to PDF button
        self.export_pdf_button = QPushButton("📄 Export to PDF")
        self.export_pdf_button.clicked.connect(self.export_to_pdf)
        self.layout.addWidget(self.export_pdf_button)

        # Print button
        self.print_button = QPushButton("🖨️ Print Receipt")
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
            background-color: #3498db;
            color: white;
            border: none;
            border-radius: 6px;
            padding: 8px 16px;
            margin-top: 8px;
        }
        QPushButton:hover {
            background-color: #2980b9;
        }
        QListWidget {
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
        invoice_strs = [f"{inv['invoice_id']} - {inv['customer_name']} - GHS {inv['total_amount']:.2f}" for inv in invoices]
        self.invoice_dropdown.addItems(invoice_strs)
        self.invoice_completer.setModel(self.invoice_dropdown.model())

    def show_receipt(self):
        if self.invoice_dropdown.currentIndex() == -1:
            QMessageBox.warning(self, "Input Error", "Select an invoice first.")
            return

        invoice_text = self.invoice_dropdown.currentText()
        invoice_id = int(invoice_text.split(" - ")[0])
        invoice = Invoice.get_invoice_by_id(invoice_id)

        if not invoice:
            QMessageBox.warning(self, "Load Error", "Invoice not found.")
            return

        self.receipt_list.clear()

        # Header
        self.receipt_list.addItem(f"Invoice ID: {invoice['invoice_id']}")
        self.receipt_list.addItem(f"Date: {invoice['invoice_date']}")
        self.receipt_list.addItem(f"Customer: {invoice['customer_name']}")
        self.receipt_list.addItem(f"Discount: GHS {invoice['discount']:.2f}")
        self.receipt_list.addItem(f"Tax: GHS {invoice['tax']:.2f}")
        self.receipt_list.addItem(f"Total: GHS {invoice['total_amount']:.2f}")
        self.receipt_list.addItem("")

        # Items
        for item in invoice["items"]:
            line = f"{item['product_name']} x {item['quantity']} @ GHS {item['unit_price']:.2f}"
            self.receipt_list.addItem(line)

    def export_to_pdf(self):
        if self.receipt_list.count() == 0:
            QMessageBox.warning(self, "Export Error", "Please load a receipt first.")
            return

        printer = QPrinter(QPrinter.PrinterMode.HighResolution)
        printer.setOutputFormat(QPrinter.OutputFormat.PdfFormat)
        invoice_text = self.invoice_dropdown.currentText()
        invoice_id = invoice_text.split(" - ")[0]
        printer.setOutputFileName(f"receipt_{invoice_id}.pdf")

        painter = QPainter(printer)
        painter.setFont(QFont("Arial", 11))
        margin = 50
        y = margin

        painter.setFont(QFont("Arial", 14, QFont.Weight.Bold))
        painter.drawText(margin, y, "Wholesale Management System Receipt")
        y += 30
        painter.setFont(QFont("Arial", 11))
        painter.drawText(margin, y, f"Invoice: {invoice_text}")
        y += 25
        painter.drawLine(margin, y, printer.pageRect().width() - margin, y)
        y += 20

        for i in range(self.receipt_list.count()):
            line_text = self.receipt_list.item(i).text()
            painter.drawText(margin, y, line_text)
            y += 20
            if y > printer.pageRect().height() - margin:
                printer.newPage()
                y = margin

        painter.end()
        QMessageBox.information(self, "Export Complete", f"Receipt saved as receipt_{invoice_id}.pdf")

    def print_receipt(self):
        if self.receipt_list.count() == 0:
            QMessageBox.warning(self, "Print Error", "Please load a receipt first.")
            return

        printer = QPrinter(QPrinter.PrinterMode.HighResolution)
        preview = QPrintPreviewDialog(printer)
        preview.paintRequested.connect(self.handle_paint_request)
        preview.exec()

    def handle_paint_request(self, printer):
        painter = QPainter(printer)
        painter.setFont(QFont("Arial", 11))
        margin = 50
        y = margin

        painter.setFont(QFont("Arial", 14, QFont.Weight.Bold))
        painter.drawText(margin, y, "Wholesale Management System Receipt")
        y += 30
        painter.setFont(QFont("Arial", 11))
        invoice_text = self.invoice_dropdown.currentText()
        painter.drawText(margin, y, f"Invoice: {invoice_text}")
        y += 25
        painter.drawLine(margin, y, printer.pageRect().width() - margin, y)
        y += 20

        for i in range(self.receipt_list.count()):
            line_text = self.receipt_list.item(i).text()
            painter.drawText(margin, y, line_text)
            y += 20
            if y > printer.pageRect().height() - margin:
                printer.newPage()
                y = margin

        painter.end()
