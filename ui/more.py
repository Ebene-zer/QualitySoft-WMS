from PyQt6.QtWidgets import QDialog, QFormLayout, QComboBox, QDialogButtonBox, QMessageBox, QVBoxLayout, QLabel, QWidget, QPushButton, QHBoxLayout
from PyQt6.QtCore import Qt, QTimer
import datetime
from database.db_handler import get_db_connection
import matplotlib.pyplot as plt
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas

# Embedded widget for sales report
class SalesReportWidget(QWidget):
    def __init__(self, user_role, parent=None):
        super().__init__(parent)
        self.user_role = user_role
        layout = QFormLayout(self)
        self.setStyleSheet("""
            background-color: #f8fafc;
            border-radius: 12px;
            padding: 18px;
        """)
        self.report_type_box = QComboBox(self)
        self.report_type_box.setMinimumHeight(40)
        self.report_type_box.setStyleSheet("font-size: 18px; background-color: #e3eafc; border-radius: 8px; padding: 6px;")
        report_types = ["Daily"]
        if self.user_role.lower() in ["admin", "ceo"]:
            report_types += ["Weekly", "Monthly", "Annual"]
        self.report_type_box.addItems(report_types)
        layout.addRow("<span style='color:#1a237e;font-weight:bold;'>Report Type:</span>", self.report_type_box)
        self.show_btn = QPushButton("Show Report")
        self.show_btn.setMinimumHeight(38)
        self.show_btn.setStyleSheet("background-color: #1976d2; color: white; font-size: 16px; border-radius: 8px; padding: 8px 18px;")
        layout.addWidget(self.show_btn)
        self.show_btn.clicked.connect(self.generate_sales_report)
        self.result_label = QLabel()
        self.result_label.setWordWrap(True)
        self.result_label.setStyleSheet("font-size: 20px; color: #263238; font-weight: bold; padding: 16px; background-color: #e3f2fd; border-radius: 8px;")
        layout.addWidget(self.result_label)
        self.setLayout(layout)
        # Auto-generate report if only one option (for Manager)
        if self.report_type_box.count() == 1:
            self.show_btn.setVisible(False)
            self.generate_sales_report()  # Call directly instead of using QTimer
        else:
            self.show_btn.setVisible(True)

    def generate_sales_report(self):
        report_type = self.report_type_box.currentText()
        conn = get_db_connection()
        cursor = conn.cursor()
        today = datetime.date.today()
        if report_type == "Daily":
            start = today.strftime('%Y-%m-%d')
            end = start
        elif report_type == "Weekly":
            start = (today - datetime.timedelta(days=today.weekday())).strftime('%Y-%m-%d')
            end = today.strftime('%Y-%m-%d')
        elif report_type == "Monthly":
            start = today.replace(day=1).strftime('%Y-%m-%d')
            end = today.strftime('%Y-%m-%d')
        elif report_type == "Annual":
            start = today.replace(month=1, day=1).strftime('%Y-%m-%d')
            end = today.strftime('%Y-%m-%d')
        else:
            self.result_label.setText("Invalid report type selected.")
            return
        cursor.execute("""
            SELECT invoice_date, total_amount FROM invoices
            WHERE DATE(invoice_date) BETWEEN ? AND ?
        """, (start, end))
        rows = cursor.fetchall()
        total_sales = sum(row[1] for row in rows)
        report_msg = f"{report_type} Sales Report\nPeriod: {start} to {end}\nTotal Sales: GHS{total_sales:,.2f}\nTransactions: {len(rows)}"
        self.result_label.setText(report_msg)
        conn.close()

