"""v4: armillary-style orrery rings (flat hoops, correct UV aspect, graduated polished brass / bronze)."""
import hashlib, io, json, math, os, random, struct, sys, zipfile, zlib
D = sys.argv[1]
SRC = os.path.join(D, "ChromaEndless-Pack3.zip"); OUTZ = os.path.join(D, "ChromaEndless-Pack4.zip")
def png(px):
    h = len(px); w = len(px[0])
    raw = b"".join(b"\x00" + b"".join(struct.pack("BBBB", *p) for p in row) for row in px)
    ch = lambda t, d: struct.pack(">I", len(d)) + t + d + struct.pack(">I", zlib.crc32(t + d) & 0xFFFFFFFF)
    return b"\x89PNG\r\n\x1a\n" + ch(b"IHDR", struct.pack(">IIBBBBB", w, h, 8, 6, 0, 0, 0)) + ch(b"IDAT", zlib.compress(raw, 9)) + ch(b"IEND", b"")
def cl(v): return max(0, min(255, int(round(v))))

S = 512; BAND = 14           # band occupies rows 0..13 (14 px tall) across 512 px
def band_tex(base, tick, seed):
    r = random.Random(seed)
    px = [[(0, 0, 0, 0)] * S for _ in range(S)]
    for y in range(S):
        for x in range(S):
            if y < BAND:
                t = y / (BAND - 1)
                # cylindrical metal shading: bright highlight 1/3 from top, darker towards the bottom
                k = .78 + .34 * math.exp(-((t - .32) / .22) ** 2) - .12 * t
                k *= .97 + .03 * math.sin(x * 2.1) + .02 * r.random()
                c = [base[i] * k for i in range(3)]
                if y in (0, BAND - 1): c = [v * .62 for v in c]                    # outer rims
                elif y in (1, BAND - 2): c = [min(255, v * 1.22) for v in c]       # rim highlight
                elif y == 2 or y == BAND - 3: c = [v * .8 for v in c]               # rim groove
                # graduations
                m = x % 32
                if 3 <= y <= BAND - 4:
                    if m == 0 and y <= BAND - 4: c = [tick[i] * .75 for i in range(3)]
                    elif m % 8 == 0 and y <= 6: c = [tick[i] * .8 for i in range(3)]
                    elif m % 4 == 0 and y <= 4: c = [tick[i] * .85 for i in range(3)]
                    if m == 16 and 7 <= y <= 9: c = [tick[i] for i in range(3)]       # small inlaid dot
                px[y][x] = (cl(c[0]), cl(c[1]), cl(c[2]), 255)
            else:
                k = .88 + .06 * math.sin(x * .7 + y * .3)
                px[y][x] = (cl(base[0] * k), cl(base[1] * k), cl(base[2] * k), 255)
    return px
GOLD = (252, 202, 84); BRONZE = (150, 96, 52)
TEX = {"band_brass": band_tex(GOLD, (110, 70, 20), 1), "band_bronze": band_tex(BRONZE, (255, 214, 110), 2)}

def ring(R, t, h, tex, n=16, vspan=BAND / S * 16):
    """flat hoop: radial thickness t, axial height h; band texture on the inner/outer faces with correct aspect."""
    L = 2 * math.pi * R / n * 1.04; out = []
    for k in range(n):
        th = k * 2 * math.pi / n
        cx, cz = 8 + R * math.cos(th), 8 + R * math.sin(th)
        phi = round(((math.degrees(th) + 90) % 180) / 22.5) * 22.5 % 180
        u0, u1 = k * 16 / n, (k + 1) * 16 / n
        if phi in (67.5, 90.0, 112.5):
            beta = 90 - phi; frm, to = (cx - t / 2, 8 - h / 2, cz - L / 2), (cx + t / 2, 8 + h / 2, cz + L / 2); radial = ("east", "west")
        else:
            beta = -phi if phi <= 45 else 180 - phi; frm, to = (cx - L / 2, 8 - h / 2, cz - t / 2), (cx + L / 2, 8 + h / 2, cz + t / 2); radial = ("north", "south")
        faces = {}
        for fc in ("north", "south", "east", "west", "up", "down"):
            if fc in radial: faces[fc] = {"uv": [round(u0, 4), 0, round(u1, 4), round(vspan, 4)], "texture": "#" + tex}
            elif fc in ("up", "down"): faces[fc] = {"uv": [round(u0, 4), .1, round(u1, 4), .2], "texture": "#" + tex}
            else: faces[fc] = {"uv": [0, 4, .5, 4.5], "texture": "#" + tex}
        e = {"from": [round(v, 4) for v in frm], "to": [round(v, 4) for v in to], "faces": faces}
        if beta: e["rotation"] = {"origin": [round(cx, 4), 8, round(cz, 4)], "axis": "y", "angle": beta}
        out.append(e)
    return out
