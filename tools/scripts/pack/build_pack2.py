"""v2: marble/gold block retextures + continuous engraved ring bands + circular-script discs."""
import hashlib, io, json, math, os, random, struct, sys, zipfile, zlib

D = sys.argv[1]
SRC = os.path.join(D, "ChromaEndless-Pack.zip")
OUTZ = os.path.join(D, "ChromaEndless-Pack2.zip")

def png(px):
    h = len(px); w = len(px[0])
    raw = b"".join(b"\x00" + b"".join(struct.pack("BBBB", *p) for p in row) for row in px)
    ch = lambda t, d: struct.pack(">I", len(d)) + t + d + struct.pack(">I", zlib.crc32(t + d) & 0xFFFFFFFF)
    return b"\x89PNG\r\n\x1a\n" + ch(b"IHDR", struct.pack(">IIBBBBB", w, h, 8, 6, 0, 0, 0)) + ch(b"IDAT", zlib.compress(raw, 9)) + ch(b"IEND", b"")
def cl(v): return max(0, min(255, int(round(v))))

# ------------------------------------------------ tileable noise
def tnoise(n, cells, seed):
    r = random.Random(seed); g = [[r.random() for _ in range(cells)] for _ in range(cells)]
    out = [[0.0] * n for _ in range(n)]
    for y in range(n):
        for x in range(n):
            gx, gy = x * cells / n, y * cells / n; x0, y0 = int(gx), int(gy); fx, fy = gx - x0, gy - y0
            fx = fx * fx * (3 - 2 * fx); fy = fy * fy * (3 - 2 * fy)
            x1, y1 = (x0 + 1) % cells, (y0 + 1) % cells
            a = g[y0][x0] * (1 - fx) + g[y0][x1] * fx; b = g[y1][x0] * (1 - fx) + g[y1][x1] * fx
            out[y][x] = a * (1 - fy) + b * fy
    return out
def tfbm(n, seed):
    L = [tnoise(n, c, seed + i) for i, c in enumerate((2, 4, 8, 16))]
    return [[sum(l[y][x] * .5 ** i for i, l in enumerate(L)) / 1.875 for x in range(n)] for y in range(n)]

# ------------------------------------------------ marble & gold block textures (32 px, seamless)
N = 32
def marble(seed=1, a=1, b=2, base=(240, 237, 231), vein=(158, 156, 164), amp=7.0):
    f = tfbm(N, seed); f2 = tfbm(N, seed + 50)
    px = []
    for y in range(N):
        row = []
        for x in range(N):
            v = math.sin((x * a + y * b) * 2 * math.pi / N + f[y][x] * amp)
            t = max(0.0, 1 - abs(v) / .10); t2 = max(0.0, 1 - abs(v) / .45) * .16
            k = .95 + .06 * f2[y][x]
            c = [base[i] * k * (1 - t * .8 - t2) + vein[i] * (t * .8 + t2) for i in range(3)]
            row.append((cl(c[0]), cl(c[1]), cl(c[2]), 255))
        px.append(row)
    return px
def bevel(px, w=1, light=1.06, dark=.86):
    n = len(px); out = [list(r) for r in px]
    for y in range(n):
        for x in range(n):
            r, g, b, a = px[y][x]
            if x < w or y < w: f = light
            elif x >= n - w or y >= n - w: f = dark
            else: continue
            out[y][x] = (cl(r * f), cl(g * f), cl(b * f), a)
    return out
def engrave_circle(px, cx, cy, r, w=.7, f=.78, hi=1.06):
    n = len(px)
    for y in range(n):
        for x in range(n):
            d = math.hypot(x + .5 - cx, y + .5 - cy) - r
            if abs(d) < w:
                rr, g, b, a = px[y][x]; px[y][x] = (cl(rr * f), cl(g * f), cl(b * f), a)
            elif w <= d < w + .8:
                rr, g, b, a = px[y][x]; px[y][x] = (cl(rr * hi), cl(g * hi), cl(b * hi), a)
    return px
def gold_block():
    f = tfbm(N, 9); px = []
    for y in range(N):
        row = []
        for x in range(N):
            br = .5 + .5 * math.sin(y * 2 * math.pi / N * 9 + f[y][x] * 3)
            k = .80 + .12 * br + .08 * f[y][x]
            row.append((cl(250 * k), cl(200 * k), cl(78 * k), 255))
        px.append(row)
    px = bevel(px, 1, 1.18, .72)
    px = bevel([r[1:-1] for r in px[1:-1]], 1, .9, 1.1) if False else px
    engrave_circle(px, 16, 16, 9, .55, .82, 1.08); engrave_circle(px, 16, 16, 6.5, .45, .85, 1.06)
    return px