# Embedded widget for graph
class GraphWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        layout = QVBoxLayout(self)
        self.setStyleSheet("""
            background-color: #f8fafc;
            border-radius: 12px;
            padding: 18px;
        """)
        controls_layout = QHBoxLayout()
        self.type_box = QComboBox()
        self.type_box.setMinimumHeight(40)
        self.type_box.setStyleSheet("font-size: 18px; background-color: #e3eafc; border-radius: 8px; padding: 6px;")
        self.type_box.addItems(["Line Chart", "Bar Chart"])
        self.period_box = QComboBox()
        self.period_box.setMinimumHeight(40)
        self.period_box.setStyleSheet("font-size: 18px; background-color: #e3eafc; border-radius: 8px; padding: 6px;")
        self.period_box.addItems(["Monthly", "Yearly"])
        controls_layout.addWidget(QLabel("<span style='color:#1a237e;font-weight:bold;'>Graph Type:</span>"))
        controls_layout.addWidget(self.type_box)
        controls_layout.addWidget(QLabel("<span style='color:#1a237e;font-weight:bold;'>Period:</span>"))
        controls_layout.addWidget(self.period_box)
        show_btn = QPushButton("Show Graph")
        show_btn.setMinimumHeight(38)
        show_btn.setStyleSheet("background-color: #1976d2; color: white; font-size: 16px; border-radius: 8px; padding: 8px 18px;")
        show_btn.clicked.connect(self.show_graph)
        controls_layout.addWidget(show_btn)
        layout.addLayout(controls_layout)
        self.figure = plt.Figure()
        self.canvas = FigureCanvas(self.figure)
        self.canvas.setStyleSheet("background-color: #e3f2fd; border-radius: 8px;")
        layout.addWidget(self.canvas)
        self.setLayout(layout)

    def show_graph(self):
        graph_type = self.type_box.currentText()
        period = self.period_box.currentText()
        conn = get_db_connection()
        cursor = conn.cursor()
        if period == "Monthly":
            cursor.execute("""
                SELECT strftime('%Y-%m', invoice_date) as period, SUM(total_amount) as total
                FROM invoices
                GROUP BY period
                ORDER BY period
            """)
            x = []
            y = []
            for row in cursor.fetchall():
                x.append(row[0])
                y.append(row[1])
            xlabel = "Month"
        else:
            cursor.execute("""
                SELECT strftime('%Y', invoice_date) as period, SUM(total_amount) as total
                FROM invoices
                GROUP BY period
                ORDER BY period
            """)
            x = []
            y = []
            for row in cursor.fetchall():
                x.append(row[0])
                y.append(row[1])
            xlabel = "Year"
        conn.close()
        self.figure.clear()
        ax = self.figure.add_subplot(111)
        if graph_type == "Line Chart":
            ax.plot(x, y, marker='o')
        else:
            ax.bar(x, y)
        ax.set_xlabel(xlabel)
        ax.set_ylabel("Total Sales")
        ax.set_title(f"Sales by {xlabel}")
        self.figure.tight_layout()
        self.canvas.draw()

class MoreDropdown(QWidget):
    def __init__(self, on_option_selected=None, parent=None, user_role=None):
        super().__init__(parent)
        self.user_role = user_role  # Store user_role for later use
        layout = QVBoxLayout(self)
        self.dropdown = QComboBox()
        self.dropdown.setMinimumWidth(200)
        self.dropdown.setMinimumHeight(35)
        self.dropdown.setStyleSheet("font-size: 16px;")
        # Only show 'Graph' if user is admin or ceo
        items = ["Sales Report"]
        if user_role and user_role.lower() in ["admin", "ceo"]:
            items.append("Graph")
        self.dropdown.addItems(items)
        self.dropdown.setEditable(True)
        self.dropdown.lineEdit().setReadOnly(True)
        self.dropdown.lineEdit().setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.dropdown.lineEdit().returnPressed.connect(self._on_enter)
        layout.addWidget(self.dropdown)
        # Add a content area for feature widgets
        self.content_area = QVBoxLayout()
        layout.addLayout(self.content_area)
        layout.addStretch(1)  # Push everything up
        self.setLayout(layout)
        self.on_option_selected = on_option_selected
        self.dropdown.currentIndexChanged.connect(self._on_index_changed)

    def _on_index_changed(self, index):
        # Clear content area
        while self.content_area.count():
            child = self.content_area.takeAt(0)
            if child.widget():
                child.widget().deleteLater()
        self.current_widget = None  # Keep a reference to prevent garbage collection
        if self.dropdown.itemText(index) == "Sales Report":
            report_widget = SalesReportWidget(self.user_role, self)
            self.content_area.addWidget(report_widget)
            report_widget.show()
            self.current_widget = report_widget
        elif self.dropdown.itemText(index) == "Graph":
            graph_widget = GraphWidget(self)
            self.content_area.addWidget(graph_widget)
            graph_widget.show()
            self.current_widget = graph_widget
        if self.on_option_selected:
            self.on_option_selected(index)

    def _on_enter(self):
        # Simulate dropdown selection on Enter key
        index = self.dropdown.currentIndex()
        self.dropdown.setCurrentIndex(index)
        # _on_index_changed will be triggered automatically
