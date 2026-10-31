from __future__ import annotations

from tkinter import filedialog
from typing import Callable

import customtkinter as ctk

from . import theme


class Sidebar(ctk.CTkFrame):
    def __init__(self, parent, on_scan: Callable[[], None], on_cancel: Callable[[], None]) -> None:
        super().__init__(parent, width=300, fg_color=theme.SURFACE, corner_radius=0)
        self.pack_propagate(False)
        self._on_scan, self._on_cancel = on_scan, on_cancel
        self.folder = ctk.StringVar(value="")

        ctk.CTkLabel(self, text="◩  Twinsight", font=theme.font(22, "bold"),
                     text_color=theme.ACCENT).pack(anchor="w", padx=24, pady=(28, 0))
        ctk.CTkLabel(self, text="Find & clean duplicate photos", font=theme.font(12),
                     text_color=theme.MUTED).pack(anchor="w", padx=24, pady=(0, 24))

        self._section("FOLDER")
        self.path_label = ctk.CTkLabel(self, text="No folder selected", font=theme.font(12),
                                       text_color=theme.MUTED, anchor="w", wraplength=250,
                                       justify="left")
        self.path_label.pack(fill="x", padx=24, pady=(0, 8))
        ctk.CTkButton(self, text="Choose folder…", height=38, corner_radius=10,
                      fg_color=theme.SURFACE_ALT, hover_color=theme.BORDER,
                      text_color=theme.TEXT, command=self._browse).pack(fill="x", padx=24)
        self.recursive = ctk.CTkSwitch(self, text="Include sub-folders", progress_color=theme.ACCENT,
                                       font=theme.font(12))
        self.recursive.select()
        self.recursive.pack(anchor="w", padx=24, pady=16)

        self._section("SIMILARITY")
        self.level_label = ctk.CTkLabel(self, text="", font=theme.font(12), text_color=theme.TEXT)
        self.level_label.pack(anchor="w", padx=24)
        self.slider = ctk.CTkSlider(self, from_=0, to=40, number_of_steps=40,
                                    progress_color=theme.ACCENT, button_color=theme.ACCENT,
                                    button_hover_color=theme.ACCENT_HOVER,
                                    command=self._slider_changed)
        self.slider.set(10)
        self.slider.pack(fill="x", padx=24, pady=(6, 0))
        ctk.CTkLabel(self, text="Strict  ←——→  Loose", font=theme.font(10),
                     text_color=theme.MUTED).pack(pady=(2, 0))
        self._slider_changed(10)

        self.scan_btn = ctk.CTkButton(self, text="Scan for duplicates", height=44, corner_radius=12,
                                      font=theme.font(14, "bold"), fg_color=theme.ACCENT,
                                      hover_color=theme.ACCENT_HOVER, command=self._on_scan)
        self.scan_btn.pack(fill="x", padx=24, pady=(28, 8))
        self.cancel_btn = ctk.CTkButton(self, text="Cancel", height=32, corner_radius=10,
                                        fg_color="transparent", text_color=theme.MUTED,
                                        hover_color=theme.SURFACE_ALT, command=self._on_cancel)

        self.progress = ctk.CTkProgressBar(self, progress_color=theme.ACCENT, height=8)
        self.progress.set(0)
        self.status = ctk.CTkLabel(self, text="Ready", font=theme.font(12),
                                   text_color=theme.MUTED, wraplength=250, justify="left")
        self.status.pack(side="bottom", anchor="w", padx=24, pady=20)

    def _section(self, title: str) -> None:
        ctk.CTkLabel(self, text=title, font=theme.font(10, "bold"),
                     text_color=theme.MUTED).pack(anchor="w", padx=24, pady=(0, 6))

    def _browse(self) -> None:
        path = filedialog.askdirectory(title="Select a folder of images")
        if path:
            self.folder.set(path)
            self.path_label.configure(text=path, text_color=theme.TEXT)

    def _slider_changed(self, value: float) -> None:
        v = int(round(value))
        desc = "Exact copies only" if v == 0 else "Near-identical" if v <= 6 else \
            "Similar (recommended)" if v <= 14 else "Loosely similar"
        self.level_label.configure(text=f"Threshold {v}  ·  {desc}")

    # -- API --------------------------------------------------------------
    @property
    def threshold(self) -> int:
        return int(round(self.slider.get()))

    def set_scanning(self, scanning: bool) -> None:
        if scanning:
            self.scan_btn.configure(state="disabled", text="Scanning…")
            self.cancel_btn.pack(fill="x", padx=24)
            self.progress.pack(fill="x", padx=24, pady=(8, 0))
        else:
            self.scan_btn.configure(state="normal", text="Scan for duplicates")
            self.cancel_btn.pack_forget()
            self.progress.pack_forget()

    def set_progress(self, fraction: float, text: str) -> None:
        self.progress.set(fraction)
        self.status.configure(text=text)

    def set_status(self, text: str) -> None:
        self.status.configure(text=text)
