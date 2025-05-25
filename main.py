from PyQt6.QtWidgets import QApplication
import sys

# Initialize the database (if you want the DB created on app start)
from database.db_handler import initialize_database
initialize_database()

# Import and launch the main dashboard window
from ui.main_window import MainWindow

def main():
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())

if __name__ == "__main__":
    main()
