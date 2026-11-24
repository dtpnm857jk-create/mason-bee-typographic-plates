#!/usr/bin/env python3
"""Stem & Mud plates 21–25. Same typographic system as 16–20.

Original SVG line art + SIL OFL typography. 5000 x 5500 px transparent PNG.
"""
from __future__ import annotations

import math
import sys
from pathlib import Path

# Reuse the plate chrome, bee, SVG rasterizer, and typography from batch 4.
sys.path.insert(0, str(Path(__file__).resolve().parent))
import render_16_20 as r  # noqa: E402
from render_16_20 import (  # noqa: E402
    F_DISP_IT,
    F_DISP_XB,
    F_MONO,
    H,
    OUT_DIR,
    SVG_DIR,
    W,
    Svg,
    _mono,
    _raster_and_paste,
    _title_block,
    apply_palette,
    draw_bee,
    font,
    make_preview,
    new_canvas,
    plate_footer,
    plate_header,
)

# Live palette: must be read from render_16_20 after apply_palette(), not copied at import time.
def INK():
    return r.INK
def MOSS():
    return r.MOSS
def CLAY():
    return r.CLAY
def DUSK():
    return r.DUSK

from PIL import Image, ImageDraw


def _simple_house(s: Svg, hx, hy, box_w=620, box_h=480, holes=(3, 3)):
    """A compact nest box on a short stem, used as a diagram unit (original geometry)."""
    x0, y0 = hx - box_w / 2, hy - box_h / 2
    s.polyline(
        [
            (x0 - 40, y0 - 10),
            (x0 + 30, y0 - 130),
            (x0 + box_w + 40, y0 - 10),
            (x0 + box_w, y0 + 8),
            (x0, y0 + 8),
            (x0 - 40, y0 - 10),
        ],
        INK(),
        8,
    )
    s.rect(x0, y0, box_w, box_h, INK(), 8, rx=14)
    cols, rows = holes
    mx, my = 70, 90
    for r in range(rows):
        for c in range(cols):
            cx = x0 + mx + c * ((box_w - 2 * mx) / max(1, cols - 1))
            cy = y0 + my + r * ((box_h - 2 * my) / max(1, rows - 1))
            s.circle(cx, cy, 18, INK(), 5)
    return x0, y0, box_w, box_h


def art_height(w: int, h: int) -> tuple[Svg, dict]:
    s = Svg(w, h)
    ground = int(h * 0.88)
    s.line(int(w * 0.12), ground, int(w * 0.88), ground, INK(), 8)
    # a few grass ticks
    for i, ox in enumerate(range(int(w * 0.14), int(w * 0.86), 90)):
        hh = 28 + (i % 3) * 14
        s.line(ox, ground, ox + 8, ground - hh, MOSS(), 4)
    hx = int(w * 0.58)
    box_h = 420
    hy = int(h * 0.34)
    x0, y0, box_w, box_h = _simple_house(s, hx, hy, box_w=560, box_h=box_h)
    # post from box to ground
    s.line(hx, y0 + box_h, hx, ground, INK(), 10)
    # dimension line to the left of the post
    dim_x = int(w * 0.28)
    top = y0 + box_h / 2
    s.line(dim_x, top, dim_x, ground, CLAY(), 7)
    s.line(dim_x - 28, top, dim_x + 28, top, CLAY(), 7)
    s.line(dim_x - 28, ground, dim_x + 28, ground, CLAY(), 7)
    # arrowheads
    s.polyline([(dim_x, top), (dim_x - 14, top + 22), (dim_x + 14, top + 22)], CLAY(), 5, closed=True)
    s.polyline([(dim_x, ground), (dim_x - 14, ground - 22), (dim_x + 14, ground - 22)], CLAY(), 5, closed=True)
    # a bee approaching the box
    draw_bee(s, x0 + box_w + 180, y0 + box_h - 40, scale=1.1, body=INK(), wing=DUSK(), facing=-1)
    anchors = {"dim": (dim_x, (top + ground) / 2)}
    return s, anchors


