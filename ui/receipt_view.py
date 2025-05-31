from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QPushButton, QLabel, QComboBox, QListWidget, QMessageBox, QFileDialog, QCompleter
)
from PyQt6.QtGui import QPalette, QBrush, QPixmap, QTextDocument, QFont
from PyQt6.QtPrintSupport import QPrintDialog, QPrinter, QPrintPreviewDialog
from PyQt6.QtCore import Qt
from models.invoice import Invoice

class ReceiptView(QWidget):
    def __init__(self):
        super().__init__()
        self.set_background_image("bg_images/receipts_bg.jpg")

        self.layout = QVBoxLayout()

        # Invoice Selector
        self.invoice_dropdown = QComboBox()
        self.invoice_dropdown.setEditable(True)
        invoice_completer = QCompleter()
        invoice_completer.setCaseSensitivity(Qt.CaseSensitivity.CaseInsensitive)
        self.invoice_dropdown.setCompleter(invoice_completer)

        self.load_invoice_ids()
        self.layout.addWidget(QLabel("Select Invoice:"))
        self.layout.addWidget(self.invoice_dropdown)

        # Load Button
        load_button = QPushButton("Load Receipt")
        load_button.clicked.connect(self.load_receipt)
        self.layout.addWidget(load_button)

        # Export PDF Button
        export_button = QPushButton("Export to PDF")
        export_button.clicked.connect(self.export_to_pdf)
        self.layout.addWidget(export_button)

        # Print Button
        print_button = QPushButton("Print Receipt")
        print_button.clicked.connect(self.print_receipt)
        self.layout.addWidget(print_button)

        # Receipt Display
        self.receipt_header = QLabel()
        self.receipt_items = QListWidget()
        self.receipt_footer = QLabel()

        self.layout.addWidget(self.receipt_header)
        self.layout.addWidget(self.receipt_items)
        self.layout.addWidget(self.receipt_footer)

        self.setLayout(self.layout)

    def set_background_image(self, image_path):
        palette = QPalette()
        pixmap = QPixmap(image_path)
        if not pixmap.isNull():
            scaled_pixmap = pixmap.scaled(self.size(), Qt.AspectRatioMode.IgnoreAspectRatio)
            palette.setBrush(QPalette.ColorRole.Window, QBrush(scaled_pixmap))
            self.setPalette(palette)

    def load_invoice_ids(self):
        self.invoice_dropdown.clear()
        invoices = Invoice.get_all_invoices()
        for inv in invoices:
            self.invoice_dropdown.addItem(f"{inv['invoice_id']} - {inv['customer_name']}")
            self.invoice_dropdown.completer().setModel(self.invoice_dropdown.model())

    def load_receipt(self):
        if self.invoice_dropdown.currentIndex() == -1:
            QMessageBox.warning(self, "Select Invoice", "Please select an invoice to view.")
            return

        invoice_id = int(self.invoice_dropdown.currentText().split(" - ")[0])
        invoice = Invoice.get_invoice_by_id(invoice_id)
        if not invoice:
            QMessageBox.warning(self, "Error", "Invoice not found.")
            return

        self.receipt_header.setText(
            f"Invoice #{invoice['invoice_id']} | {invoice['invoice_date']}\n"
            f"Customer: {invoice['customer_name']}\n"
            f"Discount: GHS {invoice['discount']} | Tax: GHS {invoice['tax']}\n"
            f"Total: GHS {invoice['total_amount']}\n"
        )

        self.receipt_items.clear()
        for item in invoice['items']:
            self.receipt_items.addItem(
                f"{item['product_name']} x {item['quantity']} @ GHS {item['unit_price']}"
            )

        self.receipt_footer.setText("Receipt loaded successfully.")

    def export_to_pdf(self):
        if self.invoice_dropdown.currentIndex() == -1:
            QMessageBox.warning(self, "Select Invoice", "Please select an invoice to export.")
            return

        invoice_id = int(self.invoice_dropdown.currentText().split(" - ")[0])
        file_path, _ = QFileDialog.getSaveFileName(self, "Save Receipt PDF", f"Invoice_{invoice_id}.pdf", "PDF Files (*.pdf)")
        if file_path:
            try:
                Invoice.export_receipt_to_pdf(invoice_id, file_path)
                QMessageBox.information(self, "Success", f"Receipt exported to {file_path}")
            except Exception as e:
                QMessageBox.warning(self, "Error", f"Failed to export PDF:\n{str(e)}")

    def print_receipt(self):
        if self.invoice_selector.currentIndex() == -1:
            QMessageBox.warning(self, "Select Invoice", "Please select an invoice to print.")
            return

        invoice_id = int(self.invoice_selector.currentText().split(" - ")[0])
        invoice = Invoice.get_invoice_by_id(invoice_id)
        if not invoice:
            QMessageBox.warning(self, "Error", "Invoice not found.")
            return

        html = f"""
        <h2 style="text-align:center;">Wholesale Management System</h2>
        <h3>Invoice #{invoice['invoice_id']}</h3>
        <p>Date: {invoice['invoice_date']}<br>
        Customer: {invoice['customer_name']}</p>
        <table border="1" cellspacing="0" cellpadding="4" width="100%">
            <tr>
                <th>Product</th><th>Quantity</th><th>Unit Price (GHS)</th><th>Subtotal (GHS)</th>
            </tr>
        """
        for item in invoice['items']:
            subtotal = item['quantity'] * item['unit_price']
            html += f"""
            <tr>
                <td>{item['product_name']}</td>
                <td align="center">{item['quantity']}</td>
                <td align="center">{item['unit_price']:.2f}</td>
                <td align="center">{subtotal:.2f}</td>
            </tr>
            """
        html += f"""
        </table>
        <p><strong>Discount:</strong> GHS {invoice['discount']:.2f}<br>
        <strong>Tax:</strong> GHS {invoice['tax']:.2f}<br>
        <strong>Total:</strong> GHS {invoice['total_amount']:.2f}</p>
        <p style="text-align:center;">Thank you for your business!</p>
        """

        doc = QTextDocument()
        doc.setDefaultFont(QFont("Helvetica", 10))
        doc.setHtml(html)

        printer = QPrinter()
        preview = QPrintPreviewDialog(printer, self)
        preview.paintRequested.connect(doc.print)
        preview.exec()
