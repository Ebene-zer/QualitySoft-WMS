from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont
from PyQt6.QtWidgets import (
    QDialog,
    QFileDialog,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMessageBox,
    QPushButton,
    QScrollArea,
    QSpinBox,
    QTextEdit,
    QVBoxLayout,
    QWidget,
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
        # Smaller minimum size for small screens; allow free resizing
        self.setMinimumSize(400, 300)
        # Show minimize/maximize buttons and enable resize grip
        self.setWindowFlag(Qt.WindowType.WindowMinimizeButtonHint, True)
        self.setWindowFlag(Qt.WindowType.WindowMaximizeButtonHint, True)
        self.setSizeGripEnabled(True)
        # Optional initial size for comfort (user can resize smaller/larger)
        self.resize(720, 560)
        # Global style for better visibility
        self.setStyleSheet(
            """
            QLabel { color: #1f2937; font-size: 14px; }
            QLineEdit, QSpinBox { font-size: 14px; padding: 7px; }
            QLineEdit { background: #ffffff; border: 1px solid #cbd5e1; border-radius: 6px; }
            QLineEdit:focus { border: 2px solid #3498db; }
            QTextEdit {
                font-size: 14px;
                background: #ffffff;
                border: 1px solid #cbd5e1;
                border-radius: 6px;
                padding: 6px;
            }
            QTextEdit:focus { border: 2px solid #3498db; }
            QPushButton { font-size: 14px; }
            """
        )

        # Main dialog layout with a scroll area + fixed bottom bar for Save
        main_layout = QVBoxLayout()
        main_layout.setContentsMargins(16, 16, 16, 16)
        main_layout.setSpacing(10)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        content_widget = QWidget()
        content_layout = QVBoxLayout(content_widget)
        content_layout.setContentsMargins(0, 0, 0, 0)
        content_layout.setSpacing(10)

        # Use a bold font for field labels so they stand out
        bold_font = QFont()
        bold_font.setBold(True)

        # Section: Business Information
        header_business = QLabel("Business Information")
        header_business.setStyleSheet("font-weight: 600; margin-bottom: 6px;")
        header_business.setWordWrap(True)
        content_layout.addWidget(header_business)

        self.label_name = QLabel("Wholesale Name:")
        self.label_name.setFont(bold_font)
        content_layout.addWidget(self.label_name)

        self.wholesale_name_edit = QLineEdit()
        self.wholesale_name_edit.setPlaceholderText("Enter wholesale name")
        self.wholesale_name_edit.setToolTip("Your business name as it should appear on receipts.")
        self.wholesale_name_edit.setClearButtonEnabled(True)
        content_layout.addWidget(self.wholesale_name_edit)

        self.label = QLabel("Wholesale Number:")
        self.label.setFont(bold_font)
        content_layout.addWidget(self.label)

        self.wholesale_edit = QLineEdit()
        self.wholesale_edit.setPlaceholderText("Enter wholesale number")
        self.wholesale_edit.setToolTip("Contact number shown on receipts (digits only).")
        self.wholesale_edit.setClearButtonEnabled(True)
        content_layout.addWidget(self.wholesale_edit)

        self.label_address = QLabel("Wholesale Address:")
        self.label_address.setFont(bold_font)
        content_layout.addWidget(self.label_address)
        self.wholesale_address_edit = QLineEdit()
        self.wholesale_address_edit.setPlaceholderText("Enter wholesale address")
        self.wholesale_address_edit.setToolTip("Your business address/location shown on receipts.")
        self.wholesale_address_edit.setClearButtonEnabled(True)
        content_layout.addWidget(self.wholesale_address_edit)

        # Section: Backup & Retention
        header_backup = QLabel("Backup & Retention")
        header_backup.setStyleSheet("font-weight: 600; margin-top: 12px;")
        header_backup.setWordWrap(True)
        content_layout.addWidget(header_backup)

        backup_dir_label = QLabel("Backup Directory:")
        backup_dir_label.setFont(bold_font)
        self.backup_dir_edit = QLineEdit()
        self.backup_dir_edit.setPlaceholderText("Select or enter backup directory (optional)")
        self.backup_dir_edit.setToolTip("Directory where backups will be stored.")
        self.backup_dir_edit.setClearButtonEnabled(True)
        browse_btn = QPushButton("Browse…")
        browse_btn.setToolTip("Choose a folder for backups")
        browse_btn.clicked.connect(self.choose_backup_directory)
        backup_hbox = QHBoxLayout()
        backup_hbox.addWidget(self.backup_dir_edit)
        backup_hbox.addWidget(browse_btn)
        content_layout.addWidget(backup_dir_label)
        content_layout.addLayout(backup_hbox)

        backup_now_btn = QPushButton("Backup Now")
        backup_now_btn.setToolTip("Create a backup now to the configured directory")
        backup_now_btn.clicked.connect(self.backup_now)
        content_layout.addWidget(backup_now_btn)

        self.last_backup_label = QLabel("Last Backup: (checking...)")
        content_layout.addWidget(self.last_backup_label)

        retention_layout = QHBoxLayout()
        retention_label = QLabel("Retention (number of backups to keep):")
        retention_label.setFont(bold_font)
        self.retention_spin = QSpinBox()
        self.retention_spin.setRange(1, 500)
        self.retention_spin.setToolTip("How many recent backups to keep automatically.")
        self.retention_spin.setValue(_get_retention_count())
        retention_layout.addWidget(retention_label)
        retention_layout.addWidget(self.retention_spin)
        content_layout.addLayout(retention_layout)

        # Section: Inventory & Alerts
        header_inventory = QLabel("Inventory & Alerts")
        header_inventory.setStyleSheet("font-weight: 600; margin-top: 12px;")
        header_inventory.setWordWrap(True)
        content_layout.addWidget(header_inventory)

        low_hbox = QHBoxLayout()
        low_label = QLabel("Low stock alert threshold:")
        low_label.setFont(bold_font)
        self.low_stock_spin = QSpinBox()
        self.low_stock_spin.setRange(0, 1_000_000)
        self.low_stock_spin.setToolTip("Products at or below this quantity are considered low in stock.")
        self.low_stock_spin.setValue(10)
        low_hbox.addWidget(low_label)
        low_hbox.addWidget(self.low_stock_spin)
        content_layout.addLayout(low_hbox)

        # Receipt footer configuration
        footer_title = QLabel("Receipt Footer")
        footer_title.setStyleSheet("font-weight: 600; margin-top: 12px;")
        footer_title.setWordWrap(True)
        content_layout.addWidget(footer_title)

        thank_label = QLabel("Thank-you message:")
        thank_label.setFont(bold_font)
        self.thank_you_edit = QLineEdit()
        self.thank_you_edit.setPlaceholderText("e.g. Thank you for buying from us!")
        self.thank_you_edit.setToolTip("Closing message printed at the bottom of receipts.")
        self.thank_you_edit.setClearButtonEnabled(True)
        content_layout.addWidget(thank_label)
        content_layout.addWidget(self.thank_you_edit)

        notes_label = QLabel("Additional notes:")
        notes_label.setFont(bold_font)
        self.receipt_notes_edit = QTextEdit()
        self.receipt_notes_edit.setPlaceholderText("Optional notes shown on receipt")
        self.receipt_notes_edit.setToolTip("Optional notes printed on receipts (appears opposite totals).")
        self.receipt_notes_edit.setAcceptRichText(False)
        self.receipt_notes_edit.setMinimumHeight(90)
        content_layout.addWidget(notes_label)
        content_layout.addWidget(self.receipt_notes_edit)

        # Build scroll area
        scroll.setWidget(content_widget)
        main_layout.addWidget(scroll)

        # Fixed bottom bar with Save button (always visible)
        self.save_btn = QPushButton("Save")
        self.save_btn.setToolTip("Save all settings")
        self.save_btn.setDefault(True)
        self.save_btn.setStyleSheet(
            """
            QPushButton {
                background-color: #21618C;
                color: white;
                border-radius: 6px;
                padding: 8px 14px;
            }
            QPushButton:hover {
                background-color: #3498db;
            }
            """
        )
        self.save_btn.clicked.connect(self.save_wholesale_number)
        bottom_bar = QHBoxLayout()
        bottom_bar.addStretch(1)
        bottom_bar.addWidget(self.save_btn)
        main_layout.addLayout(bottom_bar)

        self.setLayout(main_layout)

        self.load_wholesale_settings()

    def load_wholesale_settings(self):
        try:
            conn = get_db_connection()
            cur = conn.cursor()
            cur.execute(
                "SELECT wholesale_number, wholesale_name, wholesale_address, "
                "backup_directory, receipt_thank_you, receipt_notes, low_stock_threshold "
                "FROM settings WHERE id=1"
            )
            result = cur.fetchone()
            conn.close()
            if result:
                self.wholesale_edit.setText(result[0] or "")
                self.wholesale_name_edit.setText(result[1] or "")
                self.wholesale_address_edit.setText(result[2] or "")
                self.backup_dir_edit.setText(result[3] or "")
                # New fields (with sensible defaults)
                self.thank_you_edit.setText(result[4] or "Thank you for buying from us!")
                self.receipt_notes_edit.setPlainText(result[5] or "")
                try:
                    self.low_stock_spin.setValue(int(result[6]) if result[6] is not None else 10)
                except Exception:
                    self.low_stock_spin.setValue(10)
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
        thank_you = self.thank_you_edit.text().strip()
        receipt_notes = self.receipt_notes_edit.toPlainText().strip()
        low_stock_threshold = self.low_stock_spin.value()
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
                (
                    "UPDATE settings SET wholesale_number=?, wholesale_name=?, wholesale_address=?, "
                    "backup_directory=?, retention_count=?, receipt_thank_you=?, receipt_notes=?, "
                    "low_stock_threshold=? WHERE id=1"
                ),
                (
                    new_number,
                    new_name,
                    new_address,
                    backup_dir,
                    retention_val,
                    thank_you or "Thank you for buying from us!",
                    receipt_notes,
                    low_stock_threshold,
                ),
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