def planet(deg, R, s_, tex):
    th = math.radians(deg); cx, cz = 8 + R * math.cos(th), 8 + R * math.sin(th)
    f = {fc: {"uv": [0, 0, 16, 16], "texture": "#" + tex} for fc in ("north", "south", "east", "west", "up", "down")}
    return [{"from": [round(cx - s_, 4), round(8 - s_, 4), round(cz - s_, 4)], "to": [round(cx + s_, 4), round(8 + s_, 4), round(cz + s_, 4)],
             "rotation": {"origin": [round(cx, 4), 8, round(cz, 4)], "axis": "y", "angle": 45}, "faces": f},
            {"from": [round(cx - s_ * .8, 4), round(8 - s_ * .8, 4), round(cz - s_ * .8, 4)], "to": [round(cx + s_ * .8, 4), round(8 + s_ * .8, 4), round(cz + s_ * .8, 4)],
             "rotation": {"origin": [round(cx, 4), 8, round(cz, 4)], "axis": "x", "angle": 45}, "faces": f}]
DISP = {"fixed": {"rotation": [0, 0, 0], "translation": [0, 0, 0], "scale": [1, 1, 1]}}
gold_ring = ring(14, .7, 2.6, "b")
for deg in (0, 135, 225): gold_ring += planet(deg, 14, 1.25, "g")
bronze_ring = ring(14, .8, 3.0, "b")
for deg in (45, 180, 292.5): bronze_ring += planet(deg, 14, 1.35, "g")
MODELS = {
    "orrery_ring_gold": {"textures": {"b": "chroma:item/band_brass", "g": "chroma:item/glow", "particle": "chroma:item/band_brass"}, "elements": gold_ring, "display": DISP},
    "orrery_ring_marble": {"textures": {"b": "chroma:item/band_bronze", "g": "chroma:item/glow", "particle": "chroma:item/band_bronze"}, "elements": bronze_ring, "display": DISP},
}
files = {}
with zipfile.ZipFile(SRC) as z:
    for n in z.namelist(): files[n] = z.read(n)
for k, px in TEX.items(): files[f"assets/chroma/textures/item/{k}.png"] = png(px)
for k, m in MODELS.items(): files[f"assets/chroma/models/item/{k}.json"] = json.dumps(m, indent=1).encode()
# chandelier crown: same fix (flat hoop + brass band)
ch = json.loads(files["assets/chroma/models/item/chandelier.json"])
ch["elements"] = ring(12, .6, 2.2, "b") + ch["elements"][16:]
ch["textures"]["b"] = "chroma:item/band_brass"
files["assets/chroma/models/item/chandelier.json"] = json.dumps(ch, indent=1).encode()
buf = io.BytesIO()
with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as z:
    for p in sorted(files):
        zi = zipfile.ZipInfo(p, date_time=(2026, 1, 1, 0, 0, 0)); zi.compress_type = zipfile.ZIP_DEFLATED; z.writestr(zi, files[p])
data = buf.getvalue(); open(OUTZ, "wb").write(data)
# preview: one segment face at true aspect (5.9 x 2.6 units) magnified, for both bands
prev = []
for name in ("band_brass", "band_bronze"):
    t = TEX[name]
    for y in range(BAND * 4):
        prev.append([t[y // 4][x // 2] for x in range(256)])
    prev.append([(30, 30, 30, 255)] * 256)
open(os.path.join(D, "band_preview.png"), "wb").write(png(prev))
print("pack", len(data), "sha1", hashlib.sha1(data).hexdigest())
