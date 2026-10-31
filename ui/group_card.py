from __future__ import annotations

import math
from typing import Callable

import customtkinter as ctk

from core.models import DuplicateGroup, ImageRecord

from . import theme
from .helpers import human_size
from .image_tile import TILE_H, TILE_W, ImageTile
from .state import SelectionModel
from .thumbnails import ThumbnailLoader

HEADER_H = 58
PAD = 10
CELL_W = TILE_W + 12
CELL_H = TILE_H + 12


def columns_for(width: int) -> int:
    return max(1, (width - 2 * PAD) // CELL_W)


def height_for(group: DuplicateGroup, width: int) -> int:
    """Exact pixel height of a card; used by the virtual list for layout."""
    rows = math.ceil(len(group.images) / columns_for(width))
    return HEADER_H + rows * CELL_H + PAD


class GroupCard(ctk.CTkFrame):
    """A titled card with a wrapping grid of ImageTiles (placed at fixed coordinates)."""

    def __init__(self, parent, index: int, group: DuplicateGroup, width: int,
                 selection: SelectionModel, loader: ThumbnailLoader,
                 on_preview: Callable[[ImageRecord], None]) -> None:
        super().__init__(parent, fg_color=theme.SURFACE, corner_radius=theme.RADIUS,
                         border_width=1, border_color=theme.BORDER)
        self.group, self.selection = group, selection

        head = ctk.CTkFrame(self, fg_color="transparent", height=HEADER_H)
        head.pack_propagate(False)           # keep the fixed height despite packed children
        head.place(x=0, y=0, relwidth=1)
        self._title = ctk.CTkLabel(head, text=f"Group {index}", font=theme.font(15, "bold"))
        self._title.pack(side="left", padx=(16, 0))
        ctk.CTkLabel(head, text=f"{len(group)} similar · {human_size(group.reclaimable_bytes)} reclaimable",
                     font=theme.font(12), text_color=theme.MUTED).pack(side="left", padx=12)
        ctk.CTkButton(head, text="Clear", width=64, height=30, corner_radius=8,
                      fg_color="transparent", hover_color=theme.SURFACE_ALT,
                      text_color=theme.MUTED, command=self.clear_group).pack(side="right", padx=(0, 14))
        ctk.CTkButton(head, text="Select all but best", width=140, height=30, corner_radius=8,
                      fg_color=theme.SURFACE_ALT, hover_color=theme.BORDER, text_color=theme.TEXT,
                      command=self.select_all_but_best).pack(side="right", padx=4)

        cols = columns_for(width)
        best = group.best()
        self.tiles: list[ImageTile] = []
        for i, rec in enumerate(group.images):
            tile = ImageTile(self, rec, rec is best, selection, loader, on_preview)
            tile.place(x=PAD + (i % cols) * CELL_W + 6, y=HEADER_H + (i // cols) * CELL_H + 6)
            self.tiles.append(tile)

    # -- per-group selection ---------------------------------------------
    def select_all_but_best(self) -> None:
        best = self.group.best()
        self.selection.add_many([r.path for r in self.group.images if r is not best],
                                discard=[best.path])
        self.sync()

    def clear_group(self) -> None:
        self.selection.add_many([], discard=[r.path for r in self.group.images])
        self.sync()

    def set_index(self, index: int) -> None:
        self._title.configure(text=f"Group {index}")

    def sync(self) -> None:
        for t in self.tiles:
            t.sync()
