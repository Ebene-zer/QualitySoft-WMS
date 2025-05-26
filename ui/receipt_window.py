from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QLabel, QComboBox, QPushButton, QListWidget, QMessageBox
)
from PyQt6.QtGui import QPalette, QBrush, QPixmap
from PyQt6.QtCore import QSize, Qt
from PyQt6.QtWidgets import QFileDialog


from models.invoice import Invoice


class ReceiptWindow(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Invoice Receipt Viewer")

        self.resize(800, 600)
        self.setMinimumSize(600, 400)

        self.set_background_image("bg_images/invoice1.png")

        self.layout = QVBoxLayout()

        # Invoice selector
        self.invoice_selector = QComboBox()
        self.load_invoice_ids()
        self.layout.addWidget(QLabel("Select Invoice:"))
        self.layout.addWidget(self.invoice_selector)

        # Load button
        load_button = QPushButton("Load Receipt")
        load_button.clicked.connect(self.load_receipt)
        self.layout.addWidget(load_button)

        # Export PDF button
        export_button = QPushButton("Export to PDF")
        export_button.clicked.connect(self.export_to_pdf)
        self.layout.addWidget(export_button)

        # Receipt output widgets
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
        self.invoice_selector.clear()
        invoices = Invoice.get_all_invoices()
        for inv in invoices:
            self.invoice_selector.addItem(f"{inv['invoice_id']} - {inv['customer_name']}")

    def load_receipt(self):
        if self.invoice_selector.currentIndex() == -1:
            QMessageBox.warning(self, "Select Invoice", "Please select an invoice to view.")
            return

        invoice_text = self.invoice_selector.currentText()
        invoice_id = int(invoice_text.split(" - ")[0])

        invoice = Invoice.get_invoice_by_id(invoice_id)
        if not invoice:
            QMessageBox.warning(self, "Error", "Invoice not found.")
            return

        # Header
        self.receipt_header.setText(
            f"Invoice #{invoice['invoice_id']} | {invoice['invoice_date']}\n"
            f"Customer: {invoice['customer_name']}\n"
            f"Discount: GHS {invoice['discount']} | Tax: GHS {invoice['tax']}\n"
            f"Total: GHS {invoice['total_amount']}\n"
        )

        # Items
        self.receipt_items.clear()
        for item in invoice['items']:
            self.receipt_items.addItem(
                f"{item['product_name']} x {item['quantity']} @ GHS {item['unit_price']}"
            )

        self.receipt_footer.setText("Receipt loaded successfully.")

    def export_to_pdf(self):
            if self.invoice_selector.currentIndex() == -1:
                QMessageBox.warning(self, "Select Invoice", "Please select an invoice to export.")
                return

            invoice_text = self.invoice_selector.currentText()
            invoice_id = int(invoice_text.split(" - ")[0])

            file_path, _ = QFileDialog.getSaveFileName(self, "Save Receipt PDF", f"Invoice_{invoice_id}.pdf",
                                                       "PDF Files (*.pdf)")
            if file_path:
                try:
                    from models.invoice import Invoice
                    Invoice.export_receipt_to_pdf(invoice_id, file_path)
                    QMessageBox.information(self, "Success", f"Receipt exported to {file_path}")
                except Exception as e:
                    QMessageBox.warning(self, "Error", f"Failed to export PDF:\n{str(e)}")

