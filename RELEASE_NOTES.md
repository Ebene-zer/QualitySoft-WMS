# Tradia Release Notes

Version: 1.0.0
Release date: 2025-09-27

Overview
Tradia is a free, open-source Wholesale Management System (WMS) for Windows. This 1.0.0 release focuses on a stable, offline desktop experience with streamlined setup, secure login, robust backups, and practical day‑to‑day workflows.

Highlights
- Products and Customers management
- Invoices and Receipts (view/print/export)
- Secure login with roles; forced first-time Admin password change
- Activity Log for auditing (login attempts, password upgrades, etc.)
- Manual and automatic backups with retention
- PDF/Export using reportlab/fpdf/openpyxl
- Offline/local SQLite database with automatic migrations
- Free/open-source edition (legacy license/trial removed)

What’s New (since internal builds)
- Initial public free release (baseline schema v1)
- Activity Log added and wired into key flows
- Settings consolidated: backup directory, retention, and app preferences
- Forced first-time Admin password reset on first launch
- Default data path moved to user Documents: Documents/tradia/data/wholesale.db
- PyInstaller spec provided for reproducible packaging
- Removed legacy licensing/trial code and tables

Security & Reliability
- Passwords stored using PBKDF2-HMAC-SHA256; older hashes auto‑migrated on successful login
- Minimum password policy enforced (>=6 chars, at least one letter and one digit)
- Basic login throttling after repeated failures; attempts surfaced in Activity Log
- Backups are plain SQLite copies—keep backup folder secured if data is sensitive

Upgrade Notes
- Always make a manual backup before upgrading
- Database auto-migrates to the current baseline if needed (forward-only, idempotent)
- You can override data/DB locations via environment variables:
  - WMS_DB_NAME — full path to the SQLite file
  - TRADIA_DATA_DIR — parent directory for default database path
- When reducing backup retention in Settings, older backups are pruned after the next new backup is created

Known Limitations
- Backups are not encrypted
- Single-user desktop focus; no concurrent multi-user backend in this edition
- Internationalization and accessibility improvements planned for future releases

Getting Started
- From source: python -m main
- Installed executable: tradia.exe (via installer or portable build)
- First launch will prompt Admin to change the temporary password

Screenshots

Core workflow

- Login Window
  ![Login](https://github.com/Ebene-zer/Tradia/raw/main/assets/screenshots/login.png)

- Main Window / Dashboard
  ![Main Window](https://github.com/Ebene-zer/Tradia/raw/main/assets/screenshots/main_window.png)

- Product Management
  ![Products](https://github.com/Ebene-zer/Tradia/raw/main/assets/screenshots/products.png)

- Customer Management
  ![Customers](https://github.com/Ebene-zer/Tradia/raw/main/assets/screenshots/customers.png)

- New Invoice (Line Items, Discounts, Tax)
  ![Invoice](https://github.com/Ebene-zer/Tradia/raw/main/assets/screenshots/invoice.png)

- Receipt Viewer
  ![Receipt](https://github.com/Ebene-zer/Tradia/raw/main/assets/screenshots/receipt.png)

- Receipt Print Preview
  ![Receipt Preview](https://github.com/Ebene-zer/Tradia/raw/main/assets/screenshots/receipt_preview.png)

- Settings (Backup Path and Retention)
  ![Settings](https://github.com/Ebene-zer/Tradia/raw/main/assets/screenshots/Settings.png)

- Activity Log / Auditing
  ![Activity Log](https://github.com/Ebene-zer/Tradia/raw/main/assets/screenshots/activity_log.png)

Reports & Analytics

- Sales Overview
  ![Sales](https://github.com/Ebene-zer/Tradia/raw/main/assets/screenshots/sales.png)

- Graphs / Analytics
  ![Graphs](https://github.com/Ebene-zer/Tradia/raw/main/assets/screenshots/graph.png)

Admin

- Users Management
  ![Users](https://github.com/Ebene-zer/Tradia/raw/main/assets/screenshots/users.png)

Developer Notes
- Tests, lint, and type-check commands are documented in README.md
- Packaging via PyInstaller using tradia.spec bundles assets
- Environment variables: WMS_DB_NAME, TRADIA_DATA_DIR, SKIP_GUI_TESTS, TRADIA_RELAXED_PASSWORD_POLICY

Acknowledgements
Thanks to the PyQt6, SQLite, pandas, reportlab, fpdf, matplotlib communities.

Support
- For help, see the README “Author” section or open an issue in the repository.
