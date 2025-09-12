from PyQt6.QtWidgets import QDialog, QVBoxLayout, QLabel, QLineEdit, QPushButton, QMessageBox
from database.db_handler import get_db_connection

class SettingsDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Settings")
        self.setMinimumSize(350, 150)
        layout = QVBoxLayout()

        self.label_name = QLabel("Wholesale Name:")
        layout.addWidget(self.label_name)

        self.wholesale_name_edit = QLineEdit()
        self.wholesale_name_edit.setPlaceholderText("Enter wholesale name")
        layout.addWidget(self.wholesale_name_edit)


        self.label = QLabel("Wholesale Number:")
        layout.addWidget(self.label)

        self.wholesale_edit = QLineEdit()
        self.wholesale_edit.setPlaceholderText("Enter wholesale number")
        layout.addWidget(self.wholesale_edit)


        self.label_address = QLabel("Wholesale Address:")
        layout.addWidget(self.label_address)
        self.wholesale_address_edit = QLineEdit()
        self.wholesale_address_edit.setPlaceholderText("Enter wholesale address")
        layout.addWidget(self.wholesale_address_edit)


        self.save_btn = QPushButton("Save")
        self.save_btn.clicked.connect(self.save_wholesale_number)
        layout.addWidget(self.save_btn)

        self.setLayout(layout)
        self.load_wholesale_settings()

    def load_wholesale_settings(self):
        try:
            conn = get_db_connection()
            cur = conn.cursor()
            cur.execute("SELECT wholesale_number, wholesale_name, wholesale_address FROM settings WHERE id=1")
            result = cur.fetchone()
            conn.close()
            if result:
                self.wholesale_edit.setText(result[0])
                self.wholesale_name_edit.setText(result[1] if result[1] else "")
                self.wholesale_address_edit.setText(result[2] if result[2] else "")
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to load settings.\n{e}")

    def save_wholesale_number(self):
        new_number = self.wholesale_edit.text().strip()
        new_name = self.wholesale_name_edit.text().strip()
        new_address = self.wholesale_address_edit.text().strip()
        if not new_number.isdigit():
            QMessageBox.warning(self, "Invalid Input", "Wholesale number must be numeric.")
            return
        if not new_name:
            QMessageBox.warning(self, "Invalid Input", "Wholesale name cannot be empty.")
            return
        if not new_address:
            QMessageBox.warning(self, "Invalid Input", "Wholesale address cannot be empty.")
            return
        try:
            conn = get_db_connection()
            cur = conn.cursor()
            cur.execute("UPDATE settings SET wholesale_number=?, wholesale_name=?, wholesale_address=? WHERE id=1", (new_number, new_name, new_address))
            conn.commit()
            conn.close()
            QMessageBox.information(self, "Saved", "Settings updated successfully.")
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to save settings.\n{e}")
