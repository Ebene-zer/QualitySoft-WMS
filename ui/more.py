import os
import sys

# Force non-interactive backend early for CI / headless tests to avoid hangs
if os.environ.get("QT_QPA_PLATFORM") == "offscreen" or "pytest" in sys.modules:
    try:
        import matplotlib

        matplotlib.use("Agg")  # Must be set before importing pyplot
    except Exception:
        pass

import datetime

import matplotlib.pyplot as plt
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from PyQt6.QtCore import QPoint, Qt, QTimer
from PyQt6.QtWidgets import (
    QComboBox,
    QFormLayout,
    QHBoxLayout,
    QHeaderView,
    QLabel,
    QPushButton,
    QTableWidget,
    QTableWidgetItem,
    QToolTip,
    QVBoxLayout,
    QWidget,
)

from database.db_handler import get_db_connection
from models.product import Product
from utils import period_bounds
from utils.activity_log import fetch_recent
from utils.ui_common import format_money


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
        self.report_type_box.setStyleSheet(
            "font-size: 18px; background-color: #e3eafc; border-radius: 8px; padding: 6px;"
        )
        report_types = ["Daily"]
        if self.user_role.lower() in ["admin", "ceo"]:
            report_types += ["Weekly", "Monthly", "Annual"]
        self.report_type_box.addItems(report_types)
        layout.addRow("<span style='color:#1a237e;font-weight:bold;'>Report Type:</span>", self.report_type_box)
        self.show_btn = QPushButton("Show Report")
        self.show_btn.setMinimumHeight(38)
        self.show_btn.setStyleSheet(
            "background-color: #1976d2; color: white; font-size: 16px; border-radius: 8px; padding: 8px 18px;"
        )
        layout.addWidget(self.show_btn)
        self.show_btn.clicked.connect(self.generate_sales_report)
        self.result_label = QLabel()
        self.result_label.setWordWrap(True)
        # Remove global bold so HTML controls which parts are bold
        self.result_label.setStyleSheet(
            "font-weight: bold; color: #263238; padding: 16px; background-color: #e3f2fd; border-radius: 8px;"
        )
        # Use rich text so we can style labels and values separately
        self.result_label.setTextFormat(Qt.TextFormat.RichText)
        layout.addWidget(self.result_label)
        self.setLayout(layout)
        # Always show the button (previously hidden when only one report type)
        # Still auto-generate when there is only one option for convenience.
        if self.report_type_box.count() == 1:
            QTimer.singleShot(0, self.generate_sales_report)
        else:
            self.show_btn.setVisible(True)

    def generate_sales_report(self):
        """Generate sales report safely; avoid crashes if widget/label was deleted."""
        report_type = self.report_type_box.currentText()
        conn = get_db_connection()
        try:
            cursor = conn.cursor()
            today = datetime.date.today()

            # Use centralized helper for period bounds (end-exclusive)
            kind_map = {
                "Daily": "today",
                "Weekly": "this_week",
                "Monthly": "this_month",
                "Annual": "this_year",
            }
            kind = kind_map.get(report_type)
            if not kind:
                return
            start_iso, end_iso = period_bounds(today, kind)

            # SQL uses timestamps; append midnight time component
            iso_start = f"{start_iso} 00:00:00"
            iso_end = f"{end_iso} 00:00:00"

            cursor.execute(
                """
                SELECT COALESCE(SUM(total_amount), 0.0) AS total_sales,
                       COUNT(*) AS txns
                FROM invoices
                WHERE invoice_date >= ? AND invoice_date < ?
                """,
                (iso_start, iso_end),
            )
            agg = cursor.fetchone() or (0.0, 0)
            total_sales = float(agg[0] or 0.0)
            txns = int(agg[1] or 0)

            # Convert to display day/month/year; display end is inclusive (end - 1 day)
            try:
                start_date = datetime.date.fromisoformat(start_iso)
                end_exclusive = datetime.date.fromisoformat(end_iso)
                display_start = start_date.strftime("%d/%m/%Y")
                display_end = (end_exclusive - datetime.timedelta(days=1)).strftime("%d/%m/%Y")
            except Exception:
                display_start = start_iso
                display_end = end_iso

            if txns == 0:
                report_html = (
                    f"<span style='font-weight:Bold; font-size:18px; color:#1a237e;'>No sales found</span><br/>"
                    f"<span style='font-weight:Bold; font-size:16px; color:#00000e;'>Period:</span> "
                    f"<span style='font-family:Segue UI; font-size:14px; color:#263238;'>"
                    f"{display_start} to {display_end}</span>"
                )
            else:
                report_html = (
                    f"<span style='font-weight:Bold; font-size:18px; color:#1a237e;'>"
                    f"{report_type} Sales Report</span><br/>"
                    f"<span style='font-weight:Bold; font-size:16px; color:#00000e;'>Period:</span> "
                    f"<span style='font-family:Segue UI; font-size:14px; color:#263238;'>"
                    f"{display_start} to {display_end}</span><br/>"
                    f"<span style='font-weight:Bold; font-size:16px; color:#00000e;'>Total Sales:</span> "
                    f"<span style='font-family:Segue UI; font-size:14px; color:#263238;'>"
                    f"{format_money(total_sales)}</span><br/>"
                    f"<span style='font-weight:Bold; font-size:16px; color:#00000e;'>Transactions:</span> "
                    f"<span style='font-family:Segue UI; font-size:14px; color:#263238;'>{txns}</span>"
                )

            # Safely update label; it might be deleted if the widget was torn down
            try:
                if hasattr(self, "result_label") and self.result_label is not None:
                    self.result_label.setText(report_html)
            except RuntimeError:
                # Underlying C++ object deleted; ignore
                pass
        finally:
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
        # Add product filter (default: All Products)
        controls_layout.addWidget(QLabel("<span style='color:#1a237e;font-weight:bold;'>Graph Type:</span>"))
        controls_layout.addWidget(self.type_box)
        controls_layout.addWidget(QLabel("<span style='color:#1a237e;font-weight:bold;'>Period:</span>"))
        controls_layout.addWidget(self.period_box)
        controls_layout.addWidget(QLabel("<span style='color:#1a237e;font-weight:bold;'>Product:</span>"))
        self.product_box = QComboBox()
        self.product_box.setMinimumHeight(40)
        self.product_box.setStyleSheet("font-size: 18px; background-color: #e3eafc; border-radius: 8px; padding: 6px;")
        controls_layout.addWidget(self.product_box)
        # Populate products
        self._load_products()
        show_btn = QPushButton("Show Graph")
        show_btn.setMinimumHeight(38)
        show_btn.setStyleSheet(
            "background-color: #1976d2; color: white; font-size: 16px; border-radius: 8px; padding: 8px 18px;"
        )
        show_btn.clicked.connect(self.show_graph)
        controls_layout.addWidget(show_btn)
        layout.addLayout(controls_layout)
        self.figure = plt.Figure()
        self.canvas = FigureCanvas(self.figure)
        self.canvas.setStyleSheet("background-color: #e3f2fd; border-radius: 8px;")
        layout.addWidget(self.canvas)
        self.setLayout(layout)
        # State for tooltips
        self._hover_cid = None
        self._plot_kind = None
        self._bars = []
        self._data_labels = []
        self._data_values = []

    def _load_products(self):
        try:
            self.product_box.blockSignals(True)
            self.product_box.clear()
            self.product_box.addItem("All Products")
            for p in Product.get_all_products():
                self.product_box.addItem(f"{p.product_id} - {p.name}")
        except Exception:
            # Fallback to only All Products if model access fails
            if self.product_box.count() == 0:
                self.product_box.addItem("All Products")
        finally:
            self.product_box.blockSignals(False)

    def show_graph(self):
        graph_type = self.type_box.currentText()
        period = self.period_box.currentText()
        # Determine selected product (None means all)
        sel = self.product_box.currentText() if hasattr(self, "product_box") else "All Products"
        product_id = None
        product_label = None
        if sel and sel != "All Products":
            try:
                product_id = int(sel.split(" - ")[0])
                product_label = sel.split(" - ", 1)[1]
            except Exception:
                product_id = None
                product_label = None
        conn = get_db_connection()
        cursor = conn.cursor()
        if period == "Monthly":
            if product_id is None:
                cursor.execute(
                    """
                    SELECT strftime('%Y-%m', invoice_date) as period, SUM(total_amount) as total
                    FROM invoices
                    GROUP BY period
                    ORDER BY period
                    """
                )
            else:
                cursor.execute(
                    """
                    SELECT strftime('%Y-%m', i.invoice_date) as period,
                           SUM(ii.quantity * ii.unit_price) as total
                    FROM invoices i
                    JOIN invoice_items ii ON ii.invoice_id = i.invoice_id
                    WHERE ii.product_id = ?
                    GROUP BY period
                    ORDER BY period
                    """,
                    (product_id,),
                )
            x = []
            y = []
            for row in cursor.fetchall():
                x.append(row[0])
                y.append(row[1])
            xlabel = "Month"
        else:
            if product_id is None:
                cursor.execute(
                    """
                    SELECT strftime('%Y', invoice_date) as period, SUM(total_amount) as total
                    FROM invoices
                    GROUP BY period
                    ORDER BY period
                    """
                )
            else:
                cursor.execute(
                    """
                    SELECT strftime('%Y', i.invoice_date) as period,
                           SUM(ii.quantity * ii.unit_price) as total
                    FROM invoices i
                    JOIN invoice_items ii ON ii.invoice_id = i.invoice_id
                    WHERE ii.product_id = ?
                    GROUP BY period
                    ORDER BY period
                    """,
                    (product_id,),
                )
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
            ax.plot(x, y, marker="o")
            self._plot_kind = "line"
            self._bars = []
        else:
            bars = ax.bar(x, y)
            self._plot_kind = "bar"
            self._bars = list(bars)
        # Store data for tooltip
        self._data_labels = list(x)
        self._data_values = list(y)
        ax.set_xlabel(xlabel)
        ax.set_ylabel("Total Sales")
        title_extra = f" for {product_label}" if product_label else ""
        ax.set_title(f"Sales{title_extra} by {xlabel}")
        self.figure.tight_layout()
        self.canvas.draw()
        # Connect hover handler for tooltips
        try:
            if self._hover_cid is not None:
                self.canvas.mpl_disconnect(self._hover_cid)
        except Exception:
            pass
        self._hover_cid = self.canvas.mpl_connect("motion_notify_event", self._on_motion)

    def _on_motion(self, event):
        # Hide tooltip if not over axes
        if event is None or event.inaxes is None:
            QToolTip.hideText()
            return
        try:
            # Compute and show tooltip
            text = None
            if self._plot_kind == "bar" and self._bars:
                for idx, rect in enumerate(self._bars):
                    contains, _ = rect.contains(event)
                    if contains:
                        label = str(self._data_labels[idx]) if idx < len(self._data_labels) else ""
                        value = self._data_values[idx] if idx < len(self._data_values) else ""
                        text = f"{label}: {format_money(value)}"
                        break
            elif self._plot_kind == "line" and self._data_values:
                # Find nearest data point in pixel space
                ax = event.inaxes
                trans = ax.transData.transform
                mx, my = event.x, event.y
                best_idx = None
                best_dist2 = float("inf")
                # With categorical x, data x positions map to indices 0..N-1
                for i, val in enumerate(self._data_values):
                    px, py = trans((i, val))
                    d2 = (px - mx) ** 2 + (py - my) ** 2
                    if d2 < best_dist2:
                        best_dist2 = d2
                        best_idx = i
                # 10px threshold
                if best_idx is not None and best_dist2 <= 10**2:
                    label = str(self._data_labels[best_idx]) if best_idx < len(self._data_labels) else ""
                    value = self._data_values[best_idx]
                    text = f"{label}: {format_money(value)}"
            if text:
                # Show tooltip near cursor
                try:
                    gp = self.canvas.mapToGlobal(QPoint(int(event.x), int(event.y)))
                except Exception:
                    # Fallback: show without position binding
                    gp = None
                QToolTip.showText(gp, text, self.canvas)
            else:
                QToolTip.hideText()
        except Exception:
            # Never break interaction due to tooltip issues
            pass


