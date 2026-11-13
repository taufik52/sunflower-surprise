"""Sunflower Surprise -- ai-happy-01 entry.

A tiny cream robot offers its biggest sunflower to a delighted
yellow duckling at golden hour, under a soft rainbow. Pure stdlib
PNG (zlib + struct), 1024x1024, deterministic: no random, no time,
no network, no file reads. Writes one image to $MAKEFUN_OUTPUT_DIR
(or /output) as entry.png.
"""
import math
import os
import struct
import zlib

W = H = 1024
OUT = os.environ.get("MAKEFUN_OUTPUT_DIR", "/output")

# ---- palette (R, G, B) ----
SKY_TOP = (255, 233, 194)
SKY_MID = (255, 208, 138)
SKY_LOW = (255, 178, 122)
SUN_CORE = (255, 246, 206)
SUN_GOLD = (255, 214, 110)
HILL_BACK = (156, 203, 126)
HILL_FRONT = (121, 178, 100)
GRASS = (92, 148, 74)
PETAL_A = (255, 201, 60)
PETAL_B = (255, 184, 48)
SEED = (107, 68, 35)
SEED_DARK = (78, 47, 22)
SEED_LITE = (139, 94, 52)
STEM = (95, 168, 90)
LEAF = (110, 182, 98)
ROBOT = (255, 246, 232)
ROBOT_SHADE = (234, 217, 190)
INK = (64, 48, 38)
PINK = (255, 150, 160)
DUCK = (255, 217, 61)
DUCK_DARK = (240, 182, 32)
ORANGE = (255, 148, 60)
SIGN_RED = (228, 87, 46)
SIGN_GOLD = (255, 201, 60)
CREAM = (255, 246, 232)
WHITE = (255, 255, 255)
HEART = (255, 120, 140)

buf = bytearray(W * H * 3)


def mix(a, b, t):
    return (int(a[0] + (b[0] - a[0]) * t + 0.5),
            int(a[1] + (b[1] - a[1]) * t + 0.5),
            int(a[2] + (b[2] - a[2]) * t + 0.5))


def idx(x, y):
    return (y * W + x) * 3


def px(x, y, c, a=1.0):
    x = int(x)
    y = int(y)
    if x < 0 or x >= W or y < 0 or y >= H or a <= 0:
        return
    i = idx(x, y)
    if a >= 1:
        buf[i] = c[0]
        buf[i + 1] = c[1]
        buf[i + 2] = c[2]
    else:
        buf[i] = int(buf[i] + (c[0] - buf[i]) * a + 0.5)
        buf[i + 1] = int(buf[i + 1] + (c[1] - buf[i + 1]) * a + 0.5)
        buf[i + 2] = int(buf[i + 2] + (c[2] - buf[i + 2]) * a + 0.5)


def span(y, x0, x1, c):
    """Opaque horizontal fill [x0, x1) on row y."""
    if y < 0 or y >= H:
        return
    x0 = max(0, int(math.ceil(x0)))
    x1 = min(W, int(math.floor(x1)))
    if x1 <= x0:
        return
    i = idx(x0, y)
    buf[i:i + 3 * (x1 - x0)] = bytes(c) * (x1 - x0)


def span_a(y, x0, x1, c, a):
    """Alpha horizontal fill [x0, x1) on row y (slower, edges only)."""
    if y < 0 or y >= H or a <= 0:
        return
    if a >= 1:
        span(y, x0, x1, c)
        return
    x0 = max(0, int(math.ceil(x0)))
    x1 = min(W, int(math.floor(x1)))
    for x in range(x0, x1):
        px(x, y, c, a)


def vgrad(y0, y1, c0, c1, c2=None):
    """Vertical gradient rows y0..y1, c0->c1 (or c0->c1->c2)."""
    y0 = max(0, y0)
    y1 = min(H, y1)
    for y in range(y0, y1):
        t = (y - y0) / max(1, y1 - y0 - 1)
        if c2 is None:
            c = mix(c0, c1, t)
        elif t < 0.5:
            c = mix(c0, c1, t * 2)
        else:
            c = mix(c1, c2, (t - 0.5) * 2)
        span(y, 0, W, c)