def art_forage(w: int, h: int) -> tuple[Svg, dict]:
    s = Svg(w, h)
    cx, cy = int(w * 0.46), int(h * 0.56)
    radius = 780
    pts = []
    for i in range(80):
        a = 2 * math.pi * i / 80
        pts.append((cx + radius * math.cos(a), cy + radius * math.sin(a)))
    for i in range(0, 80, 2):
        s.line(pts[i][0], pts[i][1], pts[(i + 1) % 80][0], pts[(i + 1) % 80][1], MOSS(), 6)
    # radius dimension along a clear right-hand line, below the bee
    s.line(cx, cy, cx + radius, cy, CLAY(), 6)
    s.polyline([(cx + radius, cy), (cx + radius - 22, cy - 12), (cx + radius - 22, cy + 12)], CLAY(), 4, closed=True)
    _simple_house(s, cx, cy - 8, box_w=200, box_h=150, holes=(3, 2))

    def blossom(bx, by, r, color):
        for k in range(5):
            a = -math.pi / 2 + k * 2 * math.pi / 5
            s.ellipse(bx + math.cos(a) * r * 0.55, by + math.sin(a) * r * 0.55, r * 0.42, r * 0.28, color, 5)
        s.circle(bx, by, r * 0.22, color, 4)

    # blossoms sit on the dashed ring, well away from the house
    blossom(cx + radius * math.cos(-0.9), cy + radius * math.sin(-0.9), 64, CLAY())
    blossom(cx + radius * math.cos(0.55), cy + radius * math.sin(0.55), 58, CLAY())
    blossom(cx + radius * math.cos(-2.3), cy + radius * math.sin(-2.3), 54, CLAY())
    # bee on the ring, upper right, not on the house or the dimension line
    ang = -0.45
    draw_bee(s, cx + radius * math.cos(ang), cy + radius * math.sin(ang) - 10, scale=1.15, body=INK(), wing=DUSK(), facing=1)
    anchors = {"range": (cx + radius * 0.55, cy + 56)}
    return s, anchors


def art_stay(w: int, h: int) -> tuple[Svg, dict]:
    s = Svg(w, h)
    hx, hy = int(w * 0.42), int(h * 0.50)
    x0, y0, box_w, box_h = _simple_house(s, hx, hy, box_w=640, box_h=500)
    s.line(hx, y0 + box_h, hx, y0 + box_h + 200, INK(), 10)
    s.line(hx - 80, y0 + box_h + 200, hx + 80, y0 + box_h + 200, INK(), 8)
    # a rightward "move" arrow, clearly struck through
    ax0, ay = x0 + box_w + 120, hy
    ax1 = ax0 + 560
    s.line(ax0, ay, ax1, ay, CLAY(), 8)
    s.polyline([(ax1, ay), (ax1 - 36, ay - 22), (ax1 - 36, ay + 22)], CLAY(), 6, closed=True)
    # a steep ink stroke across the arrow so it reads as "do not"
    s.line(ax0 + 20, ay + 110, ax1 - 10, ay - 110, INK(), 10)
    draw_bee(s, x0 - 170, y0 + box_h - 20, scale=1.05, body=INK(), wing=DUSK(), facing=1)
    anchors = {"stay": (ax0 + 280, ay + 150)}
    return s, anchors


def art_color(w: int, h: int) -> tuple[Svg, dict]:
    s = Svg(w, h)
    # left: blue-green mason bee (dusk + moss wings already in series palette)
    lx, ly = int(w * 0.30), int(h * 0.50)
    draw_bee(s, lx, ly, scale=2.0, body=DUSK(), wing=MOSS(), facing=1)
    # right: a generic yellow-and-black banded oval, struck through — not a species portrait
    rx, ry = int(w * 0.72), int(h * 0.50)
    s.ellipse(rx, ry, 170, 90, CLAY(), 8)
    for off in (-70, 0, 70):
        s.path(
            f"M {rx + off - 12} {ry - 70} Q {rx + off + 10} {ry} {rx + off - 12} {ry + 70}",
            CLAY(),
            6,
        )
    # small head circle
    s.ellipse(rx - 200, ry, 70, 60, CLAY(), 7)
    # strike
    s.line(rx - 280, ry + 130, rx + 200, ry - 130, INK(), 8)
    anchors = {"left": (lx, ly + 230), "right": (rx, ry + 200)}
    return s, anchors


