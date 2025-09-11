from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QLabel, QLineEdit, QPushButton, QMessageBox, QComboBox, QHBoxLayout
)
from PyQt6.QtGui import QFont, QIcon
from PyQt6.QtCore import Qt, QSize
from models.user import User
from ui.main_window import MainWindow


class LoginWindow(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Login")
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

        title = QLabel("Welcome to QualitySoft WMS")
        title.setFont(QFont("Arial", 22,QFont.Weight.Bold))
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
        password_layout = QHBoxLayout()
        self.password_input = QLineEdit()
        self.password_input.setPlaceholderText("Password")
        self.password_input.setEchoMode(QLineEdit.EchoMode.Password)
        self.password_input.returnPressed.connect(self.authenticate)


        self.toggle_password_btn = QPushButton()
        self.toggle_password_btn.setCheckable(True)
        self.toggle_password_btn.setFixedWidth(30)
        self.toggle_password_btn.setFixedHeight(30)
        self.toggle_password_btn.setToolTip("Show/Hide Password")
        self.toggle_password_btn.setIcon(QIcon("icons/closed_eye.png"))
        self.toggle_password_btn.setIconSize(QSize(24, 24))
        self.toggle_password_btn.clicked.connect(self.toggle_password_visibility)

        password_layout.addWidget(self.password_input)
        password_layout.addWidget(self.toggle_password_btn)
        layout.addLayout(password_layout)


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
            QMessageBox.warning(self, "Missing Info", "Please Enter username and password.")
            return

        try:
            role = User.authenticate(username, password)
            if role:
                if role != selected_role:
                    QMessageBox.warning(self, "Access Denied", f"This is not {selected_role} account.")
                    return

                self.main_window = MainWindow(username, role)
                self.main_window.show()
                self.close()
            else:
                QMessageBox.warning(self, "Login Failed", "Invalid username or password.")
        except Exception as e:
            QMessageBox.critical(self, "Error", f"An error occurred during login: {e} \n"
                                                f"Contact Developer if problem persist.")


    def toggle_password_visibility(self):
        if self.toggle_password_btn.isChecked():
            self.password_input.setEchoMode(QLineEdit.EchoMode.Normal)
            self.toggle_password_btn.setIcon(QIcon("icons/open_eye.png"))
        else:
            self.password_input.setEchoMode(QLineEdit.EchoMode.Password)
            self.toggle_password_btn.setIcon(QIcon("icons/closed_eye.png"))