"""Perceptual hashing (difference hash) implemented with Pillow only."""
from __future__ import annotations

from pathlib import Path

from PIL import Image, ImageOps

from .models import ImageRecord

HASH_SIZE = 16                      # 16x16 -> 256-bit hash
HASH_BITS = HASH_SIZE * HASH_SIZE

try:  # Python 3.10+
    int.bit_count

    def hamming(a: int, b: int) -> int:
        return (a ^ b).bit_count()
except AttributeError:  # pragma: no cover
    def hamming(a: int, b: int) -> int:
        return bin(a ^ b).count("1")


def dhash(img: Image.Image) -> int:
    """Difference hash: compares neighbouring pixels of a tiny grayscale copy.

    Robust against resizing, recompression and small colour changes.
    """
    small = img.convert("L").resize((HASH_SIZE + 1, HASH_SIZE), Image.Resampling.LANCZOS)
    px = list(small.getdata())
    w = HASH_SIZE + 1
    value = 0
    for row in range(HASH_SIZE):
        base = row * w
        for col in range(HASH_SIZE):
            value = (value << 1) | (1 if px[base + col] > px[base + col + 1] else 0)
    return value


def compute_record(path: Path) -> ImageRecord:
    """Open an image and build its ImageRecord. Raises on unreadable files."""
    with Image.open(path) as img:
        img = ImageOps.exif_transpose(img)
        width, height = img.size
        h = dhash(img)
    return ImageRecord(path=path, phash=h, width=width, height=height,
                       size_bytes=path.stat().st_size)
