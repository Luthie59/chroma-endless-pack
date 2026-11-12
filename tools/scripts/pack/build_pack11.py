"""v11: brass/gold recolours of lantern/end rod/chain/lightning rod (layouts kept from the vanilla client jar),
silver & scarlet trees, aged bricks, and a themed scoreboard background panel (font trick)."""
import hashlib, io, json, os, sys, zipfile
import numpy as np
from PIL import Image, ImageDraw, ImageFilter

D = sys.argv[1]; JAR = sys.argv[2]
SRC = os.path.join(D, "ChromaEndless-Pack10.zip"); OUTZ = os.path.join(D, "ChromaEndless-Pack11.zip")
jar = zipfile.ZipFile(JAR)
def vanilla(name): return Image.open(io.BytesIO(jar.read(f"assets/minecraft/textures/block/{name}.png"))).convert("RGBA")
def has_meta(name): return f"assets/minecraft/textures/block/{name}.png.mcmeta" in jar.namelist()
def save(im): b = io.BytesIO(); im.save(b, "PNG", optimize=True); return b.getvalue()
rng = np.random.default_rng(3)

GOLD_RAMP = np.array([[70, 40, 10], [140, 92, 26], [205, 150, 48], [246, 200, 80], [255, 236, 160]], float)
def ramp(lum, stops=GOLD_RAMP):
    x = np.clip(lum, 0, 1) * (len(stops) - 1); i = np.clip(x.astype(int), 0, len(stops) - 2); f = (x - i)[..., None]
    return stops[i] * (1 - f) + stops[i + 1] * f
def regold(img, keep_bright_colour=False, scale=4, sat_keep=.35):
    """upscale x4 (nearest) and recolour greyish/metal pixels to polished gold by luminance; keep strongly coloured or very bright pixels if asked."""
    im = img.resize((img.width * scale, img.height * scale), Image.NEAREST)
    a = np.asarray(im).astype(float); rgb = a[..., :3]; al = a[..., 3]
    lum = (rgb @ np.array([.299, .587, .114])) / 255
    mx = rgb.max(-1); mn = rgb.min(-1); sat = np.where(mx > 0, (mx - mn) / np.maximum(mx, 1), 0)
    gold = ramp(lum * 1.1)
    # subtle hammered sheen
    sheen = 1 + .06 * (rng.random(lum.shape) - .5)
    gold = np.clip(gold * sheen[..., None], 0, 255)
    if keep_bright_colour:
        keep = (sat > sat_keep) | (lum > .9)
        out = np.where(keep[..., None], np.clip(rgb * 1.05, 0, 255), gold)
    else:
        out = gold
    return Image.fromarray(np.dstack([out, al]).astype(np.uint8), "RGBA")

TEX = {}
TEX["lantern"] = regold(vanilla("lantern"), keep_bright_colour=True, sat_keep=.45)       # brass frame, warm flame kept
TEX["iron_chain"] = regold(vanilla("iron_chain"))
TEX["lightning_rod"] = regold(vanilla("lightning_rod"))
TEX["end_rod"] = regold(vanilla("end_rod"), keep_bright_colour=True, sat_keep=.9)          # white crystal core kept, grey parts gold

# ---- full blocks generated at 64 px (seamless)
N = 64
def pnoise(sigma, seed, h=N, w=N):
    r = np.random.default_rng(seed).standard_normal((h, w))
    fy = np.fft.fftfreq(h)[:, None]; fx = np.fft.fftfreq(w)[None, :]
    a = np.real(np.fft.ifft2(np.fft.fft2(r) * np.exp(-(fx ** 2 + fy ** 2) * (2 * np.pi * sigma) ** 2 / 2)))
    a -= a.min(); return a / (a.max() or 1)
Y, X = np.mgrid[0:N, 0:N]
def im(rgb, alpha=None):
    a = np.full(rgb.shape[:2], 255.) if alpha is None else alpha
    return Image.fromarray(np.clip(np.dstack([rgb, a]), 0, 255).astype(np.uint8), "RGBA")
def bark(base, groove, seed):
    f = pnoise(4, seed, N, N); v = pnoise(1.2, seed + 1)
    fiss = np.abs(np.sin(X / N * 2 * np.pi * 7 + f * 6)) < .18
    k = .86 + .2 * v
    col = np.array(base) * k[..., None]
    col = np.where(fiss[..., None], np.array(groove) * (.9 + .2 * v[..., None]), col)
    return col
def rings(base, ringc, seed):
    d = np.hypot(X + .5 - 32, Y + .5 - 32) + pnoise(3, seed) * 3
    r = (np.sin(d * 1.1) * .5 + .5)
    col = np.array(base) * (.85 + .15 * r[..., None]) + np.array(ringc) * (.15 * (1 - r[..., None]))
    edge = d > 28
    return np.where(edge[..., None], np.array(base) * .75, col)
def foliage(c1, c2, hl, seed, holes=True):
    f = pnoise(1.6, seed); g = pnoise(.8, seed + 1)
    col = np.array(c1) * (1 - f[..., None]) + np.array(c2) * f[..., None]
    col = np.where((g > .72)[..., None], np.array(hl), col)
    alpha = np.where((pnoise(1.2, seed + 2) < .22) & holes, 0, 255.)
    return col, alpha
