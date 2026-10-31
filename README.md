# Twinsight – Duplicate Image Finder

Modern GUI (CustomTkinter) that finds visually similar images (jpg, png, jpeg, bmp, gif, webp, tiff),
shows them grouped side by side, and lets you tick the ones to delete.

## Run
    pip install -r requirements.txt
    python main.py

Python 3.9+ (3.10+ recommended; works on newer versions too).

## Layout
    main.py              entry point
    core/                pure logic (no GUI): models, hashing, scanner, grouping
    services/file_ops.py deleting files (Recycle Bin via send2trash, or permanent)
    ui/                  theme, sidebar, results view, group card, image tile, dialogs, preview

## How it works
Each image gets a 256-bit perceptual "difference hash". Images whose hashes differ by
<= threshold bits are grouped (slider: 0 = exact, higher = looser). The best copy in each
group (highest resolution, then biggest file) is badged BEST; "Select all but best" ticks the rest.
Click a thumbnail for a large preview.

## Build a standalone app (PyInstaller)
    Windows:      build.bat
    Linux/macOS:  ./build.sh
or manually:

    pip install -r requirements-dev.txt
    python tools/make_icon.py          # regenerates assets/app_icon.png/.ico
    pyinstaller twinsight.spec --noconfirm --clean

Output: `dist/Twinsight/` (one-folder build; zip it to share). To get a single .exe instead,
use `pyinstaller main.py --onefile --noconsole --name Twinsight --icon assets/app_icon.ico
--collect-data customtkinter --add-data "assets;assets"` (use `:` instead of `;` on Linux/macOS).
Replace `assets/app_icon.*` with your own icon any time (macOS needs `app_icon.icns`).

## Create a shareable installer (Windows, Inno Setup)
1. Install [Inno Setup 6](https://jrsoftware.org/isdl.php).
2. Run `build_installer.bat` (builds the app, then compiles `installer/twinsight.iss`).
   Or manually: `build.bat`, then open `installer/twinsight.iss` in Inno Setup and press F9.
3. Share `installer_output/Twinsight-Setup-1.0.0.exe`.

Edit the `#define` lines at the top of the `.iss` (name, version, publisher, URL) before releasing.
Keep `AppId` unchanged across versions so upgrades replace the old install.
To publish on GitHub: Releases -> Draft a new release -> attach the Setup .exe.
Unsigned installers can trigger Windows SmartScreen warnings ("More info -> Run anyway").
