from PyQt6.QtWidgets import QApplication, QWidget, QVBoxLayout, QPushButton, QMessageBox
from PyQt6.QtCore import QSize, Qt
from PyQt6.QtGui import QPalette, QBrush, QPixmap
import sys

# Import product window (which we'll build next)
from ui.product_window import ProductWindow

class MainWindow(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("QualitySoft WHOLESALE MANAGEMENT SYSTEM")
        self.resize(800, 600)
        self.setMinimumSize(600, 400)

        self.set_background_image("bg_images/main2.jpeg")

        layout = QVBoxLayout()

        self.product_button = QPushButton("🛒 Manage Products")
        self.product_button.clicked.connect(self.open_product_window)
        layout.addWidget(self.product_button)

        self.customer_button = QPushButton("👥 Manage Customers")
        self.customer_button.clicked.connect(self.show_placeholder)
        layout.addWidget(self.customer_button)

        self.invoice_button = QPushButton("🧾 Create Invoice")
        self.invoice_button.clicked.connect(self.show_placeholder)
        layout.addWidget(self.invoice_button)

        self.receipt_button = QPushButton("📄 View Receipts")
        self.receipt_button.clicked.connect(self.show_placeholder)
        layout.addWidget(self.receipt_button)

        self.setLayout(layout)

    def set_background_image(self, image_path):
        palette = QPalette()
        pixmap = QPixmap(image_path)
        if not pixmap.isNull():
            scaled_pixmap = pixmap.scaled(self.size(), Qt.AspectRatioMode.IgnoreAspectRatio)
            palette.setBrush(QPalette.ColorRole.Window, QBrush(scaled_pixmap))
            self.setPalette(palette)

    def open_product_window(self):
        self.product_window = ProductWindow()
        self.product_window.show()

    def show_placeholder(self):
        QMessageBox.information(self, "Info", "This feature is coming soon.")

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())
