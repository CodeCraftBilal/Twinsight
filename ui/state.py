"""Shared selection model (which files are marked for deletion)."""
from __future__ import annotations

from pathlib import Path
from typing import Callable, Mapping


class SelectionModel:
    def __init__(self) -> None:
        self._selected: set[Path] = set()
        self._sizes: dict[Path, int] = {}
        self._total = 0
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

    @property
    def total_bytes(self) -> int:
        """Disk space that deleting the current selection would free (kept incrementally)."""
        return self._total

    def _recount(self) -> None:
        self._total = sum(self._sizes.get(p, 0) for p in self._selected)

    def set_sizes(self, sizes: Mapping[Path, int]) -> None:
        self._sizes = dict(sizes)
        self._recount()

    def set(self, path: Path, on: bool) -> None:
        if on and path not in self._selected:
            self._selected.add(path)
            self._total += self._sizes.get(path, 0)
        elif not on and path in self._selected:
            self._selected.discard(path)
            self._total -= self._sizes.get(path, 0)
        self._notify()

    def add_many(self, paths, discard=()) -> None:
        """Select *paths* and deselect *discard* with a single notification."""
        self._selected.update(paths)
        self._selected.difference_update(discard)
        self._recount()
        self._notify()

    def replace(self, paths) -> None:
        self._selected = set(paths)
        self._recount()
        self._notify()

    def remove_many(self, paths) -> None:
        self._selected -= set(paths)
        self._recount()
        self._notify()
