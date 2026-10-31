from __future__ import annotations

import customtkinter as ctk
from PIL import ImageTk  # noqa: F401  (ensures Tk image support is loaded)

from core.models import ImageRecord

from . import theme
from .helpers import human_size
from .thumbnails import load_pil


class PreviewWindow(ctk.CTkToplevel):
    """Large preview of a single image."""

    def __init__(self, parent, record: ImageRecord) -> None:
        super().__init__(parent)
        self.title(record.name)
        self.geometry("900x700")
        self.configure(fg_color=theme.BG)
        self.bind("<Escape>", lambda _e: self.destroy())

        try:
            pil = load_pil(record.path, (860, 580))
            self._img = ctk.CTkImage(pil, size=pil.size)
            ctk.CTkLabel(self, image=self._img, text="").pack(expand=True, padx=20, pady=(20, 8))
        except Exception:
            ctk.CTkLabel(self, text="Cannot display image").pack(expand=True)

        info = (f"{record.name}\n{record.width} × {record.height}px  ·  "
                f"{human_size(record.size_bytes)}\n{record.path.parent}")
        ctk.CTkLabel(self, text=info, text_color=theme.MUTED, font=theme.font(12),
                     justify="center").pack(pady=(0, 20))
        self.after(50, self.focus_set)
