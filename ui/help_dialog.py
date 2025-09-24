from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import QDialog, QDialogButtonBox, QLabel, QPushButton, QVBoxLayout, QWidget

from utils.branding import APP_NAME


class NavigationHelpDialog(QDialog):
    def __init__(self, parent: QWidget | None = None):
        super().__init__(parent)
        self.setWindowTitle(f"How to Navigate {APP_NAME}")
        self.setMinimumWidth(520)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(18, 16, 18, 12)
        layout.setSpacing(10)
        text = QLabel(
            """
            <div style='font-size:13px; color:#2c3e50;'>
            <p><b>Top Bar:</b> Use the buttons Products, Customers, Invoice,
            Receipts, and Users (if visible) to switch views.</p>
            <p><b>More:</b> Access Sales Report, Graph, and Activity Log under the More tab based on your role.</p>
            <p><b>Settings:</b> Admin/CEO can open Settings from the top bar.</p>
            <p><b>Logout:</b> Click Logout on the top bar to end your session.</p>
            </div>
            """
        )
        text.setTextFormat(Qt.TextFormat.RichText)
        text.setWordWrap(True)
        layout.addWidget(text)

        buttons = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok, parent=self)
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)


class HelpDialog(QDialog):
    def __init__(self, on_about_clicked, parent: QWidget | None = None):
        super().__init__(parent)
        self.setWindowTitle("Help")
        self.setModal(True)
        self.setMinimumWidth(420)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(18, 16, 18, 12)
        layout.setSpacing(10)

        desc = QLabel(f"Choose an option below for help with {APP_NAME}:")
        desc.setStyleSheet("color:#2c3e50;")
        layout.addWidget(desc)

        btn_about = QPushButton(f"About {APP_NAME}")
        btn_nav = QPushButton("How to Navigate")
        for b in (btn_about, btn_nav):
            b.setMinimumHeight(36)
            b.setStyleSheet(
                """
                QPushButton { background-color: #3498db; color: white; border-radius: 6px; padding: 8px 14px; }
                QPushButton:hover { background-color: #2980b9; }
                """
            )
            layout.addWidget(b)

        btn_about.clicked.connect(on_about_clicked)
        btn_nav.clicked.connect(self.open_navigation_help)

        layout.addStretch(1)

        close_box = QDialogButtonBox(QDialogButtonBox.StandardButton.Close, parent=self)
        close_box.rejected.connect(self.reject)
        layout.addWidget(close_box)

    def open_navigation_help(self):
        dlg = NavigationHelpDialog(self)
        dlg.exec()
