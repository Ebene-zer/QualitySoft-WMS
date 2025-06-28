import sys
from PyQt6.QtWidgets import QApplication
from ui.login_window import LoginWindow
from database.db_handler import initialize_database
from models.user import User

if __name__ == "__main__":
    app = QApplication(sys.argv)

    initialize_database()

    # Add default admin user if it doesn't exist
    if not User.user_exists("admin"):
        User.add_user("admin", "admin123", "Admin")

    login = LoginWindow()
    login.show()
    sys.exit(app.exec())
