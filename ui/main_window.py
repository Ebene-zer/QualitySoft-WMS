from PyQt6.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QStackedWidget, QLabel
)
from PyQt6.QtGui import QFont
import sys

from ui.product_view import ProductView
from ui.customer_view import CustomerView
from ui.invoice_view import InvoiceView
from ui.receipt_view import ReceiptView
from ui.user_view import UserView


class MainWindow(QWidget):
    def __init__(self, logged_in_user, role):
        super().__init__()
        self.logged_in_user = logged_in_user
        self.user_role = role
        self.setWindowTitle("QUALITYSOFT WHOLESALE MANAGEMENT SYSTEM")
        self.resize(1000, 700)
        self.setMinimumSize(800, 500)

        # Set flat background color
        self.setStyleSheet("background-color: #f0f2f5;")

        main_layout = QVBoxLayout()

        # Top button bar layout
        button_bar_layout = QHBoxLayout()
        button_bar_layout.setSpacing(12)

        self.nav_buttons = []

        def create_nav_button(text, index, height=40, font_size=10, width=None):
            btn = QPushButton(text)
            btn.setFixedHeight(height)
            btn.setFont(QFont("Segoe UI", font_size, QFont.Weight.Medium))
            if width:
                btn.setFixedWidth(width)
            btn.setStyleSheet(self.button_style(normal=True))
            btn.clicked.connect(lambda: self.switch_view(index))
            button_bar_layout.addWidget(btn)
            self.nav_buttons.append(btn)

        # Place 'More' button first, as a square with tooltip
        btn_more = QPushButton("\u2630")
        btn_more.setFixedHeight(40)
        btn_more.setFixedWidth(40)
        btn_more.setFont(QFont("Segoe UI", 14, QFont.Weight.Medium))
        btn_more.setStyleSheet(self.button_style(normal=True))
        btn_more.setToolTip("More")
        btn_more.clicked.connect(lambda: self.switch_view(0))
        button_bar_layout.addWidget(btn_more)
        self.nav_buttons.append(btn_more)

        create_nav_button("🛒 Products", 1, 40, 10)
        create_nav_button("👥 Customers", 2, 40, 10)
        create_nav_button("🧾 Invoices", 3, 40, 10)
        create_nav_button("📄 Receipts", 4, 40, 10)

        # Track the index for the Users tab
        users_tab_index = 5
        if self.user_role.lower() in ["admin", "ceo"]:
            create_nav_button("🔐 Users", 5, 40, 10)
            users_tab_index = 6

        btn_logout = QPushButton("🚪 Logout")
        btn_logout.setFixedHeight(40)
        btn_logout.setFont(QFont("Segoe UI", 10, QFont.Weight.Medium))
        btn_logout.setStyleSheet("""
            QPushButton {
                background-color: orange;
                color: white;
                border-radius: 6px;
                padding: 8px 14px;
            }
            QPushButton:hover {
                background-color: #c0392b;
            }
        """)
        btn_logout.clicked.connect(self.logout)
        button_bar_layout.addWidget(btn_logout)

        main_layout.addLayout(button_bar_layout)

        # Central stacked widget
        self.stacked_widget = QStackedWidget()
        # Add More tab first
        more_tab = QWidget()
        more_layout = QVBoxLayout()
        more_layout.addWidget(QLabel("More features coming soon..."))
        more_tab.setLayout(more_layout)
        self.stacked_widget.addWidget(more_tab)
        self.stacked_widget.addWidget(ProductView())
        self.stacked_widget.addWidget(CustomerView())
        self.stacked_widget.addWidget(InvoiceView())
        self.stacked_widget.addWidget(ReceiptView())
        self.stacked_widget.addWidget(UserView())
        main_layout.addWidget(self.stacked_widget)
        self.setLayout(main_layout)

        # Set first button as active
        self.switch_view(0)

    def button_style(self, normal=True):
        if normal:
            return """
                QPushButton {
                    background-color: #3498db;
                    color: white;
                    border-radius: 6px;
                    padding: 8px 14px;
                }
                QPushButton:hover {
                    background-color: #2980b9;
                }
            """
        else:
            return """
                QPushButton {
                    background-color: #2ecc71;
                    color: white;
                    border-radius: 6px;
                    padding: 8px 14px;
                }
            """

    def switch_view(self, index):
        self.stacked_widget.setCurrentIndex(index)

        # Refresh relevant view when switched to
        widget = self.stacked_widget.currentWidget()
        if hasattr(widget, "load_customers"):
            widget.load_customers()
        if hasattr(widget, "load_products"):
            widget.load_products()
        if hasattr(widget, "load_invoice_ids"):
            widget.load_invoice_ids()
        if hasattr(widget, "load_invoices"):
            widget.load_invoices()
        if hasattr(widget, "load_users"):
            widget.load_users()

        # Update button styles to highlight active one
        for i, btn in enumerate(self.nav_buttons):
            if i == index:
                btn.setStyleSheet(self.button_style(normal=False))
            else:
                btn.setStyleSheet(self.button_style(normal=True))

    def logout(self):
        from ui.login_window import LoginWindow
        self.login_window = LoginWindow()
        self.login_window.show()
        self.close()


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainWindow("admin", "Admin")
    window.show()
    sys.exit(app.exec())
