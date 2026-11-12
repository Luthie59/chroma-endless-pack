"""v10: scoreboard icon glyphs + separators, 'La Citadelle' branding, server icon."""
import hashlib, io, json, math, os, sys, zipfile
from PIL import Image, ImageDraw

D = sys.argv[1]
SRC = os.path.join(D, "ChromaEndless-Pack9.zip"); OUTZ = os.path.join(D, "ChromaEndless-Pack10.zip")
GOLD = (246, 200, 78, 255); GOLD_D = (168, 118, 34, 255); GOLD_L = (255, 232, 150, 255)
def png(im): b = io.BytesIO(); im.save(b, "PNG", optimize=True); return b.getvalue()
def canvas(w=16, h=16): return Image.new("RGBA", (w, h), (0, 0, 0, 0))

def emblem():
    im = canvas(); d = ImageDraw.Draw(im)
    d.ellipse([0, 0, 15, 15], outline=GOLD, width=2); d.ellipse([4, 4, 11, 11], outline=GOLD_L, width=1)
    d.ellipse([6, 1, 9, 4], outline=GOLD, width=1); d.point([(7, 7), (8, 8)], fill=GOLD_L)
    return im
def coin():
    im = canvas(); d = ImageDraw.Draw(im)
    d.ellipse([1, 1, 14, 14], fill=GOLD, outline=GOLD_D, width=1); d.ellipse([4, 4, 11, 11], outline=GOLD_D, width=1)
    d.line([(5, 4), (5, 5)], fill=GOLD_L); d.line([(4, 5), (4, 6)], fill=GOLD_L)
    return im
def bolt():
    im = canvas(); d = ImageDraw.Draw(im)
    d.polygon([(9, 0), (3, 9), (7, 9), (5, 15), (13, 5), (8, 5), (11, 0)], fill=(255, 196, 60, 255), outline=(200, 110, 20, 255))
    return im
def shield():
    im = canvas(); d = ImageDraw.Draw(im)
    d.polygon([(2, 1), (13, 1), (13, 8), (7.5, 15), (2, 8)], fill=(170, 26, 38, 255), outline=GOLD)
    d.line([(7, 3), (7, 11)], fill=GOLD); d.line([(4, 6), (11, 6)], fill=GOLD)
    return im
def people():
    im = canvas(); d = ImageDraw.Draw(im)
    for ox, c in ((0, (200, 210, 225, 255)), (6, (240, 244, 250, 255))):
        d.ellipse([2 + ox, 2, 6 + ox, 6], fill=c); d.rounded_rectangle([1 + ox, 8, 7 + ox, 15], radius=2, fill=c)
    return im
def star():
    im = canvas(); d = ImageDraw.Draw(im)
    pts = []
    for k in range(10):
        r = 7.5 if k % 2 == 0 else 3.2; a = -math.pi / 2 + k * math.pi / 5
        pts.append((7.5 + r * math.cos(a), 8 + r * math.sin(a)))
    d.polygon(pts, fill=GOLD, outline=GOLD_D)
    return im
def signal():
    im = canvas(); d = ImageDraw.Draw(im)
    for i, h in enumerate((4, 7, 10, 14)):
        d.rectangle([1 + i * 4, 15 - h, 3 + i * 4, 15], fill=(110, 220, 120, 255), outline=(40, 120, 50, 255))
    return im
def flag():
    im = canvas(); d = ImageDraw.Draw(im)
    d.line([(3, 1), (3, 15)], fill=GOLD_D, width=2); d.polygon([(4, 1), (14, 4), (4, 8)], fill=(200, 40, 40, 255), outline=(120, 20, 20, 255))
    d.rectangle([1, 14, 6, 15], fill=GOLD)
    return im
def member():
    im = canvas(); d = ImageDraw.Draw(im)
    c = (120, 200, 255, 255); d.ellipse([5, 1, 10, 6], fill=c); d.rounded_rectangle([3, 8, 12, 15], radius=3, fill=c)
    return im
def hourglass():
    im = canvas(); d = ImageDraw.Draw(im)
    d.rectangle([2, 0, 13, 1], fill=GOLD_D); d.rectangle([2, 14, 13, 15], fill=GOLD_D)
    d.polygon([(3, 2), (12, 2), (8, 8), (7, 8)], outline=(220, 230, 240, 255)); d.polygon([(7, 8), (8, 8), (12, 13), (3, 13)], outline=(220, 230, 240, 255))
    d.polygon([(5, 4), (10, 4), (8, 7), (7, 7)], fill=GOLD); d.polygon([(4, 12), (11, 12), (8, 10), (7, 10)], fill=GOLD)
    return im
