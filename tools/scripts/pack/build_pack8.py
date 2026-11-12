"""v8: original detailed blue police-box style portal model + spinning vortex model."""
import hashlib, io, json, math, os, sys, zipfile
import numpy as np
from PIL import Image, ImageDraw, ImageFont, ImageFilter

D = sys.argv[1]
SRC = os.path.join(D, "ChromaEndless-Pack7.zip"); OUTZ = os.path.join(D, "ChromaEndless-Pack8.zip")
rng = np.random.default_rng(7)
def save(im):
    b = io.BytesIO(); im.save(b, "PNG", optimize=True); return b.getvalue()
def noise(h, w, sigma, seed):
    r = np.random.default_rng(seed).standard_normal((h, w))
    fy = np.fft.fftfreq(h)[:, None]; fx = np.fft.fftfreq(w)[None, :]
    a = np.real(np.fft.ifft2(np.fft.fft2(r) * np.exp(-(fx ** 2 + fy ** 2) * (2 * np.pi * sigma) ** 2 / 2)))
    a -= a.min(); return a / (a.max() or 1)

BLUE = np.array([22, 50, 108.])
def painted(h, w, seed):
    grain = np.sin(np.arange(h)[:, None] * .0 + np.arange(w)[None, :] * 0 + noise(h, w, 2, seed) * 8) * .5 + .5
    k = .9 + .08 * noise(h, w, 6, seed + 1) + .04 * grain
    wear = noise(h, w, 1.2, seed + 2) > .88
    col = BLUE * k[..., None]
    col = np.where(wear[..., None], col * 1.25 + 10, col)
    return col
def to_im(col, alpha=None):
    a = np.full(col.shape[:2], 255.) if alpha is None else alpha
    return Image.fromarray(np.clip(np.dstack([col, a]), 0, 255).astype(np.uint8), "RGBA")

# --- wall: 64 x 128, two door leaves, 4 rows (top row windows), recessed panels with bevels
def wall_tex():
    H, W = 128, 64
    col = painted(H, W, 1)
    def rect(x0, y0, x1, y1, f): col[y0:y1, x0:x1] *= f
    def panel(x0, y0, x1, y1):
        col[y0:y1, x0:x1] = painted(y1 - y0, x1 - x0, x0 * 7 + y0) * .78          # recess
        col[y0:y0 + 1, x0:x1] *= .7; col[y0:y1, x0:x0 + 1] *= .7                # shadow top/left
        col[y1 - 1:y1, x0:x1] *= 1.3; col[y0:y1, x1 - 1:x1] *= 1.25            # light bottom/right
    col[:, 31:33] *= .62                                                      # door split
    rows = [(6, 34), (38, 66), (70, 98), (102, 124)]
    for i, (y0, y1) in enumerate(rows):
        for (x0, x1) in ((5, 28), (36, 59)):
            if i == 0:   # window: 2 x 3 panes, warm light, white frame
                col[y0:y1, x0:x1] = np.array([236, 236, 230.])
                for px in range(2):
                    for py in range(3):
                        a0 = x0 + 2 + px * 11; b0 = y0 + 2 + py * 9
                        gl = np.linspace(1.0, .82, 7)[:, None, None]
                        col[b0:b0 + 7, a0:a0 + 9] = np.array([255, 232, 170.]) * gl
            else:
                panel(x0, y0, x1, y1)
    # little notice plaque on the left door, handle on the right
    col[44:58, 9:24] = np.array([236, 232, 220.]); col[46:47, 11:22] = 40; col[49:50, 11:20] = 40; col[52:53, 11:21] = 40; col[55:56, 11:18] = 40
    col[78:84, 37:39] = np.array([200, 170, 90.])
    col[:, :1] *= .7; col[:, -1:] *= .7
    return to_im(col)
def sign_tex():
    W, H = 256, 48
    im = Image.new("RGBA", (W, H), (14, 14, 18, 255)); d = ImageDraw.Draw(im)
    d.rectangle([0, 0, W - 1, H - 1], outline=(40, 60, 110, 255), width=3)
    try: f = ImageFont.truetype("C:/Windows/Fonts/arialbd.ttf", 26)
    except Exception: f = ImageFont.load_default()
    txt = "PORTAIL TEMPOREL"
    bb = d.textbbox((0, 0), txt, font=f); tw, th = bb[2] - bb[0], bb[3] - bb[1]
    d.text(((W - tw) / 2 - bb[0], (H - th) / 2 - bb[1]), txt, font=f, fill=(245, 245, 240, 255))
    im = im.resize((128, 24), Image.LANCZOS)
    return im
