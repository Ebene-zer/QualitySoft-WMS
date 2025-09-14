from models.customer import Customer


class TestCustomerModel:
    def test_add_and_get_customers(self):
        Customer.add_customer("Alice", "0123456789", "Wonderland")
        Customer.add_customer("Bob", "9876543210", "Dreamland")
        customers = Customer.get_all_customers()
        assert len(customers) > 0
        names = {c.name for c in customers}
        assert "Alice" in names
        assert "Bob" in names

    def test_update_customer(self):
        Customer.add_customer("Charlie", "1112223334", "Nowhere")
        customers = Customer.get_all_customers()
        customer_id = customers[0].customer_id
        Customer.update_customer(customer_id, "Charles", "9998887776", "Somewhere")
        updated = Customer.get_customer_by_id(customer_id)
        assert updated.name == "Charles"
        assert updated.phone_number == "9998887776"
        assert updated.address == "Somewhere"

    def test_delete_customer(self):
        Customer.add_customer("Daisy", "0001112223", "Meadow")
        customers = Customer.get_all_customers()
        customer_id = customers[0].customer_id
        Customer.delete_customer(customer_id)
        remaining_customers = Customer.get_all_customers()
        assert len(remaining_customers) == 0
