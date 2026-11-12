"""v7: realistic 64px seamless retextures of the citadel's vanilla blocks (numpy + Pillow)."""
import hashlib, io, json, os, sys, zipfile
import numpy as np
from PIL import Image

D = sys.argv[1]
SRC = os.path.join(D, "ChromaEndless-Pack6.zip"); OUTZ = os.path.join(D, "ChromaEndless-Pack7.zip")
N = 64
rng = np.random.default_rng(42)

def pnoise(sigma, n=N, seed=None):
    """seamless (periodic) gaussian-filtered noise in [0,1]"""
    r = np.random.default_rng(seed) if seed is not None else rng
    w = r.standard_normal((n, n))
    fy = np.fft.fftfreq(n)[:, None]; fx = np.fft.fftfreq(n)[None, :]
    g = np.exp(-(fx ** 2 + fy ** 2) * (2 * np.pi * sigma) ** 2 / 2)
    a = np.real(np.fft.ifft2(np.fft.fft2(w) * g))
    a -= a.min(); a /= (a.max() or 1)
    return a
def fbm(seed, n=N):
    return (pnoise(8, n, seed) * .5 + pnoise(4, n, seed + 1) * .25 + pnoise(2, n, seed + 2) * .15 + pnoise(1, n, seed + 3) * .1)
def rgb(base, k):
    return np.clip(np.stack([base[0] * k, base[1] * k, base[2] * k], -1), 0, 255)
def rgba(arr3, alpha=255):
    a = np.full(arr3.shape[:2] + (1,), alpha, float) if np.isscalar(alpha) else alpha[..., None]
    return np.concatenate([arr3, a], -1)
def save(arr):
    im = Image.fromarray(np.clip(arr, 0, 255).astype(np.uint8), "RGBA")
    b = io.BytesIO(); im.save(b, "PNG", optimize=True); return b.getvalue()
Y, X = np.mgrid[0:N, 0:N]

# ------------------------------------------------ materials
def plaster():
    k = .965 + .05 * (fbm(1) - .5) + .03 * (pnoise(.6, seed=5) - .5)
    pores = (rng.random((N, N)) < .012) * -.07
    return rgba(rgb((236, 233, 227), k + pores))
def travertine():
    band = np.sin((Y / N) * 2 * np.pi * 5 + fbm(7) * 5) * .5 + .5
    k = .9 + .08 * band + .05 * (fbm(8) - .5)
    pores = (pnoise(.7, seed=9) > .78) * -.16
    return rgba(rgb((226, 220, 206), k + pores))
