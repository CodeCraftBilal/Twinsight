from __future__ import annotations

from typing import Callable

import customtkinter as ctk

from core.models import ImageRecord

from . import theme
from .helpers import human_size
from .state import SelectionModel
from .thumbnails import ThumbnailLoader

TILE_W = theme.THUMB + 20
TILE_H = 250


class ImageTile(ctk.CTkFrame):
    """One image: thumbnail, checkbox, metadata. Fixed size (TILE_W x TILE_H)."""

    def __init__(self, parent, record: ImageRecord, is_best: bool,
                 selection: SelectionModel, loader: ThumbnailLoader,
                 on_preview: Callable[[ImageRecord], None]) -> None:
        super().__init__(parent, width=TILE_W, height=TILE_H, fg_color=theme.SURFACE_ALT,
                         corner_radius=12, border_width=2, border_color=theme.SURFACE_ALT)
        self.pack_propagate(False)           # keep fixed TILE_W x TILE_H size
        self._dead = False
        self.record = record
        self.selection = selection
        self._var = ctk.BooleanVar(value=record.path in selection)

        box = theme.THUMB
        self._thumb = ctk.CTkLabel(self, text="…", width=box, height=box,
                                   text_color=theme.MUTED, cursor="hand2")
        self._thumb.pack(padx=10, pady=(10, 6))
        self._thumb.bind("<Button-1>", lambda _e: on_preview(record))

        top = ctk.CTkFrame(self, fg_color="transparent")
        top.pack(fill="x", padx=10)
        self._check = ctk.CTkCheckBox(
            top, text="Delete", variable=self._var, command=self._toggled,
            width=20, checkbox_width=20, checkbox_height=20, corner_radius=6,
            fg_color=theme.DANGER, hover_color=theme.DANGER_HOVER, font=theme.font(12))
        self._check.pack(side="left")
        if is_best:
            ctk.CTkLabel(top, text="BEST", font=theme.font(10, "bold"), text_color="white",
                         fg_color=theme.SUCCESS, corner_radius=6, width=38, height=18
                         ).pack(side="right")

        name = record.name if len(record.name) <= 20 else record.name[:17] + "…"
        ctk.CTkLabel(self, text=name, font=theme.font(12, "bold"), anchor="w"
                     ).pack(fill="x", padx=12, pady=(6, 0))
        ctk.CTkLabel(self, text=f"{record.width}×{record.height} · {human_size(record.size_bytes)}",
                     font=theme.font(11), text_color=theme.MUTED, anchor="w"
                     ).pack(fill="x", padx=12, pady=(0, 10))
        self._restyle()
        loader.request(record.path, self._set_image, lambda: self._dead)

    def destroy(self) -> None:
        self._dead = True
        super().destroy()

    def _set_image(self, pil) -> None:
        if self._dead:
            return
        if pil is None:
            self._thumb.configure(text="unreadable")
            return
        self._ctk_img = ctk.CTkImage(pil, size=pil.size)
        self._thumb.configure(image=self._ctk_img, text="")

    def _toggled(self) -> None:
        self.selection.set(self.record.path, self._var.get())
        self._restyle()

    def sync(self) -> None:
        self._var.set(self.record.path in self.selection)
        self._restyle()

    def _restyle(self) -> None:
        on = self._var.get()
        self.configure(border_color=theme.DANGER if on else theme.SURFACE_ALT,
                       fg_color=theme.SELECTED if on else theme.SURFACE_ALT)
