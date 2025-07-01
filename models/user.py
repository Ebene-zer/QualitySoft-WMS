import hashlib
import os
from database.db_handler import get_db_connection

class User:
    @staticmethod
    def hash_password(password, salt=None):
        if salt is None:
            salt = os.urandom(16)
        pwd_hash = hashlib.pbkdf2_hmac(
            'sha256',
            password.encode('utf-8'),
            salt,
            100_000
        )
        return salt.hex() + pwd_hash.hex()

    @staticmethod
    def verify_password(stored_password_hash, password_attempt):
        salt_hex = stored_password_hash[:32]
        hash_hex = stored_password_hash[32:]

        salt = bytes.fromhex(salt_hex)
        attempt_hash = hashlib.pbkdf2_hmac(
            'sha256',
            password_attempt.encode('utf-8'),
            salt,
            100_000
        )
        return attempt_hash.hex() == hash_hex

    @staticmethod
    def add_user(username, password, role):
        from database.db_handler import get_db_connection
        import sqlite3

        connection = get_db_connection()
        cursor = connection.cursor()

        password_hash = User.hash_password(password)  # Use the correct hashing method

        try:
            cursor.execute("""
                INSERT INTO users (username, password_hash, role)
                VALUES (?, ?, ?)
            """, (username, password_hash, role))
            connection.commit()
        except sqlite3.IntegrityError as e:
            connection.rollback()
            raise e
        finally:
            connection.close()

    @staticmethod
    def authenticate(username, password):
        try:
            connection = get_db_connection()
            cursor = connection.cursor()
            cursor.execute("SELECT password_hash, role FROM users WHERE username = ?", (username,))
            result = cursor.fetchone()
            connection.close()

            if result:
                stored_hash, stored_role = result
                if User.verify_password(stored_hash, password):
                    return stored_role  # Return role if authentication succeeds
            return None  # Authentication failed
        except Exception as e:
            print(f"Authentication error: {e}")
            return None

    @staticmethod
    def get_user_role(username):
        connection = get_db_connection()
        cursor = connection.cursor()
        cursor.execute("""
            SELECT role FROM users WHERE username = ?
        """, (username,))
        result = cursor.fetchone()
        connection.close()

        if result:
            return result[0]
        return None

    @staticmethod
    def user_exists(username):
        connection = get_db_connection()
        cursor = connection.cursor()
        cursor.execute("SELECT 1 FROM users WHERE username = ?", (username,))
        result = cursor.fetchone()
        connection.close()
        return result is not None
