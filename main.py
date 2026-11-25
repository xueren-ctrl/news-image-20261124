#!/usr/bin/env python3
"""Draw the front page of 'The World in One Day' for Tuesday 24 November 2026.

Pure Python standard library only (zlib, struct, os). No network, no fonts
from disk, no image libraries: every letter is drawn from a small bitmap
font defined in this file, every chart, icon and map is drawn from shapes,
and the PNG bytes are encoded by hand. Running this program writes one
deterministic 1024x1024 image to /output/entry.png (or $MAKEFUN_OUTPUT_DIR).

The news on the page was researched and verified in the build session:
only events that happened, or were first reported, on 24 November 2026
in some time zone appear as that day's news. Bigger stories from 21-23
November are listed in the DATE CHECK footer as deliberately left out.
"""

import os
import struct
import zlib

W = 1024
H = 1024

# ---- palette ------------------------------------------------------------
PAPER = (248, 244, 232)   # warm newsprint
INK = (26, 26, 26)        # near-black ink
RED = (176, 42, 32)       # headline accent
BLUE = (31, 78, 121)      # second accent
GREY = (107, 107, 107)    # muted text
LIGHT = (233, 227, 210)   # light panel
MAPSEA = (214, 226, 232)  # sea on the map
MAPLAND = (201, 210, 186) # land on the map
WHITE = (255, 255, 255)
GOLD = (184, 134, 11)

# ---- framebuffer --------------------------------------------------------
fb = bytearray(W * H * 3)
for _y in range(H):
    row = bytes(PAPER) * W
    fb[_y * W * 3:(_y + 1) * W * 3] = row


def set_px(x, y, c):
    if 0 <= x < W and 0 <= y < H:
        i = (y * W + x) * 3
        fb[i] = c[0]
        fb[i + 1] = c[1]
        fb[i + 2] = c[2]


def fill_rect(x, y, w, h, c):
    x0 = max(0, x)
    y0 = max(0, y)
    x1 = min(W, x + w)
    y1 = min(H, y + h)
    if x1 <= x0 or y1 <= y0:
        return
    span = bytes(c) * (x1 - x0)
    for yy in range(y0, y1):
        i = (yy * W + x0) * 3
        fb[i:i + len(span)] = span


def hline(x, y, w, c, t=1):
    fill_rect(x, y, w, t, c)


def vline(x, y, h, c, t=1):
    fill_rect(x, y, t, h, c)


def rect_outline(x, y, w, h, c, t=1):
    hline(x, y, w, c, t)
    hline(x, y + h - t, w, c, t)
    vline(x, y, h, c, t)
    vline(x + w - t, y, h, c, t)


def draw_line(x0, y0, x1, y1, c, t=1):
    """Bresenham line with square thickness."""
    dx = abs(x1 - x0)
    dy = -abs(y1 - y0)
    sx = 1 if x0 < x1 else -1
    sy = 1 if y0 < y1 else -1
    err = dx + dy
    r = t // 2
    while True:
        fill_rect(x0 - r, y0 - r, t, t, c)
        if x0 == x1 and y0 == y1:
            break
        e2 = 2 * err
        if e2 >= dy:
            err += dy
            x0 += sx
        if e2 <= dx:
            err += dx
            y0 += sy


def fill_circle(cx, cy, r, c):
    for yy in range(cy - r, cy + r + 1):
        dx = int((r * r - (yy - cy) * (yy - cy)) ** 0.5)
        fill_rect(cx - dx, yy, 2 * dx + 1, 1, c)


