"""v3: textured models for pennants, chandeliers and flying buttresses + command list to swap them in."""
import hashlib, io, json, math, os, random, struct, sys, zipfile, zlib

D = sys.argv[1]; POS = sys.argv[2]
SRC = os.path.join(D, "ChromaEndless-Pack2.zip"); OUTZ = os.path.join(D, "ChromaEndless-Pack3.zip")
def png(px):
    h = len(px); w = len(px[0])
    raw = b"".join(b"\x00" + b"".join(struct.pack("BBBB", *p) for p in row) for row in px)
    ch = lambda t, d: struct.pack(">I", len(d)) + t + d + struct.pack(">I", zlib.crc32(t + d) & 0xFFFFFFFF)
    return b"\x89PNG\r\n\x1a\n" + ch(b"IHDR", struct.pack(">IIBBBBB", w, h, 8, 6, 0, 0, 0)) + ch(b"IDAT", zlib.compress(raw, 9)) + ch(b"IEND", b"")
def cl(v): return max(0, min(255, int(round(v))))

# ---------------- flag texture 64x64 (flag drawn in the top 64x32, rest transparent)
def flag_tex():
    W_, H_ = 64, 32; r = random.Random(3)
    px = [[(0, 0, 0, 0)] * 64 for _ in range(64)]
    for y in range(H_):
        for x in range(W_):
            # swallowtail notch on the free end
            if x > 46 and abs(y - 15.5) < (x - 46) * .95: continue
            weave = .93 + .05 * ((x + y) % 2) + .04 * r.random()
            fold = .9 + .1 * math.sin(x * .35)
            c = (168 * weave * fold, 22 * weave * fold, 34 * weave * fold)
            gold = (y < 2 or y > H_ - 3 or x < 3)
            notch_edge = x > 46 and abs(abs(y - 15.5) - (x - 46) * .95) < 1.3
            if gold or notch_edge:
                g = .85 + .15 * ((x * 3 + y) % 5) / 5; c = (246 * g, 196 * g, 72 * g)
            d = math.hypot(x + .5 - 22, y + .5 - 16)
            for rr, w in ((9.5, 1.1), (6.5, .8)):
                if abs(d - rr) < w: c = (246, 200, 80)
            for k in range(3):
                a = k * 2 * math.pi / 3 + .5; cx, cy = 22 + 3.2 * math.cos(a), 16 + 3.2 * math.sin(a)
                if abs(math.hypot(x + .5 - cx, y + .5 - cy) - 1.7) < .6: c = (246, 200, 80)
            if d < 1.2: c = (246, 200, 80)
            px[y][x] = (cl(c[0]), cl(c[1]), cl(c[2]), 255)
    return px

def faces(tex, uv_long=None, long=(), small=(0, 0, 1, 1)):
    return {fc: {"uv": list(uv_long) if (uv_long and fc in long) else list(small), "texture": "#" + tex}
            for fc in ("north", "south", "east", "west", "up", "down")}
def box(frm, to, tex, rot=None, uv=None, long=(), small=(0, 0, 16, 16)):
    e = {"from": [round(v, 4) for v in frm], "to": [round(v, 4) for v in to], "faces": faces(tex, uv, long, small)}
    if rot: e["rotation"] = rot
    return e
def oriented(cx, cz, phi_deg, length, t, y0, y1, tex, uv=None):
    """thin bar centred (cx,cz), horizontal direction phi (multiples of 22.5)"""
    phi = round((phi_deg % 180) / 22.5) * 22.5 % 180
    if phi in (67.5, 90.0, 112.5):
        beta = 90 - phi; frm, to = (cx - t / 2, y0, cz - length / 2), (cx + t / 2, y1, cz + length / 2); lg = ("east", "west", "up", "down")
    else:
        beta = -phi if phi <= 45 else 180 - phi; frm, to = (cx - length / 2, y0, cz - t / 2), (cx + length / 2, y1, cz + t / 2); lg = ("north", "south", "up", "down")
    rot = {"origin": [round(cx, 4), round((y0 + y1) / 2, 4), round(cz, 4)], "axis": "y", "angle": beta} if beta else None
    return box(frm, to, tex, rot, uv, lg)
