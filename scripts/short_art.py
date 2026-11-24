#!/usr/bin/env python3
"""Flat-vector stickman art for the Emu War short.

Design space is 1080x1920; the renderer draws at SS times that and downsamples
once, so all numbers below are readable "screen pixels".

Palette is locked to the shorts-visual-style bible:
  ink #14161A, paper #F4F1EA, accent #FF5A36, blue #2C7BE5, warm #E8C07D
"""
from __future__ import annotations

import math
from typing import Iterable, Sequence

from PIL import Image, ImageDraw, ImageFont

# ---------------------------------------------------------------- palette
INK = (20, 22, 26)
PAPER = (244, 241, 234)
ACCENT = (255, 90, 54)
BLUE = (44, 123, 229)
WARM = (232, 192, 125)

SS = 2  # supersample factor
LW = 3 * SS  # uniform outline width


def px(v: float) -> float:
    return v * SS


# ---------------------------------------------------------------- fonts
def load_font(size: int, bold: bool = True) -> ImageFont.FreeTypeFont:
    names = (
        ["arialbd.ttf", "seguisb.ttf", "segoeuib.ttf", "impact.ttf", "DejaVuSans-Bold.ttf"]
        if bold
        else ["arial.ttf", "segoeui.ttf", "DejaVuSans.ttf"]
    )
    for name in names:
        try:
            return ImageFont.truetype(name, size)
        except Exception:
            continue
    return ImageFont.load_default()


# ---------------------------------------------------------------- strokes
def stroke(d: ImageDraw.ImageDraw, pts: Sequence[tuple[float, float]],
           color=INK, w: float = LW) -> None:
    """Polyline with round caps and joins."""
    if len(pts) < 2:
        return
    d.line([(px(x), px(y)) for x, y in pts], fill=color, width=int(round(w)), joint="curve")
    r = w / 2
    for x, y in (pts[0], pts[-1]):
        d.ellipse([px(x - r), px(y - r), px(x + r), px(y + r)], fill=color)


def outlined_stroke(d: ImageDraw.ImageDraw, pts: Sequence[tuple[float, float]],
                    fill, w: float) -> None:
    """A thick coloured limb with a proper ink outline."""
    stroke(d, pts, INK, w + 2 * LW)
    stroke(d, pts, fill, w)


def dot(d: ImageDraw.ImageDraw, x: float, y: float, r: float, color=INK) -> None:
    d.ellipse([px(x - r), px(y - r), px(x + r), px(y + r)], fill=color)


def shape(d: ImageDraw.ImageDraw, kind: str, box: Sequence[float], fill=PAPER,
          outline=INK, w: float = LW) -> None:
    b = [px(v) for v in box]
    if kind == "ellipse":
        d.ellipse(b, fill=fill, outline=outline, width=int(w))
    elif kind == "rect":
        d.rectangle(b, fill=fill, outline=outline, width=int(w))
    elif kind == "rrect":
        d.rounded_rectangle(b, radius=px(18), fill=fill, outline=outline, width=int(w))


def poly(d: ImageDraw.ImageDraw, pts: Iterable[tuple[float, float]], fill=PAPER,
         outline=INK, w: float = LW) -> None:
    p = [(px(x), px(y)) for x, y in pts]
    d.polygon(p, fill=fill, outline=outline, width=int(w))


def flat_poly(d: ImageDraw.ImageDraw, pts: Iterable[tuple[float, float]], fill=PAPER) -> None:
    d.polygon([(px(x), px(y)) for x, y in pts], fill=fill)


def arc(d: ImageDraw.ImageDraw, box, start, end, color=INK, w: float = LW) -> None:
    d.arc([px(v) for v in box], start, end, fill=color, width=int(w))


# ---------------------------------------------------------------- hats
def hat(d: ImageDraw.ImageDraw, x: float, y: float, r: float, kind: str) -> None:
    """y is the top of the head, r the head radius."""
    if kind == "slouch":
        poly(d, [(x - r * 1.95, y + r * 0.22), (x + r * 1.95, y + r * 0.06),
                 (x + r * 1.60, y - r * 0.32), (x - r * 1.60, y - r * 0.18)], fill=WARM)
        poly(d, [(x - r * 0.98, y + r * 0.06), (x - r * 0.82, y - r * 0.92),
                 (x + r * 0.82, y - r * 0.92), (x + r * 0.98, y + r * 0.03)], fill=WARM)
        stroke(d, [(x - r * 0.92, y - r * 0.44), (x + r * 0.92, y - r * 0.44)], ACCENT, LW * 1.1)
    elif kind == "farmer":
        poly(d, [(x - r * 1.8, y + r * 0.14), (x + r * 1.8, y + r * 0.14),
                 (x + r * 1.20, y - r * 0.46), (x - r * 1.20, y - r * 0.46)], fill=WARM)
        poly(d, [(x - r * 0.92, y + r * 0.06), (x - r * 0.74, y - r * 0.82),
                 (x + r * 0.74, y - r * 0.82), (x + r * 0.92, y + r * 0.02)], fill=WARM)
    elif kind == "cap":
        poly(d, [(x - r * 1.05, y + r * 0.10), (x + r * 1.05, y + r * 0.10),
                 (x + r * 0.85, y - r * 0.60), (x - r * 0.85, y - r * 0.60)], fill=BLUE)
        poly(d, [(x + r * 0.6, y + r * 0.10), (x + r * 1.55, y + r * 0.22),
                 (x + r * 1.5, y - r * 0.05), (x + r * 0.6, y - r * 0.02)], fill=BLUE)


