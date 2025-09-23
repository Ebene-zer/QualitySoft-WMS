from database.db_handler import get_db_connection
from utils.activity_log import log_action
from utils.session import get_current_username


# The product class
class Product:
    def __init__(self, product_id, name, price, stock_quantity):
        self.product_id = product_id
        self.name = name
        self.price = price
        self.stock_quantity = stock_quantity

    @staticmethod
    def _name_exists(name: str, exclude_id: int | None = None) -> bool:
        """Return True if a product with the same name exists (case-insensitive).
        Optionally exclude a given product_id.
        """
        connection = get_db_connection()
        cursor = connection.cursor()
        if exclude_id is None:
            cursor.execute(
                """
                SELECT 1 FROM products
                WHERE name = ? COLLATE NOCASE
                LIMIT 1
            """,
                (name,),
            )
        else:
            cursor.execute(
                """
                SELECT 1 FROM products
                WHERE name = ? COLLATE NOCASE AND product_id != ?
                LIMIT 1
            """,
                (name, exclude_id),
            )
        row = cursor.fetchone()
        connection.close()
        return row is not None

    # Add products method/function
    @staticmethod
    def add_product(name, price, stock_quantity):
        # Prevent duplicate names (case-insensitive)
        if Product._name_exists(name):
            raise ValueError("Product already exists.\n" "You may want to update the existing product instead.")
        connection = get_db_connection()
        cursor = connection.cursor()
        cursor.execute(
            """
            INSERT INTO products (name, price, stock_quantity)
            VALUES (?, ?, ?)
        """,
            (name, price, stock_quantity),
        )
        new_id = cursor.lastrowid
        connection.commit()
        connection.close()
        try:
            log_action(get_current_username(), "PRODUCT_ADD", f"{name} qty={stock_quantity} price={price}")
        except Exception:
            pass
        return new_id

    # Update products details method
    @staticmethod
    def update_product(product_id, name, price, stock_quantity):
        connection = get_db_connection()
        cursor = connection.cursor()
        cursor.execute(
            """
            UPDATE products
            SET name = ?, price = ?, stock_quantity = ?
            WHERE product_id = ?
        """,
            (name, price, stock_quantity, product_id),
        )
        connection.commit()
        connection.close()
        try:
            log_action(
                get_current_username(),
                "PRODUCT_UPDATE",
                f"id={product_id} -> {name} qty={stock_quantity} price={price}",
            )
        except Exception:
            pass

    # Delete products
    @staticmethod
    def delete_product(product_id):
        connection = get_db_connection()
        cursor = connection.cursor()
        cursor.execute(
            """
            DELETE FROM products
            WHERE product_id = ?
        """,
            (product_id,),
        )
        connection.commit()
        connection.close()
        try:
            log_action(get_current_username(), "PRODUCT_DELETE", f"id={product_id}")
        except Exception:
            pass

    # Get all existing products
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

    # Get product using product ID
    @staticmethod
    def get_product_by_id(product_id):
        connection = get_db_connection()
        cursor = connection.cursor()
        cursor.execute(
            """
            SELECT product_id, name, price, stock_quantity
            FROM products
            WHERE product_id = ?
        """,
            (product_id,),
        )
        row = cursor.fetchone()
        connection.close()
        return Product(*row) if row else None

    # Update stock quantity upon adding/deleting product
    @staticmethod
    def update_stock(product_id, new_quantity, connection=None):
        own_connection = False
        if connection is None:
            connection = get_db_connection()
            own_connection = True

        cursor = connection.cursor()
        cursor.execute(
            """
            UPDATE products
            SET stock_quantity = ?
            WHERE product_id = ?
        """,
            (new_quantity, product_id),
        )

        if own_connection:
            connection.commit()
            connection.close()

    # Check for low stock quantity
    @staticmethod
    def get_products_below_stock(threshold):
        connection = get_db_connection()
        cursor = connection.cursor()
        cursor.execute(
            """
            SELECT product_id, name, price, stock_quantity FROM products
            WHERE stock_quantity <= ?
        """,
            (threshold,),
        )
        rows = cursor.fetchall()
        connection.close()
        return [Product(*row) for row in rows]
