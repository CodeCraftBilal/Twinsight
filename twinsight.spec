# -*- mode: python ; coding: utf-8 -*-
# Build:  pyinstaller twinsight.spec --noconfirm --clean
import sys
from PyInstaller.utils.hooks import collect_data_files

APP_NAME = "Twinsight"

# CustomTkinter ships themes/fonts as data files that must be bundled.
datas = collect_data_files("customtkinter")
datas += [("assets", "assets")]

icon = "assets/app_icon.ico" if sys.platform.startswith("win") else (
    "assets/app_icon.icns" if sys.platform == "darwin" else "assets/app_icon.png")

a = Analysis(
    ["main.py"],
    pathex=["."],
    binaries=[],
    datas=datas,
    hiddenimports=["PIL._tkinter_finder", "send2trash"],
    hookspath=[],
    runtime_hooks=[],
    excludes=["numpy", "matplotlib", "pandas", "scipy", "pytest"],
    noarchive=False,
)
pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,      # one-folder build: faster startup, fewer AV false positives
    name=APP_NAME,
    debug=False,
    strip=False,
    upx=False,
    console=False,              # GUI app: no terminal window
    icon=icon,
)
coll = COLLECT(exe, a.binaries, a.datas, strip=False, upx=False, name=APP_NAME)

# macOS .app bundle (ignored on other platforms)
if sys.platform == "darwin":
    app = BUNDLE(coll, name=f"{APP_NAME}.app", icon="assets/app_icon.icns",
                 bundle_identifier="com.example.twinsight")
