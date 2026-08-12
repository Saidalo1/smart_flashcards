"""Generates the app icon and embeds it as base64 in icon.py.

Design language matches the app: the translation-card navy gradient plus the
gold hint (💡) colour. Rendered following 2026 icon practice — a squircle
(superellipse) tile, a single centred glyph inside the ~66% safe zone, one
subtle high-contrast gradient, a soft glow for depth, and 4x supersampling so
edges stay crisp when the OS scales it down to the tray. Requires Pillow + numpy.
"""
import base64
import pathlib

import numpy as np
from PIL import Image, ImageDraw

OUT = 256          # final icon size
SS = 4             # supersample factor
W = OUT * SS       # working resolution

NAVY_TL = np.array([36, 38, 70])     # top-left (lighter)
NAVY_BR = np.array([12, 42, 82])     # bottom-right (deeper)  ~ app #0f3460
GOLD_TOP = np.array([255, 232, 138])
GOLD_BOT = np.array([238, 183, 12])  # ~ app #f1c40f
NAVY_INK = (20, 30, 58)


def _squircle_alpha(n=5.0):
    yy, xx = np.mgrid[0:W, 0:W].astype(np.float64)
    c = (W - 1) / 2.0
    a = W / 2.0
    d = np.abs((xx - c) / a) ** n + np.abs((yy - c) / a) ** n
    return (d <= 1.0)


def _background():
    yy, xx = np.mgrid[0:W, 0:W].astype(np.float64)
    t = (xx + yy) / (2 * (W - 1))                       # diagonal 0..1
    bg = NAVY_TL[None, None, :] * (1 - t)[..., None] + NAVY_BR[None, None, :] * t[..., None]
    # soft gold glow centred on the bulb, for depth
    gx, gy = W * 0.5, W * 0.40
    r = np.sqrt((xx - gx) ** 2 + (yy - gy) ** 2)
    glow = np.clip(1 - r / (W * 0.46), 0, 1) ** 2.2
    bg += np.array([250, 205, 70])[None, None, :] * glow[..., None] * 0.28
    return np.clip(bg, 0, 255).astype(np.uint8)


def _gold_gradient(y0, y1):
    yy = np.mgrid[0:W, 0:W][0].astype(np.float64)
    t = np.clip((yy - y0) / (y1 - y0), 0, 1)
    g = GOLD_TOP[None, None, :] * (1 - t)[..., None] + GOLD_BOT[None, None, :] * t[..., None]
    return Image.fromarray(np.clip(g, 0, 255).astype(np.uint8), 'RGB')


def build_icon():
    s = SS
    bg = Image.fromarray(_background(), 'RGB')

    # glyph mask (a clean lightbulb: round bulb + screw base + foot)
    glyph = Image.new('L', (W, W), 0)
    g = ImageDraw.Draw(glyph)
    g.ellipse([76 * s, 56 * s, 180 * s, 160 * s], fill=255)                 # bulb
    g.rounded_rectangle([105 * s, 150 * s, 151 * s, 190 * s], radius=15 * s, fill=255)  # base
    g.rounded_rectangle([117 * s, 190 * s, 139 * s, 203 * s], radius=7 * s, fill=255)   # foot

    gold = _gold_gradient(56 * s, 203 * s)
    icon = Image.composite(gold, bg, glyph).convert('RGBA')

    # subtle detail: two navy grooves on the screw base + a soft filament
    d = ImageDraw.Draw(icon)
    d.line([108 * s, 166 * s, 148 * s, 166 * s], fill=NAVY_INK, width=5 * s)
    d.line([108 * s, 179 * s, 148 * s, 179 * s], fill=NAVY_INK, width=5 * s)
    d.line([119 * s, 150 * s, 128 * s, 96 * s], fill=NAVY_INK, width=4 * s)
    d.line([137 * s, 150 * s, 128 * s, 96 * s], fill=NAVY_INK, width=4 * s)

    # apply squircle alpha
    alpha = np.asarray(icon)[:, :, 3].copy()
    alpha[~_squircle_alpha()] = 0
    arr = np.asarray(icon).copy()
    arr[:, :, 3] = alpha
    icon = Image.fromarray(arr, 'RGBA')

    return icon.resize((OUT, OUT), Image.LANCZOS)


def main():
    here = pathlib.Path(__file__).parent
    build_icon().save(here / 'app_icon.png', 'PNG')
    b64 = base64.b64encode((here / 'app_icon.png').read_bytes()).decode()
    (here / 'icon.py').write_text(
        "# App tray/window icon, embedded as base64 so it works inside the PyInstaller\n"
        "# bundle with no external file dependency. Regenerate with create_icon.py.\n"
        "icon_b64 = '%s'\n" % b64, encoding='utf-8')
    print(f"Wrote app_icon.png ({(here / 'app_icon.png').stat().st_size} bytes) and icon.py")


if __name__ == '__main__':
    main()
