import hashlib
import os
from database.db_handler import get_db_connection

class User:
    @staticmethod
    def hash_password(password, salt=None):
        if salt is None:
            salt = os.urandom(16)  # 16-byte salt

        # Use PBKDF2 with SHA256, 100,000 iterations (slow hashing)
        pwd_hash = hashlib.pbkdf2_hmac(
            'sha256',
            password.encode('utf-8'),
            salt,
            100_000
        )
        # Return combined salt + hash as hex string for storage
        return salt.hex() + pwd_hash.hex()

    @staticmethod
    def verify_password(stored_password_hash, password_attempt):
        salt_hex = stored_password_hash[:32]  # first 16 bytes (32 hex chars)
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
    def add_user(username, password, role='admin'):
        connection = get_db_connection()
        cursor = connection.cursor()
        password_hash = User.hash_password(password)
        try:
            cursor.execute("""
                INSERT INTO users (username, password_hash, role)
                VALUES (?, ?, ?)
            """, (username, password_hash, role))
            connection.commit()
        except Exception as e:
            print(f"Error adding user: {e}")
        finally:
            connection.close()

    @staticmethod
    def authenticate(username, password):
        try:
            connection = get_db_connection()
            cursor = connection.cursor()
            cursor.execute("SELECT password_hash FROM users WHERE username = ?", (username,))
            result = cursor.fetchone()
            connection.close()

            if result:
                stored_hash = result[0]
                return User.verify_password(stored_hash, password)
            return False
        except Exception as e:
            print(f"Authentication error: {e}")
            return False