TEX["pale_oak_log"] = im(bark((214, 216, 222), (120, 124, 136), 11))
TEX["pale_oak_log_top"] = im(rings((222, 224, 230), (150, 154, 166), 12))
c, a = foliage((196, 204, 214), (238, 242, 248), (255, 255, 255), 13); TEX["pale_oak_leaves"] = im(c, a)
TEX["crimson_stem"] = im(bark((128, 26, 38), (62, 10, 20), 14))
TEX["crimson_stem_top"] = im(rings((150, 36, 44), (90, 16, 24), 15))
c, _ = foliage((150, 20, 26), (210, 52, 34), (255, 132, 60), 16, holes=False); TEX["nether_wart_block"] = im(c)
def bricks():
    off = ((Y // 16) % 2) * 16
    mortar = ((Y % 16) < 2) | (((X + off) % 32) < 2)
    tone = pnoise(6, 21)[(Y // 16) * 16 % N, ((X + off) // 32 * 32) % N]
    k = .82 + .25 * tone + .08 * (pnoise(1, 22) - .5)
    col = np.array([150, 70, 52.]) * k[..., None]
    col = np.where(mortar[..., None], np.array([196, 188, 172.]) * (.9 + .1 * pnoise(1, 23)[..., None]), col)
    return im(col)
TEX["bricks"] = bricks()
for k in list(TEX):
    if has_meta(k) and k not in ("lantern",):
        print("note: vanilla animation meta exists for", k)

# ---- scoreboard background panel (124 x 146), placed behind all lines with a negative space
PW, PH = 124, 146
panel = Image.new("RGBA", (PW, PH), (0, 0, 0, 0)); dp = ImageDraw.Draw(panel)
grad = np.linspace(0, 1, PH)[:, None]
bg = np.dstack([np.full((PH, PW), 14.) + 10 * grad, np.full((PH, PW), 18.) + 12 * grad, np.full((PH, PW), 40.) + 18 * grad, np.full((PH, PW), 205.)])
panel = Image.fromarray(bg.astype(np.uint8), "RGBA"); dp = ImageDraw.Draw(panel)
wm = Image.new("RGBA", (PW, PH), (0, 0, 0, 0)); dw = ImageDraw.Draw(wm)
cx, cy = PW / 2, PH / 2
for r_, w_ in ((52, 2), (40, 1), (14, 1)): dw.ellipse([cx - r_, cy - r_, cx + r_, cy + r_], outline=(246, 200, 80, 40), width=w_)
for k in range(6):
    a = k * np.pi / 3 + .4; x0, y0 = cx + 46 * np.cos(a), cy + 46 * np.sin(a)
    dw.ellipse([x0 - 7, y0 - 7, x0 + 7, y0 + 7], outline=(246, 200, 80, 34), width=1)
    dw.line([(cx + 14 * np.cos(a), cy + 14 * np.sin(a)), (cx + 39 * np.cos(a), cy + 39 * np.sin(a))], fill=(246, 200, 80, 26), width=1)
panel.alpha_composite(wm)
dp = ImageDraw.Draw(panel)
dp.rectangle([0, 0, PW - 1, PH - 1], outline=(200, 150, 50, 255), width=1)
dp.rectangle([2, 2, PW - 3, PH - 3], outline=(110, 80, 30, 200), width=1)
for (x0, y0) in ((0, 0), (PW - 7, 0), (0, PH - 7), (PW - 7, PH - 7)):
    dp.rectangle([x0, y0, x0 + 6, y0 + 6], fill=(246, 200, 80, 255)); dp.rectangle([x0 + 2, y0 + 2, x0 + 4, y0 + 4], fill=(120, 80, 20, 255))

files = {}
with zipfile.ZipFile(SRC) as z:
    for n in z.namelist(): files[n] = z.read(n)
for k, img in TEX.items(): files[f"assets/minecraft/textures/block/{k}.png"] = save(img)
files["assets/minecraft/textures/block/lantern.png.mcmeta"] = jar.read("assets/minecraft/textures/block/lantern.png.mcmeta")
files["assets/chroma/textures/font/sb_panel.png"] = save(panel)
font = json.loads(files["assets/minecraft/font/default.json"])
font["providers"] = [p for p in font["providers"] if "" not in p.get("chars", []) and p.get("type") != "space"]
font["providers"].append({"type": "bitmap", "file": "chroma:font/sb_panel.png", "ascent": 8, "height": PH, "chars": [""]})
font["providers"].append({"type": "space", "advances": {"": -(PW + 1)}})
files["assets/minecraft/font/default.json"] = json.dumps(font, ensure_ascii=True, indent=1).encode()
buf = io.BytesIO()
with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as z:
    for p in sorted(files):
        zi = zipfile.ZipInfo(p, date_time=(2026, 1, 1, 0, 0, 0)); zi.compress_type = zipfile.ZIP_DEFLATED; z.writestr(zi, files[p])
data = buf.getvalue(); open(OUTZ, "wb").write(data)
# previews
sheet = Image.new("RGBA", (64 * 6, 64 * 2 + 160), (70, 90, 110, 255))
for i, k in enumerate(["pale_oak_log", "pale_oak_log_top", "pale_oak_leaves", "crimson_stem", "nether_wart_block", "bricks"]):
    sheet.alpha_composite(TEX[k].resize((64, 64)), (i * 64, 0))
for i, k in enumerate(["lantern", "iron_chain", "lightning_rod", "end_rod"]):
    t = TEX[k]; t2 = t.crop((0, 0, t.width, min(t.height, t.width))).resize((64, 64), Image.NEAREST); sheet.alpha_composite(t2, (i * 64, 64))
sheet.alpha_composite(panel, (10, 132))
sheet.save(os.path.join(D, "pack11_preview.png"))
print("pack", len(data), "sha1", hashlib.sha1(data).hexdigest(), "lantern", TEX["lantern"].size)
