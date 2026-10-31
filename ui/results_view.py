from __future__ import annotations

import customtkinter as ctk

from core.models import DuplicateGroup

from . import theme
from .group_card import GroupCard
from .preview import PreviewWindow
from .state import SelectionModel
from .thumbnails import ThumbnailLoader

PAGE = 15  # groups rendered per "page" to keep the UI responsive


class ResultsView(ctk.CTkScrollableFrame):
    def __init__(self, parent, selection: SelectionModel) -> None:
        super().__init__(parent, fg_color="transparent")
        self.selection = selection
        self.loader = ThumbnailLoader((theme.THUMB, theme.THUMB))
        self._groups: list[DuplicateGroup] = []
        self._cards: list[GroupCard] = []
        self._more_btn: ctk.CTkButton | None = None
        self._placeholder: ctk.CTkLabel | None = None
        self._poll()

    def _poll(self) -> None:
        self.loader.poll()
        self.after(40, self._poll)

    # -- public API -------------------------------------------------------
    def show_message(self, text: str) -> None:
        self.clear()
        self._placeholder = ctk.CTkLabel(self, text=text, font=theme.font(15),
                                         text_color=theme.MUTED, justify="center")
        self._placeholder.pack(pady=120)

    def show_groups(self, groups: list[DuplicateGroup]) -> None:
        self.clear()
        self._groups = groups
        if not groups:
            self.show_message("🎉  No similar images found.\nTry raising the similarity slider.")
            return
        self._render_next()

    def clear(self) -> None:
        for w in self.winfo_children():
            w.destroy()
        self._cards.clear()
        self._groups = []
        self._more_btn = self._placeholder = None

    def sync(self) -> None:
        for c in self._cards:
            c.sync()

    def remove_paths(self, deleted) -> None:
        """Re-render after deletion, dropping groups that are no longer duplicates."""
        gone = set(deleted)
        new_groups = []
        for g in self._groups:
            g.images = [r for r in g.images if r.path not in gone]
            if len(g.images) > 1:
                new_groups.append(g)
        self.show_groups(new_groups)

    @property
    def groups(self) -> list[DuplicateGroup]:
        return self._groups

    # -- internals --------------------------------------------------------
    def _render_next(self) -> None:
        if self._more_btn is not None:
            self._more_btn.destroy()
            self._more_btn = None
        start = len(self._cards)
        for i, g in enumerate(self._groups[start:start + PAGE], start=start + 1):
            card = GroupCard(self, i, g, self.selection, self.loader,
                             lambda rec: PreviewWindow(self.winfo_toplevel(), rec))
            card.pack(fill="x", pady=8, padx=4)
            self._cards.append(card)
        remaining = len(self._groups) - len(self._cards)
        if remaining > 0:
            self._more_btn = ctk.CTkButton(
                self, text=f"Show more groups ({remaining} left)", height=40,
                fg_color=theme.SURFACE, hover_color=theme.SURFACE_ALT, text_color=theme.TEXT,
                border_width=1, border_color=theme.BORDER, corner_radius=10,
                command=self._render_next)
            self._more_btn.pack(pady=12)
