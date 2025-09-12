from datetime import datetime
from database.db_handler import get_db_connection
from models.product import Product

#Invoice Class
class Invoice:
    def __init__(self, invoice_id, customer_id, invoice_date, discount, tax, total_amount):
        self.invoice_id = invoice_id
        self.customer_id = customer_id
        self.invoice_date = invoice_date
        self.discount = discount
        self.tax = tax
        self.total_amount = total_amount

    #Create Invoice method
    @staticmethod
    def create_invoice(customer_id, items, discount=0.0, tax=0.0):
        connection = get_db_connection()
        cursor = connection.cursor()

        subtotal = sum(item['quantity'] * item['unit_price'] for item in items) #Calculate Subtotal for each item
        total_after_discount = subtotal - discount + tax #Imply discount
        invoice_date = datetime.now().strftime("%Y-%m-%d %H:%M:%S") #Date

        cursor.execute("""
            INSERT INTO invoices (customer_id, invoice_date, discount, tax, total_amount)
            VALUES (?, ?, ?, ?, ?)
        """, (customer_id, invoice_date, discount, tax, total_after_discount))
        invoice_id = cursor.lastrowid

        for item in items:
            product_id = item['product_id']
            quantity = item['quantity']
            unit_price = item['unit_price']

            cursor.execute("""
                INSERT INTO invoice_items (invoice_id, product_id, quantity, unit_price)
                VALUES (?, ?, ?, ?)
            """, (invoice_id, product_id, quantity, unit_price))

            product = Product.get_product_by_id(product_id)
            if product is None:
                connection.rollback()
                connection.close()
                raise ValueError(f"Product ID {product_id} not found.")

            new_stock = product.stock_quantity - quantity
            if new_stock < 0:
                connection.rollback()
                connection.close()
                raise ValueError(f"Insufficient stock for product ID {product_id}. Current stock: {product.stock_quantity}")

            Product.update_stock(product_id, new_stock, connection)

        connection.commit()
        connection.close()
        return invoice_id

    #Update Invoice
    @staticmethod
    def update_invoice(invoice_id, customer_id, items, discount=0.0, tax=0.0):
        connection = get_db_connection()
        cursor = connection.cursor()

        cursor.execute("SELECT product_id, quantity FROM invoice_items WHERE invoice_id = ?", (invoice_id,))
        old_items = cursor.fetchall()
        for product_id, quantity in old_items:
            product = Product.get_product_by_id(product_id)
            if product:
                Product.update_stock(product_id, product.stock_quantity + quantity, connection)

        cursor.execute("DELETE FROM invoice_items WHERE invoice_id = ?", (invoice_id,))

        subtotal = sum(item['quantity'] * item['unit_price'] for item in items)
        total_after_discount = subtotal - discount + tax

        cursor.execute("""
            UPDATE invoices
            SET customer_id = ?, discount = ?, tax = ?, total_amount = ?
            WHERE invoice_id = ?
        """, (customer_id, discount, tax, total_after_discount, invoice_id))

        for item in items:
            product_id = item['product_id']
            quantity = item['quantity']
            unit_price = item['unit_price']

            cursor.execute("""
                INSERT INTO invoice_items (invoice_id, product_id, quantity, unit_price)
                VALUES (?, ?, ?, ?)
            """, (invoice_id, product_id, quantity, unit_price))

            product = Product.get_product_by_id(product_id)
            if product is None:
                connection.rollback()
                connection.close()
                raise ValueError(f"Product ID {product_id} not found.")

            new_stock = product.stock_quantity - quantity
            if new_stock < 0:
                connection.rollback()
                connection.close()
                raise ValueError(f"Insufficient stock for product ID {product_id}. Current stock: {product.stock_quantity}")

            Product.update_stock(product_id, new_stock, connection)

        connection.commit()
        connection.close()


    #Delete Invoice
    @staticmethod
    def delete_invoice(invoice_id):
        connection = get_db_connection()
        cursor = connection.cursor()

        cursor.execute("SELECT product_id, quantity FROM invoice_items WHERE invoice_id = ?", (invoice_id,))
        items = cursor.fetchall()
        for product_id, quantity in items:
            product = Product.get_product_by_id(product_id)
            if product:
                Product.update_stock(product_id, product.stock_quantity + quantity, connection)

        cursor.execute("DELETE FROM invoice_items WHERE invoice_id = ?", (invoice_id,))
        cursor.execute("DELETE FROM invoices WHERE invoice_id = ?", (invoice_id,))

        connection.commit()
        connection.close()


    #Get all Invoice
    @staticmethod
    def get_all_invoices():
        connection = get_db_connection()
        cursor = connection.cursor()
        cursor.execute("""
            SELECT invoices.invoice_id, customers.name, invoices.total_amount
            FROM invoices
            JOIN customers ON invoices.customer_id = customers.customer_id
        """)
        rows = cursor.fetchall()
        connection.close()

        # Return list of simple objects or named tuples for attribute access
        invoices = []
        for row in rows:
            invoice = type('InvoiceRecord', (object,), {})()
            invoice.invoice_id = row[0]
            invoice.customer_name = row[1]
            invoice.total_amount = row[2]
            invoices.append(invoice)
        return invoices

    #Get to Invoice by ID
    @staticmethod
    def get_invoice_by_id(invoice_id):
        connection = get_db_connection()
        cursor = connection.cursor()

        cursor.execute("""
            SELECT i.invoice_id, c.name, i.invoice_date, i.discount, i.tax, i.total_amount, i.customer_id, c.phone_number
            FROM invoices i
            JOIN customers c ON i.customer_id = c.customer_id
            WHERE i.invoice_id = ?
        """, (invoice_id,))
        row = cursor.fetchone()

        if not row:
            connection.close()
            return None

        invoice = {
            "invoice_id": row[0],
            "customer_name": row[1],
            "invoice_date": row[2],
            "discount": row[3],
            "tax": row[4],
            "total_amount": row[5],
            "customer_id": row[6],
            "customer_number": row[7],
            "items": []
        }

        cursor.execute("""
            SELECT p.name, ii.quantity, ii.unit_price
            FROM invoice_items ii
            JOIN products p ON ii.product_id = p.product_id
            WHERE ii.invoice_id = ?
        """, (invoice_id,))
        items = cursor.fetchall()

        connection.close()

        invoice["items"] = [
            {"product_name": item[0], "quantity": item[1], "unit_price": item[2]}
            for item in items
        ]

        return invoice

    @staticmethod
    def get_wholesale_name():
        try:
            conn = get_db_connection()
            cur = conn.cursor()
            cur.execute("SELECT wholesale_name FROM settings WHERE id=1")
            result = cur.fetchone()
            conn.close()
            if result and result[0]:
                return result[0]
            return "Wholesale Name Here"
        except Exception:
            return "Wholesale Name Here"

    @staticmethod
    def get_wholesale_address():
        try:
            conn = get_db_connection()
            cur = conn.cursor()
            cur.execute("SELECT wholesale_address FROM settings WHERE id=1")
            result = cur.fetchone()
            conn.close()
            if result and result[0]:
                return result[0]
            return ""
        except Exception:
            return ""

    @staticmethod
    def format_receipt_data(invoice, wholesale_number=None, wholesale_address=None):
        if wholesale_number is None:
            wholesale_number = Invoice.get_wholesale_name()
        if wholesale_address is None:
            wholesale_address = Invoice.get_wholesale_address()
        """
        Returns all formatted data needed for receipt PDF export and UI display.
        """
        invoice_number = invoice.get("invoice_id", "")
        invoice_date = invoice.get("invoice_date", "")
        customer_name = invoice.get("customer_name", "")
        customer_number = invoice.get("customer_number", "N/A")
        # Defensive extraction of contact number
        contact_number = str(wholesale_number)
        if contact_number.lower().startswith('wholesale contact:'):
            contact_number = contact_number[18:]
        wholesale_contact = f"Wholesale Contact: {contact_number}"
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
        return {
            "invoice_number": invoice_number,
            "invoice_date": invoice_date,
            "customer_name": customer_name,
            "customer_number": customer_number,
            "wholesale_contact": contact_number,
            "wholesale_address": wholesale_address,
            "items": items,
            "total_items": total_items,
            "discount": discount,
            "tax": tax,
            "total": total
        }

    @staticmethod
    def export_receipt_to_pdf(formatted_data, file_path):
        from reportlab.lib.pagesizes import A4
        from reportlab.lib import colors
        from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
        from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
        from reportlab.lib.units import mm
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
        elements.append(Paragraph(Invoice.get_wholesale_name(), title_style))
        # Minimal font for contact and address
        contact_address_style = ParagraphStyle(
            name="ContactAddress",
            parent=styles["Normal"],
            alignment=1,
            fontSize=10,
            textColor=colors.darkgray,
            spaceAfter=8,
        )
        contact_line = f"Contact: {formatted_data.get('wholesale_contact', '')} | Location: {formatted_data.get('wholesale_address', '')}"
        elements.append(Paragraph(contact_line, contact_address_style))
        elements.append(Paragraph(f"Invoice Number: {formatted_data['invoice_number']}", styles["Normal"]))
        elements.append(Paragraph(f"Date: {formatted_data['invoice_date']}", styles["Normal"]))
        elements.append(Paragraph(f"Customer Name: {formatted_data['customer_name']}", styles["Normal"]))
        elements.append(Paragraph(f"Customer Number: {formatted_data['customer_number']}", styles["Normal"]))
        elements.append(Spacer(1, 12))
        table_data = [
            ["Product", "Quantity", "Unit Price (GH¢)", "Subtotal (GH¢)"]
        ] + formatted_data['items']
        table_data.append(["", f"Total Items: {formatted_data['total_items']}", "", ""])
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
        summary_style = ParagraphStyle(name="Summary", parent=styles["Normal"], leftIndent=400)
        elements.append(Paragraph(f"Discount: GH¢ {formatted_data['discount']}", summary_style))
        elements.append(Paragraph(f"Tax: GH¢ {formatted_data['tax']}", summary_style))
        elements.append(Paragraph(f"Total: GH¢ {formatted_data['total']}", summary_style))
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
