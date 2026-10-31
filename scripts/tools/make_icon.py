"""Generate assets/app_icon.png and assets/app_icon.ico (run: python tools/make_icon.py)."""
from pathlib import Path

from PIL import Image, ImageDraw

OUT = Path(__file__).resolve().parent.parent / "assets"
S = 1024


def gradient(size: int) -> Image.Image:
    top, bottom = (124, 108, 240), (84, 62, 200)
    img = Image.new("RGB", (size, size))
    px = img.load()
    for y in range(size):
        t = y / (size - 1)
        c = tuple(int(top[i] + (bottom[i] - top[i]) * t) for i in range(3))
        for x in range(size):
            px[x, y] = c
    return img


def frame(color, outline=None) -> Image.Image:
    """A 'photo' card with a sun and mountains."""
    w, h = 520, 420
    card = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    d = ImageDraw.Draw(card)
    d.rounded_rectangle([0, 0, w - 1, h - 1], radius=56, fill=color)
    d.ellipse([w - 190, 60, w - 90, 160], fill=(255, 205, 90, 255))
    d.polygon([(40, h - 50), (190, 190), (300, h - 50)], fill=(108, 92, 231, 255))
    d.polygon([(210, h - 50), (330, 250), (w - 40, h - 50)], fill=(34, 197, 139, 255))
    return card


def build() -> Image.Image:
    bg = gradient(S).convert("RGBA")
    mask = Image.new("L", (S, S), 0)
    ImageDraw.Draw(mask).rounded_rectangle([0, 0, S - 1, S - 1], radius=220, fill=255)
    icon = Image.new("RGBA", (S, S), (0, 0, 0, 0))
    icon.paste(bg, (0, 0), mask)

    back = frame((255, 255, 255, 150)).rotate(8, expand=True, resample=Image.BICUBIC)
    front = frame((255, 255, 255, 255)).rotate(-6, expand=True, resample=Image.BICUBIC)
    icon.alpha_composite(back, (330, 150))
    icon.alpha_composite(front, (150, 330))
    return icon


if __name__ == "__main__":
    OUT.mkdir(exist_ok=True)
    img = build()
    img.resize((512, 512), Image.LANCZOS).save(OUT / "app_icon.png")
    img.save(OUT / "app_icon.ico",
             sizes=[(16, 16), (24, 24), (32, 32), (48, 48), (64, 64), (128, 128), (256, 256)])
    print("Icons written to", OUT)
