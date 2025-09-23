from __future__ import annotations

import math
import os
import subprocess
import sys

from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import (
    QDialog,
    QFileDialog,
    QHBoxLayout,
    QLabel,
    QMessageBox,
    QPushButton,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
)

from models.customer import Customer


class CustomerHistoryDialog(QDialog):
    """Dialog to display a customer's purchase history in a sortable, paginated table with export options."""

    def __init__(self, parent, customer_id: int, customer_name: str, page_size: int = 10):
        super().__init__(parent)
        self.setWindowTitle(f"Purchase History — {customer_name}")
        self.resize(640, 420)

        self.customer_id = customer_id
        self.customer_name = customer_name
        self._page_size = max(1, int(page_size))
        self._page = 1
        self._data: list[tuple[int, str, float]] = []

        main = QVBoxLayout()
        header = QLabel(f"Customer: {customer_name}")
        header.setAlignment(Qt.AlignmentFlag.AlignLeft)
        main.addWidget(header)

        self.table = QTableWidget(0, 3)
        self.table.setHorizontalHeaderLabels(["Invoice #", "Date", "Total"])
        self.table.setEditTriggers(self.table.EditTrigger.NoEditTriggers)
        self.table.setSelectionBehavior(self.table.SelectionBehavior.SelectRows)
        self.table.setSortingEnabled(True)
        main.addWidget(self.table)

        controls = QHBoxLayout()
        self.btn_prev = QPushButton("Previous")
        self.btn_prev.clicked.connect(self.prev_page)
        self.btn_next = QPushButton("Next")
        self.btn_next.clicked.connect(self.next_page)
        self.page_label = QLabel()
        controls.addWidget(self.btn_prev)
        controls.addWidget(self.page_label)
        controls.addWidget(self.btn_next)
        controls.addStretch(1)

        # Remove CSV export; keep only PDF export
        self.btn_export_pdf = QPushButton("Export PDF")
        self.btn_export_pdf.clicked.connect(self._export_pdf_interactive)
        controls.addWidget(self.btn_export_pdf)

        main.addLayout(controls)
        self.setLayout(main)

        self._load_data()
        self._refresh()

    # --- data loading and pagination ---
    def _load_data(self):
        # history rows: (invoice_id, invoice_date, total_amount)
        try:
            history = Customer.get_customer_purchase_history(self.customer_id)
        except Exception:
            history = []
        # Normalize to tuples
        self._data = [(int(h[0]), str(h[1]), float(h[2])) for h in history]
        self._page = 1

    def _refresh(self):
        total_pages = max(1, math.ceil(len(self._data) / self._page_size))
        self._page = min(max(1, self._page), total_pages)
        start = (self._page - 1) * self._page_size
        end = start + self._page_size
        page_rows = self._data[start:end]

        self.table.setRowCount(0)
        for r, (inv_id, inv_date, total) in enumerate(page_rows):
            self.table.insertRow(r)
            self.table.setItem(r, 0, QTableWidgetItem(str(inv_id)))
            self.table.setItem(r, 1, QTableWidgetItem(inv_date))
            self.table.setItem(r, 2, QTableWidgetItem(f"{total:.2f}"))
        self.page_label.setText(f"Page {self._page} of {total_pages}")
        self.btn_prev.setEnabled(self._page > 1)
        self.btn_next.setEnabled(self._page < total_pages)

    def next_page(self):
        self._page += 1
        self._refresh()

    def prev_page(self):
        self._page -= 1
        self._refresh()

    # --- export helpers usable by tests ---
    def export_pdf_to(self, file_path: str):
        # Minimal table PDF export
        from reportlab.lib import colors
        from reportlab.lib.pagesizes import A4
        from reportlab.lib.styles import getSampleStyleSheet
        from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle

        doc = SimpleDocTemplate(file_path, pagesize=A4, rightMargin=30, leftMargin=30, topMargin=30, bottomMargin=30)
        styles = getSampleStyleSheet()
        elems = [Paragraph(f"Purchase History — {self.customer_name}", styles["Title"]), Spacer(1, 8)]
        data = [["Invoice #", "Date", "Total"]]
        for inv_id, inv_date, total in self._data:
            data.append([str(inv_id), inv_date, f"{total:.2f}"])
        tbl = Table(data, hAlign="LEFT")
        tbl.setStyle(
            TableStyle(
                [
                    ("BACKGROUND", (0, 0), (-1, 0), colors.lightgrey),
                    ("GRID", (0, 0), (-1, -1), 0.25, colors.grey),
                    ("ALIGN", (2, 1), (2, -1), "RIGHT"),
                ]
            )
        )
        elems.append(tbl)
        doc.build(elems)

    # --- interactive wrappers ---
    def _export_pdf_interactive(self):
        path, _ = QFileDialog.getSaveFileName(self, "Export PDF", "history.pdf", "PDF Files (*.pdf)")
        if path:
            try:
                self.export_pdf_to(path)
                # Try to open the exported PDF with the system default viewer
                try:
                    if sys.platform.startswith("darwin"):
                        subprocess.Popen(["open", path])
                    elif os.name == "nt":
                        os.startfile(path)
                    else:
                        subprocess.Popen(["xdg-open", path])
                except Exception:
                    # Ignore open errors; still show a success message
                    pass
                QMessageBox.information(self, "Export Complete", f"PDF exported to:\n{path}")
            except Exception as e:
                QMessageBox.critical(self, "Export Failed", f"Could not export PDF:\n{e}")