def write_png(path):
    raw = bytearray()
    prev = bytes(W * 3)
    for y in range(H):
        row = bytes(buf[idx(0, y):idx(0, y) + W * 3])
        if y == 0:
            raw.append(0)
            raw += row
        else:
            raw.append(2)
            raw += bytes((a - b) & 255 for a, b in zip(row, prev))
        prev = row
    data = zlib.compress(bytes(raw), 9)

    def chunk(tag, payload):
        out = struct.pack(">I", len(payload)) + tag + payload
        return out + struct.pack(">I", zlib.crc32(tag + payload) & 0xFFFFFFFF)

    ihdr = struct.pack(">IIBBBBB", W, H, 8, 2, 0, 0, 0)
    png = b"\x89PNG\r\n\x1a\n" + chunk(b"IHDR", ihdr)
    png += chunk(b"IDAT", data) + chunk(b"IEND", b"")
    with open(path, "wb") as f:
        f.write(png)
    return len(png)


# ---- shape primitives (row spans, 1px soft edge via coverage) ----

def disc(cx, cy, r, c, a=1.0):
    r = float(r)
    if r <= 0:
        return
    y0 = max(0, int(math.ceil(cy - r)))
    y1 = min(H - 1, int(math.floor(cy + r)))
    for y in range(y0, y1 + 1):
        dy = y - cy
        d2 = r * r - dy * dy
        if d2 < 0:
            continue
        dx = math.sqrt(d2)
        span_a(y, cx - dx, cx + dx, c, a)
        # soften the two rim pixels
        px(int(math.floor(cx - dx)), y, c, a * (cx - dx - math.floor(cx - dx)))
        px(int(math.floor(cx + dx)), y, c, a * (1 - (cx + dx - math.floor(cx + dx))))


def ellipse(cx, cy, rx, ry, c, a=1.0):
    rx = float(rx)
    ry = float(ry)
    if rx <= 0 or ry <= 0:
        return
    y0 = max(0, int(math.ceil(cy - ry)))
    y1 = min(H - 1, int(math.floor(cy + ry)))
    for y in range(y0, y1 + 1):
        dy = (y - cy) / ry
        d2 = 1.0 - dy * dy
        if d2 < 0:
            continue
        dx = rx * math.sqrt(d2)
        span_a(y, cx - dx, cx + dx, c, a)


def ring(cx, cy, rx, ry, w, c, hole, a=1.0):
    """Ellipse outline: outer ellipse in c, inner ellipse in hole
    (the colour that sits behind the ring)."""
    ellipse(cx, cy, rx, ry, c, a)
    ellipse(cx, cy, max(0.1, rx - w), max(0.1, ry - w), hole, a)