def ring(R, t, tex, n=16):
    L = 2 * math.pi * R / n * 1.06; out = []
    for k in range(n):
        th = k * 2 * math.pi / n
        out.append(oriented(8 + R * math.cos(th), 8 + R * math.sin(th), math.degrees(th) + 90, L, t, 8 - t / 2, 8 + t / 2, tex,
                            (k * 16 / n, 0, (k + 1) * 16 / n, 2)))
    return out
DISP = {"fixed": {"rotation": [0, 0, 0], "translation": [0, 0, 0], "scale": [1, 1, 1]}}

# ---------------- pennant: pole finial + 3 wavy flag segments
pen_el = [box((7.4, 6, 7.4), (8.6, 20, 8.6), "o"), box((7, 19.5, 7), (9, 21.5, 9), "g", {"origin": [8, 20.5, 8], "axis": "y", "angle": 45})]
seg = 22 / 3
for i in range(3):
    x0 = 8.6 + i * seg; dz = (0, .7, 0)[i]
    pen_el.append(box((x0, 8, 7.85 + dz), (x0 + seg, 18, 8.15 + dz), "f", None, (i * 16 / 3, 0, (i + 1) * 16 / 3, 8), ("north", "south"), (0, 0, .2, .2)))
PENNANT = {"textures": {"f": "chroma:item/flag", "o": "chroma:item/gold_plain", "g": "chroma:item/glow", "particle": "chroma:item/flag"}, "elements": pen_el, "display": DISP}

# ---------------- chandelier: engraved crown ring, 8 arms, 8 candles, pendant
ch_el = ring(12, 1.1, "b")
for k in range(8):
    phi = k * 45
    cx, cz = 8 + 8 * math.cos(math.radians(phi)), 8 + 8 * math.sin(math.radians(phi))
    ch_el.append(oriented(cx, cz, phi, 8, .7, 7.65, 8.35, "o"))
    px_, pz_ = 8 + 12 * math.cos(math.radians(phi)), 8 + 12 * math.sin(math.radians(phi))
    ch_el.append(box((px_ - .7, 8.5, pz_ - .7), (px_ + .7, 10.6, pz_ + .7), "w"))
    ch_el.append(box((px_ - .45, 10.6, pz_ - .45), (px_ + .45, 12.3, pz_ + .45), "g", {"origin": [round(px_, 4), 11.4, round(pz_, 4)], "axis": "y", "angle": 45}))
ch_el += [box((7.6, -1, 7.6), (8.4, 3, 8.4), "o"), box((7, -3, 7), (9, -1, 9), "g", {"origin": [8, -2, 8], "axis": "y", "angle": 45})]
CHANDELIER = {"textures": {"b": "chroma:item/band_gold", "o": "chroma:item/gold_plain", "w": "minecraft:block/quartz_block_bottom", "g": "chroma:item/glow",
                           "particle": "chroma:item/gold_plain"}, "elements": ch_el, "display": DISP}

# ---------------- flying buttress: marble beam along z (-16..32), gold spine, gold rings, underside trim
bt_el = [box((5, 4, -16), (11, 12, 32), "m", None, (0, 0, 16, 16), ("east", "west", "up", "down"), (0, 0, 16, 16)),
         box((7, 12, -16), (9, 13.2, 32), "o"), box((6.2, 3, -16), (9.8, 4, 32), "o")]
for zc in (-10, 2, 14, 26):
    bt_el.append(box((4.4, 3.4, zc - .7), (11.6, 12.6, zc + .7), "e"))
BUTTRESS = {"textures": {"m": "minecraft:block/quartz_block_bottom", "o": "chroma:item/gold_plain", "e": "chroma:item/gold", "particle": "chroma:item/gold"},
            "elements": bt_el, "display": DISP}

MODELS = {"pennant": PENNANT, "chandelier": CHANDELIER, "buttress": BUTTRESS}
for m in MODELS.values():
    for e in m["elements"]:
        for v in e["from"] + e["to"]:
            assert -16 <= v <= 32, ("out of bounds", v)

