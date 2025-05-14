import sqlite3
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
        """, (customer_id,))
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
        """, (customer_id,))
        row = cursor.fetchone()
        connection.close()
        return Customer(*row) if row else None

    @staticmethod
    def get_customer_purchase_history(customer_id):
        connection = get_db_connection()
        cursor = connection.cursor()
        cursor.execute("""
            SELECT o.order_id, o.order_date, o.total_amount
            FROM orders o
            WHERE o.customer_id = ?
            ORDER BY o.order_date DESC
        """, (customer_id,))
        history = cursor.fetchall()
        connection.close()
        return history
