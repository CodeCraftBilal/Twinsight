"""Group images whose hashes are within a Hamming-distance threshold.

Uses the pigeonhole principle: if two 256-bit hashes differ in <= t bits and we
split them into t+1 chunks, at least one chunk is identical. We therefore only
compare images that share a chunk, avoiding the full O(n^2) comparison.

:class:`IncrementalGrouper` accepts images one at a time, so results can be
shown *while* a scan is still running.
"""
from __future__ import annotations

from collections import defaultdict

from .hashing import HASH_BITS, hamming
from .models import DuplicateGroup, ImageRecord


class IncrementalGrouper:
    def __init__(self, threshold: int) -> None:
        self.threshold = threshold
        chunks = threshold + 1
        bounds = [round(i * HASH_BITS / chunks) for i in range(chunks + 1)]
        self._slices = [(bounds[i], (1 << (bounds[i + 1] - bounds[i])) - 1) for i in range(chunks)]
        self._buckets: list[dict[int, list[int]]] = [defaultdict(list) for _ in range(chunks)]
        self._records: list[ImageRecord] = []
        self._parent: list[int] = []
        self._members: dict[int, list[int]] = {}   # root -> member indices
        self._group_count = 0
        self.dirty = False                          # changed since last snapshot()

    # -- union-find -------------------------------------------------------
    def _find(self, x: int) -> int:
        p = self._parent
        while p[x] != x:
            p[x] = p[p[x]]
            x = p[x]
        return x

    def _union(self, a: int, b: int) -> None:
        ra, rb = self._find(a), self._find(b)
        if ra == rb:
            return
        if len(self._members[ra]) < len(self._members[rb]):
            ra, rb = rb, ra
        sa, sb = len(self._members[ra]), len(self._members[rb])
        if sa == 1 and sb == 1:
            self._group_count += 1       # two singletons become a new group
        elif sa > 1 and sb > 1:
            self._group_count -= 1       # two groups merge into one
        self._parent[rb] = ra
        self._members[ra].extend(self._members.pop(rb))
        self.dirty = True

    # -- public API -------------------------------------------------------
    def add(self, rec: ImageRecord) -> None:
        idx = len(self._records)
        self._records.append(rec)
        self._parent.append(idx)
        self._members[idx] = [idx]
        for (lo, mask), buckets in zip(self._slices, self._buckets):
            bucket = buckets[(rec.phash >> lo) & mask]
            for other in bucket:
                if self._find(other) != self._find(idx) and \
                        hamming(self._records[other].phash, rec.phash) <= self.threshold:
                    self._union(other, idx)
            bucket.append(idx)

    @property
    def total(self) -> int:
        return len(self._records)

    @property
    def group_count(self) -> int:
        return self._group_count

    def snapshot(self, sort_by_size: bool = False) -> list[DuplicateGroup]:
        """Current groups (size >= 2). Live order = discovery order (stable)."""
        self.dirty = False
        groups = []
        for members in self._members.values():
            if len(members) < 2:
                continue
            imgs = sorted((self._records[i] for i in members),
                          key=lambda r: (-r.pixels, -r.size_bytes))
            groups.append(DuplicateGroup(imgs, gid=min(members)))
        if sort_by_size:
            groups.sort(key=lambda g: (-len(g), g.gid))
        else:
            groups.sort(key=lambda g: g.gid)
        return groups


def group_similar(records: list[ImageRecord], threshold: int) -> list[DuplicateGroup]:
    """Batch helper: groups (size >= 2), biggest groups first."""
    g = IncrementalGrouper(threshold)
    for r in records:
        g.add(r)
    return g.snapshot(sort_by_size=True)