# ---------------------------------------------------------------- stickman
POSES = {
    "stand":  ((-1.9, 1.5), (1.9, 1.5), (-1.0, 4.2), (1.0, 4.2)),
    "aim":    ((-1.0, 1.2), (2.5, 0.9), (-1.5, 4.0), (1.3, 4.2)),
    "kneel":  ((-1.2, 1.4), (2.4, 1.0), (-1.6, 2.2), (1.4, 4.0)),
    "run":    ((-2.4, 0.2), (2.2, 1.9), (-2.4, 3.3), (1.8, 4.4)),
    "point":  ((-1.9, 1.4), (3.0, -0.2), (-1.0, 4.2), (1.0, 4.2)),
    "plead":  ((-2.2, -0.4), (2.2, -0.4), (-1.0, 4.2), (1.0, 4.2)),
    "slump":  ((-1.5, 2.6), (1.5, 2.6), (-1.0, 4.2), (1.0, 4.2)),
    "carry":  ((-1.2, 0.4), (1.2, 0.4), (-1.0, 4.2), (1.0, 4.2)),
    "cheer":  ((-2.4, -1.2), (2.4, -1.2), (-1.0, 4.2), (1.0, 4.2)),
    "facepalm": ((-1.9, 1.5), (1.1, -1.6), (-1.0, 4.2), (1.0, 4.2)),
    "push":   ((-1.0, 1.0), (2.6, 0.6), (-1.9, 4.2), (1.6, 4.2)),
    "rest":   ((-0.55, 3.0), (0.55, 3.0), (-1.0, 4.2), (1.0, 4.2)),
}


def stickman(d: ImageDraw.ImageDraw, x: float, y: float, h: float = 300,
             pose: str = "stand", fill=PAPER, outline=INK,
             hat_kind: str | None = None, eyes: bool = True,
             mouth: str | None = None, brow: str | None = None,
             head_fill=None) -> None:
    """x,y = point between the feet; h = total height."""
    r = 0.105 * h
    head = (x, y - 0.795 * h)
    neck = (x, y - 0.685 * h)
    hip = (x, y - 0.435 * h)

    al, ar, ll, lr = POSES.get(pose, POSES["stand"])

    def off(base, o):
        return (base[0] + o[0] * r, base[1] + o[1] * r)

    stroke(d, [hip, off(hip, ll)], outline)
    stroke(d, [hip, off(hip, lr)], outline)
    stroke(d, [neck, hip], outline)
    stroke(d, [neck, off(neck, al)], outline)
    stroke(d, [neck, off(neck, ar)], outline)
    d.ellipse([px(head[0] - r), px(head[1] - r), px(head[0] + r), px(head[1] + r)],
              fill=head_fill or fill, outline=outline, width=int(LW))
    if eyes:
        dot(d, head[0] - 0.34 * r, head[1] - 0.06 * r, 0.13 * r)
        dot(d, head[0] + 0.34 * r, head[1] - 0.06 * r, 0.13 * r)
    if brow == "angry":
        stroke(d, [(head[0] - 0.58 * r, head[1] - 0.34 * r),
                   (head[0] - 0.12 * r, head[1] - 0.20 * r)], outline, LW * 1.1)
        stroke(d, [(head[0] + 0.58 * r, head[1] - 0.34 * r),
                   (head[0] + 0.12 * r, head[1] - 0.20 * r)], outline, LW * 1.1)
    elif brow == "sad":
        stroke(d, [(head[0] - 0.58 * r, head[1] - 0.20 * r),
                   (head[0] - 0.12 * r, head[1] - 0.36 * r)], outline, LW * 1.1)
        stroke(d, [(head[0] + 0.58 * r, head[1] - 0.20 * r),
                   (head[0] + 0.12 * r, head[1] - 0.36 * r)], outline, LW * 1.1)
    if mouth == "flat":
        stroke(d, [(head[0] - 0.30 * r, head[1] + 0.38 * r),
                   (head[0] + 0.30 * r, head[1] + 0.38 * r)], outline, LW * 0.9)
    elif mouth == "frown":
        arc(d, (head[0] - 0.35 * r, head[1] + 0.20 * r,
                head[0] + 0.35 * r, head[1] + 0.66 * r), 200, 340, outline, LW * 0.9)
    elif mouth == "open":
        d.ellipse([px(head[0] - 0.17 * r), px(head[1] + 0.22 * r),
                   px(head[0] + 0.17 * r), px(head[1] + 0.58 * r)], fill=outline)
    if hat_kind:
        hat(d, head[0], head[1] - r, r, hat_kind)


# ---------------------------------------------------------------- emu
def _foot(d: ImageDraw.ImageDraw, x: float, y: float, s: int, size: float) -> None:
    for k in (-1, 0, 1):
        stroke(d, [(x, y), (x + s * size * (1.15 + 0.12 * abs(k)), y + size * 0.55 * k)],
               INK, LW * 1.5)


