"""v5: opaque swallowtail pennant (no pole, no alpha) + marble/gold urn model."""
import hashlib, io, json, math, os, random, struct, sys, zipfile, zlib
D = sys.argv[1]
SRC = os.path.join(D, "ChromaEndless-Pack4.zip"); OUTZ = os.path.join(D, "ChromaEndless-Pack5.zip")
def png(px):
    h = len(px); w = len(px[0])
    raw = b"".join(b"\x00" + b"".join(struct.pack("BBBB", *p) for p in row) for row in px)
    ch = lambda t, d: struct.pack(">I", len(d)) + t + d + struct.pack(">I", zlib.crc32(t + d) & 0xFFFFFFFF)
    return b"\x89PNG\r\n\x1a\n" + ch(b"IHDR", struct.pack(">IIBBBBB", w, h, 8, 6, 0, 0, 0)) + ch(b"IDAT", zlib.compress(raw, 9)) + ch(b"IEND", b"")
def cl(v): return max(0, min(255, int(round(v))))

# opaque 64x64 flag cloth: crimson, gold border, circular emblem; fully opaque everywhere
def flag2():
    r = random.Random(4); px = []
    for y in range(64):
        row = []
        for x in range(64):
            weave = .93 + .05 * ((x + y) % 2) + .04 * r.random(); fold = .9 + .1 * math.sin(x * .3)
            c = (168 * weave * fold, 22 * weave * fold, 34 * weave * fold)
            if y < 3 or y > 60 or x < 3:
                g = .85 + .15 * ((x * 3 + y) % 5) / 5; c = (246 * g, 196 * g, 72 * g)
            d = math.hypot(x + .5 - 22, y + .5 - 32)
            for rr, w in ((17, 1.6), (12, 1.0)):
                if abs(d - rr) < w: c = (246, 200, 80)
            for k in range(3):
                a = k * 2 * math.pi / 3 + .5; cx, cy = 22 + 6 * math.cos(a), 32 + 6 * math.sin(a)
                if abs(math.hypot(x + .5 - cx, y + .5 - cy) - 3) < .8: c = (246, 200, 80)
            if d < 2: c = (246, 200, 80)
            row.append((cl(c[0]), cl(c[1]), cl(c[2]), 255))
        px.append(row)
    return px
def face_all(tex, uv): return {fc: {"uv": list(uv), "texture": "#" + tex} for fc in ("north", "south", "east", "west", "up", "down")}
def box(frm, to, tex, uv_main, uv_edge=(0, 0, 1, 1), main=("north", "south"), rot=None):
    f = face_all(tex, uv_edge)
    for fc in main: f[fc] = {"uv": list(uv_main), "texture": "#" + tex}
    e = {"from": [round(v, 4) for v in frm], "to": [round(v, 4) for v in to], "faces": f}
    if rot: e["rotation"] = rot
    return e
DISP = {"fixed": {"rotation": [0, 0, 0], "translation": [0, 0, 0], "scale": [1, 1, 1]}}
# flag body x 9.5..24, tails x 24..30.5 (upper and lower), thickness .5 ; texture u maps over x 9.5..30.5 (21 units -> 16 uv)
def u(x): return round((x - 9.5) / 21 * 16, 4)
pen = [box((9.5, 8, 7.75), (24, 18, 8.25), "f", (u(9.5), 0, u(24), 16)),
       box((24, 13.4, 7.75), (30.5, 18, 8.25), "f", (u(24), 0, u(30.5), 7.36)),
       box((24, 8, 7.75), (30.5, 12.6, 8.25), "f", (u(24), 8.64, u(30.5), 16)),
       box((9.5, 17.6, 7.6), (24, 18.4, 8.4), "o", (0, 0, 16, 1), main=("north", "south", "up")),
       box((9.5, 7.6, 7.6), (24, 8.4, 8.4), "o", (0, 0, 16, 1), main=("north", "south", "down"))]
PENNANT = {"textures": {"f": "chroma:item/flag2", "o": "chroma:item/gold_plain", "particle": "chroma:item/flag2"}, "elements": pen, "display": DISP}
# urn: plinth, foot, body, shoulder, neck, lip, two handles, gold bands
def cyl(r, y0, y1, tex):
    return [box((8 - r, y0, 8 - r), (8 + r, y1, 8 + r), tex, (0, 0, 16, 16), (0, 0, 16, 16), main=()),
            box((8 - r * .92, y0 + .02, 8 - r * .92), (8 + r * .92, y1 - .02, 8 + r * .92), tex, (0, 0, 16, 16), (0, 0, 16, 16), main=(),
                rot={"origin": [8, (y0 + y1) / 2, 8], "axis": "y", "angle": 45})]
urn = (cyl(5, 0, 2, "m") + cyl(3.2, 2, 4, "m") + cyl(2.6, 4, 5, "o") + cyl(5, 5, 11, "m") + cyl(5.3, 8, 8.8, "o") +
       cyl(3.8, 11, 13, "m") + cyl(2.4, 13, 16, "m") + cyl(3.6, 16, 17.2, "o"))
urn += [box((2.2, 10, 7.4), (3.2, 15, 8.6), "o", (0, 0, 16, 16), main=()), box((12.8, 10, 7.4), (13.8, 15, 8.6), "o", (0, 0, 16, 16), main=()),
        box((2.2, 14.2, 7.4), (5.4, 15.2, 8.6), "o", (0, 0, 16, 16), main=()), box((10.6, 14.2, 7.4), (13.8, 15.2, 8.6), "o", (0, 0, 16, 16), main=())]
URN = {"textures": {"m": "minecraft:block/quartz_block_bottom", "o": "chroma:item/gold", "particle": "chroma:item/gold"}, "elements": urn, "display": DISP}
MODELS = {"pennant": PENNANT, "urn": URN}
files = {}
with zipfile.ZipFile(SRC) as z:
    for n in z.namelist(): files[n] = z.read(n)
files["assets/chroma/textures/item/flag2.png"] = png(flag2())
for k, m in MODELS.items():
    files[f"assets/chroma/models/item/{k}.json"] = json.dumps(m, indent=1).encode()
    files[f"assets/chroma/items/{k}.json"] = json.dumps({"model": {"type": "minecraft:model", "model": f"chroma:item/{k}"}}).encode()
buf = io.BytesIO()
with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as z:
    for p in sorted(files):
        zi = zipfile.ZipInfo(p, date_time=(2026, 1, 1, 0, 0, 0)); zi.compress_type = zipfile.ZIP_DEFLATED; z.writestr(zi, files[p])
data = buf.getvalue(); open(OUTZ, "wb").write(data)
open(os.path.join(D, "flag2_preview.png"), "wb").write(png(flag2()))
print("pack", len(data), "sha1", hashlib.sha1(data).hexdigest())
