from PyQt6.QtWidgets import QWidget, QVBoxLayout, QLabel, QLineEdit, QPushButton, QMessageBox, QFrame
from PyQt6.QtGui import QFont
from PyQt6.QtCore import Qt
from models.user import User
from ui.main_window import MainWindow


class LoginWindow(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Login")
        self.resize(400, 300)
        self.setMinimumSize(350, 250)

        self.setStyleSheet("""
            QWidget {
                background-color: #F2F2F2;
            }
            QLineEdit {
                padding: 8px;
                border: 1px solid #ccc;
                border-radius: 6px;
                font-size: 14px;
            }
            QPushButton {
                padding: 10px;
                border-radius: 6px;
                background-color: #2E86C1;
                color: white;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #21618C;
            }
        """)

        main_layout = QVBoxLayout()
        main_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)

        card = QFrame()
        card.setStyleSheet("""
            QFrame {
                background-color: white;
                border-radius: 10px;
                padding: 20px;
            }
        """)
        card_layout = QVBoxLayout()

        title = QLabel("QUALITYSOFT WMS")
        title.setFont(QFont("Arial", 18, weight=QFont.Weight.Bold))
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        card_layout.addWidget(title)

        self.username_input = QLineEdit()
        self.username_input.setPlaceholderText("Username")
        self.username_input.returnPressed.connect(self.authenticate)
        card_layout.addWidget(self.username_input)

        self.password_input = QLineEdit()
        self.password_input.setPlaceholderText("Password")
        self.password_input.setEchoMode(QLineEdit.EchoMode.Password)
        self.password_input.returnPressed.connect(self.authenticate)
        card_layout.addWidget(self.password_input)

        login_button = QPushButton("Login")
        login_button.clicked.connect(self.authenticate)
        card_layout.addWidget(login_button)

        card.setLayout(card_layout)
        main_layout.addWidget(card)

        self.setLayout(main_layout)

    def authenticate(self):
        username = self.username_input.text().strip()
        password = self.password_input.text().strip()

        if User.authenticate(username, password):
            self.main_window = MainWindow(username)
            self.main_window.show()
            self.close()
        else:
            QMessageBox.warning(self, "Login Failed", "Invalid username or password.")
