"""Pure layout maths for the virtual list (no Tk imports, so it is unit-testable)."""
from __future__ import annotations

from bisect import bisect_left, bisect_right


class ListLayout:
    """Vertical stack of variable-height rows with a gap between them."""

    def __init__(self, gap: int = 10, pad: int = 6) -> None:
        self.gap, self.pad = gap, pad
        self._heights: list[int] = []
        self._offsets: list[int] = []
        self.total = pad * 2

    def __len__(self) -> int:
        return len(self._heights)

    def rebuild(self, heights: list[int]) -> None:
        offs, y = [], self.pad
        for h in heights:
            offs.append(y)
            y += h + self.gap
        self._heights, self._offsets = list(heights), offs
        self.total = (y - self.gap + self.pad) if heights else self.pad * 2

    def offset(self, i: int) -> int:
        return self._offsets[i]

    def height(self, i: int) -> int:
        return self._heights[i]

    def clamp(self, top: float, viewport_h: int) -> int:
        return int(min(max(top, 0), max(0, self.total - viewport_h)))

    def visible(self, top: float, viewport_h: int, buffer: float = 0) -> range:
        """Indices of rows intersecting [top - buffer, top + viewport_h + buffer]."""
        if not self._offsets:
            return range(0)
        lo, hi = top - buffer, top + viewport_h + buffer
        first = max(bisect_right(self._offsets, lo) - 1, 0)
        last = bisect_left(self._offsets, hi)
        return range(first, max(last, first))

    def anchor(self, top: float) -> tuple[int, float]:
        """(row index, distance into that row) at scroll position *top*."""
        if not self._offsets:
            return 0, 0.0
        i = max(bisect_right(self._offsets, top) - 1, 0)
        return i, top - self._offsets[i]
