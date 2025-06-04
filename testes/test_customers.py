import unittest
from models.customer import Customer
from database.db_handler import get_db_connection

class TestCustomerModel(unittest.TestCase):
    def setUp(self):
        # Clear customers table before each test
        connection = get_db_connection()
        cursor = connection.cursor()
        cursor.execute("DELETE FROM customers")
        connection.commit()
        connection.close()

    def test_add_and_get_customers(self):
        Customer.add_customer("Alice", "123456789", "Wonderland")
        Customer.add_customer("Bob", "987654321", "Dreamland")
        customers = Customer.get_all_customers()
        self.assertEqual(len(customers), 2)
        self.assertEqual(customers[0].name, "Alice")
        self.assertEqual(customers[1].name, "Bob")

    def test_update_customer(self):
        Customer.add_customer("Charlie", "111222333", "Nowhere")
        customers = Customer.get_all_customers()
        customer_id = customers[0].customer_id

        Customer.update_customer(customer_id, "Charles", "999888777", "Somewhere")
        updated = Customer.get_customer_by_id(customer_id)

        self.assertEqual(updated.name, "Charles")
        self.assertEqual(updated.phone_number, "999888777")
        self.assertEqual(updated.address, "Somewhere")

    def test_delete_customer(self):
        Customer.add_customer("Daisy", "000111222", "Meadow")
        customers = Customer.get_all_customers()
        customer_id = customers[0].customer_id

        Customer.delete_customer(customer_id)
        remaining_customers = Customer.get_all_customers()
        self.assertEqual(len(remaining_customers), 0)

if __name__ == '__main__':
    unittest.main()
