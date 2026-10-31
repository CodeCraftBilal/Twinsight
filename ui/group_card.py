from __future__ import annotations

from typing import Callable

import customtkinter as ctk

from core.models import DuplicateGroup, ImageRecord

from . import theme
from .image_tile import ImageTile
from .state import SelectionModel
from .thumbnails import ThumbnailLoader


class GroupCard(ctk.CTkFrame):
    """A titled card holding a horizontally-wrapping row of ImageTiles."""

    COLS = 5

    def __init__(self, parent, index: int, group: DuplicateGroup,
                 selection: SelectionModel, loader: ThumbnailLoader,
                 on_preview: Callable[[ImageRecord], None]) -> None:
        super().__init__(parent, fg_color=theme.SURFACE, corner_radius=theme.RADIUS,
                         border_width=1, border_color=theme.BORDER)
        head = ctk.CTkFrame(self, fg_color="transparent")
        head.pack(fill="x", padx=16, pady=(14, 8))
        ctk.CTkLabel(head, text=f"Group {index}", font=theme.font(15, "bold")).pack(side="left")
        ctk.CTkLabel(head, text=f"{len(group)} similar images", font=theme.font(12),
                     text_color=theme.MUTED).pack(side="left", padx=10)

        grid = ctk.CTkFrame(self, fg_color="transparent")
        grid.pack(fill="x", padx=10, pady=(0, 10))
        best = group.best()
        self.tiles: list[ImageTile] = []
        for i, rec in enumerate(group.images):
            tile = ImageTile(grid, rec, rec is best, selection, loader, on_preview)
            tile.grid(row=i // self.COLS, column=i % self.COLS, padx=6, pady=6, sticky="n")
            self.tiles.append(tile)

    def sync(self) -> None:
        for t in self.tiles:
            t.sync()
