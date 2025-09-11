import tempfile
import webbrowser
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QLabel, QTableWidget, QTableWidgetItem,
    QPushButton, QMessageBox, QComboBox, QCompleter, QFileDialog, QDialog, QHBoxLayout
)

from PyQt6.QtCore import Qt, QObject, QEvent


from models.invoice import Invoice
from database.db_handler import get_db_connection

from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib.units import mm


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

        # --- Enhancement: Show extra details ---
        wholesale_contact = f"Wholesale Contact: {self.get_wholesale_number()}"
        customer_number = invoice.get("customer_number", "N/A")
        total_items = sum(item['quantity'] for item in invoice["items"])

        # Remove previous details if any
        if hasattr(self, 'details_label'):
            self.layout.removeWidget(self.details_label)
            self.details_label.deleteLater()
        self.details_label = QLabel(f"Customer Number: {customer_number} | {wholesale_contact} | Total Items: {total_items}")
        self.layout.insertWidget(3, self.details_label)
        # --- End enhancement ---

        for item in invoice["items"]:
            row = self.receipt_table.rowCount()
            self.receipt_table.insertRow(row)
            item_product = QTableWidgetItem(item['product_name'])
            item_product.setFlags(Qt.ItemFlag.ItemIsSelectable | Qt.ItemFlag.ItemIsEnabled)
            self.receipt_table.setItem(row, 0, item_product)
            item_qty = QTableWidgetItem(str(item['quantity']))
            item_qty.setFlags(Qt.ItemFlag.ItemIsSelectable | Qt.ItemFlag.ItemIsEnabled)
            self.receipt_table.setItem(row, 1, item_qty)
            item_price = QTableWidgetItem(f"GH¢ {item['unit_price']:,.2f}")
            item_price.setFlags(Qt.ItemFlag.ItemIsSelectable | Qt.ItemFlag.ItemIsEnabled)
            self.receipt_table.setItem(row, 2, item_price)
            total = item['quantity'] * item['unit_price']
            item_total = QTableWidgetItem(f"GH¢ {total:,.2f}")
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

        # Prepare data
        invoice_number = invoice.get("invoice_id", "")
        invoice_date = invoice.get("invoice_date", "")
        customer_name = invoice.get("customer_name", "")
        customer_number = invoice.get("customer_number", "N/A")
        wholesale_contact = f"Wholesale Number: {self.get_wholesale_number()}"
        items = [
            [
                item["product_name"],
                str(item["quantity"]),
                f"{item['unit_price']:.2f}",
                f"{item['quantity'] * item['unit_price']:.2f}"
            ]
            for item in invoice["items"]
        ]
        total_items = sum(item['quantity'] for item in invoice["items"])
        discount = f"{invoice.get('discount', 0):.2f}"
        tax = f"{invoice.get('tax', 0):.2f}"
        total = f"{invoice.get('total_amount', 0):.2f}"

        # Create PDF
        doc = SimpleDocTemplate(file_path, pagesize=A4, rightMargin=30, leftMargin=30, topMargin=30, bottomMargin=30)
        styles = getSampleStyleSheet()
        elements = []

        # Title
        title_style = ParagraphStyle(
            name="Title",
            parent=styles["Title"],
            alignment=1,  # Center
            fontSize=18,
            leading=22,
            spaceAfter=10,
            fontName="Helvetica-Bold"
        )
        elements.append(Paragraph("Wholesale Name Here", title_style))

        # Invoice details (with enhancements)
        elements.append(Paragraph(f"Invoice Number: {invoice_number}", styles["Normal"]))
        elements.append(Paragraph(f"Date: {invoice_date}", styles["Normal"]))
        elements.append(Paragraph(f"Customer Name: {customer_name}", styles["Normal"]))
        elements.append(Paragraph(f"Customer Number: {customer_number}", styles["Normal"]))
        elements.append(Paragraph(f"{wholesale_contact}", styles["Normal"]))
        elements.append(Spacer(1, 12))

        # Table data
        table_data = [
            ["Product", "Quantity", "Unit Price (GH¢)", "Subtotal (GH¢)"]
        ] + items
        # Add total items row at the bottom
        table_data.append(["", f"Total Items: {total_items}", "", ""])

        table = Table(table_data, colWidths=[60*mm, 30*mm, 40*mm, 40*mm])
        table.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), colors.lightblue),
            ("TEXTCOLOR", (0, 0), (-1, 0), colors.black),
            ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
            ("ALIGN", (1, 1), (-1, -1), "CENTER"),
            ("GRID", (0, 0), (-1, -1), 0.5, colors.black),
            ("BOTTOMPADDING", (0, 0), (-1, 0), 8),
            ("TOPPADDING", (0, 0), (-1, 0), 8),
            ("BOTTOMPADDING", (0, 1), (-1, -2), 6),
            ("TOPPADDING", (0, 1), (-1, -2), 6),
            ("FONTNAME", (0, -1), (-1, -1), "Helvetica-Bold"),
            ("BACKGROUND", (0, -1), (-1, -1), colors.whitesmoke),
        ]))
        elements.append(table)
        elements.append(Spacer(1, 16))

        # Summary
        summary_style = ParagraphStyle(name="Summary", parent=styles["Normal"], leftIndent=400,)
        elements.append(Paragraph(f"Discount: GH¢ {discount}", summary_style))
        elements.append(Paragraph(f"Tax: GH¢ {tax}", summary_style))
        elements.append(Paragraph(f"Total: GH¢ {total}", summary_style))
        elements.append(Spacer(1, 30))



        # Footer
        footer_style = ParagraphStyle(
            name="Footer",
            parent=styles["Normal"],
            alignment=1,  # Center
            fontSize=11,
            textColor=colors.grey,
            spaceBefore=40
        )
        elements.append(Spacer(1, 60))
        elements.append(Paragraph("Thank you for buying from us!", footer_style))

        doc.build(elements)
        QMessageBox.information(self, "Export Complete", f"Receipt saved as {file_path}")





    def print_receipt(self):
        # Generate a temp PDF and open it for printing
        if self.invoice_dropdown.currentIndex() == -1:
            QMessageBox.warning(self, "Print Error", "Please load a receipt first.")
            return

        invoice_text = self.invoice_dropdown.currentText()
        invoice_id = int(invoice_text.split(" - ")[0])
        invoice = Invoice.get_invoice_by_id(invoice_id)
        if not invoice:
            QMessageBox.warning(self, "Print Error", "Invoice not found.")
            return

        with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp:
            tmp_path = tmp.name
        self.export_to_pdf_custom_path(invoice, tmp_path)
        webbrowser.open(tmp_path)

    def export_to_pdf_custom_path(self, invoice, file_path):
        invoice_number = invoice.get("invoice_id", "")
        invoice_date = invoice.get("invoice_date", "")
        customer_name = invoice.get("customer_name", "")
        customer_number = invoice.get("customer_number", "N/A")
        wholesale_contact = f"Wholesale Contact: {self.get_wholesale_number()}"
        items = [
            [
                item["product_name"],
                str(item["quantity"]),
                f"{item['unit_price']:.2f}",
                f"{item['quantity'] * item['unit_price']:,.2f}"
            ]
            for item in invoice["items"]
        ]
        total_items = sum(item['quantity'] for item in invoice["items"])
        discount = f"{invoice.get('discount', 0):,.2f}"
        tax = f"{invoice.get('tax', 0):,.2f}"
        total = f"{invoice.get('total_amount', 0):,.2f}"
        doc = SimpleDocTemplate(file_path, pagesize=A4, rightMargin=30, leftMargin=30, topMargin=30, bottomMargin=30)
        styles = getSampleStyleSheet()
        elements = []
        title_style = ParagraphStyle(
            name="Title",
            parent=styles["Title"],
            alignment=1,
            fontSize=18,
            leading=22,
            spaceAfter=10,
            fontName="Helvetica-Bold"
        )
        elements.append(Paragraph("Wholesale Name Here", title_style))
        elements.append(Paragraph(f"Invoice Number: {invoice_number}", styles["Normal"]))
        elements.append(Paragraph(f"Date: {invoice_date}", styles["Normal"]))
        elements.append(Paragraph(f"Customer Name: {customer_name}", styles["Normal"]))
        elements.append(Paragraph(f"Customer Number: {customer_number}", styles["Normal"]))
        elements.append(Paragraph(f"{wholesale_contact}", styles["Normal"]))
        elements.append(Spacer(1, 12))
        table_data = [
            ["Product", "Quantity", "Unit Price (GH¢)", "Subtotal (GH¢)"]
        ] + items
        table_data.append(["", f"Total Items: {total_items}", "", ""])

        table = Table(table_data, colWidths=[60*mm, 30*mm, 40*mm, 40*mm])
        table.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), colors.lightblue),
            ("TEXTCOLOR", (0, 0), (-1, 0), colors.black),
            ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
            ("ALIGN", (1, 1), (-1, -1), "CENTER"),
            ("GRID", (0, 0), (-1, -1), 0.5, colors.black),
            ("BOTTOMPADDING", (0, 0), (-1, 0), 8),
            ("TOPPADDING", (0, 0), (-1, 0), 8),
            ("BOTTOMPADDING", (0, 1), (-1, -1), 6),
            ("TOPPADDING", (0, 1), (-1, -1), 6),
            ("FONTNAME", (0, -1), (-1, -1), "Helvetica-Bold"),
            ("BACKGROUND", (0, -1), (-1, -1), colors.whitesmoke),
        ]))
        elements.append(table)
        elements.append(Spacer(1, 16))
        summary_style = ParagraphStyle(name="Summary", parent=styles["Normal"], leftIndent=400)
        elements.append(Paragraph(f"Discount: GH¢ {discount}", summary_style))
        elements.append(Paragraph(f"Tax: GH¢ {tax}", summary_style))
        elements.append(Paragraph(f"Total: GH¢ {total}", summary_style))
        elements.append(Spacer(1, 30))
        footer_style = ParagraphStyle(
            name="Footer",
            parent=styles["Normal"],
            alignment=1,
            fontSize=11,
            textColor=colors.grey,
            spaceBefore=40
        )
        elements.append(Spacer(1, 60))
        elements.append(Paragraph("Thank you for buying from us!", footer_style))

        doc.build(elements)
        # Remove QPrinter/QPainter printing logic to prevent crash
        # The PDF is generated and opened for printing via the default PDF viewer.
