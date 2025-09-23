# Tradia

Version: 1.0.0

An easy-to-use Wholesale Management System (WMS) for Windows desktops. Manage products, customers, invoices, receipts, users, and safe local backups. Designed for small / medium wholesale businesses that need an offline, self‑contained solution.

## Author
- Product: Tradia
- Developer: Ebenezer Fuachie
- Year: 2025
- Email: fuachiee717@gmail.com
- Phone: +233 548253251

---
## At a Glance
| Feature | Status |
|---------|--------|
| Products & Customers | ✅ |
| Invoices & Receipts | ✅ |
| User Roles & Secure Login | ✅ |
| Forced First-Time Admin Password Reset | ✅ |
| 14‑Day Trial + Product Pin Unlock | ✅ |
| Manual + Automatic Backups | ✅ |
| Backup Retention & Custom Location | ✅ |
| PDF / Export (fpdf, reportlab, openpyxl) | ✅ |
| Offline (No Internet Needed) | ✅ |

---
## System Requirements
- Windows 10 / 11 (64‑bit recommended)
- RAM: 4 GB minimum
- Disk: < 200 MB (plus data growth)
- No external database or internet required

---
## Installation (End Users – Executable Distribution)
1. Receive the installer or portable ZIP from the developer or official source.
2. If installer: Run it and follow prompts.
3. If ZIP: Extract to a writable folder (e.g. `C:\tradia`).
4. Launch `tradia.exe`.
5. First launch will display a temporary Admin password – copy it somewhere safe (one‑time view).
6. Log in as Admin → you will be forced to set a new secure password.
7. Start entering Products & Customers, then create Invoices.

### Portable vs Installed
- Portable: Just delete the folder to remove (keep `wholesale.db` if you want to retain data).
- Installed: Use Windows “Add or Remove Programs”.

---
## Trial & Activation
- A 14‑day evaluation period starts automatically on first launch.
- After the trial ends, the Product Pin dialog appears and the application requires a valid activation Pin to continue normal usage.
- A Request Code (UUID) is displayed to help authorized distributors generate a Pin.
- Do not attempt to modify application data or files to circumvent activation—this may corrupt data and violates product terms.

---
## Backups (Highly Recommended)
| Mode | How |
|------|-----|
| Manual | Settings → Backup Now |
| Automatic | On app exit if > 24h since last backup |

- Default location (if none set): `Documents/tradia/backups`
- Filenames: `backup_YYYYmmdd_HHMMSS.db`
- Retention: Only the most recent N backups (configurable) are kept. Lowering the retention value prunes older backups the next time a new backup is created.
- To restore: Close app → (Optional but recommended: make a copy of the current `wholesale.db`) → Replace `wholesale.db` with chosen backup copy → Reopen.
- Keep periodic off‑machine backups (USB / cloud sync) for disaster recovery.

> Backups are plain SQLite database copies (not encrypted). Secure the directory if data is sensitive.

---
## Quick Start Workflow
1. Launch app → Change temporary Admin password.
2. Add initial Products (stock quantity validated).
3. Add Customers.
4. Create an Invoice (adds line items, tax / discount optional).
5. View Receipts to reprint / export.
6. Open Settings → Configure backup directory + retention.
7. Before the trial ends, ensure you have obtained an activation Product Pin.

---
## Security (User-Facing Summary)
- Passwords stored hashed (PBKDF2-HMAC-SHA256).
- No password recovery—keep credentials safe.
- Product activation (Pin) is required after trial expiration; unauthorized alterations to data files to bypass activation may result in access issues or data loss.
- Backups & DB are unencrypted; apply OS / physical security where appropriate.

---
## Updating the Application
1. Perform a Manual Backup first. (This creates a timestamped copy you can revert to.)
2. Replace old executable/ folder or run new installer.
3. Existing `wholesale.db` is reused automatically (migrations run if needed).

### Database File Location
- Primary data file: `wholesale.db` (default stored alongside the executable unless `WMS_DB_NAME` env var overrides path).
- Backups remain in the configured backup directory.

---
## Uninstalling
- Backup data if needed.
- Remove installation folder or uninstall via Control Panel (installer builds).
- Delete or archive backup directory optionally.

---
## Troubleshooting (End Users)
| Issue | Resolution |
|-------|------------|
| App does not start | Re-download, ensure AV did not quarantine, run as standard user. |
| Trial expired | Enter Product Pin when activation dialog appears. |
| Cannot save backup | Select a writable directory in Settings (avoid Program Files). |
| Login role mismatch | Ensure correct role is selected in the dropdown before authenticating. |
| Missing recent data | Restore from latest backup (close app first). |

