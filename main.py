import sys
import uuid
from datetime import datetime

from PyQt6.QtGui import QGuiApplication
from PyQt6.QtWidgets import QApplication, QDialog, QLabel, QLineEdit, QMessageBox, QPushButton, QVBoxLayout

from database.db_handler import initialize_database
from models.user import User
from ui.login_window import LoginWindow
from utils.license_manager import check_product_pin, is_trial_expired, set_license_field


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


if __name__ == "__main__":
    app = QApplication(sys.argv)
    initialize_database()
    # Add default admin user if it doesn't exist
    if not User.user_exists("admin"):
        User.add_user("admin", "admin123", "Admin")
    if is_trial_expired():
        pin_dialog = PinDialog()
        if pin_dialog.exec() != QDialog.DialogCode.Accepted:
            sys.exit(0)
    login = LoginWindow()
    login.show()
    sys.exit(app.exec())
