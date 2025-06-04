#Import Framework and Library
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QLabel, QListWidget, QPushButton, QMessageBox, QComboBox, QCompleter
)
from PyQt6.QtGui import QPainter, QFont
from PyQt6.QtPrintSupport import QPrinter, QPrintDialog, QPrintPreviewDialog
from PyQt6.QtCore import Qt
from models.invoice import Invoice


class ReceiptView(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("View Receipt")
        self.setStyleSheet(self.get_stylesheet())

        self.layout = QVBoxLayout() #Set Layout

        #Dropdown of Receipts
        self.invoice_dropdown = QComboBox()
        self.invoice_dropdown.setEditable(True)
        self.invoice_completer = QCompleter()
        self.invoice_completer.setCaseSensitivity(Qt.CaseSensitivity.CaseInsensitive)
        self.invoice_dropdown.setCompleter(self.invoice_completer)

        self.layout.addWidget(QLabel("Select Invoice:"))
        self.layout.addWidget(self.invoice_dropdown)

        self.show_receipt_button = QPushButton("Show Receipt")
        self.show_receipt_button.clicked.connect(self.show_receipt)
        self.layout.addWidget(self.show_receipt_button)

        self.receipt_list = QListWidget()
        self.layout.addWidget(self.receipt_list)

        # Export to PDF button
        self.export_pdf_button = QPushButton("Export to PDF")
        self.export_pdf_button.clicked.connect(self.export_to_pdf)
        self.layout.addWidget(self.export_pdf_button)

        # Print button
        self.print_button = QPushButton("Print Receipt")
        self.print_button.clicked.connect(self.print_receipt)
        self.layout.addWidget(self.print_button)

        self.setLayout(self.layout)

        self.load_invoices()

    #Receipt View Style
    def get_stylesheet(self):
        return """
        QWidget {
            background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
                        stop:0 #dfe9f3, stop:1 #ffffff);
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            font-size: 14px;
            color: #222222;
        }
        QLabel {
            font-weight: 600;
            margin: 6px 0;
        }
        QComboBox {
            background-color: white;
            border: 1px solid #bbb;
            border-radius: 6px;
            padding: 6px;
        }
        QComboBox:focus {
            border: 2px solid #5dade2;
        }
        QPushButton {
            background-color: #5dade2;
            color: white;
            border-radius: 8px;
            padding: 8px 16px;
            margin-top: 10px;
        }
        QPushButton:hover {
            background-color: #85c1e9;
        }
        QListWidget {
            background-color: white;
            border: 1px solid #bbb;
            border-radius: 6px;
            padding: 8px;
            max-height: 200px;
        }
        """

    #Load Prepared Receipts
    def load_invoices(self):
        self.invoice_dropdown.clear()
        invoices = Invoice.get_all_invoices()
        invoice_strs = [f"{inv.invoice_id} - {inv.customer_name} - GHS {inv.total:.2f}" for inv in invoices]
        self.invoice_dropdown.addItems(invoice_strs)
        self.invoice_completer.setModel(self.invoice_dropdown.model())

    # Act upon a click on Show Receipt
    def show_receipt(self):
        if self.invoice_dropdown.currentIndex() == -1:
            QMessageBox.warning(self, "Input Error", "Select an invoice first.")
            return

        invoice_text = self.invoice_dropdown.currentText()
        invoice_id = int(invoice_text.split(" - ")[0])

        receipt_details = Invoice.get_receipt_details(invoice_id)
        self.receipt_list.clear()
        for line in receipt_details:
            self.receipt_list.addItem(line)


    #Act upon a click on Export to PDF Button
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

        # Header
        painter.setFont(QFont("Arial", 14, QFont.Weight.Bold))
        painter.drawText(margin, y, f"Wholesale Management System Receipt")
        y += 30
        painter.setFont(QFont("Arial", 11))
        painter.drawText(margin, y, f"Invoice: {invoice_text}")
        y += 25

        # Draw a line separator
        painter.drawLine(margin, y, printer.pageRect().width() - margin, y)
        y += 20

        # Receipt lines
        for i in range(self.receipt_list.count()):
            line_text = self.receipt_list.item(i).text()
            painter.drawText(margin, y, line_text)
            y += 20

            if y > printer.pageRect().height() - margin:
                printer.newPage()
                y = margin

        painter.end()

        QMessageBox.information(self, "PDF Exported", f"Receipt saved as receipt_{invoice_id}.pdf")

    def print_receipt(self):
        if self.receipt_list.count() == 0:
            QMessageBox.warning(self, "Print Error", "Please load a receipt first.")
            return

        printer = QPrinter(QPrinter.PrinterMode.HighResolution)
        preview_dialog = QPrintPreviewDialog(printer)
        preview_dialog.paintRequested.connect(self.handle_paint_request)
        preview_dialog.exec()

    def handle_paint_request(self, printer):
        painter = QPainter(printer)
        painter.setFont(QFont("Arial", 11))
        margin = 50
        y = margin

        # Header
        painter.setFont(QFont("Arial", 14, QFont.Weight.Bold))
        painter.drawText(margin, y, f"Wholesale Management System Receipt")
        y += 30
        painter.setFont(QFont("Arial", 11))
        invoice_text = self.invoice_dropdown.currentText()
        painter.drawText(margin, y, f"Invoice: {invoice_text}")
        y += 25

        # Draw a line separator
        painter.drawLine(margin, y, printer.pageRect().width() - margin, y)
        y += 20

        # Receipt lines
        for i in range(self.receipt_list.count()):
            line_text = self.receipt_list.item(i).text()
            painter.drawText(margin, y, line_text)
            y += 20

            if y > printer.pageRect().height() - margin:
                printer.newPage()
                y = margin

        painter.end()
