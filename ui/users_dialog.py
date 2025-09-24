from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import QDialog, QDialogButtonBox, QVBoxLayout

from ui.user_view import UserView


class UsersDialog(QDialog):
    def __init__(self, current_user_role: str, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Users")
        self.setMinimumSize(800, 500)
        # Enable minimize/maximize buttons and resizing
        self.setWindowFlag(Qt.WindowType.WindowMinimizeButtonHint, True)
        self.setWindowFlag(Qt.WindowType.WindowMaximizeButtonHint, True)
        self.setSizeGripEnabled(True)

        layout = QVBoxLayout(self)
        self.user_view = UserView(current_user_role=current_user_role)
        layout.addWidget(self.user_view)

        buttons = QDialogButtonBox(QDialogButtonBox.StandardButton.Close, parent=self)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)
        self.setLayout(layout)
