from PyQt6.QtWidgets import QWidget, QVBoxLayout, QLabel, QLineEdit, QPushButton, QMessageBox
from PyQt6.QtGui import QPalette, QBrush, QPixmap
from PyQt6.QtCore import Qt
from models.user import User
from ui.main_window import MainWindow

class LoginWindow(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Login")
        self.resize(400, 300)
        self.setMinimumSize(300, 200)
        self.set_background_image("bg_images/user1.jpeg")

        layout = QVBoxLayout()

        title = QLabel("WMS Login")
        title.setStyleSheet("font-size: 20px; font-weight: bold; color: white;")
        layout.addWidget(title, alignment=Qt.AlignmentFlag.AlignCenter)

        self.username_input = QLineEdit()
        self.username_input.setPlaceholderText("Username")
        self.username_input.returnPressed.connect(self.authenticate)
        layout.addWidget(self.username_input)

        self.password_input = QLineEdit()
        self.password_input.setPlaceholderText("Password")
        self.password_input.setEchoMode(QLineEdit.EchoMode.Password)
        self.password_input.returnPressed.connect(self.authenticate)
        layout.addWidget(self.password_input)

        login_button = QPushButton("Login")
        login_button.clicked.connect(self.authenticate)
        layout.addWidget(login_button)

        self.setLayout(layout)

    def set_background_image(self, image_path):
        palette = QPalette()
        pixmap = QPixmap(image_path)
        if not pixmap.isNull():
            scaled_pixmap = pixmap.scaled(self.size(), Qt.AspectRatioMode.KeepAspectRatioByExpanding)
            palette.setBrush(QPalette.ColorRole.Window, QBrush(scaled_pixmap))
            self.setPalette(palette)

    def authenticate(self):
        username = self.username_input.text().strip()
        password = self.password_input.text().strip()

        if User.authenticate(username, password):
            self.main_window = MainWindow(username)
            self.main_window.show()
            self.close()
        else:
            QMessageBox.warning(self, "Login Failed", "Invalid username or password.")