def emu(d: ImageDraw.ImageDraw, x: float, y: float, h: float = 260,
        pose: str = "stand", fill=WARM, flip: bool = False) -> None:
    """x,y = feet; h = total height."""
    s = -1 if flip else 1
    body_c = (x, y - 0.47 * h)
    brx, bry = 0.255 * h, 0.185 * h
    head_c = (x + s * 0.30 * h, y - 0.885 * h)
    hr = 0.088 * h

    if pose == "run":
        body_c = (x, y - 0.44 * h)
        head_c = (x + s * 0.38 * h, y - 0.84 * h)
        hip_l = (x - s * 0.04 * h, y - 0.33 * h)
        knee_l = (x - s * 0.20 * h, y - 0.20 * h)
        foot_l = (x - s * 0.30 * h, y - 0.02 * h)
        hip_r = (x + s * 0.05 * h, y - 0.33 * h)
        knee_r = (x + s * 0.16 * h, y - 0.16 * h)
        foot_r = (x + s * 0.24 * h, y)
    elif pose == "look":
        head_c = (x + s * 0.30 * h, y - 0.91 * h)
        hip_l = (x - s * 0.05 * h, y - 0.33 * h)
        knee_l = (x - s * 0.07 * h, y - 0.17 * h)
        foot_l = (x - s * 0.08 * h, y)
        hip_r = (x + s * 0.05 * h, y - 0.33 * h)
        knee_r = (x + s * 0.07 * h, y - 0.17 * h)
        foot_r = (x + s * 0.08 * h, y)
    else:
        hip_l = (x - s * 0.05 * h, y - 0.33 * h)
        knee_l = (x - s * 0.08 * h, y - 0.17 * h)
        foot_l = (x - s * 0.09 * h, y)
        hip_r = (x + s * 0.05 * h, y - 0.33 * h)
        knee_r = (x + s * 0.08 * h, y - 0.17 * h)
        foot_r = (x + s * 0.09 * h, y)

    # legs (behind body)
    for hip, knee, foot in ((hip_l, knee_l, foot_l), (hip_r, knee_r, foot_r)):
        stroke(d, [hip, knee, foot], INK, LW * 1.9)
        _foot(d, foot[0], foot[1], s, 0.055 * h)

    # tail fan
    for k, ang in enumerate((6, 22, 38)):
        a = math.radians(180 - ang) if s > 0 else math.radians(ang)
        base = (body_c[0] - s * 0.17 * h, body_c[1] - 0.01 * h)
        tip = (base[0] + 0.17 * h * math.cos(a), base[1] - 0.17 * h * math.sin(a))
        outlined_stroke(d, [base, tip], fill, 0.042 * h)

    # body
    d.ellipse([px(body_c[0] - brx), px(body_c[1] - bry),
               px(body_c[0] + brx), px(body_c[1] + bry)],
              fill=fill, outline=INK, width=int(LW))
    # feather ticks
    for k in range(2):
        stroke(d, [(body_c[0] - s * 0.06 * h, body_c[1] + (0.02 + 0.05 * k) * h),
                   (body_c[0] - s * 0.15 * h, body_c[1] + (0.06 + 0.05 * k) * h)],
               INK, LW * 0.7)

    # neck: tapered quad from body to head
    neck = [
        (body_c[0] + s * 0.08 * h, body_c[1] - 0.05 * h),
        (head_c[0] - s * 0.075 * h, head_c[1] + 0.02 * h),
        (head_c[0] + s * 0.055 * h, head_c[1] + 0.01 * h),
        (body_c[0] + s * 0.24 * h, body_c[1] + 0.02 * h),
    ]
    poly(d, neck, fill=fill)

    # head
    d.ellipse([px(head_c[0] - hr), px(head_c[1] - hr),
               px(head_c[0] + hr), px(head_c[1] + hr)],
              fill=fill, outline=INK, width=int(LW))
    # crest
    for k in range(3):
        stroke(d, [(head_c[0] - s * 0.02 * h, head_c[1] - hr * 0.85),
                   (head_c[0] - s * (0.02 + 0.03 * k) * h, head_c[1] - hr * 1.55)],
               INK, LW * 0.8)
    # beak
    poly(d, [(head_c[0] + s * hr * 0.55, head_c[1] - hr * 0.20),
             (head_c[0] + s * hr * 2.35, head_c[1] + hr * 0.10),
             (head_c[0] + s * hr * 0.55, head_c[1] + hr * 0.42)], fill=ACCENT)
    # eye
    dot(d, head_c[0] + s * hr * 0.18, head_c[1] - hr * 0.22, hr * 0.22)


def emu_foot(d: ImageDraw.ImageDraw, x: float, y: float, s: int, size: float) -> None:
    """Big three-toed foot. (x,y) = ankle, toes splay downward."""
    for ang, k in ((152, 0.92), (90, 1.12), (28, 0.92)):
        a = math.radians(ang)
        tip = (x + s * size * k * math.cos(a), y + size * k * math.sin(a))
        outlined_stroke(d, [(x, y), tip], WARM, size * 0.30)
        dot(d, tip[0], tip[1], size * 0.10, INK)
    d.ellipse([px(x - size * 0.24), px(y - size * 0.24),
               px(x + size * 0.24), px(y + size * 0.24)],
              fill=WARM, outline=INK, width=int(LW))


def emu_top(d: ImageDraw.ImageDraw, x: float, y: float, s: float = 1.0,
            flip: bool = False) -> None:
    """Emu seen from directly above: long body, neck forward, tail back."""
    k = -1 if flip else 1
    for sy in (-1, 1):
        stroke(d, [(x - k * 10 * s, y + sy * 12 * s),
                   (x - k * 34 * s, y + sy * 30 * s)], INK, LW * 1.5)
    for sy in (-1, 0, 1):
        stroke(d, [(x - k * 36 * s, y + sy * 6 * s),
                   (x - k * 60 * s, y + sy * 22 * s)], WARM, LW * 2.4)
    d.ellipse([px(x - 44 * s), px(y - 24 * s), px(x + 44 * s), px(y + 24 * s)],
              fill=WARM, outline=INK, width=int(LW))
    outlined_stroke(d, [(x + k * 28 * s, y), (x + k * 86 * s, y - 10 * s)], WARM, 15 * s)
    hx = x + k * 98 * s
    hx0, hx1 = sorted((hx - 13 * s, hx + 13 * s))
    hy0, hy1 = sorted((y - 23 * s, y + 3 * s))
    d.ellipse([px(hx0), px(hy0), px(hx1), px(hy1)],
              fill=WARM, outline=INK, width=int(LW))
    poly(d, [(hx + k * 8 * s, y - 16 * s), (hx + k * 32 * s, y - 8 * s),
             (hx + k * 8 * s, y - 1 * s)], fill=ACCENT)




