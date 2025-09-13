from database.db_handler import get_db_connection
# The product class
class Product:
    def __init__(self, product_id, name, price, stock_quantity):
        self.product_id = product_id
        self.name = name
        self.price = price
        self.stock_quantity = stock_quantity

#Add products method/function
    @staticmethod
    def add_product(name, price, stock_quantity):
        connection = get_db_connection()
        cursor = connection.cursor()
        cursor.execute("""
            INSERT INTO products (name, price, stock_quantity)
            VALUES (?, ?, ?)
        """, (name, price, stock_quantity))
        connection.commit()
        connection.close()

#Update products details method
    @staticmethod
    def update_product(product_id, name, price, stock_quantity):
        connection = get_db_connection()
        cursor = connection.cursor()
        cursor.execute("""
            UPDATE products
            SET name = ?, price = ?, stock_quantity = ?
            WHERE product_id = ?
        """, (name, price, stock_quantity, product_id))
        connection.commit()
        connection.close()

#Delete products
    @staticmethod
    def delete_product(product_id):
        connection = get_db_connection()
        cursor = connection.cursor()
        cursor.execute("""
            DELETE FROM products
            WHERE product_id = ?
        """, (product_id,))
        connection.commit()
        connection.close()

#Get all existing products
    @staticmethod
    def get_all_products():
        connection = get_db_connection()
        cursor = connection.cursor()
        # Return products ordered A-Z by name (case-insensitive)
        cursor.execute("""
            SELECT product_id, name, price, stock_quantity
            FROM products
            ORDER BY name COLLATE NOCASE
        """)
        rows = cursor.fetchall()
        connection.close()
        return [Product(*row) for row in rows]

#Get product using product ID
    @staticmethod
    def get_product_by_id(product_id):
        connection = get_db_connection()
        cursor = connection.cursor()
        cursor.execute("""
            SELECT product_id, name, price, stock_quantity 
            FROM products
            WHERE product_id = ?
        """, (product_id,))
        row = cursor.fetchone()
        connection.close()
        return Product(*row) if row else None


#Update stock quantity upon adding/deleting product
    @staticmethod
    def update_stock(product_id, new_quantity, connection=None):
        own_connection = False
        if connection is None:
            connection = get_db_connection()
            own_connection = True

        cursor = connection.cursor()
        cursor.execute("""
            UPDATE products
            SET stock_quantity = ?
            WHERE product_id = ?
        """, (new_quantity, product_id))

        if own_connection:
            connection.commit()
            connection.close()

#Check for low stock quantity
    @staticmethod
    def get_products_below_stock(threshold):
        connection = get_db_connection()
        cursor = connection.cursor()
        cursor.execute("""
            SELECT product_id, name, price, stock_quantity FROM products
            WHERE stock_quantity <= ?
        """, (threshold,))
        rows = cursor.fetchall()
        connection.close()
        return [Product(*row) for row in rows]

