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


   # #Print Receipt Method
   #  @staticmethod
   #  def print_receipt(invoice_id):
   #      invoice = Invoice.get_invoice_by_id(invoice_id)
   #      if not invoice:
   #          raise ValueError(f"Invoice ID {invoice_id} not found.")
   #
   #      #Receipt Details
   #      print(f"\n--- Invoice #{invoice['invoice_id']} ---")
   #      print(f"Date: {invoice['invoice_date']}")
   #      print(f"Customer: {invoice['customer_name']}")
   #      print(f"Discount: GHS {invoice['discount']}")
   #      print(f"Tax: GHS {invoice['tax']}")
   #      print(f"Total: GHS {invoice['total_amount']}")
   #      print("Items:")
   #      for item in invoice['items']:
   #          print(f" Product: {item['product_name']} | Quantity: {item['quantity']} | Unit Price: GHS {item['unit_price']}")
   #      print("-----------------------------\n")
   #
   #
   #  #Export receipt to PDF
   #  @staticmethod
   #  def export_receipt_to_pdf(invoice_id, output_path):
   #      from reportlab.lib.pagesizes import A4
   #      from reportlab.pdfgen import canvas
   #      from reportlab.platypus import Table, TableStyle
   #      from reportlab.lib import colors
   #
   #      invoice = Invoice.get_invoice_by_id(invoice_id)
   #      if not invoice:
   #          raise ValueError(f"Invoice ID {invoice_id} not found.")
   #
   #      c = canvas.Canvas(output_path, pagesize=A4)
   #      width, height = A4
   #      y = height - 50
   #
   #      # Header
   #      c.setFont("Helvetica-Bold", 20)
   #      c.drawString(50, y, "Wholesale Name Here")
   #      y -= 30
   #
   #      c.setFont("Helvetica-Bold", 16)
   #      c.drawString(50, y, f"Invoice #{invoice['invoice_id']}")
   #      y -= 25
   #
   #      c.setFont("Helvetica", 12)
   #      c.drawString(50, y, f"Date: {invoice['invoice_date']}")
   #      y -= 18
   #      c.drawString(50, y, f"Customer: {invoice['customer_name']}")
   #      y -= 25
   #
   #      # Table headers and data
   #      table_data = [["Product", "Quantity", "Unit Price (GHS)", "Subtotal (GHS)"]]
   #      for item in invoice['items']:
   #          subtotal = item['quantity'] * item['unit_price']
   #          table_data.append([
   #              item['product_name'],
   #              str(item['quantity']),
   #              f"{item['unit_price']:.2f}",
   #              f"{subtotal:.2f}"
   #          ])
   #
   #      table = Table(table_data, colWidths=[180, 80, 100, 100])
   #      table.setStyle(TableStyle([
   #          ('BACKGROUND', (0, 0), (-1, 0), colors.darkblue),
   #          ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
   #          ('ALIGN', (1, 0), (-1, -1), 'CENTER'),
   #          ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
   #          ('FONTSIZE', (0, 0), (-1, 0), 12),
   #          ('BOTTOMPADDING', (0, 0), (-1, 0), 8),
   #          ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
   #      ]))
   #
   #      table.wrapOn(c, width, height)
   #      table_height = table._height
   #      table.drawOn(c, 50, y - table_height)
   #      y -= table_height + 20
   #
   #      # Totals
   #      c.setFont("Helvetica-Bold", 12)
   #      c.drawString(50, y, f"Discount: GHS {invoice['discount']:.2f}")
   #      y -= 18
   #      c.drawString(50, y, f"Tax: GHS {invoice['tax']:.2f}")
   #      y -= 18
   #      c.drawString(50, y, f"Total: GHS {invoice['total_amount']:.2f}")
   #      y -= 30
   #
   #      # Footer
   #      c.setFont("Helvetica-Oblique", 10)
   #      c.setFillColor(colors.darkgray)
   #      c.drawString(50, 30, "Thank you for buying from us!")
   #
   #      c.save()
