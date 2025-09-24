from datetime import datetime

from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import QDialog, QDialogButtonBox, QLabel, QVBoxLayout

from utils.branding import APP_NAME, APP_VERSION


class AboutDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle(f"About {APP_NAME}")
        self.setModal(True)
        self.setMinimumWidth(420)
        # Enable minimize/maximize buttons and resizing
        self.setWindowFlag(Qt.WindowType.WindowMinimizeButtonHint, True)
        self.setWindowFlag(Qt.WindowType.WindowMaximizeButtonHint, True)
        self.setSizeGripEnabled(True)

        year = datetime.now().year

        layout = QVBoxLayout(self)
        layout.setContentsMargins(18, 16, 18, 12)
        layout.setSpacing(8)

        title = QLabel(f"<b style='font-size:18px'>{APP_NAME}</b>")
        subtitle = QLabel(f"Version {APP_VERSION}")
        subtitle.setStyleSheet("color:#555")
        copyright_lbl = QLabel(f"&copy; {year} Ebenezer Fuachie. All rights reserved.")
        license_lbl = QLabel("License: Apache-2.0")
        for w in (title, subtitle, copyright_lbl, license_lbl):
            w.setTextFormat(Qt.TextFormat.RichText)
            layout.addWidget(w)

        layout.addStretch(1)

        buttons = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok, parent=self)
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

        self.setLayout(layout)
