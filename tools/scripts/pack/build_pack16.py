"""v16: adaptive scoreboard that actually renders.
Minecraft packs font glyphs into 256x256 atlas pages: any glyph image wider/taller than 256 px is silently dropped.
So the background is 2 tiles (170x137) and the separator 4 tiles (170x14 at height 7). Sidebar max = 15 lines.
Watermark = original circular-script ("gallifreyan-like") writing, procedurally drawn.
  line 1 = F3(-2) F1(panel L) 1C(-1) F4(panel R) F2(-339) | 19(sep start) 1C 1D 1C 1D 1C 1D 1B(-341)"""
import hashlib, io, json, math, os, random, sys, zipfile
import numpy as np
from PIL import Image, ImageDraw

D = sys.argv[1]
SRC = os.path.join(D, "ChromaEndless-Pack15.zip"); OUTZ = os.path.join(D, "ChromaEndless-Pack16.zip")
def save(im):
    assert im.width <= 256 and im.height <= 256, ("glyph too big", im.size)
    b = io.BytesIO(); im.save(b, "PNG", optimize=True); return b.getvalue()
files = {}
with zipfile.ZipFile(SRC) as z:
    for n in z.namelist(): files[n] = z.read(n)
GOLD, GOLD_L = (246, 200, 80, 255), (255, 232, 150, 255)
U = lambda cp: chr(cp)

# ---------------- separator tiles (2x res, rendered at height 7)
TW = 170
def sep_tile(start):
    im = Image.new("RGBA", (TW, 14), (0, 0, 0, 0)); d = ImageDraw.Draw(im)
    x0 = 10 if start else 0
    d.line([(x0, 7), (TW - 1, 7)], fill=GOLD, width=2)
    d.line([(x0, 5), (TW - 1, 5)], fill=(246, 200, 80, 70)); d.line([(x0, 9), (TW - 1, 9)], fill=(246, 200, 80, 70))
    if start:
        d.ellipse([0, 2, 10, 12], fill=GOLD); d.ellipse([3, 5, 7, 9], fill=GOLD_L)
    for x in range(40 if start else 2, TW, 48):
        d.polygon([(x, 3), (x + 4, 7), (x, 11), (x - 4, 7)], fill=GOLD); d.point((x, 7), fill=GOLD_L)
    return im
files["assets/chroma/textures/font/sb_separator.png"] = save(sep_tile(True))
files["assets/chroma/textures/font/sb_separator_c.png"] = save(sep_tile(False))
SEP_TILE_ADV = TW // 2 + 1                       # 86
SEP_TOTAL = 4 * SEP_TILE_ADV - 3                 # 341

# ---------------- background (340 x 137) with circular-script watermark, cut in two tiles
PW, PH = 340, 137
grad = np.linspace(0, 1, PH)[:, None] * np.ones((1, PW))
bg = np.dstack([14 + 10 * grad, 18 + 12 * grad, 40 + 18 * grad, np.full((PH, PW), 205.)])
panel = Image.fromarray(bg.astype(np.uint8), "RGBA")

rnd = random.Random(1963)
wm = Image.new("RGBA", (PW, PH), (0, 0, 0, 0)); dw = ImageDraw.Draw(wm)
INK = lambda a: (246, 200, 80, a)
def word(cx, cy, r, a=60):
    """one 'word': a circle with letter arcs cut into its rim, inner circles, dots and strokes."""
    dw.ellipse([cx - r, cy - r, cx + r, cy + r], outline=INK(a), width=1)
    n = rnd.randint(3, 6); base = rnd.random() * 360
    for k in range(n):
        ang = base + k * 360 / n + rnd.uniform(-12, 12); rad = math.radians(ang)
        lr = r * rnd.uniform(.22, .38)
        kind = rnd.choice(["arc", "inner", "on", "cut"])
        if kind == "inner":        # letter circle inside the word
            d_ = r - lr - 2; lx, ly = cx + d_ * math.cos(rad), cy + d_ * math.sin(rad)
            dw.ellipse([lx - lr, ly - lr, lx + lr, ly + lr], outline=INK(a), width=1)
        elif kind == "on":         # letter circle sitting on the rim
            lx, ly = cx + r * math.cos(rad), cy + r * math.sin(rad)
            dw.ellipse([lx - lr, ly - lr, lx + lr, ly + lr], outline=INK(a), width=1)
        else:                      # arc bitten into the rim
            d_ = r * (.92 if kind == "arc" else 1.05); lx, ly = cx + d_ * math.cos(rad), cy + d_ * math.sin(rad)
            dw.arc([lx - lr, ly - lr, lx + lr, ly + lr], ang + 90, ang + 270, fill=INK(a), width=1)
        for _ in range(rnd.randint(0, 3)):    # vowel dots
            dd = rnd.uniform(.3, .7) * r; da = rad + rnd.uniform(-.3, .3)
            px_, py_ = cx + dd * math.cos(da), cy + dd * math.sin(da)
            dw.ellipse([px_ - 1, py_ - 1, px_ + 1, py_ + 1], fill=INK(a + 10))
        if rnd.random() < .4:      # stroke toward the centre
            dw.line([(cx + r * .2 * math.cos(rad), cy + r * .2 * math.sin(rad)), (cx + r * .85 * math.cos(rad), cy + r * .85 * math.sin(rad))], fill=INK(a - 15), width=1)
