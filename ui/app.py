from __future__ import annotations

import queue
import sys
import threading
from pathlib import Path

import customtkinter as ctk

from app_paths import resource_path
from core.grouping import group_similar
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
        self.summary = ctk.CTkLabel(bar, text="", font=theme.font(14, "bold"))
        self.summary.pack(side="left", padx=18, pady=14)

        self.delete_btn = ctk.CTkButton(bar, text="Delete selected", width=140, height=36,
                                        corner_radius=10, fg_color=theme.DANGER,
                                        hover_color=theme.DANGER_HOVER, command=self.delete_selected)
        self.delete_btn.pack(side="right", padx=(6, 14), pady=10)
        for text, cmd in (("Clear", self.clear_selection), ("Select all but best", self.auto_select),):
            ctk.CTkButton(bar, text=text, height=36, corner_radius=10, fg_color=theme.SURFACE_ALT,
                          hover_color=theme.BORDER, text_color=theme.TEXT, command=cmd
                          ).pack(side="right", padx=6, pady=10)

    def _update_toolbar(self) -> None:
        n = len(self.selection)
        self.delete_btn.configure(state="normal" if n else "disabled",
                                  text=f"Delete selected ({n})" if n else "Delete selected")
        groups = self.results.groups if hasattr(self, "results") else []
        if groups:
            total = sum(len(g) for g in groups)
            self.summary.configure(text=f"{len(groups)} groups · {total} images · {n} selected")
        else:
            self.summary.configure(text="Results")

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
        folder = self.sidebar.folder.get()
        if not folder or not Path(folder).is_dir():
            self.sidebar.set_status("Please choose a valid folder first.")
            return
        self.selection.replace([])
        self.results.show_message("Scanning…")
        self._cancel.clear()
        self.sidebar.set_scanning(True)
        args = (Path(folder), bool(self.sidebar.recursive.get()), self.sidebar.threshold)
        self._worker = threading.Thread(target=self._scan_worker, args=args, daemon=True)
        self._worker.start()

    def cancel_scan(self) -> None:
        self._cancel.set()

    def _scan_worker(self, folder: Path, recursive: bool, threshold: int) -> None:
        put = self._events.put
        records, failed = scan_folder(
            folder, recursive, lambda d, t: put(("progress", d, t)), self._cancel)
        if self._cancel.is_set():
            put(("cancelled",))
            return
        put(("grouping",))
        groups = group_similar(records, threshold)
        put(("done", groups, len(records), len(failed)))

    def _drain_events(self) -> None:
        try:
            while True:
                ev = self._events.get_nowait()
                kind = ev[0]
                if kind == "progress":
                    _, d, t = ev
                    self.sidebar.set_progress(d / t if t else 1, f"Analysing {d} / {t}")
                elif kind == "grouping":
                    self.sidebar.set_progress(1, "Comparing images…")
                elif kind == "cancelled":
                    self.sidebar.set_scanning(False)
                    self.sidebar.set_status("Scan cancelled")
                    self.results.show_message("Scan cancelled.")
                elif kind == "done":
                    _, groups, n, failed = ev
                    self.sidebar.set_scanning(False)
                    note = f" ({failed} unreadable)" if failed else ""
                    self.sidebar.set_status(f"Scanned {n} images{note}")
                    self.results.show_groups(groups)
                    self._update_toolbar()
        except queue.Empty:
            pass
        self.after(60, self._drain_events)

    # -- deleting ---------------------------------------------------------
    def delete_selected(self) -> None:
        paths = self.selection.paths
        if not paths:
            return
        trash = file_ops.trash_available()
        ok, to_trash = ConfirmDialog.ask(
            self, "Delete selected images?",
            f"{len(paths)} file(s) will be removed from your disk.",
            "Delete", extra_check="Move to Recycle Bin / Trash (safer)" if trash else None)
        if not ok:
            return
        result = file_ops.delete_files(paths, to_trash=trash and to_trash)
        self.selection.remove_many(result.deleted)
        self.results.remove_paths(result.deleted)
        msg = f"Deleted {len(result.deleted)} files · freed {human_size(result.freed_bytes)}"
        if result.errors:
            msg += f" · {len(result.errors)} failed"
        self.sidebar.set_status(msg)
        self._update_toolbar()

    def _close(self) -> None:
        self._cancel.set()
        self.results.loader.shutdown()
        self.destroy()