def pillar_side():
    m = marble(3, 0, 1, amp=5)
    out = []
    for y in range(N):
        row = []
        for x in range(N):
            fl = math.cos(((x + .5) % 8) / 8 * 2 * math.pi)      # 4 flutes
            f = .90 + .10 * (fl * .5 + .5)
            if (x % 8) in (0, 7): f *= .9
            r, g, b, a = m[y][x]; row.append((cl(r * f), cl(g * f), cl(b * f), 255))
        out.append(row)
    return out
def pillar_top():
    m = bevel(marble(4, 1, 1), 1, 1.04, .9)
    engrave_circle(m, 16, 16, 12, .6, .85); engrave_circle(m, 16, 16, 5, .5, .85)
    return m
def chiseled_side():
    m = bevel(marble(5, 2, 1), 2, 1.07, .84)
    engrave_circle(m, 16, 16, 9.5, .7, .8); engrave_circle(m, 16, 16, 4, .55, .82)
    for k in range(4):
        a = k * math.pi / 2 + math.pi / 4
        engrave_circle(m, 16 + 9.5 * math.cos(a), 16 + 9.5 * math.sin(a), 2.2, .45, .8)
    return m
def chiseled_top():
    m = bevel(marble(6, 1, 2), 2, 1.07, .84)
    for rr in (11, 7.5, 3):
        engrave_circle(m, 16, 16, rr, .55, .82)
    return m
