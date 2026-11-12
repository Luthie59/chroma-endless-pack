"""v14: wider fixed-width scoreboard (separator 320px -> 161 advance) and matching background panel."""
import hashlib, io, json, os, sys, zipfile
import numpy as np
from PIL import Image, ImageDraw

D = sys.argv[1]
SRC = os.path.join(D, "ChromaEndless-Pack13.zip"); OUTZ = os.path.join(D, "ChromaEndless-Pack14.zip")
def save(im): b = io.BytesIO(); im.save(b, "PNG", optimize=True); return b.getvalue()
files = {}
with zipfile.ZipFile(SRC) as z:
    for n in z.namelist(): files[n] = z.read(n)

# separator 240x14 -> 320x14 : stretch the plain line on both sides of the centre motif
sep = Image.open(io.BytesIO(files["assets/chroma/textures/font/sb_separator.png"])).convert("RGBA")
a = np.asarray(sep)
L, M, R = a[:, :90], a[:, 90:150], a[:, 150:]
fillL = np.repeat(a[:, 85:86], 40, axis=1); fillR = np.repeat(a[:, 155:156], 40, axis=1)
sep2 = Image.fromarray(np.concatenate([L, fillL, M, fillR, R], axis=1), "RGBA")
assert sep2.size == (320, 14)
files["assets/chroma/textures/font/sb_separator.png"] = save(sep2)
SEP_ADV = 320 * 7 // 14 + 1          # 161

# panel exactly as wide as the board
PW, PH = SEP_ADV, 146
grad = np.linspace(0, 1, PH)[:, None]
bg = np.dstack([np.full((PH, PW), 14.) + 10 * grad, np.full((PH, PW), 18.) + 12 * grad, np.full((PH, PW), 40.) + 18 * grad, np.full((PH, PW), 205.)])
panel = Image.fromarray(bg.astype(np.uint8), "RGBA")
wm = Image.new("RGBA", (PW, PH), (0, 0, 0, 0)); dw = ImageDraw.Draw(wm)
cx, cy = PW / 2, PH / 2
for r_, w_ in ((56, 2), (44, 1), (15, 1)): dw.ellipse([cx - r_, cy - r_, cx + r_, cy + r_], outline=(246, 200, 80, 40), width=w_)
for k in range(6):
    an = k * np.pi / 3 + .4; x0, y0 = cx + 50 * np.cos(an), cy + 50 * np.sin(an)
    dw.ellipse([x0 - 7, y0 - 7, x0 + 7, y0 + 7], outline=(246, 200, 80, 34), width=1)
    dw.line([(cx + 15 * np.cos(an), cy + 15 * np.sin(an)), (cx + 43 * np.cos(an), cy + 43 * np.sin(an))], fill=(246, 200, 80, 26), width=1)
panel.alpha_composite(wm)
dp = ImageDraw.Draw(panel)
dp.rectangle([0, 0, PW - 1, PH - 1], outline=(200, 150, 50, 255), width=1)
dp.rectangle([2, 2, PW - 3, PH - 3], outline=(110, 80, 30, 200), width=1)
for (x0, y0) in ((0, 0), (PW - 7, 0), (0, PH - 7), (PW - 7, PH - 7)):
    dp.rectangle([x0, y0, x0 + 6, y0 + 6], fill=(246, 200, 80, 255)); dp.rectangle([x0 + 2, y0 + 2, x0 + 4, y0 + 4], fill=(120, 80, 20, 255))
files["assets/chroma/textures/font/sb_panel.png"] = save(panel)

font = json.loads(files["assets/minecraft/font/default.json"])
for p in font["providers"]:
    if p.get("type") == "space" and "" in p.get("advances", {}): p["advances"][""] = -(PW + 1)
files["assets/minecraft/font/default.json"] = json.dumps(font, ensure_ascii=True, indent=1).encode()

buf = io.BytesIO()
with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as z:
    for p in sorted(files):
        zi = zipfile.ZipInfo(p, date_time=(2026, 1, 1, 0, 0, 0)); zi.compress_type = zipfile.ZIP_DEFLATED; z.writestr(zi, files[p])
data = buf.getvalue(); open(OUTZ, "wb").write(data)
prev = Image.new("RGBA", (PW + 20, PH + 20), (90, 110, 130, 255)); prev.alpha_composite(panel, (10, 10))
s2 = sep2.resize((161, 7)); prev.alpha_composite(s2, (10, 11)); prev.alpha_composite(s2, (10, 10 + 15 * 9 + 1))
prev.resize(((PW + 20) * 2, (PH + 20) * 2), Image.NEAREST).save(os.path.join(D, "pack14_preview.png"))
print(hashlib.sha1(data).hexdigest(), PW)