def flagstones():
    tile = (X // 32) + 2 * (Y // 32)
    tone = np.array([.97, 1.03, 1.0, .94])[tile]
    k = tone * (.94 + .1 * (fbm(11) - .5)) + .04 * (1 - ((X % 32) + (Y % 32)) / 64)
    joint = ((X % 32) == 0) | ((Y % 32) == 0)
    k = np.where(joint, .62, k)
    edge = ((X % 32) == 1) | ((Y % 32) == 1)
    k = np.where(edge, k * 1.06, k)
    return rgba(rgb((200, 197, 190), k))
def gray_marble():
    f = fbm(13)
    v = np.abs(np.sin((X + Y * .5) / N * 2 * np.pi * 2 + f * 9))
    vein = np.clip(1 - v / .08, 0, 1)
    k = .9 + .1 * (fbm(14) - .5)
    base = rgb((132, 133, 135), k)
    return rgba(base * (1 - vein[..., None] * .8) + np.array([228, 228, 226]) * vein[..., None] * .8)
def gold_mosaic():
    tx, ty = X // 8, Y // 8
    r = np.random.default_rng(15).random((8, 8))
    k = .78 + .3 * r[ty, tx] + .06 * (pnoise(1.2, seed=16) - .5)
    col = rgb((240, 186, 64), k)
    grout = ((X % 8) == 0) | ((Y % 8) == 0)
    hi = ((X % 8) == 1) | ((Y % 8) == 1)
    col = np.where(grout[..., None], np.array([92, 70, 38]), col)
    col = np.where(hi[..., None], np.clip(col * 1.12, 0, 255), col)
    return rgba(col)
def birch_planks():
    row = Y // 16
    off = np.array([0, 24, 8, 40])[row]
    seam_v = ((X + off) % 32) == 0
    grain = np.sin((Y % 16) * .9 + pnoise(3, seed=17)[Y, X] * 6 + row * 2) * .5 + .5
    k = .9 + .07 * grain + .05 * (fbm(18) - .5) + np.array([0, .03, -.02, .02])[row]
    k = np.where((Y % 16) == 0, .7, k)
    k = np.where(seam_v, .76, k)
    return rgba(rgb((214, 196, 150), k))
def red_grass_top():
    f = fbm(19)
    k = .75 + .3 * f
    blades = pnoise(.55, seed=20) > .64
    col = rgb((128, 22, 30), k)
    col = np.where(blades[..., None], np.clip(rgb((190, 50, 40), .9 + .2 * f), 0, 255), col)
    tips = pnoise(.5, seed=21) > .82
    col = np.where(tips[..., None], np.array([226, 96, 54]), col)
    return rgba(col)
def soil(base, seed):
    f = fbm(seed)
    k = .82 + .25 * f
    col = rgb(base, k)
    peb = pnoise(.8, seed=seed + 1) > .8
    col = np.where(peb[..., None], np.clip(col * 1.18 + 8, 0, 255), col)
    return rgba(col)
def red_grass_side():
    s = soil((112, 58, 44), 30)[..., :3]
    top = red_grass_top()[..., :3]
    edge = 10 + (pnoise(1.5, seed=31)[0] * 8).astype(int)
    mask = Y < edge[X]
    return rgba(np.where(mask[..., None], top, s))
def bookshelf():
    r = np.random.default_rng(33)
    col = rgb((104, 72, 40), .9 + .1 * fbm(34))                 # wood back
    frame = (Y < 3) | (Y >= 61) | ((Y >= 30) & (Y < 34)) | (X < 2) | (X >= 62)
    col = np.where(frame[..., None], rgb((128, 90, 50), .95 + .08 * fbm(35)), col)
    palette = [(120, 24, 30), (30, 70, 48), (36, 52, 104), (110, 70, 30), (70, 30, 80), (150, 120, 60), (90, 26, 22), (40, 90, 96)]
    for y0, y1 in ((3, 30), (34, 61)):
        x = 2
        while x < 62:
            w = int(r.integers(3, 7)); h = int(r.integers(y1 - y0 - 8, y1 - y0))
            if r.random() < .08: x += w; continue                      # a gap
            c = np.array(palette[int(r.integers(0, len(palette)))], float) * (.85 + .3 * r.random())
            xs = slice(x, min(x + w, 62)); ys = slice(y1 - h, y1)
            shade = np.linspace(.8, 1.1, max(1, min(x + w, 62) - x))[None, :, None]
            col[ys, xs] = np.clip(c[None, None, :] * shade, 0, 255)
            band = y1 - h + int(h * .2)
            col[band:band + 1, xs] = np.array([230, 190, 90])
            col[y1 - h:y1 - h + 1, xs] *= .7
            x += w
    return rgba(col)
def lamp(base, edge, seed):
    d = np.hypot((X + .5 - 32) / 32, (Y + .5 - 32) / 32)
    k = np.clip(1 - d * .55, 0, 1)
    col = np.array(edge) + (np.array(base) - np.array(edge)) * k[..., None]
    col = col * (.97 + .05 * pnoise(1.0, seed=seed)[..., None])
    frame = (X < 3) | (X >= 61) | (Y < 3) | (Y >= 61)
    col = np.where(frame[..., None], rgb((196, 150, 60), .85 + .2 * fbm(seed + 1)), col)
    inner = ((X == 3) | (X == 60) | (Y == 3) | (Y == 60)) & ~frame
    col = np.where(inner[..., None], col * .8, col)
    return rgba(col)
def clear_glass():
    a = np.full((N, N), 14.0)
    streak = (np.abs(((X - Y) % 64) - 20) < 2) | (np.abs(((X - Y) % 64) - 26) < 1)
    a = np.where(streak, 46, a)
    frame = (X == 0) | (Y == 0) | (X == N - 1) | (Y == N - 1)
    a = np.where(frame, 80, a)
    col = np.where(frame[..., None], np.array([235, 240, 245.]), np.array([225, 238, 248.]))
    return np.concatenate([np.broadcast_to(col, (N, N, 3)), a[..., None]], -1)
def frosted():
    a = 118 + 22 * (fbm(41) - .5) * 2
    frame = (X == 0) | (Y == 0) | (X == N - 1) | (Y == N - 1)
    a = np.where(frame, 170, a)
    col = rgb((240, 242, 246), .97 + .04 * fbm(42))
    return np.concatenate([col, a[..., None]], -1)
def amber_window():
    d = np.hypot((X + .5 - 32) / 32, (Y + .5 - 32) / 32)
    col = np.array([255, 226, 150.]) * (1 - d[..., None] * .3) + np.array([246, 170, 60.]) * (d[..., None] * .3)
    col = col * (.95 + .08 * pnoise(1.5, seed=43)[..., None])
    a = np.full((N, N), 165.0)
    lead = (np.abs(X - 31.5) < 1) | (np.abs(Y - 31.5) < 1) | (X < 2) | (X >= 62) | (Y < 2) | (Y >= 62)
    col = np.where(lead[..., None], np.array([70, 58, 44.]), col); a = np.where(lead, 245, a)
    return np.concatenate([np.clip(col, 0, 255), a[..., None]], -1)
def pool_mosaic():
    tx, ty = X // 8, Y // 8
    r = np.random.default_rng(45).random((8, 8))
    k = .75 + .35 * r[ty, tx]
    col = rgb((52, 140, 160), k)
    col = np.where((r[ty, tx] > .85)[..., None], rgb((230, 200, 110), .9 + .1 * r[ty, tx]), col)
    grout = ((X % 8) == 0) | ((Y % 8) == 0)
    col = np.where(grout[..., None], np.array([200, 205, 200]), col)
    return rgba(col)
def wool(c, seed):
    weave = (((X // 2) + (Y // 2)) % 2) * .06 - .03
    k = .93 + weave + .06 * (pnoise(.8, seed=seed) - .5) + .05 * (fbm(seed + 1) - .5)
    return rgba(rgb(c, k))

TEX = {
    "white_concrete": plaster(), "calcite": travertine(), "polished_diorite": flagstones(), "light_gray_concrete": gray_marble(),
    "yellow_terracotta": gold_mosaic(), "birch_planks": birch_planks(), "crimson_nylium": red_grass_top(), "crimson_nylium_side": red_grass_side(),
    "red_terracotta": soil((150, 62, 46), 50), "orange_terracotta": soil((166, 92, 50), 52), "terracotta": soil((152, 96, 70), 54),
    "bookshelf": bookshelf(), "ochre_froglight_top": lamp((255, 236, 180), (236, 176, 86), 60), "ochre_froglight_side": lamp((255, 236, 180), (236, 176, 86), 62),
    "pearlescent_froglight_top": lamp((255, 246, 250), (232, 200, 218), 64), "pearlescent_froglight_side": lamp((255, 246, 250), (232, 200, 218), 66),
    "glass": clear_glass(), "white_stained_glass": frosted(), "yellow_stained_glass": amber_window(), "prismarine_bricks": pool_mosaic(),
}
for name, c in (("white", (236, 236, 232)), ("red", (160, 38, 35)), ("orange", (236, 120, 32)), ("yellow", (246, 196, 52)), ("light_blue", (72, 170, 214)),
                ("lime", (122, 190, 42)), ("magenta", (190, 70, 180)), ("cyan", (30, 140, 150)), ("pink", (236, 142, 172))):
    TEX[f"{name}_wool"] = wool(c, 80 + len(name))

files = {}
with zipfile.ZipFile(SRC) as z:
    for n in z.namelist(): files[n] = z.read(n)
for k, arr in TEX.items(): files[f"assets/minecraft/textures/block/{k}.png"] = save(arr)
buf = io.BytesIO()
with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as z:
    for p in sorted(files):
        zi = zipfile.ZipInfo(p, date_time=(2026, 1, 1, 0, 0, 0)); zi.compress_type = zipfile.ZIP_DEFLATED; z.writestr(zi, files[p])
data = buf.getvalue(); open(OUTZ, "wb").write(data)
# preview: each texture tiled 2x2 on a mid-grey background (alpha composited)
names = list(TEX); cols = 6; cell = 128
sheet = Image.new("RGBA", (cols * cell, ((len(names) + cols - 1) // cols) * cell), (90, 110, 130, 255))
for i, n in enumerate(names):
    im = Image.fromarray(np.clip(TEX[n], 0, 255).astype(np.uint8), "RGBA")
    for dx in (0, 64):
        for dy in (0, 64): sheet.alpha_composite(im, ((i % cols) * cell + dx, (i // cols) * cell + dy))
sheet.save(os.path.join(D, "pack7_preview.png"))
print("pack", len(data), "sha1", hashlib.sha1(data).hexdigest(), "textures", len(TEX))
