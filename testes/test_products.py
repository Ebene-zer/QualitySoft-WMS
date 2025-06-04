import unittest
from models.product import Product
from database.db_handler import get_db_connection

class TestProductModel(unittest.TestCase):
    def setUp(self):
        # Clear products table before each test
        connection = get_db_connection()
        cursor = connection.cursor()
        cursor.execute("DELETE FROM products")
        connection.commit()
        connection.close()

    def test_add_and_get_products(self):
        Product.add_product("Laptop", 1000.0, 10)
        Product.add_product("Phone", 500.0, 20)
        products = Product.get_all_products()

        self.assertEqual(len(products), 2)
        self.assertEqual(products[0].name, "Laptop")
        self.assertEqual(products[1].stock_quantity, 20)

    def test_update_product(self):
        Product.add_product("Tablet", 300.0, 5)
        products = Product.get_all_products()
        product_id = products[0].product_id

        Product.update_product(product_id, "Tablet Pro", 400.0, 8)
        updated = Product.get_product_by_id(product_id)

        self.assertEqual(updated.name, "Tablet Pro")
        self.assertEqual(updated.price, 400.0)
        self.assertEqual(updated.stock_quantity, 8)

    def test_delete_product(self):
        Product.add_product("Headphones", 150.0, 12)
        products = Product.get_all_products()
        product_id = products[0].product_id

        Product.delete_product(product_id)
        remaining_products = Product.get_all_products()

        self.assertEqual(len(remaining_products), 0)

if __name__ == '__main__':
    unittest.main()
