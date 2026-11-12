"""v18: custom item model for the "Fragment de chronon" (chroma:chronon) — original violet time-crystal shard
with a golden hourglass core and an animated golden glint (8 frames, 32x32).
Used by CitadelleMessages >= 1.4.1 through the item_model component."""
import io, json, os, sys, zipfile
from PIL import Image, ImageDraw

D = sys.argv[1]
SRC = os.path.join(D, "ChromaEndless-Pack17.zip"); OUTZ = os.path.join(D, "ChromaEndless-Pack18.zip")
S = 32
files = {}
with zipfile.ZipFile(SRC) as z:
    for n in z.namelist(): files[n] = z.read(n)

OUT = (34, 14, 66, 255)          # outline
V_D, V_M, V_L, V_XL = (92, 38, 168, 255), (136, 70, 230, 255), (176, 120, 255, 255), (222, 190, 255, 255)
G, G_L, G_D = (246, 200, 80, 255), (255, 236, 160, 255), (170, 118, 30, 255)
WHITE = (255, 255, 255, 255)

def base():
    im = Image.new("RGBA", (S, S), (0, 0, 0, 0)); d = ImageDraw.Draw(im)
    # small companion shard (behind)
    small = [(5, 20), (10, 22), (9, 29), (4, 28)]
    d.polygon(small, fill=V_D, outline=OUT)
    d.line([(6, 22), (8, 27)], fill=V_M)
    # main shard: left facet dark, right facet light, ridge
    top, rt, rb, bot, lb, lt = (17, 1), (25, 9), (22, 26), (15, 30), (9, 21), (11, 8)
    ridge_top, ridge_bot = (17, 2), (16, 29)
    d.polygon([top, ridge_top, ridge_bot, bot, lb, lt], fill=V_M)
    d.polygon([top, rt, rb, bot, ridge_bot, ridge_top], fill=V_L)
    d.polygon([top, rt, rb, bot, lb, lt], outline=OUT)
    d.line([ridge_top, ridge_bot], fill=V_XL)
    d.line([(12, 9), (16, 3)], fill=V_XL)                 # top-left edge light
    d.line([(10, 21), (14, 28)], fill=V_D)                # lower-left shadow
    # golden hourglass core
    cx, cy = 17, 16
    d.polygon([(cx - 3, cy - 5), (cx + 3, cy - 5), (cx, cy)], fill=G, outline=G_D)
    d.polygon([(cx - 3, cy + 5), (cx + 3, cy + 5), (cx, cy)], fill=G, outline=G_D)
    d.line([(cx - 4, cy - 6), (cx + 4, cy - 6)], fill=G_L)
    d.line([(cx - 4, cy + 6), (cx + 4, cy + 6)], fill=G_L)
    d.point((cx, cy + 3), fill=G_L); d.point((cx - 1, cy + 4), fill=G_L); d.point((cx + 1, cy + 4), fill=G_L)
    d.point((cx, cy - 3), fill=G_L)
    # rim glints
    for p in ((20, 5), (23, 9), (13, 12)):
        d.point(p, fill=WHITE)
    return im

def sparkle(im, x, y, size, alpha):
    d = ImageDraw.Draw(im)
    c = (255, 240, 180, alpha); w = (255, 255, 255, alpha)
    for k in range(1, size + 1):
        a = max(40, alpha - 60 * (k - 1))
        for (px, py) in ((x + k, y), (x - k, y), (x, y + k), (x, y - k)):
            if 0 <= px < S and 0 <= py < S: d.point((px, py), fill=(255, 236, 150, a))
    d.point((x, y), fill=w)
    if size >= 2:
        for (px, py) in ((x + 1, y + 1), (x - 1, y - 1), (x + 1, y - 1), (x - 1, y + 1)):
            d.point((px, py), fill=c[:3] + (alpha // 2,))

# glint path: travels up the ridge, then flares at the tip, then rests
path = [(16, 26, 1, 200), (16, 21, 2, 230), (17, 12, 2, 255), (17, 6, 3, 255), (18, 3, 2, 200), None, None, None]
frames = []
for step in path:
    f = base()
    if step: sparkle(f, *step)
    frames.append(f)
strip = Image.new("RGBA", (S, S * len(frames)))
for i, f in enumerate(frames): strip.paste(f, (0, i * S))

def png(im):
    b = io.BytesIO(); im.save(b, "PNG", optimize=True); return b.getvalue()

files["assets/chroma/textures/item/chronon.png"] = png(strip)
files["assets/chroma/textures/item/chronon.png.mcmeta"] = json.dumps(
    {"animation": {"frametime": 3, "interpolate": False}}).encode()
files["assets/chroma/models/item/chronon.json"] = json.dumps(
    {"parent": "minecraft:item/generated", "textures": {"layer0": "chroma:item/chronon"}}, indent=1).encode()
files["assets/chroma/items/chronon.json"] = json.dumps(
    {"model": {"type": "minecraft:model", "model": "chroma:item/chronon"}}).encode()

frames[0].resize((S * 8, S * 8), Image.NEAREST).save(os.path.join(D, "chronon_preview.png"))
strip.resize((S * 4, S * 4 * len(frames)), Image.NEAREST).save(os.path.join(D, "chronon_strip.png"))

with zipfile.ZipFile(OUTZ, "w", zipfile.ZIP_DEFLATED) as z:
    for n in sorted(files): z.writestr(n, files[n])
print("ok", OUTZ)
