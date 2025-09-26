import os
import tempfile

from database.db_handler import get_schema_version, initialize_database
from utils import backup as backup_mod
from utils.backup import (
    get_last_backup_time,
    list_backups,
    perform_backup,
    resolve_backup_dir,
    update_backup_directory,
    update_retention_count,
)


def test_schema_version_upgraded(db):  # db fixture auto use sets up isolated DB
    initialize_database()
    # Squashed baseline migration now sets version to 1 (previous tests expected >=3 before squashing)
    assert get_schema_version() >= 1


def test_backup_creation_and_retention(db):
    # Force retention to small number
    update_retention_count(3)
    # Create 4 backups
    created = [perform_backup() for _ in range(4)]
    backups = list_backups()
    assert len(backups) == 3  # only the last 3 kept
    # Last created backup must be present
    assert any(created[-1] == b for b in backups)


def test_backup_directory_override(db):
    with tempfile.TemporaryDirectory() as tempdir:
        update_backup_directory(tempdir)
        path = perform_backup()
        assert os.path.commonpath([tempdir]) == os.path.commonpath([tempdir, os.path.dirname(path)])


def test_last_backup_time_updates(db):
    # Ensure no backups initially
    # (Fresh DB, default directory may contain old backups if a path reused; use temp dir override)
    with tempfile.TemporaryDirectory() as tempdir:
        update_backup_directory(tempdir)
        assert get_last_backup_time(tempdir) is None
        perform_backup()
        assert get_last_backup_time(tempdir) is not None


def test_needs_backup_logic(db):
    with tempfile.TemporaryDirectory() as tempdir:
        update_backup_directory(tempdir)
        # First call -> needs backup
        assert backup_mod.needs_backup(hours=24) is True
        perform_backup()
        # Immediately after, should not need another backup with large hours window
        assert backup_mod.needs_backup(hours=24) is False
        # Force by using hours=0
        assert backup_mod.needs_backup(hours=0) is True


def test_perform_backup_missing_db(monkeypatch, db):
    # Point to a non-existent DB path temporarily
    monkeypatch.setenv("WMS_DB_NAME", "non_existent_file.db")
    # ensure directory resolvable
    resolve_backup_dir()
    try:
        try:
            perform_backup()
        except FileNotFoundError:
            pass
    finally:
        # reset to test db used by fixtures (set again)
        monkeypatch.delenv("WMS_DB_NAME", raising=False)
