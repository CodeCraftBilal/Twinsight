"""Folder walking and parallel hashing with progress + cancellation."""
from __future__ import annotations

import os
import threading
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
from typing import Callable, Iterator

from .hashing import compute_record
from .models import ImageRecord

IMAGE_EXTENSIONS = {
    ".jpg", ".jpeg", ".png", ".bmp", ".gif", ".webp", ".tif", ".tiff",
}

ProgressCb = Callable[[int, int], None]


def find_images(folder: Path, recursive: bool = True) -> Iterator[Path]:
    if recursive:
        for root, _dirs, files in os.walk(folder):
            for f in files:
                if Path(f).suffix.lower() in IMAGE_EXTENSIONS:
                    yield Path(root) / f
    else:
        for p in folder.iterdir():
            if p.is_file() and p.suffix.lower() in IMAGE_EXTENSIONS:
                yield p


def scan_folder(
    folder: Path,
    recursive: bool,
    progress: ProgressCb | None = None,
    cancel: threading.Event | None = None,
) -> tuple[list[ImageRecord], list[Path]]:
    """Hash every image in *folder*. Returns (records, unreadable_paths)."""
    paths = list(find_images(folder, recursive))
    total = len(paths)
    records: list[ImageRecord] = []
    failed: list[Path] = []
    done = 0
    workers = min(8, (os.cpu_count() or 2))

    with ThreadPoolExecutor(max_workers=workers) as pool:
        futures = {pool.submit(compute_record, p): p for p in paths}
        for fut in as_completed(futures):
            if cancel and cancel.is_set():
                for f in futures:
                    f.cancel()
                break
            try:
                records.append(fut.result())
            except Exception:
                failed.append(futures[fut])
            done += 1
            if progress:
                progress(done, total)
    return records, failed
