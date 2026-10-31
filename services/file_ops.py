from __future__ import annotations

import os
from dataclasses import dataclass, field
from pathlib import Path

try:
    from send2trash import send2trash
except ImportError:  # optional dependency
    send2trash = None


@dataclass
class DeleteResult:
    deleted: list[Path] = field(default_factory=list)
    errors: list[tuple[Path, str]] = field(default_factory=list)
    freed_bytes: int = 0


def trash_available() -> bool:
    return send2trash is not None


def delete_files(paths: list[Path], to_trash: bool = True) -> DeleteResult:
    """Delete files, preferring the recycle bin when available."""
    result = DeleteResult()
    for p in paths:
        try:
            size = p.stat().st_size
            if to_trash and send2trash is not None:
                send2trash(str(p))
            else:
                os.remove(p)
            result.deleted.append(p)
            result.freed_bytes += size
        except Exception as exc:
            result.errors.append((p, str(exc)))
    return result
