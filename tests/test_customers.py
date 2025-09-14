import unittest
from models.customer import Customer
from testes.base_test import BaseTestCase

class TestCustomerModel(BaseTestCase):
    def test_add_and_get_customers(self):
        self.log("Adding customers Alice and Bob.")
        Customer.add_customer("Alice", "0123456789", "Wonderland")
        Customer.add_customer("Bob", "9876543210", "Dreamland")
        customers = Customer.get_all_customers()
        self.log(f"Total customers: {len(customers)}")
        self.assertListNotEmpty(customers)
        names = {c.name for c in customers}
        self.assertIn("Alice", names)
        self.assertIn("Bob", names)

    def test_update_customer(self):
        self.log("Adding customer Charlie.")
        Customer.add_customer("Charlie", "1112223334", "Nowhere")
        customers = Customer.get_all_customers()
        customer_id = customers[0].customer_id
        self.log(f"Updating customer {customer_id}.")
        Customer.update_customer(customer_id, "Charles", "9998887776", "Somewhere")
        updated = Customer.get_customer_by_id(customer_id)
        self.assertEqual(updated.name, "Charles")
        self.assertEqual(updated.phone_number, "9998887776")
        self.assertEqual(updated.address, "Somewhere")

    def test_delete_customer(self):
        self.log("Adding customer Daisy.")
        Customer.add_customer("Daisy", "0001112223", "Meadow")
        customers = Customer.get_all_customers()
        customer_id = customers[0].customer_id
        self.log(f"Deleting customer {customer_id}.")
        Customer.delete_customer(customer_id)
        remaining_customers = Customer.get_all_customers()
        self.log(f"Remaining customers: {len(remaining_customers)}")
        self.assertEqual(len(remaining_customers), 0)

if __name__ == '__main__':
    unittest.main()
