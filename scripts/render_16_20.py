#!/usr/bin/env python3
"""Stem & Mud plates 16–20.

Original typographic field plates with hand-built SVG line art.
Typography uses SIL OFL fonts in ../../fonts (Newsreader, IBM Plex).
Illustrations are drawn as SVG in code (no stock, clip art, or AI images)
and rasterized, then composed onto a 5000 x 5500 px transparent RGBA PNG.

Colorways: dark ink for light garments; light ink for dark garments.
"""
from __future__ import annotations

import math
import sys
import tempfile
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parent.parent
FONT_DIR = ROOT / "fonts"
OUT_DIR = ROOT / "output"
SVG_DIR = ROOT / "output" / "svg"

W, H = 5000, 5500  # print-ready master size (pixels)

INK = (28, 32, 26, 255)
MOSS = (55, 82, 62, 255)
CLAY = (166, 96, 52, 255)
DUSK = (64, 88, 106, 255)
RULE = INK

INK_LIGHT = (240, 232, 214, 255)
MOSS_LIGHT = (176, 204, 178, 255)
CLAY_LIGHT = (224, 176, 136, 255)
DUSK_LIGHT = (170, 196, 214, 255)


def apply_palette(*, light_ink: bool = False) -> None:
    global INK, MOSS, CLAY, DUSK, RULE
    if light_ink:
        INK, MOSS, CLAY, DUSK = INK_LIGHT, MOSS_LIGHT, CLAY_LIGHT, DUSK_LIGHT
    else:
        INK, MOSS, CLAY, DUSK = (28, 32, 26, 255), (55, 82, 62, 255), (166, 96, 52, 255), (64, 88, 106, 255)
    RULE = INK


def css(color) -> str:
    return f"rgb({color[0]},{color[1]},{color[2]})"


def font(name: str, size: int) -> ImageFont.FreeTypeFont:
    return ImageFont.truetype(str(FONT_DIR / name), size=size)


F_DISP = "Newsreader-DisplayBold.ttf"
F_DISP_XB = "Newsreader-DisplayExtraBold.ttf"
F_DISP_IT = "Newsreader-DisplayItalic.ttf"
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
    if fill is None:
        fill = INK
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
# SVG builder and rasterizer
# ---------------------------------------------------------------------------


class Svg:
    def __init__(self, w: int, h: int):
        self.w = w
        self.h = h
        self.els: list[str] = []

    def _stroke(self, color, width, extra="") -> str:
        return (
            f'stroke="{css(color)}" stroke-width="{width}" fill="none" '
            f'stroke-linecap="round" stroke-linejoin="round" {extra}'
        ).strip()

    def line(self, x1, y1, x2, y2, color, width, extra=""):
        self.els.append(
            f'<line x1="{x1:.2f}" y1="{y1:.2f}" x2="{x2:.2f}" y2="{y2:.2f}" {self._stroke(color, width, extra)}/>'
        )

    def polyline(self, pts, color, width, closed=False, extra=""):
        pairs = " ".join(f"{x:.2f},{y:.2f}" for x, y in pts)
        tag = "polygon" if closed else "polyline"
        self.els.append(f'<{tag} points="{pairs}" {self._stroke(color, width, extra)}/>')

    def circle(self, cx, cy, r, color, width, extra=""):
        self.els.append(
            f'<circle cx="{cx:.2f}" cy="{cy:.2f}" r="{r:.2f}" {self._stroke(color, width, extra)}/>'
        )

    def ellipse(self, cx, cy, rx, ry, color, width, extra=""):
        self.els.append(
            f'<ellipse cx="{cx:.2f}" cy="{cy:.2f}" rx="{rx:.2f}" ry="{ry:.2f}" {self._stroke(color, width, extra)}/>'
        )

    def rect(self, x, y, w, h, color, width, rx=0, extra=""):
        self.els.append(
            f'<rect x="{x:.2f}" y="{y:.2f}" width="{w:.2f}" height="{h:.2f}" '
            f'rx="{rx:.2f}" {self._stroke(color, width, extra)}/>'
        )

    def path(self, d, color, width, extra=""):
        self.els.append(f'<path d="{d}" {self._stroke(color, width, extra)}/>')

    def tilted_ellipse(self, cx, cy, rx, ry, angle_deg, color, width, vein=True):
        a = math.radians(angle_deg)
        pts = []
        for i in range(64):
            t = 2 * math.pi * i / 64
            x = rx * math.cos(t)
            y = ry * math.sin(t)
            xr = x * math.cos(a) - y * math.sin(a)
            yr = x * math.sin(a) + y * math.cos(a)
            pts.append((cx + xr, cy + yr))
        self.polyline(pts, color, width, closed=True)
        if vein:
            self.line(
                cx - rx * 0.35 * math.cos(a),
                cy - rx * 0.35 * math.sin(a),
                cx + rx * 0.72 * math.cos(a),
                cy + rx * 0.72 * math.sin(a),
                color,
                max(2, width * 0.5),
            )

    def to_string(self) -> str:
        body = "\n  ".join(self.els)
        return (
            f'<?xml version="1.0" encoding="UTF-8"?>\n'
            f'<svg xmlns="http://www.w3.org/2000/svg" width="{self.w}" height="{self.h}" '
            f'viewBox="0 0 {self.w} {self.h}" fill="none">\n  {body}\n</svg>\n'
        )

    def write(self, path: Path) -> Path:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(self.to_string(), encoding="utf-8")
        return path


