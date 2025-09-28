# Tradia

Version: 1.0.0

[Release Notes (v1.0.0) — includes screenshots of key features](RELEASE_NOTES.md)

An easy-to-use Wholesale Management System (WMS) for Windows desktops (FREE / open-source edition). Manage products, customers, invoices, receipts, users, backups, and view an activity log for auditing. Offline, self‑contained.

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
| Activity Log / Auditing | ✅ |
| Manual + Automatic Backups | ✅ |
| Backup Retention & Custom Location | ✅ |
| PDF / Export (fpdf, reportlab, openpyxl) | ✅ |
| Offline (No Internet Needed) | ✅ |
| License / Activation | ❌ (Removed in free edition) |

> This repository now represents the free, fully unlocked edition. Prior trial / activation mechanics were removed for simplicity and openness.

---
## System Requirements
- Windows 10 / 11 (64‑bit recommended)
- RAM: 4 GB minimum
- Disk: < 200 MB (plus data growth)
- No external database or internet required

---
## Installation (End Users – Executable Distribution)
1. Obtain the installer or portable ZIP release.
2. If installer: Run it and follow prompts.
3. If ZIP: Extract to a writable folder (e.g. `C:\tradia`).
4. Launch `tradia.exe`.
5. First launch shows a temporary Admin password (one‑time) — sign in and you will be forced to set a new secure password.
6. Begin adding Products, then Customers, then create Invoices.

### Portable vs Installed
- Portable: Delete the folder to remove (retain your data in `Documents/tradia/data/wholesale.db` unless you overrode the location).
- Installed: Use Windows “Add or Remove Programs”.

---
## Edition & Licensing
- Current edition: Free & open-source (Apache 2.0). No activation, trial, or product pins.
- All data is local; you may redistribute compiled binaries consistent with the license.
- Legacy documentation references to 14‑day trial / activation pins are deprecated and removed from code.

---
## Backups (Highly Recommended)
| Mode | How |
|------|-----|
| Manual | Settings → Backup Now |
| Automatic | On app exit if > 24h since last backup |

- Default location (if none set): `Documents/tradia/backups`
- Filenames: `backup_YYYYmmdd_HHMMSS.db`
- Retention: Only the most recent N backups (configurable) are kept. Lowering the retention value prunes older backups next time a new backup is created.
- Restore: Close app → (Optional: copy current DB) → Replace it with selected backup → Reopen.
- Keep periodic off‑machine backups (USB / cloud sync) for disaster recovery.

> Backups are plain SQLite database copies (not encrypted). Secure the directory if data is sensitive.

---
## Quick Start Workflow
1. Launch app → Change temporary Admin password.
2. Add initial Products (stock quantity validated).
3. Add Customers.
4. Create an Invoice (line items, discount, tax optional).
5. View / reprint Receipts or export data.
6. Configure backup directory + retention in Settings.
7. Review Activity Log (Admin) for auditing if needed.

---
## Security (User-Facing Summary)
- Passwords stored hashed using PBKDF2-HMAC-SHA256.
  - Hash format: `iterations$salt$hash` (current iterations: 100000). Older hashes are auto‑migrated to the new format on successful login.
- Password policy: minimum 6 characters, must include at least one letter and one digit.
  - During tests/demos you can temporarily relax policy by setting `TRADIA_RELAXED_PASSWORD_POLICY=1` before launching.
- Login hardening: repeated failures are throttled and temporarily locked.
  - After 5 failed attempts for a username, further attempts are soft‑locked for ~30 seconds. The UI shows a "Temporarily Locked" message with the remaining wait time.
  - All failed attempts are recorded in the Activity Log with action `LOGIN_FAIL` (includes running counter). Successful legacy hash upgrades log as `PASS_HASH_UPGRADE`.
- Forced first login password change for the seeded Admin account.
- Backups & DB are unencrypted; apply OS / physical security as appropriate.

---
## Updating the Application
1. Make a Manual Backup first.
2. Replace old executable/folder or run new installer.
3. Existing database auto-migrates if schema changes occur (see Migrations).

### Database File Location
- Default main data file: `Documents/tradia/data/wholesale.db` (auto-created).  
  Override with env `WMS_DB_NAME` (full path) or set `TRADIA_DATA_DIR` to move the folder.
- Backups: user-configured directory.

---
## Uninstalling
- Backup data if needed.
- Remove installation folder or uninstall via Control Panel.
- Optionally archive/delete backup directory.

---
## Troubleshooting (End Users)
| Issue | Resolution |
|-------|------------|
| App does not start | Re-download, ensure antivirus did not quarantine, run as standard user. |
| Cannot save backup | Pick a writable directory in Settings (avoid Program Files). |
| Login role mismatch | Select the correct role (Admin/Manager/etc.) before authenticating. |
| Missing recent data | Restore from latest backup (close app first). |
| "Temporarily Locked" on login | Wait up to 30 seconds and try again, or contact an Admin to reset your password. |

Support: Email or call the contacts in Author section.

---
## Privacy
- All data local. No telemetry or external network calls.

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
- Squashed baseline migration (schema version 1) creates all current tables including: products, customers, invoices, invoice_items, users, settings, activity_log, schema_version.
- License / activation tables were intentionally removed in this free edition.
- Add future forward-only migrations by: (1) creating a new `_migration_N`, (2) bumping `CURRENT_SCHEMA_VERSION`, (3) implementing idempotent changes.

### Packaging (PyInstaller)
Recommended: use the provided spec for reproducible builds.
```
pyinstaller tradia.spec
```
This bundles the assets folder and handles common hidden imports.

### Environment Variables
- WMS_DB_NAME – override DB path (testing / multi-instance)
- TRADIA_DATA_DIR – change the default data directory (where wholesale.db lives)
- SKIP_GUI_TESTS=1 – skip GUI test execution in CI/headless environments
- TRADIA_RELAXED_PASSWORD_POLICY=1 – relax password policy and throttling in test/demo environments

---
## Changelog (Summary)
- 1.0.0: Initial public free release (baseline schema v1, activity log added, removed legacy trial/licensing code, consolidated settings, backup retention, forced admin password change). Updated default DB path to user Documents and added PyInstaller spec.

## Roadmap (Selected)
- Permission matrix refinements (granular per-action control)
- Optional encrypted backups
- Rich analytics / dashboards
- Internationalization & accessibility
- Optional modular plugin or (future) hosted API backend for multi-user concurrent access

> The previous multi-phase web/SaaS migration plan is deferred; focus is on stabilizing core desktop features first.

## License
Apache License 2.0 (see LICENSE file).

## Disclaimer
Provided “as‑is” without warranty. Assess legal/regulatory suitability before production use.

## Acknowledgements
- PyQt6, SQLite, pandas, reportlab, fpdf, matplotlib contributors.

---
© 2025 Ebenezer Fuachie