def separator():
    W, H = 240, 14; im = Image.new("RGBA", (W, H), (0, 0, 0, 0)); d = ImageDraw.Draw(im)
    c = H // 2
    for x in range(8, W - 8):
        t = abs(x - W / 2) / (W / 2); a = int(255 * (1 - t ** 3))
        d.point((x, c), fill=(GOLD[0], GOLD[1], GOLD[2], a)); d.point((x, c - 1), fill=(GOLD_L[0], GOLD_L[1], GOLD_L[2], int(a * .5)))
    d.ellipse([W / 2 - 6, c - 6, W / 2 + 6, c + 6], outline=GOLD, width=2); d.ellipse([W / 2 - 2, c - 2, W / 2 + 2, c + 2], fill=GOLD_L)
    for k, s_ in ((-1, 1), (1, 1)):
        cx = W / 2 + k * 22; d.ellipse([cx - 3, c - 3, cx + 3, c + 3], outline=GOLD, width=1)
    d.ellipse([2, c - 2, 6, c + 2], fill=GOLD); d.ellipse([W - 7, c - 2, W - 3, c + 2], fill=GOLD)
    return im
GLYPHS = [("", "emblem", emblem(), 8, 7), ("", "coin", coin(), 8, 7), ("", "bolt", bolt(), 8, 7), ("", "shield", shield(), 8, 7),
          ("", "people", people(), 8, 7), ("", "star", star(), 8, 7), ("", "signal", signal(), 8, 7), ("", "flag", flag(), 8, 7),
          ("", "member", member(), 8, 7), ("", "hourglass", hourglass(), 8, 7), ("", "separator", separator(), 7, 6)]

files = {}
with zipfile.ZipFile(SRC) as z:
    for n in z.namelist(): files[n] = z.read(n)
font = json.loads(files["assets/minecraft/font/default.json"])
font["providers"] = [p for p in font["providers"] if not any(ch in "".join(g[0] for g in GLYPHS) for ch in p.get("chars", []))]
for ch, name, im, h, asc in GLYPHS:
    files[f"assets/chroma/textures/font/sb_{name}.png"] = png(im)
    font["providers"].append({"type": "bitmap", "file": f"chroma:font/sb_{name}.png", "ascent": asc, "height": h, "chars": [ch]})
files["assets/minecraft/font/default.json"] = json.dumps(font, ensure_ascii=True, indent=1).encode()
files["pack.mcmeta"] = json.dumps({"pack": {"description": "§6§lLa Citadelle §7- pack du serveur", "min_format": 75, "max_format": 75}}, ensure_ascii=False, indent=2).encode()
# server-list icon (64x64): golden seal on night-blue
icon = Image.new("RGBA", (64, 64), (14, 18, 38, 255)); d = ImageDraw.Draw(icon)
for r_, w_ in ((29, 3), (22, 2)): d.ellipse([32 - r_, 32 - r_, 32 + r_, 32 + r_], outline=GOLD, width=w_)
for k in range(5):
    a = k * 2 * math.pi / 5 - math.pi / 2; cx, cy = 32 + 13 * math.cos(a), 32 + 13 * math.sin(a)
    d.ellipse([cx - 5, cy - 5, cx + 5, cy + 5], outline=GOLD_L, width=1); d.line([(32, 32), (cx, cy)], fill=GOLD_D, width=1)
d.ellipse([28, 28, 36, 36], fill=GOLD)
for k in range(24):
    a = k * math.pi / 12; d.point((32 + 26 * math.cos(a), 32 + 26 * math.sin(a)), fill=GOLD_L)
icon.convert("RGB").save(os.path.join(D, "server-icon.png"))
buf = io.BytesIO()
with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as z:
    for p in sorted(files):
        zi = zipfile.ZipInfo(p, date_time=(2026, 1, 1, 0, 0, 0)); zi.compress_type = zipfile.ZIP_DEFLATED; z.writestr(zi, files[p])
data = buf.getvalue(); open(OUTZ, "wb").write(data)
sheet = Image.new("RGBA", (360, 120), (40, 42, 50, 255))
for i, (ch, name, im, h, asc) in enumerate(GLYPHS[:-1]): sheet.alpha_composite(im.resize((32, 32), Image.NEAREST), (8 + i * 34, 8))
sheet.alpha_composite(GLYPHS[-1][2], (8, 56)); sheet.alpha_composite(icon.resize((48, 48)), (290, 56))
sheet.save(os.path.join(D, "sb_preview.png"))
print("pack", len(data), "sha1", hashlib.sha1(data).hexdigest())