def sentence(cx, cy, R, words, a=55):
    """a 'sentence': double outer ring, words placed around the inside, joined by lines."""
    dw.ellipse([cx - R, cy - R, cx + R, cy + R], outline=INK(a), width=2)
    dw.ellipse([cx - R + 4, cy - R + 4, cx + R - 4, cy + R - 4], outline=INK(a - 15), width=1)
    pts = []
    for k in range(words):
        ang = math.radians(-90 + k * 360 / words + rnd.uniform(-8, 8)); wr = R * rnd.uniform(.24, .32)
        d_ = R - wr - 7; wx, wy = cx + d_ * math.cos(ang), cy + d_ * math.sin(ang)
        word(wx, wy, wr, a + 5); pts.append((wx, wy, wr))
    word(cx, cy, R * .2, a + 10)
    for i in range(len(pts)):                 # connecting lines between words
        if rnd.random() < .7:
            (x1, y1, r1), (x2, y2, r2) = pts[i], pts[(i + rnd.choice([1, 2])) % len(pts)]
            dw.line([(x1, y1), (x2, y2)], fill=INK(a - 25), width=1)
sentence(92, PH / 2, 60, 6)
sentence(232, PH / 2 - 8, 44, 5, a=45)
word(300, 30, 18, 40); word(305, 108, 14, 38); word(18, 20, 10, 40); word(20, 118, 12, 40)
panel.alpha_composite(wm)

dp = ImageDraw.Draw(panel)
dp.line([(0, 0), (PW - 1, 0)], fill=(200, 150, 50, 255)); dp.line([(2, 2), (PW - 1, 2)], fill=(110, 80, 30, 200))
dp.line([(0, 0), (0, PH - 1)], fill=(200, 150, 50, 255)); dp.line([(2, 2), (2, PH - 3)], fill=(110, 80, 30, 200))
# bottom edge = ornamental separator (the 15-line limit leaves no room for a separator line)
bsep = Image.new("RGBA", (PW * 2, 14), (0, 0, 0, 0))
for i in range(4): bsep.alpha_composite(sep_tile(i == 0), (i * TW, 0))
bsep = bsep.resize((PW, 7), Image.LANCZOS)
panel.alpha_composite(bsep, (0, PH - 7))
for y0 in (0,):
    dp.rectangle([0, y0, 6, y0 + 6], fill=GOLD); dp.rectangle([2, y0 + 2, 4, y0 + 4], fill=(120, 80, 20, 255))
dp.polygon([(0, PH // 2 - 6), (4, PH // 2), (0, PH // 2 + 6)], fill=GOLD)
HALF = PW // 2
files["assets/chroma/textures/font/sb_panel.png"] = save(panel.crop((0, 0, HALF, PH)))
files["assets/chroma/textures/font/sb_panel_r.png"] = save(panel.crop((HALF, 0, PW, PH)))

# ---------------- font
font = json.loads(files["assets/minecraft/font/default.json"])
keep = []
for p in font["providers"]:
    if p.get("type") == "space": continue
    if p.get("file") in ("chroma:font/sb_panel.png", "chroma:font/sb_separator.png"): continue
    keep.append(p)
keep += [
    {"type": "bitmap", "file": "chroma:font/sb_panel.png", "ascent": 8, "height": PH, "chars": [U(0xE0F1)]},
    {"type": "bitmap", "file": "chroma:font/sb_panel_r.png", "ascent": 8, "height": PH, "chars": [U(0xE0F4)]},
    {"type": "bitmap", "file": "chroma:font/sb_separator.png", "ascent": 6, "height": 7, "chars": [U(0xE019)]},
    {"type": "bitmap", "file": "chroma:font/sb_separator_c.png", "ascent": 6, "height": 7, "chars": [U(0xE01D)]},
    {"type": "space", "advances": {U(0xE0F3): -2, U(0xE01C): -1, U(0xE0F2): -(2 * (HALF + 1) - 1 - 2), U(0xE01B): -SEP_TOTAL}},
]
font["providers"] = keep
for p in keep:
    for k in p.get("advances", {}): assert len(k) == 1, k
    for s in p.get("chars", []): assert all(0xE000 <= ord(c) <= 0xF8FF for c in s), s
files["assets/minecraft/font/default.json"] = json.dumps(font, ensure_ascii=True, indent=1).encode()
# the line-1 / net-zero arithmetic
line1 = -2 + (HALF + 1) - 1 + (HALF + 1) - (2 * (HALF + 1) - 1 - 2)
assert line1 == 0, line1

buf = io.BytesIO()
with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as z:
    for p in sorted(files):
        zi = zipfile.ZipInfo(p, date_time=(2026, 1, 1, 0, 0, 0)); zi.compress_type = zipfile.ZIP_DEFLATED; z.writestr(zi, files[p])
data = buf.getvalue(); open(OUTZ, "wb").write(data)
scr = Image.new("RGBA", (320, 170), (110, 150, 90, 255)); x = 320 - 3 - 190
scr.alpha_composite(panel.crop((0, 0, 320 - (x - 2), PH)), (x - 2, 20))
st = Image.new("RGBA", (TW * 2, 7)); st.alpha_composite(sep_tile(True).resize((TW // 2, 7)), (0, 0))
for i in range(1, 4): st.alpha_composite(sep_tile(False).resize((TW // 2, 7)), (i * (TW // 2), 0))
scr.alpha_composite(st.crop((0, 0, 320 - x, 7)), (x, 21))
scr.resize((960, 510), Image.NEAREST).save(os.path.join(D, "pack16_preview.png"))
print(hashlib.sha1(data).hexdigest(), "E0F2", -(2 * (HALF + 1) - 1 - 2), "E01B", -SEP_TOTAL)