Support: Email or call the contacts in Author section.

---
## Privacy
- All data local. No telemetry, no external sync.
- You fully control your business records.

---
## Developer / Technical Section
(Skip if you only use the packaged executable.)

### Environment Setup
```
python -m venv .venv
.venv\Scripts\activate
pip install -e .[dev]
```

### Run From Source
```
python -m main
```
Or (after install):
```
tradia
```

### Tests & Quality
```
pytest -q
coverage run -m pytest && coverage report
ruff check .
ruff format .
mypy .
```

### Migrations
- Forward-only, auto-run at startup.
- schema_version progression: 1 (base) → 2 (backup_directory) → 3 (retention_count).

### Packaging (PyInstaller example)
```
pyinstaller --noconfirm --noconsole --name tradia \
  --add-data "icons;icons" main.py
```
Add code signing for production distribution (optional but recommended).

### Environment Variables
- WMS_DB_NAME – override DB path (testing / multi-instance)
- SKIP_GUI_TESTS=1 – skip GUI test execution in CI/headless

---
## Changelog (Summary)
- 1.0.0: First stable release (core management, trial, activation, backup + retention, migrations v1–v3, forced admin password reset).

## Roadmap (Selected)
- Role-based permission matrix
- Encrypted/signed license artifacts
- Encrypted backups & scheduled service
- Analytics / dashboards (optional)
- Internationalization & accessibility improvements

### Planned Transition to a Web-Based Platform
*Unchanged from previous description (strategic roadmap retained).*

**Phase 1 – Service-Oriented Core (Foundations)**
- Extract core business logic (products, customers, invoicing, licensing) into a shared, testable service layer.
- Introduce REST/GraphQL API backend (likely FastAPI or Django REST Framework) while keeping the desktop app operational.
- Migrate from direct SQLite access to an abstraction that can target PostgreSQL in production while still supporting SQLite for local / demo use.

**Phase 2 – Authentication & Security Enhancements**
- Centralized user management (JWT / OAuth2).
- Role + permission matrix (granular feature flags: inventory adjust, financial reports, user admin, etc.).
- Optional MFA (TOTP/email).

**Phase 3 – Web Front-End**
- SPA (React / Vue / Svelte) or lightweight server-rendered UI (if rapid adoption preferred).
- Responsive UI for tablets (warehouse floor usage).
- Reusable component library (design system for forms, tables, receipt previews).

**Phase 4 – Data & Scaling**
- Primary DB: PostgreSQL (transactions, concurrency, reporting views).
- Background workers (Celery / RQ) for heavy PDF/report generation, scheduled backups, license checks.
- Object storage (receipts, exports) with signed URL access.

**Phase 5 – Migration & Coexistence**
- Desktop → Web migration tool: exports existing `wholesale.db` data (products, customers, invoices, users) to the hosted platform via secure import.
- Transitional hybrid mode: desktop app can operate in “sync” mode (optional) until full web adoption.

**Phase 6 – Advanced Web Features**
- Real-time inventory adjustments (WebSockets or Server-Sent Events).
- Audit trails & change history (per record).
- Multi-tenant hosting (isolation per company) for SaaS deployment.

**Phase 7 – Observability & Operations**
- Central logging, metrics (Prometheus / OpenTelemetry), anomaly alerts (e.g. sudden stock drops).
- Automated nightly encrypted backups + retention policies per tenant.

**Data Migration Strategy (High Level)**
1. Versioned export from current schema (v1–v3).
2. Transform & load scripts (ETL) for PostgreSQL target schema.
3. Validation pass (row counts, integrity, sample invoice totals).
4. Dry-run before production cutover.

**Why This Matters**
- Enables multi-user concurrency beyond local file locking.
- Facilitates permission granularity and audit logging.
- Supports centralized deployment, updates, and managed backups.

**Desktop App Maintenance Policy (Post-Web Launch)**
- Desktop edition remains supported for single-location offline clients.
- Critical fixes (security / data integrity) prioritized; new feature focus shifts to web.

> This plan is iterative and may adjust based on user feedback and adoption priorities.

## License
Apache License 2.0 (see LICENSE file).

## Disclaimer
Provided “as‑is” without warranty. Assess legal/regulatory suitability before production use.

## Acknowledgements
- PyQt6, SQLite, pandas, reportlab, fpdf, matplotlib contributors.

---
© 2025 Ebenezer Fuachie