def rasterize_svg(svg_path: Path, w: int, h: int) -> Image.Image:
    try:
        import cairosvg
    except ImportError as exc:
        raise SystemExit(
            "cairosvg is required to render plates 16–25. "
            "Install dependencies with: pip install -r requirements.txt"
        ) from exc
    out = Path(tempfile.mkstemp(suffix=".png")[1])
    cairosvg.svg2png(
        url=str(svg_path),
        write_to=str(out),
        output_width=int(w),
        output_height=int(h),
        background_color="rgba(0,0,0,0)",
    )
    im = Image.open(out).convert("RGBA")
    out.unlink(missing_ok=True)
    return im


def paste_art(base: Image.Image, art: Image.Image, cx: int, top: int) -> None:
    x = cx - art.width // 2
    base.alpha_composite(art, (x, top))


# ---------------------------------------------------------------------------
# Original bee (new geometry; stylized solitary-bee profile, facing right)
# ---------------------------------------------------------------------------


def draw_bee(svg: Svg, cx: float, cy: float, scale: float, body=None, wing=None, facing: int = 1) -> None:
    if body is None:
        body = INK
    if wing is None:
        wing = DUSK

    def X(x: float) -> float:
        return cx + facing * x * scale

    def Y(y: float) -> float:
        return cy + y * scale

    def S(v: float) -> float:
        return v * scale

    # abdomen sits to the right of the thorax, with only a slight overlap
    svg.ellipse(X(118), Y(2), S(82), S(38), body, max(3, S(8)))
    for off in (86, 118, 150):
        svg.path(
            f"M {X(off - 6)} {Y(-28)} Q {X(off + 8)} {Y(2)} {X(off - 5)} {Y(30)}",
            body,
            max(2, S(5)),
        )
    # thorax
    svg.ellipse(X(-2), Y(0), S(50), S(46), body, max(3, S(8)))
    # head
    svg.ellipse(X(-78), Y(-4), S(34), S(30), body, max(3, S(8)))
    # antennae
    svg.path(
        f"M {X(-104)} {Y(-22)} Q {X(-148)} {Y(-84)} {X(-176)} {Y(-72)}",
        body,
        max(2, S(5)),
    )
    svg.path(
        f"M {X(-96)} {Y(-16)} Q {X(-136)} {Y(-58)} {X(-160)} {Y(-46)}",
        body,
        max(2, S(5)),
    )

    def wing_ellipse(wx, wy, rx, ry, ang):
        a = math.radians(ang if facing == 1 else 180 - ang)
        pts = []
        for i in range(64):
            th = 2 * math.pi * i / 64
            x = rx * math.cos(th)
            y = ry * math.sin(th)
            xr = x * math.cos(a) - y * math.sin(a)
            yr = x * math.sin(a) + y * math.cos(a)
            pts.append((X(wx) + xr * scale, Y(wy) + yr * scale))
        svg.polyline(pts, wing, max(2, S(5)), closed=True)
        svg.line(
            X(wx) - rx * 0.35 * math.cos(a) * scale,
            Y(wy) - rx * 0.35 * math.sin(a) * scale,
            X(wx) + rx * 0.72 * math.cos(a) * scale,
            Y(wy) + rx * 0.72 * math.sin(a) * scale,
            wing,
            max(2, S(3)),
        )

    wing_ellipse(14, -100, 148, 40, -30)
    wing_ellipse(-8, -78, 124, 32, -18)
    # three legs, bent downward with a slight forward reach
    for ox, mid_fwd, tip_fwd, mid_dn, tip_dn in (
        (-10, 18, 40, 52, 66),
        (16, 8, 28, 58, 72),
        (44, -8, 10, 54, 68),
    ):
        svg.polyline(
            [(X(ox), Y(44)), (X(ox + mid_fwd), Y(mid_dn)), (X(ox + tip_fwd), Y(tip_dn))],
            body,
            max(2, S(5)),
        )


