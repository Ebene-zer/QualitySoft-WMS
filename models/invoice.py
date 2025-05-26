from datetime import datetime
from database.db_handler import get_db_connection
from models.product import Product


class Invoice:
    def __init__(self, invoice_id, customer_id, invoice_date, discount, tax, total_amount):
        self.invoice_id = invoice_id
        self.customer_id = customer_id
        self.invoice_date = invoice_date
        self.discount = discount
        self.tax = tax
        self.total_amount = total_amount

    @staticmethod
    def create_invoice(customer_id, items, discount=0.0, tax=0.0):
        connection = get_db_connection()
        cursor = connection.cursor()

        subtotal = sum(item['quantity'] * item['unit_price'] for item in items)
        total_after_discount = subtotal - discount + tax
        invoice_date = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

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

    @staticmethod
    def get_all_invoices():
        connection = get_db_connection()
        cursor = connection.cursor()

        cursor.execute("""
            SELECT i.invoice_id, c.name, i.invoice_date, i.discount, i.tax, i.total_amount
            FROM invoices i
            JOIN customers c ON i.customer_id = c.customer_id
            ORDER BY i.invoice_date DESC
        """)
        rows = cursor.fetchall()
        connection.close()

        invoices = []
        for row in rows:
            invoices.append({
                "invoice_id": row[0],
                "customer_name": row[1],
                "invoice_date": row[2],
                "discount": row[3],
                "tax": row[4],
                "total_amount": row[5]
            })

        return invoices

    @staticmethod
    def get_invoice_by_id(invoice_id):
        connection = get_db_connection()
        cursor = connection.cursor()

        cursor.execute("""
            SELECT i.invoice_id, c.name, i.invoice_date, i.discount, i.tax, i.total_amount
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
    def print_receipt(invoice_id):
        invoice = Invoice.get_invoice_by_id(invoice_id)
        if not invoice:
            raise ValueError(f"Invoice ID {invoice_id} not found.")

        print(f"\n--- Invoice #{invoice['invoice_id']} ---")
        print(f"Date: {invoice['invoice_date']}")
        print(f"Customer: {invoice['customer_name']}")
        print(f"Discount: GHS {invoice['discount']}")
        print(f"Tax: GHS {invoice['tax']}")
        print(f"Total: GHS {invoice['total_amount']}")
        print("Items:")
        for item in invoice['items']:
            print(f" Product: {item['product_name']} | Quantity: {item['quantity']} | Unit Price: GHS {item['unit_price']}")
        print("-----------------------------\n")


    @staticmethod
    def export_receipt_to_pdf(invoice_id, output_path):
        from reportlab.lib.pagesizes import A4
        from reportlab.pdfgen import canvas

        invoice = Invoice.get_invoice_by_id(invoice_id)
        if not invoice:
            raise ValueError(f"Invoice ID {invoice_id} not found.")

        c = canvas.Canvas(output_path, pagesize=A4)
        width, height = A4

        y = height - 50

        c.setFont("Helvetica-Bold", 18)
        c.drawString(50, y, f"Invoice #{invoice['invoice_id']}")
        y -= 30

        c.setFont("Helvetica", 12)
        c.drawString(50, y, f"Date: {invoice['invoice_date']}")
        y -= 20
        c.drawString(50, y, f"Customer: {invoice['customer_name']}")
        y -= 30

        c.setFont("Helvetica-Bold", 14)
        c.drawString(50, y, "Items:")
        y -= 20

        c.setFont("Helvetica", 12)
        for item in invoice['items']:
            c.drawString(60, y, f"{item['product_name']} x {item['quantity']} @ GHS {item['unit_price']}")
            y -= 20
            if y < 50:
                c.showPage()
                y = height - 50

        y -= 10
        c.setFont("Helvetica-Bold", 12)
        c.drawString(50, y, f"Discount: GHS {invoice['discount']}")
        y -= 20
        c.drawString(50, y, f"Tax: GHS {invoice['tax']}")
        y -= 20
        c.drawString(50, y, f"Total: GHS {invoice['total_amount']}")
        y -= 30

        c.drawString(50, y, "Thank you for buying from us!")

        c.save()

