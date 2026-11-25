#!/usr/bin/env python3
"""Newspaper front page: the world news of Tuesday 24 November 2026.

Draws one 1024x1024 image, entirely in code, with the Python standard
library only (struct + zlib for the PNG encoder, os for the output path).
No network, no photos, no files read at run time: every pixel comes from
the drawing routines below, so two runs write byte-identical files.

The page: a masthead naming the day, a timeline of the day in local
times, two lead stories (Asia's market rebound; the US rally reversing
at the close), the first Saryu-Kamala Express to Janakpur, four short
stories from Europe, the Middle East and the US, a world map with pins,
an "ALSO ON THIS DAY" list, and a DATE CHECK footer that names the
big 23 November events deliberately left out.
"""

import os
import struct
import zlib

W = 1024
H = 1024

# Palette: warm newsprint paper, near-black ink, brick red, grey, blue.
PAPER = (245, 240, 220)
INK = (26, 26, 26)
RED = (176, 32, 32)
GREY = (107, 107, 107)
BLUE = (42, 74, 138)
DARKBLUE = (30, 60, 120)
MAPSEA = (220, 232, 240)
LAND = (198, 214, 172)
WHITE = (255, 255, 255)


class Canvas:
    """An RGB pixel buffer with tiny drawing primitives."""

    def __init__(self, w, h, bg):
        self.w = w
        self.h = h
        self.px = bytearray(w * h * 3)
        r, g, b = bg
        for i in range(0, len(self.px), 3):
            self.px[i] = r
            self.px[i + 1] = g
            self.px[i + 2] = b

    def set(self, x, y, c):
        if 0 <= x < self.w and 0 <= y < self.h:
            i = (y * self.w + x) * 3
            self.px[i] = c[0]
            self.px[i + 1] = c[1]
            self.px[i + 2] = c[2]

    def fill_rect(self, x, y, w, h, c):
        for yy in range(y, y + h):
            for xx in range(x, x + w):
                self.set(xx, yy, c)

    def rect_outline(self, x, y, w, h, c, t=1):
        for k in range(t):
            self.hline(x, y + k, w, c)
            self.hline(x, y + h - 1 - k, w, c)
            self.vline(x + k, y, h, c)
            self.vline(x + w - 1 - k, y, h, c)

    def hline(self, x, y, w, c):
        for xx in range(x, x + w):
            self.set(xx, y, c)

    def vline(self, x, y, h, c):
        for yy in range(y, y + h):
            self.set(x, yy, c)

    def line(self, x0, y0, x1, y1, c):
        """Bresenham line, endpoints inclusive."""
        dx = abs(x1 - x0)
        dy = -abs(y1 - y0)
        sx = 1 if x0 < x1 else -1
        sy = 1 if y0 < y1 else -1
        err = dx + dy
        x, y = x0, y0
        while True:
            self.set(x, y, c)
            if x == x1 and y == y1:
                break
            e2 = 2 * err
            if e2 >= dy:
                err += dy
                x += sx
            if e2 <= dx:
                err += dx
                y += sy

    def polyline(self, pts, c):
        for (x0, y0), (x1, y1) in zip(pts, pts[1:]):
            self.line(x0, y0, x1, y1, c)

    def circle(self, cx, cy, r, c):
        """Filled disc, drawn row by row."""
        for yy in range(cy - r, cy + r + 1):
            half = int((r * r - (yy - cy) ** 2) ** 0.5)
            self.hline(cx - half, yy, 2 * half + 1, c)

    def circle_outline(self, cx, cy, r, c):
        steps = max(12, 4 * r)
        pts = []
        for k in range(steps + 1):
            import math
            a = 2 * math.pi * k / steps
            pts.append((cx + int(r * math.cos(a)), cy + int(r * math.sin(a))))
        self.polyline(pts, c)


def _chunk(typ, data):
    out = struct.pack(">I", len(data)) + typ + data
    out += struct.pack(">I", zlib.crc32(typ + data) & 0xFFFFFFFF)
    return out


