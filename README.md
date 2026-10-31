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