# ---------------------------------------------------------------- props
def wheat(d: ImageDraw.ImageDraw, x: float, y: float, h: float = 180,
          color=WARM) -> None:
    stroke(d, [(x, y), (x, y - h)], INK, LW * 0.8)
    for i in range(5):
        yy = y - h + i * (h * 0.10)
        stroke(d, [(x, yy), (x - 0.09 * h, yy - 0.06 * h)], color, LW * 1.5)
        stroke(d, [(x, yy), (x + 0.09 * h, yy - 0.06 * h)], color, LW * 1.5)
    stroke(d, [(x, y - h), (x, y - h - 0.10 * h)], color, LW * 1.7)


def fence(d: ImageDraw.ImageDraw, x: float, y: float, n: int = 5,
          spacing: float = 150, broken: int | None = None, height: float = 190) -> None:
    top = y - height
    posts = []
    for i in range(n):
        px_ = x + i * spacing
        tilt = 22 if broken is not None and abs(i - broken) <= 1 else 0
        stroke(d, [(px_, y), (px_ + tilt, top)], INK, LW * 2.0)
        posts.append((px_, top, tilt))
    for rail_y in (top + height * 0.22, top + height * 0.60):
        for i in range(n - 1):
            a = (posts[i][0], rail_y)
            b = (posts[i + 1][0], rail_y)
            if broken is not None and i == broken:
                stroke(d, [a, (a[0] + spacing * 0.42, rail_y + 30)], WARM, LW * 2.0)
                stroke(d, [(b[0] - spacing * 0.26, rail_y - 20), b], WARM, LW * 2.0)
            else:
                stroke(d, [a, b], WARM, LW * 2.0)


def machine_gun(d: ImageDraw.ImageDraw, x: float, y: float, s: float = 1.0,
                flash: bool = False, aim: float = 0.0) -> None:
    """Tripod-mounted Lewis gun. (x,y) is the ground point."""
    apex = (x, y - 240 * s)
    for dx in (-95, 0, 95):
        stroke(d, [(x + dx * s, y), apex], INK, LW * 1.5)
    # stock
    poly(d, [(x - 120 * s, apex[1] - 30 * s), (x - 70 * s, apex[1] - 56 * s),
             (x - 70 * s, apex[1] + 8 * s), (x - 120 * s, apex[1] + 22 * s)], fill=WARM)
    # receiver
    shape(d, "rrect", (x - 78 * s, apex[1] - 54 * s, x + 92 * s, apex[1] + 20 * s), fill=BLUE)
    # barrel
    barrel_end = (x + 300 * s, apex[1] - 34 * s + aim * 80 * s)
    outlined_stroke(d, [(x + 80 * s, apex[1] - 24 * s), barrel_end], INK, LW * 3.0)
    # cooling jacket rings
    for i in range(4):
        t = 0.30 + i * 0.15
        bx = x + 80 * s + (barrel_end[0] - x - 80 * s) * t
        by = apex[1] - 24 * s + (barrel_end[1] - apex[1] + 24 * s) * t
        stroke(d, [(bx, by - 15 * s), (bx, by + 15 * s)], WARM, LW * 1.3)
    # ammo drum
    d.ellipse([px(x - 34 * s), px(apex[1] - 100 * s), px(x + 48 * s), px(apex[1] - 30 * s)],
              fill=WARM, outline=INK, width=int(LW))
    dot(d, x + 7 * s, apex[1] - 65 * s, 8 * s, INK)
    if flash:
        fx, fy = barrel_end
        pts = []
        for i in range(10):
            ang = -math.pi / 2 + i * math.pi / 5
            rad = (80 if i % 2 == 0 else 34) * s
            pts.append((fx + rad * math.cos(ang), fy + rad * math.sin(ang)))
        poly(d, pts, fill=ACCENT, outline=INK)


def truck(d: ImageDraw.ImageDraw, x: float, y: float, s: float = 1.0) -> None:
    shape(d, "rect", (x, y - 150 * s, x + 300 * s, y - 40 * s), fill=BLUE)
    shape(d, "rect", (x + 210 * s, y - 205 * s, x + 320 * s, y - 120 * s), fill=BLUE)
    shape(d, "rect", (x + 232 * s, y - 190 * s, x + 300 * s, y - 140 * s), fill=PAPER)
    for wx in (x + 70 * s, x + 250 * s):
        d.ellipse([px(wx - 42 * s), px(y - 62 * s), px(wx + 42 * s), px(y + 22 * s)],
                  fill=INK)
        d.ellipse([px(wx - 16 * s), px(y - 36 * s), px(wx + 16 * s), px(y - 4 * s)],
                  fill=PAPER)


def sun(d: ImageDraw.ImageDraw, x: float, y: float, r: float, color=ACCENT) -> None:
    d.ellipse([px(x - r), px(y - r), px(x + r), px(y + r)], fill=color,
              outline=INK, width=int(LW))