def blue_tex():
    return to_im(painted(32, 32, 9))
def lamp_tex():
    y, x = np.mgrid[0:32, 0:32]; dd = np.hypot(x - 15.5, y - 15.5) / 16
    col = np.dstack([255 - 10 * dd, 248 - 40 * dd, 230 - 90 * dd]) * 1.0
    col[:, ::8] *= .75; col[::10, :] *= .8
    return to_im(col)
def vortex_tex():
    W, H = 512, 32
    t = np.linspace(0, 1, W)[None, :]; yy = np.linspace(0, 1, H)[:, None]
    streak = noise(H, W, 1.5, 21)
    c1 = np.array([60, 140, 255.]); c2 = np.array([170, 80, 255.])
    mix_ = (np.sin(t * 2 * np.pi * 3 + streak * 4) * .5 + .5)[..., None]
    col = c1 * (1 - mix_) + c2 * mix_
    glow = np.exp(-((yy - .5) / .28) ** 2)[..., None]
    col = col * (.6 + .7 * glow) + 60 * glow
    col = np.clip(col, 0, 255)
    full = np.zeros((512, 512, 3)); full[:] = col.mean(axis=(0, 1)); full[:H] = col
    return to_im(full)
TEX = {"box_wall": wall_tex(), "box_sign": sign_tex(), "box_blue": blue_tex(), "box_lamp": lamp_tex(), "vortex_band": vortex_tex()}

def faces(tex, main=None, uv=(0, 0, 16, 16), edge=(0, 0, 4, 4)):
    f = {fc: {"uv": list(edge), "texture": "#" + tex} for fc in ("north", "south", "east", "west", "up", "down")}
    for fc in (main or ()): f[fc] = {"uv": list(uv), "texture": "#" + tex}
    return f
def box(frm, to, tex, main=None, uv=(0, 0, 16, 16), edge=(0, 0, 4, 4), rot=None):
    e = {"from": [round(v, 4) for v in frm], "to": [round(v, 4) for v in to], "faces": faces(tex, main, uv, edge)}
    if rot: e["rotation"] = rot
    return e
B = "b"; ALL = ("north", "south", "east", "west", "up", "down")
el = [box((-1, -8, -1), (17, -7, 17), B, ALL, (0, 0, 16, 16))]                                  # plinth
for cx, cz in ((-.5, -.5), (14.5, -.5), (-.5, 14.5), (14.5, 14.5)):
    el.append(box((cx, -7, cz), (cx + 2, 25, cz + 2), B, ALL, (0, 0, 4, 16)))                    # corner posts
el += [box((1.5, -7, .3), (14.5, 21, 1.1), "w", ("north",)), box((1.5, -7, 14.9), (14.5, 21, 15.7), "w", ("south",)),
       box((.3, -7, 1.5), (1.1, 21, 14.5), "w", ("west",)), box((14.9, -7, 1.5), (15.7, 21, 14.5), "w", ("east",)),
       box((1.1, -7, 1.1), (14.9, 21, 14.9), B)]                                                # walls + inner core
el += [box((.6, 21, -.2), (15.4, 24.5, 1.2), "s", ("north",), (0, 0, 16, 16), (0, 0, 1, 1)),
       box((.6, 21, 14.8), (15.4, 24.5, 16.2), "s", ("south",), (0, 0, 16, 16), (0, 0, 1, 1)),
       box((-.2, 21, .6), (1.2, 24.5, 15.4), "s", ("west",), (0, 0, 16, 16), (0, 0, 1, 1)),
       box((14.8, 21, .6), (16.2, 24.5, 15.4), "s", ("east",), (0, 0, 16, 16), (0, 0, 1, 1))]    # sign boxes
el += [box((-1, 24.5, -1), (17, 26, 17), B, ALL), box((.5, 26, .5), (15.5, 27.5, 15.5), B, ALL), box((2.5, 27.5, 2.5), (13.5, 28.6, 13.5), B, ALL)]
el += [box((6, 28.6, 6), (10, 29.2, 10), B, ALL), box((6.6, 29.2, 6.6), (9.4, 31.2, 9.4), "l", ALL),
       box((6.2, 31.2, 6.2), (9.8, 31.7, 9.8), B, ALL), box((7.4, 31.7, 7.4), (8.6, 32, 8.6), B, ALL)]
