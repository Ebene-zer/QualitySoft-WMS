from __future__ import annotations

import sys
from pathlib import Path

# Determine application base directory (supports PyInstaller when frozen).
# When frozen, sys._MEIPASS points to the temp unpack directory.
_BASE_DIR = Path(getattr(sys, "_MEIPASS", Path(__file__).resolve().parent.parent))
_ASSETS_DIR = _BASE_DIR / "assets"


def asset_path(name: str) -> str:
    """Return absolute path for an asset by filename.

    Example:
        icon = QIcon(asset_path("tradia.ico"))
    """
    return str(_ASSETS_DIR / name)


def base_dir() -> Path:  # pragma: no cover - trivial
    return _BASE_DIR