def hills(d: ImageDraw.ImageDraw, y: float, color=WARM, amp: float = 90,
          phase: float = 0.0) -> None:
    pts = [(0, 2400), (0, y)]
    for i in range(0, 25):
        x = i * 48
        yy = y - amp * (0.55 + 0.45 * math.sin(i * 0.55 + phase))
        pts.append((x, yy))
    pts += [(1080, y), (1080, 2400)]
    poly(d, pts, fill=color, outline=INK, w=LW)


def ground(d: ImageDraw.ImageDraw, y: float = 1250, color=PAPER) -> None:
    d.rectangle([0, px(y), px(1080), px(2400)], fill=color)
    stroke(d, [(0, y), (1080, y)], INK, LW)


def dust(d: ImageDraw.ImageDraw, x: float, y: float, r: float, color=WARM) -> None:
    for dx, dy, k in ((-0.62, 0.10, 0.52), (0.02, -0.22, 0.66), (0.66, 0.12, 0.46)):
        rr = r * k
        d.ellipse([px(x + dx * r - rr), px(y + dy * r - rr),
                   px(x + dx * r + rr), px(y + dy * r + rr)], fill=color)
    for k in (-1, 1):
        stroke(d, [(x + k * r * 0.40, y - r * 0.30),
                   (x + k * r * 0.26, y - r * 0.54)], INK, LW * 0.8)


def speed_lines(d: ImageDraw.ImageDraw, x: float, y: float, n: int = 5,
                dx: float = -1, dy: float = 0, length: float = 120,
                gap: float = 46, color=ACCENT) -> None:
    for i in range(n):
        ox = x + (i - n / 2) * gap * -dy
        oy = y + (i - n / 2) * gap * dx
        stroke(d, [(ox, oy), (ox + dx * length, oy + dy * length)], color, LW * 1.5)


def shadow(d: ImageDraw.ImageDraw, x: float, y: float, rx: float) -> None:
    d.ellipse([px(x - rx), px(y - rx * 0.13), px(x + rx), px(y + rx * 0.13)], fill=WARM)


def arrow(d: ImageDraw.ImageDraw, x: float, y: float, dx: float, dy: float,
          color=ACCENT) -> None:
    L = math.hypot(dx, dy)
    ux, uy = dx / L, dy / L
    tip = (x + dx, y + dy)
    stroke(d, [(x, y), tip], color, LW * 1.8)
    poly(d, [tip,
             (tip[0] - ux * 28 - uy * 15, tip[1] - uy * 28 + ux * 15),
             (tip[0] - ux * 28 + uy * 15, tip[1] - uy * 28 - ux * 15)], fill=color)


# ---------------------------------------------------------------- scenes

def s01a(d):
    """Wide: lone gunner faces a line of emus, low sun."""
    sun(d, 800, 1105, 135)
    hills(d, 1250, WARM, 70, 0.6)
    ground(d, 1250)
    for i, x in enumerate((640, 705, 770, 835, 900, 960)):
        emu(d, x, 1255, 110 + (i % 3) * 8, pose="look")
    shadow(d, 350, 1580, 160)
    machine_gun(d, 320, 1580, 0.95, aim=0.0)
    stickman(d, 380, 1580, 440, pose="aim", fill=BLUE, hat_kind="slouch",
             brow="angry", mouth="flat")
    for x, h in ((60, 210), (120, 150), (1000, 230), (940, 160)):
        wheat(d, x, 1900, h)


def s01b(d):
    """Extreme close: the gunner's face under the brim."""
    d.ellipse([px(80), px(300), px(1000), px(1220)], fill=ACCENT, outline=INK, width=int(LW))
    # neck first so the shoulders overlap it
    flat_poly(d, [(452, 1080), (628, 1080), (700, 1560), (380, 1560)], PAPER)
    # shoulders
    poly(d, [(0, 1920), (1080, 1920), (1000, 1520), (700, 1390), (360, 1400), (70, 1530)],
         fill=BLUE)
    # head
    d.ellipse([px(240), px(600), px(840), px(1200)], fill=PAPER, outline=INK, width=int(LW))
    # hat
    poly(d, [(120, 720), (960, 690), (900, 620), (180, 650)], fill=WARM)
    poly(d, [(300, 650), (330, 380), (750, 380), (780, 640)], fill=WARM)
    stroke(d, [(300, 560), (780, 545)], ACCENT, LW * 1.6)
    # eyes
    dot(d, 440, 880, 26, INK)
    dot(d, 650, 880, 26, INK)
    # angry brows
    stroke(d, [(360, 800), (480, 832)], INK, LW * 1.7)
    stroke(d, [(730, 800), (610, 832)], INK, LW * 1.7)
    # mouth
    stroke(d, [(470, 1060), (620, 1060)], INK, LW * 1.6)


def s02a(d):
    """Wide: emus pour through a broken fence into wheat."""
    sun(d, 180, 380, 90)
    hills(d, 1150, WARM, 80, 2.2)
    ground(d, 1150)
    for i, (x, h) in enumerate(((140, 120), (230, 140), (330, 110), (430, 135),
                                (540, 115), (650, 130), (760, 110), (870, 135),
                                (960, 120))):
        emu(d, x, 1350 + (i % 2) * 26, h, pose="run")
    fence(d, -20, 1660, 8, 148, broken=3)
    for x, h in ((80, 170), (250, 140), (520, 190), (800, 150), (990, 180)):
        wheat(d, x, 1900, h)


