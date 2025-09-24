from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import QDialog, QDialogButtonBox, QLabel, QPushButton, QVBoxLayout, QWidget

from utils.branding import APP_NAME


class NavigationHelpDialog(QDialog):
    def __init__(self, parent: QWidget | None = None):
        super().__init__(parent)
        self.setWindowTitle(f"How to Navigate {APP_NAME}")
        self.setMinimumWidth(520)
        # Enable minimize/maximize buttons and resizing
        self.setWindowFlag(Qt.WindowType.WindowMinimizeButtonHint, True)
        self.setWindowFlag(Qt.WindowType.WindowMaximizeButtonHint, True)
        self.setSizeGripEnabled(True)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(18, 16, 18, 12)
        layout.setSpacing(10)
        text = QLabel(
            """
            <div style='font-size:14px; color:#1f2937; line-height:1.6;'>
            <p><b>Top Bar:</b> Use the buttons Products, Customers, Invoice,
            Receipts, and Users (if visible) to switch views.</p>
            <p><b>More:</b> Under the More tab you can open Sales Report, Graph, and
            Activity Log (availability depends on your role).</p>
            <p><b>Graphs:</b> Choose Line or Bar, select Monthly or Yearly, and pick a
            Product. The default is <i>All Products</i>; select a specific product to see
            its individual sales trend. Click <i>Show Graph</i> to update.</p>
            <p><b>Settings:</b> Admin/CEO can open Settings from the top bar to update
            business info, receipt footer, backup directory, and retention.</p>
            <p><b>Logout:</b> Click Logout on the top bar to end your session.</p>
            <hr/>
            <p style='font-weight:700;'>Getting Started (Basics)</p>
            <ol>
              <li><b>Add Products:</b> Go to Products and add name, price, and stock.</li>
              <li><b>Add Customers:</b> Go to Customers and add at least one customer.</li>
              <li><b>Create an Invoice:</b> In Invoice, select a customer, add items with
                  quantities, then click <i>Save Invoice</i>.</li>
              <li><b>View/Print Receipts:</b> Open Receipts, select the invoice, then
                  Load to preview. You can Print or Export to PDF.</li>
              <li><b>Review Performance:</b> In More → Sales Report or Graph, view totals
                  and trends. Use the Product filter in Graph for item-specific sales.</li>
              <li><b>Backups:</b> In Settings, choose a backup folder and retention. Use
                  <i>Backup Now</i> and review the last backup time.</li>
            </ol>
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
        # Enable minimize/maximize buttons and resizing
        self.setWindowFlag(Qt.WindowType.WindowMinimizeButtonHint, True)
        self.setWindowFlag(Qt.WindowType.WindowMaximizeButtonHint, True)
        self.setSizeGripEnabled(True)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(18, 16, 18, 12)
        layout.setSpacing(10)

        desc = QLabel(f"Choose an option below for help with {APP_NAME}:")
        desc.setStyleSheet("color:#1f2937; font-size:14px;")
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
        # Add dark-red hover to the Close button for better affordance
        try:
            btn_close = close_box.button(QDialogButtonBox.StandardButton.Close)
            if btn_close is not None:
                btn_close.setStyleSheet(
                    "QPushButton { padding: 8px 16px; border-radius: 6px; }"
                    "QPushButton:hover { background-color: #b71c1c; color: white; }"
                )
        except Exception:
            pass
        layout.addWidget(close_box)

    def open_navigation_help(self):
        dlg = NavigationHelpDialog(self)
        dlg.exec()
