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
    # Primary: packaged assets directory (root/assets or PyInstaller bundle)
    p = _ASSETS_DIR / name
    if p.exists():
        return str(p)
    # Fallback: current working directory's assets (portable zip scenarios)
    alt = Path.cwd() / "assets" / name
    if alt.exists():
        return str(alt)
    # Last resort: return the primary path even if missing (caller may handle)
    return str(p)


def base_dir() -> Path:  # pragma: no cover - trivial
    return _BASE_DIR