def s02b(d):
    """Close: a huge three-toed foot stomps a rail apart."""
    ground(d, 1520)
    for x in (-40, 1000):
        stroke(d, [(x, 1520), (x, 700)], INK, LW * 2.2)
    outlined_stroke(d, [(-40, 1010), (1100, 980)], WARM, 16)
    # the snapping rail
    outlined_stroke(d, [(-40, 1330), (400, 1312)], WARM, 18)
    outlined_stroke(d, [(820, 1300), (1120, 1288)], WARM, 18)
    for k in range(6):
        poly(d, [(410 + k * 16, 1318), (450 + k * 34, 1218 - k * 14),
                 (484 + k * 30, 1330)], fill=WARM)
    # leg dropping in from the top of frame
    outlined_stroke(d, [(560, -140), (596, 420), (608, 900)], WARM, 150)
    for k in range(4):
        stroke(d, [(520 + k * 34, 120 + k * 30), (462 + k * 42, 250 + k * 34)], INK, LW * 1.2)
    emu_foot(d, 608, 900, 1, 250)
    # impact
    for a in (-150, -120, -90, -60, -30):
        rad = math.radians(a)
        stroke(d, [(608 + 150 * math.cos(rad), 1290 + 90 * math.sin(rad)),
                   (608 + 230 * math.cos(rad), 1290 + 140 * math.sin(rad))], ACCENT, LW * 1.6)
    speed_lines(d, 300, 620, 4, dx=-0.35, dy=1, length=130, gap=56)
    dust(d, 850, 1370, 170)
    for x, h in ((40, 220), (1010, 260)):
        wheat(d, x, 1920, h)



def s03a(d):
    """Interior: farmers plead with a government man behind a desk."""
    d.rectangle([0, px(0), px(1080), px(1150)], fill=PAPER)
    stroke(d, [(0, 1150), (1080, 1150)], INK, LW)
    d.rectangle([0, px(1150), px(1080), px(2400)], fill=WARM)
    # framed portrait on the wall
    shape(d, "rect", (60, 210, 400, 620), fill=WARM)
    shape(d, "rect", (92, 242, 368, 588), fill=PAPER, w=LW * 0.9)
    d.ellipse([px(186), px(300), px(274), px(388)], fill=INK)
    poly(d, [(126, 566), (334, 566), (300, 442), (160, 442)], fill=INK)
    # window
    shape(d, "rect", (700, 240, 980, 620), fill=PAPER)
    stroke(d, [(840, 240), (840, 620)], INK, LW)
    stroke(d, [(700, 430), (980, 430)], INK, LW)
    # government man: silhouette, arms down behind the desk
    stickman(d, 800, 1300, 540, pose="rest", fill=INK, head_fill=PAPER,
             brow="angry", mouth="flat")
    # farmers
    stickman(d, 170, 1370, 580, pose="plead", hat_kind="farmer", mouth="open", brow="sad")
    stickman(d, 400, 1400, 620, pose="plead", hat_kind="farmer", mouth="open", brow="sad")
    # desk in front of everyone, occluding their legs
    shape(d, "rect", (300, 1010, 1010, 1200), fill=WARM)
    # two requisition forms on the desk
    for i in range(2):
        shape(d, "rect", (350 + i * 170, 1040, 500 + i * 170, 1108), fill=PAPER, w=LW * 0.8)
        stroke(d, [(372 + i * 170, 1064), (478 + i * 170, 1064)], INK, LW * 0.9)
        stroke(d, [(372 + i * 170, 1086), (446 + i * 170, 1086)], INK, LW * 0.9)



def s03b(d):
    """Close: a stamp lands on the request form."""
    ground(d, 1200, WARM)
    shape(d, "rect", (110, 880, 970, 1520), fill=PAPER)
    for i in range(7):
        stroke(d, [(190, 970 + i * 62), (780 - (i % 3) * 90, 970 + i * 62)], INK, LW * 0.9)
    for i in range(2):
        stroke(d, [(210 + i * 92, 1390), (330 + i * 92, 1370)], INK, LW * 2.6)
        stroke(d, [(235 + i * 92, 1390), (235 + i * 92, 1450)], INK, LW * 1.7)
        stroke(d, [(310 + i * 92, 1378), (310 + i * 92, 1450)], INK, LW * 1.7)
    # sleeve + hand gripping the stamp
    outlined_stroke(d, [(540, 400), (620, 690)], BLUE, 112)
    d.ellipse([px(566), px(660), px(706), px(800)], fill=PAPER, outline=INK, width=int(LW))
    for k in range(3):
        stroke(d, [(596 + k * 24, 726), (600 + k * 24, 786)], INK, LW * 0.9)
    shape(d, "rect", (560, 850, 740, 940), fill=BLUE)
    stroke(d, [(610, 940), (610, 1030)], INK, LW * 4)
    d.ellipse([px(555), px(1005), px(665), px(1080)], fill=ACCENT, outline=INK, width=int(LW))
    for a in (-160, -130, -100, -70, -40, -10):
        rad = math.radians(a)
        stroke(d, [(610 + 120 * math.cos(rad), 1060 + 70 * math.sin(rad)),
                   (610 + 175 * math.cos(rad), 1060 + 100 * math.sin(rad))], ACCENT, LW * 1.5)


