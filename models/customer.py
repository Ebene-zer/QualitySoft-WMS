from database.db_handler import get_db_connection

class Customer:
    def __init__(self, customer_id, name, phone_number, address):
        self.customer_id = customer_id
        self.name = name
        self.phone_number = phone_number
        self.address = address

    @staticmethod
    def add_customer(name, phone_number, address):
        connection = get_db_connection()
        cursor = connection.cursor()
        cursor.execute("""
            INSERT INTO customers (name, phone_number, address)
            VALUES (?, ?, ?)
        """, (name, phone_number, address))
        connection.commit()
        connection.close()

    @staticmethod
    def update_customer(customer_id, name, phone_number, address):
        connection = get_db_connection()
        cursor = connection.cursor()
        cursor.execute("""
            UPDATE customers
            SET name = ?, phone_number = ?, address = ?
            WHERE customer_id = ?
        """, (name, phone_number, address, customer_id))
        connection.commit()
        connection.close()

    @staticmethod
    def delete_customer(customer_id):
        connection = get_db_connection()
        cursor = connection.cursor()
        cursor.execute("""
            DELETE FROM customers
            WHERE customer_id = ?
        """, (customer_id,))  # <-- tuple!
        connection.commit()
        connection.close()

    @staticmethod
    def get_all_customers():
        connection = get_db_connection()
        cursor = connection.cursor()
        cursor.execute("""
            SELECT customer_id, name, phone_number, address FROM customers
        """)
        rows = cursor.fetchall()
        connection.close()
        customers = [Customer(*row) for row in rows]
        return customers

    @staticmethod
    def get_customer_by_id(customer_id):
        connection = get_db_connection()
        cursor = connection.cursor()
        cursor.execute("""
            SELECT customer_id, name, phone_number, address FROM customers
            WHERE customer_id = ?
        """, (customer_id,))  # <-- tuple!
        row = cursor.fetchone()
        connection.close()
        return Customer(*row) if row else None

    @staticmethod
    def get_customer_purchase_history(customer_id):
        connection = get_db_connection()
        cursor = connection.cursor()
        cursor.execute("""
            SELECT o.invoice_id, o.invoice_date, o.total_amount
            FROM invoices o
            WHERE o.customer_id = ?
            ORDER BY o.invoice_date DESC
        """, (customer_id,))  # <-- tuple!
        history = cursor.fetchall()
        connection.close()
        return history
