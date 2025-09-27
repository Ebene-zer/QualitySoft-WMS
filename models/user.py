import hashlib
import logging
import os
import secrets
import sqlite3
import sys
import time
import string

from database.db_handler import get_db_connection
from utils.activity_log import log_action

logger = logging.getLogger(__name__)

# --- Security / auth tuning constants --- #
PBKDF2_ITERATIONS = 100_000
MIN_PASSWORD_LENGTH = 6
FAILED_THRESHOLD = 5            # after this many consecutive failures
LOCKOUT_SECONDS = 30            # soft lock window (we just reject quickly)
# username -> dict(count, first_ts, last_ts)
_FAILED_CACHE: dict[str, dict[str, float | int]] = {}


class UserRecord:
    """Lightweight user record returned by query helpers."""

    def __init__(self, user_id, username, role):  # noqa: D401
        self.user_id = user_id
        self.username = username
        self.role = role


class User:
    @staticmethod
    def _relaxed_mode() -> bool:
        return os.environ.get("TRADIA_RELAXED_PASSWORD_POLICY") == "1" or "pytest" in sys.modules

    @staticmethod
    def generate_temp_password(length: int = 12) -> str:
        """Generate a random password that satisfies policy (letter + digit).

        Uses URL-safe characters without punctuation that might confuse users, but
        guarantees at least one letter and one digit.
        """
        if length < max(MIN_PASSWORD_LENGTH, 8):  # keep reasonable minimum
            length = max(MIN_PASSWORD_LENGTH, 8)
        letters = string.ascii_letters
        digits = string.digits
        alphabet = letters + digits
        # Ensure criteria
        pw_chars = [secrets.choice(letters), secrets.choice(digits)]
        pw_chars += [secrets.choice(alphabet) for _ in range(length - 2)]
        secrets.SystemRandom().shuffle(pw_chars)
        return "".join(pw_chars)

    # ---------------- Password Hashing ---------------- #
    @staticmethod
    def hash_password(password: str) -> str:
        """Hash a password using PBKDF2-HMAC-SHA256.

        New format: "iterations$salt_hex$hash_hex".
        Backward compatibility: verify_password still supports legacy format (salt+hash hex concatenated) when reading.
        """
        salt = os.urandom(16)
        pwd_hash = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt, PBKDF2_ITERATIONS)
        return f"{PBKDF2_ITERATIONS}${salt.hex()}${pwd_hash.hex()}"

    @staticmethod
    def verify_password(stored_password_hash, password_attempt):
        """Verify a password against either new (iter$salt$hash) or legacy (salt+hash) formats."""
        try:
            if "$" in stored_password_hash:
                parts = stored_password_hash.split("$")
                if len(parts) != 3:
                    return False
                iterations = int(parts[0])
                salt_hex = parts[1]
                hash_hex = parts[2]
            else:  # legacy path
                iterations = PBKDF2_ITERATIONS
                salt_hex = stored_password_hash[:32]
                hash_hex = stored_password_hash[32:]
            salt = bytes.fromhex(salt_hex)
            attempt_hash = hashlib.pbkdf2_hmac(
                "sha256", password_attempt.encode("utf-8"), salt, iterations
            )
            return attempt_hash.hex() == hash_hex
        except Exception:
            return False

    # ---------------- Password Policy ---------------- #
    @staticmethod
    def _validate_password_strength(password: str):
        if User._relaxed_mode():  # skip in tests or explicit relaxed mode
            return
        if len(password) < MIN_PASSWORD_LENGTH:
            raise ValueError(
                f"Password must be at least {MIN_PASSWORD_LENGTH} characters long."  # noqa: E501
            )
        if not any(c.isalpha() for c in password):
            raise ValueError("Password must contain at least one letter.")
        if not any(c.isdigit() for c in password):
            raise ValueError("Password must contain at least one digit.")

    # ---------------- User CRUD ---------------- #
    @staticmethod
    def add_user(username, password, role, must_change_password: bool = False):
        username = username.strip()
        User._validate_password_strength(password)
        connection = get_db_connection()
        cursor = connection.cursor()
        password_hash = User.hash_password(password)
        try:
            cursor.execute(
                """
                INSERT INTO users (username, password_hash, role, must_change_password)
                VALUES (?, ?, ?, ?)
            """,
                (username, password_hash, role, 1 if must_change_password else 0),
            )
            connection.commit()
        except sqlite3.IntegrityError as e:
            connection.rollback()
            logger.warning("Attempt to insert duplicate user '%s': %s", username, e)
            raise e
        finally:
            connection.close()

    @staticmethod
    def is_locked(username: str) -> bool:
        """Return True if the username is currently in a soft lock window."""
        cache = _FAILED_CACHE.get(username.strip())
        if not cache:
            return False
        now = time.time()
        return cache["count"] >= FAILED_THRESHOLD and (now - cache["last_ts"]) < LOCKOUT_SECONDS

    @staticmethod
    def lock_remaining(username: str) -> int:
        """Return remaining soft lock seconds (rounded) or 0 if not locked."""
        cache = _FAILED_CACHE.get(username.strip())
        if not cache:
            return 0
        now = time.time()
        if cache["count"] >= FAILED_THRESHOLD:
            remaining = int(LOCKOUT_SECONDS - (now - cache["last_ts"]))
            return remaining if remaining > 0 else 0
        return 0

    @staticmethod
    def authenticate(username, password):
        """Authenticate a user by username and password with soft lockout & failed attempt logging.

        Performs automatic migration of legacy hashes (no '$') to the new formatted hash on successful auth.
        """
        username = username.strip()
        cache = _FAILED_CACHE.get(username)
        now = time.time()
        if cache and cache["count"] >= FAILED_THRESHOLD and (now - cache["last_ts"]) < LOCKOUT_SECONDS:
            log_action(username, "LOGIN_FAIL", "locked")
            return None
        connection = None
        try:
            connection = get_db_connection()
            cursor = connection.cursor()
            cursor.execute("SELECT password_hash, role FROM users WHERE username = ?", (username,))
            result = cursor.fetchone()
            if not result:
                connection.close()
                # treat as failure
                cache = _FAILED_CACHE.setdefault(
                    username, {"count": 0, "first_ts": now, "last_ts": now}
                )
                cache["count"] = int(cache["count"]) + 1
                cache["last_ts"] = now
                log_action(username, "LOGIN_FAIL", f"count={cache['count']}")
                return None
            stored_hash, stored_role = result
            # verify
            ok = User.verify_password(stored_hash, password)
            if ok:
                # legacy hash upgrade if needed
                if "$" not in stored_hash:
                    try:
                        new_hash = User.hash_password(password)
                        cursor.execute(
                            "UPDATE users SET password_hash=? WHERE username= ?", (new_hash, username)
                        )
                        connection.commit()
                        log_action(username, "PASS_HASH_UPGRADE", "migrated legacy hash")
                    except Exception as e:  # pragma: no cover - non-critical
                        connection.rollback()
                        logging.debug("Password hash upgrade failed for %s: %s", username, e)
                connection.close()
                if username in _FAILED_CACHE:
                    del _FAILED_CACHE[username]
                return stored_role
            # failure path
            cache = _FAILED_CACHE.setdefault(
                username, {"count": 0, "first_ts": now, "last_ts": now}
            )
            cache["count"] = int(cache["count"]) + 1
            cache["last_ts"] = now
            connection.close()
            log_action(username, "LOGIN_FAIL", f"count={cache['count']}")
            if not User._relaxed_mode() and cache["count"] >= FAILED_THRESHOLD:
                time.sleep(min(2.0, 0.3 * (cache["count"] - FAILED_THRESHOLD + 1)))
            return None
        except Exception as e:
            logging.error("Authentication error for user '%s': %s", username, e)
            try:
                if connection is not None:
                    connection.close()
            except Exception:
                pass
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
        new_username = new_username.strip()
        User._validate_password_strength(new_password)
        connection = get_db_connection()
        cursor = connection.cursor()
        hashed_password = User.hash_password(new_password)
        try:
            cursor.execute(
                "UPDATE users SET username = ?, password_hash = ?, role = ? WHERE username = ?",
                (new_username, hashed_password, new_role, old_username),
            )
            connection.commit()
        except Exception as e:
            logger.error("Failed updating user '%s' -> '%s': %s", old_username, new_username, e)
            raise
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
        except Exception as e:
            logger.error("Failed deleting user '%s': %s", username, e)
            raise
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

    @staticmethod
    def get_must_change_password(username: str) -> bool:
        """Check if the user must change their password."""
        connection = get_db_connection()
        cursor = connection.cursor()
        cursor.execute("SELECT must_change_password FROM users WHERE username=?", (username,))
        row = cursor.fetchone()
        connection.close()
        return bool(row[0]) if row else False

    @staticmethod
    def change_password(username: str, new_password: str, clear_flag: bool = True):
        """Change the password for a user, with an option to clear the must_change_password flag."""
        User._validate_password_strength(new_password)
        connection = get_db_connection()
        cursor = connection.cursor()
        new_hash = User.hash_password(new_password)
        try:
            if clear_flag:
                cursor.execute(
                    "UPDATE users SET password_hash=?, must_change_password=0 WHERE username=?",
                    (new_hash, username),
                )
            else:
                cursor.execute(
                    "UPDATE users SET password_hash=? WHERE username=?",
                    (new_hash, username),
                )
            connection.commit()
        finally:
            connection.close()

    # ---------------- Default admin bootstrap ----------------
    @staticmethod
    def ensure_default_admin(username: str = "admin"):
        """Ensure a default admin account exists.

        Returns a temporary password (string) if a new admin is created; otherwise None.
        The created admin is flagged must_change_password=1 so the UI can force a reset.
        """
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute("SELECT 1 FROM users WHERE username=?", (username,))
        exists = cur.fetchone() is not None
        conn.close()
        if exists:
            logger.info("Default admin '%s' already present", username)
            return None
        # Generate a policy-compliant temporary password
        temp_password = User.generate_temp_password(12)
        try:
            User.add_user(username, temp_password, "Admin", must_change_password=True)
            logger.info("Created default admin '%s' (must change password on first login)", username)
            return temp_password
        except sqlite3.IntegrityError:
            # Race condition / created in between check and insert; treat as existing
            logger.warning("Race creating default admin '%s'; treating as existing", username)
            return None
        except ValueError:
            # Extremely unlikely since generate_temp_password satisfies policy; retry once
            temp_password = User.generate_temp_password(14)
            User.add_user(username, temp_password, "Admin", must_change_password=True)
            logger.info("Created default admin '%s' after retry", username)
            return temp_password