def encode_png(cv):
    """Encode the canvas as a PNG (8-bit RGB, filter 0 per row)."""
    raw = bytearray()
    stride = cv.w * 3
    for y in range(cv.h):
        raw.append(0)
        raw += cv.px[y * stride:(y + 1) * stride]
    ihdr = struct.pack(">IIBBBBB", cv.w, cv.h, 8, 2, 0, 0, 0)
    return (b"\x89PNG\r\n\x1a\n"
            + _chunk(b"IHDR", ihdr)
            + _chunk(b"IDAT", zlib.compress(bytes(raw), 9))
            + _chunk(b"IEND", b""))


def save_png(cv, path):
    with open(path, "wb") as f:
        f.write(encode_png(cv))


# ---------------------------------------------------------------------------
# Bitmap font. Every glyph is 5 columns wide and 7 rows tall, stored as
# seven 5-bit numbers (bit 4 = leftmost column). Designed here from
# scratch for this page: capitals, lower case, digits and punctuation.
# ---------------------------------------------------------------------------

FONT = {
    "A": (0x0E, 0x11, 0x11, 0x1F, 0x11, 0x11, 0x11),
    "B": (0x1E, 0x11, 0x11, 0x1E, 0x11, 0x11, 0x1E),
    "C": (0x0E, 0x11, 0x10, 0x10, 0x10, 0x11, 0x0E),
    "D": (0x1E, 0x11, 0x11, 0x11, 0x11, 0x11, 0x1E),
    "E": (0x1F, 0x10, 0x10, 0x1E, 0x10, 0x10, 0x1F),
    "F": (0x1F, 0x10, 0x10, 0x1E, 0x10, 0x10, 0x10),
    "G": (0x0E, 0x11, 0x10, 0x17, 0x11, 0x11, 0x0F),
    "H": (0x11, 0x11, 0x11, 0x1F, 0x11, 0x11, 0x11),
    "I": (0x0E, 0x04, 0x04, 0x04, 0x04, 0x04, 0x0E),
    "J": (0x07, 0x02, 0x02, 0x02, 0x02, 0x12, 0x0C),
    "K": (0x11, 0x12, 0x14, 0x18, 0x14, 0x12, 0x11),
    "L": (0x10, 0x10, 0x10, 0x10, 0x10, 0x10, 0x1F),
    "M": (0x11, 0x1B, 0x15, 0x15, 0x11, 0x11, 0x11),
    "N": (0x11, 0x19, 0x15, 0x13, 0x11, 0x11, 0x11),
    "O": (0x0E, 0x11, 0x11, 0x11, 0x11, 0x11, 0x0E),
    "P": (0x1E, 0x11, 0x11, 0x1E, 0x10, 0x10, 0x10),
    "Q": (0x0E, 0x11, 0x11, 0x11, 0x15, 0x12, 0x0D),
    "R": (0x1E, 0x11, 0x11, 0x1E, 0x14, 0x12, 0x11),
    "S": (0x0F, 0x10, 0x10, 0x0E, 0x01, 0x01, 0x1E),
    "T": (0x1F, 0x04, 0x04, 0x04, 0x04, 0x04, 0x04),
    "U": (0x11, 0x11, 0x11, 0x11, 0x11, 0x11, 0x0E),
    "V": (0x11, 0x11, 0x11, 0x11, 0x11, 0x0A, 0x04),
    "W": (0x11, 0x11, 0x11, 0x15, 0x15, 0x1B, 0x11),
    "X": (0x11, 0x11, 0x0A, 0x04, 0x0A, 0x11, 0x11),
    "Y": (0x11, 0x11, 0x0A, 0x04, 0x04, 0x04, 0x04),
    "Z": (0x1F, 0x01, 0x02, 0x04, 0x08, 0x10, 0x1F),
    "0": (0x0E, 0x11, 0x13, 0x15, 0x19, 0x11, 0x0E),
    "1": (0x04, 0x0C, 0x04, 0x04, 0x04, 0x04, 0x0E),
    "2": (0x0E, 0x11, 0x01, 0x06, 0x08, 0x10, 0x1F),
    "3": (0x1F, 0x02, 0x04, 0x02, 0x01, 0x11, 0x0E),
    "4": (0x02, 0x06, 0x0A, 0x12, 0x1F, 0x02, 0x02),
    "5": (0x1F, 0x10, 0x1E, 0x01, 0x01, 0x11, 0x0E),
    "6": (0x06, 0x08, 0x10, 0x1E, 0x11, 0x11, 0x0E),
    "7": (0x1F, 0x01, 0x02, 0x04, 0x08, 0x08, 0x08),
    "8": (0x0E, 0x11, 0x11, 0x0E, 0x11, 0x11, 0x0E),
    "9": (0x0E, 0x11, 0x11, 0x0F, 0x01, 0x02, 0x0C),
    "a": (0x00, 0x00, 0x0E, 0x01, 0x0F, 0x11, 0x0F),
    "b": (0x10, 0x10, 0x1E, 0x11, 0x11, 0x11, 0x1E),
    "c": (0x00, 0x00, 0x0E, 0x11, 0x10, 0x11, 0x0E),
    "d": (0x01, 0x01, 0x0F, 0x11, 0x11, 0x11, 0x0F),
    "e": (0x00, 0x00, 0x0E, 0x11, 0x1F, 0x10, 0x0E),
    "f": (0x06, 0x09, 0x08, 0x1E, 0x08, 0x08, 0x08),
    "g": (0x00, 0x0F, 0x11, 0x11, 0x0F, 0x01, 0x0E),
    "h": (0x10, 0x10, 0x1E, 0x11, 0x11, 0x11, 0x11),
    "i": (0x04, 0x00, 0x0C, 0x04, 0x04, 0x04, 0x0E),
    "j": (0x02, 0x00, 0x06, 0x02, 0x02, 0x12, 0x0C),
    "k": (0x10, 0x10, 0x12, 0x14, 0x18, 0x14, 0x12),
    "l": (0x0C, 0x04, 0x04, 0x04, 0x04, 0x04, 0x0E),
    "m": (0x00, 0x00, 0x1A, 0x15, 0x15, 0x15, 0x15),
    "n": (0x00, 0x00, 0x1E, 0x11, 0x11, 0x11, 0x11),
    "o": (0x00, 0x00, 0x0E, 0x11, 0x11, 0x11, 0x0E),
    "p": (0x00, 0x00, 0x1E, 0x11, 0x11, 0x1E, 0x10),
    "q": (0x00, 0x00, 0x0F, 0x11, 0x11, 0x0F, 0x01),
    "r": (0x00, 0x00, 0x16, 0x19, 0x10, 0x10, 0x10),
    "s": (0x00, 0x00, 0x0F, 0x10, 0x0E, 0x01, 0x1E),
    "t": (0x04, 0x04, 0x1F, 0x04, 0x04, 0x04, 0x06),
    "u": (0x00, 0x00, 0x11, 0x11, 0x11, 0x13, 0x0D),
    "v": (0x00, 0x00, 0x11, 0x11, 0x11, 0x0A, 0x04),
    "w": (0x00, 0x00, 0x11, 0x15, 0x15, 0x15, 0x0A),
    "x": (0x00, 0x00, 0x11, 0x0A, 0x04, 0x0A, 0x11),
    "y": (0x00, 0x00, 0x11, 0x11, 0x0F, 0x01, 0x0E),
    "z": (0x00, 0x00, 0x1F, 0x02, 0x04, 0x08, 0x1F),
    " ": (0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00),
    ".": (0x00, 0x00, 0x00, 0x00, 0x00, 0x0C, 0x0C),
    ",": (0x00, 0x00, 0x00, 0x00, 0x0C, 0x04, 0x08),
    "-": (0x00, 0x00, 0x00, 0x0E, 0x00, 0x00, 0x00),
    "+": (0x00, 0x04, 0x04, 0x1F, 0x04, 0x04, 0x00),
    "%": (0x19, 0x1A, 0x02, 0x04, 0x08, 0x0B, 0x13),
    "'": (0x04, 0x04, 0x08, 0x00, 0x00, 0x00, 0x00),
    "/": (0x01, 0x02, 0x02, 0x04, 0x08, 0x08, 0x10),
    "(": (0x02, 0x04, 0x08, 0x08, 0x08, 0x04, 0x02),
    ")": (0x08, 0x04, 0x02, 0x02, 0x02, 0x04, 0x08),
    "!": (0x04, 0x04, 0x04, 0x04, 0x04, 0x00, 0x04),
    "?": (0x0E, 0x11, 0x01, 0x06, 0x04, 0x00, 0x04),
    "&": (0x0C, 0x12, 0x14, 0x08, 0x15, 0x12, 0x0D),
    "$": (0x04, 0x0F, 0x14, 0x0E, 0x05, 0x1E, 0x04),
    "=": (0x00, 0x00, 0x1F, 0x00, 0x1F, 0x00, 0x00),
    '"': (0x0A, 0x0A, 0x00, 0x00, 0x00, 0x00, 0x00),
    ";": (0x00, 0x0C, 0x0C, 0x00, 0x0C, 0x04, 0x08),
    ":": (0x00, 0x0C, 0x0C, 0x00, 0x0C, 0x0C, 0x00),
    "*": (0x00, 0x04, 0x15, 0x0E, 0x15, 0x04, 0x00),
}