for e in el:
    for v in e["from"] + e["to"]: assert -16 <= v <= 32
DISP = {"fixed": {"rotation": [0, 0, 0], "translation": [0, 0, 0], "scale": [1, 1, 1]}}
BOX = {"textures": {"b": "chroma:item/box_blue", "w": "chroma:item/box_wall", "s": "chroma:item/box_sign", "l": "chroma:item/box_lamp",
                    "particle": "chroma:item/box_blue"}, "elements": el, "display": DISP}

def ring_y(R, y, t, h, tex, n=16, vspan=1.0):
    L = 2 * math.pi * R / n * 1.04; out = []
    for k in range(n):
        th = k * 2 * math.pi / n; cx, cz = 8 + R * math.cos(th), 8 + R * math.sin(th)
        phi = round(((math.degrees(th) + 90) % 180) / 22.5) * 22.5 % 180
        u0, u1 = k * 16 / n, (k + 1) * 16 / n
        if phi in (67.5, 90.0, 112.5):
            beta = 90 - phi; frm, to = (cx - t / 2, y - h / 2, cz - L / 2), (cx + t / 2, y + h / 2, cz + L / 2); rad = ("east", "west")
        else:
            beta = -phi if phi <= 45 else 180 - phi; frm, to = (cx - L / 2, y - h / 2, cz - t / 2), (cx + L / 2, y + h / 2, cz + t / 2); rad = ("north", "south")
        f = {fc: {"uv": [round(u0, 4), 0, round(u1, 4), vspan] if fc in rad else [round(u0, 4), .2, round(u1, 4), .4], "texture": "#" + tex}
             for fc in ("north", "south", "east", "west", "up", "down")}
        e = {"from": [round(v, 4) for v in frm], "to": [round(v, 4) for v in to], "faces": f}
        if beta: e["rotation"] = {"origin": [round(cx, 4), round(y, 4), round(cz, 4)], "axis": "y", "angle": beta}
        out.append(e)
    return out
vel = []
for i, (R, y) in enumerate(((4, -6), (7, -1), (10, 4), (13, 9), (16, 14), (19, 19))):
    vel += ring_y(R, y, .5, 1.6, "v")
for e in vel:
    for v in e["from"] + e["to"]: assert -16 <= v <= 32, v
VORTEX = {"textures": {"v": "chroma:item/vortex_band", "particle": "chroma:item/vortex_band"}, "elements": vel, "display": DISP}

files = {}
with zipfile.ZipFile(SRC) as z:
    for n in z.namelist(): files[n] = z.read(n)
for k, im in TEX.items(): files[f"assets/chroma/textures/item/{k}.png"] = save(im)
for k, m in (("portal_box", BOX), ("vortex", VORTEX)):
    files[f"assets/chroma/models/item/{k}.json"] = json.dumps(m, indent=1).encode()
    files[f"assets/chroma/items/{k}.json"] = json.dumps({"model": {"type": "minecraft:model", "model": f"chroma:item/{k}"}}).encode()
buf = io.BytesIO()
with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as z:
    for p in sorted(files):
        zi = zipfile.ZipInfo(p, date_time=(2026, 1, 1, 0, 0, 0)); zi.compress_type = zipfile.ZIP_DEFLATED; z.writestr(zi, files[p])
data = buf.getvalue(); open(OUTZ, "wb").write(data)
# preview: front elevation drawing (wall + sign + roof) and the textures
pv = Image.new("RGBA", (420, 300), (60, 70, 90, 255))
pv.paste(TEX["box_wall"].resize((104, 208), Image.NEAREST), (40, 70)); pv.paste(TEX["box_sign"].resize((120, 24), Image.NEAREST), (32, 44))
pv.paste(TEX["box_blue"].resize((136, 20), Image.NEAREST), (24, 24)); pv.paste(TEX["box_lamp"].resize((24, 18), Image.NEAREST), (80, 4))
pv.paste(TEX["box_wall"].resize((128, 256), Image.NEAREST), (200, 20)); pv.paste(TEX["vortex_band"].crop((0, 0, 512, 32)).resize((256, 16)), (160, 280))
pv.save(os.path.join(D, "box_preview.png"))
print("pack", len(data), "sha1", hashlib.sha1(data).hexdigest())
