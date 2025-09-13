from database.db_handler import get_db_connection
#Customer Class
class Customer:
    def __init__(self, customer_id, name, phone_number, address):
        self.customer_id = customer_id
        self.name = name
        self.phone_number = phone_number
        self.address = address

#Add customer method/function
    @staticmethod
    def add_customer(name, phone_number, address):
        # Model-level validation
        if not name or not name.strip():
            raise ValueError("Customer name is required.")
        if not address or not address.strip():
            raise ValueError("Address is required.")
        if phone_number and not (phone_number.isdigit() and len(phone_number) == 10):
            raise ValueError("Phone number must be 10 digits.")
        connection = get_db_connection()
        cursor = connection.cursor()
        cursor.execute("""
            INSERT INTO customers (name, phone_number, address)
            VALUES (?, ?, ?)
        """, (name, phone_number, address))
        connection.commit()
        connection.close()

#Update existing customer's details
    @staticmethod
    def update_customer(customer_id, name, phone_number, address):
        # Model-level validation
        if not name or not name.strip():
            raise ValueError("Customer name is required.")
        if not address or not address.strip():
            raise ValueError("Address is required.")
        if phone_number and not (phone_number.isdigit() and len(phone_number) == 10):
            raise ValueError("Phone number must be 10 digits.")
        connection = get_db_connection()
        cursor = connection.cursor()
        cursor.execute("""
            UPDATE customers
            SET name = ?, phone_number = ?, address = ?
            WHERE customer_id = ?
        """, (name, phone_number, address, customer_id))
        connection.commit()
        connection.close()

#Delete a customer
    @staticmethod
    def delete_customer(customer_id):
        connection = get_db_connection()
        cursor = connection.cursor()
        cursor.execute("""
            DELETE FROM customers
            WHERE customer_id = ?
        """, (customer_id,))
        connection.commit()
        connection.close()

#Get all customers
    @staticmethod
    def get_all_customers():
        connection = get_db_connection()
        cursor = connection.cursor()
        # Return customers ordered A-Z by name (case-insensitive)
        cursor.execute("""
            SELECT customer_id, name, phone_number, address FROM customers
            ORDER BY name COLLATE NOCASE
        """)
        rows = cursor.fetchall()
        connection.close()
        return [Customer(*row) for row in rows]

#Get a customer by ID
    @staticmethod
    def get_customer_by_id(customer_id):
        connection = get_db_connection()
        cursor = connection.cursor()
        cursor.execute("""
            SELECT customer_id, name, phone_number, address FROM customers
            WHERE customer_id = ?
        """, (customer_id,))
        row = cursor.fetchone()
        connection.close()
        return Customer(*row) if row else None

#Customer's purchase history
    @staticmethod
    def get_customer_purchase_history(customer_id):
        connection = get_db_connection()
        cursor = connection.cursor()
        cursor.execute("""
            SELECT invoice_id, invoice_date, total_amount
            FROM invoices
            WHERE customer_id = ?
            ORDER BY invoice_date DESC
        """, (customer_id,))
        history = cursor.fetchall()
        connection.close()
        return history
