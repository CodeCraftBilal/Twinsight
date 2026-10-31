"""Shared selection model (which files are marked for deletion)."""
from __future__ import annotations

from pathlib import Path
from typing import Callable


class SelectionModel:
    def __init__(self) -> None:
        self._selected: set[Path] = set()
        self._listeners: list[Callable[[], None]] = []

    def subscribe(self, fn: Callable[[], None]) -> None:
        self._listeners.append(fn)

    def _notify(self) -> None:
        for fn in self._listeners:
            fn()

    def __contains__(self, path: Path) -> bool:
        return path in self._selected

    def __len__(self) -> int:
        return len(self._selected)

    @property
    def paths(self) -> list[Path]:
        return sorted(self._selected)

    def set(self, path: Path, on: bool) -> None:
        (self._selected.add if on else self._selected.discard)(path)
        self._notify()

    def replace(self, paths) -> None:
        self._selected = set(paths)
        self._notify()

    def remove_many(self, paths) -> None:
        self._selected -= set(paths)
        self._notify()
