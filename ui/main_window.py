from PyQt6.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QStackedWidget, QLabel, QFrame
)
from PyQt6.QtCore import Qt
import sys

from ui.product_view import ProductView
from ui.customer_view import CustomerView
from ui.invoice_view import InvoiceView
from ui.receipt_view import ReceiptView
from ui.user_view import UserView


class MainWindow(QWidget):
    def __init__(self, logged_in_user):
        super().__init__()
        self.logged_in_user = logged_in_user
        self.setWindowTitle("QUALITYSOFT WHOLESALE MANAGEMENT SYSTEM")
        self.resize(1000, 700)
        self.setMinimumSize(600, 400)

        self.setStyleSheet("""
            QWidget {
                background-color: #F4F6F7;
            }
            QPushButton {
                padding: 10px 18px;
                border-radius: 6px;
                background-color: #2E86C1;
                color: white;
                font-size: 14px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #21618C;
            }
        """)

        main_layout = QVBoxLayout()

        # Top Title Bar
        title_bar = QLabel("QUALITYSOFT WHOLESALE MANAGEMENT SYSTEM")
        title_bar.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title_bar.setStyleSheet("font-size: 20px; font-weight: bold; padding: 12px; color: #2C3E50;")
        main_layout.addWidget(title_bar)

        # Top button bar layout
        button_bar = QHBoxLayout()
        button_bar.setSpacing(12)

        btn_products = QPushButton("🛒 Products")
        btn_products.clicked.connect(lambda: self.switch_view(0))
        button_bar.addWidget(btn_products)

        btn_customers = QPushButton("👥 Customers")
        btn_customers.clicked.connect(lambda: self.switch_view(1))
        button_bar.addWidget(btn_customers)

        btn_invoices = QPushButton("🧾 Invoices")
        btn_invoices.clicked.connect(lambda: self.switch_view(2))
        button_bar.addWidget(btn_invoices)

        btn_receipts = QPushButton("📄 Receipts")
        btn_receipts.clicked.connect(lambda: self.switch_view(3))
        button_bar.addWidget(btn_receipts)

        if self.logged_in_user == "admin":
            btn_users = QPushButton("🔐 Users")
            btn_users.clicked.connect(lambda: self.switch_view(4))
            button_bar.addWidget(btn_users)

        btn_logout = QPushButton("🚪 Logout")
        btn_logout.clicked.connect(self.logout)
        button_bar.addWidget(btn_logout)

        main_layout.addLayout(button_bar)

        # Horizontal separator
        separator = QFrame()
        separator.setFrameShape(QFrame.Shape.HLine)
        separator.setStyleSheet("color: #ccc;")
        main_layout.addWidget(separator)

        # Central stacked widget
        self.stacked_widget = QStackedWidget()
        self.stacked_widget.addWidget(ProductView())
        self.stacked_widget.addWidget(CustomerView())
        self.stacked_widget.addWidget(InvoiceView())
        self.stacked_widget.addWidget(ReceiptView())
        self.stacked_widget.addWidget(UserView())
        main_layout.addWidget(self.stacked_widget)

        self.setLayout(main_layout)

    def switch_view(self, index):
        self.stacked_widget.setCurrentIndex(index)
        widget = self.stacked_widget.currentWidget()
        if hasattr(widget, "load_customers"):
            widget.load_customers()
        if hasattr(widget, "load_products"):
            widget.load_products()
        if hasattr(widget, "load_invoice_ids"):
            widget.load_invoice_ids()
        if hasattr(widget, "load_users"):
            widget.load_users()

    def logout(self):
        from ui.login_window import LoginWindow
        self.login_window = LoginWindow()
        self.login_window.show()
        self.close()


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainWindow("admin")
    window.show()
    sys.exit(app.exec())