def bricks():
    m = marble(7, 1, 1)
    out = []
    for y in range(N):
        row = []
        for x in range(N):
            off = 0 if (y // 8) % 2 == 0 else 8
            mort = (y % 8 == 7) or ((x + off) % 16 == 15)
            edge = (y % 8 == 0) or ((x + off) % 16 == 0)
            r, g, b, a = m[y][x]; f = .78 if mort else 1.05 if edge else 1.0
            row.append((cl(r * f), cl(g * f), cl(b * f), 255))
        out.append(row)
    return out

BLOCK_TEX = {
    "quartz_block_bottom": marble(1),
    "quartz_block_top": bevel(marble(2, 2, 1), 1, 1.04, .9),
    "quartz_block_side": bevel(marble(8, 1, 2), 1, 1.04, .9),
    "quartz_pillar": pillar_side(),
    "quartz_pillar_top": pillar_top(),
    "chiseled_quartz_block": chiseled_side(),
    "chiseled_quartz_block_top": chiseled_top(),
    "quartz_bricks": bricks(),
    "gold_block": gold_block(),
}

# ------------------------------------------------ circular-script helpers (anti-aliased strokes)
class Canvas:
    def __init__(self, w, h, bg=(0, 0, 0, 0)):
        self.w, self.h = w, h; self.px = [[bg] * w for _ in range(h)]; self.cov = [[0.0] * w for _ in range(h)]
    def cover(self, x, y, a):
        if 0 <= x < self.w and 0 <= y < self.h and a > 0: self.cov[y][x] = max(self.cov[y][x], min(1.0, a))
    def ring(self, cx, cy, r, w):
        for y in range(int(cy - r - w - 2), int(cy + r + w + 3)):
            for x in range(int(cx - r - w - 2), int(cx + r + w + 3)):
                d = abs(math.hypot(x + .5 - cx, y + .5 - cy) - r); self.cover(x, y, w / 2 + .5 - d)
    def arc(self, cx, cy, r, w, a0, a1):
        for y in range(int(cy - r - w - 2), int(cy + r + w + 3)):
            for x in range(int(cx - r - w - 2), int(cx + r + w + 3)):
                ang = math.atan2(y + .5 - cy, x + .5 - cx) % (2 * math.pi)
                lo, hi = a0 % (2 * math.pi), a1 % (2 * math.pi)
                inside = lo <= ang <= hi if lo <= hi else (ang >= lo or ang <= hi)
                if inside:
                    d = abs(math.hypot(x + .5 - cx, y + .5 - cy) - r); self.cover(x, y, w / 2 + .5 - d)
    def dot(self, cx, cy, r):
        for y in range(int(cy - r - 2), int(cy + r + 3)):
            for x in range(int(cx - r - 2), int(cx + r + 3)):
                self.cover(x, y, r + .5 - math.hypot(x + .5 - cx, y + .5 - cy))
    def line(self, x0, y0, x1, y1, w):
        L2 = (x1 - x0) ** 2 + (y1 - y0) ** 2 or 1
        for y in range(int(min(y0, y1)) - 3, int(max(y0, y1)) + 4):
            for x in range(int(min(x0, x1)) - 3, int(max(x0, x1)) + 4):
                t = max(0, min(1, ((x + .5 - x0) * (x1 - x0) + (y + .5 - y0) * (y1 - y0)) / L2))
                d = math.hypot(x + .5 - (x0 + t * (x1 - x0)), y + .5 - (y0 + t * (y1 - y0))); self.cover(x, y, w / 2 + .5 - d)
    def erase_disc(self, cx, cy, r):
        for y in range(int(cy - r - 1), int(cy + r + 2)):
            for x in range(int(cx - r - 1), int(cx + r + 2)):
                if 0 <= x < self.w and 0 <= y < self.h and math.hypot(x + .5 - cx, y + .5 - cy) < r: self.cov[y][x] = 0

def letter(cv, wx, wy, wr, ang, kind, rnd, size):
    """a 'letter' sitting on the rim of a word circle (centre wx,wy radius wr) at angle ang"""
    px_, py_ = wx + wr * math.cos(ang), wy + wr * math.sin(ang)
    inx, iny = wx + (wr - size * 1.25) * math.cos(ang), wy + (wr - size * 1.25) * math.sin(ang)
    if kind == 0:                                   # circle inside the word, touching
        cv.ring(inx, iny, size, 1.3)
    elif kind == 1:                                 # circle crossing the rim (arc)
        cv.ring(px_, py_, size, 1.3)
    elif kind == 2:                                 # deep circle
        cx_, cy_ = wx + (wr - size * 2.0) * math.cos(ang), wy + (wr - size * 2.0) * math.sin(ang); cv.ring(cx_, cy_, size, 1.3); inx, iny = cx_, cy_
    for j in range(rnd.choice((0, 0, 1, 2, 3))):    # dots
        b = ang + math.pi + (j - 1) * .55
        cv.dot(inx + size * .55 * math.cos(b), iny + size * .55 * math.sin(b), max(1.0, size * .16))
    if rnd.random() < .45:                          # a line leaving the letter outward-ish
        b = ang + math.pi + rnd.uniform(-.7, .7)
        cv.line(inx + size * math.cos(b), iny + size * math.sin(b), inx + size * 2.6 * math.cos(b), iny + size * 2.6 * math.sin(b), 1.1)
    if rnd.random() < .35:                          # vowel: small circle on the rim
        cv.ring(px_ + size * .9 * math.cos(ang + .6), py_ + size * .9 * math.sin(ang + .6), size * .35, 1.0)

def render(cv, col=(244, 200, 74), dark=(120, 80, 22), bg=None, shade=True):
    out = []
    for y in range(cv.h):
        row = []
        for x in range(cv.w):
            a = cv.cov[y][x]
            if bg is not None:
                br, bgc, bb, ba = bg[y][x]
                if a > 0:   # engraved: dark groove with light lower edge
                    row.append((cl(br * (1 - .55 * a)), cl(bgc * (1 - .58 * a)), cl(bb * (1 - .6 * a)), 255))
                else:
                    up = cv.cov[y - 1][x] if y > 0 else 0
                    row.append((cl(br * (1 + .12 * up)), cl(bgc * (1 + .12 * up)), cl(bb * (1 + .1 * up)), 255))
            else:
                if a > 0:
                    s_ = (.92 + .16 * ((x * 3 + y) % 9) / 9) if shade else 1
                    row.append((cl(col[0] * s_), cl(col[1] * s_), cl(col[2] * s_), cl(255 * a)))
                else:
                    near = any(0 <= x + dx < cv.w and 0 <= y + dy < cv.h and cv.cov[y + dy][x + dx] > .5 for dx, dy in ((1, 0), (0, 1), (-1, 0), (0, -1), (1, 1)))
                    row.append(dark + (190,) if near else (0, 0, 0, 0))
        out.append(row)
    return out

# ------------------------------------------------ floor disc: proper circular-script composition (256 px)
def glyph_disc(seed=4):
    S = 256; c = S / 2; cv = Canvas(S, S); rnd = random.Random(seed)
    R = 118
    cv.ring(c, c, R, 4.2); cv.ring(c, c, R - 7, 1.6)
    words = []
    n = 5
    for k in range(n):
        ang = k * 2 * math.pi / n + rnd.uniform(-.15, .15)
        wr = rnd.uniform(26, 34)
        dist_ = R - 7 - wr - 1.5                           # tangent to inner rim
        wx, wy = c + dist_ * math.cos(ang), c + dist_ * math.sin(ang)
        cv.ring(wx, wy, wr, 2.2); words.append((wx, wy, wr, ang))
        nl = rnd.randint(3, 5)
        for j in range(nl):
            la = ang + math.pi + (j - (nl - 1) / 2) * (2 * math.pi / (nl + 1)) * .9
            letter(cv, wx, wy, wr, la, rnd.choice((0, 1, 1, 2)), rnd, rnd.uniform(6, 9))
    # central sentence circle and connections
    cv.ring(c, c, 30, 2.4); cv.ring(c, c, 22, 1.2)
    for j in range(4):
        letter(cv, c, c, 30, j * math.pi / 2 + .4, rnd.choice((0, 1)), rnd, 6.5)
    for (wx, wy, wr, ang) in words:
        cv.line(c + 30 * math.cos(ang), c + 30 * math.sin(ang), wx - wr * math.cos(ang), wy - wr * math.sin(ang), 1.6)
    for k in range(48):
        a = k * math.pi / 24; cv.dot(c + (R + 0.0) * math.cos(a), c + (R + 0.0) * math.sin(a), 1.0) if False else None
    return render(cv)

# ------------------------------------------------ ring bands (128 x 128, band in the first 16 rows)
def band(base_px, seed, col_dark=True):
    W_, H_ = 128, 16; cv = Canvas(W_, H_); rnd = random.Random(seed)
    cv.line(0, 2, W_, 2, 1.0); cv.line(0, 13.5, W_, 13.5, 1.0); cv.line(0, 8, W_, 8, .8)
    x = 6
    while x < W_ - 6:
        r_ = rnd.uniform(3.2, 4.6)
        cv.erase_disc(x, 8, r_ + 1.2)
        cv.ring(x, 8, r_, 1.0)
        k = rnd.random()
        if k < .3: cv.dot(x, 8 - r_ * .35, 1.0)
        elif k < .55:
            cv.dot(x - 1.4, 8 + r_ * .3, .8); cv.dot(x + 1.4, 8 + r_ * .3, .8)
        elif k < .75: cv.line(x, 8 - r_, x + r_ * .9, 8 - r_ * 1.9, .9)
        else: cv.ring(x, 8 - r_, 1.4, .8)
        x += rnd.uniform(11, 15)
    strip = render(cv, bg=[row[:W_] for row in base_px[:H_]])
    full = [list(r) for r in base_px]
    for y in range(H_): full[y] = strip[y]
    return full
def big(px, n=128):
    s_ = n // len(px); return [[px[y // s_][x // s_] for x in range(n)] for y in range(n)]
gold_base = []
f = tfbm(128, 31)
for y in range(128):
    gold_base.append([(cl(250 * (.8 + .12 * (.5 + .5 * math.sin(x * .9 + f[y][x] * 4)) + .08 * f[y][x])),
                       cl(200 * (.8 + .12 * (.5 + .5 * math.sin(x * .9 + f[y][x] * 4)) + .08 * f[y][x])),
                       cl(78 * (.8 + .12 * (.5 + .5 * math.sin(x * .9 + f[y][x] * 4)) + .08 * f[y][x])), 255) for x in range(128)])
marble_base = big(marble(12, 1, 0, amp=6))
ITEM_TEX = {"band_gold": band(gold_base, 1), "band_marble": band(marble_base, 2), "glyph": glyph_disc()}

# ------------------------------------------------ ring models with continuous UVs
def ring_elements(R, t, tex, n=16, planets=(), planet_tex="g"):
    els = []; L = 2 * math.pi * R / n * 1.06
    for k in range(n):
        th = k * 2 * math.pi / n
        cx, cz = 8 + R * math.cos(th), 8 + R * math.sin(th)
        phi = round(((math.degrees(th) + 90) % 180) / 22.5) * 22.5 % 180
        u0, u1 = k * 16 / n, (k + 1) * 16 / n
        if phi in (67.5, 90.0, 112.5):
            beta = 90 - phi; frm, to = (cx - t / 2, 8 - t / 2, cz - L / 2), (cx + t / 2, 8 + t / 2, cz + L / 2); long = ("east", "west", "up", "down")
        else:
            beta = -phi if phi <= 45 else 180 - phi; frm, to = (cx - L / 2, 8 - t / 2, cz - t / 2), (cx + L / 2, 8 + t / 2, cz + t / 2); long = ("north", "south", "up", "down")
        faces = {}
        for fc in ("north", "south", "east", "west", "up", "down"):
            faces[fc] = {"uv": [round(u0, 4), 0, round(u1, 4), 2] if fc in long else [0, 4, 2, 6], "texture": "#" + tex}
        e = {"from": [round(v, 4) for v in frm], "to": [round(v, 4) for v in to], "faces": faces}
        if beta: e["rotation"] = {"origin": [round(cx, 4), 8, round(cz, 4)], "axis": "y", "angle": beta}
        els.append(e)
    for deg in planets:
        th = math.radians(deg); cx, cz = 8 + R * math.cos(th), 8 + R * math.sin(th); s_ = t * 1.5
        els.append({"from": [round(cx - s_, 4), round(8 - s_, 4), round(cz - s_, 4)], "to": [round(cx + s_, 4), round(8 + s_, 4), round(cz + s_, 4)],
                    "rotation": {"origin": [round(cx, 4), 8, round(cz, 4)], "axis": "y", "angle": 45},
                    "faces": {fc: {"uv": [0, 0, 16, 16], "texture": "#" + planet_tex} for fc in ("north", "south", "east", "west", "up", "down")}})
    return els
DISP = {"fixed": {"rotation": [0, 0, 0], "translation": [0, 0, 0], "scale": [1, 1, 1]}}
RING_MODELS = {
    "orrery_ring_gold": {"textures": {"b": "chroma:item/band_gold", "g": "chroma:item/glow", "particle": "chroma:item/band_gold"},
                         "elements": ring_elements(14, 1.0, "b", planets=(0, 135, 225)), "display": DISP},
    "orrery_ring_marble": {"textures": {"b": "chroma:item/band_marble", "o": "chroma:item/band_gold", "g": "chroma:item/glow", "particle": "chroma:item/band_marble"},
                           "elements": ring_elements(14, 1.1, "b", planets=(45, 180, 292.5)) + ring_elements(15.2, .35, "o") + ring_elements(12.8, .35, "o"),
                           "display": DISP},
}

# ------------------------------------------------ assemble
files = {}
with zipfile.ZipFile(SRC) as z:
    for n_ in z.namelist(): files[n_] = z.read(n_)
for k, px in BLOCK_TEX.items(): files[f"assets/minecraft/textures/block/{k}.png"] = png(px)
for k, px in ITEM_TEX.items(): files[f"assets/chroma/textures/item/{k}.png"] = png(px)
for k, m in RING_MODELS.items(): files[f"assets/chroma/models/item/{k}.json"] = json.dumps(m, indent=1).encode()
files["pack.mcmeta"] = json.dumps({"pack": {"description": "§6§lChroma Endless §7- Citadelle", "min_format": 75, "max_format": 75}}, ensure_ascii=False, indent=2).encode()
buf = io.BytesIO()
with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as z:
    for p in sorted(files):
        zi = zipfile.ZipInfo(p, date_time=(2026, 1, 1, 0, 0, 0)); zi.compress_type = zipfile.ZIP_DEFLATED; z.writestr(zi, files[p])
data = buf.getvalue(); open(OUTZ, "wb").write(data)
# previews: block textures tiled 3x3 + bands + disc
tiles = list(BLOCK_TEX.items())
W2 = 96 * 5; H2 = 96 * 2 + 16 * 2 * 2 + 4 + 256
sheet = [[(36, 36, 42, 255)] * max(W2, 512) for _ in range(H2)]
for i, (k, px) in enumerate(tiles):
    ox, oy = (i % 5) * 96, (i // 5) * 96
    for y in range(96):
        for x in range(96): sheet[oy + y][ox + x] = px[y % 32][x % 32]
oy = 192
for k in ("band_gold", "band_marble"):
    px = ITEM_TEX[k]
    for y in range(32):
        for x in range(512): sheet[oy + y][x] = px[(y // 2)][(x // 2) % 128]
    oy += 34
g = ITEM_TEX["glyph"]
for y in range(256):
    for x in range(256):
        if g[y][x][3] > 0: sheet[oy + y][x] = g[y][x]
open(os.path.join(D, "pack2_preview.png"), "wb").write(png(sheet))
print("pack", len(data), "sha1", hashlib.sha1(data).hexdigest())
