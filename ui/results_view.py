from __future__ import annotations

import customtkinter as ctk

from core.models import DuplicateGroup

from . import theme
from .group_card import GroupCard, height_for
from .preview import PreviewWindow
from .state import SelectionModel
from .thumbnails import ThumbnailLoader
from .virtual_list import VirtualList


class ResultsView(ctk.CTkFrame):
    """Duplicate groups in a virtualised list. :meth:`set_groups` may be called
    repeatedly while a scan runs; only rows near the viewport are real widgets."""

    def __init__(self, parent, selection: SelectionModel) -> None:
        super().__init__(parent, fg_color="transparent")
        self.selection = selection
        self.loader = ThumbnailLoader((theme.THUMB, theme.THUMB))
        self._groups: list[DuplicateGroup] = []
        self._list = VirtualList(
            self, factory=self._make_card, height_of=height_for,
            key_of=lambda g: g.gid, sig_of=lambda g: g.signature,
            renumber=lambda card, i: card.set_index(i + 1))
        self._list.pack(fill="both", expand=True)
        self._placeholder = ctk.CTkLabel(self, text="", font=theme.font(15),
                                         text_color=theme.MUTED, justify="center")
        self._poll()

    def _make_card(self, parent, group: DuplicateGroup, index: int, width: int) -> GroupCard:
        return GroupCard(parent, index + 1, group, width, self.selection, self.loader,
                         lambda rec: PreviewWindow(self.winfo_toplevel(), rec))

    def _poll(self) -> None:
        self.loader.poll()
        self.after(40, self._poll)

    # -- public API -------------------------------------------------------
    @property
    def groups(self) -> list[DuplicateGroup]:
        return self._groups

    def show_message(self, text: str) -> None:
        self._groups = []
        self._list.set_items([])
        self._show_placeholder(text)

    def clear(self) -> None:
        self.show_message("")

    def set_groups(self, groups: list[DuplicateGroup], final: bool = False) -> None:
        self._groups = groups
        self._list.set_items(groups)
        if groups:
            self._placeholder.place_forget()
        else:
            self._show_placeholder(
                "🎉  No similar images found.\nTry raising the similarity slider." if final
                else "Scanning…\nDuplicates will appear here as soon as they are found.")

    def sync(self) -> None:
        for card in self._list.mounted_widgets():
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

    def _show_placeholder(self, text: str) -> None:
        self._placeholder.configure(text=text)
        self._placeholder.place(relx=0.5, rely=0.4, anchor="center")
        self._placeholder.lift()
