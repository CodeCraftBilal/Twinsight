"""Design tokens: one place to restyle the whole app."""
import customtkinter as ctk

BG = ("#f4f5f9", "#0f1117")
SURFACE = ("#ffffff", "#171a23")
SURFACE_ALT = ("#eceef5", "#1e222e")
BORDER = ("#dcdfea", "#2a2f3d")
TEXT = ("#1b1e2b", "#e8eaf2")
MUTED = ("#6b7083", "#8a90a6")
ACCENT = "#6c5ce7"
ACCENT_HOVER = "#5b4bd1"
DANGER = "#ef4565"
DANGER_HOVER = "#d63554"
SUCCESS = "#22c58b"
SELECTED = ("#fde7ec", "#3a1c27")

RADIUS = 14
THUMB = 150


def setup() -> None:
    ctk.set_appearance_mode("dark")
    ctk.set_default_color_theme("dark-blue")


def font(size: int = 13, weight: str = "normal") -> ctk.CTkFont:
    return ctk.CTkFont(size=size, weight=weight)
