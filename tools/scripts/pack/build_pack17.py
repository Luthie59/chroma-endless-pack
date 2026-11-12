"""v17: "Console temporelle" — custom background for the DeluxeMenus main menu (5-row chest, 176x204).
The background is a font glyph put in the menu title:
  title = &f E031(-8) E030(gui 176x204, advance 177) E032(back to title start) &6&l Console Temporelle
Glyph uses ascent 13 so its top lands on the top edge of the container (title is drawn at y+6).
Slot geometry (vanilla generic_54, rows=5): menu slot (r,c) item at x=8+18c, y=18+18r;
"Inventaire" label at y=110; player inventory y=121+18r, hotbar y=179."""
import io, json, math, os, random, sys, zipfile
import numpy as np
from PIL import Image, ImageDraw

D = sys.argv[1]
SRC = os.path.join(D, "ChromaEndless-Pack16.zip"); OUTZ = os.path.join(D, "ChromaEndless-Pack17.zip")
U = chr
W, H = 176, 204
TOP_END = 109                     # navy part = header + 5 menu rows
MENU_SLOTS = [4, 10, 11, 12, 13, 14, 15, 16, 28, 30, 32, 34, 40]

def save(im):
    assert im.width <= 256 and im.height <= 256, ("glyph too big", im.size)
    b = io.BytesIO(); im.save(b, "PNG", optimize=True); return b.getvalue()

files = {}
with zipfile.ZipFile(SRC) as z:
    for n in z.namelist(): files[n] = z.read(n)

GOLD, GOLD_L, GOLD_D = (246, 200, 80, 255), (255, 232, 150, 255), (140, 96, 30, 255)
NAVY_D = (9, 13, 28, 255)
INK = lambda a: (246, 200, 80, a)

# ---------------- base: navy gradient (top) + aged brass parchment (player inventory)
y = np.arange(H)[:, None] * np.ones((1, W))
navy = np.dstack([14 + 9 * y / TOP_END, 19 + 11 * y / TOP_END, 42 + 16 * y / TOP_END, np.full((H, W), 255.)])
img = Image.fromarray(navy.astype(np.uint8), "RGBA")
d = ImageDraw.Draw(img)
d.rectangle([0, TOP_END, W - 1, H - 1], fill=(198, 178, 136, 255))

# ---------------- circular-script watermark (original "gallifreyan-like" writing)
rnd = random.Random(2005)
wm = Image.new("RGBA", (W, H), (0, 0, 0, 0)); dw = ImageDraw.Draw(wm)
def word(cx, cy, r, a):
    dw.ellipse([cx - r, cy - r, cx + r, cy + r], outline=INK(a))
    n = rnd.randint(3, 5); base = rnd.random() * 360
    for k in range(n):
        ang = base + k * 360 / n + rnd.uniform(-12, 12); rad = math.radians(ang); lr = r * rnd.uniform(.22, .36)
        if rnd.random() < .5:
            dd = r - lr - 1; lx, ly = cx + dd * math.cos(rad), cy + dd * math.sin(rad)
            dw.ellipse([lx - lr, ly - lr, lx + lr, ly + lr], outline=INK(a))
        else:
            lx, ly = cx + r * math.cos(rad), cy + r * math.sin(rad)
            dw.arc([lx - lr, ly - lr, lx + lr, ly + lr], ang + 90, ang + 270, fill=INK(a))
        if rnd.random() < .5:
            dw.line([(cx + r * .2 * math.cos(rad), cy + r * .2 * math.sin(rad)),
                     (cx + r * .8 * math.cos(rad), cy + r * .8 * math.sin(rad))], fill=INK(a - 10))
def sentence(cx, cy, R, words, a):
    dw.ellipse([cx - R, cy - R, cx + R, cy + R], outline=INK(a), width=2)
    dw.ellipse([cx - R + 4, cy - R + 4, cx + R - 4, cy + R - 4], outline=INK(a - 12))
    for k in range(words):
        ang = math.radians(-90 + k * 360 / words); wr = R * .27; dd = R - wr - 7
        word(cx + dd * math.cos(ang), cy + dd * math.sin(ang), wr, a)
    word(cx, cy, R * .22, a + 5)
sentence(88, 63, 44, 6, 34)
word(20, 40, 11, 30); word(156, 40, 11, 30); word(22, 92, 9, 28); word(154, 92, 9, 28)
wm_top = Image.new("RGBA", (W, H), (0, 0, 0, 0)); wm_top.paste(wm.crop((0, 17, W, TOP_END)), (0, 17))
img.alpha_composite(wm_top)
d = ImageDraw.Draw(img)

# ---------------- header band + title ornaments (title text sits at x 31..146, y 6..14)
d.rectangle([0, 0, W - 1, 16], fill=(10, 14, 32, 255))
d.line([(3, 16), (W - 4, 16)], fill=GOLD); d.line([(3, 17), (W - 4, 17)], fill=GOLD_D)
for cx in (19, 157):
    d.ellipse([cx - 5, 5, cx + 5, 15], outline=GOLD); d.ellipse([cx - 2, 8, cx + 2, 12], fill=GOLD_L)
    d.line([(cx, 3), (cx, 6)], fill=GOLD)