# ---------------------------------------------------------------------------
# Text. One character cell is 6 px wide (5 px glyph + 1 px gap) at scale 1.
# ---------------------------------------------------------------------------

def char_w(scale):
    return 6 * scale


def text_w(s, scale):
    return len(s) * char_w(scale)


def draw_char(cv, x, y, ch, scale, color):
    rows = FONT.get(ch)
    if rows is None:
        return
    for r in range(7):
        bits = rows[r]
        for c in range(5):
            if bits >> (4 - c) & 1:
                cv.fill_rect(x + c * scale, y + r * scale, scale, scale, color)


def draw_text(cv, x, y, s, scale, color):
    for i, ch in enumerate(s):
        draw_char(cv, x + i * char_w(scale), y, ch, scale, color)


def draw_centered(cv, cx, y, s, scale, color):
    draw_text(cv, cx - text_w(s, scale) // 2, y, s, scale, color)


def wrap_lines(s, max_chars):
    """Greedy word wrap; returns a list of lines, each <= max_chars."""
    lines = []
    for chunk in s.split("\n"):
        words = chunk.split(" ")
        cur = ""
        for w in words:
            nxt = w if not cur else cur + " " + w
            if len(nxt) <= max_chars:
                cur = nxt
            else:
                if cur:
                    lines.append(cur)
                cur = w
        if cur:
            lines.append(cur)
    return lines


def draw_para(cv, x, y, s, scale, color, max_chars, leading=14):
    for i, ln in enumerate(wrap_lines(s, max_chars)):
        draw_text(cv, x, y + i * leading, ln, scale, color)
    return y + len(wrap_lines(s, max_chars)) * leading


# ---------------------------------------------------------------------------
# Page sections. Content runs between x=24 and x=1000.
# ---------------------------------------------------------------------------

CX0, CX1 = 24, 1000


def draw_frame(cv):
    cv.rect_outline(6, 6, W - 12, H - 12, INK, 2)
    cv.rect_outline(14, 14, W - 28, H - 28, INK, 1)


def draw_masthead(cv):
    draw_centered(cv, W // 2, 32, "THE WORLD IN ONE DAY", 4, INK)
    draw_centered(cv, W // 2, 66, "TUESDAY 24 NOVEMBER 2026", 6, RED)
    draw_centered(cv, W // 2, 116,
                  "FULL-DAY EDITION - STORIES VERIFIED TO 24 NOV 23:59 UTC"
                  " - ALL TIMES LOCAL", 2, GREY)
    cv.hline(CX0, 138, CX1 - CX0, INK)
    cv.hline(CX0, 142, CX1 - CX0, INK)


def draw_timeline(cv):
    y = 152
    draw_text(cv, CX0, y, "THE DAY IN LOCAL TIME", 2, RED)
    items = [
        ("08:00 SGT - SG GDP +6.1%", "09:25 KST - KOSPI +5.9%",
         "10:00 CET - IFO 90.6"),
        ("10:00 IST - TRAIN DUE", "13:00 IST - RETURN TRAIN",
         "16:00 EST - DOW +0.9%"),
    ]
    col_x = (CX0, 353, 682)
    for row, trio in enumerate(items):
        for col, txt in enumerate(trio):
            draw_text(cv, col_x[col], y + 20 + row * 20, txt, 2, INK)
    cv.hline(CX0, 222, CX1 - CX0, INK)


def draw_headline_asia(cv):
    x0, x1 = CX0, 500
    y = 232
    draw_text(cv, x0, y, "MARKETS - ASIA", 2, RED)
    draw_text(cv, x0, y + 20, "ASIA ROARS BACK", 4, INK)
    draw_text(cv, x0, y + 56, "SK HYNIX +8.1%, SAMSUNG +6.8%", 2, INK)
    # Rising KOSPI line chart.
    bx, by, bw, bh = x0, y + 78, 476, 84
    cv.rect_outline(bx, by, bw, bh, INK, 1)
    pts = [(bx + 16, by + 66), (bx + 86, by + 58), (bx + 156, by + 52),
           (bx + 226, by + 44), (bx + 296, by + 30), (bx + 366, by + 18),
           (bx + 446, by + 10)]
    cv.polyline(pts, RED)
    draw_text(cv, bx + 8, by + bh - 16, "MON -3.3%", 2, GREY)
    draw_text(cv, bx + bw - 118, by + 4, "TUE +5.9%", 2, RED)
    draw_para(cv, x0, y + 174, "KOSPI jumps 5.9% as chip stocks lead "
              "the rebound.", 2, INK, 38)
    draw_text(cv, x0, y + 214, "SEOUL ECONOMIC DAILY - CONFIRMED", 2, GREY)


def draw_headline_wallst(cv):
    x0, x1 = 524, CX1
    y = 232
    draw_text(cv, x0, y, "ECONOMY - UNITED STATES", 2, RED)
    draw_text(cv, x0, y + 20, "RALLY REVERSES ON WALL ST", 3, INK)
    draw_text(cv, x0, y + 52, "NASDAQ -1.5%, S&P -0.5%, DOW +0.9%", 2, INK)
    # Rise-then-fall line chart: Monday's rally gives it all back.
    bx, by, bw, bh = x0, y + 78, 476, 84
    cv.rect_outline(bx, by, bw, bh, INK, 1)
    pts = [(bx + 16, by + 66), (bx + 96, by + 46), (bx + 176, by + 28),
           (bx + 256, by + 18), (bx + 326, by + 34), (bx + 396, by + 54),
           (bx + 456, by + 68)]
    cv.polyline(pts, RED)
    draw_text(cv, bx + 8, by + bh - 16, "MON RALLY", 2, GREY)
    draw_text(cv, bx + bw - 118, by + 4, "TUE -1.5%", 2, RED)
    draw_para(cv, x0, y + 174, "Nvidia -6% after +31% on Huang's "
              "return.", 2, INK, 38)
    draw_text(cv, x0, y + 214, "INVESTOPEDIA - CONFIRMED", 2, GREY)


def draw_train(cv, x, y):
    """Three-car train with rails, drawn from rectangles and discs."""
    for i, col in enumerate((RED, BLUE, BLUE)):
        cx = x + i * 92
        cv.fill_rect(cx, y, 84, 42, col)
        cv.rect_outline(cx, y, 84, 42, INK, 1)
        for w in range(3):
            cv.fill_rect(cx + 10 + w * 26, y + 10, 16, 14, WHITE)
            cv.rect_outline(cx + 10 + w * 26, y + 10, 16, 14, INK, 1)
        cv.circle(cx + 18, y + 48, 6, INK)
        cv.circle(cx + 66, y + 48, 6, INK)
    cv.hline(x - 6, y + 58, 3 * 92, INK)
    cv.hline(x - 6, y + 64, 3 * 92, INK)
    for t in range(0, 3 * 92, 14):
        cv.vline(x - 6 + t, y + 58, 7, INK)


def draw_train_strip(cv):
    y = 478
    cv.hline(CX0, y - 6, CX1 - CX0, INK)
    draw_train(cv, 30, 492)
    tx = 330
    draw_text(cv, tx, y + 6, "TRANSPORT - INDIA AND NEPAL", 2, RED)
    draw_text(cv, tx, y + 26, "FIRST TRAIN JOINS TWO HOLY CITIES", 3, INK)
    draw_para(cv, tx, y + 60, "The Saryu-Kamala Express reaches "
              "Janakpur at 10am. 604 km in 19 hours. Weekly service "
              "from 28 Nov.", 2, INK, 50)
    draw_text(cv, tx, y + 96, "INDIAN RAILWAYS - CONFIRMED", 2, GREY)


def _icon_building(cv, x, y, col):
    cv.fill_rect(x, y + 6, 18, 14, col)
    cv.fill_rect(x + 3, y + 2, 12, 4, col)
    for wx in (x + 4, x + 10):
        cv.fill_rect(wx, y + 10, 3, 4, WHITE)
        cv.fill_rect(wx, y + 15, 3, 4, WHITE)


def _icon_dome(cv, x, y, col):
    cv.fill_rect(x + 2, y + 10, 16, 10, col)
    cv.fill_rect(x + 8, y + 2, 4, 8, col)
    cv.fill_rect(x + 6, y + 6, 8, 4, col)


def _icon_megaphone(cv, x, y, col):
    cv.fill_rect(x + 2, y + 8, 8, 6, col)
    cv.polyline([(x + 10, y + 4), (x + 20, y + 2), (x + 20, y + 18),
                 (x + 10, y + 16)], col)
    cv.line(x + 10, y + 4, x + 10, y + 16, col)
    cv.fill_rect(x + 6, y + 14, 3, 6, col)


def _icon_burst(cv, x, y, col):
    cx, cy = x + 10, y + 10
    for k in range(8):
        import math
        a = math.pi * k / 4
        cv.line(cx, cy, cx + int(9 * math.cos(a)),
                cy + int(9 * math.sin(a)), col)
    cv.circle(cx, cy, 3, col)


def draw_small_stories(cv):
    y = 612
    cv.hline(CX0, y - 8, CX1 - CX0, INK)
    stories = [
        ("REUTERS", _icon_building, BLUE,
         "SINGAPORE", "LIFTS OUTLOOK",
         "Q3 growth of 6.1% beats forecasts."),
        ("IFO", _icon_dome, DARKBLUE,
         "GERMANY IFO", "90.6",
         "Business morale up 7th month, best since May 2023."),
        ("REUTERS", _icon_megaphone, RED,
         "GAZA STRIKE", "",
         "Hamas security chief killed in Gaza City airstrike."),
        ("BARCHART", _icon_burst, RED,
         "HORMUZ", "TANKERS HIT",
         "Three tankers struck; oil up, US mulls new tariffs."),
    ]
    for i, (src, icon, col, h1, h2, body) in enumerate(stories):
        x = CX0 + i * 244
        icon(cv, x, y, col)
        draw_text(cv, x + 28, y + 4, src, 2, GREY)
        hy = y + 28
        draw_text(cv, x, hy, h1, 2, INK)
        if h2:
            draw_text(cv, x, hy + 15, h2, 2, INK)
            by = hy + 34
        else:
            by = hy + 19
        draw_para(cv, x, by, body, 2, INK, 19)


# ---------------------------------------------------------------------------
# World map. Continents are coarse polygons of my own, plotted in a
# simple equirectangular projection (lon -170..190, lat -55..75).
# ---------------------------------------------------------------------------

CONTINENTS = [
    # North America
    [(-168, 66), (-140, 70), (-125, 72), (-110, 73), (-95, 80), (-85, 70),
     (-75, 62), (-60, 55), (-55, 47), (-70, 42), (-75, 35), (-80, 26),
     (-90, 21), (-97, 16), (-105, 20), (-115, 28), (-125, 40),
     (-125, 49), (-140, 60), (-155, 58), (-165, 60)],
    # South America
    [(-80, 10), (-70, 12), (-60, 8), (-50, 0), (-40, -5), (-35, -10),
     (-40, -20), (-50, -30), (-60, -35), (-70, -40), (-73, -50),
     (-70, -55), (-75, -40), (-80, -20), (-80, -5), (-82, 5)],
    # Europe
    [(-10, 36), (-9, 43), (-2, 48), (0, 50), (5, 53), (8, 57), (10, 59),
     (18, 56), (21, 55), (24, 59), (30, 60), (30, 70), (25, 71),
     (18, 69), (12, 66), (5, 60), (-5, 58), (-10, 52), (-10, 44)],
    # Africa
    [(-17, 15), (-10, 30), (0, 35), (10, 37), (20, 32), (32, 31),
     (35, 28), (40, 15), (48, 11), (51, 10), (44, 0), (40, -10),
     (35, -20), (32, -28), (28, -33), (20, -35), (15, -30), (12, -18),
     (13, -10), (9, 4), (0, 5), (-8, 5), (-15, 10)],
    # Asia
    [(30, 70), (40, 68), (50, 70), (60, 72), (70, 73), (80, 73),
     (90, 75), (100, 76), (110, 74), (120, 73), (130, 72), (140, 72),
     (150, 70), (160, 69), (170, 66), (162, 60), (158, 52), (150, 59),
     (142, 50), (140, 40), (135, 35), (130, 33), (127, 35), (122, 38),
     (120, 32), (115, 23), (110, 20), (108, 12), (105, 9), (100, 8),
     (97, 15), (95, 20), (92, 22), (88, 22), (85, 20), (80, 15),
     (77, 8), (75, 20), (72, 20), (68, 23), (65, 25), (60, 25),
     (57, 26), (52, 28), (50, 30), (48, 30), (44, 30), (40, 36),
     (36, 36), (33, 42), (30, 46), (28, 45), (30, 50), (32, 55),
     (35, 60), (40, 65)],
    # Australia
    [(113, -22), (114, -30), (115, -35), (120, -34), (125, -32),
     (130, -32), (135, -35), (140, -38), (145, -38), (150, -37),
     (153, -32), (153, -27), (150, -23), (146, -19), (142, -15),
     (142, -11), (137, -12), (135, -15), (132, -12), (130, -13),
     (126, -14), (122, -17), (118, -20), (114, -22)],
]


def _project(bx, by, bw, bh, lon, lat):
    x = bx + int((lon + 170) / 360.0 * bw)
    y = by + int((75 - lat) / 130.0 * bh)
    return (x, y)


def _fill_polygon(cv, pts, c):
    """Scanline fill of a simple polygon."""
    if not pts:
        return
    ys = [p[1] for p in pts]
    for y in range(min(ys), max(ys) + 1):
        xs = []
        n = len(pts)
        for i in range(n):
            x0, y0 = pts[i]
            x1, y1 = pts[(i + 1) % n]
            if (y0 <= y < y1) or (y1 <= y < y0):
                t = (y - y0) / float(y1 - y0)
                xs.append(x0 + t * (x1 - x0))
        xs.sort()
        for a, b in zip(xs[0::2], xs[1::2]):
            cv.hline(int(a), y, max(1, int(b) - int(a)), c)


def draw_map(cv, bx, by, bw, bh):
    cv.fill_rect(bx, by, bw, bh, MAPSEA)
    cv.rect_outline(bx, by, bw, bh, INK, 1)
    for cont in CONTINENTS:
        pts = [_project(bx, by, bw, bh, lon, lat) for lon, lat in cont]
        _fill_polygon(cv, pts, LAND)
        cv.polyline(pts + [pts[0]], LAND)
    # Numbered pins follow the ALSO list; plain dots for Gaza,
    # Singapore and Hormuz.
    pins = [
        (127.0, 37.5, "1"), (139.7, 35.7, "2"), (86.0, 26.7, "3"),
        (72.8, 19.0, "4"), (13.4, 52.5, "5"), (100.5, 13.7, "6"),
        (-9.1, 38.7, "7"), (-74.0, 40.7, "8"),
    ]
    dots = [(34.5, 31.5), (103.8, 1.4), (56.5, 26.5)]
    for lon, lat, num in pins:
        px, py = _project(bx, by, bw, bh, lon, lat)
        cv.circle(px, py, 7, RED)
        cv.circle(px, py, 6, WHITE)
        draw_text(cv, px - 3, py - 3, num, 1, RED)
    for lon, lat in dots:
        px, py = _project(bx, by, bw, bh, lon, lat)
        cv.circle(px, py, 4, RED)


def draw_also(cv):
    y = 748
    draw_text(cv, CX0, y, "WHERE IT HAPPENED", 2, RED)
    draw_map(cv, CX0, y + 20, 380, 150)
    ax = 428
    draw_text(cv, ax, y, "ALSO ON THIS DAY", 2, RED)
    items = [
        "SEOUL: SK hynix chief bought shares.",
        "TOKYO: Yen near 159 per dollar.",
        "JANAKPUR: Return train leaves at 1pm.",
        "MUMBAI: Shut for Guru Nanak Jayanti.",
        "BERLIN: Ifo 90.6, best since May 2023.",
        "BANGKOK: 1,000 plan a 16-km fuel march.",
        "LISBON: Unions rally as budget looms.",
        "NEW YORK: Sanofi to buy Insmed for $41B.",
    ]
    for i, txt in enumerate(items):
        draw_text(cv, ax, y + 22 + i * 17, "%d. %s" % (i + 1, txt), 2, INK)


def draw_date_check(cv):
    y = 934
    cv.hline(CX0, y, CX1 - CX0, INK)
    draw_text(cv, CX0, y + 8, "DATE CHECK - NOT TODAY, LEFT OUT ON PURPOSE",
              2, RED)
    draw_text(cv, CX0, y + 26,
              "HUANG REINSTATED - 23 NOV / WOMEN'S WORLD CUP - 23 NOV / "
              "EU SANCTIONS - 23 NOV", 2, INK)
    draw_text(cv, CX0, y + 44,
              "COP31 COLLAPSES - 22 NOV / VANUATU QUAKE - 23 NOV / "
              "GOMEZ RESIGNS - 23 NOV", 2, INK)


def build_page():
    cv = Canvas(W, H, PAPER)
    draw_frame(cv)
    draw_masthead(cv)
    draw_timeline(cv)
    cv.vline(512, 232, 228, INK)
    draw_headline_asia(cv)
    draw_headline_wallst(cv)
    draw_train_strip(cv)
    draw_small_stories(cv)
    cv.hline(CX0, 736, CX1 - CX0, INK)
    draw_also(cv)
    draw_date_check(cv)
    return cv


def main():
    outdir = os.environ.get("MAKEFUN_OUTPUT_DIR", "/output")
    os.makedirs(outdir, exist_ok=True)
    save_png(build_page(), os.path.join(outdir, "entry.png"))


if __name__ == "__main__":
    main()
