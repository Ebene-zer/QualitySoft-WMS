from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QLabel, QLineEdit, QPushButton, QMessageBox, QComboBox, QHBoxLayout
)
from PyQt6.QtGui import QFont, QColor, QPalette
from PyQt6.QtCore import Qt
from models.user import User
from ui.main_window import MainWindow


class LoginWindow(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("QUALITYSOFT WMS - Login")
        self.resize(450, 300)
        self.setMinimumSize(350, 250)

        self.setStyleSheet("""
            QWidget {
                background-color: #f4f6f9;
            }
            QLabel {
                color: #333;
                font-size: 16px;
            }
            QLineEdit, QComboBox {
                padding: 8px;
                border: 1px solid #bbb;
                border-radius: 6px;
                font-size: 14px;
            }
            QPushButton {
                padding: 10px;
                font-weight: bold;
                background-color: #005bb5;
                color: white;
                border: none;
                border-radius: 6px;
            }
            QPushButton:hover {
                background-color: #004999;
            }
        """)

        layout = QVBoxLayout()

        title = QLabel("Welcome to WMS")
        title.setFont(QFont("Arial", 22, QFont.Weight.Bold))
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(title)

        # Role selection
        role_layout = QVBoxLayout()
        role_label = QLabel("Select Role:")
        self.role_combo = QComboBox()
        self.role_combo.addItems(["Manager", "CEO", "Admin"])
        role_layout.addWidget(role_label)
        role_layout.addWidget(self.role_combo)
        layout.addLayout(role_layout)

        # Username field
        self.username_input = QLineEdit()
        self.username_input.setPlaceholderText("Username")
        self.username_input.returnPressed.connect(self.authenticate)
        layout.addWidget(self.username_input)

        # Password field
        self.password_input = QLineEdit()
        self.password_input.setPlaceholderText("Password")
        self.password_input.setEchoMode(QLineEdit.EchoMode.Password)
        self.password_input.returnPressed.connect(self.authenticate)
        layout.addWidget(self.password_input)

        # Login button
        login_button = QPushButton("Login")
        login_button.clicked.connect(self.authenticate)
        layout.addWidget(login_button)

        self.setLayout(layout)

    def authenticate(self):
        username = self.username_input.text().strip()
        password = self.password_input.text().strip()
        selected_role = self.role_combo.currentText()

        if not username or not password:
            QMessageBox.warning(self, "Missing Info", "Please fill in both username and password.")
            return

        role = User.authenticate(username, password)
        if role:
            self.main_window = MainWindow(username, role)
            self.main_window.show()
            self.close()
        else:
            QMessageBox.warning(self, "Login Failed", "Invalid username or password.")



