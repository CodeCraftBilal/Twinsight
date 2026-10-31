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
    """Shows duplicate groups. :meth:`set_groups` can be called repeatedly while a
    scan is running: unchanged cards are kept, changed/new ones are (re)built."""

    def __init__(self, parent, selection: SelectionModel) -> None:
        super().__init__(parent, fg_color="transparent")
        self.selection = selection
        self.loader = ThumbnailLoader((theme.THUMB, theme.THUMB))
        self._groups: list[DuplicateGroup] = []
        self._cards: dict[int, tuple[frozenset, GroupCard]] = {}  # gid -> (signature, card)
        self._order: list[GroupCard] = []                          # cards as currently packed
        self._visible = PAGE
        self._more_btn: ctk.CTkButton | None = None
        self._placeholder: ctk.CTkLabel | None = None
        self._poll()

    def _poll(self) -> None:
        self.loader.poll()
        self.after(40, self._poll)

    # -- public API -------------------------------------------------------
    @property
    def groups(self) -> list[DuplicateGroup]:
        return self._groups

    def show_message(self, text: str) -> None:
        self.clear()
        self._ensure_placeholder(text)

    def clear(self) -> None:
        for _sig, card in self._cards.values():
            card.destroy()
        self._cards.clear()
        self._order.clear()
        self._groups = []
        self._visible = PAGE
        if self._more_btn is not None:
            self._more_btn.destroy()
            self._more_btn = None
        if self._placeholder is not None:
            self._placeholder.destroy()
            self._placeholder = None

    def set_groups(self, groups: list[DuplicateGroup], final: bool = False) -> None:
        self._groups = groups
        if not groups:
            self._drop_cards()
            self._ensure_placeholder(
                "🎉  No similar images found.\nTry raising the similarity slider." if final
                else "Scanning…\nDuplicates will appear here as soon as they are found.")
            return
        if self._placeholder is not None:
            self._placeholder.destroy()
            self._placeholder = None

        shown = groups[:self._visible]
        keep = {g.gid for g in shown}
        for gid in [k for k in self._cards if k not in keep]:
            self._cards.pop(gid)[1].destroy()

        new_order: list[GroupCard] = []
        for idx, g in enumerate(shown, start=1):
            entry = self._cards.get(g.gid)
            if entry and entry[0] == g.signature:
                card = entry[1]
            else:
                if entry:
                    entry[1].destroy()
                card = GroupCard(self, idx, g, self.selection, self.loader,
                                 lambda rec: PreviewWindow(self.winfo_toplevel(), rec))
                self._cards[g.gid] = (g.signature, card)
            new_order.append(card)
        for idx, card in enumerate(new_order, start=1):
            card.set_index(idx)          # numbering can change when the order changes
        self._repack(new_order)
        self._update_more_button()

    def sync(self) -> None:
        for _sig, card in self._cards.values():
            card.sync()

    def remove_paths(self, deleted) -> None:
        """Drop deleted files; groups that are no longer duplicates disappear."""
        gone = set(deleted)
        groups = []
        for g in self._groups:
            imgs = [r for r in g.images if r.path not in gone]
            if len(imgs) > 1:
                groups.append(DuplicateGroup(imgs, gid=g.gid))
        self.set_groups(groups, final=True)

    # -- internals --------------------------------------------------------
    def _ensure_placeholder(self, text: str) -> None:
        if self._placeholder is None:
            self._placeholder = ctk.CTkLabel(self, text=text, font=theme.font(15),
                                             text_color=theme.MUTED, justify="center")
            self._placeholder.pack(pady=120)
        else:
            self._placeholder.configure(text=text)

    def _drop_cards(self) -> None:
        for _sig, card in self._cards.values():
            card.destroy()
        self._cards.clear()
        self._order.clear()
        if self._more_btn is not None:
            self._more_btn.destroy()
            self._more_btn = None

    def _repack(self, new_order: list[GroupCard]) -> None:
        """Re-pack only from the first position that changed (avoids flicker)."""
        old = self._order
        first = 0
        while first < len(old) and first < len(new_order) and old[first] is new_order[first]:
            first += 1
        if self._more_btn is not None:
            self._more_btn.pack_forget()
        for card in old[first:]:
            if card.winfo_exists():
                card.pack_forget()
        for card in new_order[first:]:
            card.pack(fill="x", pady=8, padx=4)
        self._order = new_order

    def _update_more_button(self) -> None:
        remaining = len(self._groups) - len(self._order)
        if remaining <= 0:
            if self._more_btn is not None:
                self._more_btn.destroy()
                self._more_btn = None
            return
        text = f"Show more groups ({remaining} left)"
        if self._more_btn is None:
            self._more_btn = ctk.CTkButton(
                self, height=40, fg_color=theme.SURFACE, hover_color=theme.SURFACE_ALT,
                text_color=theme.TEXT, border_width=1, border_color=theme.BORDER,
                corner_radius=10, command=self._show_more)
        self._more_btn.configure(text=text)
        self._more_btn.pack(pady=12)

    def _show_more(self) -> None:
        self._visible += PAGE
        self.set_groups(self._groups, final=True)