def circle_outline(cx, cy, r, c, t=2):
    for a in range(360):
        import math
        x = int(cx + r * math.cos(math.radians(a)))
        y = int(cy + r * math.sin(math.radians(a)))
        fill_rect(x - t // 2, y - t // 2, t, t, c)


def fill_poly(points, c):
    """Scanline fill for a simple polygon given as [(x, y), ...]."""
    if not points:
        return
    ys = [p[1] for p in points]
    y0, y1 = min(ys), max(ys)
    n = len(points)
    for y in range(y0, y1 + 1):
        xs = []
        for i in range(n):
            x1, yy1 = points[i]
            x2, yy2 = points[(i + 1) % n]
            if (yy1 <= y < yy2) or (yy2 <= y < yy1):
                x = x1 + (y - yy1) * (x2 - x1) / (yy2 - yy1)
                xs.append(x)
        xs.sort()
        for k in range(0, len(xs) - 1, 2):
            fill_rect(int(xs[k]), y, int(xs[k + 1]) - int(xs[k]) + 1, 1, c)


# ---- PNG encoding (stdlib only) -----------------------------------------
def _chunk(typ, data):
    out = struct.pack(">I", len(data)) + typ + data
    out += struct.pack(">I", zlib.crc32(typ + data) & 0xFFFFFFFF)
    return out


def encode_png():
    raw = bytearray()
    for y in range(H):
        raw.append(0)  # filter: none
        raw += fb[y * W * 3:(y + 1) * W * 3]
    comp = zlib.compress(bytes(raw), 9)
    png = b"\x89PNG\r\n\x1a\n"
    png += _chunk(b"IHDR", struct.pack(">IIBBBBB", W, H, 8, 2, 0, 0, 0))
    png += _chunk(b"IDAT", comp)
    png += _chunk(b"IEND", b"")
    return png


def main():
    build_page()
    outdir = os.environ.get("MAKEFUN_OUTPUT_DIR", "/output")
    os.makedirs(outdir, exist_ok=True)
    with open(os.path.join(outdir, "entry.png"), "wb") as f:
        f.write(encode_png())



# ---- bitmap font --------------------------------------------------------
# 5 wide x 9 tall cell. Rows 0-6 are the cap height, row 6 is the
# baseline, rows 7-8 hold descenders. Lowercase x-height letters sit on
# rows 2-6. Each glyph is 9 strings of 5 chars, '#' = ink, '.' = empty.
# Designed by hand in this session.
FONT = {
"A": ("..#..",
      ".#.#.",
      "#...#",
      "#...#",
      "#####",
      "#...#",
      "#...#",
      ".....",
      "....."),
"B": ("####.",
      "#...#",
      "#...#",
      "####.",
      "#...#",
      "#...#",
      "####.",
      ".....",
      "....."),
"C": (".####",
      "#....",
      "#....",
      "#....",
      "#....",
      "#....",
      ".####",
      ".....",
      "....."),
"D": ("####.",
      "#...#",
      "#...#",
      "#...#",
      "#...#",
      "#...#",
      "####.",
      ".....",
      "....."),
"E": ("#####",
      "#....",
      "#....",
      "####.",
      "#....",
      "#....",
      "#####",
      ".....",
      "....."),
"F": ("#####",
      "#....",
      "#....",
      "####.",
      "#....",
      "#....",
      "#....",
      ".....",
      "....."),
"G": (".####",
      "#....",
      "#....",
      "#..##",
      "#...#",
      "#...#",
      ".###.",
      ".....",
      "....."),
"H": ("#...#",
      "#...#",
      "#...#",
      "#####",
      "#...#",
      "#...#",
      "#...#",
      ".....",
      "....."),
"I": ("#####",
      "..#..",
      "..#..",
      "..#..",
      "..#..",
      "..#..",
      "#####",
      ".....",
      "....."),
"J": ("..###",
      "...#.",
      "...#.",
      "...#.",
      "...#.",
      "#..#.",
      ".##..",
      ".....",
      "....."),
"K": ("#...#",
      "#..#.",
      "#.#..",
      "##...",
      "#.#..",
      "#..#.",
      "#...#",
      ".....",
      "....."),
"L": ("#....",
      "#....",
      "#....",
      "#....",
      "#....",
      "#....",
      "#####",
      ".....",
      "....."),
"M": ("#...#",
      "##.##",
      "#.#.#",
      "#.#.#",
      "#...#",
      "#...#",
      "#...#",
      ".....",
      "....."),
"N": ("#...#",
      "##..#",
      "##..#",
      "#.#.#",
      "#..##",
      "#..##",
      "#...#",
      ".....",
      "....."),
"O": (".###.",
      "#...#",
      "#...#",
      "#...#",
      "#...#",
      "#...#",
      ".###.",
      ".....",
      "....."),
"P": ("####.",
      "#...#",
      "#...#",
      "####.",
      "#....",
      "#....",
      "#....",
      ".....",
      "....."),
"Q": (".###.",
      "#...#",
      "#...#",
      "#...#",
      "#.#.#",
      "#..#.",
      ".##.#",
      ".....",
      "....."),
"R": ("####.",
      "#...#",
      "#...#",
      "####.",
      "#.#..",
      "#..#.",
      "#...#",
      ".....",
      "....."),
"S": (".####",
      "#....",
      "#....",
      ".###.",
      "....#",
      "....#",
      "####.",
      ".....",
      "....."),
"T": ("#####",
      "..#..",
      "..#..",
      "..#..",
      "..#..",
      "..#..",
      "..#..",
      ".....",
      "....."),
"U": ("#...#",
      "#...#",
      "#...#",
      "#...#",
      "#...#",
      "#...#",
      ".###.",
      ".....",
      "....."),
"V": ("#...#",
      "#...#",
      "#...#",
      "#...#",
      "#...#",
      ".#.#.",
      "..#..",
      ".....",
      "....."),
"W": ("#...#",
      "#...#",
      "#...#",
      "#.#.#",
      "#.#.#",
      "##.##",
      "#...#",
      ".....",
      "....."),
"X": ("#...#",
      "#...#",
      ".#.#.",
      "..#..",
      ".#.#.",
      "#...#",
      "#...#",
      ".....",
      "....."),
"Y": ("#...#",
      "#...#",
      ".#.#.",
      "..#..",
      "..#..",
      "..#..",
      "..#..",
      ".....",
      "....."),
"Z": ("#####",
      "....#",
      "...#.",
      "..#..",
      ".#...",
      "#....",
      "#####",
      ".....",
      "....."),
}

FONT.update({
"a": (".....",
      ".....",
      ".###.",
      "....#",
      ".####",
      "#...#",
      ".####",
      ".....",
      "....."),
"b": ("#....",
      "#....",
      "####.",
      "#...#",
      "#...#",
      "#...#",
      "####.",
      ".....",
      "....."),
"c": (".....",
      ".....",
      ".####",
      "#....",
      "#....",
      "#....",
      ".####",
      ".....",
      "....."),
"d": ("....#",
      "....#",
      ".####",
      "#...#",
      "#...#",
      "#...#",
      ".####",
      ".....",
      "....."),
"e": (".....",
      ".....",
      ".###.",
      "#...#",
      "#####",
      "#....",
      ".###.",
      ".....",
      "....."),
"f": ("..##.",
      ".#...",
      "#....",
      "####.",
      "#....",
      "#....",
      "#....",
      ".....",
      "....."),
"g": (".....",
      ".....",
      ".####",
      "#...#",
      "#...#",
      ".####",
      "....#",
      ".###.",
      "....."),
"h": ("#....",
      "#....",
      "####.",
      "#...#",
      "#...#",
      "#...#",
      "#...#",
      ".....",
      "....."),
"i": (".....",
      "..#..",
      ".....",
      ".##..",
      "..#..",
      "..#..",
      ".###.",
      ".....",
      "....."),
"j": (".....",
      "...#.",
      ".....",
      "...#.",
      "...#.",
      "...#.",
      "...#.",
      "...#.",
      ".##.."),
"k": ("#....",
      "#....",
      "#..#.",
      "#.#..",
      "##...",
      "#.#..",
      "#..#.",
      ".....",
      "....."),
"l": (".##..",
      "..#..",
      "..#..",
      "..#..",
      "..#..",
      "..#..",
      ".###.",
      ".....",
      "....."),
"m": (".....",
      ".....",
      "##.#.",
      "#.#.#",
      "#.#.#",
      "#.#.#",
      "#.#.#",
      ".....",
      "....."),
"n": (".....",
      ".....",
      "####.",
      "#...#",
      "#...#",
      "#...#",
      "#...#",
      ".....",
      "....."),
"o": (".....",
      ".....",
      ".###.",
      "#...#",
      "#...#",
      "#...#",
      ".###.",
      ".....",
      "....."),
"p": (".....",
      ".....",
      "####.",
      "#...#",
      "#...#",
      "####.",
      "#....",
      "#....",
      "#...."),
"q": (".....",
      ".....",
      ".####",
      "#...#",
      "#...#",
      ".####",
      "....#",
      "....#",
      "....#"),
"r": (".....",
      ".....",
      "#.##.",
      "##..#",
      "#....",
      "#....",
      "#....",
      ".....",
      "....."),
"s": (".....",
      ".....",
      ".####",
      "#....",
      ".###.",
      "....#",
      "####.",
      ".....",
      "....."),
"t": ("..#..",
      "..#..",
      "####.",
      "..#..",
      "..#..",
      "..#..",
      "..##.",
      ".....",
      "....."),
"u": (".....",
      ".....",
      "#...#",
      "#...#",
      "#...#",
      "#...#",
      ".###.",
      ".....",
      "....."),
"v": (".....",
      ".....",
      "#...#",
      "#...#",
      "#...#",
      ".#.#.",
      "..#..",
      ".....",
      "....."),
"w": (".....",
      ".....",
      "#...#",
      "#...#",
      "#.#.#",
      "#.#.#",
      ".#.#.",
      ".....",
      "....."),
"x": (".....",
      ".....",
      "#...#",
      ".#.#.",
      "..#..",
      ".#.#.",
      "#...#",
      ".....",
      "....."),
"y": (".....",
      ".....",
      "#...#",
      "#...#",
      "#...#",
      ".####",
      "....#",
      ".###.",
      "....."),
"z": (".....",
      ".....",
      "#####",
      "....#",
      "...#.",
      "..#..",
      "#####",
      ".....",
      "....."),
"0": (".###.",
      "#...#",
      "#..##",
      "#.#.#",
      "##..#",
      "#...#",
      ".###.",
      ".....",
      "....."),
"1": ("..#..",
      ".##..",
      "..#..",
      "..#..",
      "..#..",
      "..#..",
      ".###.",
      ".....",
      "....."),
"2": (".###.",
      "#...#",
      "....#",
      "...#.",
      "..#..",
      ".#...",
      "#####",
      ".....",
      "....."),
"3": ("####.",
      "....#",
      "....#",
      ".###.",
      "....#",
      "....#",
      "####.",
      ".....",
      "....."),
"4": ("...#.",
      "..##.",
      ".#.#.",
      "#..#.",
      "#####",
      "...#.",
      "...#.",
      ".....",
      "....."),
"5": ("#####",
      "#....",
      "####.",
      "....#",
      "....#",
      "#...#",
      ".###.",
      ".....",
      "....."),
"6": (".###.",
      "#....",
      "#....",
      "####.",
      "#...#",
      "#...#",
      ".###.",
      ".....",
      "....."),
"7": ("#####",
      "....#",
      "...#.",
      "...#.",
      "..#..",
      "..#..",
      "..#..",
      ".....",
      "....."),
"8": (".###.",
      "#...#",
      "#...#",
      ".###.",
      "#...#",
      "#...#",
      ".###.",
      ".....",
      "....."),
"9": (".###.",
      "#...#",
      "#...#",
      ".####",
      "....#",
      "....#",
      ".###.",
      ".....",
      "....."),
".": (".....",
      ".....",
      ".....",
      ".....",
      ".....",
      ".....",
      ".##..",
      ".##..",
      "....."),
",": (".....",
      ".....",
      ".....",
      ".....",
      ".....",
      ".....",
      ".##..",
      ".##..",
      ".#..."),
":": (".....",
      ".....",
      ".##..",
      ".##..",
      ".....",
      ".##..",
      ".##..",
      ".....",
      "....."),
"'": ("..#..",
      "..#..",
      "..#..",
      ".....",
      ".....",
      ".....",
      ".....",
      ".....",
      "....."),
"-": (".....",
      ".....",
      ".....",
      ".....",
      ".###.",
      ".....",
      ".....",
      ".....",
      "....."),
"/": ("....#",
      "...#.",
      "...#.",
      "..#..",
      "..#..",
      ".#...",
      ".#...",
      "#....",
      "....."),
"%": ("##...",
      "##.#.",
      "...#.",
      "..#..",
      ".#...",
      ".#.##",
      "...##",
      ".....",
      "....."),
"+": (".....",
      "..#..",
      "..#..",
      ".###.",
      "..#..",
      "..#..",
      ".....",
      ".....",
      "....."),
" ": (".....",
      ".....",
      ".....",
      ".....",
      ".....",
      ".....",
      ".....",
      ".....",
      "....."),
})


# ---- text ----------------------------------------------------------------
def text_width(s, scale):
    return len(s) * 6 * scale - scale


def draw_text(x, y, s, scale, color):
    """Draw string s with its top-left at (x, y). Returns width used."""
    cx = x
    for ch in s:
        g = FONT.get(ch)
        if g is None:
            cx += 6 * scale
            continue
        for r in range(9):
            row = g[r]
            for c in range(5):
                if row[c] == '#':
                    fill_rect(cx + c * scale, y + r * scale, scale, scale, color)
        cx += 6 * scale
    return cx - x


def draw_text_centered(cx, y, s, scale, color):
    w = text_width(s, scale)
    draw_text(cx - w // 2, y, s, scale, color)
    return w


def wrap_text(s, max_w, scale):
    """Greedy word wrap. Returns a list of lines fitting max_w pixels."""
    words = s.split(" ")
    lines = []
    cur = ""
    for word in words:
        trial = word if not cur else cur + " " + word
        if text_width(trial, scale) <= max_w or not cur:
            cur = trial
        else:
            lines.append(cur)
            cur = word
    if cur:
        lines.append(cur)
    return lines


def draw_para(x, y, s, max_w, scale, color, leading=None):
    """Draw a wrapped paragraph. Returns the y just below the last line."""
    if leading is None:
        leading = 9 * scale + 4
    yy = y
    for line in wrap_text(s, max_w, scale):
        draw_text(x, yy, line, scale, color)
        yy += leading
    return yy


# ---- illustrations --------------------------------------------------------
def draw_kospi_chart(x, y, w, h):
    """Schematic line chart: Monday dip, Tuesday rebound. Labels are the
    verified facts (Mon close -3.3%, Tue morning +5.9%)."""
    fill_rect(x, y, w, h, WHITE)
    rect_outline(x, y, w, h, INK, 1)
    # gridlines
    for gy in (y + h // 3, y + 2 * h // 3):
        draw_line(x + 4, gy, x + w - 4, gy, LIGHT, 1)
    pts = [(x + 8, y + h - 18), (x + w // 4, y + h - 30),
           (x + w // 2, y + h - 34), (x + 3 * w // 4, y + h - 52),
           (x + w - 10, y + 14)]
    for i in range(len(pts) - 1):
        draw_line(pts[i][0], pts[i][1], pts[i + 1][0], pts[i + 1][1], RED, 3)
    # arrowhead at the end
    ex, ey = pts[-1]
    fill_poly([(ex, ey), (ex - 12, ey + 2), (ex - 4, ey + 10)], RED)
    draw_text(x + 8, y + h - 16, "MON -3.3%", 2, GREY)
    draw_text(x + w - 110, y + 2, "TUE +5.9%", 2, RED)


def draw_sg_bars(x, y, w, h):
    """Three bars: Q2 6.4%, Q3 6.1%, 2026 about 6%."""
    fill_rect(x, y, w, h, WHITE)
    rect_outline(x, y, w, h, INK, 1)
    vals = [("Q2", "6.4%", 6.4), ("Q3", "6.1%", 6.1), ("2026", "6.0%", 6.0)]
    bw = 46
    gap = (w - 3 * bw) // 4
    base = y + h - 20
    for i, (lab, val, v) in enumerate(vals):
        bh = int((v / 7.0) * (h - 36))
        bx = x + gap + i * (bw + gap)
        fill_rect(bx, base - bh, bw, bh, BLUE)
        draw_text_centered(bx + bw // 2, base - bh - 16, val, 2, INK)
        draw_text_centered(bx + bw // 2, base + 4, lab, 2, GREY)


def draw_train(x, y, w, h):
    """Side view of a passenger train on a track."""
    # track
    hline(x, y + h - 14, w, INK, 2)
    hline(x, y + h - 8, w, INK, 2)
    for tx in range(x + 6, x + w - 6, 18):
        vline(tx, y + h - 14, 6, INK, 2)
    # cars
    car_w = (w - 40) // 3
    car_h = h - 34
    cy = y + 6
    for i in range(3):
        cx = x + 10 + i * (car_w + 6)
        fill_rect(cx, cy, car_w, car_h, RED if i == 0 else BLUE)
        rect_outline(cx, cy, car_w, car_h, INK, 2)
        # windows
        for wx in range(cx + 8, cx + car_w - 8, 20):
            fill_rect(wx, cy + 8, 12, 12, WHITE)
        # wheels
        fill_circle(cx + 14, cy + car_h + 4, 6, INK)
        fill_circle(cx + car_w - 14, cy + car_h + 4, 6, INK)
    # chimney on the locomotive
    fill_rect(x + 16, cy - 8, 8, 10, INK)


def draw_icon_factory(x, y, s):
    fill_rect(x, y + 14 * s // 4, 30 * s // 4, 16 * s // 4, BLUE)
    fill_rect(x + 4 * s // 4, y + 4 * s // 4, 4 * s // 4, 10 * s // 4, BLUE)
    fill_rect(x + 12 * s // 4, y + 8 * s // 4, 4 * s // 4, 6 * s // 4, BLUE)
    for wx in range(x + 4, x + 28, 8):
        fill_rect(wx, y + 18, 4, 4, WHITE)


def draw_icon_sun(x, y, s):
    fill_circle(x + 15, y + 15, 10, RED)
    for a in range(0, 360, 45):
        import math
        x2 = int(x + 15 + 15 * math.cos(math.radians(a)))
        y2 = int(y + 15 + 15 * math.sin(math.radians(a)))
        draw_line(x + 15, y + 15, x2, y2, RED, 2)


def draw_icon_megaphone(x, y, s):
    fill_poly([(x, y + 8), (x + 22, y), (x + 22, y + 24), (x, y + 16)], RED)
    fill_rect(x + 22, y + 6, 5, 12, INK)
    draw_line(x + 6, y + 16, x + 10, y + 28, INK, 3)


def draw_icon_parliament(x, y, s):
    fill_rect(x, y + 20, 30, 4, INK)
    fill_poly([(x, y + 20), (x + 15, y + 6), (x + 30, y + 20)], BLUE)
    for cx in (x + 4, x + 13, x + 22):
        fill_rect(cx, y + 24, 3, 6, INK)


# ---- world map ------------------------------------------------------------
CONTINENTS = [
    # North America
    [(-168, 66), (-140, 70), (-120, 72), (-95, 80), (-80, 73), (-65, 60),
     (-55, 47), (-70, 42), (-75, 35), (-80, 25), (-90, 21), (-97, 16),
     (-105, 20), (-115, 30), (-125, 40), (-125, 49), (-140, 60), (-165, 60)],
    # South America
    [(-80, 10), (-75, 5), (-60, 0), (-50, -5), (-35, -8), (-40, -20),
     (-48, -28), (-58, -38), (-65, -45), (-70, -54), (-73, -37),
     (-70, -20), (-80, -5), (-80, 5)],
    # Africa
    [(-17, 15), (-10, 30), (0, 36), (10, 37), (20, 32), (30, 31),
     (35, 28), (43, 12), (51, 11), (48, 0), (40, -10), (35, -20),
     (32, -29), (20, -35), (12, -18), (9, -1), (-8, 4)],
    # Eurasia
    [(-10, 36), (-9, 43), (-2, 48), (0, 50), (5, 53), (8, 57), (18, 56),
     (21, 55), (24, 58), (28, 60), (30, 70), (40, 68), (55, 68), (70, 72),
     (90, 75), (110, 77), (130, 72), (150, 70), (170, 66), (178, 65),
     (170, 60), (160, 55), (150, 59), (142, 50), (140, 40), (135, 35),
     (130, 32), (122, 30), (115, 22), (108, 18), (105, 10), (100, 8),
     (97, 15), (92, 21), (88, 22), (80, 15), (77, 8), (72, 20), (66, 25),
     (60, 25), (55, 26), (50, 29), (48, 30), (43, 28), (40, 36), (36, 36),
     (30, 36), (26, 38), (22, 37), (18, 40), (12, 44), (8, 44), (3, 43),
     (-2, 37), (-9, 37)],
    # Australia
    [(113, -22), (114, -30), (115, -35), (120, -34), (124, -33), (129, -32),
     (132, -32), (135, -35), (138, -35), (140, -38), (142, -39), (145, -38),
     (147, -39), (150, -37), (153, -32), (153, -27), (150, -23), (146, -19),
     (142, -11), (136, -12), (132, -11), (130, -13), (126, -14), (122, -17),
     (118, -20)],
]

PINS = [
    (1, "SEOUL", 127, 37),
    (2, "TOKYO", 139, 35),
    (3, "SINGAPORE", 104, 1),
    (4, "JANAKPUR", 86, 26),
    (5, "MUMBAI", 73, 19),
    (6, "BANGKOK", 100, 14),
    (7, "LISBON", -9, 39),
    (8, "FRANKFURT", 8, 50),
]


def draw_map(x, y, w, h):
    fill_rect(x, y, w, h, MAPSEA)
    rect_outline(x, y, w, h, INK, 1)

    def proj(lon, lat):
        px = x + int((lon + 180) / 360.0 * w)
        py = y + int((85 - lat) / 150.0 * h)
        return (px, py)

    for cont in CONTINENTS:
        fill_poly([proj(lon, lat) for lon, lat in cont], MAPLAND)
    for num, name, lon, lat in PINS:
        px, py = proj(lon, lat)
        fill_circle(px, py, 6, RED)
        circle_outline(px, py, 6, WHITE, 1)
        draw_text_centered(px, py - 4, str(num), 1, WHITE)


# ---- page layout ------------------------------------------------------------
def tag(x, y, s, scale=2, color=GREY):
    draw_text(x, y, s, scale, color)


def build_page():
    # outer frame
    rect_outline(12, 12, 1000, 1000, INK, 3)
    rect_outline(18, 18, 988, 988, INK, 1)

    # ---- masthead ----
    draw_text_centered(512, 26, "THE WORLD IN ONE DAY", 4, INK)
    draw_text_centered(512, 64, "TUESDAY 24 NOVEMBER 2026", 6, RED)
    draw_text_centered(512, 120, "FULL-DAY EDITION - STORIES VERIFIED TO 24 NOV 23:59 UTC - ALL TIMES LOCAL", 2, GREY)
    hline(24, 140, 976, INK, 4)
    hline(24, 147, 976, INK, 1)

    # ---- timeline strip ----
    draw_text(24, 156, "THE DAY IN LOCAL TIME", 2, RED)
    tl = [
        ("08:00 SGT", "SG GDP +6.1%"),
        ("09:25 KST", "KOSPI +5.9%"),
        ("10:00 CET", "IFO 90.6"),
        ("10:00 IST", "TRAIN DUE"),
        ("13:00 IST", "RETURN TRAIN"),
        ("16:00 EST", "DOW +0.9%"),
    ]
    for i, (t, ev) in enumerate(tl):
        col = i % 3
        row = i // 3
        ex = 24 + col * 326
        ey = 176 + row * 22
        draw_text(ex, ey, t + " - " + ev, 2, INK)
    hline(24, 222, 976, INK, 1)

    # ---- leads ----
    vline(512, 230, 262, INK, 1)
    # lead 1: KOSPI
    draw_text(24, 232, "MARKETS - ASIA", 2, RED)
    draw_text(24, 254, "ASIA ROARS BACK", 5, INK)
    draw_text(24, 306, "SK HYNIX +8.1%, SAMSUNG +6.8%", 2, INK)
    draw_kospi_chart(24, 336, 472, 72)
    draw_para(24, 420, "KOSPI jumps 5.9% as chip stocks lead the rebound.", 472, 3, INK)
    tag(24, 486, "SEOUL ECONOMIC DAILY - CONFIRMED")
    # lead 2: US market reversal
    draw_text(528, 232, "ECONOMY - UNITED STATES", 2, RED)
    draw_text(528, 254, "RALLY REVERSES ON WALL ST", 3, INK)
    draw_text(528, 306, "NASDAQ -1.5%, S&P -0.5%, DOW +0.9%", 2, INK)
    # US reversal chart: rises on Monday's rally, then falls on Tuesday.
    # Drawn inline with primitives (the two stock chart helpers carry
    # hardcoded KOSPI / Singapore labels, which would be wrong here).
    fill_rect(528, 340, 472, 72, WHITE)
    rect_outline(528, 340, 472, 72, INK, 1)
    for gy in (340 + 72 // 3, 340 + 2 * 72 // 3):
        draw_line(528 + 4, gy, 528 + 472 - 4, gy, LIGHT, 1)
    pts = [(528 + 8, 340 + 72 - 20), (528 + 472 // 4, 340 + 72 - 34),
           (528 + 472 // 2, 340 + 18), (528 + 3 * 472 // 4, 340 + 72 - 30),
           (528 + 472 - 10, 340 + 72 - 16)]
    for i in range(len(pts) - 1):
        draw_line(pts[i][0], pts[i][1], pts[i + 1][0], pts[i + 1][1], RED, 3)
    draw_text(528 + 8, 340 + 72 - 16, "MON RALLY", 2, GREY)
    draw_text(528 + 472 - 110, 340 + 2, "TUE -1.5%", 2, RED)
    draw_para(528, 420, "Nvidia -6% after +31% on Huang's return.", 472, 3, INK)
    tag(528, 486, "INVESTOPEDIA - CONFIRMED")
    hline(24, 500, 976, INK, 1)

    # ---- train band ----
    draw_text(344, 508, "TRANSPORT - INDIA AND NEPAL", 2, RED)
    draw_train(24, 516, 300, 76)
    draw_text(344, 530, "FIRST TRAIN JOINS TWO HOLY CITIES", 3, INK)
    draw_text(344, 564, "The Saryu-Kamala Express reaches Janakpur at 10am.", 2, INK)
    draw_text(344, 586, "604 km in 19 hours. Weekly service from 28 Nov.", 2, INK)
    tag(344, 610, "INDIAN RAILWAYS - CONFIRMED")
    hline(24, 630, 976, INK, 1)

    # ---- small stories ----
    small = [
        ("SINGAPORE LIFTS OUTLOOK",
         "Q3 growth of 6.1% beats forecasts.",
         "REUTERS", draw_icon_factory),
        ("GERMANY IFO 90.6",
         "Morale up 7th month, best since May 2023.",
         "IFO", draw_icon_parliament),
        ("GAZA STRIKE",
         "Hamas security chief killed in Gaza.",
         "REUTERS", draw_icon_megaphone),
        ("HORMUZ TANKERS HIT",
         "Three tankers struck; oil +2.35%.",
         "BARCHART", draw_icon_sun),
    ]
    for i, (head, body, src, icon) in enumerate(small):
        x = 24 + i * 246
        icon(x, 640, 4)
        draw_text(x + 34, 646, src, 2, GREY)
        draw_para(x, 668, head, 238, 3, INK, leading=27)
        draw_para(x, 722, body, 238, 2, INK, leading=19)
    hline(24, 764, 976, INK, 1)

    # ---- map + also on this day ----
    draw_text(24, 772, "WHERE IT HAPPENED", 2, RED)
    draw_map(24, 794, 440, 124)
    vline(484, 772, 168, INK, 1)
    draw_text(504, 772, "ALSO ON THIS DAY", 2, RED)
    also = [
        "1. SEOUL: SK hynix chief bought shares.",
        "2. TOKYO: Yen near 159 per dollar.",
        "3. JANAKPUR: Return train leaves at 1pm.",
        "4. MUMBAI: Shut for Guru Nanak Jayanti.",
        "5. BERLIN: Ifo 90.6, best since May 2023.",
        "6. BANGKOK: 1,000 plan a 16-km fuel march.",
        "7. LISBON: Unions rally as budget looms.",
        "8. NEW YORK: Sanofi buys Insmed for $41B.",
    ]
    yy = 794
    for item in also:
        draw_text(504, yy, item, 2, INK)
        yy += 18
    hline(24, 942, 976, INK, 1)

    # ---- date check footer ----
    draw_text(24, 950, "DATE CHECK - NOT TODAY, LEFT OUT ON PURPOSE", 2, RED)
    draw_text(24, 970, "HUANG REINSTATED - 23 NOV / WOMEN'S WORLD CUP - 23 NOV / EU SANCTIONS - 23 NOV", 2, INK)
    draw_text(24, 988, "COP31 COLLAPSES - 22 NOV / VANUATU QUAKE - 23 NOV / GOMEZ RESIGNS - 23 NOV", 2, INK)


if __name__ == "__main__":
    main()
