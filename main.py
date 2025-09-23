import logging
import secrets
import sys
import uuid
from datetime import datetime

from PyQt6.QtGui import QGuiApplication
from PyQt6.QtWidgets import (
    QApplication,
    QDialog,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMessageBox,
    QPushButton,
    QVBoxLayout,
)

from database.db_handler import initialize_database
from models.user import User
from ui.login_window import LoginWindow
from utils.license_manager import (
    check_product_pin,
    is_trial_expired,
    set_license_field,
)

# Application version constant (optional)
__version__ = "1.0.0"


def _configure_logging():
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    )
    logging.getLogger("sqlite3").setLevel(logging.WARNING)


class PinDialog(QDialog):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Product Pin Required")
        self.setFixedSize(350, 200)
        layout = QVBoxLayout()
        self.license_code = str(uuid.uuid4())
        layout.addWidget(QLabel("Trial expired. Enter Product Pin to continue:"))
        self.code_label = QLabel(f"License Request Code: {self.license_code}")
        layout.addWidget(self.code_label)
        self.copy_btn = QPushButton("Copy Code")
        self.copy_btn.clicked.connect(self.copy_code)
        layout.addWidget(self.copy_btn)
        self.pin_input = QLineEdit()
        self.pin_input.setEchoMode(QLineEdit.EchoMode.Password)
        layout.addWidget(self.pin_input)
        self.submit_btn = QPushButton("Submit")
        self.submit_btn.clicked.connect(self.check_pin)
        layout.addWidget(self.submit_btn)
        self.setLayout(layout)
        self.pin_valid = False

    def get_license_code(self):
        return self.license_code

    def copy_code(self):
        QGuiApplication.clipboard().setText(self.license_code)
        QMessageBox.information(self, "Copied", "License Request Code copied to clipboard.")

    def check_pin(self):
        try:
            pin = self.pin_input.text().strip()
            if check_product_pin(pin):
                # Reset trial period after valid pin entry
                set_license_field("trial_days", 14)
                # Store trial_start in Day/Month/Year format
                set_license_field("trial_start", datetime.now().strftime("%d/%m/%Y"))
                self.pin_valid = True
                self.accept()
            else:
                QMessageBox.warning(self, "Invalid Pin", "The Product Pin is incorrect.")
        except Exception as e:
            QMessageBox.critical(self, "Error", f"An error occurred during pin validation: {e}")


class InitialAdminSetupDialog(QDialog):
    """Dialog shown when the initial admin account is created; allows copying the temp password."""

    def __init__(self, username: str, temp_password: str, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Initial Admin Setup")
        self.setModal(True)
        self.temp_password = temp_password
        layout = QVBoxLayout()
        layout.addWidget(QLabel("An admin account was created."))
        layout.addWidget(QLabel(f"Username: {username}"))
        layout.addWidget(QLabel("Temporary Password (copy & store securely):"))
        self.pass_field = QLineEdit(temp_password)
        self.pass_field.setReadOnly(True)
        self.pass_field.setCursorPosition(0)
        layout.addWidget(self.pass_field)
        btn_row = QHBoxLayout()
        self.copy_btn = QPushButton("Copy Password")
        self.close_btn = QPushButton("Close")
        self.copy_btn.clicked.connect(self.copy_password)
        self.close_btn.clicked.connect(self.accept)
        btn_row.addWidget(self.copy_btn)
        btn_row.addWidget(self.close_btn)
        layout.addLayout(btn_row)
        layout.addWidget(QLabel("You must set a new password now (you will be prompted)."))
        self.setLayout(layout)
        # Auto-select for quick Ctrl+C
        self.pass_field.selectAll()

    def copy_password(self):
        QGuiApplication.clipboard().setText(self.temp_password)
        QMessageBox.information(self, "Copied", "Temporary password copied to clipboard.")


def main() -> int:
    """Application entry point used by console script 'tradia'.

    Returns an exit status code.
    """
    _configure_logging()
    app = QApplication.instance() or QApplication(sys.argv)
    initialize_database()
    if not User.user_exists("admin"):
        temp_pass = secrets.token_urlsafe(10)
        User.add_user("admin", temp_pass, "Admin", must_change_password=True)
        # Replace simple message box with copy-capable dialog
        dlg = InitialAdminSetupDialog("admin", temp_pass)
        dlg.exec()
    if is_trial_expired():
        pin_dialog = PinDialog()
        if pin_dialog.exec() != QDialog.DialogCode.Accepted:
            return 0
    login = LoginWindow()
    login.show()
    return app.exec()


if __name__ == "__main__":
    sys.exit(main())