# ---------------------------------------------------------------------------
# Plate illustrations (SVG)
# ---------------------------------------------------------------------------


def art_thermometer(w: int, h: int) -> tuple[Svg, dict]:
    """A marked thermometer with a bee in cool-morning flight. Returns label anchors."""
    s = Svg(w, h)
    # Layout in the art box
    tx = int(w * 0.38)
    top = int(h * 0.08)
    bot = int(h * 0.88)
    tube_w = 70
    bulb_r = 92
    tube_top = top + 20
    tube_bot = bot - bulb_r * 2 + 30
    # tube
    s.rect(tx - tube_w / 2, tube_top, tube_w, tube_bot - tube_top, INK, 10, rx=tube_w / 2)
    # bulb
    s.circle(tx, tube_bot + bulb_r - 18, bulb_r, INK, 10)
    # inner column up to the 55 mark
    # Scale: 40°F at tube_bot-20, 70°F at tube_top+40
    def y_for_f(temp: float) -> float:
        t0, t1 = 40.0, 70.0
        y0, y1 = tube_bot - 10, tube_top + 50
        return y0 + (temp - t0) / (t1 - t0) * (y1 - y0)

    y55 = y_for_f(55)
    # column (two close vertical lines to suggest a fill without a solid flood)
    col_x0 = tx - 16
    col_x1 = tx + 16
    s.line(tx, tube_bot + bulb_r - 18, tx, y55, CLAY, 22)
    s.circle(tx, tube_bot + bulb_r - 18, 48, CLAY, 8)
    # ticks
    anchors = {}
    for temp, major in ((40, False), (45, False), (50, True), (55, True), (60, True), (65, False), (70, False)):
        y = y_for_f(temp)
        tick = 54 if major else 28
        s.line(tx + tube_w / 2 + 8, y, tx + tube_w / 2 + 8 + tick, y, MOSS if temp == 55 else INK, 7 if major else 5)
        if major:
            anchors[temp] = (tx + tube_w / 2 + 8 + tick + 24, y)
    anchors["bee"] = (int(w * 0.74), int(h * 0.36))
    # dotted flight, starting well to the right of the temperature labels
    bx, by = anchors["bee"]
    start_x = tx + 520
    for i in range(7):
        t = i / 6
        px = start_x + (bx - 220 - start_x) * t
        py = y55 - 30 + (by - y55 + 10) * t
        s.circle(px, py, 6, MOSS, 4)
    draw_bee(s, bx, by, scale=1.55, body=INK, wing=DUSK, facing=1)
    return s, anchors


