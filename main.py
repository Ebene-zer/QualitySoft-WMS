import sys
from PyQt6.QtWidgets import QApplication
from ui.login_window import LoginWindow
from database.db_handler import initialize_database
from models.user import User

if __name__ == "__main__":
    app = QApplication(sys.argv)

    # Ensure tables exist
    initialize_database()

    # Add default admin user if it doesn't exist
    from database.db_handler import get_db_connection
    connection = get_db_connection()
    cursor = connection.cursor()
    cursor.execute("SELECT * FROM users WHERE username = 'Eben'")
    result = cursor.fetchone()
    connection.close()

    if not result:
        User.add_user("Eben", "admin123")
       # print("Admin user created (username: admin / password: admin123)")

    login = LoginWindow()
    login.show()
    sys.exit(app.exec())
