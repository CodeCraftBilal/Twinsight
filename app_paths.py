"""Resolve bundled resource paths both in dev and inside a PyInstaller build."""
import sys
from pathlib import Path


def resource_path(relative: str) -> Path:
    base = Path(getattr(sys, "_MEIPASS", Path(__file__).resolve().parent))
    return base / relative
