from __future__ import annotations

import customtkinter as ctk

from . import theme


class ConfirmDialog(ctk.CTkToplevel):
    """Modal confirm dialog. Use ConfirmDialog.ask(...) -> bool."""

    def __init__(self, parent, title: str, message: str, confirm_text: str,
                 danger: bool = True, extra_check: str | None = None) -> None:
        super().__init__(parent)
        self.title(title)
        self.configure(fg_color=theme.SURFACE)
        self.resizable(False, False)
        self.result = False
        self.extra_value = True

        ctk.CTkLabel(self, text=title, font=theme.font(18, "bold")).pack(
            padx=28, pady=(24, 6), anchor="w")
        ctk.CTkLabel(self, text=message, font=theme.font(13), text_color=theme.MUTED,
                     justify="left", wraplength=380).pack(padx=28, anchor="w")

        self._check_var = ctk.BooleanVar(value=True)
        if extra_check:
            ctk.CTkCheckBox(self, text=extra_check, variable=self._check_var,
                            fg_color=theme.ACCENT, hover_color=theme.ACCENT_HOVER
                            ).pack(padx=28, pady=(16, 0), anchor="w")

        row = ctk.CTkFrame(self, fg_color="transparent")
        row.pack(fill="x", padx=28, pady=24)
        ctk.CTkButton(row, text="Cancel", width=100, height=36, corner_radius=10,
                      fg_color=theme.SURFACE_ALT, hover_color=theme.BORDER,
                      text_color=theme.TEXT, command=self.destroy).pack(side="right", padx=(8, 0))
        color, hover = (theme.DANGER, theme.DANGER_HOVER) if danger else (theme.ACCENT, theme.ACCENT_HOVER)
        ctk.CTkButton(row, text=confirm_text, width=120, height=36, corner_radius=10,
                      fg_color=color, hover_color=hover, command=self._ok).pack(side="right")

        self.transient(parent)
        self.after(50, self._grab)

    def _grab(self) -> None:
        try:
            self.grab_set()
            self.focus_set()
        except Exception:
            pass

    def _ok(self) -> None:
        self.result = True
        self.extra_value = self._check_var.get()
        self.destroy()

    @classmethod
    def ask(cls, parent, *args, **kwargs) -> tuple[bool, bool]:
        dlg = cls(parent, *args, **kwargs)
        parent.wait_window(dlg)
        return dlg.result, dlg.extra_value