d.line([(26, 10), (28, 10)], fill=GOLD); d.line([(148, 10), (150, 10)], fill=GOLD)

# ---------------- ornamental divider on the empty 3rd row (y 54..71)
cy = 63
d.line([(10, cy), (W - 11, cy)], fill=GOLD); d.line([(10, cy + 1), (W - 11, cy + 1)], fill=GOLD_D)
for x in (30, 59, 117, 146):
    d.polygon([(x, cy - 3), (x + 3, cy), (x, cy + 3), (x - 3, cy)], fill=GOLD); d.point((x, cy), fill=GOLD_L)
d.ellipse([88 - 7, cy - 7, 88 + 7, cy + 7], fill=(10, 14, 32, 255), outline=GOLD)
d.ellipse([88 - 4, cy - 4, 88 + 4, cy + 4], outline=GOLD_L)
d.line([(88, cy - 3), (88, cy)], fill=GOLD_L); d.line([(88, cy), (90, cy + 1)], fill=GOLD_L)   # clock hands

# ---------------- menu sockets (only on used slots)
def socket(x, y):           # x,y = item corner (16x16)
    d.rectangle([x - 2, y - 2, x + 17, y + 17], fill=GOLD_D)
    d.rectangle([x - 1, y - 1, x + 16, y + 16], fill=GOLD)
    d.rectangle([x, y, x + 15, y + 15], fill=NAVY_D)
    d.line([(x, y), (x + 15, y)], fill=(4, 6, 14, 255)); d.line([(x, y), (x, y + 15)], fill=(4, 6, 14, 255))
    for (px, py) in ((x - 2, y - 2), (x + 17, y - 2), (x - 2, y + 17), (x + 17, y + 17)):
        d.point((px, py), fill=GOLD_L)
for s in MENU_SLOTS:
    r, c = divmod(s, 9); socket(8 + 18 * c, 18 + 18 * r)

# ---------------- transition + player inventory panel
d.line([(0, TOP_END - 1), (W - 1, TOP_END - 1)], fill=GOLD_D)
d.line([(0, TOP_END), (W - 1, TOP_END)], fill=GOLD)
d.line([(0, TOP_END + 1), (W - 1, TOP_END + 1)], fill=(232, 214, 168, 255))
def inv_slot(x, y):
    d.rectangle([x - 1, y - 1, x + 16, y + 16], fill=(150, 128, 88, 255))
    d.line([(x - 1, y - 1), (x + 15, y - 1)], fill=(96, 78, 48, 255)); d.line([(x - 1, y - 1), (x - 1, y + 15)], fill=(96, 78, 48, 255))
    d.line([(x, y + 16), (x + 16, y + 16)], fill=(240, 226, 190, 255)); d.line([(x + 16, y), (x + 16, y + 16)], fill=(240, 226, 190, 255))
for r in range(3):
    for c in range(9): inv_slot(8 + 18 * c, 121 + 18 * r)
for c in range(9): inv_slot(8 + 18 * c, 179)

# ---------------- outer frame (gold, bevelled corners)
d.rectangle([0, 0, W - 1, H - 1], outline=GOLD_D)
d.rectangle([1, 1, W - 2, H - 2], outline=GOLD)
for (x, y) in ((0, 0), (W - 1, 0), (0, H - 1), (W - 1, H - 1)):
    d.point((x, y), fill=(0, 0, 0, 0))
for (x, y) in ((2, 2), (W - 7, 2), (2, H - 7), (W - 7, H - 7)):
    d.rectangle([x, y, x + 4, y + 4], fill=GOLD); d.rectangle([x + 1, y + 1, x + 3, y + 3], fill=GOLD_D); d.point((x + 2, y + 2), fill=GOLD_L)

files["assets/chroma/textures/font/gui_console.png"] = save(img)
img.save(os.path.join(D, "gui_console_preview.png"))

# ---------------- font
TITLE_W = 115                                  # "Console Temporelle" in bold = 97 + 18
TITLE_X = -8 + (W - TITLE_W) // 2 + 1          # start of the title text, relative to the title origin
font = json.loads(files["assets/minecraft/font/default.json"])
provs = [p for p in font["providers"] if p.get("file") != "chroma:font/gui_console.png"]
provs.append({"type": "bitmap", "file": "chroma:font/gui_console.png", "ascent": 13, "height": H, "chars": [U(0xE030)]})
for p in provs:
    if p.get("type") == "space":
        p["advances"][U(0xE031)] = -8
        p["advances"][U(0xE032)] = TITLE_X - (-8 + W + 1)
font["providers"] = provs
for p in provs:
    for k in p.get("advances", {}): assert len(k) == 1, k
files["assets/minecraft/font/default.json"] = json.dumps(font, ensure_ascii=False, indent=1).encode("utf-8")
json.loads(files["assets/minecraft/font/default.json"].decode("utf-8"))

with zipfile.ZipFile(OUTZ, "w", zipfile.ZIP_DEFLATED) as z:
    for n in sorted(files): z.writestr(n, files[n])
print("ok", OUTZ, "E032 =", TITLE_X - (-8 + W + 1))
