#!/usr/bin/env python3
"""Original typographic + line-art designs for a solitary-bee habitat POD series.

All typography uses SIL Open Font License fonts vendored in ../fonts.
Illustrations are drawn procedurally (no stock, clip art, or AI images).
Output: 5000 x 5500 px RGBA PNG with transparent background.
"""
from __future__ import annotations

import math
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont, ImageFilter

ROOT = Path(__file__).resolve().parent.parent
FONT_DIR = ROOT / "fonts"
OUT_DIR = ROOT / "output"

# Print-ready master size in pixels.
W, H = 5000, 5500

# Print-safer near-primaries (not neon RGB-only). Designed as dark ink on light garments.
INK = (28, 32, 26, 255)
MOSS = (55, 82, 62, 255)
CLAY = (166, 96, 52, 255)
DUSK = (64, 88, 106, 255)
RULE = (28, 32, 26, 255)

# Light-ink palette for dark garments (ivory / pale moss / pale clay / pale slate).
INK_LIGHT = (240, 232, 214, 255)
MOSS_LIGHT = (176, 204, 178, 255)
CLAY_LIGHT = (224, 176, 136, 255)
DUSK_LIGHT = (170, 196, 214, 255)


def apply_palette(*, light_ink: bool = False) -> None:
    """Swap working colors. Call before rendering a batch. Body references
    read these globals at call time; default-arg colors are resolved in-function."""
    global INK, MOSS, CLAY, DUSK, RULE
    if light_ink:
        INK, MOSS, CLAY, DUSK = INK_LIGHT, MOSS_LIGHT, CLAY_LIGHT, DUSK_LIGHT
    else:
        INK, MOSS, CLAY, DUSK = (28, 32, 26, 255), (55, 82, 62, 255), (166, 96, 52, 255), (64, 88, 106, 255)
    RULE = INK


def font(name: str, size: int) -> ImageFont.FreeTypeFont:
    return ImageFont.truetype(str(FONT_DIR / name), size=size)


F_DISP = "Newsreader-DisplayBold.ttf"
F_DISP_XB = "Newsreader-DisplayExtraBold.ttf"
F_DISP_IT = "Newsreader-DisplayItalic.ttf"
F_DISP_BIT = "Newsreader-DisplayBoldItalic.ttf"
F_TEXT = "Newsreader-TextSemibold.ttf"
F_MONO = "IBMPlexMono-Medium.ttf"
F_MONO_B = "IBMPlexMono-Bold.ttf"
F_SANS = "IBMPlexSans-Medium.ttf"


def new_canvas() -> Image.Image:
    return Image.new("RGBA", (W, H), (0, 0, 0, 0))


def text_size(draw: ImageDraw.ImageDraw, text: str, fnt: ImageFont.FreeTypeFont) -> tuple[int, int]:
    b = draw.textbbox((0, 0), text, font=fnt)
    return b[2] - b[0], b[3] - b[1]


