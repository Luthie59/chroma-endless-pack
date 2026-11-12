"""Add textured 3D models (orrery rings, gem core, marble statue, engraved glyph disc) to the Chroma Endless pack."""
import hashlib, io, json, math, os, random, struct, sys, zipfile, zlib

D = sys.argv[1]
SRC = os.path.join(D, "ChromaEndless-Logos.zip")
OUTZ = os.path.join(D, "ChromaEndless-Pack.zip")

def png(px):
    h = len(px); w = len(px[0])
    raw = b"".join(b"\x00" + b"".join(struct.pack("BBBB", *p) for p in row) for row in px)
    ch = lambda t, d: struct.pack(">I", len(d)) + t + d + struct.pack(">I", zlib.crc32(t + d) & 0xFFFFFFFF)
    return b"\x89PNG\r\n\x1a\n" + ch(b"IHDR", struct.pack(">IIBBBBB", w, h, 8, 6, 0, 0, 0)) + ch(b"IDAT", zlib.compress(raw, 9)) + ch(b"IEND", b"")
def clamp(v): return max(0, min(255, int(v)))
rng = random.Random(7)
def vnoise(w, h, cell, seed):
    r = random.Random(seed); g = [[r.random() for _ in range(w // cell + 2)] for _ in range(h // cell + 2)]
    out = [[0.0] * w for _ in range(h)]
    for y in range(h):
        for x in range(w):
            gx, gy = x / cell, y / cell; x0, y0 = int(gx), int(gy); fx, fy = gx - x0, gy - y0
            fx = fx * fx * (3 - 2 * fx); fy = fy * fy * (3 - 2 * fy)
            a = g[y0][x0] * (1 - fx) + g[y0][x0 + 1] * fx; b = g[y0 + 1][x0] * (1 - fx) + g[y0 + 1][x0 + 1] * fx
            out[y][x] = a * (1 - fy) + b * fy
    return out
def fbm(w, h, seed):
    layers = [vnoise(w, h, c, seed + i) for i, c in enumerate((16, 8, 4, 2))]
    return [[sum(l[y][x] * (0.5 ** i) for i, l in enumerate(layers)) / 1.875 for x in range(w)] for y in range(h)]

# ---------------- textures
def tex_marble(n=64, seed=1, base=(238, 235, 228), vein=(150, 150, 158)):
    f = fbm(n, n, seed); px = []
    for y in range(n):
        row = []
        for x in range(n):
            v = math.sin((x * .9 + y * .35) * .22 + f[y][x] * 9.0)
            t = max(0.0, 1 - abs(v) / .09)            # thin veins
            t2 = max(0.0, 1 - abs(v) / .35) * .18      # soft halo
            k = .93 + .07 * f[y][x]
            c = [base[i] * k * (1 - t - t2) + vein[i] * (t + t2) for i in range(3)]
            row.append((clamp(c[0]), clamp(c[1]), clamp(c[2]), 255))
        px.append(row)
    return px
def tex_gold(n=64, seed=3, engrave=True):
    f = fbm(n, n, seed); px = []
    for y in range(n):
        row = []
        for x in range(n):
            brushed = .5 + .5 * math.sin(y * 1.7 + f[y][x] * 6)
            k = .78 + .14 * brushed + .08 * f[y][x]
            c = [246 * k, 196 * k, 72 * k]
            if engrave:
                cx, cy = n / 2, n / 2; d = math.hypot(x + .5 - cx, y + .5 - cy)
                for rr in (n * .42, n * .30, n * .12):
                    if abs(d - rr) < .7: c = [c[0] * .55, c[1] * .5, c[2] * .45]
                    elif abs(d - rr - 1) < .6: c = [min(255, c[0] * 1.15), min(255, c[1] * 1.15), c[2] * 1.1]
                if (x + y) % 16 == 0 and abs(d - n * .36) < 4: c = [c[0] * .6, c[1] * .55, c[2] * .5]
            if x in (0, n - 1) or y in (0, n - 1): c = [c[0] * .7, c[1] * .65, c[2] * .6]
            row.append((clamp(c[0]), clamp(c[1]), clamp(c[2]), 255))
        px.append(row)
    return px
def tex_robe(n=64):
    m = tex_marble(n, 11, base=(244, 241, 236), vein=(185, 182, 178)); px = []
    for y in range(n):
        row = []
        for x in range(n):
            fold = .86 + .14 * (0.5 + 0.5 * math.sin(x * .55 + math.sin(y * .08) * 2))
            r, g, b, a = m[y][x]; row.append((clamp(r * fold), clamp(g * fold), clamp(b * fold), 255))
        px.append(row)
    return px
def tex_crimson(n=32):
    f = fbm(n, n, 21)
    return [[(clamp(150 + 40 * f[y][x]), clamp(20 + 12 * f[y][x]), clamp(30 + 15 * f[y][x]), 255) for x in range(n)] for y in range(n)]
def tex_glow(n=32):
    px = []
    for y in range(n):
        row = []
        for x in range(n):
            d = math.hypot(x + .5 - n / 2, y + .5 - n / 2) / (n / 2)
            row.append((255, clamp(250 - 80 * d), clamp(225 - 170 * d), 255))
        px.append(row)
    return px
def tex_glyph(n=128):
    px = [[(0, 0, 0, 0)] * n for _ in range(n)]
    gold = (240, 196, 70); dark = (150, 105, 30)
    def plot(x, y, a, col=gold):
        if 0 <= x < n and 0 <= y < n and a > 0:
            r, g, b, a0 = px[y][x]; a = min(1, a)
            na = max(a0 / 255, a)
            px[y][x] = (clamp(col[0]), clamp(col[1]), clamp(col[2]), clamp(na * 255))
    def circle(cx, cy, r, w):
        for y in range(int(cy - r - w - 2), int(cy + r + w + 3)):
            for x in range(int(cx - r - w - 2), int(cx + r + w + 3)):
                d = abs(math.hypot(x + .5 - cx, y + .5 - cy) - r)
                plot(x, y, (w / 2 + .6 - d) / 1.2)
    def disc(cx, cy, r):
        for y in range(int(cy - r - 2), int(cy + r + 3)):
            for x in range(int(cx - r - 2), int(cx + r + 3)):
                plot(x, y, r + .6 - math.hypot(x + .5 - cx, y + .5 - cy))
    def line(x0, y0, x1, y1, w):
        L = math.hypot(x1 - x0, y1 - y0)
        for y in range(int(min(y0, y1)) - 3, int(max(y0, y1)) + 4):
            for x in range(int(min(x0, x1)) - 3, int(max(x0, x1)) + 4):
                t = max(0, min(1, ((x + .5 - x0) * (x1 - x0) + (y + .5 - y0) * (y1 - y0)) / (L * L)))
                d = math.hypot(x + .5 - (x0 + t * (x1 - x0)), y + .5 - (y0 + t * (y1 - y0)))
                plot(x, y, (w / 2 + .6 - d) / 1.2)
    c = n / 2
    circle(c, c, 60, 3.2); circle(c, c, 55, 1.2); circle(c, c, 38, 2.2)
    r = random.Random(5)
    for k in range(6):
        a = k * math.pi / 3 + .3
        cx, cy = c + 46.5 * math.cos(a), c + 46.5 * math.sin(a)
        rr = 6 + r.random() * 4
        circle(cx, cy, rr, 1.8)
        for j in range(r.randint(1, 3)):
            b = r.random() * 2 * math.pi; disc(cx + (rr - 3) * math.cos(b), cy + (rr - 3) * math.sin(b), 1.6)
        line(c + 38 * math.cos(a), c + 38 * math.sin(a), cx - rr * math.cos(a), cy - rr * math.sin(a), 1.4)
    for k in range(3):
        a = k * 2 * math.pi / 3 + 1.1
        cx, cy = c + 18 * math.cos(a), c + 18 * math.sin(a)
        circle(cx, cy, 11, 1.8); disc(cx, cy, 2.4)
        line(cx, cy, c, c, 1.2)
    circle(c, c, 7, 2.2); disc(c, c, 3)
    for k in range(24):
        a = k * math.pi / 12
        disc(c + 57.5 * math.cos(a), c + 57.5 * math.sin(a), 1.1)
    # dark rim for depth
    out = []
    for y in range(n):
        row = []
        for x in range(n):
            r_, g_, b_, a_ = px[y][x]
            if a_ == 0:
                near = any(0 <= x + dx < n and 0 <= y + dy < n and px[y + dy][x + dx][3] > 120 for dx, dy in ((1, 0), (0, 1), (-1, 0), (0, -1)))
                row.append((dark[0], dark[1], dark[2], 170) if near else (0, 0, 0, 0))
            else:
                shade = .9 + .2 * ((x + y) % 7) / 7
                row.append((clamp(r_ * shade), clamp(g_ * shade), clamp(b_ * shade), a_))
        out.append(row)
    return out

TEX = {"gold": tex_gold(), "gold_plain": tex_gold(engrave=False), "marble": tex_marble(), "robe": tex_robe(),
       "crimson": tex_crimson(), "glow": tex_glow(), "glyph": tex_glyph()}

# ---------------- models
def el(frm, to, tex, rot=None, uvfull=True):
    faces = {f: {"uv": [0, 0, 16, 16], "texture": "#" + tex} for f in ("north", "south", "east", "west", "up", "down")}
    e = {"from": [round(v, 4) for v in frm], "to": [round(v, 4) for v in to], "faces": faces}
    if rot: e["rotation"] = rot
    return e
def ring_elements(R, t, tex, n=16, planets=(), planet_tex="glow"):
    els = []
    L = 2 * math.pi * R / n * 1.06
    for k in range(n):
        th = k * 2 * math.pi / n
        cx, cz = 8 + R * math.cos(th), 8 + R * math.sin(th)
        phi = (math.degrees(th) + 90) % 180
        phi = round(phi / 22.5) * 22.5 % 180
        if phi in (67.5, 90.0, 112.5):
            beta = 90 - phi
            frm, to = (cx - t / 2, 8 - t / 2, cz - L / 2), (cx + t / 2, 8 + t / 2, cz + L / 2)
        else:
            beta = -phi if phi <= 45 else 180 - phi
            frm, to = (cx - L / 2, 8 - t / 2, cz - t / 2), (cx + L / 2, 8 + t / 2, cz + t / 2)
        rot = {"origin": [round(cx, 4), 8, round(cz, 4)], "axis": "y", "angle": beta} if beta else None
        els.append(el(frm, to, tex, rot))
    for deg in planets:
        th = math.radians(deg); cx, cz = 8 + R * math.cos(th), 8 + R * math.sin(th); s_ = t * 1.5
        els.append(el((cx - s_, 8 - s_, cz - s_), (cx + s_, 8 + s_, cz + s_), planet_tex, {"origin": [round(cx, 4), 8, round(cz, 4)], "axis": "y", "angle": 45}))
    return els
def model(textures, elements):
    return {"textures": dict(textures, particle="chroma:item/" + list(textures.values())[0].split("/")[-1] if False else list(textures.values())[0]),
            "elements": elements,
            "display": {"fixed": {"rotation": [0, 0, 0], "translation": [0, 0, 0], "scale": [1, 1, 1]},
                        "head": {"rotation": [0, 0, 0], "translation": [0, 0, 0], "scale": [1, 1, 1]}}}
T = lambda k: "chroma:item/" + k
MODELS = {
    "orrery_ring_gold": model({"r": T("gold"), "g": T("glow")}, ring_elements(14, .9, "r", planets=(0, 135, 225), planet_tex="g")),
    "orrery_ring_marble": model({"r": T("marble"), "o": T("gold_plain"), "g": T("glow")}, ring_elements(14, 1.0, "r", planets=(45, 180, 292.5), planet_tex="g")
                                + ring_elements(15.1, .35, "o") + ring_elements(12.9, .35, "o")),
    "orrery_core": model({"g": T("glow"), "o": T("gold")}, [
        el((5, 5, 5), (11, 11, 11), "g"),
        el((5, 5, 5), (11, 11, 11), "g", {"origin": [8, 8, 8], "axis": "y", "angle": 45}),
        el((5.5, 5.5, 5.5), (10.5, 10.5, 10.5), "g", {"origin": [8, 8, 8], "axis": "x", "angle": 45}),
        el((7.6, 1, 7.6), (8.4, 15, 8.4), "o"), el((1, 7.6, 7.6), (15, 8.4, 8.4), "o")]),
    "statue": model({"m": T("robe"), "o": T("gold"), "c": T("crimson"), "f": T("marble"), "g": T("glow")}, [
        el((2.5, 0, 3.5), (13.5, 6, 12.5), "m"),
        el((3.5, 6, 4.5), (12.5, 13, 11.5), "m"),
        el((4.6, 11.8, 4.6), (11.4, 13.2, 11.4), "c"),
        el((4.5, 13, 5.2), (11.5, 20, 10.8), "m"),
        el((3.4, 19.5, 4.8), (12.6, 21.5, 11.2), "c"),
        el((6.2, 21.5, 6.2), (9.8, 25.2, 9.8), "f"),
        el((2.6, 20, 11.0), (13.4, 30, 11.7), "o", {"origin": [8, 20, 11.3], "axis": "x", "angle": -22.5}),
        el((2.6, 20, 5.8), (3.3, 27, 11.2), "o", {"origin": [3, 20, 11], "axis": "y", "angle": 22.5}),
        el((12.7, 20, 5.8), (13.4, 27, 11.2), "o", {"origin": [13, 20, 11], "axis": "y", "angle": -22.5}),
        el((2.0, 11, 6), (4.6, 19.5, 10), "m", {"origin": [3.3, 19.5, 8], "axis": "x", "angle": -22.5}),
        el((11.4, 11, 6), (14.0, 19.5, 10), "m", {"origin": [12.7, 19.5, 8], "axis": "x", "angle": -22.5}),
        el((13.6, 0, 4.6), (14.6, 31, 5.6), "o"),
        el((12.9, 29.4, 3.9), (15.3, 31.8, 6.3), "g", {"origin": [14.1, 30.6, 5.1], "axis": "y", "angle": 45}),
        el((2.0, 5.4, 3.0), (14.0, 6.0, 13.0), "o")]),
    "glyph_disc": {"textures": {"g": T("glyph"), "particle": T("glyph")},
                   "elements": [{"from": [-8, 0, -8], "to": [24, .15, 24],
                                 "faces": {"up": {"uv": [0, 0, 16, 16], "texture": "#g"}, "down": {"uv": [0, 16, 16, 0], "texture": "#g"}}}],
                   "display": {"fixed": {"rotation": [0, 0, 0], "translation": [0, 0, 0], "scale": [1, 1, 1]}}},
}
for m in MODELS.values():
    m["textures"]["particle"] = list(v for k, v in m["textures"].items() if k != "particle")[0]

# ---------------- assemble pack (keep existing logo font)
files = {}
with zipfile.ZipFile(SRC) as z:
    for n in z.namelist(): files[n] = z.read(n)
for k, px in TEX.items(): files[f"assets/chroma/textures/item/{k}.png"] = png(px)
for k, m in MODELS.items():
    files[f"assets/chroma/models/item/{k}.json"] = json.dumps(m, indent=1).encode()
    files[f"assets/chroma/items/{k}.json"] = json.dumps({"model": {"type": "minecraft:model", "model": f"chroma:item/{k}"}}).encode()
files["pack.mcmeta"] = json.dumps({"pack": {"description": "§6§lChroma Endless §7- Logos & modèles", "min_format": 75, "max_format": 75}},
                                  ensure_ascii=False, indent=2).encode("utf-8")
buf = io.BytesIO()
with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as z:
    for p in sorted(files):
        zi = zipfile.ZipInfo(p, date_time=(2026, 1, 1, 0, 0, 0)); zi.compress_type = zipfile.ZIP_DEFLATED; z.writestr(zi, files[p])
data = buf.getvalue(); open(OUTZ, "wb").write(data)
# preview sheet of textures
sheet_w = 64 * 6 + 128; sheet = [[(40, 40, 46, 255)] * sheet_w for _ in range(128)]
xo = 0
for k in ("gold", "marble", "robe", "crimson", "glow", "gold_plain", "glyph"):
    px = TEX[k]; n = len(px); s_ = 64 // n if n < 64 else 1
    for y in range(n * s_):
        for x in range(n * s_):
            if xo + x < sheet_w and y < 128:
                p = px[y // s_][x // s_]
                if p[3] > 0: sheet[y][xo + x] = p
    xo += n * s_
open(os.path.join(D, "textures_preview.png"), "wb").write(png(sheet))
print("pack", len(data), "sha1", hashlib.sha1(data).hexdigest(), "models", list(MODELS))
