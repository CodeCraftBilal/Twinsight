from __future__ import annotations

import queue
import sys
import threading
import time
from pathlib import Path

import customtkinter as ctk

from app_paths import resource_path
from core.grouping import IncrementalGrouper
from core.scanner import scan_folder
from services import file_ops

from . import theme
from .dialogs import ConfirmDialog
from .helpers import human_size
from .results_view import ResultsView
from .sidebar import Sidebar
from .state import SelectionModel


class App(ctk.CTk):
    def __init__(self) -> None:
        theme.setup()
        super().__init__()
        self.title("Twinsight — Duplicate Image Finder")
        self.geometry("1280x800")
        self.minsize(1000, 600)
        self.configure(fg_color=theme.BG)

        self.selection = SelectionModel()
        self.selection.subscribe(self._update_toolbar)
        self._events: queue.Queue = queue.Queue()
        self._cancel = threading.Event()
        self._worker: threading.Thread | None = None
        self._scanning = False
        self._busy = False                 # a delete is running
        self._stats = (0, 0, 0)            # (groups, images, reclaimable bytes) - cached

        self.sidebar = Sidebar(self, self.start_scan, self.cancel_scan)
        self.sidebar.pack(side="left", fill="y")

        main = ctk.CTkFrame(self, fg_color="transparent")
        main.pack(side="left", fill="both", expand=True, padx=24, pady=20)
        self._build_toolbar(main)
        self.results = ResultsView(main, self.selection)
        self.results.pack(fill="both", expand=True, pady=(12, 0))
        self.results.show_message("Choose a folder and press  Scan  to begin.")

        self._update_toolbar()
        self.after(60, self._drain_events)
        self.after(250, self._set_icon)  # CustomTkinter resets the icon on Windows at ~200ms
        self.protocol("WM_DELETE_WINDOW", self._close)

    def _set_icon(self) -> None:
        try:
            if sys.platform.startswith("win"):
                self.iconbitmap(str(resource_path("assets/app_icon.ico")))
            else:
                from PIL import Image, ImageTk
                self._icon = ImageTk.PhotoImage(Image.open(resource_path("assets/app_icon.png")))
                self.iconphoto(True, self._icon)
        except Exception:
            pass  # icon is cosmetic

    # -- toolbar ----------------------------------------------------------
    def _build_toolbar(self, parent) -> None:
        bar = ctk.CTkFrame(parent, fg_color=theme.SURFACE, corner_radius=theme.RADIUS,
                           border_width=1, border_color=theme.BORDER)
        bar.pack(fill="x")
        info = ctk.CTkFrame(bar, fg_color="transparent")
        info.pack(side="left", padx=18, pady=12)
        self.summary = ctk.CTkLabel(info, text="", font=theme.font(14, "bold"), anchor="w")
        self.summary.pack(anchor="w")
        self.space_label = ctk.CTkLabel(info, text="", font=theme.font(12),
                                        text_color=theme.MUTED, anchor="w")
        self.space_label.pack(anchor="w")

        self.delete_btn = ctk.CTkButton(bar, text="Delete selected", width=210, height=38,
                                        corner_radius=10, fg_color=theme.DANGER,
                                        hover_color=theme.DANGER_HOVER, command=self.delete_selected)
        self.delete_btn.pack(side="right", padx=(6, 14), pady=10)
        for text, cmd in (("Clear", self.clear_selection), ("Select all but best", self.auto_select),):
            ctk.CTkButton(bar, text=text, height=38, corner_radius=10, fg_color=theme.SURFACE_ALT,
                          hover_color=theme.BORDER, text_color=theme.TEXT, command=cmd
                          ).pack(side="right", padx=6, pady=10)

    def _update_toolbar(self) -> None:
        n, freed = len(self.selection), self.selection.total_bytes
        can_delete = n > 0 and not self._scanning and not self._busy
        label = f"Delete {n} · free {human_size(freed)}" if n else "Delete selected"
        self.delete_btn.configure(state="normal" if can_delete else "disabled", text=label)

        n_groups, total, reclaim = self._stats
        if n_groups:
            live = "  ·  scanning…" if self._scanning else ""
            self.summary.configure(text=f"{n_groups} groups · {total} images{live}")
            sel = (f"Selected {n} file{'s' if n != 1 else ''} → frees {human_size(freed)}"
                   if n else "Nothing selected")
            self.space_label.configure(
                text=f"{sel}   |   Up to {human_size(reclaim)} can be reclaimed")
        else:
            self.summary.configure(text="Results")
            self.space_label.configure(text="")

    # -- selection --------------------------------------------------------
    def auto_select(self) -> None:
        """Mark every image except the best one in each group."""
        paths = [r.path for g in self.results.groups for r in g.images if r is not g.best()]
        self.selection.replace(paths)
        self.results.sync()

    def clear_selection(self) -> None:
        self.selection.replace([])
        self.results.sync()

    # -- scanning ---------------------------------------------------------
    def start_scan(self) -> None:
        if self._busy:
            return
        folder = self.sidebar.folder.get()
        if not folder or not Path(folder).is_dir():
            self.sidebar.set_status("Please choose a valid folder first.")
            return
        self.selection.replace([])
        self.selection.set_sizes({})
        self.results.show_message("Scanning…\nDuplicates will appear here as soon as they are found.")
        self._cancel.clear()
        self._scanning = True
        self.sidebar.set_scanning(True)
        self._update_toolbar()
        args = (Path(folder), bool(self.sidebar.recursive.get()), self.sidebar.threshold)
        self._worker = threading.Thread(target=self._scan_worker, args=args, daemon=True)
        self._worker.start()

    def cancel_scan(self) -> None:
        self._cancel.set()

    def _scan_worker(self, folder: Path, recursive: bool, threshold: int) -> None:
        put = self._events.put
        grouper = IncrementalGrouper(threshold)
        last_emit = [0.0]

        def on_record(rec) -> None:
            grouper.add(rec)
            now = time.monotonic()
            if grouper.dirty and now - last_emit[0] > 0.6:   # throttle UI refreshes
                last_emit[0] = now
                put(("groups", grouper.snapshot()))

        last_prog = [0.0]

        def on_progress(done: int, total: int) -> None:
            now = time.monotonic()
            if done == total or now - last_prog[0] > 0.1:
                last_prog[0] = now
                put(("progress", done, total, grouper.group_count))

        _records, failed = scan_folder(folder, recursive, on_progress, self._cancel, on_record)
        put(("done", grouper.snapshot(sort_by_size=True), grouper.total, len(failed),
             self._cancel.is_set()))

    def _apply_groups(self, groups, final: bool) -> None:
        self._stats = (len(groups), sum(len(g) for g in groups),
                       sum(g.reclaimable_bytes for g in groups))
        self.selection.set_sizes({r.path: r.size_bytes for g in groups for r in g.images})
        self.results.set_groups(groups, final=final)
        self._update_toolbar()

    def _drain_events(self) -> None:
        latest_groups = None
        try:
            while True:
                ev = self._events.get_nowait()
                kind = ev[0]
                if kind == "progress":
                    _, d, t, g = ev
                    self.sidebar.set_progress(
                        d / t if t else 1, f"Analysing {d} / {t}\n{g} duplicate group{'s' if g != 1 else ''} found")
                elif kind == "groups":
                    latest_groups = ev[1]          # only the newest snapshot matters
                elif kind == "del_progress":
                    self.sidebar.set_status(f"Deleting {ev[1]} / {ev[2]}…")
                elif kind == "del_done":
                    self._finish_delete(ev[1])
                elif kind == "done":
                    _, groups, n, failed, cancelled = ev
                    latest_groups = None
                    self._scanning = False
                    self.sidebar.set_scanning(False)
                    note = f" ({failed} unreadable)" if failed else ""
                    self.sidebar.set_status(
                        ("Scan cancelled — showing partial results\n" if cancelled else "")
                        + f"Scanned {n} images{note}")
                    self._apply_groups(groups, final=True)
        except queue.Empty:
            pass
        if latest_groups is not None:
            self._apply_groups(latest_groups, final=False)
        self.after(60, self._drain_events)

    # -- deleting ---------------------------------------------------------
    def delete_selected(self) -> None:
        paths = self.selection.paths
        if not paths:
            return
        trash = file_ops.trash_available()
        chosen = set(paths)
        wiped = sum(1 for g in self.results.groups if all(r.path in chosen for r in g.images))
        message = (f"{len(paths)} file(s) will be removed, freeing "
                   f"{human_size(self.selection.total_bytes)}.")
        if wiped:
            message += (f"\n\n⚠ In {wiped} group(s) every copy is selected, so those images "
                        "will be gone completely.")
        ok, to_trash = ConfirmDialog.ask(
            self, "Delete selected images?", message,
            "Delete", extra_check="Move to Recycle Bin / Trash (safer)" if trash else None)
        if not ok:
            return
        self._busy = True
        self.sidebar.set_status(f"Deleting 0 / {len(paths)}…")
        self._update_toolbar()
        threading.Thread(target=self._delete_worker, args=(paths, trash and to_trash),
                         daemon=True).start()

    def _delete_worker(self, paths, to_trash: bool) -> None:
        """Runs off the UI thread so deleting thousands of files never freezes the window."""
        last = [0.0]

        def progress(done: int, total: int) -> None:
            now = time.monotonic()
            if done == total or now - last[0] > 0.15:
                last[0] = now
                self._events.put(("del_progress", done, total))

        self._events.put(("del_done", file_ops.delete_files(paths, to_trash, progress)))

    def _finish_delete(self, result) -> None:
        self._busy = False
        self.selection.remove_many(result.deleted)
        self.results.remove_paths(result.deleted)
        groups = self.results.groups
        self._stats = (len(groups), sum(len(g) for g in groups),
                       sum(g.reclaimable_bytes for g in groups))
        msg = f"Deleted {len(result.deleted)} files · freed {human_size(result.freed_bytes)}"
        if result.errors:
            msg += f" · {len(result.errors)} failed"
        self.sidebar.set_status(msg)
        self._update_toolbar()

    def _close(self) -> None:
        self._cancel.set()
        self.results.loader.shutdown()
        self.destroy()
