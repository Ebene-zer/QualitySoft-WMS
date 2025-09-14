from models.product import Product


class TestProductModel:
    def test_add_and_get_products(self):
        Product.add_product("Soap", 2.5, 100)
        Product.add_product("Brush", 1.0, 50)
        products = Product.get_all_products()
        assert len(products) > 0
        names = {p.name for p in products}
        assert names == {"Soap", "Brush"}

    def test_update_product(self):
        Product.add_product("Toothpaste", 3.0, 30)
        products = Product.get_all_products()
        product_id = products[0].product_id
        Product.update_product(product_id, "Toothpaste Max", 3.5, 25)
        updated = Product.get_product_by_id(product_id)
        assert updated.name == "Toothpaste Max"
        assert updated.price == 3.5
        assert updated.stock_quantity == 25

    def test_delete_product(self):
        Product.add_product("Shampoo", 5.0, 20)
        products = Product.get_all_products()
        product_id = products[0].product_id
        Product.delete_product(product_id)
        remaining_products = Product.get_all_products()
        assert len(remaining_products) == 0

    def test_get_products_below_stock(self):
        Product.add_product("ItemA", 1.0, 5)
        Product.add_product("ItemB", 1.0, 2)
        Product.add_product("ItemC", 1.0, 10)
        low = Product.get_products_below_stock(5)
        names = {p.name for p in low}
        assert "ItemA" in names
        assert "ItemB" in names
        assert "ItemC" not in names
