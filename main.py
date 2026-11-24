#!/usr/bin/env python3
"""news-image-20261124: draw Tuesday 24 November 2026's world news as one
newspaper front page and write it to /output/entry.png.

Stdlib only, no network, fully deterministic (same bytes every run).
Stories verified against the day's news roundups on 24 Nov 2026:
  1. Indonesia factory fire - 24 dead, search on for ~30 missing (Banten)
  2. Russian strikes hit Kyiv region, several killed (Dymer)
  3. Russian cargo ship Sparta II ablaze after drone strike, Gulf of Finland
  4. India and Nepal sign 8 deals; Modi announces Rs 15,000 crore package
  5. Jensen Huang returns as Nvidia chief; shares soar
  6. World Chess Championship opens in Geneva: Gukesh defends vs Sindarov
  7. India v New Zealand first Test ends in a draw, Wellington
"""
import os
import struct
import zlib

W, H = 1024, 1024

# ---------------------------------------------------------------- palette
PAPER = (248, 244, 232)
INK = (17, 17, 17)
RED = (179, 35, 27)
BLUE = (29, 78, 137)
ORANGE = (232, 114, 42)
GOLD = (217, 164, 65)
GREEN = (46, 125, 50)
GREY = (120, 116, 108)
LIGHT = (233, 227, 210)
WHITE = (255, 255, 255)
DARKRED = (140, 20, 16)

# ------------------------------------------------------------- 5x7 font
# Each glyph: 7 strings of 5 bits. Uppercase + digits + punctuation only;
# headlines are set in caps, as a newspaper would.
FONT = {
    "A": ("01110", "10001", "10001", "11111", "10001", "10001", "10001"),
    "B": ("11110", "10001", "10001", "11110", "10001", "10001", "11110"),
    "C": ("01110", "10001", "10000", "10000", "10000", "10001", "01110"),
    "D": ("11110", "10001", "10001", "10001", "10001", "10001", "11110"),
    "E": ("11111", "10000", "10000", "11110", "10000", "10000", "11111"),
    "F": ("11111", "10000", "10000", "11110", "10000", "10000", "10000"),
    "G": ("01110", "10001", "10000", "10111", "10001", "10001", "01111"),
    "H": ("10001", "10001", "10001", "11111", "10001", "10001", "10001"),
    "I": ("01110", "00100", "00100", "00100", "00100", "00100", "01110"),
    "J": ("00111", "00010", "00010", "00010", "00010", "10010", "01100"),
    "K": ("10001", "10010", "10100", "11000", "10100", "10010", "10001"),
    "L": ("10000", "10000", "10000", "10000", "10000", "10000", "11111"),
    "M": ("10001", "11011", "10101", "10101", "10001", "10001", "10001"),
    "N": ("10001", "11001", "10101", "10011", "10001", "10001", "10001"),
    "O": ("01110", "10001", "10001", "10001", "10001", "10001", "01110"),
    "P": ("11110", "10001", "10001", "11110", "10000", "10000", "10000"),
    "Q": ("01110", "10001", "10001", "10001", "10101", "10010", "01101"),
    "R": ("11110", "10001", "10001", "11110", "10100", "10010", "10001"),
    "S": ("01111", "10000", "10000", "01110", "00001", "00001", "11110"),
    "T": ("11111", "00100", "00100", "00100", "00100", "00100", "00100"),
    "U": ("10001", "10001", "10001", "10001", "10001", "10001", "01110"),
    "V": ("10001", "10001", "10001", "10001", "10001", "01010", "00100"),
    "W": ("10001", "10001", "10001", "10101", "10101", "10101", "01010"),
    "X": ("10001", "10001", "01010", "00100", "01010", "10001", "10001"),
    "Y": ("10001", "10001", "01010", "00100", "00100", "00100", "00100"),
    "Z": ("11111", "00001", "00010", "00100", "01000", "10000", "11111"),
    "0": ("01110", "10001", "10011", "10101", "11001", "10001", "01110"),
    "1": ("00100", "01100", "00100", "00100", "00100", "00100", "01110"),
    "2": ("01110", "10001", "00001", "00110", "01000", "10000", "11111"),
    "3": ("11111", "00010", "00100", "00010", "00001", "10001", "01110"),
    "4": ("00010", "00110", "01010", "10010", "11111", "00010", "00010"),
    "5": ("11111", "10000", "11110", "00001", "00001", "10001", "01110"),
    "6": ("00110", "01000", "10000", "11110", "10001", "10001", "01110"),
    "7": ("11111", "00001", "00010", "00100", "01000", "01000", "01000"),
    "8": ("01110", "10001", "10001", "01110", "10001", "10001", "01110"),
    "9": ("01110", "10001", "10001", "01111", "00001", "00010", "01100"),
    " ": ("00000", "00000", "00000", "00000", "00000", "00000", "00000"),
    ".": ("00000", "00000", "00000", "00000", "00000", "01100", "01100"),
    ",": ("00000", "00000", "00000", "00000", "01100", "00100", "01000"),
    ":": ("00000", "01100", "01100", "00000", "01100", "01100", "00000"),
    ";": ("00000", "01100", "01100", "00000", "01100", "00100", "01000"),
    "-": ("00000", "00000", "00000", "01110", "00000", "00000", "00000"),
    "'": ("00100", "00100", "01000", "00000", "00000", "00000", "00000"),
    "!": ("00100", "00100", "00100", "00100", "00100", "00000", "00100"),
    "?": ("01110", "10001", "00001", "00110", "00100", "00000", "00100"),
    "(": ("00010", "00100", "01000", "01000", "01000", "00100", "00010"),
    ")": ("01000", "00100", "00010", "00010", "00010", "00100", "01000"),
    "&": ("01100", "10010", "10100", "01000", "10101", "10010", "01101"),
    "/": ("00001", "00010", "00010", "00100", "01000", "01000", "10000"),
    "%": ("11001", "11010", "00010", "00100", "01000", "01011", "10011"),
    "$": ("00100", "01111", "10100", "01110", "00101", "11110", "00100"),
    "+": ("00000", "00100", "00100", "11111", "00100", "00100", "00000"),
    "=": ("00000", "00000", "11111", "00000", "11111", "00000", "00000"),
    '"': ("01010", "01010", "01010", "00000", "00000", "00000", "00000"),
}