def art_leafcutter(w: int, h: int) -> tuple[Svg, dict]:
    """A broad leaf with a circular notch cut from the margin, a detached disc, and a bee."""
    s = Svg(w, h)

    # Midrib runs diagonally up-right. Width envelope is a pointed ovate leaf.
    stem = (int(w * 0.16), int(h * 0.78))
    tip = (int(w * 0.44), int(h * 0.16))
    dx, dy = tip[0] - stem[0], tip[1] - stem[1]
    length = math.hypot(dx, dy)
    ux, uy = dx / length, dy / length
    px, py = -uy, ux  # perpendicular
    max_w = 210

    def midrib_point(t: float):
        return (stem[0] + dx * t, stem[1] + dy * t)

    def envelope(t: float) -> float:
        # widest around t=0.42, pointed at both ends
        return max_w * (math.sin(math.pi * t) ** 0.85)

    # Bite: a circle whose center sits on the right margin near mid-leaf
    bite_t = 0.52
    mx, my = midrib_point(bite_t)
    bite_r = 95
    # place center just outside the right margin so the cut is a deep circular notch
    bx = mx + px * (envelope(bite_t) + bite_r * 0.15)
    by = my + py * (envelope(bite_t) + bite_r * 0.15)

    def inside_bite(x, y) -> bool:
        return (x - bx) ** 2 + (y - by) ** 2 < bite_r * bite_r

    # Sample the closed outline: stem -> left side -> tip -> right side -> stem
    left = []
    right = []
    steps = 80
    for i in range(steps + 1):
        t = i / steps
        cx, cy = midrib_point(t)
        e = envelope(t)
        left.append((cx - px * e, cy - py * e))
        right.append((cx + px * e, cy + py * e))

    # Reconstruct right side: when the outline enters the bite, follow the inner arc
    right_rev = list(reversed(right[:-1]))  # tip to stem, skip duplicate tip
    rebuilt = []
    in_bite = False
    arc_started = False
    first_idx = last_idx = None
    for i, (x, y) in enumerate(right_rev):
        hit = inside_bite(x, y)
        if hit and not in_bite:
            first_idx = i
        if in_bite and not hit:
            last_idx = i
            break
        in_bite = hit
    # Build path: left side (stem to tip), then right side until first bite point,
    # then the interior circular arc, then the rest of the right side.
    outline = left + right_rev
    # We'll build more carefully:
    path_pts = list(left)
    if first_idx is None:
        path_pts += right_rev
    else:
        path_pts += right_rev[:first_idx]
        # arc from right_rev[first_idx] to right_rev[last_idx-1], interior to the leaf
        a0 = math.atan2(right_rev[first_idx][1] - by, right_rev[first_idx][0] - bx)
        a1 = math.atan2(right_rev[last_idx - 1][1] - by, right_rev[last_idx - 1][0] - bx)
        # We want the arc that cuts into the leaf (toward the midrib, i.e. inward)
        # Choose the shorter arc that goes toward midrib point.
        def mid_angle(a, b, direction):
            # direction +1 = ccw
            span = (b - a) % (2 * math.pi) if direction == 1 else (a - b) % (2 * math.pi)
            return span
        # test a point slightly ccw from a0; if it's closer to midrib, go ccw
        test_ccw = (bx + bite_r * math.cos(a0 + 0.2), by + bite_r * math.sin(a0 + 0.2))
        mid = midrib_point(bite_t)
        dist_ccw = (test_ccw[0] - mid[0]) ** 2 + (test_ccw[1] - mid[1]) ** 2
        test_cw = (bx + bite_r * math.cos(a0 - 0.2), by + bite_r * math.sin(a0 - 0.2))
        dist_cw = (test_cw[0] - mid[0]) ** 2 + (test_cw[1] - mid[1]) ** 2
        direction = 1 if dist_ccw < dist_cw else -1
        span = (a1 - a0) % (2 * math.pi) if direction == 1 else (a0 - a1) % (2 * math.pi)
        n_arc = 28
        for k in range(n_arc + 1):
            ang = a0 + direction * span * (k / n_arc)
            path_pts.append((bx + bite_r * math.cos(ang), by + bite_r * math.sin(ang)))
        path_pts += right_rev[last_idx:]

    s.polyline(path_pts, MOSS, 10, closed=True)
    # midrib
    rib = [midrib_point(i / 40) for i in range(41)]
    s.polyline(rib, MOSS, 6)
    # a few veins, avoiding the bite
    for t0 in (0.28, 0.40, 0.68):
        cx, cy = midrib_point(t0)
        e = envelope(t0) * 0.72
        # only the left (uncut) side for the middle vein if near the bite
        s.line(cx, cy, cx - px * e, cy - py * e, MOSS, 4)
        if t0 != 0.40:
            s.line(cx, cy, cx + px * e * 0.55, cy + py * e * 0.55, MOSS, 4)
    # short petiole
    pet_x = stem[0] - ux * 70
    pet_y = stem[1] - uy * 70
    s.line(pet_x, pet_y, stem[0], stem[1], MOSS, 8)

    # Detached circular disc, up and to the right of the bite, same radius
    disc = (int(w * 0.58), int(h * 0.28))
    s.circle(disc[0], disc[1], bite_r, CLAY, 8)
    # a short vein on the disc, same angle as the midrib
    s.line(
        disc[0] - ux * 50,
        disc[1] - uy * 50,
        disc[0] + ux * 50,
        disc[1] + uy * 50,
        CLAY,
        4,
    )

    bee_pos = (int(w * 0.80), int(h * 0.58))
    for i in range(6):
        tt = (i + 1) / 7
        px_ = disc[0] + (bee_pos[0] - 200 - disc[0]) * tt
        py_ = disc[1] + (bee_pos[1] - disc[1]) * tt + math.sin(tt * math.pi) * 40
        s.circle(px_, py_, 6, DUSK, 4)
    draw_bee(s, bee_pos[0], bee_pos[1], scale=1.45, body=INK, wing=DUSK, facing=1)
    return s, {"disc": disc, "leaf": midrib_point(0.5)}