# Embedded widget for activity log
class ActivityLogWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        layout = QVBoxLayout(self)

        # Simple table without extra controls or heavy styling
        self.table = QTableWidget()
        self.table.setColumnCount(4)
        self.table.setHorizontalHeaderLabels(["Timestamp", "User", "Action", "Details"])
        self.table.setEditTriggers(self.table.EditTrigger.NoEditTriggers)
        # Apply requested styling: header bold black 16px; data 14px
        self.table.setStyleSheet(
            "QHeaderView::section { font-weight: bold; color: black; font-size: 16px; }\n"
            "QTableWidget { font-size: 14px; }"
        )
        header = self.table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(2, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(3, QHeaderView.ResizeMode.Stretch)
        self.table.verticalHeader().setVisible(False)

        layout.addWidget(self.table)
        self.setLayout(layout)
        self.load_logs()

    def load_logs(self):
        rows = fetch_recent(200)
        tbl = self.table
        tbl.setSortingEnabled(False)
        tbl.setRowCount(len(rows))
        for r_idx, row in enumerate(rows):
            # row: (timestamp, username, action, details)
            ts, user, action, details = row
            for c_idx, val in enumerate((ts, user, action, details)):
                item = QTableWidgetItem(str(val))
                item.setFlags(item.flags() & ~Qt.ItemFlag.ItemIsEditable)
                tbl.setItem(r_idx, c_idx, item)
        tbl.setSortingEnabled(True)


class MoreDropdown(QWidget):
    def __init__(self, on_option_selected=None, parent=None, user_role: str = "Manager"):
        super().__init__(parent)
        self.on_option_selected = on_option_selected
        self.user_role = user_role
        outer = QVBoxLayout(self)
        self.dropdown = QComboBox()
        outer.addWidget(self.dropdown)
        self.content_area = QWidget()
        self.content_layout = QVBoxLayout(self.content_area)
        self.content_layout.setContentsMargins(0, 0, 0, 0)
        outer.addWidget(self.content_area)
        # Options by role
        role = (user_role or "").lower()
        options = ["Sales Report"]
        if role in ("admin", "ceo"):
            options += ["Graph", "Activity Log"]
        self.dropdown.addItems(options)
        self.dropdown.currentIndexChanged.connect(self._on_index_changed)
        # Default: show Sales Report
        self.current_widget: QWidget | None = None
        self._on_index_changed(0)

    def _on_index_changed(self, index: int):
        # Clear current widget
        if self.current_widget is not None:
            self.current_widget.setParent(None)
            self.current_widget.deleteLater()
            self.current_widget = None
        label = self.dropdown.itemText(index)
        if label == "Sales Report":
            self.current_widget = SalesReportWidget(user_role=self.user_role)
        elif label == "Graph":
            self.current_widget = GraphWidget()
        elif label == "Activity Log":
            self.current_widget = ActivityLogWidget()
        else:
            self.current_widget = QWidget()
        self.content_layout.addWidget(self.current_widget)
        if callable(self.on_option_selected):
            try:
                self.on_option_selected(label)
            except Exception:
                pass

    def _on_enter(self):
        # Hook for keyboard navigation; optional
        self.dropdown.setFocus()
