from datetime import datetime

from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import QDialog, QDialogButtonBox, QLabel, QVBoxLayout

from utils.branding import APP_NAME, APP_VERSION, SUPPORT_EMAIL, SUPPORT_PHONES


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

        # Useful information for users (readable, brief)
        about_body = QLabel(
            """
            <div style='font-size:13px; color:#1f2937; line-height:1.6; margin-top:6px;'>
              <p><b>Overview:</b> Tradia helps you manage products, customers, invoices, and receipts with
              built-in backups and role-based access.</p>
              <p><b>Highlights:</b></p>
              <ul>
                <li>Inventory and pricing management</li>
                <li>Customer records with purchase history</li>
                <li>Invoicing with printable / PDF receipts</li>
                <li>Sales reports and graphs with product filter</li>
                <li>Configurable backups and retention</li>
              </ul>
              <p><i>Tip:</i> Start by adding products and customers,
              then create your first invoice from the Invoice tab.</p>
            </div>
            """
        )
        about_body.setTextFormat(Qt.TextFormat.RichText)
        about_body.setWordWrap(True)
        layout.addWidget(about_body)

        # Support & Contact
        support_hdr = QLabel("Support")
        support_hdr.setStyleSheet("font-weight:700; color:#111827; margin-top:10px; font-size:14px;")
        layout.addWidget(support_hdr)
        # Build contact HTML dynamically
        phones_html = " / ".join(f"<a href='tel:{p}'>{p}</a>" if p else "" for p in (SUPPORT_PHONES or []) if p)
        email_html = f"<a href='mailto:{SUPPORT_EMAIL}'>{SUPPORT_EMAIL}</a>" if SUPPORT_EMAIL else ""
        parts = ["<div style='font-size:13px; color:#1f2937; line-height:1.6;'>"]
        if email_html:
            parts.append(f"<p><b>Email:</b> {email_html}</p>")
        if phones_html:
            parts.append(f"<p><b>Contact:</b> {phones_html}</p>")
        parts.append("</div>")
        support_html = "".join(parts)
        support_txt = QLabel(support_html)
        support_txt.setTextFormat(Qt.TextFormat.RichText)
        support_txt.setOpenExternalLinks(True)
        support_txt.setWordWrap(True)
        layout.addWidget(support_txt)

        layout.addStretch(1)

        buttons = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok, parent=self)
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        # Hover style for OK button
        try:
            ok_btn = buttons.button(QDialogButtonBox.StandardButton.Ok)
            if ok_btn is not None:
                ok_btn.setStyleSheet(
                    "QPushButton { background-color: #1976d2; color: white; padding: 8px 16px; border-radius: 6px; }"
                    "QPushButton:hover { background-color: #1565c0; color: white; }"
                )
        except Exception:
            pass
        layout.addWidget(buttons)

        self.setLayout(layout)
