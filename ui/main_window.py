from PyQt6.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QStackedWidget
)
from PyQt6.QtGui import QPalette, QBrush, QPixmap
from PyQt6.QtCore import QSize, Qt
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
        self.setMinimumSize(800, 500)

        self.set_background_image("bg_images/image1.png")

        # Main Layout
        main_layout = QHBoxLayout()

        # Sidebar Layout
        sidebar_layout = QVBoxLayout()
        sidebar_layout.setSpacing(20)

        btn_products = QPushButton("🛒 Products")
        btn_products.clicked.connect(lambda: self.switch_view(0))
        sidebar_layout.addWidget(btn_products)

        btn_customers = QPushButton("👥 Customers")
        btn_customers.clicked.connect(lambda: self.switch_view(1))
        sidebar_layout.addWidget(btn_customers)

        btn_invoices = QPushButton("🧾 Invoices")
        btn_invoices.clicked.connect(lambda: self.switch_view(2))
        sidebar_layout.addWidget(btn_invoices)

        btn_receipts = QPushButton("📄 Receipts")
        btn_receipts.clicked.connect(lambda: self.switch_view(3))
        sidebar_layout.addWidget(btn_receipts)

        # Only show User Management button if admin
        if self.logged_in_user == "admin":
            btn_users = QPushButton("🔐 Users")
            btn_users.clicked.connect(lambda: self.switch_view(4))
            sidebar_layout.addWidget(btn_users)

        sidebar_layout.addStretch()

        # Central stacked widget
        self.stacked_widget = QStackedWidget()
        self.stacked_widget.addWidget(ProductView())
        self.stacked_widget.addWidget(CustomerView())
        self.stacked_widget.addWidget(InvoiceView())
        self.stacked_widget.addWidget(ReceiptView())
        self.stacked_widget.addWidget(UserView())  # <--- instantiate the UserView correctly

        # Add layouts to main layout
        main_layout.addLayout(sidebar_layout)
        main_layout.addWidget(self.stacked_widget)

        self.setLayout(main_layout)

    def set_background_image(self, image_path):
        self.bg_pixmap = QPixmap(image_path)

    def resizeEvent(self, event):
        if hasattr(self, "bg_pixmap") and not self.bg_pixmap.isNull():
            scaled_pixmap = self.bg_pixmap.scaled(self.size(), Qt.AspectRatioMode.KeepAspectRatioByExpanding)
            palette = QPalette()
            palette.setBrush(QPalette.ColorRole.Window, QBrush(scaled_pixmap))
            self.setPalette(palette)
        super().resizeEvent(event)

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
        if hasattr(widget, "load_users"):
            widget.load_users()


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainWindow("admin")  # for testing directly from this file
    window.show()
    sys.exit(app.exec())
