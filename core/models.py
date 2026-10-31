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
    """A set of images that look alike."""

    images: list[ImageRecord] = field(default_factory=list)

    def best(self) -> ImageRecord:
        """The image we suggest keeping: highest resolution, then largest file."""
        return max(self.images, key=lambda r: (r.pixels, r.size_bytes))

    def __len__(self) -> int:
        return len(self.images)
