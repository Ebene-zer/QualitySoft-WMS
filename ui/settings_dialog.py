from PyQt6.QtWidgets import (
    QDialog,
    QFileDialog,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMessageBox,
    QPushButton,
    QSpinBox,
    QVBoxLayout,
)

from database.db_handler import get_db_connection
from utils.backup import (
    _get_retention_count,
    get_last_backup_time,
    perform_backup,
    resolve_backup_dir,
    update_backup_directory,
    update_retention_count,
)


class SettingsDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Settings")
        self.setMinimumSize(460, 320)
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

        # Insert backup directory controls
        backup_dir_label = QLabel("Backup Directory:")
        self.backup_dir_edit = QLineEdit()
        self.backup_dir_edit.setPlaceholderText("Select or enter backup directory (optional)")
        browse_btn = QPushButton("Browse…")
        browse_btn.clicked.connect(self.choose_backup_directory)
        backup_hbox = QHBoxLayout()
        backup_hbox.addWidget(self.backup_dir_edit)
        backup_hbox.addWidget(browse_btn)
        layout.addWidget(backup_dir_label)
        layout.addLayout(backup_hbox)

        # Manual backup button
        backup_now_btn = QPushButton("Backup Now")
        backup_now_btn.clicked.connect(self.backup_now)
        layout.addWidget(backup_now_btn)

        # Last backup status label
        self.last_backup_label = QLabel("Last Backup: (checking...)")
        layout.addWidget(self.last_backup_label)

        # Retention configuration
        retention_layout = QHBoxLayout()
        retention_label = QLabel("Retention (number of backups to keep):")
        self.retention_spin = QSpinBox()
        self.retention_spin.setRange(1, 500)
        self.retention_spin.setValue(_get_retention_count())
        retention_layout.addWidget(retention_label)
        retention_layout.addWidget(self.retention_spin)
        layout.addLayout(retention_layout)

        # Save button (unchanged reference name)
        self.save_btn = QPushButton("Save")
        self.save_btn.clicked.connect(self.save_wholesale_number)
        layout.addWidget(self.save_btn)

        self.setLayout(layout)

        self.load_wholesale_settings()

    def load_wholesale_settings(self):
        try:
            conn = get_db_connection()
            cur = conn.cursor()
            cur.execute(
                "SELECT wholesale_number, wholesale_name, wholesale_address, backup_directory FROM settings WHERE id=1"
            )
            result = cur.fetchone()
            conn.close()
            if result:
                self.wholesale_edit.setText(result[0])
                self.wholesale_name_edit.setText(result[1] if result[1] else "")
                self.wholesale_address_edit.setText(result[2] if result[2] else "")
                self.backup_dir_edit.setText(result[3] or "")
            self.refresh_backup_status()
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to load settings.\n{e}")

    def refresh_backup_status(self):
        last = get_last_backup_time()
        if last is None:
            self.last_backup_label.setText("Last Backup: Never")
        else:
            self.last_backup_label.setText(f"Last Backup: {last.strftime('%Y-%m-%d %H:%M:%S')}")

    def choose_backup_directory(self):
        directory = QFileDialog.getExistingDirectory(self, "Select Backup Directory", resolve_backup_dir())
        if directory:
            self.backup_dir_edit.setText(directory)

    def backup_now(self):
        # Ensure backup directory saved first if user changed it
        if self.backup_dir_edit.text().strip():
            try:
                update_backup_directory(self.backup_dir_edit.text().strip())
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Failed to update backup directory before backup: {e}")
                return
        try:
            path = perform_backup()
            self.refresh_backup_status()
            QMessageBox.information(self, "Backup Created", f"Backup stored at:\n{path}")
        except Exception as e:
            QMessageBox.critical(self, "Backup Failed", f"Backup could not be created:\n{e}")

    def save_wholesale_number(self):
        new_number = self.wholesale_edit.text().strip()
        new_name = self.wholesale_name_edit.text().strip()
        new_address = self.wholesale_address_edit.text().strip()
        backup_dir = self.backup_dir_edit.text().strip()
        retention_val = self.retention_spin.value()
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
            cur.execute(
                "UPDATE settings SET wholesale_number=?, wholesale_name=?, "
                "wholesale_address=?, backup_directory=?, retention_count=? WHERE id=1",
                (new_number, new_name, new_address, backup_dir, retention_val),
            )
            conn.commit()
            conn.close()
            try:
                update_retention_count(retention_val)
            except Exception:
                pass
            QMessageBox.information(self, "Saved", "Settings updated successfully.")
            self.refresh_backup_status()
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to save settings.\n{e}")
