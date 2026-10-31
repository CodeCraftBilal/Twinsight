"""Group images whose hashes are within a Hamming-distance threshold.

Uses the pigeonhole principle: if two 256-bit hashes differ in <= t bits and we
split them into t+1 chunks, at least one chunk is identical. We therefore only
compare images that share a chunk, avoiding the full O(n^2) comparison.
"""
from __future__ import annotations

from collections import defaultdict

from .hashing import HASH_BITS, hamming
from .models import DuplicateGroup, ImageRecord


class _UnionFind:
    def __init__(self, n: int) -> None:
        self.parent = list(range(n))

    def find(self, x: int) -> int:
        while self.parent[x] != x:
            self.parent[x] = self.parent[self.parent[x]]
            x = self.parent[x]
        return x

    def union(self, a: int, b: int) -> None:
        ra, rb = self.find(a), self.find(b)
        if ra != rb:
            self.parent[rb] = ra


def group_similar(records: list[ImageRecord], threshold: int) -> list[DuplicateGroup]:
    """Return groups (size >= 2) of similar images, biggest groups first."""
    n = len(records)
    if n < 2:
        return []

    chunks = threshold + 1
    bounds = [round(i * HASH_BITS / chunks) for i in range(chunks + 1)]
    uf = _UnionFind(n)

    for c in range(chunks):
        lo, hi = bounds[c], bounds[c + 1]
        mask = (1 << (hi - lo)) - 1
        buckets: dict[int, list[int]] = defaultdict(list)
        for idx, rec in enumerate(records):
            buckets[(rec.phash >> lo) & mask].append(idx)
        for members in buckets.values():
            for i in range(len(members)):
                a = members[i]
                for j in range(i + 1, len(members)):
                    b = members[j]
                    if uf.find(a) != uf.find(b) and \
                            hamming(records[a].phash, records[b].phash) <= threshold:
                        uf.union(a, b)

    clusters: dict[int, list[ImageRecord]] = defaultdict(list)
    for idx, rec in enumerate(records):
        clusters[uf.find(idx)].append(rec)

    groups = [DuplicateGroup(sorted(v, key=lambda r: (-r.pixels, -r.size_bytes)))
              for v in clusters.values() if len(v) > 1]
    groups.sort(key=len, reverse=True)
    return groups
