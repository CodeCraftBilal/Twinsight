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
    ui/                  theme, sidebar, results view, virtual list + layout, group card, image tile, dialogs, preview

## How it works
Each image gets a 256-bit perceptual "difference hash". Images whose hashes differ by
<= threshold bits are grouped (slider: 0 = exact, higher = looser). The best copy in each
group (highest resolution, then biggest file) is badged BEST; "Select all but best" ticks the rest.
Click a thumbnail for a large preview.

## Build a standalone app (PyInstaller)
    Windows:      scripts\build.bat
    Linux/macOS:  ./scripts/build.sh
or manually:

    pip install -r requirements-dev.txt
    python scripts/tools/make_icon.py          # regenerates assets/app_icon.png/.ico
    pyinstaller twinsight.spec --noconfirm --clean

Output: `dist/Twinsight/` (one-folder build; zip it to share). To get a single .exe instead,
use `pyinstaller main.py --onefile --noconsole --name Twinsight --icon assets/app_icon.ico
--collect-data customtkinter --add-data "assets;assets"` (use `:` instead of `;` on Linux/macOS).
Replace `assets/app_icon.*` with your own icon any time (macOS needs `app_icon.icns`).

## Create a shareable installer (Windows, Inno Setup)
1. Install [Inno Setup 6](https://jrsoftware.org/isdl.php).
2. Run `scripts\build_installer.bat` (builds the app, then compiles `installer/twinsight.iss`).
   Or manually: `scripts\build.bat`, then open `installer/twinsight.iss` in Inno Setup and press F9.
3. Share `installer_output/Twinsight-Setup-1.0.0.exe`.

Edit the `#define` lines at the top of the `.iss` (name, version, publisher, URL) before releasing.
Keep `AppId` unchanged across versions so upgrades replace the old install.
To publish on GitHub: Releases -> Draft a new release -> attach the Setup .exe.
Unsigned installers can trigger Windows SmartScreen warnings ("More info -> Run anyway").

## Live results & space saved
Duplicates appear in the results list *while* the scan is still running (groups grow and merge
as more images are analysed; Delete is enabled once the scan finishes, and Cancel keeps the
partial results). The toolbar always shows how much disk space the current selection will free
and how much could be reclaimed in total.

## Performance (virtualised list)
Results use a virtual list (`ui/virtual_list.py`, maths in `ui/layout.py`): only the groups near the
visible area exist as widgets (plus a small buffer), so 100,000 groups cost the same as 20. Rows are
created a few at a time nearest the viewport, thumbnails for rows that scroll away are skipped, JPEGs are
decoded at reduced size, and deleting runs in a background thread with progress.

Each group card has **Select all but best** (keeps the highest-resolution copy, ticks the rest) and **Clear**.