def art_no_stinger(w: int, h: int) -> tuple[Svg, dict]:
    """A male mason bee in profile with a callout at the abdomen tip."""
    s = Svg(w, h)
    cx, cy = int(w * 0.46), int(h * 0.52)
    scale = 2.35
    draw_bee(s, cx, cy, scale=scale, body=INK, wing=DUSK, facing=1)
    # abdomen tip is roughly cx + 196*scale
    tip_x = cx + 118 * scale + 82 * scale  # abdomen center + rx
    tip_y = cy + 2 * scale
    # a short, blunt abdomen tip mark — no sting shaft extending out
    s.circle(tip_x, tip_y, 14, CLAY, 6)
    lx1, ly1 = tip_x + 24, tip_y - 10
    lx2, ly2 = tip_x + 260, tip_y - 160
    s.polyline([(lx1, ly1), (lx2, ly2), (lx2 + 340, ly2)], MOSS, 6)
    anchors = {"label": (lx2 + 24, ly2 - 70), "male": (cx, cy + 46 * scale + 80)}
    return s, anchors


def art_morning_house(w: int, h: int) -> tuple[Svg, dict]:
    """A simple nest house with early light to one side and later shade implied."""
    s = Svg(w, h)
    # house toward the right-center; sun on the left
    hx, hy = int(w * 0.56), int(h * 0.58)
    box_w, box_h = 980, 720
    x0, y0 = hx - box_w / 2, hy - box_h / 2
    # shed roof with a clear overhang on the morning (left) side
    roof_l = (x0 - 90, y0 - 20)
    roof_peak = (x0 - 10, y0 - 200)
    roof_r = (x0 + box_w + 50, y0 - 20)
    s.polyline([roof_l, roof_peak, roof_r, (x0 + box_w, y0), (x0, y0), roof_l], INK, 10)
    # box
    s.rect(x0, y0, box_w, box_h, INK, 10, rx=18)
    # entrance holes: 3 rows x 5
    cols, rows = 5, 3
    margin_x, margin_y = 90, 110
    for r in range(rows):
        for c in range(cols):
            cx = x0 + margin_x + c * ((box_w - 2 * margin_x) / (cols - 1))
            cy = y0 + margin_y + r * ((box_h - 2 * margin_y - 40) / (rows - 1))
            s.circle(cx, cy, 28, INK, 7)
    # a short post under the box
    s.line(hx, y0 + box_h, hx, y0 + box_h + 160, INK, 10)
    s.line(hx - 80, y0 + box_h + 160, hx + 80, y0 + box_h + 160, INK, 8)
    # bee approaching a lower-right hole, not sitting on the grid
    bee_x = x0 + box_w + 200
    bee_y = y0 + box_h - 80
    draw_bee(s, bee_x, bee_y, scale=0.95, body=INK, wing=DUSK, facing=-1)
    # early-light sun, closer to the house
    sun_x, sun_y, sun_r = int(w * 0.16), int(h * 0.34), 120
    s.circle(sun_x, sun_y, sun_r, CLAY, 8)
    for i in range(8):
        a = math.radians(-20 + i * 28)
        s.line(
            sun_x + math.cos(a) * (sun_r + 18),
            sun_y + math.sin(a) * (sun_r + 18),
            sun_x + math.cos(a) * (sun_r + 70),
            sun_y + math.sin(a) * (sun_r + 70),
            CLAY,
            7,
        )
    # a soft shade hatch on the far right of the house (afternoon)
    shade_x = x0 + box_w + 70
    for i in range(5):
        yy = y0 + 60 + i * 80
        s.line(shade_x, yy, shade_x + 80, yy + 46, DUSK, 5)
    anchors = {
        "early": (sun_x, sun_y + sun_r + 90),
        "later": (shade_x + 110, y0 + 40 + 2 * 80),
    }
    return s, anchors


