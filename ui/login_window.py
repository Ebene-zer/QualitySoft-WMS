from PyQt6.QtCore import QSize, Qt
from PyQt6.QtGui import QFont, QIcon
from PyQt6.QtWidgets import (
    QComboBox,
    QDialog,
    QFormLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMessageBox,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from models.user import User
from ui.main_window import MainWindow
from utils.branding import APP_NAME
from utils.session import set_current_user


class PasswordChangeDialog(QDialog):
    def __init__(self, username: str, parent=None):
        super().__init__(parent)
        self.username = username
        self.setWindowTitle("Change Password")
        self.setModal(True)
        self.resize(350, 180)
        layout = QVBoxLayout()
        form = QFormLayout()
        self.new_pwd = QLineEdit()
        self.new_pwd.setEchoMode(QLineEdit.EchoMode.Password)
        self.confirm_pwd = QLineEdit()
        self.confirm_pwd.setEchoMode(QLineEdit.EchoMode.Password)
        form.addRow("New Password:", self.new_pwd)
        form.addRow("Confirm Password:", self.confirm_pwd)
        layout.addLayout(form)
        btn_row = QHBoxLayout()
        self.ok_btn = QPushButton("Save")
        self.cancel_btn = QPushButton("Cancel")
        self.ok_btn.clicked.connect(self._on_save)
        self.cancel_btn.clicked.connect(self.reject)
        btn_row.addWidget(self.ok_btn)
        btn_row.addWidget(self.cancel_btn)
        layout.addLayout(btn_row)
        self.setLayout(layout)

    def _on_save(self):
        pwd = self.new_pwd.text().strip()
        confirm = self.confirm_pwd.text().strip()
        if len(pwd) < 8:
            QMessageBox.warning(self, "Weak Password", "Password must be at least 8 characters long.")
            return
        if pwd != confirm:
            QMessageBox.warning(self, "Mismatch", "Passwords do not match.")
            return
        try:
            User.change_password(self.username, pwd, clear_flag=True)
            QMessageBox.information(self, "Updated", "Password changed successfully.")
            self.accept()
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to change password: {e}")


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

        title = QLabel(f"Welcome to {APP_NAME}")
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

                # Force password change if required
                try:
                    if User.get_must_change_password(username) is True:
                        dlg = PasswordChangeDialog(username, self)
                        if dlg.exec() != QDialog.DialogCode.Accepted:
                            QMessageBox.information(self, "Cancelled", "Password change required before access.")
                            return
                except Exception:
                    # If the column/method not available, proceed (legacy DB) – fail open only for backward compat.
                    pass

                self.main_window = MainWindow(username, role)
                set_current_user(username, role)
                self.main_window.show()
                self.close()
            else:
                QMessageBox.warning(self, "Login Failed", "Invalid username or password.")
        except Exception as e:
            QMessageBox.critical(
                self, "Error", f"An error occurred during login: {e} \n" f"Contact Developer if problem persist."
            )

    def toggle_password_visibility(self):
        if self.toggle_password_btn.isChecked():
            self.password_input.setEchoMode(QLineEdit.EchoMode.Normal)
            self.toggle_password_btn.setIcon(QIcon("icons/open_eye.png"))
        else:
            self.password_input.setEchoMode(QLineEdit.EchoMode.Password)
            self.toggle_password_btn.setIcon(QIcon("icons/closed_eye.png"))