def draw_centered(draw: ImageDraw.ImageDraw, y: int, text: str, fnt: ImageFont.FreeTypeFont, fill=None, anchor_y="top") -> int:
    if fill is None:
        fill = INK
    w, h = text_size(draw, text, fnt)
    x = (W - w) // 2
    if anchor_y == "mid":
        draw.text((x, y - h // 2), text, font=fnt, fill=fill)
        return y + h // 2
    draw.text((x, y), text, font=fnt, fill=fill)
    return y + h


def draw_tracked(draw: ImageDraw.ImageDraw, cx: int, y: int, text: str, fnt: ImageFont.FreeTypeFont, tracking: int, fill=None) -> int:
    """Draw a centered string with added letter-spacing (px)."""
    if fill is None:
        fill = INK
    widths = [text_size(draw, ch if ch != " " else "A", fnt)[0] if ch != " " else int(text_size(draw, "A", fnt)[0] * 0.45) for ch in text]
    # For spaces use a fraction of A; for others use the char width. Recompute properly:
    widths = []
    for ch in text:
        if ch == " ":
            widths.append(int(text_size(draw, "I", fnt)[0] * 0.7))
        else:
            widths.append(text_size(draw, ch, fnt)[0])
    total = sum(widths) + tracking * (len(text) - 1)
    x = cx - total // 2
    h = 0
    for ch, ww in zip(text, widths):
        if ch != " ":
            draw.text((x, y), ch, font=fnt, fill=fill)
            h = max(h, text_size(draw, ch, fnt)[1])
        x += ww + tracking
    return y + h


def hrule(draw: ImageDraw.ImageDraw, y: int, width: int = 2800, thickness: int = 6, fill=None) -> None:
    if fill is None:
        fill = INK
    x0 = (W - width) // 2
    draw.rectangle([x0, y, x0 + width, y + thickness], fill=fill)


def plate_header(draw: ImageDraw.ImageDraw, plate: str, topic: str, y: int = 620) -> int:
    label = f"{plate}    ·    {topic}"
    y = draw_tracked(draw, W // 2, y, label, font(F_MONO, 64), tracking=10, fill=INK)
    hrule(draw, y + 70, 3000, 5)
    return y + 140


def plate_footer(draw: ImageDraw.ImageDraw, caption: str, y: int = 4980) -> None:
    hrule(draw, y - 90, 3000, 5)
    draw_tracked(draw, W // 2, y, caption, font(F_MONO, 52), tracking=8, fill=INK)


# ---------------------------------------------------------------------------
# Original line illustrations (procedural, not copied from any source image)
# ---------------------------------------------------------------------------


def _tilted_ellipse(d, cx_, cy_, rw, rh, angle_deg, fill, width):
    pts = []
    a = math.radians(angle_deg)
    for i in range(60):
        t = 2 * math.pi * i / 60
        x = rw * math.cos(t)
        y = rh * math.sin(t)
        xr = x * math.cos(a) - y * math.sin(a)
        yr = x * math.sin(a) + y * math.cos(a)
        pts.append((cx_ + xr, cy_ + yr))
    d.line(pts + [pts[0]], fill=fill, width=width, joint="curve")
    d.line(
        [
            (cx_ - rw * 0.35 * math.cos(a), cy_ - rw * 0.35 * math.sin(a)),
            (cx_ + rw * 0.72 * math.cos(a), cy_ + rw * 0.72 * math.sin(a)),
        ],
        fill=fill,
        width=max(3, width // 2),
    )


def draw_bee_side(d: ImageDraw.ImageDraw, cx: int, cy: int, scale: float, body=None, wing=None) -> None:
    """Original stylized solitary-bee profile (not a cartoon honeybee). Facing right."""
    if body is None:
        body = INK
    if wing is None:
        wing = DUSK
    s = scale
    # abdomen (elongated, banded)
    d.ellipse([cx + int(20 * s), cy - int(42 * s), cx + int(185 * s), cy + int(46 * s)], outline=body, width=int(9 * s))
    for off in (48, 82, 116):
        x = cx + int(off * s)
        d.arc([x - int(16 * s), cy - int(36 * s), x + int(16 * s), cy + int(40 * s)], 250, 110, fill=body, width=int(6 * s))
    # thorax
    d.ellipse([cx - int(62 * s), cy - int(54 * s), cx + int(52 * s), cy + int(54 * s)], outline=body, width=int(9 * s))
    # head
    d.ellipse([cx - int(122 * s), cy - int(36 * s), cx - int(42 * s), cy + int(34 * s)], outline=body, width=int(9 * s))
    # antennae
    d.arc([cx - int(180 * s), cy - int(100 * s), cx - int(70 * s), cy - int(8 * s)], 200, 345, fill=body, width=int(6 * s))
    d.arc([cx - int(168 * s), cy - int(78 * s), cx - int(58 * s), cy + int(8 * s)], 200, 355, fill=body, width=int(6 * s))
    # wings
    _tilted_ellipse(d, cx + int(20 * s), cy - int(110 * s), int(150 * s), int(42 * s), -32, wing, int(6 * s))
    _tilted_ellipse(d, cx + int(-4 * s), cy - int(86 * s), int(128 * s), int(34 * s), -20, wing, int(5 * s))
    # legs
    for ox, ang in ((-8, 68), (16, 92), (44, 114)):
        x1 = cx + int(ox * s)
        y1 = cy + int(46 * s)
        x2 = x1 + int(48 * s * math.cos(math.radians(ang)))
        y2 = y1 + int(62 * s * math.sin(math.radians(ang)))
        d.line([(x1, y1), (x2, y2), (x2 + int(22 * s), y2 + int(10 * s))], fill=body, width=int(6 * s), joint="curve")


def draw_stem_nest(base: Image.Image, cx: int, top: int, height: int) -> None:
    """Cross-section of a hollow plant stem with mud-partitioned nest cells."""
    overlay = Image.new("RGBA", base.size, (0, 0, 0, 0))
    d = ImageDraw.Draw(overlay)
    # Scale from a reference height of 2000 px
    s = height / 2000
    x0 = int(cx - 230 * s)
    x1 = int(cx + 230 * s)
    y0 = top
    y1 = top + height
    wall = int(36 * s)
    d.rounded_rectangle([x0, y0, x1, y1], radius=int(90 * s), outline=INK, width=int(14 * s))
    d.rounded_rectangle(
        [x0 + wall, y0 + int(50 * s), x1 - wall, y1 - int(40 * s)],
        radius=int(60 * s),
        outline=MOSS,
        width=int(8 * s),
    )
    cavity_top = y0 + int(110 * s)
    cavity_bot = y1 - int(110 * s)
    for i in range(3):
        py = int(cavity_top + (i + 1) * (cavity_bot - cavity_top) / 4)
        pts = []
        steps = 20
        for k in range(steps + 1):
            t = k / steps
            x = x0 + wall + int(20 * s) + t * (x1 - x0 - 2 * wall - int(40 * s))
            bump = int(22 * s * math.sin(math.pi * t))
            pts.append((x, py + (bump if i % 2 == 0 else -bump)))
        d.line(pts, fill=CLAY, width=int(18 * s), joint="curve")
        d.line([(x, y + int(18 * s)) for x, y in pts], fill=CLAY, width=int(7 * s), joint="curve")
    # nodes / a small leaf at the upper side, so it reads as a plant stem
    mid_y = y0 + int(80 * s)
    d.ellipse([x1 - int(8 * s), mid_y - int(18 * s), x1 + int(28 * s), mid_y + int(18 * s)], outline=MOSS, width=int(7 * s))
    leaf = []
    for k in range(24):
        t = k / 23
        lx = x1 + int(20 * s) + t * int(260 * s)
        ly = mid_y - int(70 * s * math.sin(math.pi * t))
        leaf.append((lx, ly))
    for k in range(23, -1, -1):
        t = k / 23
        lx = x1 + int(20 * s) + t * int(260 * s)
        ly = mid_y + int(70 * s * math.sin(math.pi * t))
        leaf.append((lx, ly))
    d.line(leaf + [leaf[0]], fill=MOSS, width=int(8 * s), joint="curve")
    d.line(
        [(x1 + int(20 * s), mid_y), (x1 + int(270 * s), mid_y)],
        fill=MOSS,
        width=int(5 * s),
    )
    # entrance ticks and a clearly visible bee
    d.line([(x0 - int(110 * s), y1), (x0 - int(16 * s), y1)], fill=INK, width=int(7 * s))
    d.line([(x1 + int(16 * s), y1), (x1 + int(110 * s), y1)], fill=INK, width=int(7 * s))
    draw_bee_side(d, cx + int(40 * s), y1 + int(150 * s), scale=0.95 * s, body=INK, wing=DUSK)
    base.alpha_composite(overlay)


def draw_mud_tube(base: Image.Image, cx: int, top: int, length: int) -> None:
    """Horizontal nest tube with mud partitions — masonry, not honeycomb."""
    overlay = Image.new("RGBA", base.size, (0, 0, 0, 0))
    d = ImageDraw.Draw(overlay)
    s = length / 2800
    height = int(340 * s)
    x0 = cx - length // 2
    x1 = cx + length // 2 - int(420 * s)  # leave room for the bee on the right
    y0 = top
    y1 = top + height
    # capsule body
    d.rounded_rectangle([x0, y0, x1, y1], radius=height // 2, outline=INK, width=int(14 * s))
    # mud partitions
    inner_left = x0 + height // 2
    inner_right = x1 - height // 2
    for i in range(1, 5):
        px = int(inner_left + i * (inner_right - inner_left) / 5)
        pts = []
        for k in range(24):
            t = k / 23
            y = y0 + int(22 * s) + t * (height - int(44 * s))
            x = px + int(16 * s * math.sin(math.pi * t))
            pts.append((x, y))
        d.line(pts, fill=CLAY, width=int(18 * s), joint="curve")
    lip_x = x1
    # dotted flight and bee
    midy = (y0 + y1) // 2
    for i in range(7):
        px = lip_x + int(24 * s) + i * int(36 * s)
        d.ellipse([px, midy - 7, px + 14, midy + 7], fill=MOSS)
    draw_bee_side(d, lip_x + int(420 * s), midy, scale=1.05 * s, body=INK, wing=DUSK)
    base.alpha_composite(overlay)


def draw_commute(base: Image.Image, cx: int, top: int, width: int, height: int) -> None:
    overlay = Image.new("RGBA", base.size, (0, 0, 0, 0))
    d = ImageDraw.Draw(overlay)
    x0, x1 = cx - width // 2, cx + width // 2
    pts = []
    for i in range(120):
        t = i / 119
        x = x0 + t * (x1 - x0)
        y = top + height // 2 + int((height * 0.28) * math.sin(math.pi * t))
        pts.append((x, y))
    for i in range(0, len(pts) - 1, 2):
        if (i // 2) % 3 != 2:
            d.line([pts[i], pts[min(i + 2, len(pts) - 1)]], fill=MOSS, width=12, joint="curve")
    bx, by = pts[72]
    draw_bee_side(d, bx, by - 8, scale=1.55, body=INK, wing=DUSK)
    base.alpha_composite(overlay)


def draw_blossom_and_osmia(base: Image.Image, cx: int, top: int, size: int) -> None:
    overlay = Image.new("RGBA", base.size, (0, 0, 0, 0))
    d = ImageDraw.Draw(overlay)
    s = size / 900
    bx, by = cx - int(380 * s), top + int(420 * s)
    # Five teardrop petals arranged around a center (original, not a logo)
    petal_len = int(340 * s)
    petal_w = int(150 * s)
    for i in range(5):
        ang = math.radians(-90 + i * 72)
        # petal tip
        tip_x = bx + math.cos(ang) * petal_len
        tip_y = by + math.sin(ang) * petal_len
        # two side control directions perpendicular to angle
        px, py = -math.sin(ang), math.cos(ang)
        pts = []
        # rounded teardrop via two half-ellipses in polar-ish points
        for k in range(32):
            t = k / 31  # 0 at base, 1 at tip
            # width envelope
            env = math.sin(math.pi * t)
            along = t * petal_len
            # start slightly out from center so petals meet cleanly
            along = int(40 * s) + t * (petal_len - int(40 * s))
            x = bx + math.cos(ang) * along + px * env * petal_w
            y = by + math.sin(ang) * along + py * env * petal_w
            pts.append((x, y))
        for k in range(31, -1, -1):
            t = k / 31
            env = math.sin(math.pi * t)
            along = int(40 * s) + t * (petal_len - int(40 * s))
            x = bx + math.cos(ang) * along - px * env * petal_w
            y = by + math.sin(ang) * along - py * env * petal_w
            pts.append((x, y))
        d.line(pts + [pts[0]], fill=CLAY, width=int(10 * s), joint="curve")
        # midrib
        d.line(
            [(bx + math.cos(ang) * 50 * s, by + math.sin(ang) * 50 * s), (tip_x, tip_y)],
            fill=CLAY,
            width=int(4 * s),
        )
    d.ellipse([bx - int(78 * s), by - int(78 * s), bx + int(78 * s), by + int(78 * s)], outline=CLAY, width=int(9 * s))
    d.ellipse([bx - int(28 * s), by - int(28 * s), bx + int(28 * s), by + int(28 * s)], outline=CLAY, width=int(7 * s))
    for i in range(8):
        ang = math.radians(i * 45)
        x2 = bx + math.cos(ang) * 70 * s
        y2 = by + math.sin(ang) * 70 * s
        d.line([(bx, by), (x2, y2)], fill=CLAY, width=int(4 * s))
        d.ellipse([x2 - 7 * s, y2 - 7 * s, x2 + 7 * s, y2 + 7 * s], fill=CLAY)
    draw_bee_side(d, cx + int(620 * s), top + int(430 * s), scale=1.55 * s, body=DUSK, wing=MOSS)
    base.alpha_composite(overlay)


def draw_gauge(base: Image.Image, cx: int, top: int, diameter: int) -> None:
    """Entrance hole with a complete dimension line across the diameter."""
    overlay = Image.new("RGBA", base.size, (0, 0, 0, 0))
    d = ImageDraw.Draw(overlay)
    r = diameter // 2
    cy = top + r
    d.ellipse([cx - r, cy - r, cx + r, cy + r], outline=INK, width=16)
    d.ellipse([cx - r + 48, cy - r + 48, cx + r - 48, cy + r - 48], outline=MOSS, width=8)
    # full diameter dimension, slightly below center so it does not cut the hole in half optically
    dy = cy
    # ticks outside the rim
    ext = 70
    d.line([(cx - r, cy - ext), (cx - r, cy + ext)], fill=CLAY, width=10)
    d.line([(cx + r, cy - ext), (cx + r, cy + ext)], fill=CLAY, width=10)
    # arrows just inside the rim, leaving a short gap for the numeral
    gap = 210
    d.line([(cx - r + 8, dy), (cx - gap, dy)], fill=CLAY, width=10)
    d.line([(cx + gap, dy), (cx + r - 8, dy)], fill=CLAY, width=10)
    for sign in (-1, 1):
        tip_x = cx + sign * (r - 8)
        d.polygon(
            [(tip_x, dy), (tip_x - sign * 48, dy - 26), (tip_x - sign * 48, dy + 26)],
            fill=CLAY,
        )
    # numeral in the gap, drawn later on the base? do it here
    fnt = font(F_MONO_B, 72)
    label = "8 mm"
    # measure against overlay
    tmp = ImageDraw.Draw(overlay)
    tw, th = text_size(tmp, label, fnt)
    tmp.text((cx - tw // 2, dy - th // 2 - 8), label, font=fnt, fill=CLAY)
    # bee to the lower right, clearly part of the composition
    draw_bee_side(d, cx + r + 360, cy + int(r * 0.55), scale=1.15, body=INK, wing=DUSK)
    base.alpha_composite(overlay)
    return cy + r


# ---------------------------------------------------------------------------
# Five designs
# ---------------------------------------------------------------------------

def design_01() -> Image.Image:
    im = new_canvas()
    d = ImageDraw.Draw(im)
    hy = plate_header(d, "PLATE 01", "STEM NEST")
    y = hy + 80
    y = draw_centered(d, y, "Hollow stems.", font(F_DISP_XB, 300), INK) + 8
    y = draw_centered(d, y, "Please wait.", font(F_DISP_IT, 280), MOSS)
    # Art in the remaining band above the footer
    band_top = y + 120
    band_bot = 4780
    stem_h = min(2000, band_bot - band_top - 260)
    stem_top = band_top
    draw_stem_nest(im, W // 2, stem_top, stem_h)
    plate_footer(d, "CUT NOTHING UNTIL THEY EMERGE")
    return im


def design_02() -> Image.Image:
    im = new_canvas()
    d = ImageDraw.Draw(im)
    hy = plate_header(d, "PLATE 02", "MASONRY")
    y = hy + 120
    y = draw_centered(d, y, "Mud walls,", font(F_DISP_XB, 320), INK) + 16
    y = draw_centered(d, y, "no honey.", font(F_DISP_IT, 320), CLAY)
    band_top = y + 200
    band_bot = 4780
    mid = (band_top + band_bot) // 2
    tube_h = 360
    draw_mud_tube(im, W // 2, mid - tube_h // 2, length=3000)
    plate_footer(d, "A LINEAR NEST, NOT A HIVE")
    return im


def design_03() -> Image.Image:
    im = new_canvas()
    d = ImageDraw.Draw(im)
    hy = plate_header(d, "PLATE 03", "SOLITARY TRANSIT")
    y = hy + 120
    y = draw_centered(d, y, "Most bees", font(F_DISP_XB, 340), INK) + 8
    y = draw_centered(d, y, "commute alone.", font(F_DISP_IT, 280), MOSS)
    band_top = y + 80
    band_bot = 4780
    h = min(1100, band_bot - band_top)
    top = band_top + max(0, (band_bot - band_top - h) // 2)
    draw_commute(im, W // 2, top, width=3600, height=h)
    plate_footer(d, "A NOTE ON SOLITARY SPECIES")
    return im


def design_04() -> Image.Image:
    im = new_canvas()
    d = ImageDraw.Draw(im)
    hy = plate_header(d, "PLATE 04", "EARLY SPRING")
    y = hy + 80
    y = draw_centered(d, y, "Osmia,", font(F_DISP_XB, 360), DUSK) + 4
    y = draw_centered(d, y, "opening shift.", font(F_DISP_IT, 280), INK)
    band_top = y + 80
    band_bot = 4780
    size = min(1250, band_bot - band_top - 20)
    top = band_top + 40
    draw_blossom_and_osmia(im, W // 2, top, size=size)
    plate_footer(d, "GENUS OSMIA  ·  ORCHARD BLOOM")
    return im


def design_05() -> Image.Image:
    im = new_canvas()
    d = ImageDraw.Draw(im)
    hy = plate_header(d, "PLATE 05", "ENTRANCE GAUGE")
    y = hy + 40
    y = draw_centered(d, y, "8 mm", font(F_DISP_XB, 480), INK)
    y = draw_centered(d, y + 4, "please.", font(F_DISP_IT, 260), CLAY)
    band_top = y + 80
    band_bot = 4780
    diameter = min(1400, band_bot - band_top - 200)
    top = band_top + max(0, (band_bot - band_top - diameter - 120) // 2)
    draw_gauge(im, W // 2, top, diameter=diameter)
    plate_footer(d, "PREFERRED HOLE  ·  ORCHARD MASON BEE")
    return im



def draw_egg_rooms(base: Image.Image, cx: int, top: int, length: int) -> None:
    """Linear nest of single-egg chambers separated by mud walls."""
    overlay = Image.new("RGBA", base.size, (0, 0, 0, 0))
    d = ImageDraw.Draw(overlay)
    s = length / 3000
    height = int(420 * s)
    x0 = cx - length // 2
    x1 = cx + length // 2
    y0, y1 = top, top + height
    d.rounded_rectangle([x0, y0, x1, y1], radius=height // 2, outline=INK, width=int(14 * s))
    inner_l = x0 + height // 2
    inner_r = x1 - height // 2
    rooms = 5
    # partition positions between rooms
    edges = [int(inner_l + i * (inner_r - inner_l) / rooms) for i in range(rooms + 1)]
    for i, px in enumerate(edges[1:-1], start=1):
        pts = []
        for k in range(24):
            t = k / 23
            y = y0 + int(24 * s) + t * (height - int(48 * s))
            x = px + int(14 * s * math.sin(math.pi * t))
            pts.append((x, y))
        d.line(pts, fill=CLAY, width=int(16 * s), joint="curve")
    # one slightly tilted rice-grain egg on a low, wide pollen loaf
    midy = (y0 + y1) // 2
    for i in range(rooms):
        rx0, rx1 = edges[i], edges[i + 1]
        rcx = (rx0 + rx1) // 2
        d.ellipse(
            [rcx - int(58 * s), midy + int(28 * s), rcx + int(58 * s), midy + int(72 * s)],
            outline=MOSS,
            width=int(6 * s),
        )
        # elongated egg, almost horizontal, resting on the loaf
        ew, eh = int(44 * s), int(20 * s)
        # simple 2-point tilt via a short oval plus a second slightly offset stroke
        d.ellipse(
            [rcx - ew, midy - eh + int(8 * s), rcx + ew, midy + eh + int(8 * s)],
            outline=INK,
            width=int(7 * s),
        )
    base.alpha_composite(overlay)


def draw_neighbor_tubes(base: Image.Image, cx: int, top: int, width: int, height: int) -> None:
    """Several independent nest tubes standing side by side — neighbors, not a hive."""
    overlay = Image.new("RGBA", base.size, (0, 0, 0, 0))
    d = ImageDraw.Draw(overlay)
    n = 4
    gap = int(width * 0.10)
    tube_w = int((width - gap * (n - 1)) / n)
    heights = [int(height * r) for r in (0.86, 1.0, 0.78, 0.92)]
    ground = top + height
    d.line([(cx - width // 2 - 40, ground + 20), (cx + width // 2 + 40, ground + 20)], fill=INK, width=8)
    left = cx - width // 2
    tube_boxes = []
    for i in range(n):
        tw = tube_w
        th = heights[i]
        x0 = left + i * (tube_w + gap)
        x1 = x0 + tw
        y1 = ground
        y0 = y1 - th
        tube_boxes.append((x0, y0, x1, y1, tw))
        rad = min(tw // 2, 80)
        d.rounded_rectangle([x0, y0, x1, y1], radius=rad, outline=INK, width=10)
        # mud cap across the open top
        d.arc([x0 + 8, y0 - 6, x1 - 8, y0 + int(tw * 0.55)], 200, 340, fill=CLAY, width=14)
        mid = (y0 + y1) // 2
        d.line([(x0 + 16, mid), (x1 - 16, mid + 8)], fill=CLAY, width=7)
    # bee approaching the first tube from the left (facing right), clear of the title
    x0, y0, x1, y1, tw = tube_boxes[0]
    draw_bee_side(d, x0 - 300, y0 + 90, scale=0.88, body=INK, wing=DUSK)
    base.alpha_composite(overlay)


def draw_scopa_bee(base: Image.Image, cx: int, cy: int, scale: float = 2.2) -> None:
    """Large profile bee with a stippled pollen load on the underside of the abdomen."""
    overlay = Image.new("RGBA", base.size, (0, 0, 0, 0))
    d = ImageDraw.Draw(overlay)
    draw_bee_side(d, cx, cy, scale=scale, body=INK, wing=DUSK)
    s = scale
    # scopa: dense short strokes hanging from the ventral abdomen
    for i in range(14):
        t = i / 13
        x = cx + int((40 + t * 130) * s)
        y = cy + int(44 * s)
        # slightly curved downward hairs / pollen grains
        d.line([(x, y), (x + int(6 * s), y + int((28 + (i % 3) * 8) * s))], fill=CLAY, width=max(3, int(4 * s)))
        d.ellipse(
            [x + int(2 * s), y + int(24 * s), x + int(12 * s), y + int(36 * s)],
            outline=CLAY,
            width=max(2, int(3 * s)),
        )
    base.alpha_composite(overlay)


def draw_depth_tube(base: Image.Image, cx: int, top: int, length: int) -> None:
    """Nest tube with a 6-inch / 15 cm overall length and a 3-inch entrance zone."""
    overlay = Image.new("RGBA", base.size, (0, 0, 0, 0))
    d = ImageDraw.Draw(overlay)
    s = length / 3200
    height = int(300 * s)
    x0 = cx - length // 2
    x1 = cx + length // 2
    y0, y1 = top, top + height
    d.rounded_rectangle([x0, y0, x1, y1], radius=height // 2, outline=INK, width=int(14 * s))
    # tick at mid-length = 3 inches from the open (right) end
    mid = (x0 + x1) // 2
    d.line([(mid, y0 - int(20 * s)), (mid, y1 + int(20 * s))], fill=MOSS, width=int(6 * s))
    # labels inside the two halves
    fnt = font(F_MONO, max(36, int(48 * s)))
    for label, lx in (("DAUGHTERS", (x0 + mid) // 2), ("SONS", (mid + x1) // 2)):
        tw, th = text_size(d, label, fnt)
        d.text((lx - tw // 2, (y0 + y1) // 2 - th // 2), label, font=fnt, fill=MOSS)
    # overall dimension line below
    dy = y1 + int(140 * s)
    d.line([(x0, dy), (x1, dy)], fill=CLAY, width=int(8 * s))
    d.line([(x0, dy - 40), (x0, dy + 40)], fill=CLAY, width=int(8 * s))
    d.line([(x1, dy - 40), (x1, dy + 40)], fill=CLAY, width=int(8 * s))
    for sign, tip in ((1, x0), (-1, x1)):
        d.polygon([(tip, dy), (tip + sign * 40, dy - 20), (tip + sign * 40, dy + 20)], fill=CLAY)
    cap = "6 in   ·   about 15 cm"
    f2 = font(F_MONO_B, max(40, int(56 * s)))
    tw, th = text_size(d, cap, f2)
    # knock out a gap by not drawing text over the line is fine; just place text above the line
    d.text(((x0 + x1) // 2 - tw // 2, dy - th - 20), cap, font=f2, fill=CLAY)
    # a bee at the open right end
    draw_bee_side(d, x1 + int(280 * s), (y0 + y1) // 2, scale=0.9 * s, body=INK, wing=DUSK)
    base.alpha_composite(overlay)


def draw_sealed_tube(base: Image.Image, cx: int, top: int, length: int) -> None:
    """A completed, mud-capped nest tube: do not open until spring."""
    overlay = Image.new("RGBA", base.size, (0, 0, 0, 0))
    d = ImageDraw.Draw(overlay)
    s = length / 2800
    height = int(340 * s)
    x0 = cx - length // 2
    x1 = cx + length // 2
    y0, y1 = top, top + height
    d.rounded_rectangle([x0, y0, x1, y1], radius=height // 2, outline=INK, width=int(14 * s))
    # three elongated cocoons, closed in for winter
    midy = (y0 + y1) // 2
    for ox in (-0.30, -0.02, 0.26):
        cx_ = cx + int(ox * length)
        d.ellipse(
            [cx_ - int(110 * s), midy - int(58 * s), cx_ + int(110 * s), midy + int(58 * s)],
            outline=MOSS,
            width=int(7 * s),
        )
        d.ellipse(
            [cx_ - int(70 * s), midy - int(32 * s), cx_ + int(70 * s), midy + int(32 * s)],
            outline=MOSS,
            width=int(4 * s),
        )
    # thick mud plug sealing the right-hand entrance
    cap_w = int(90 * s)
    d.arc([x1 - cap_w * 2, y0 + 6, x1 + 6, y1 - 6], 270, 90, fill=CLAY, width=int(22 * s))
    d.arc([x1 - cap_w * 2 + int(18 * s), y0 + 18, x1 - 8, y1 - 18], 280, 80, fill=CLAY, width=int(12 * s))
    # a short clay lip continuing slightly past the rim
    d.line([(x1 - int(8 * s), y0 + int(40 * s)), (x1 - int(8 * s), y1 - int(40 * s))], fill=CLAY, width=int(10 * s))
    base.alpha_composite(overlay)


def design_06() -> Image.Image:
    im = new_canvas()
    d = ImageDraw.Draw(im)
    hy = plate_header(d, "PLATE 06", "NEST CELLS")
    y = hy + 100
    y = draw_centered(d, y, "One egg", font(F_DISP_XB, 340), INK) + 8
    y = draw_centered(d, y, "per room.", font(F_DISP_IT, 300), CLAY)
    band_top = y + 220
    band_bot = 4780
    mid = (band_top + band_bot) // 2
    draw_egg_rooms(im, W // 2, mid - 210, length=3200)
    plate_footer(d, "A SINGLE CHAMBER, A SINGLE EGG")
    return im


def design_07() -> Image.Image:
    im = new_canvas()
    d = ImageDraw.Draw(im)
    hy = plate_header(d, "PLATE 07", "GREGARIOUS")
    y = hy + 80
    y = draw_centered(d, y, "Neighbors,", font(F_DISP_XB, 320), INK) + 8
    y = draw_centered(d, y, "not a colony.", font(F_DISP_IT, 280), MOSS)
    band_top = y + 220
    band_bot = 4780
    h = min(1200, band_bot - band_top - 120)
    top = band_top + 40
    draw_neighbor_tubes(im, W // 2, top, width=2200, height=h)
    plate_footer(d, "SIDE BY SIDE, EACH HER OWN NEST")
    return im


def design_08() -> Image.Image:
    im = new_canvas()
    d = ImageDraw.Draw(im)
    hy = plate_header(d, "PLATE 08", "SCOPA")
    y = hy + 80
    y = draw_centered(d, y, "Pollen on", font(F_DISP_XB, 340), INK) + 8
    y = draw_centered(d, y, "the underside.", font(F_DISP_IT, 280), CLAY)
    band_top = y + 80
    band_bot = 4780
    cy = (band_top + band_bot) // 2
    draw_scopa_bee(im, W // 2 - 60, cy + 40, scale=2.7)
    plate_footer(d, "ABDOMINAL SCOPA  ·  NOT A POLLEN BASKET")
    return im


def design_09() -> Image.Image:
    im = new_canvas()
    d = ImageDraw.Draw(im)
    hy = plate_header(d, "PLATE 09", "HOLE DEPTH")
    y = hy + 60
    y = draw_centered(d, y, "Six inches,", font(F_DISP_XB, 300), INK) + 8
    y = draw_centered(d, y, "or mostly sons.", font(F_DISP_IT, 260), MOSS)
    band_top = y + 200
    band_bot = 4780
    mid = (band_top + band_bot) // 2
    draw_depth_tube(im, W // 2 - 80, mid - 200, length=3000)
    plate_footer(d, "DEEPER TUBES, MORE DAUGHTERS")
    return im


def design_10() -> Image.Image:
    im = new_canvas()
    d = ImageDraw.Draw(im)
    hy = plate_header(d, "PLATE 10", "OVERWINTER")
    y = hy + 80
    y = draw_centered(d, y, "Unopened", font(F_DISP_XB, 340), INK) + 8
    y = draw_centered(d, y, "until spring.", font(F_DISP_IT, 300), DUSK)
    band_top = y + 240
    band_bot = 4780
    mid = (band_top + band_bot) // 2
    draw_sealed_tube(im, W // 2, mid - 180, length=3000)
    plate_footer(d, "COCOONS STAY IN THE TUBE")
    return im


def checkerboard(size: tuple[int, int], cell: int = 48) -> Image.Image:
    im = Image.new("RGBA", size, (235, 232, 224, 255))
    d = ImageDraw.Draw(im)
    c2 = (214, 210, 200, 255)
    w, h = size
    for y in range(0, h, cell):
        for x in range(0, w, cell):
            if ((x // cell) + (y // cell)) % 2 == 0:
                d.rectangle([x, y, x + cell, y + cell], fill=c2)
    return im



def draw_emergence(base: Image.Image, cx: int, top: int, length: int) -> None:
    """A nest tube with a smaller male already out and a larger bee still at the entrance."""
    overlay = Image.new("RGBA", base.size, (0, 0, 0, 0))
    d = ImageDraw.Draw(overlay)
    s = length / 2800
    height = int(300 * s)
    x0 = cx - length // 2
    x1 = cx + length // 2 - int(700 * s)
    y0, y1 = top, top + height
    d.rounded_rectangle([x0, y0, x1, y1], radius=height // 2, outline=INK, width=int(14 * s))
    # closed back
    d.pieslice([x0, y0, x0 + height, y1], 90, 270, outline=INK, width=int(8 * s))
    midy = (y0 + y1) // 2
    # female still in the mouth of the tube (larger)
    draw_bee_side(d, x1 - int(40 * s), midy, scale=0.72 * s, body=INK, wing=DUSK)
    # male already out, slightly ahead and smaller
    draw_bee_side(d, x1 + int(520 * s), midy - int(40 * s), scale=0.58 * s, body=MOSS, wing=DUSK)
    # dotted path between them
    for i in range(5):
        px = x1 + int(140 * s) + i * int(36 * s)
        d.ellipse([px, midy - 6, px + 12, midy + 6], fill=CLAY)
    base.alpha_composite(overlay)


def draw_clay_not_sand(base: Image.Image, cx: int, top: int, width: int) -> None:
    """Two specimen piles: a cohesive clay clod versus loose sand grains."""
    overlay = Image.new("RGBA", base.size, (0, 0, 0, 0))
    d = ImageDraw.Draw(overlay)
    s = width / 2800
    # left: clay clod — one solid, moldable mass
    lx, ly = cx - int(620 * s), top + int(220 * s)
    d.ellipse([lx - int(230 * s), ly - int(170 * s), lx + int(240 * s), ly + int(190 * s)], outline=CLAY, width=int(12 * s))
    # irregular surface marks — avoid a face-like arrangement
    d.arc([lx - int(180 * s), ly - int(120 * s), lx - int(20 * s), ly + int(20 * s)], 200, 320, fill=CLAY, width=int(7 * s))
    d.arc([lx + int(20 * s), ly - int(10 * s), lx + int(200 * s), ly + int(140 * s)], 40, 150, fill=CLAY, width=int(7 * s))
    d.line([(lx - int(40 * s), ly + int(40 * s)), (lx + int(80 * s), ly + int(10 * s))], fill=CLAY, width=int(6 * s))
    fnt = font(F_MONO_B, max(40, int(56 * s)))
    tw, th = text_size(d, "CLAY", fnt)
    d.text((lx - tw // 2, ly + int(230 * s)), "CLAY", font=fnt, fill=CLAY)
    # divider
    d.line([(cx, top - 20), (cx, top + int(560 * s))], fill=INK, width=int(6 * s))
    # right: loose sand — many small unconnected grains
    rx, ry = cx + int(620 * s), top + int(220 * s)
    grains = [
        (-180, -80, 36), (-80, -140, 28), (20, -90, 40), (120, -40, 30),
        (-150, 20, 32), (-40, 10, 44), (80, 30, 26), (160, 80, 34),
        (-100, 120, 30), (10, 140, 36), (110, 150, 28), (-200, 90, 24),
        (50, -20, 22), (-20, 80, 20),
    ]
    for ox, oy, r in grains:
        d.ellipse([rx + int(ox * s) - int(r * s), ry + int(oy * s) - int(r * s),
                   rx + int(ox * s) + int(r * s), ry + int(oy * s) + int(r * s)],
                  outline=MOSS, width=int(5 * s))
    tw, th = text_size(d, "SAND", fnt)
    d.text((rx - tw // 2, ry + int(230 * s)), "SAND", font=fnt, fill=MOSS)
    base.alpha_composite(overlay)


def draw_one_generation(base: Image.Image, cx: int, top: int, size: int) -> None:
    """A single life-cycle loop: egg, cocoon, adult — once a year."""
    overlay = Image.new("RGBA", base.size, (0, 0, 0, 0))
    d = ImageDraw.Draw(overlay)
    s = size / 1400
    # three stations on a circular path
    r = int(420 * s)
    cy = top + int(480 * s)
    stations = [
        (0, "EGG"),       # right
        (120, "COCOON"),  # lower left
        (240, "ADULT"),   # upper left
    ]
    pts = []
    for ang_deg, label in stations:
        a = math.radians(ang_deg - 90)
        # wait, let's place them at 90, 210, 330 for an even triangle around center
        pass
    # Use 90 (top), 210, 330
    placed = []
    for i, (ang_deg, label) in enumerate(((90, "EGG"), (210, "COCOON"), (330, "ADULT"))):
        a = math.radians(ang_deg)
        px = cx + int(math.cos(a) * r)
        py = cy + int(math.sin(a) * r)
        placed.append((px, py, label))
    # arrows along the circle, between stations
    for i in range(3):
        a0 = math.radians((90 + i * 120) + 25)
        a1 = math.radians((90 + (i + 1) * 120) - 25)
        pts = []
        steps = 16
        for k in range(steps + 1):
            t = k / steps
            a = a0 + (a1 - a0) * t
            pts.append((cx + int(math.cos(a) * r), cy + int(math.sin(a) * r)))
        d.line(pts, fill=MOSS, width=int(8 * s), joint="curve")
        # arrowhead at end of arc
        ang = a1
        tip = (cx + int(math.cos(ang) * r), cy + int(math.sin(ang) * r))
        tx = math.cos(ang + math.pi / 2)
        ty = math.sin(ang + math.pi / 2)
        # forward along the arc
        fx, fy = -math.sin(ang), math.cos(ang)
        # hmm, simpler chevron
        back_x = tip[0] - int(28 * s * math.cos(ang + 0.4))
        # use tangent of the circle (perpendicular to radius, counterclockwise)
        tang = ang + math.pi / 2
        bx = tip[0] - int(34 * s * math.cos(tang))
        by = tip[1] - int(34 * s * math.sin(tang))
        d.polygon([
            tip,
            (bx + int(16 * s * math.cos(ang)), by + int(16 * s * math.sin(ang))),
            (bx - int(16 * s * math.cos(ang)), by - int(16 * s * math.sin(ang))),
        ], fill=MOSS)
    fnt = font(F_MONO, max(32, int(40 * s)))
    # EGG
    px, py, _ = placed[0]
    d.ellipse([px - int(28 * s), py - int(48 * s), px + int(28 * s), py + int(48 * s)], outline=INK, width=int(8 * s))
    tw, th = text_size(d, "EGG", fnt)
    d.text((px - tw // 2, py + int(70 * s)), "EGG", font=fnt, fill=INK)
    # COCOON
    px, py, _ = placed[1]
    d.ellipse([px - int(70 * s), py - int(40 * s), px + int(70 * s), py + int(40 * s)], outline=CLAY, width=int(8 * s))
    d.ellipse([px - int(44 * s), py - int(22 * s), px + int(44 * s), py + int(22 * s)], outline=CLAY, width=int(5 * s))
    tw, th = text_size(d, "COCOON", fnt)
    d.text((px - tw // 2, py + int(64 * s)), "COCOON", font=fnt, fill=CLAY)
    # ADULT — small bee
    px, py, _ = placed[2]
    draw_bee_side(d, px, py, scale=0.55 * s, body=INK, wing=DUSK)
    tw, th = text_size(d, "ADULT", fnt)
    d.text((px - tw // 2, py + int(90 * s)), "ADULT", font=fnt, fill=INK)
    # center word
    f2 = font(F_MONO_B, max(40, int(52 * s)))
    tw, th = text_size(d, "ONCE", f2)
    d.text((cx - tw // 2, cy - th // 2), "ONCE", font=f2, fill=INK)
    base.alpha_composite(overlay)


def draw_ground_nest(base: Image.Image, cx: int, top: int, width: int, height: int) -> None:
    """A soil horizon with a simple underground tunnel and a small entrance hole."""
    overlay = Image.new("RGBA", base.size, (0, 0, 0, 0))
    d = ImageDraw.Draw(overlay)
    s = width / 3000
    ground_y = top + int(280 * s)
    # horizon
    d.line([(cx - width // 2, ground_y), (cx + width // 2, ground_y)], fill=INK, width=int(10 * s))
    # short grass ticks above the line
    for i, ox in enumerate(range(-1200, 1201, 140)):
        x = cx + int(ox * s)
        h = int((40 + (i % 3) * 18) * s)
        d.line([(x, ground_y), (x + int(10 * s), ground_y - h)], fill=MOSS, width=int(5 * s))
    # entrance hole on the horizon
    hole_x = cx - int(200 * s)
    d.ellipse([hole_x - int(36 * s), ground_y - int(16 * s), hole_x + int(36 * s), ground_y + int(16 * s)], outline=INK, width=int(8 * s))
    # tunnel: a bent path downward then sideways, ending in a cell
    pts = []
    path = [
        (hole_x, ground_y + int(10 * s)),
        (hole_x + int(20 * s), ground_y + int(180 * s)),
        (hole_x + int(80 * s), ground_y + int(320 * s)),
        (hole_x + int(260 * s), ground_y + int(400 * s)),
        (hole_x + int(520 * s), ground_y + int(430 * s)),
    ]
    d.line(path, fill=CLAY, width=int(16 * s), joint="curve")
    # terminal cell
    ex, ey = path[-1]
    d.ellipse([ex, ey - int(50 * s), ex + int(140 * s), ey + int(50 * s)], outline=CLAY, width=int(8 * s))
    # bee approaching the entrance from above
    draw_bee_side(d, hole_x + int(280 * s), ground_y - int(140 * s), scale=0.85 * s, body=INK, wing=DUSK)
    base.alpha_composite(overlay)


def draw_closed_back(base: Image.Image, cx: int, top: int, length: int) -> None:
    """A nest tube with a clearly blind back end and an open entrance."""
    overlay = Image.new("RGBA", base.size, (0, 0, 0, 0))
    d = ImageDraw.Draw(overlay)
    s = length / 3000
    height = int(320 * s)
    x0 = cx - length // 2
    x1 = cx + length // 2
    y0, y1 = top, top + height
    d.rounded_rectangle([x0, y0, x1, y1], radius=height // 2, outline=INK, width=int(14 * s))
    # solid filled back (left half-circle plug)
    plug = int(height * 0.92)
    d.pieslice([x0 + 8, y0 + 8, x0 + plug, y1 - 8], 90, 270, outline=CLAY, width=int(16 * s))
    d.arc([x0 + 8, y0 + 8, x0 + plug, y1 - 8], 90, 270, fill=CLAY, width=int(16 * s))
    # a second inner clay stroke to read as a solid cap
    d.line([(x0 + plug // 2, y0 + int(28 * s)), (x0 + plug // 2, y1 - int(28 * s))], fill=CLAY, width=int(14 * s))
    # open entrance ticks on the right
    midy = (y0 + y1) // 2
    d.line([(x1 + int(20 * s), y0), (x1 + int(80 * s), y0)], fill=INK, width=int(6 * s))
    d.line([(x1 + int(20 * s), y1), (x1 + int(80 * s), y1)], fill=INK, width=int(6 * s))
    fnt = font(F_MONO, max(32, int(44 * s)))
    tw, th = text_size(d, "CLOSED", fnt)
    d.text((x0 + int(40 * s), y1 + int(40 * s)), "CLOSED", font=fnt, fill=CLAY)
    tw, th = text_size(d, "OPEN", fnt)
    d.text((x1 - tw - int(20 * s), y1 + int(40 * s)), "OPEN", font=fnt, fill=INK)
    draw_bee_side(d, x1 + int(280 * s), midy, scale=0.8 * s, body=INK, wing=DUSK)
    base.alpha_composite(overlay)


def design_11() -> Image.Image:
    im = new_canvas()
    d = ImageDraw.Draw(im)
    hy = plate_header(d, "PLATE 11", "EMERGENCE")
    y = hy + 60
    y = draw_centered(d, y, "The males", font(F_DISP_XB, 320), INK) + 8
    y = draw_centered(d, y, "come out first.", font(F_DISP_IT, 280), MOSS)
    band_top = y + 200
    band_bot = 4780
    mid = (band_top + band_bot) // 2
    draw_emergence(im, W // 2, mid - 160, length=3000)
    plate_footer(d, "MALES EMERGE, THEN THE FEMALES")
    return im


def design_12() -> Image.Image:
    im = new_canvas()
    d = ImageDraw.Draw(im)
    hy = plate_header(d, "PLATE 12", "MASONRY MUD")
    y = hy + 80
    y = draw_centered(d, y, "Clay,", font(F_DISP_XB, 380), CLAY) + 4
    y = draw_centered(d, y, "not sand.", font(F_DISP_IT, 300), MOSS)
    band_top = y + 80
    draw_clay_not_sand(im, W // 2, band_top + 280, width=2800)
    plate_footer(d, "MOIST CLAY HOLDS THE WALLS")
    return im


def design_13() -> Image.Image:
    im = new_canvas()
    d = ImageDraw.Draw(im)
    hy = plate_header(d, "PLATE 13", "LIFE CYCLE")
    y = hy + 60
    y = draw_centered(d, y, "One generation", font(F_DISP_XB, 280), INK) + 8
    y = draw_centered(d, y, "a year.", font(F_DISP_IT, 300), DUSK)
    band_top = y + 40
    band_bot = 4780
    size = min(1500, band_bot - band_top - 40)
    draw_one_generation(im, W // 2, band_top + 20, size=size)
    plate_footer(d, "A SINGLE COHORT")
    return im


def design_14() -> Image.Image:
    im = new_canvas()
    d = ImageDraw.Draw(im)
    hy = plate_header(d, "PLATE 14", "GROUND NEST")
    y = hy + 60
    y = draw_centered(d, y, "Most of us", font(F_DISP_XB, 320), INK) + 8
    y = draw_centered(d, y, "nest in the ground.", font(F_DISP_IT, 260), CLAY)
    band_top = y + 80
    band_bot = 4780
    h = min(1400, band_bot - band_top - 40)
    draw_ground_nest(im, W // 2, band_top + 20, width=3000, height=h)
    plate_footer(d, "ABOUT SEVENTY PERCENT OF SOLITARY SPECIES")
    return im


def design_15() -> Image.Image:
    im = new_canvas()
    d = ImageDraw.Draw(im)
    hy = plate_header(d, "PLATE 15", "TUBE ENDS")
    y = hy + 80
    y = draw_centered(d, y, "Closed", font(F_DISP_XB, 360), INK) + 8
    y = draw_centered(d, y, "at the back.", font(F_DISP_IT, 300), CLAY)
    band_top = y + 200
    band_bot = 4780
    mid = (band_top + band_bot) // 2
    draw_closed_back(im, W // 2 - 80, mid - 200, length=3000)
    plate_footer(d, "A BLIND END, AN OPEN ENTRANCE")
    return im



LABELS = [
    "01  Hollow stems. Please wait.",
    "02  Mud walls, no honey.",
    "03  Most bees commute alone.",
    "04  Osmia, opening shift.",
    "05  Eight millimeters, please.",
    "06  One egg per room.",
    "07  Neighbors, not a colony.",
    "08  Pollen on the underside.",
    "09  Six inches, or mostly sons.",
    "10  Unopened until spring.",
    "11  The males come out first.",
    "12  Clay, not sand.",
    "13  One generation a year.",
    "14  Most of us nest in the ground.",
    "15  Closed at the back.",
]

JOBS = [
    ("01-hollow-stems-please-wait.png", "design_01"),
    ("02-mud-walls-no-honey.png", "design_02"),
    ("03-most-bees-commute-alone.png", "design_03"),
    ("04-osmia-opening-shift.png", "design_04"),
    ("05-eight-millimeters-please.png", "design_05"),
    ("06-one-egg-per-room.png", "design_06"),
    ("07-neighbors-not-a-colony.png", "design_07"),
    ("08-pollen-on-the-underside.png", "design_08"),
    ("09-six-inches-or-mostly-sons.png", "design_09"),
    ("10-unopened-until-spring.png", "design_10"),
    ("11-the-males-come-out-first.png", "design_11"),
    ("12-clay-not-sand.png", "design_12"),
    ("13-one-generation-a-year.png", "design_13"),
    ("14-most-of-us-nest-in-the-ground.png", "design_14"),
    ("15-closed-at-the-back.png", "design_15"),
]


def make_preview(
    paths: list[Path],
    out: Path,
    labels: list[str],
    title: str,
    sub: str,
    *,
    cols: int = 5,
    mode: str = "check",  # "check" or "dark"
) -> None:
    thumb_w, thumb_h = 720, 792
    pad = 48
    label_h = 70
    header = 160
    footer = 80
    n = len(paths)
    rows = max(1, math.ceil(n / cols))
    sheet_w = pad + cols * (thumb_w + pad)
    sheet_h = header + rows * (thumb_h + label_h + pad) + footer
    if mode == "dark":
        sheet_bg = (22, 22, 20)
        title_fill = (240, 232, 214)
        sub_fill = (176, 176, 168)
        frame = (240, 232, 214)
        tile_bg = (18, 18, 16, 255)
    else:
        sheet_bg = (248, 246, 240)
        title_fill = (28, 32, 26)
        sub_fill = (80, 80, 74)
        frame = (28, 32, 26)
        tile_bg = None
    sheet = Image.new("RGB", (sheet_w, sheet_h), sheet_bg)
    d = ImageDraw.Draw(sheet)
    f_title = font(F_SANS, 28)
    tw, th = text_size(d, title, f_title)
    d.text(((sheet_w - tw) // 2, 44), title, font=f_title, fill=title_fill)
    f_sub = font(F_MONO, 16)
    sw, sh = text_size(d, sub, f_sub)
    d.text(((sheet_w - sw) // 2, 92), sub, font=f_sub, fill=sub_fill)
    f_lab = font(F_MONO, 16)
    for i, path in enumerate(paths):
        r, c = divmod(i, cols)
        art = Image.open(path).convert("RGBA")
        art.thumbnail((thumb_w, thumb_h), Image.Resampling.LANCZOS)
        if mode == "dark":
            bg = Image.new("RGBA", (thumb_w, thumb_h), tile_bg)
        else:
            bg = checkerboard((thumb_w, thumb_h), 24)
        ox = (thumb_w - art.width) // 2
        oy = (thumb_h - art.height) // 2
        bg.alpha_composite(art, (ox, oy))
        x = pad + c * (thumb_w + pad)
        y = header + r * (thumb_h + label_h + pad)
        sheet.paste(bg.convert("RGB"), (x, y))
        d.rectangle([x, y, x + thumb_w - 1, y + thumb_h - 1], outline=frame, width=2)
        lab = labels[i] if i < len(labels) else path.stem
        lw, lh = text_size(d, lab, f_lab)
        d.text((x + (thumb_w - lw) // 2, y + thumb_h + 18), lab, font=f_lab, fill=title_fill)
    sheet.save(out, "PNG", optimize=True)
    print("preview", out, sheet.size)


def render_batch(out_dir: Path, *, light_ink: bool) -> list[Path]:
    apply_palette(light_ink=light_ink)
    out_dir.mkdir(parents=True, exist_ok=True)
    fns = {name: globals()[fn_name] for name, fn_name in JOBS}
    paths = []
    kind = "light-ink/dark-garment" if light_ink else "dark-ink/light-garment"
    for name, fn_name in JOBS:
        print(f"rendering [{kind}] {name}")
        im = fns[name]()
        dest = out_dir / name
        im.save(dest, "PNG")
        print("  saved", dest, im.size, im.mode)
        paths.append(dest)
    return paths


def render_named(names: list[str], out_dir: Path, *, light_ink: bool) -> list[Path]:
    apply_palette(light_ink=light_ink)
    out_dir.mkdir(parents=True, exist_ok=True)
    wanted = {name: fn for name, fn in JOBS if name in names}
    kind = "light-ink/dark-garment" if light_ink else "dark-ink/light-garment"
    paths = []
    for name, fn_name in JOBS:
        if name not in wanted:
            dest = out_dir / name
            if dest.exists():
                paths.append(dest)
            continue
        print(f"rendering [{kind}] {name}")
        im = globals()[fn_name]()
        dest = out_dir / name
        im.save(dest, "PNG")
        print("  saved", dest, im.size, im.mode)
        paths.append(dest)
    return paths


def main() -> None:
    batch3 = [
        "11-the-males-come-out-first.png",
        "12-clay-not-sand.png",
        "13-one-generation-a-year.png",
        "14-most-of-us-nest-in-the-ground.png",
        "15-closed-at-the-back.png",
    ]
    light_paths = render_named(batch3, OUT_DIR, light_ink=False)
    dark_dir = OUT_DIR / "dark"
    dark_paths = render_named(batch3, dark_dir, light_ink=True)

    make_preview(
        light_paths,
        OUT_DIR / "preview.png",
        LABELS,
        "Stem & Mud  ·  15 typographic plates  ·  5000×5500 px PNG",
        "Dark-ink colorway for light garments  ·  transparent ground on a checkerboard  ·  drafts / unpublished batch 3",
        cols=5,
        mode="check",
    )
    make_preview(
        light_paths[5:10],
        OUT_DIR / "preview-batch2.png",
        LABELS[5:10],
        "Stem & Mud  ·  batch 2  ·  plates 06–10  ·  5000×5500 px PNG",
        "Dark-ink colorway for light garments  ·  transparent ground on a checkerboard",
        cols=5,
        mode="check",
    )
    make_preview(
        light_paths[10:],
        OUT_DIR / "preview-batch3.png",
        LABELS[10:],
        "Stem & Mud  ·  batch 3  ·  plates 11–15  ·  5000×5500 px PNG",
        "Dark-ink colorway for light garments  ·  transparent ground on a checkerboard  ·  not yet published",
        cols=5,
        mode="check",
    )
    make_preview(
        dark_paths,
        OUT_DIR / "preview-dark.png",
        LABELS,
        "Stem & Mud  ·  light-ink colorway for dark garments  ·  all 15 plates",
        "Ivory / pale moss / pale clay / pale slate on a dark ground  ·  transparent masters",
        cols=5,
        mode="dark",
    )


if __name__ == "__main__":
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    main()
