import unittest
import sqlite3
from models.user import User
from database.db_handler import get_db_connection, initialize_database

class TestUserModel(unittest.TestCase):
    def setUp(self):
        # Ensure database and tables exist
        initialize_database()
        connection = get_db_connection()
        cursor = connection.cursor()
        cursor.execute("DELETE FROM users")
        connection.commit()
        connection.close()

    def test_add_and_authenticate_user(self):
        User.add_user("testuser", "securepassword", "Admin")
        role = User.authenticate("testuser", "securepassword")
        self.assertIsNotNone(role)
        self.assertEqual(role, "Admin")

    def test_wrong_password_authentication(self):
        User.add_user("testuser", "securepassword", "Admin")
        role = User.authenticate("testuser", "wrongpassword")
        self.assertIsNone(role)

    def test_duplicate_username(self):
        User.add_user("testuser", "password1", "Admin")
        with self.assertRaises(sqlite3.IntegrityError):
            User.add_user("testuser", "password2", "Manager")

if __name__ == '__main__':
    unittest.main()
# This code is a unit test for the User model in a Python application.