files = {}
with zipfile.ZipFile(SRC) as z:
    for n in z.namelist(): files[n] = z.read(n)
files["assets/chroma/textures/item/flag.png"] = png(flag_tex())
for k, m in MODELS.items():
    files[f"assets/chroma/models/item/{k}.json"] = json.dumps(m, indent=1).encode()
    files[f"assets/chroma/items/{k}.json"] = json.dumps({"model": {"type": "minecraft:model", "model": f"chroma:item/{k}"}}).encode()
buf = io.BytesIO()
with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as z:
    for p in sorted(files):
        zi = zipfile.ZipInfo(p, date_time=(2026, 1, 1, 0, 0, 0)); zi.compress_type = zipfile.ZIP_DEFLATED; z.writestr(zi, files[p])
data = buf.getvalue(); open(OUTZ, "wb").write(data)
open(os.path.join(D, "flag_preview.png"), "wb").write(png([[p if p[3] else (40, 40, 46, 255) for p in row] for row in flag_tex()[:32]]))

# ---------------- swap commands
def qaxis(ax, ay, az, a): s = math.sin(a / 2); return (ax * s, ay * s, az * s, math.cos(a / 2))
def qmul(a, b):
    ax, ay, az, aw = a; bx, by, bz, bw = b
    return (aw * bx + ax * bw + ay * bz - az * by, aw * by - ax * bz + ay * bw + az * bx, aw * bz + ax * by - ay * bx + az * bw, aw * bw - ax * bx - ay * by - az * bz)
F = lambda v: ("%.5f" % v).rstrip("0").rstrip(".") + "f"
def summon(p, model, q, sc, tags, extra=""):
    return ("execute in minecraft:overworld run summon item_display %.4f %.4f %.4f {item:{id:\"minecraft:paper\",count:1,components:{\"minecraft:item_model\":\"chroma:%s\"}},"
            "item_display:\"fixed\",Tags:[%s],view_range:5f,transformation:{left_rotation:[%s],right_rotation:[0f,0f,0f,1f],translation:[0f,0f,0f],scale:[%s]}%s}"
            % (p[0], p[1], p[2], model, ",".join('"%s"' % t for t in tags), ",".join(F(v) for v in q), ",".join(F(v) for v in sc), extra))
def kill(p):
    return "execute in minecraft:overworld run kill @e[type=minecraft:block_display,tag=chroma,x=%.4f,y=%.4f,z=%.4f,distance=..0.05]" % tuple(p)
pos = json.load(open(POS)); cmds = []
for e in pos["pennants"]:
    p = e["p"]; cmds.append(kill(p))
    th = -e["ang"] + math.pi                                # outward, compensating item_display's 180° flip
    cmds.append(summon((p[0], p[1] - 0.69, p[2]), "pennant", qaxis(0, 1, 0, th), (2.2, 2.2, 2.2), ["chroma", "chroma_model", "chroma_pennant"]))
for p in pos["chandeliers"]:
    cmds.append(kill(p))
    cmds.append(summon(p, "chandelier", (0, 0, 0, 1), (2.5, 2.5, 2.5), ["chroma", "chroma_model", "chroma_chandelier"], ",brightness:{sky:15,block:15}"))
for e in pos["buttresses"]:
    p0, p1 = e["p0"], e["p1"]; cmds.append(kill(p0))
    v = [p1[i] - p0[i] for i in range(3)]; L = math.sqrt(sum(c * c for c in v)); h = math.hypot(v[0], v[2])
    elev = math.atan2(v[1], h); yaw = math.atan2(v[0] / h, v[2] / h)
    q = qmul(qaxis(0, 1, 0, yaw), qaxis(1, 0, 0, -elev))
    mid = [p0[i] + v[i] / 2 for i in range(3)]
    cmds.append(summon(mid, "buttress", q, (2.93, 2.6, L / 3), ["chroma", "chroma_model", "chroma_buttress"]))
json.dump(cmds, open(os.path.join(D, "swap_cmds.json"), "w"))
print("pack", len(data), "sha1", hashlib.sha1(data).hexdigest(), "cmds", len(cmds))