def s04a(d):
    """Wide: the gun team sets up on the flock at the waterhole."""
    hills(d, 1180, WARM, 60, 4.0)
    ground(d, 1180)
    d.ellipse([px(560), px(1390), px(1000), px(1535)], fill=BLUE, outline=INK, width=int(LW))
    for i, (x, h) in enumerate(((600, 140), (680, 152), (760, 136), (840, 150), (920, 142))):
        emu(d, x, 1400 + (i % 2) * 18, h, pose="look")
    shadow(d, 330, 1620, 200)
    machine_gun(d, 250, 1620, 1.0, aim=-0.05)
    stickman(d, 170, 1620, 430, pose="kneel", fill=BLUE, hat_kind="slouch", brow="angry")
    stickman(d, 520, 1780, 460, pose="carry", fill=BLUE, hat_kind="slouch")
    for x, h in ((60, 180), (1000, 220)):
        wheat(d, x, 1900, h)



def s04b(d):
    """Over the shoulder: the barrel covers the waterhole."""
    sun(d, 250, 660, 115)
    hills(d, 1180, WARM, 70, 1.0)
    ground(d, 1180)
    d.ellipse([px(150), px(1235), px(760), px(1395)], fill=BLUE, outline=INK, width=int(LW))
    for i, (x, y, h) in enumerate(((200, 1195, 120), (295, 1175, 136), (390, 1205, 124),
                                   (485, 1170, 142), (575, 1200, 128), (660, 1180, 134),
                                   (255, 1330, 130), (365, 1348, 140), (505, 1336, 128),
                                   (625, 1326, 136))):
        emu(d, x, y, h, pose="look", flip=i % 2 == 0)
    # gunner's back, bottom-right
    poly(d, [(1080, 2100), (620, 2100), (665, 1640), (860, 1550), (1080, 1600)], fill=BLUE)
    poly(d, [(1080, 1590), (820, 1535), (855, 1430), (1080, 1465)], fill=WARM)
    # barrel reaching into the flock
    outlined_stroke(d, [(890, 1690), (520, 1320)], INK, 56)
    for i in range(4):
        t = 0.18 + i * 0.20
        bx = 890 + (520 - 890) * t
        by = 1690 + (1320 - 1690) * t
        stroke(d, [(bx - 26, by + 38), (bx + 26, by - 38)], WARM, LW * 1.4)
    d.ellipse([px(780), px(1490), px(905), px(1615)], fill=WARM, outline=INK, width=int(LW))
    dot(d, 842, 1552, 14, INK)



def s05a(d):
    """Chaos: muzzle flash, emus scatter."""
    sun(d, 540, 300, 110)
    hills(d, 1050, WARM, 60, 3.0)
    ground(d, 1050)
    for x, y, h, fl in ((120, 1500, 220, False), (250, 1420, 200, True),
                        (820, 1480, 210, False), (960, 1380, 190, True),
                        (400, 1560, 160, False), (700, 1600, 170, True),
                        (60, 1700, 180, False), (1020, 1660, 160, False)):
        emu(d, x, y, h, pose="run", flip=fl)
    machine_gun(d, 180, 1790, 0.95, flash=True, aim=-0.25)
    stickman(d, 95, 1800, 380, pose="kneel", fill=BLUE, hat_kind="slouch", mouth="open")
    dust(d, 320, 1730, 120)
    dust(d, 880, 1560, 95)
    speed_lines(d, 480, 900, 4, dx=1, dy=0.4, length=130)


def s05b(d):
    """Close: an emu sprints past the lens."""
    ground(d, 1200)
    emu(d, 520, 1780, 860, pose="run")
    speed_lines(d, 900, 700, 6, dx=-1, dy=0.1, length=190, gap=52)
    dust(d, 960, 1720, 140)
    dust(d, 170, 1840, 100)
    for x, h in ((40, 240), (1030, 280)):
        wheat(d, x, 1920, h)


def s06a(d):
    """Wide: the gun jams, emus run straight past."""
    hills(d, 1120, WARM, 70, 5.0)
    ground(d, 1120)
    for x, h, fl in ((80, 190, False), (300, 210, True),
                     (760, 200, False), (980, 180, True)):
        emu(d, x, 1370, h, pose="run", flip=fl)
    machine_gun(d, 390, 1720, 1.0, aim=0.35)
    stickman(d, 330, 1760, 440, pose="push", fill=BLUE, hat_kind="slouch",
             mouth="open", brow="angry")
    stroke(d, [(500, 1120), (540, 990)], ACCENT, LW * 1.8)
    stroke(d, [(560, 1130), (630, 1030)], ACCENT, LW * 1.8)
    for x, h in ((60, 200), (1010, 240)):
        wheat(d, x, 1920, h)


def s06b(d):
    """Extreme close: the gunner loses it."""
    d.ellipse([px(120), px(360), px(960), px(1200)], fill=WARM, outline=INK, width=int(LW))
    flat_poly(d, [(470, 1100), (620, 1100), (700, 1560), (390, 1560)], PAPER)
    poly(d, [(0, 1920), (1080, 1920), (980, 1540), (640, 1440), (300, 1470), (40, 1570)],
         fill=BLUE)
    d.ellipse([px(260), px(640), px(800), px(1180)], fill=PAPER, outline=INK, width=int(LW))
    poly(d, [(140, 750), (920, 720), (860, 650), (200, 680)], fill=WARM)
    poly(d, [(320, 680), (350, 420), (730, 420), (760, 670)], fill=WARM)
    stroke(d, [(320, 600), (760, 585)], ACCENT, LW * 1.6)
    # eyes: one squint, one dot
    stroke(d, [(360, 870), (470, 880)], INK, LW * 2.2)
    dot(d, 650, 885, 24, INK)
    stroke(d, [(330, 800), (480, 840)], INK, LW * 1.8)
    stroke(d, [(720, 805), (600, 845)], INK, LW * 1.8)
    # yelling mouth
    d.ellipse([px(470), px(990), px(620), px(1120)], fill=INK)
    # sweat
    for x, y in ((880, 560), (940, 690), (820, 470)):
        poly(d, [(x, y - 34), (x - 18, y), (x + 18, y)], fill=BLUE)
    # jammed barrel
    outlined_stroke(d, [(760, 1780), (1120, 1500)], INK, 44)
    stroke(d, [(820, 1600), (900, 1530)], ACCENT, LW * 5)


