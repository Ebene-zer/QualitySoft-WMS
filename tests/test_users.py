import unittest
from models.user import User
from tests.base_test import BaseTestCase

class TestUserModel(BaseTestCase):
    def test_add_and_get_users(self):
        self.log("Adding users.")
        User.add_user("admin", "pass", "Admin")
        User.add_user("ceo", "pass", "CEO")
        users = User.get_all_users()
        self.assertGreaterEqual(len(users), 2)
        usernames = {u.username for u in users}
        self.assertIn("admin", usernames)
        self.assertIn("ceo", usernames)

    def test_update_user_by_username(self):
        User.add_user("manager", "pass", "Manager")
        self.assertIsNotNone(User.authenticate("manager", "pass"))
        User.update_user("manager", "manager2", "newpass", "Manager")
        # Old username should fail
        self.assertIsNone(User.authenticate("manager", "pass"))
        # New username + password should pass
        self.assertIsNotNone(User.authenticate("manager2", "newpass"))

    def test_authenticate_success_and_failure(self):
        User.add_user("user1", "secret", "Manager")
        self.assertIsNotNone(User.authenticate("user1", "secret"))
        self.assertIsNone(User.authenticate("user1", "wrong"))
        self.assertIsNone(User.authenticate("ghost", "secret"))

    def test_delete_user(self):
        User.add_user("temp", "pass", "Staff")
        self.assertIsNotNone(User.authenticate("temp", "pass"))
        User.delete_user("temp")
        self.assertIsNone(User.authenticate("temp", "pass"))

if __name__ == '__main__':
    unittest.main()