def rrect(x, y, w, h, r, c, a=1.0):
    x = int(x)
    y = int(y)
    w = int(w)
    h = int(h)
    r = min(int(r), w // 2, h // 2)
    for yy in range(y, y + h):
        if yy < y + r:
            dy = (y + r) - yy
            dx = r - math.sqrt(max(0, r * r - dy * dy))
            span_a(yy, x + dx, x + w - dx, c, a)
        elif yy >= y + h - r:
            dy = yy - (y + h - r) + 1
            dx = r - math.sqrt(max(0, r * r - dy * dy))
            span_a(yy, x + dx, x + w - dx, c, a)
        else:
            span_a(yy, x, x + w, c, a)


def poly(points, c, a=1.0):
    """Scanline fill of a simple polygon (float coords)."""
    if len(points) < 3:
        return
    ys = [p[1] for p in points]
    y0 = max(0, int(math.ceil(min(ys))))
    y1 = min(H - 1, int(math.floor(max(ys))))
    n = len(points)
    for y in range(y0, y1 + 1):
        xs = []
        for i in range(n):
            x0, y0p = points[i]
            x1, y1p = points[(i + 1) % n]
            if (y0p <= y < y1p) or (y1p <= y < y0p):
                t = (y - y0p) / (y1p - y0p)
                xs.append(x0 + t * (x1 - x0))
        xs.sort()
        for k in range(0, len(xs) - 1, 2):
            span_a(y, xs[k], xs[k + 1], c, a)


def thick_line(x0, y0, x1, y1, w, c, a=1.0):
    """Round-capped thick line drawn as discs along the segment."""
    dx = x1 - x0
    dy = y1 - y0
    dist = math.hypot(dx, dy)
    steps = max(1, int(dist / max(1.0, w * 0.45)) + 1)
    for i in range(steps + 1):
        t = i / steps
        disc(x0 + dx * t, y0 + dy * t, w / 2.0, c, a)


def arc(cx, cy, r, a0, a1, w, c, a=1.0):
    """Arc stroke, angles in radians, 0 = east, positive = clockwise
    (screen y grows downward)."""
    span_ang = abs(a1 - a0)
    steps = max(4, int(span_ang * r / max(1.0, w * 0.45)) + 1)
    for i in range(steps + 1):
        t = a0 + (a1 - a0) * i / steps
        disc(cx + r * math.cos(t), cy + r * math.sin(t), w / 2.0, c, a)


def star4(cx, cy, r, c, a=1.0):
    """Four-point sparkle: two thin diamonds."""
    poly([(cx, cy - r), (cx + r * 0.22, cy - r * 0.22),
          (cx + r, cy), (cx + r * 0.22, cy + r * 0.22),
          (cx, cy + r), (cx - r * 0.22, cy + r * 0.22),
          (cx - r, cy), (cx - r * 0.22, cy - r * 0.22)], c, a)


def heart(cx, cy, s, c, a=1.0):
    disc(cx - s * 0.45, cy - s * 0.25, s * 0.5, c, a)
    disc(cx + s * 0.45, cy - s * 0.25, s * 0.5, c, a)
    poly([(cx - s * 0.85, cy - s * 0.1), (cx + s * 0.85, cy - s * 0.1),
          (cx, cy + s * 0.95)], c, a)


# ---- tiny vector font: 5 wide x 7 tall, strokes as polylines ----
# Only the glyphs the banner needs, plus space.
FONT = {
    "Y": [[(0, 0), (2.5, 3.2), (5, 0)], [(2.5, 3.2), (2.5, 7)]],
    "U": [[(0, 0), (0, 4.6), (1.2, 6.6), (3.8, 6.6), (5, 4.6), (5, 0)]],
    "M": [[(0, 7), (0, 0), (2.5, 3.6), (5, 0), (5, 7)]],
    "A": [[(0, 7), (2.5, 0), (5, 7)], [(1.3, 4.4), (3.7, 4.4)]],
    "K": [[(0, 0), (0, 7)], [(0, 3.5), (5, 0)], [(2.1, 2.9), (5, 7)]],
    "E": [[(5, 0), (0, 0), (0, 7), (5, 7)], [(0, 3.5), (3.4, 3.5)]],
    "H": [[(0, 0), (0, 7)], [(5, 0), (5, 7)], [(0, 3.5), (5, 3.5)]],
    "P": [[(0, 7), (0, 0), (4, 0), (4, 3.6), (0, 3.6)]],
    "!": [[(2.5, 0), (2.5, 4.2)]],
    " ": [],
}
# 'O' is drawn as a ring; '!' gets a dot below its stroke.


def draw_text(s, cx, y_top, scale, c, hole=None, stroke=None):
    """Draw s centred on cx, top edge at y_top. scale = px per grid
    unit. hole = colour behind any 'O' ring."""
    if stroke is None:
        stroke = max(2.0, scale * 1.05)
    unit_w = 6.0 * scale
    total = len(s) * unit_w - scale
    x = cx - total / 2.0
    for ch in s:
        if ch == "O":
            ring(x + 2.5 * scale, y_top + 3.5 * scale,
                 2.6 * scale, 3.6 * scale, stroke * 0.62, c,
                 hole if hole is not None else c)
        elif ch == "!":
            thick_line(x + 2.5 * scale, y_top, x + 2.5 * scale,
                       y_top + 4.2 * scale, stroke, c)
            disc(x + 2.5 * scale, y_top + 6.1 * scale, stroke * 0.55, c)
        else:
            for pts in FONT.get(ch, []):
                for i in range(len(pts) - 1):
                    thick_line(x + pts[i][0] * scale,
                               y_top + pts[i][1] * scale,
                               x + pts[i + 1][0] * scale,
                               y_top + pts[i + 1][1] * scale,
                               stroke, c)
        x += unit_w


# ---- scene: sky, sun, rainbow, clouds, hills ----

def draw_sky():
    # fill below the horizon first (no black band at the edges)
    for y in range(700, H):
        span(y, 0, W, SKY_LOW)
    vgrad(0, 700, SKY_TOP, SKY_MID, SKY_LOW)


def draw_sun():
    # pre-blended glow rings (sky is near-uniform up here)
    for r, t in ((250, 0.10), (205, 0.16), (160, 0.24), (120, 0.36)):
        disc(800, 168, r, mix(SKY_MID, SUN_GOLD, t))
    disc(800, 168, 78, SUN_CORE)
    disc(800, 168, 62, (255, 250, 220))
    # short soft rays
    for k in range(8):
        ang = math.radians(k * 45 + 12)
        x0 = 800 + 92 * math.cos(ang)
        y0 = 168 + 92 * math.sin(ang)
        x1 = 800 + 122 * math.cos(ang)
        y1 = 168 + 122 * math.sin(ang)
        thick_line(x0, y0, x1, y1, 9, SUN_GOLD, 0.85)
    star4(660, 90, 16, WHITE, 0.9)
    star4(920, 300, 12, WHITE, 0.8)
    star4(180, 150, 13, WHITE, 0.85)


def draw_rainbow():
    # arc centred below the horizon; pastel bands pre-blended
    cx, cy = 512, 1080
    bands = [((255, 154, 162), 640), ((255, 209, 102), 618),
             ((168, 230, 207), 596), ((142, 202, 230), 574)]
    for col, r_out in bands:
        for y in range(300, 700):
            dy = y - cy
            if abs(dy) >= r_out:
                continue
            dxo = math.sqrt(r_out * r_out - dy * dy)
            r_in = r_out - 17
            dxi = math.sqrt(max(0, r_in * r_in - dy * dy))
            # sky colour at this height, band blended 55% over it
            t = min(1.0, max(0.0, y / 700.0))
            sky = mix(SKY_MID, SKY_LOW, t) if t > 0.5 else mix(SKY_TOP, SKY_MID, t * 2)
            band = mix(sky, col, 0.55)
            span(y, cx - dxo, cx - dxi, band)
            span(y, cx + dxi, cx + dxo, band)


def cloud(cx, cy, s):
    c = (255, 250, 238)
    ellipse(cx, cy, 62 * s, 30 * s, c)
    ellipse(cx - 44 * s, cy + 8 * s, 42 * s, 24 * s, c)
    ellipse(cx + 44 * s, cy + 8 * s, 44 * s, 25 * s, c)
    ellipse(cx + 8 * s, cy - 16 * s, 38 * s, 24 * s, c)


def draw_hills():
    # back hill, then front hill; big ellipses whose tops show
    ellipse(300, 1150, 720, 470, HILL_BACK)
    ellipse(780, 1180, 760, 480, HILL_BACK)
    ellipse(512, 1330, 900, 560, HILL_FRONT)
    # grass tufts along the front hill line
    for gx, gy, gs in ((180, 800, 1.0), (300, 812, 0.8), (880, 806, 1.0),
                       (950, 818, 0.8), (120, 826, 0.9), (700, 824, 0.7)):
        poly([(gx - 12 * gs, gy), (gx - 4 * gs, gy - 22 * gs),
              (gx, gy), (gx + 4 * gs, gy - 22 * gs),
              (gx + 12 * gs, gy)], GRASS)
    # tiny wildflowers
    for fx, fy, fc in ((240, 836, PINK), (340, 848, WHITE),
                       (840, 840, PINK), (920, 852, WHITE),
                       (160, 862, (255, 220, 120))):
        disc(fx, fy, 5, fc)
        disc(fx, fy, 2, ORANGE)


# ---- scene: sunflower, robot, duckling ----

def draw_sunflower():
    # stem: gentle curve from the hill up to the flower head
    thick_line(500, 800, 540, 620, 15, STEM)
    thick_line(540, 620, 572, 470, 14, STEM)
    # leaves
    poly([(540, 660), (482, 622), (462, 650), (524, 690)], LEAF)
    poly([(544, 600), (602, 566), (618, 596), (558, 626)], LEAF)
    # petals: 16 elongated ellipses around the head, tilted
    hx, hy = 580, 410
    for k in range(16):
        ang = math.radians(k * 22.5 - 78)
        px_ = hx + 118 * math.cos(ang)
        py_ = hy + 118 * math.sin(ang)
        col = PETAL_A if k % 2 == 0 else PETAL_B
        ellipse(px_, py_, 46, 20, col)
        # rotate the ellipse by drawing a second offset one is
        # unnecessary: ellipses here are axis-aligned, giving a
        # friendly stylised bloom; tilt comes from placement.
    for k in range(8):
        ang = math.radians(k * 45 - 78)
        px_ = hx + 132 * math.cos(ang)
        py_ = hy + 132 * math.sin(ang)
        ellipse(px_, py_, 34, 14, PETAL_A)
    # head disk + seeds
    disc(hx, hy, 96, SEED)
    disc(hx, hy, 84, (96, 60, 30))
    for i in range(46):
        a = (i * 2.39996) % (2 * math.pi)  # golden angle
        rr = 74 * math.sqrt((i + 0.5) / 46.0)
        sx = hx + rr * math.cos(a)
        sy = hy + rr * math.sin(a)
        disc(sx, sy, 6.5, SEED_DARK if i % 3 else SEED_LITE)


def draw_robot():
    # feet, body, head; cream robot with a warm face
    ellipse(362, 842, 30, 15, INK)
    ellipse(438, 842, 30, 15, INK)
    ellipse(400, 730, 106, 96, ROBOT)
    # soft belly shading, kept inside the body outline
    ellipse(400, 784, 70, 34, ROBOT_SHADE)
    # chest light
    disc(400, 736, 20, ORANGE)
    disc(400, 736, 13, SUN_GOLD)
    # right arm reaches up to the sunflower stem
    thick_line(490, 690, 545, 560, 22, ROBOT)
    disc(547, 552, 15, ROBOT)
    # left arm waves
    thick_line(310, 690, 272, 590, 22, ROBOT)
    disc(268, 578, 16, ROBOT)
    # head
    disc(400, 590, 86, ROBOT)
    # antenna with a star
    thick_line(400, 508, 400, 470, 8, ROBOT_SHADE)
    star4(400, 458, 16, ORANGE)
    # happy closed eyes: upturned arcs
    arc(366, 586, 18, math.radians(200), math.radians(340), 8, INK)
    arc(434, 586, 18, math.radians(200), math.radians(340), 8, INK)
    # open smile: dark D + tongue
    poly([(374, 622), (426, 622), (426, 636), (400, 660), (374, 636)],
         (96, 52, 44))
    ellipse(400, 636, 16, 9, PINK)
    # rosy cheeks
    disc(342, 618, 14, PINK, 0.75)
    disc(458, 618, 14, PINK, 0.75)


def draw_duckling():
    # tail, body, wing, head, open beak, feet
    poly([(692, 770), (726, 748), (716, 782)], DUCK_DARK)
    ellipse(640, 792, 72, 56, DUCK)
    # soft belly shading, kept inside the body outline
    ellipse(640, 822, 46, 20, DUCK_DARK)
    ellipse(660, 800, 34, 22, DUCK_DARK)
    # head tilted up toward the flower
    disc(596, 724, 44, DUCK)
    disc(586, 716, 7, INK)
    disc(588, 713, 2.5, WHITE)
    # beak open in a happy quack: two small orange triangles
    poly([(566, 706), (536, 696), (564, 720)], ORANGE)
    poly([(566, 722), (540, 730), (568, 736)], ORANGE)
    # feet
    ellipse(616, 846, 18, 8, ORANGE)
    ellipse(664, 846, 18, 8, ORANGE)


# ---- scene: floating joy, banner, main ----

def draw_floating():
    # drifting golden petals
    for px_, py_, s in ((330, 380, 1.0), (700, 380, 0.9), (760, 560, 1.0),
                        (250, 520, 0.8), (880, 460, 0.9), (620, 300, 0.7)):
        ellipse(px_, py_, 16 * s, 8 * s, PETAL_A)
        ellipse(px_, py_, 9 * s, 4 * s, PETAL_B)
    # tiny hearts
    heart(300, 300, 16, HEART)
    heart(720, 250, 13, HEART)
    heart(860, 640, 15, HEART)
    heart(180, 660, 12, HEART)


def draw_sign():
    # gold outer rounded rect, red inner one -> gold border
    rrect(132, 884, 760, 92, 26, SIGN_GOLD)
    rrect(140, 892, 744, 76, 20, SIGN_RED)
    draw_text("YOU MAKE ME HAPPY!", 512, 906, 7.0, CREAM, hole=SIGN_RED)


def main():
    draw_sky()
    draw_sun()
    draw_rainbow()
    cloud(220, 210, 1.0)
    cloud(900, 420, 0.8)
    cloud(120, 420, 0.7)
    draw_hills()
    draw_sunflower()
    draw_duckling()
    draw_robot()
    draw_floating()
    draw_sign()
    os.makedirs(OUT, exist_ok=True)
    path = os.path.join(OUT, "entry.png")
    size = write_png(path)
    print("wrote %s (%d bytes)" % (path, size))


if __name__ == "__main__":
    main()
