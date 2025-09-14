import hashlib
import os

from database.db_handler import get_db_connection


class UserRecord:
    """Lightweight user record returned by query helpers."""

    def __init__(self, user_id, username, role):
        self.user_id = user_id
        self.username = username
        self.role = role


class User:
    @staticmethod
    def hash_password(password, salt=None):
        """Hash a password for storing."""
        if salt is None:
            salt = os.urandom(16)
        pwd_hash = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt, 100_000)
        return salt.hex() + pwd_hash.hex()

    @staticmethod
    def verify_password(stored_password_hash, password_attempt):
        """Verify a password against an existing hash."""
        salt_hex = stored_password_hash[:32]
        hash_hex = stored_password_hash[32:]

        salt = bytes.fromhex(salt_hex)
        attempt_hash = hashlib.pbkdf2_hmac("sha256", password_attempt.encode("utf-8"), salt, 100_000)
        return attempt_hash.hex() == hash_hex

    @staticmethod
    def add_user(username, password, role):
        """Add a new user with hashed password."""
        import sqlite3

        from database.db_handler import get_db_connection

        connection = get_db_connection()
        cursor = connection.cursor()

        password_hash = User.hash_password(password)  # Use the correct hashing method

        try:
            cursor.execute(
                """
                INSERT INTO users (username, password_hash, role)
                VALUES (?, ?, ?)
            """,
                (username, password_hash, role),
            )
            connection.commit()
        except sqlite3.IntegrityError as e:
            connection.rollback()
            raise e
        finally:
            connection.close()

    @staticmethod
    def authenticate(username, password):
        """Authenticate a user by username and password."""
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
        """Get the role of a user by username."""
        connection = get_db_connection()
        cursor = connection.cursor()
        cursor.execute(
            """
            SELECT role FROM users WHERE username = ?
        """,
            (username,),
        )
        result = cursor.fetchone()
        connection.close()

        if result:
            return result[0]
        return None

    @staticmethod
    def user_exists(username):
        """Check if a user exists by username."""
        connection = get_db_connection()
        cursor = connection.cursor()
        cursor.execute("SELECT 1 FROM users WHERE username = ?", (username,))
        result = cursor.fetchone()
        connection.close()
        return result is not None

    @staticmethod
    def update_user(old_username, new_username, new_password, new_role):
        """Update an existing user's details."""
        connection = get_db_connection()
        cursor = connection.cursor()
        hashed_password = User.hash_password(new_password)
        try:
            cursor.execute(
                "UPDATE users SET username = ?, password_hash = ?, role = ? WHERE username = ?",
                (new_username, hashed_password, new_role, old_username),
            )
            connection.commit()
        finally:
            connection.close()

    @staticmethod
    def delete_user(username):
        """Delete a user by username."""
        connection = get_db_connection()
        cursor = connection.cursor()
        try:
            cursor.execute("DELETE FROM users WHERE username = ?", (username,))
            connection.commit()
        finally:
            connection.close()

    # ---------------- New helper query methods ----------------
    @staticmethod
    def get_all_users():
        """Return list of UserRecord objects for all users ordered by username."""
        connection = get_db_connection()
        cursor = connection.cursor()
        cursor.execute("SELECT rowid as user_id, username, role FROM users ORDER BY username")
        rows = cursor.fetchall()
        connection.close()
        return [UserRecord(*row) for row in rows]

    @staticmethod
    def get_user_by_id(user_id):
        """Return a single UserRecord by rowid (internal autoincrement)."""
        connection = get_db_connection()
        cursor = connection.cursor()
        cursor.execute("SELECT rowid as user_id, username, role FROM users WHERE rowid = ?", (user_id,))
        row = cursor.fetchone()
        connection.close()
        return UserRecord(*row) if row else None
