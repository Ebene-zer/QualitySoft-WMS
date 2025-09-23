from datetime import datetime

from database.db_handler import get_db_connection
from models.product import Product


# Invoice Class
class Invoice:
    def __init__(self, invoice_id, customer_id, invoice_date, discount, tax, total_amount):
        self.invoice_id = invoice_id
        self.customer_id = customer_id
        self.invoice_date = invoice_date
        self.discount = discount
        self.tax = tax
        self.total_amount = total_amount

    # Create Invoice method
    @staticmethod
    def create_invoice(customer_id, items, discount=0.0, tax=0.0):
        # Use a DB transaction to validate and reserve stock atomically to avoid race conditions.
        connection = get_db_connection()
        cursor = connection.cursor()
        try:
            # Acquire a write lock to prevent concurrent stock changes
            cursor.execute("BEGIN IMMEDIATE")

            # Aggregate requested quantities per product_id
            requested = {}
            for it in items:
                pid = it["product_id"]
                requested[pid] = requested.get(pid, 0) + int(it["quantity"])

            # Validate stock for each product against current DB value
            for pid, req_qty in requested.items():
                cursor.execute("SELECT stock_quantity FROM products WHERE product_id = ?", (pid,))
                row = cursor.fetchone()
                if not row:
                    raise ValueError(f"Product ID {pid} not found.")
                stock = row[0]
                if req_qty > stock:
                    raise ValueError(
                        f"Insufficient stock for product ID {pid}. Available: {stock}, requested: {req_qty}."
                    )

            # All validations passed; insert invoice
            subtotal = sum(int(item["quantity"]) * float(item["unit_price"]) for item in items)
            total_after_discount = subtotal - float(discount) + float(tax)
            invoice_date = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

            cursor.execute(
                """
                INSERT INTO invoices (customer_id, invoice_date, discount, tax, total_amount)
                VALUES (?, ?, ?, ?, ?)
            """,
                (customer_id, invoice_date, discount, tax, total_after_discount),
            )
            invoice_id = cursor.lastrowid

            # Insert invoice_items and decrement stock in the same transaction
            for item in items:
                product_id = item["product_id"]
                quantity = int(item["quantity"])
                unit_price = float(item["unit_price"])

                cursor.execute(
                    """
                    INSERT INTO invoice_items (invoice_id, product_id, quantity, unit_price)
                    VALUES (?, ?, ?, ?)
                """,
                    (invoice_id, product_id, quantity, unit_price),
                )

                cursor.execute(
                    "UPDATE products SET stock_quantity = stock_quantity - ? WHERE product_id = ?",
                    (quantity, product_id),
                )

            connection.commit()
            return invoice_id
        except Exception:
            connection.rollback()
            raise
        finally:
            connection.close()

    # Update Invoice
    @staticmethod
    def update_invoice(invoice_id, customer_id, items, discount=0.0, tax=0.0):
        connection = get_db_connection()
        cursor = connection.cursor()
        try:
            cursor.execute("BEGIN IMMEDIATE")

            # Restore stock from existing invoice items
            cursor.execute("SELECT product_id, quantity FROM invoice_items WHERE invoice_id = ?", (invoice_id,))
            old_items = cursor.fetchall()
            for product_id, quantity in old_items:
                cursor.execute(
                    "UPDATE products SET stock_quantity = stock_quantity + ? WHERE product_id = ?",
                    (quantity, product_id),
                )

            # Remove old invoice items
            cursor.execute("DELETE FROM invoice_items WHERE invoice_id = ?", (invoice_id,))

            # Aggregate requested quantities for the new items
            requested = {}
            for it in items:
                pid = it["product_id"]
                requested[pid] = requested.get(pid, 0) + int(it["quantity"])

            # Validate stock availability for each product
            for pid, req_qty in requested.items():
                cursor.execute("SELECT stock_quantity FROM products WHERE product_id = ?", (pid,))
                row = cursor.fetchone()
                if not row:
                    raise ValueError(f"Product ID {pid} not found.")
                stock = row[0]
                if req_qty > stock:
                    raise ValueError(
                        f"Insufficient stock for product ID {pid}. Available: {stock}, requested: {req_qty}."
                    )

            # Update invoice header
            subtotal = sum(int(item["quantity"]) * float(item["unit_price"]) for item in items)
            total_after_discount = subtotal - float(discount) + float(tax)
            cursor.execute(
                """
                UPDATE invoices
                SET customer_id = ?, discount = ?, tax = ?, total_amount = ?
                WHERE invoice_id = ?
            """,
                (customer_id, discount, tax, total_after_discount, invoice_id),
            )

            # Insert new invoice_items and decrement stock
            for item in items:
                product_id = item["product_id"]
                quantity = int(item["quantity"])
                unit_price = float(item["unit_price"])
                cursor.execute(
                    """
                    INSERT INTO invoice_items (invoice_id, product_id, quantity, unit_price)
                    VALUES (?, ?, ?, ?)
                """,
                    (invoice_id, product_id, quantity, unit_price),
                )
                cursor.execute(
                    "UPDATE products SET stock_quantity = stock_quantity - ? WHERE product_id = ?",
                    (quantity, product_id),
                )

            connection.commit()
        except Exception:
            connection.rollback()
            raise
        finally:
            connection.close()

    # Delete Invoice
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

    # Get all Invoice
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
            invoice = type("InvoiceRecord", (object,), {})()
            invoice.invoice_id = row[0]
            invoice.customer_name = row[1]
            invoice.total_amount = row[2]
            invoices.append(invoice)
        return invoices

    # Get to Invoice by ID
    @staticmethod
    def get_invoice_by_id(invoice_id):
        connection = get_db_connection()
        cursor = connection.cursor()

        cursor.execute(
            """
            SELECT i.invoice_id,
                   c.name,
                   i.invoice_date,
                   i.discount,
                   i.tax,
                   i.total_amount,
                   i.customer_id,
                   c.phone_number
            FROM invoices i
            JOIN customers c ON i.customer_id = c.customer_id
            WHERE i.invoice_id = ?
            """,
            (invoice_id,),
        )
        row = cursor.fetchone()

        if not row:
            connection.close()
            return None

        # Defensive: handle missing columns in mock/fetchone
        invoice = {
            "invoice_id": row[0] if len(row) > 0 else None,
            "customer_name": row[1] if len(row) > 1 else None,
            "invoice_date": row[2] if len(row) > 2 else None,
            "discount": row[3] if len(row) > 3 else None,
            "tax": row[4] if len(row) > 4 else None,
            "total_amount": row[5] if len(row) > 5 else None,
            "customer_id": row[6] if len(row) > 6 else None,
            "customer_number": row[7] if len(row) > 7 else None,
            "items": [],
        }

        cursor.execute(
            """
            SELECT p.name, ii.quantity, ii.unit_price
            FROM invoice_items ii
            JOIN products p ON ii.product_id = p.product_id
            WHERE ii.invoice_id = ?
        """,
            (invoice_id,),
        )
        items = cursor.fetchall()

        connection.close()

        invoice["items"] = [{"product_name": item[0], "quantity": item[1], "unit_price": item[2]} for item in items]

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
    def get_receipt_texts():
        """Return (thank_you, notes) from settings with safe defaults."""
        try:
            conn = get_db_connection()
            cur = conn.cursor()
            cur.execute("SELECT receipt_thank_you, receipt_notes FROM settings WHERE id=1")
            row = cur.fetchone()
            conn.close()
            thank = row[0] if row and row[0] else "Thank you for buying from us!"
            notes = row[1] if row and row[1] else ""
            return thank, notes
        except Exception:
            return "Thank you for buying from us!", ""

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
        # Convert stored invoice_date (ISO) to Day/Month/Year for display
        raw_date = invoice.get("invoice_date", "")
        invoice_date = raw_date
        if raw_date:
            try:
                # Try parse with timestamp first
                dt = datetime.strptime(raw_date, "%Y-%m-%d %H:%M:%S")
                invoice_date = dt.strftime("%d/%m/%Y %H:%M:%S")
            except Exception:
                try:
                    dt = datetime.strptime(raw_date, "%Y-%m-%d")
                    invoice_date = dt.strftime("%d/%m/%Y")
                except Exception:
                    # leave as-is if unknown format
                    invoice_date = raw_date
        customer_name = invoice.get("customer_name", "")
        customer_number = invoice.get("customer_number", "N/A")
        # Defensive extraction of contact number
        contact_number = str(wholesale_number)
        if contact_number.lower().startswith("wholesale contact:"):
            contact_number = contact_number[18:]
        items = [
            [
                item["product_name"],
                str(item["quantity"]),
                f"{item['unit_price']:.2f}",
                f"{item['quantity'] * item['unit_price']:.2f}",
            ]
            for item in invoice["items"]
        ]
        total_items = sum(item["quantity"] for item in invoice["items"])
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
            "total": total,
        }

    @staticmethod
    def export_receipt_to_pdf(formatted_data, file_path):
        from reportlab.lib import colors
        from reportlab.lib.pagesizes import A4
        from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
        from reportlab.lib.units import mm
        from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle

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
            fontName="Helvetica-Bold",
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
        contact_line = (
            "Contact: "
            f"{formatted_data.get('wholesale_contact', '')} | Location: "
            f"{formatted_data.get('wholesale_address', '')}"
        )
        elements.append(Paragraph(contact_line, contact_address_style))
        # Details
        elements.append(
            Paragraph(
                f"<b>Invoice Number:</b> <font name='Helvetica'>{formatted_data['invoice_number']}</font>",
                styles["Normal"],
            )
        )
        elements.append(
            Paragraph(
                f"<b>Date:</b> <font name='Helvetica'>{formatted_data['invoice_date']}</font>",
                styles["Normal"],
            )
        )
        elements.append(
            Paragraph(
                f"<b>Customer Name:</b> <font name='Helvetica'>{formatted_data['customer_name']}</font>",
                styles["Normal"],
            )
        )
        elements.append(Spacer(1, 12))
        # Items table
        table_data = [["Product", "Quantity", "Unit Price (GH¢)", "Subtotal (GH¢)"]] + formatted_data["items"]
        table_data.append(["", f"Total Items: {formatted_data['total_items']}", "", ""])
        table = Table(table_data, colWidths=[60 * mm, 30 * mm, 40 * mm, 40 * mm])
        table.setStyle(
            TableStyle(
                [
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
                ]
            )
        )
        elements.append(table)
        elements.append(Spacer(1, 16))

        # Summary (right) and Notes (left) side by side
        summary_right = ParagraphStyle(name="SummaryRight", parent=styles["Normal"], alignment=2)
        notes_style = ParagraphStyle(name="NotesLeft", parent=styles["Normal"], fontSize=10, textColor=colors.grey)

        discount = formatted_data["discount"]
        tax = formatted_data["tax"]
        total = formatted_data["total"]
        summary_text = f"Discount: GH¢ {discount}<br/>" f"Tax: GH¢ {tax}<br/>" f"<b>Total: GH¢ {total}</b>"
        thank_you, notes = Invoice.get_receipt_texts()
        notes_para = Paragraph(notes or "", notes_style)
        summary_para = Paragraph(summary_text, summary_right)

        summary_notes_table = Table(
            [[notes_para, summary_para]],
            colWidths=[100 * mm, 70 * mm],
            hAlign="LEFT",
        )
        summary_notes_table.setStyle(
            TableStyle(
                [
                    ("VALIGN", (0, 0), (-1, -1), "TOP"),
                    ("LEFTPADDING", (0, 0), (0, 0), 0),
                    ("RIGHTPADDING", (-1, 0), (-1, 0), 0),
                    ("TOPPADDING", (0, 0), (-1, -1), 0),
                    ("BOTTOMPADDING", (0, 0), (-1, -1), 0),
                ]
            )
        )
        elements.append(summary_notes_table)
        elements.append(Spacer(1, 30))

        # Footer thank-you centered
        footer_style = ParagraphStyle(
            name="Footer",
            parent=styles["Normal"],
            alignment=1,
            fontSize=11,
            textColor=colors.grey,
            spaceBefore=20,
        )
        elements.append(Paragraph(thank_you, footer_style))

        doc.build(elements)
