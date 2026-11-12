"""v15: adaptive scoreboard. The sidebar is anchored to the right screen edge, so a background that starts at the
board's left edge and is wider than any board simply runs off-screen on the right: it always fits.
Separators get a zero net advance so they never widen the board.
  line 1  = E0F3(-2) E0F1(panel, adv PW+1) E0F2(-(PW-1)) E019(separator) E01B(-sep advance)
  line 16 = E019 E01B"""
import hashlib, io, json, os, sys, zipfile
import numpy as np
from PIL import Image, ImageDraw

D = sys.argv[1]
SRC = os.path.join(D, "ChromaEndless-Pack14.zip"); OUTZ = os.path.join(D, "ChromaEndless-Pack15.zip")
def save(im): b = io.BytesIO(); im.save(b, "PNG", optimize=True); return b.getvalue()
files = {}
with zipfile.ZipFile(SRC) as z:
    for n in z.namelist(): files[n] = z.read(n)
GOLD, GOLD_L, GOLD_D = (246, 200, 80, 255), (255, 232, 150, 255), (150, 105, 30, 255)

# ---- separator: 2x resolution (rendered at height 7 from 14 px), starts with an ornament, runs right
SW = 640; sep = Image.new("RGBA", (SW, 14), (0, 0, 0, 0)); d = ImageDraw.Draw(sep)
d.line([(10, 7), (SW - 1, 7)], fill=GOLD, width=2)
d.line([(10, 5), (SW - 1, 5)], fill=(246, 200, 80, 70)); d.line([(10, 9), (SW - 1, 9)], fill=(246, 200, 80, 70))
d.ellipse([0, 2, 10, 12], fill=GOLD); d.ellipse([3, 5, 7, 9], fill=GOLD_L)                    # left cap
for x in range(40, SW, 48):                                                                   # small diamonds
    d.polygon([(x, 3), (x + 4, 7), (x, 11), (x - 4, 7)], fill=GOLD); d.point((x, 7), fill=GOLD_L)
files["assets/chroma/textures/font/sb_separator.png"] = save(sep)
SEP_ADV = SW * 7 // 14 + 1

# ---- panel: only the left side is ever seen as an edge; top/bottom borders run off-screen
PW, PH = 340, 146
grad = np.linspace(0, 1, PH)[:, None] * np.ones((1, PW))
hfade = np.clip(np.linspace(0, 1, PW)[None, :] * 6, 0, 1) * np.ones((PH, 1))
bg = np.dstack([14 + 10 * grad, 18 + 12 * grad, 40 + 18 * grad, 205 + 0 * hfade])
panel = Image.fromarray(bg.astype(np.uint8), "RGBA")
wm = Image.new("RGBA", (PW, PH), (0, 0, 0, 0)); dw = ImageDraw.Draw(wm)
cx, cy = 88, PH / 2
for r_, w_ in ((56, 2), (44, 1), (15, 1)): dw.ellipse([cx - r_, cy - r_, cx + r_, cy + r_], outline=(246, 200, 80, 38), width=w_)
for k in range(6):
    an = k * np.pi / 3 + .4; x0, y0 = cx + 50 * np.cos(an), cy + 50 * np.sin(an)
    dw.ellipse([x0 - 7, y0 - 7, x0 + 7, y0 + 7], outline=(246, 200, 80, 32), width=1)
    dw.line([(cx + 15 * np.cos(an), cy + 15 * np.sin(an)), (cx + 43 * np.cos(an), cy + 43 * np.sin(an))], fill=(246, 200, 80, 24), width=1)
panel.alpha_composite(wm)
dp = ImageDraw.Draw(panel)
dp.line([(0, 0), (PW - 1, 0)], fill=(200, 150, 50, 255)); dp.line([(0, PH - 1), (PW - 1, PH - 1)], fill=(200, 150, 50, 255))
dp.line([(2, 2), (PW - 1, 2)], fill=(110, 80, 30, 200)); dp.line([(2, PH - 3), (PW - 1, PH - 3)], fill=(110, 80, 30, 200))
dp.line([(0, 0), (0, PH - 1)], fill=(200, 150, 50, 255)); dp.line([(2, 2), (2, PH - 3)], fill=(110, 80, 30, 200))
for y0 in (0, PH - 7):
    dp.rectangle([0, y0, 6, y0 + 6], fill=GOLD); dp.rectangle([2, y0 + 2, 4, y0 + 4], fill=(120, 80, 20, 255))
dp.polygon([(0, PH // 2 - 6), (4, PH // 2), (0, PH // 2 + 6)], fill=GOLD)                       # left-edge clasp
files["assets/chroma/textures/font/sb_panel.png"] = save(panel)

font = json.loads(files["assets/minecraft/font/default.json"])
for p in font["providers"]:
    if p.get("file") == "chroma:font/sb_panel.png": p["height"], p["ascent"] = PH, 8
font["providers"] = [p for p in font["providers"] if p.get("type") != "space"]
font["providers"].append({"type": "space", "advances": {chr(0xE0F2): -(PW - 1), chr(0xE0F3): -2, chr(0xE01B): -SEP_ADV}})
for p in font["providers"]:                       # every key/char must be exactly one codepoint
    for ch in list(p.get("chars", [])) + list(p.get("advances", {}).keys()):
        assert all(len(c) == 1 for c in ([ch] if "advances" in p else ch)), ("bad glyph key", ch)
files["assets/minecraft/font/default.json"] = json.dumps(font, ensure_ascii=True, indent=1).encode()

buf = io.BytesIO()
with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as z:
    for p in sorted(files):
        zi = zipfile.ZipInfo(p, date_time=(2026, 1, 1, 0, 0, 0)); zi.compress_type = zipfile.ZIP_DEFLATED; z.writestr(zi, files[p])
data = buf.getvalue(); open(OUTZ, "wb").write(data)
# preview: a 180-px board at the right edge of a 300-px "screen"
scr = Image.new("RGBA", (300, 190), (110, 150, 90, 255)); x = 300 - 3 - 180
scr.alpha_composite(panel.crop((0, 0, 300 - (x - 2), PH)), (x - 2, 30))
s2 = sep.resize((SW // 2, 7)); scr.alpha_composite(s2.crop((0, 0, 300 - x, 7)), (x, 31)); scr.alpha_composite(s2.crop((0, 0, 300 - x, 7)), (x, 30 + 15 * 9 + 1))
scr.resize((600, 380), Image.NEAREST).save(os.path.join(D, "pack15_preview.png"))
print(hashlib.sha1(data).hexdigest(), SEP_ADV)