def art_wood(w: int, h: int) -> tuple[Svg, dict]:
    s = Svg(w, h)
    cx, cy = int(w * 0.42), int(h * 0.52)
    length, height = 2000, 780
    x0, y0 = cx - length / 2, cy - height / 2
    s.rect(x0, y0, length, height, INK(), 10, rx=20)
    # end-grain rings on the left end, so it reads as a timber section
    for r in (40, 80, 120, 160):
        s.ellipse(x0 + 8, cy, 18, r, MOSS(), 5)
    # grain lines
    for i, yy in enumerate((y0 + 120, y0 + 230, y0 + 400, y0 + 520, y0 + 650)):
        pts = []
        for k in range(20):
            t = k / 19
            x = x0 + 80 + t * (length - 140)
            pts.append((x, yy + 14 * math.sin(t * math.pi * 2 + i)))
        s.polyline(pts, MOSS(), 5)
    draw_bee(s, int(w * 0.80), cy, scale=1.35, body=INK(), wing=DUSK(), facing=-1)
    anchors = {"label": (cx, y0 - 20)}
    return s, anchors


def design_21() -> Image.Image:
    im = new_canvas()
    d = ImageDraw.Draw(im)
    hy = plate_header(d, "PLATE 21", "HOUSE HEIGHT")
    y = hy + 40
    y = _title_block(d, y, "Three to six", "feet up.", 300, 300, INK(), CLAY(), gap=6)
    band_top = y + 40
    band_bot = 4780
    art_h = min(2200, band_bot - band_top)
    art_w = 3800
    top = band_top + max(0, (band_bot - band_top - art_h) // 2)
    svg, anchors = art_height(art_w, art_h)
    _raster_and_paste(im, svg, "21-three-to-six-feet-up.svg", art_w, art_h, top)
    art_x = (W - art_w) // 2
    dx, dy = anchors["dim"]
    _mono(d, art_x + dx + 40, top + dy, "3–6 ft", size=52, fill=CLAY(), anchor="lm")
    _mono(d, art_x + dx + 40, top + dy + 64, "about 1–2 m", size=40, fill=CLAY(), anchor="lm")
    plate_footer(d, "OPTIMUM HEIGHT  ·  OFF THE GROUND")
    return im


def design_22() -> Image.Image:
    im = new_canvas()
    d = ImageDraw.Draw(im)
    hy = plate_header(d, "PLATE 22", "FORAGE RANGE")
    y = hy + 40
    y = _title_block(d, y, "A few hundred", "feet.", 300, 300, INK(), MOSS(), gap=6)
    band_top = y + 20
    band_bot = 4780
    art_h = min(2300, band_bot - band_top)
    art_w = 4000
    top = band_top + max(0, (band_bot - band_top - art_h) // 2)
    svg, anchors = art_forage(art_w, art_h)
    _raster_and_paste(im, svg, "22-a-few-hundred-feet.svg", art_w, art_h, top)
    art_x = (W - art_w) // 2
    rx, ry = anchors["range"]
    _mono(d, art_x + rx, top + ry, "about 200–300 ft", size=48, fill=CLAY(), anchor="mm")
    plate_footer(d, "FLOWERS NEAR THE NEST")
    return im


def design_23() -> Image.Image:
    im = new_canvas()
    d = ImageDraw.Draw(im)
    hy = plate_header(d, "PLATE 23", "LEAVE IT PUT")
    y = hy + 30
    y = _title_block(d, y, "Don't move it", "mid-season.", 280, 280, INK(), CLAY(), gap=8)
    band_top = y + 40
    band_bot = 4780
    art_h = min(2100, band_bot - band_top)
    art_w = 4000
    top = band_top + max(0, (band_bot - band_top - art_h) // 2)
    svg, anchors = art_stay(art_w, art_h)
    _raster_and_paste(im, svg, "23-dont-move-it-mid-season.svg", art_w, art_h, top)
    art_x = (W - art_w) // 2
    sx, sy = anchors["stay"]
    _mono(d, art_x + sx, top + sy, "DO NOT MOVE", size=48, fill=INK(), anchor="mm")
    plate_footer(d, "NOT WHILE THEY ARE NESTING")
    return im


def design_24() -> Image.Image:
    im = new_canvas()
    d = ImageDraw.Draw(im)
    hy = plate_header(d, "PLATE 24", "OSMIA LIGNARIA")
    y = hy + 40
    y = _title_block(d, y, "Blue-green,", "not gold.", 320, 300, DUSK(), CLAY(), gap=6)
    band_top = y + 40
    band_bot = 4780
    art_h = min(2100, band_bot - band_top)
    art_w = 4000
    top = band_top + max(0, (band_bot - band_top - art_h) // 2)
    svg, anchors = art_color(art_w, art_h)
    _raster_and_paste(im, svg, "24-blue-green-not-gold.svg", art_w, art_h, top)
    art_x = (W - art_w) // 2
    lx, ly = anchors["left"]
    rx, ry = anchors["right"]
    _mono(d, art_x + lx, top + ly, "OSMIA LIGNARIA", size=44, fill=DUSK(), anchor="mm")
    _mono(d, art_x + rx, top + ry, "NOT THIS", size=44, fill=INK(), anchor="mm")
    plate_footer(d, "BLUE ORCHARD MASON BEE")
    return im


def design_25() -> Image.Image:
    im = new_canvas()
    d = ImageDraw.Draw(im)
    hy = plate_header(d, "PLATE 25", "NEST WOOD")
    y = hy + 50
    y = _title_block(d, y, "Untreated wood,", "please.", 280, 280, INK(), MOSS(), gap=8)
    band_top = y + 80
    band_bot = 4780
    art_h = min(1900, band_bot - band_top)
    art_w = 4000
    top = band_top + max(0, (band_bot - band_top - art_h) // 2)
    svg, anchors = art_wood(art_w, art_h)
    _raster_and_paste(im, svg, "25-untreated-wood-please.svg", art_w, art_h, top)
    art_x = (W - art_w) // 2
    lx, ly = anchors["label"]
    _mono(d, art_x + art_w * 0.42, top + max(int(ly) - 80, 8), "UNTREATED", size=52, fill=CLAY(), anchor="mm")
    plate_footer(d, "AVOID PRESSURE-TREATED LUMBER")
    return im


DESIGNS = {
    "21-three-to-six-feet-up.png": design_21,
    "22-a-few-hundred-feet.png": design_22,
    "23-dont-move-it-mid-season.png": design_23,
    "24-blue-green-not-gold.png": design_24,
    "25-untreated-wood-please.png": design_25,
}

LABELS = [
    "21  Three to six feet up.",
    "22  A few hundred feet.",
    "23  Don't move it mid-season.",
    "24  Blue-green, not gold.",
    "25  Untreated wood, please.",
]


def render_named(names, out_dir: Path, *, light_ink: bool):
    apply_palette(light_ink=light_ink)
    out_dir.mkdir(parents=True, exist_ok=True)
    paths = []
    for name in names:
        im = DESIGNS[name]()
        path = out_dir / name
        im.save(path, "PNG", optimize=True)
        print("wrote", path, im.size, im.mode, path.stat().st_size)
        paths.append(path)
    return paths


def main() -> None:
    SVG_DIR.mkdir(parents=True, exist_ok=True)
    names = list(DESIGNS.keys())
    light_paths = render_named(names, OUT_DIR, light_ink=False)
    dark_paths = render_named(names, OUT_DIR / "dark", light_ink=True)
    make_preview(
        light_paths,
        OUT_DIR / "preview-batch5.png",
        LABELS,
        "Stem & Mud  ·  batch 5  ·  plates 21–25  ·  5000×5500 px PNG",
        "Dark-ink colorway for light garments  ·  transparent ground on a checkerboard  ·  drafts, not uploaded",
        cols=5,
        mode="check",
    )
    make_preview(
        dark_paths,
        OUT_DIR / "preview-batch5-dark.png",
        LABELS,
        "Stem & Mud  ·  batch 5  ·  light-ink colorway for dark garments  ·  plates 21–25",
        "Ivory / pale moss / pale clay / pale slate on a dark ground  ·  transparent masters  ·  drafts, not uploaded",
        cols=5,
        mode="dark",
    )


if __name__ == "__main__":
    r.OUT_DIR.mkdir(parents=True, exist_ok=True)
    r.SVG_DIR.mkdir(parents=True, exist_ok=True)
    main()