def art_found_cavity(w: int, h: int) -> tuple[Svg, dict]:
    """A section of wood with a pre-existing cavity and a bee at the entrance."""
    s = Svg(w, h)
    cx, cy = int(w * 0.42), int(h * 0.50)
    length, height = 2100, 720
    x0, y0 = cx - length / 2, cy - height / 2
    x1, y1 = x0 + length, y0 + height
    # irregular outer timber: rounded rectangle plus a few bark nicks
    s.rect(x0, y0, length, height, INK, 12, rx=70)
    # bark ticks along the top and bottom
    for i in range(11):
        t = (i + 0.5) / 11
        px = x0 + 80 + t * (length - 160)
        s.line(px, y0, px + 16, y0 + 28, INK, 5)
        s.line(px + 30, y1, px + 14, y1 - 26, INK, 5)
    # gentle grain lines
    for i, yy in enumerate((y0 + 140, y0 + 230, y0 + 500, y0 + 590)):
        pts = []
        steps = 24
        for k in range(steps + 1):
            t = k / steps
            x = x0 + 80 + t * (length - 160)
            bump = 16 * math.sin(t * math.pi * 2 + i)
            pts.append((x, yy + bump))
        s.polyline(pts, MOSS, 5)
    # pre-existing cavity: a smooth oval tunnel from mid-left to the open right end
    hole_y = (y0 + y1) / 2
    hole_r = 78
    # inner cavity as a long rounded slot opening to the right
    cav_x0 = x0 + 220
    cav_x1 = x1 - 10
    s.path(
        f"M {cav_x0 + hole_r:.1f} {hole_y - hole_r:.1f} "
        f"L {cav_x1:.1f} {hole_y - hole_r:.1f} "
        f"M {cav_x0 + hole_r:.1f} {hole_y + hole_r:.1f} "
        f"L {cav_x1:.1f} {hole_y + hole_r:.1f}",
        CLAY,
        10,
    )
    s.path(
        f"M {cav_x0 + hole_r:.1f} {hole_y - hole_r:.1f} "
        f"A {hole_r:.1f} {hole_r:.1f} 0 0 0 {cav_x0 + hole_r:.1f} {hole_y + hole_r:.1f}",
        CLAY,
        10,
    )
    # opening ticks at the right
    s.line(x1 + 10, hole_y - hole_r - 20, x1 + 70, hole_y - hole_r - 20, INK, 6)
    s.line(x1 + 10, hole_y + hole_r + 20, x1 + 70, hole_y + hole_r + 20, INK, 6)
    # bee entering from the right
    bx, by = int(w * 0.82), hole_y
    for i in range(6):
        s.circle(x1 + 40 + i * 36, hole_y, 6, MOSS, 4)
    draw_bee(s, bx, by, scale=1.35, body=INK, wing=DUSK, facing=-1)
    anchors = {"label": (cav_x0 + hole_r, y0 - 20), "hole": (cav_x0 + hole_r, hole_y)}
    return s, anchors


# ---------------------------------------------------------------------------
# Plates
# ---------------------------------------------------------------------------


def _title_block(d, y, line1, line2, size1, size2, c1, c2, gap=8) -> int:
    y = draw_centered(d, y, line1, font(F_DISP_XB, size1), c1) + gap
    y = draw_centered(d, y, line2, font(F_DISP_IT, size2), c2)
    return y


def _compose(svg: Svg, svg_name: str, art_w: int, art_h: int, top: int) -> tuple[Image.Image, dict]:
    path = SVG_DIR / svg_name
    # Rebuild svg? caller already has the Svg object
    return path, {}