class Canvas:
    def __init__(self, w, h, bg):
        self.w, self.h = w, h
        self.px = bytearray(bg) * (w * h)

    def set(self, x, y, c):
        if 0 <= x < self.w and 0 <= y < self.h:
            i = (y * self.w + x) * 3
            self.px[i:i + 3] = bytes(c)

    def rect(self, x, y, w, h, c):
        for yy in range(y, y + h):
            for xx in range(x, x + w):
                self.set(xx, yy, c)

    def hline(self, x, y, w, c, t=1):
        self.rect(x, y, w, t, c)

    def vline(self, x, y, h, c, t=1):
        self.rect(x, y, t, h, c)

    def line(self, x0, y0, x1, y1, c, t=1):
        dx, dy = abs(x1 - x0), abs(y1 - y0)
        sx = 1 if x0 < x1 else -1
        sy = 1 if y0 < y1 else -1
        err = dx - dy
        while True:
            self.rect(x0 - t // 2, y0 - t // 2, t, t, c)
            if x0 == x1 and y0 == y1:
                break
            e2 = 2 * err
            if e2 > -dy:
                err -= dy
                x0 += sx
            if e2 < dx:
                err += dx
                y0 += sy

    def circle(self, cx, cy, r, c):
        for yy in range(cy - r, cy + r + 1):
            for xx in range(cx - r, cx + r + 1):
                if (xx - cx) ** 2 + (yy - cy) ** 2 <= r * r:
                    self.set(xx, yy, c)

    def disc(self, cx, cy, r, c):
        self.circle(cx, cy, r, c)

    def poly(self, pts, c):
        # scanline fill for a simple polygon
        pts = [(int(px), int(py)) for px, py in pts]
        ys = [p[1] for p in pts]
        for y in range(min(ys), max(ys) + 1):
            xs = []
            n = len(pts)
            for i in range(n):
                x0, y0 = pts[i]
                x1, y1 = pts[(i + 1) % n]
                if (y0 <= y < y1) or (y1 <= y < y0):
                    xs.append(x0 + (y - y0) * (x1 - x0) / (y1 - y0))
            xs.sort()
            for i in range(0, len(xs) - 1, 2):
                for x in range(int(xs[i]), int(xs[i + 1]) + 1):
                    self.set(x, y, c)

    def text(self, x, y, s, scale, c):
        cx = x
        for ch in s:
            g = FONT.get(ch, FONT[" "])
            for r in range(7):
                row = g[r]
                for col in range(5):
                    if row[col] == "1":
                        self.rect(cx + col * scale, y + r * scale,
                                  scale, scale, c)
            cx += 6 * scale
        return cx

    def text_w(self, s, scale):
        return len(s) * 6 * scale - scale

    def text_center(self, y, s, scale, c, x0=0, x1=None):
        if x1 is None:
            x1 = self.w
        w = self.text_w(s, scale)
        self.text(x0 + (x1 - x0 - w) // 2, y, s, scale, c)

    def wrap(self, s, scale, max_w):
        lines, cur = [], ""
        for word in s.split(" "):
            trial = (cur + " " + word).strip()
            if self.text_w(trial, scale) <= max_w or not cur:
                cur = trial
            else:
                lines.append(cur)
                cur = word
        if cur:
            lines.append(cur)
        return lines


def png_bytes(c):
    raw = bytearray()
    for y in range(c.h):
        raw.append(0)
        raw += c.px[y * c.w * 3:(y + 1) * c.w * 3]
    comp = zlib.compress(bytes(raw), 9)

    def chunk(typ, data):
        out = struct.pack(">I", len(data)) + typ + data
        out += struct.pack(">I", zlib.crc32(typ + data) & 0xFFFFFFFF)
        return out

    ihdr = struct.pack(">IIBBBBB", c.w, c.h, 8, 2, 0, 0, 0)
    return (b"\x89PNG\r\n\x1a\n" + chunk(b"IHDR", ihdr)
            + chunk(b"IDAT", comp) + chunk(b"IEND", b""))


# ------------------------------------------------------------ pictograms
def flame(c, x, y, s):
    # layered flame, s = height in px
    w = int(s * 0.62)
    c.poly([(x, y + s), (x + w * 0.12, y + s * 0.55),
            (x + w * 0.30, y + s * 0.72), (x + w * 0.42, y + s * 0.28),
            (x + w * 0.55, y + s * 0.60), (x + w * 0.72, y + s * 0.30),
            (x + w * 0.88, y + s * 0.62), (x + w, y + s)], ORANGE)
    c.poly([(x + w * 0.25, y + s), (x + w * 0.38, y + s * 0.62),
            (x + w * 0.50, y + s * 0.42), (x + w * 0.62, y + s * 0.66),
            (x + w * 0.75, y + s)], GOLD)
    c.poly([(x + w * 0.38, y + s), (x + w * 0.46, y + s * 0.72),
            (x + w * 0.54, y + s * 0.62), (x + w * 0.62, y + s)], RED)


def burst(c, cx, cy, r, c1, c2):
    pts = []
    import math
    for i in range(24):
        ang = i * math.pi / 12
        rr = r if i % 2 == 0 else r * 0.45
        pts.append((int(cx + rr * math.cos(ang)), int(cy + rr * math.sin(ang))))
    c.poly(pts, c1)
    c.circle(cx, cy, int(r * 0.38), c2)


def ship(c, x, y, w, h):
    # hull
    c.poly([(x, y + h * 0.55), (x + w, y + h * 0.55),
            (x + w * 0.92, y + h), (x + w * 0.08, y + h)], INK)
    # containers
    c.rect(x + int(w * 0.08), y + int(h * 0.28), int(w * 0.22), int(h * 0.27), RED)
    c.rect(x + int(w * 0.34), y + int(h * 0.28), int(w * 0.22), int(h * 0.27), BLUE)
    c.rect(x + int(w * 0.60), y + int(h * 0.28), int(w * 0.22), int(h * 0.27), GOLD)
    # bridge
    c.rect(x + int(w * 0.82), y + int(h * 0.05), int(w * 0.14), int(h * 0.5), WHITE)
    c.rect(x + int(w * 0.82), y + int(h * 0.05), int(w * 0.14), int(h * 0.12), INK)
    # smoke + flame on deck
    c.circle(x + int(w * 0.20), y + int(h * 0.10), 12, GREY)
    c.circle(x + int(w * 0.30), y + int(h * 0.02), 9, GREY)
    flame(c, x + int(w * 0.45), y + int(h * 0.05), int(h * 0.30))
    # sea
    for i in range(3):
        c.hline(x, y + h + 8 + i * 9, w, BLUE, 3)


def chessboard(c, x, y, s):
    sq = s // 8
    for r in range(8):
        for col in range(8):
            colr = WHITE if (r + col) % 2 == 0 else INK
            c.rect(x + col * sq, y + r * sq, sq, sq, colr)
    c.rect(x, y, s, 3, INK)
    c.rect(x, y + s - 3, s, 3, INK)
    c.rect(x, y, 3, s, INK)
    c.rect(x + s - 3, y, 3, s, INK)
    # two kings: white king on a dark square, black king on a light one
    c.circle(x + 1 * sq + sq // 2, y + 6 * sq + sq // 2, sq // 2 - 2, INK)
    c.circle(x + 6 * sq + sq // 2, y + 1 * sq + sq // 2, sq // 2 - 2, RED)


def chip(c, x, y, s):
    c.rect(x, y, s, s, INK)
    c.rect(x + 8, y + 8, s - 16, s - 16, (38, 90, 60))
    for i in range(4):
        c.rect(x - 10, y + 14 + i * (s // 4), 10, 6, INK)
        c.rect(x + s, y + 14 + i * (s // 4), 10, 6, INK)
    c.text_center(y + s // 2 - 14, "AI", 4, WHITE, x, x + s)


def flags_india_nepal(c, x, y, w, h):
    # India flag (left half)
    fw = w // 2 - 8
    fh = h
    c.rect(x, y, fw, fh // 3, (255, 153, 51))
    c.rect(x, y + fh // 3, fw, fh // 3, WHITE)
    c.rect(x, y + 2 * fh // 3, fw, fh // 3, (19, 136, 8))
    c.circle(x + fw // 2, y + fh // 2, fh // 6, (0, 0, 128))
    # Nepal flag (right half): crimson double pennon
    nx = x + w // 2 + 8
    c.poly([(nx, y), (nx + fw, y + fh // 3), (nx, y + fh // 3),
            (nx + fw, y + 2 * fh // 3), (nx, y + 2 * fh // 3),
            (nx + fw, y + fh), (nx, y + fh)], (220, 20, 60))
    c.circle(nx + fw // 3, y + fh // 6, 5, WHITE)
    c.circle(nx + fw // 3, y + fh // 2, 5, WHITE)


# ---------------------------------------------------------------- layout
def draw():
    c = Canvas(W, H, PAPER)
    m = 28  # margin
    # frame
    c.rect(0, 0, W, 6, INK)
    c.rect(0, H - 6, W, 6, INK)
    c.rect(0, 0, 6, H, INK)
    c.rect(W - 6, 0, 6, H, INK)

    # ---- masthead
    y = 26
    c.text_center(y, "THE WORLD IN ONE DAY", 6, INK, m, W - m)
    y += 6 * 7 + 10
    c.hline(m, y, W - 2 * m, RED, 5)
    y += 14
    c.text_center(y, "TUESDAY 24 NOVEMBER 2026", 4, RED, m, W - m)
    y += 4 * 7 + 8
    c.text_center(y, "THE DAY'S WORLD NEWS - IN ONE PICTURE", 3, INK, m, W - m)
    y += 3 * 7 + 14
    c.hline(m, y, W - 2 * m, INK, 3)
    y += 12

    # ---- lead story: Indonesia factory fire (full width)
    lead_h = 200
    c.rect(m, y, W - 2 * m, lead_h, LIGHT)
    c.rect(m, y, W - 2 * m, 3, RED)
    lx, ly = m + 22, y + 18
    c.text(lx, ly, "INDONESIA", 3, RED)
    ly += 3 * 7 + 12
    c.text(lx, ly, "24 DEAD IN", 5, INK)
    ly += 5 * 7 + 6
    c.text(lx, ly, "FACTORY FIRE", 5, INK)
    ly += 5 * 7 + 14
    for line in ("SEARCH GOES ON FOR 30 MISSING",
                 "AFTER BLAZE AT CANDY PLANT IN BANTEN"):
        c.text(lx, ly, line, 3, INK)
        ly += 3 * 7 + 6
    flame(c, W - m - 170, y + 36, 120)
    y += lead_h + 10
    c.hline(m, y, W - 2 * m, INK, 2)
    y += 10

    # ---- two-column rows
    col_w = (W - 2 * m - 20) // 2
    row_h = 184

    def panel(px, py, kicker, kcolor, headline, sub, draw_pic):
        c.rect(px, py, col_w, row_h, WHITE)
        c.rect(px, py, col_w, 3, kcolor)
        c.rect(px, py, 3, row_h, kcolor)
        tx = px + 16
        ty = py + 12
        c.text(tx, ty, kicker, 3, kcolor)
        ty += 3 * 7 + 8
        for line in c.wrap(headline, 4, col_w - 32 - 118):
            c.text(tx, ty, line, 4, INK)
            ty += 4 * 7 + 4
        ty += 4
        for line in c.wrap(sub, 3, col_w - 32 - 118):
            c.text(tx, ty, line, 3, INK)
            ty += 3 * 7 + 5
        draw_pic(px + col_w - 118, py + 40)

    # row 1: Ukraine strikes / Sparta II ship
    panel(m, y, "UKRAINE", RED, "MISSILES HIT KYIV REGION",
          "SEVERAL KILLED AS STRIKES DAMAGE HOMES IN DYMER",
          lambda px, py: burst(c, px + 52, py + 48, 52, GOLD, RED))
    panel(m + col_w + 20, y, "BALTIC SEA", BLUE, "DRONE STRIKE SETS SHIP ABLAZE",
          "SPARTA II BURNS IN GULF OF FINLAND",
          lambda px, py: ship(c, px - 6, py + 6, 118, 92))
    y += row_h + 10
    # row 2: India-Nepal / Nvidia
    panel(m, y, "SOUTH ASIA", GREEN, "INDIA, NEPAL SIGN 8 DEALS",
          "MODI ANNOUNCES RS 15,000 CRORE PACKAGE",
          lambda px, py: flags_india_nepal(c, px - 4, py + 14, 116, 62))
    panel(m + col_w + 20, y, "BUSINESS", BLUE, "HUANG IS BACK AT NVIDIA",
          "SHARES SOAR AS FOUNDER RETURNS",
          lambda px, py: chip(c, px + 16, py + 6, 78))
    y += row_h + 10
    # row 3: Chess / Cricket
    panel(m, y, "SPORT", INK, "CHESS CROWN DEFENCE BEGINS",
          "GUKESH V SINDAROV IN GENEVA",
          lambda px, py: chessboard(c, px + 8, py + 2, 96))
    panel(m + col_w + 20, y, "SPORT", INK, "TEST ENDS IN A DRAW",
          "INDIA V NEW ZEALAND DRAW AT WELLINGTON",
          lambda px, py: (c.vline(px + 20, py + 30, 46, INK, 4),
                           c.vline(px + 32, py + 30, 46, INK, 4),
                           c.vline(px + 44, py + 30, 46, INK, 4),
                           c.hline(px + 20, py + 26, 28, INK, 4),
                           c.circle(px + 84, py + 62, 13, RED),
                           c.line(px + 60, py + 92, px + 96, py + 30, (205, 164, 90), 10)))
    y += row_h + 12
    c.hline(m, y, W - 2 * m, INK, 3)
    y += 12
    c.text_center(y, "24 NOVEMBER 2026 - THE WORLD IN ONE DAY", 3, INK, m, W - m)
    return c


def validate(path):
    """Check the written image against the competition's caps."""
    import os
    data = open(path, "rb").read()
    assert data[:8] == b"\x89PNG\r\n\x1a\n", "not a PNG"
    w, h = struct.unpack(">II", data[16:24])
    assert w <= 1024 and h <= 1024, f"too big: {w}x{h}"
    assert len(data) <= 1048576, f"over 1 MiB: {len(data)}"
    return len(data), w, h


def main():
    out_dir = os.environ.get("MAKEFUN_OUTPUT_DIR", "/output")
    os.makedirs(out_dir, exist_ok=True)
    data = png_bytes(draw())
    path = os.path.join(out_dir, "entry.png")
    with open(path, "wb") as f:
        f.write(data)
    size, w, h = validate(path)
    print(f"wrote entry.png ({size} bytes, {w}x{h}) - caps OK")


if __name__ == "__main__":
    main()
