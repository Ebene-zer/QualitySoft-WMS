import sqlite3
import os

DB_NAME = os.environ.get("WMS_DB_NAME", "wholesale.db")

def get_db_connection(db_name=None):
    if db_name is None:
        db_name = DB_NAME
    connection = sqlite3.connect(db_name, timeout=10)
    return connection

def initialize_database():
    connection = get_db_connection()
    cursor = connection.cursor()

    # Create products table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS products (
            product_id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            price REAL NOT NULL,
            stock_quantity INTEGER NOT NULL
        )
    """)

    # Create customers table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS customers (
            customer_id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            phone_number TEXT CHECK (LENGTH(phone_number) = 10),
            address TEXT
        )
    """)

    # Create invoices table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS invoices (
            invoice_id INTEGER PRIMARY KEY AUTOINCREMENT,
            customer_id INTEGER NOT NULL,
            invoice_date TEXT NOT NULL,
            discount REAL DEFAULT 0,
            tax REAL DEFAULT 0,
            total_amount REAL NOT NULL,
            FOREIGN KEY (customer_id) REFERENCES customers(customer_id)
        )
    """)

    # Create invoice_items table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS invoice_items (
            item_id INTEGER PRIMARY KEY AUTOINCREMENT,
            invoice_id INTEGER NOT NULL,
            product_id INTEGER NOT NULL,
            quantity INTEGER NOT NULL,
            unit_price REAL NOT NULL,
            FOREIGN KEY (invoice_id) REFERENCES invoices(invoice_id),
            FOREIGN KEY (product_id) REFERENCES products(product_id)
        )
    """)

    # Create users table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            user_id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL,
            role TEXT NOT NULL DEFAULT 'admin'
        )
    """)

    # Create license table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS license (
            id INTEGER PRIMARY KEY,
            trial_start TEXT,
            product_pin TEXT,
            trial_days INTEGER
        )
    """)
    # Insert default license row if not exists
    cursor.execute("SELECT COUNT(*) FROM license")
    if cursor.fetchone()[0] == 0:
        cursor.execute("INSERT INTO license (id, trial_start, product_pin, trial_days) VALUES (1, DATE('now'), '', 14)")

    # Create settings table for wholesale number
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS settings (
            id INTEGER PRIMARY KEY,
            wholesale_number TEXT
        )
    """)
    # Insert default wholesale number if not exists
    cursor.execute("SELECT COUNT(*) FROM settings")
    if cursor.fetchone()[0] == 0:
        cursor.execute("INSERT INTO settings (id, wholesale_number) VALUES (1, '')")

    connection.commit()
    connection.close()
