from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path


@dataclass(frozen=True)
class ImageRecord:
    """Metadata + perceptual hash of one image file."""

    path: Path
    phash: int
    width: int
    height: int
    size_bytes: int

    @property
    def pixels(self) -> int:
        return self.width * self.height

    @property
    def name(self) -> str:
        return self.path.name


@dataclass
class DuplicateGroup:
    """A set of images that look alike. ``gid`` is stable while a scan grows the group."""

    images: list[ImageRecord] = field(default_factory=list)
    gid: int = 0

    def best(self) -> ImageRecord:
        """The image we suggest keeping: highest resolution, then largest file."""
        return max(self.images, key=lambda r: (r.pixels, r.size_bytes))

    @property
    def reclaimable_bytes(self) -> int:
        """Space freed if everything except the best image is deleted."""
        return sum(r.size_bytes for r in self.images) - self.best().size_bytes

    @property
    def signature(self) -> frozenset:
        """Identity of the current membership (used to detect changes)."""
        return frozenset(r.path for r in self.images)

    def __len__(self) -> int:
        return len(self.images)
