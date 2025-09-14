import unittest
from models.product import Product
from tests.base_test import BaseTestCase

class TestProductModel(BaseTestCase):
    def test_add_and_get_products(self):
        self.log("Adding products.")
        Product.add_product("Soap", 2.5, 100)
        Product.add_product("Brush", 1.0, 50)
        products = Product.get_all_products()
        self.log(f"Total products: {len(products)}")
        self.assertListNotEmpty(products)
        names = {p.name for p in products}
        self.assertSetEqual(names, {"Soap", "Brush"})

    def test_update_product(self):
        self.log("Adding product Toothpaste.")
        Product.add_product("Toothpaste", 3.0, 30)
        products = Product.get_all_products()
        product_id = products[0].product_id
        self.log(f"Updating product {product_id}.")
        Product.update_product(product_id, "Toothpaste Max", 3.5, 25)
        updated = Product.get_product_by_id(product_id)
        self.assertDictContains(updated.__dict__, ["name", "price", "stock_quantity"])
        self.assertEqual(updated.name, "Toothpaste Max")
        self.assertEqual(updated.price, 3.5)
        self.assertEqual(updated.stock_quantity, 25)

    def test_delete_product(self):
        self.log("Adding product Shampoo.")
        Product.add_product("Shampoo", 5.0, 20)
        products = Product.get_all_products()
        product_id = products[0].product_id
        self.log(f"Deleting product {product_id}.")
        Product.delete_product(product_id)
        remaining_products = Product.get_all_products()
        self.log(f"Remaining products: {len(remaining_products)}")
        self.assertEqual(len(remaining_products), 0)

    def test_get_products_below_stock(self):
        Product.add_product("ItemA", 1.0, 5)
        Product.add_product("ItemB", 1.0, 2)
        Product.add_product("ItemC", 1.0, 10)
        low = Product.get_products_below_stock(5)
        names = {p.name for p in low}
        self.assertIn("ItemA", names)
        self.assertIn("ItemB", names)
        self.assertNotIn("ItemC", names)

if __name__ == '__main__':
    unittest.main()
