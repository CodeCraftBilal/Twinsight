"""A virtualised vertical list: only rows near the viewport exist as widgets.

Memory and CPU stay flat whether the list has 20 rows or 200,000.
Widgets are created lazily (a few per idle pass, nearest the viewport first)
and destroyed once they scroll far away.
"""
from __future__ import annotations

import sys
import tkinter
from typing import Any, Callable, Hashable

import customtkinter as ctk

from .layout import ListLayout

SIDE = 4  # horizontal margin around each row


class VirtualList(ctk.CTkFrame):
    BUFFER = 0.75          # viewports of extra rows kept mounted above/below
    MOUNT_PER_PASS = 3     # rows created per idle pass (keeps the UI responsive)
    WHEEL_STEP = 80        # pixels per mouse-wheel notch

    def __init__(
        self, parent,
        factory: Callable[[Any, Any, int, int], Any],   # (parent, item, index, width) -> widget
        height_of: Callable[[Any, int], int],           # (item, width) -> pixel height
        key_of: Callable[[Any], Hashable],
        sig_of: Callable[[Any], Hashable],              # changes when a row must be rebuilt
        renumber: Callable[[Any, int], None] | None = None,
    ) -> None:
        super().__init__(parent, fg_color="transparent")
        self._factory, self._height_of = factory, height_of
        self._key_of, self._sig_of, self._renumber = key_of, sig_of, renumber

        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(0, weight=1)
        self._view = ctk.CTkFrame(self, fg_color="transparent", corner_radius=0)
        self._view.grid(row=0, column=0, sticky="nsew")
        self._bar = ctk.CTkScrollbar(self, command=self._on_bar)
        self._bar.grid(row=0, column=1, sticky="ns", padx=(4, 0))

        self._layout = ListLayout(gap=10, pad=6)
        self._items: list[Any] = []
        self._index_of: dict[Hashable, int] = {}
        self._mounted: dict[Hashable, tuple[Hashable, Any, int]] = {}  # key -> (sig, widget, idx)
        self._top = 0
        self._layout_w = 0
        self._mount_job = None
        self._resize_job = None

        self._view.bind("<Configure>", self._on_configure, add="+")
        for seq in ("<MouseWheel>", "<Button-4>", "<Button-5>"):
            # CTk widgets forbid bind_all, so call the plain-tkinter implementation directly
            tkinter.Misc.bind_all(self, seq, self._on_wheel, add="+")

    # ------------------------------------------------------------ public API
    def set_items(self, items: list[Any]) -> None:
        self._items = items
        self._index_of = {self._key_of(it): i for i, it in enumerate(items)}
        self._rebuild_layout()
        for key in list(self._mounted):
            sig, widget, old_i = self._mounted[key]
            i = self._index_of.get(key)
            if i is None or self._sig_of(items[i]) != sig:
                self._drop(key)
            elif i != old_i:
                if self._renumber:
                    self._renumber(widget, i)
                self._mounted[key] = (sig, widget, i)
        self._top = self._layout.clamp(self._top, self._vh())
        self._after_change()

    def mounted_widgets(self) -> list[Any]:
        return [w for _s, w, _i in self._mounted.values()]

    def scroll_to_top(self) -> None:
        self._set_top(0)

    # --------------------------------------------------------------- layout
    def _vh(self) -> int:
        return max(self._view.winfo_height(), 1)

    def _card_width(self) -> int:
        return max(self._view.winfo_width() - 2 * SIDE, 120)

    def _rebuild_layout(self) -> None:
        self._layout_w = self._card_width()
        w = self._layout_w
        self._layout.rebuild([self._height_of(it, w) for it in self._items])

    def _on_configure(self, _event=None) -> None:
        if self._card_width() != self._layout_w:
            if self._resize_job:
                self.after_cancel(self._resize_job)
            self._resize_job = self.after(120, self._relayout_width)
        else:
            self._top = self._layout.clamp(self._top, self._vh())
            self._after_change()

    def _relayout_width(self) -> None:
        """Width changed -> row heights change. Keep the same row at the top."""
        self._resize_job = None
        idx, within = self._layout.anchor(self._top)
        for key in list(self._mounted):
            self._drop(key)
        self._rebuild_layout()
        if self._items:
            self._top = self._layout.clamp(self._layout.offset(min(idx, len(self._items) - 1)) + within,
                                           self._vh())
        self._after_change()

    # ------------------------------------------------------ mounting logic
    def _visible(self) -> range:
        vh = self._vh()
        return self._layout.visible(self._top, vh, vh * self.BUFFER)

    def _drop(self, key: Hashable) -> None:
        _sig, widget, _i = self._mounted.pop(key)
        widget.destroy()

    def _after_change(self) -> None:
        keep = {self._key_of(self._items[i]) for i in self._visible()}
        for key in [k for k in self._mounted if k not in keep]:
            self._drop(key)
        self._place_all()
        self._update_bar()
        self._schedule_mount()

    def _place_all(self) -> None:
        lay, w, top = self._layout, self._layout_w, self._top
        for _sig, widget, i in self._mounted.values():
            h = lay.height(i)
            if getattr(widget, "_vl_size", None) != (w, h):
                # CTk widgets take width/height via configure(), not place()
                widget.configure(width=w, height=h)
                widget._vl_size = (w, h)
            widget.place(x=SIDE, y=lay.offset(i) - top)

    def _schedule_mount(self) -> None:
        if self._mount_job is None:
            self._mount_job = self.after(1, self._mount_step)

    def _mount_step(self) -> None:
        self._mount_job = None
        if self._view.winfo_width() < 50 or not self._items:
            return
        missing = [i for i in self._visible()
                   if self._key_of(self._items[i]) not in self._mounted]
        if not missing:
            return
        centre = self._top + self._vh() / 2
        lay = self._layout
        missing.sort(key=lambda i: abs(lay.offset(i) + lay.height(i) / 2 - centre))
        for i in missing[:self.MOUNT_PER_PASS]:
            it = self._items[i]
            widget = self._factory(self._view, it, i, self._layout_w)
            self._mounted[self._key_of(it)] = (self._sig_of(it), widget, i)
        self._place_all()
        if len(missing) > self.MOUNT_PER_PASS:
            self._schedule_mount()

    # ------------------------------------------------------------ scrolling
    def _set_top(self, y: float) -> None:
        y = self._layout.clamp(y, self._vh())
        if y != self._top:
            self._top = y
            self._after_change()

    def _update_bar(self) -> None:
        total, vh = self._layout.total, self._vh()
        if total <= vh:
            self._bar.set(0, 1)
        else:
            self._bar.set(self._top / total, (self._top + vh) / total)

    def _on_bar(self, *args) -> None:
        if args[0] == "moveto":
            self._set_top(float(args[1]) * self._layout.total)
        elif args[0] == "scroll":
            n, unit = int(args[1]), args[2]
            self._set_top(self._top + n * (self._vh() * 0.9 if unit == "pages" else self.WHEEL_STEP))

    def _pointer_over_list(self) -> bool:
        try:
            x, y = self.winfo_pointerxy()
            over = self.winfo_containing(x, y)
            if over is None or over.winfo_toplevel() is not self.winfo_toplevel():
                return False
            v = self._view
            return (v.winfo_rootx() <= x < v.winfo_rootx() + v.winfo_width() and
                    v.winfo_rooty() <= y < v.winfo_rooty() + v.winfo_height())
        except Exception:
            return False

    def _on_wheel(self, event) -> None:
        try:
            if not self.winfo_exists() or not self._pointer_over_list():
                return
            if event.num == 4:
                dy = -self.WHEEL_STEP
            elif event.num == 5:
                dy = self.WHEEL_STEP
            elif sys.platform == "darwin":
                dy = -event.delta * 6
            else:
                dy = -event.delta / 120 * self.WHEEL_STEP
            self._set_top(self._top + dy)
        except Exception:
            pass