def s07a(d):
    """Top-down diagram: the firing line crosses empty ground."""
    ground(d, 0, PAPER)
    for i in range(9):
        stroke(d, [(0, 200 + i * 190), (1080, 200 + i * 190)], WARM, LW * 0.6)
    for i in range(6):
        stroke(d, [(i * 200, 0), (i * 200, 1920)], WARM, LW * 0.6)
    # gun at the left edge
    shape(d, "rrect", (30, 900, 150, 1020), fill=BLUE)
    outlined_stroke(d, [(150, 960), (330, 960)], INK, 30)
    # firing line
    for i in range(15):
        stroke(d, [(330 + i * 52, 960), (330 + i * 52 + 30, 960)], ACCENT, LW * 2.4)
    # scattered emus
    for x, y, fl in ((230, 540, False), (470, 330, True), (700, 610, False),
                     (930, 370, True), (330, 1290, True), (610, 1520, False),
                     (880, 1270, True), (1000, 1600, False)):
        emu_top(d, x, y, 1.5, fl)
    for x, y, dx, dy in ((430, 960, -90, -170), (500, 960, 40, -190),
                         (570, 960, -40, 200), (640, 960, 120, 170)):
        arrow(d, x, y, dx, dy)


def s07b(d):
    """Wide: emus radiate outward, one soldier alone."""
    sun(d, 540, 280, 90)
    hills(d, 1000, WARM, 60, 2.0)
    ground(d, 1000)
    ring = [(180, 1180, 155), (380, 1080, 145), (700, 1080, 150), (900, 1180, 155),
            (120, 1480, 165), (330, 1560, 160), (750, 1560, 155), (960, 1460, 165),
            (520, 1740, 145)]
    for i, (x, y, h) in enumerate(ring):
        emu(d, x, y, h, pose="run", flip=i % 2 == 0)
    stickman(d, 540, 1440, 390, pose="slump", fill=BLUE, hat_kind="slouch",
             mouth="frown", brow="sad")
    for x, y, dx, dy in ((430, 1330, -120, -120), (660, 1330, 120, -120),
                         (430, 1490, -140, 100), (660, 1490, 140, 100)):
        arrow(d, x, y, dx, dy)


def s08a(d):
    """Wide: the truck leaves, the emus hold the field."""
    sun(d, 880, 420, 120)
    hills(d, 1200, WARM, 80, 1.4)
    ground(d, 1200)
    truck(d, 20, 1650, 1.2)
    dust(d, 10, 1690, 130)
    for i, (x, h) in enumerate(((620, 200), (720, 215), (820, 195), (920, 210))):
        emu(d, x, 1520 + (i % 2) * 16, h, pose="look", flip=True)
    for x, h in ((60, 240), (1000, 260)):
        wheat(d, x, 1920, h)



def s08b(d):
    """Extreme close: deadpan emu face."""
    ground(d, 1740)
    # neck
    poly(d, [(300, 2400), (840, 2400), (740, 1000), (400, 1000)], fill=WARM)
    # head
    d.ellipse([px(270), px(540), px(830), px(1070)], fill=WARM, outline=INK, width=int(LW * 2))
    # crest
    for k in range(4):
        stroke(d, [(430 + k * 55, 580), (400 + k * 62, 470)], INK, LW * 1.6)
    # beak
    poly(d, [(800, 740), (1080, 810), (800, 900)], fill=ACCENT, w=LW * 2)
    # eye
    d.ellipse([px(520), px(680), px(640), px(800)], fill=PAPER, outline=INK, width=int(LW * 2))
    dot(d, 580, 740, 22, INK)
    stroke(d, [(500, 660), (660, 690)], INK, LW * 2.6)


SCENES = {
    "1a": s01a, "1b": s01b, "2a": s02a, "2b": s02b,
    "3a": s03a, "3b": s03b, "4a": s04a, "4b": s04b,
    "5a": s05a, "5b": s05b, "6a": s06a, "6b": s06b,
    "7a": s07a, "7b": s07b, "8a": s08a, "8b": s08b,
}


SHIFT = 180


def render_scene(key: str, size=(1080, 1920)) -> Image.Image:
    w, h = size
    img = Image.new("RGB", (w * SS, (h + SHIFT) * SS), PAPER)
    d = ImageDraw.Draw(img)
    SCENES[key](d)
    return img.crop((0, SHIFT * SS, w * SS, (h + SHIFT) * SS))


def contact_sheet(path: str, cols: int = 4, thumb=(270, 480)) -> None:
    keys = list(SCENES)
    rows = (len(keys) + cols - 1) // cols
    sheet = Image.new("RGB", (cols * thumb[0], rows * thumb[1]), (255, 255, 255))
    for i, k in enumerate(keys):
        im = render_scene(k).resize(thumb, Image.Resampling.LANCZOS)
        sheet.paste(im, ((i % cols) * thumb[0], (i // cols) * thumb[1]))
    sheet.save(path)


if __name__ == "__main__":
    import sys
    out = sys.argv[1] if len(sys.argv) > 1 else "contact_sheet.png"
    contact_sheet(out)
    print("wrote", out)
