"""Background thumbnail loading so the UI never blocks."""
from __future__ import annotations

import queue
from collections import OrderedDict
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from typing import Callable

from PIL import Image, ImageOps


def load_pil(path: Path, box: tuple[int, int]) -> Image.Image:
    with Image.open(path) as img:
        img.draft("RGB", box)          # JPEG: decode at reduced size (much faster); no-op otherwise
        img = ImageOps.exif_transpose(img)
        img.thumbnail(box, Image.Resampling.LANCZOS)
        return img.convert("RGBA")


class ThumbnailLoader:
    """Loads PIL thumbnails in worker threads; results are delivered on the
    Tk thread by calling :meth:`poll` periodically (Tk is not thread-safe)."""

    def __init__(self, box: tuple[int, int], cache_size: int = 600) -> None:
        self.box = box
        self._pool = ThreadPoolExecutor(max_workers=4)
        self._results: queue.Queue = queue.Queue()
        self._cache: OrderedDict[Path, Image.Image] = OrderedDict()
        self._cache_size = cache_size

    def request(self, path: Path, callback: Callable[[Image.Image | None], None],
                cancelled: Callable[[], bool] | None = None) -> None:
        """*cancelled* lets a request be skipped if its widget scrolled away meanwhile."""
        if path in self._cache:
            self._cache.move_to_end(path)
            callback(self._cache[path])
            return

        def work() -> None:
            if cancelled and cancelled():
                return
            try:
                img = load_pil(path, self.box)
            except Exception:
                img = None
            self._results.put((path, img, callback))

        self._pool.submit(work)

    def poll(self, max_items: int = 12) -> None:
        for _ in range(max_items):
            try:
                path, img, cb = self._results.get_nowait()
            except queue.Empty:
                return
            if img is not None:
                self._cache[path] = img
                while len(self._cache) > self._cache_size:
                    self._cache.popitem(last=False)
            try:
                cb(img)
            except Exception:
                pass  # widget was destroyed meanwhile

    def shutdown(self) -> None:
        self._pool.shutdown(wait=False, cancel_futures=True)