def _raster_and_paste(base: Image.Image, svg: Svg, name: str, art_w: int, art_h: int, top: int) -> dict:
    path = svg.write(SVG_DIR / name)
    art = rasterize_svg(path, art_w, art_h)
    paste_art(base, art, W // 2, top)
    return {"top": top, "w": art_w, "h": art_h}


def _mono(draw, x, y, text, size=48, fill=None, anchor="lt"):
    if fill is None:
        fill = INK
    fnt = font(F_MONO, size)
    if anchor == "lm":
        tw, th = text_size(draw, text, fnt)
        draw.text((x, y - th // 2), text, font=fnt, fill=fill)
    elif anchor == "mm":
        tw, th = text_size(draw, text, fnt)
        draw.text((x - tw // 2, y - th // 2), text, font=fnt, fill=fill)
    else:
        draw.text((x, y), text, font=fnt, fill=fill)


def design_16() -> Image.Image:
    im = new_canvas()
    d = ImageDraw.Draw(im)
    hy = plate_header(d, "PLATE 16", "COOL FLIGHT")
    y = hy + 60
    y = _title_block(d, y, "Flying by", "fifty-five.", 300, 300, INK, DUSK, gap=4)
    band_top = y + 80
    band_bot = 4780
    art_h = min(2000, band_bot - band_top)
    art_w = 3600
    top = band_top + max(0, (band_bot - band_top - art_h) // 2)
    svg, anchors = art_thermometer(art_w, art_h)
    _raster_and_paste(im, svg, "16-flying-by-fifty-five.svg", art_w, art_h, top)
    # temperature labels, mapped from art-box space into canvas space
    art_x = (W - art_w) // 2
    for temp, key in ((50, 50), (55, 55), (60, 60)):
        ax, ay = anchors[key]
        cx, cy = art_x + ax, top + ay
        if temp == 55:
            _mono(d, cx, cy, "55°F", size=52, fill=CLAY, anchor="lm")
            _mono(d, cx, cy + 58, "about 13°C", size=40, fill=CLAY, anchor="lm")
        else:
            _mono(d, cx, cy, f"{temp}°F", size=44, fill=INK, anchor="lm")
    plate_footer(d, "ABOUT 55°F  ·  COOL MORNING FLIGHT")
    return im


def design_17() -> Image.Image:
    im = new_canvas()
    d = ImageDraw.Draw(im)
    hy = plate_header(d, "PLATE 17", "LEAFCUTTER")
    y = hy + 40
    y = _title_block(d, y, "I cut circles,", "not hexagons.", 280, 280, INK, MOSS, gap=8)
    band_top = y + 40
    band_bot = 4780
    art_h = min(2100, band_bot - band_top)
    art_w = 3800
    top = band_top + max(0, (band_bot - band_top - art_h) // 2)
    svg, _ = art_leafcutter(art_w, art_h)
    _raster_and_paste(im, svg, "17-i-cut-circles-not-hexagons.svg", art_w, art_h, top)
    plate_footer(d, "MEGACHILE  ·  LEAF CELLS, NOT WAX")
    return im


def design_18() -> Image.Image:
    im = new_canvas()
    d = ImageDraw.Draw(im)
    hy = plate_header(d, "PLATE 18", "MALE BEES")
    y = hy + 40
    y = _title_block(d, y, "The males", "have no stinger.", 280, 260, INK, CLAY, gap=8)
    band_top = y + 40
    band_bot = 4780
    art_h = min(2000, band_bot - band_top)
    art_w = 3800
    top = band_top + max(0, (band_bot - band_top - art_h) // 2)
    svg, anchors = art_no_stinger(art_w, art_h)
    _raster_and_paste(im, svg, "18-the-males-have-no-stinger.svg", art_w, art_h, top)
    art_x = (W - art_w) // 2
    lx, ly = anchors["label"]
    _mono(d, art_x + lx, top + ly, "NO STINGER", size=56, fill=MOSS, anchor="lt")
    mx, my = anchors["male"]
    _mono(d, art_x + mx, top + min(my, art_h - 40), "MALE", size=48, fill=INK, anchor="mm")
    plate_footer(d, "FEMALES STING ONLY IF HANDLED ROUGHLY")
    return im


def design_19() -> Image.Image:
    im = new_canvas()
    d = ImageDraw.Draw(im)
    hy = plate_header(d, "PLATE 19", "HOUSE SITING")
    y = hy + 20
    y = _title_block(d, y, "Light early,", "shade later.", 280, 260, CLAY, DUSK, gap=6)
    band_top = y + 20
    band_bot = 4780
    art_h = min(2200, band_bot - band_top)
    art_w = 4000
    top = band_top + max(0, (band_bot - band_top - art_h) // 2)
    svg, anchors = art_morning_house(art_w, art_h)
    _raster_and_paste(im, svg, "19-light-early-shade-later.svg", art_w, art_h, top)
    art_x = (W - art_w) // 2
    mx, my = anchors["early"]
    _mono(d, art_x + mx, top + my, "EARLY", size=48, fill=CLAY, anchor="mm")
    sx, sy = anchors["later"]
    _mono(d, art_x + sx, top + sy, "LATER", size=44, fill=DUSK, anchor="mm")
    plate_footer(d, "WARMED EARLY  ·  SHADE LATER")
    return im


def design_20() -> Image.Image:
    im = new_canvas()
    d = ImageDraw.Draw(im)
    hy = plate_header(d, "PLATE 20", "FOUND CAVITY")
    y = hy + 60
    y = _title_block(d, y, "I borrow", "the hole.", 340, 320, INK, MOSS, gap=8)
    band_top = y + 80
    band_bot = 4780
    art_h = min(1900, band_bot - band_top)
    art_w = 4000
    top = band_top + max(0, (band_bot - band_top - art_h) // 2)
    svg, anchors = art_found_cavity(art_w, art_h)
    _raster_and_paste(im, svg, "20-i-borrow-the-hole.svg", art_w, art_h, top)
    art_x = (W - art_w) // 2
    lx, ly = anchors["label"]
    _mono(d, art_x + art_w * 0.42, top + max(int(ly) - 70, 8), "PRE-EXISTING", size=48, fill=CLAY, anchor="mm")
    plate_footer(d, "A READY-MADE CAVITY")
    return im


DESIGNS = {
    "16-flying-by-fifty-five.png": design_16,
    "17-i-cut-circles-not-hexagons.png": design_17,
    "18-the-males-have-no-stinger.png": design_18,
    "19-light-early-shade-later.png": design_19,
    "20-i-borrow-the-hole.png": design_20,
}

LABELS = [
    "16  Flying by fifty-five.",
    "17  I cut circles, not hexagons.",
    "18  The males have no stinger.",
    "19  Light early, shade later.",
    "20  I borrow the hole.",
]


def checkerboard(size: tuple[int, int], cell: int = 48) -> Image.Image:
    w, h = size
    im = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    a, b = (232, 228, 218, 255), (214, 210, 200, 255)
    for y in range(0, h, cell):
        for x in range(0, w, cell):
            d.rectangle([x, y, x + cell - 1, y + cell - 1], fill=a if (x // cell + y // cell) % 2 == 0 else b)
    return im


def make_preview(
    paths: list[Path],
    out: Path,
    labels: list[str],
    title: str,
    sub: str,
    *,
    cols: int = 5,
    mode: str = "check",
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


def render_named(names: list[str], out_dir: Path, *, light_ink: bool) -> list[Path]:
    apply_palette(light_ink=light_ink)
    out_dir.mkdir(parents=True, exist_ok=True)
    paths = []
    for name in names:
        fn = DESIGNS[name]
        im = fn()
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
        OUT_DIR / "preview-batch4.png",
        LABELS,
        "Stem & Mud  ·  batch 4  ·  plates 16–20  ·  5000×5500 px PNG",
        "Dark-ink colorway for light garments  ·  transparent ground on a checkerboard  ·  drafts, not uploaded",
        cols=5,
        mode="check",
    )
    make_preview(
        dark_paths,
        OUT_DIR / "preview-batch4-dark.png",
        LABELS,
        "Stem & Mud  ·  batch 4  ·  light-ink colorway for dark garments  ·  plates 16–20",
        "Ivory / pale moss / pale clay / pale slate on a dark ground  ·  transparent masters  ·  drafts, not uploaded",
        cols=5,
        mode="dark",
    )


if __name__ == "__main__":
    main()
