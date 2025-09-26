from __future__ import annotations

import logging
import os
import sys
from logging.handlers import RotatingFileHandler
from pathlib import Path

from .resource_paths import base_dir

DEFAULT_MAX_BYTES = 512 * 1024  # 512 KB per file
DEFAULT_BACKUP_COUNT = 5

# Module-level idempotence flags (avoid function attribute hacks)
_LOGGING_CONFIGURED = False
_EXCEPT_HOOK_INSTALLED = False


def _resolve_log_dir() -> Path:
    """Return a persistent log directory.

    Priority:
      1. TRADIA_LOG_DIR environment variable (created if missing)
      2. User Documents/tradia/logs
      3. Application base directory /logs (last resort)
    """
    # 1. Env override
    env_dir = os.getenv("TRADIA_LOG_DIR")
    if env_dir:
        p = Path(env_dir).expanduser().resolve()
        p.mkdir(parents=True, exist_ok=True)
        return p
    # 2. User Documents
    docs = Path.home() / "Documents" / "tradia" / "logs"
    try:
        docs.mkdir(parents=True, exist_ok=True)
        return docs
    except Exception:
        pass
    # 3. Base dir fallback (may be read‑only in some deployments)
    fallback = base_dir() / "logs"
    try:
        fallback.mkdir(parents=True, exist_ok=True)
    except Exception:
        # swallow – will attempt to log to stderr only
        pass
    return fallback


def configure_logging(level: int = logging.INFO):
    """Configure application logging with rotating file handler + console.

    Safe to call multiple times; subsequent calls are ignored if already configured.
    """
    global _LOGGING_CONFIGURED
    if _LOGGING_CONFIGURED:  # idempotent
        return
    log_dir = _resolve_log_dir()
    log_path = log_dir / "tradia.log"

    handlers: list[logging.Handler] = []

    # Rotating file handler
    try:
        file_handler = RotatingFileHandler(
            log_path, maxBytes=DEFAULT_MAX_BYTES, backupCount=DEFAULT_BACKUP_COUNT, encoding="utf-8"
        )
        file_handler.setFormatter(
            logging.Formatter("%(asctime)s [%(levelname)s] %(name)s: %(message)s")
        )
        handlers.append(file_handler)
    except Exception as e:
        # Fall back silently; still keep console logging
        sys.stderr.write(f"[WARN] Could not create log file handler: {e}\n")

    # Console / stderr handler
    console = logging.StreamHandler()
    console.setFormatter(logging.Formatter("%(asctime)s [%(levelname)s] %(name)s: %(message)s"))
    handlers.append(console)

    logging.basicConfig(level=level, handlers=handlers)
    logging.getLogger("sqlite3").setLevel(logging.WARNING)
    logging.getLogger("PyQt6").setLevel(logging.WARNING)

    logging.getLogger(__name__).info("Logging initialized (file: %s)", log_path)
    _LOGGING_CONFIGURED = True


def install_global_excepthook():
    """Install a global exception hook to log uncaught exceptions and show a user dialog.

    The GUI message box import is done lazily to avoid circular import issues before QApplication exists.
    """
    global _EXCEPT_HOOK_INSTALLED
    if _EXCEPT_HOOK_INSTALLED:
        return
    logger = logging.getLogger("global.excepthook")

    def _hook(exc_type, exc_value, exc_tb):  # pragma: no cover - interactive / crash path
        logger.exception("Uncaught exception", exc_info=(exc_type, exc_value, exc_tb))
        try:
            from PyQt6.QtWidgets import QApplication, QMessageBox

            app = QApplication.instance()
            if app is not None:
                QMessageBox.critical(
                    None,
                    "Unexpected Error",
                    ("An unexpected error occurred and was logged. "
                     "You may continue, but consider restarting.\n\n" f"{exc_type.__name__}: {exc_value}"),
                )
        except Exception:
            pass
        # Delegate to default (prints to stderr)
        sys.__excepthook__(exc_type, exc_value, exc_tb)

    sys.excepthook = _hook
    _EXCEPT_HOOK_INSTALLED = True
