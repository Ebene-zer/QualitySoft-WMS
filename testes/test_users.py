import unittest
from models.user import User
from database.db_handler import initialize_database

initialize_database()


class TestUserModel(unittest.TestCase):
    def setUp(self):
        # Clear users table before each test
        connection = initialize_database()
        cursor = connection.cursor()
        cursor.execute("DELETE FROM users")
        connection.commit()
        connection.close()

    def test_add_and_authenticate_user(self):
        User.add_user("testuser", "securepassword", "Admin")
        user = User.authenticate("testuser", "securepassword")
        self.assertIsNotNone(user)
        self.assertEqual(user.username, "testuser")
        self.assertEqual(user.role, "Admin")

    def test_wrong_password_authentication(self):
        User.add_user("testuser", "securepassword", "admin")
        user = User.authenticate("testuser", "wrongpassword")
        self.assertIsNone(user)

    def test_duplicate_username(self):
        User.add_user("testuser", "password1", "admin")
        with self.assertRaises(Exception):
            User.add_user("testuser", "password2", "user")

if __name__ == '__main__':
    unittest.main()
