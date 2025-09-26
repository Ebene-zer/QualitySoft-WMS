"""Application entry point (FREE edition) - initializes DB, ensures default admin, shows login."""
import logging
import sys
from typing import Any

from PyQt6.QtCore import Qt
from PyQt6.QtGui import QGuiApplication, QIcon
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
from utils.logging_setup import configure_logging, install_global_excepthook
from utils.resource_paths import asset_path

__version__ = "1.0.0"


class AdminSetupDialog(QDialog):
    """Popup shown once when the default admin account is auto-created.
    Allows copying the temporary password and informs user to change it after log in.
    """

    def __init__(self, username: str, temp_password: str, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Initial Admin Setup")
        self.setModal(True)
        self.temp_password = temp_password
        layout = QVBoxLayout(self)
        layout.addWidget(QLabel("An administrator account has been created."))
        layout.addWidget(QLabel(f"Username: {username}"))
        layout.addWidget(QLabel("Temporary Password (copy & store securely):"))
        self.pass_field = QLineEdit(temp_password)
        self.pass_field.setReadOnly(True)
        self.pass_field.setCursorPosition(0)
        layout.addWidget(self.pass_field)
        btn_row = QHBoxLayout()
        copy_btn = QPushButton("Copy Password")
        close_btn = QPushButton("Close")
        copy_btn.clicked.connect(self.copy_password)
        close_btn.clicked.connect(self.accept)
        btn_row.addWidget(copy_btn)
        btn_row.addWidget(close_btn)
        layout.addLayout(btn_row)
        layout.addWidget(QLabel("You must set a new password after first login."))
        self.pass_field.selectAll()

    def copy_password(self):
        QGuiApplication.clipboard().setText(self.temp_password)
        QMessageBox.information(self, "Copied", "Temporary password copied to clipboard.")


_APP_ICON: QIcon | None = None  # cached after load


def _set_app_icon(app: QApplication):
    """Set a global window icon (single canonical file: tradia.ico)."""
    global _APP_ICON
    if _APP_ICON is not None:
        app.setWindowIcon(_APP_ICON)
        return
    icon_file = asset_path("tradia.ico")
    _APP_ICON = QIcon(icon_file)
    if not _APP_ICON.isNull():
        app.setWindowIcon(_APP_ICON)
        logging.info("Application icon set from tradia.ico")
    else:
        logging.warning("Failed loading tradia.ico icon.")
    if sys.platform.startswith("win"):
        try:
            import ctypes
            app_id = "Tradia.App"
            ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(app_id)
            logging.info("Set Windows AppUserModelID to %s", app_id)
        except Exception as e:
            logging.debug("Could not set Windows AppUserModelID: %s", e)


def main() -> int:
    configure_logging()
    install_global_excepthook()
    # Enable High-DPI scaling before QApplication instance
    try:
        aa_scale: Any = getattr(Qt.ApplicationAttribute, "AA_EnableHighDpiScaling", None)
        if aa_scale is not None:
            QApplication.setAttribute(aa_scale, True)
        aa_pix: Any = getattr(Qt.ApplicationAttribute, "AA_UseHighDpiPixmaps", None)
        if aa_pix is not None:
            QApplication.setAttribute(aa_pix, True)
        QGuiApplication.setHighDpiScaleFactorRoundingPolicy(
            Qt.HighDpiScaleFactorRoundingPolicy.PassThrough
        )
    except Exception:
        pass
    app_inst = QApplication.instance()
    app: QApplication
    if isinstance(app_inst, QApplication):
        app = app_inst
    else:
        app = QApplication(sys.argv)
    _set_app_icon(app)
    initialize_database()
    # Create default admin if missing and show popup (skip during tests)
    temp_pass = User.ensure_default_admin("admin")
    if temp_pass and "pytest" not in sys.modules:
        try:
            dlg = AdminSetupDialog("admin", temp_pass)
            if _APP_ICON:
                dlg.setWindowIcon(_APP_ICON)
            dlg.exec()
        except Exception as e:
            logging.warning("Failed showing admin setup dialog: %s", e)
    # Directly show login (activation/trial removed)
    login = LoginWindow()
    if _APP_ICON:
        login.setWindowIcon(_APP_ICON)
    login.show()
    return app.exec()


if __name__ == "__main__":
    sys.exit(main())
