"""'L'Horloge Éternelle' for the Instant Éternel overlay pack: original astronomical clock face (128 px),
frozen hands (18:21, the island's hour) with a heart-tipped minute hand, monogram back plate and an orrery ring.
Returns {pack path: bytes} to merge into Amitie-Overlay.zip."""
import io, json, math
from PIL import Image, ImageDraw

N = 128
C = N / 2
GOLD_D, GOLD, GOLD_L, GOLD_XL = (150, 100, 30, 255), (226, 176, 64, 255), (252, 216, 120, 255), (255, 244, 200, 255)
NAVY = (22, 22, 58, 255)
PINK, PINK_D = (255, 150, 200, 255), (200, 70, 130, 255)

# 3x5 pixel glyphs (scaled x2) for the numerals and the monogram
GLYPHS = {
    "I": ["###", ".#.", ".#.", ".#.", "###"], "V": ["#.#", "#.#", "#.#", "#.#", ".#."], "X": ["#.#", "#.#", ".#.", "#.#", "#.#"],
    "L": ["#..", "#..", "#..", "#..", "###"], "M": ["#.#", "###", "###", "#.#", "#.#"],
}
def text(d, s, cx, cy, col, k=2):
    w = len(s) * 4 * k - k
    x0 = int(cx - w / 2); y0 = int(cy - 5 * k / 2)
    for i, ch in enumerate(s):
        for r, row in enumerate(GLYPHS[ch]):
            for c, v in enumerate(row):
                if v == "#": d.rectangle([x0 + (i * 4 + c) * k, y0 + r * k, x0 + (i * 4 + c) * k + k - 1, y0 + r * k + k - 1], fill=col)

def heart(d, cx, cy, s, fill, outline=None):
    pts = []
    for t in range(0, 360, 6):
        a = math.radians(t)
        x = 16 * math.sin(a) ** 3
        y = -(13 * math.cos(a) - 5 * math.cos(2 * a) - 2 * math.cos(3 * a) - math.cos(4 * a))
        pts.append((cx + x * s / 16, cy + y * s / 16))
    d.polygon(pts, fill=fill, outline=outline)

def ring(d, r0, r1, col):
    d.ellipse([C - r1, C - r1, C + r1, C + r1], fill=col)
    d.ellipse([C - r0, C - r0, C + r0, C + r0], fill=(0, 0, 0, 0))

def face():
    im = Image.new("RGBA", (N, N), (0, 0, 0, 0))
    px = im.load()
    for y in range(N):                                  # sunset enamel dial
        for x in range(N):
            dx, dy = x - C + .5, y - C + .5
            d = math.hypot(dx, dy)
            if d <= 46:
                t = (dy + 46) / 92
                top, mid, bot = (40, 30, 90), (220, 90, 140), (255, 170, 80)
                col = [int(top[i] + (mid[i] - top[i]) * min(1, t * 1.6)) if t < .62 else int(mid[i] + (bot[i] - mid[i]) * (t - .62) / .38) for i in range(3)]
                px[x, y] = tuple(col) + (255,)
    d = ImageDraw.Draw(im)
    for i in range(40):                                 # stars in the upper dial
        a = i * 2.399; r = 8 + (i * 7) % 34
        x, y = C + math.cos(a) * r, C + math.sin(a) * r
        if y < C - 4: d.point((x, y), fill=(255, 250, 220, 255))
    d.ellipse([C - 9, C + 22, C + 9, C + 40], fill=(255, 226, 150, 255))   # setting sun on the dial's horizon
    d.rectangle([C - 46, C + 31, C + 46, C + 46], fill=None)
    for r in (40, 33):                                  # golden circular script rings
        d.ellipse([C - r, C - r, C + r, C + r], outline=GOLD, width=1)
    for k in range(10):
        a = k * 2 * math.pi / 10
        x, y = C + math.cos(a) * 36.5, C + math.sin(a) * 36.5
        rr = 3 if k % 2 else 2
        d.ellipse([x - rr, y - rr, x + rr, y + rr], outline=GOLD_L)
        if k % 3 == 0: d.point((x, y), fill=GOLD_XL)
    band = Image.new("RGBA", (N, N), (0, 0, 0, 0)); bd = ImageDraw.Draw(band)
    ring(bd, 46, 57, NAVY)                              # numeral band on its own layer (ring() clears its centre)
    im.alpha_composite(band)
    for h in range(12):
        a = math.radians(h * 30 - 90)
        x, y = C + math.cos(a) * 51.5, C + math.sin(a) * 51.5
        numeral = ["XII", "I", "II", "III", "IV", "V", "VI", "VII", "VIII", "IX", "X", "XI"][h]
        k = 1 if len(numeral) > 2 else 2
        text(d, numeral, x, y, GOLD_L, k)
    im2 = Image.new("RGBA", (N, N), (0, 0, 0, 0)); d2 = ImageDraw.Draw(im2)   # bezel with ticks and gems
    ring(d2, 57, 63, GOLD)
    d2.ellipse([C - 63, C - 63, C + 63, C + 63], outline=GOLD_D, width=1)
    d2.ellipse([C - 57, C - 57, C + 57, C + 57], outline=GOLD_D, width=1)
    for m in range(60):
        a = math.radians(m * 6)
        r0 = 58.5 if m % 5 else 57.5
        d2.line([(C + math.cos(a) * r0, C + math.sin(a) * r0), (C + math.cos(a) * 61.5, C + math.sin(a) * 61.5)], fill=GOLD_D if m % 5 else GOLD_XL)
    for g in range(12):
        a = math.radians(g * 30 + 15)
        x, y = C + math.cos(a) * 60, C + math.sin(a) * 60
        d2.ellipse([x - 1.6, y - 1.6, x + 1.6, y + 1.6], fill=PINK if g % 2 else (170, 120, 255, 255))
    for y in range(N):                                  # bezel highlight top-left
        for x in range(N):
            p = im2.getpixel((x, y))
            if p[3] and (x + y) < N * .8: im2.putpixel((x, y), tuple(min(255, int(v * 1.12)) for v in p[:3]) + (255,))
    im.alpha_composite(im2)
    d = ImageDraw.Draw(im)
    text(d, "L", C - 9, C + 14, GOLD_XL, 1); text(d, "M", C + 9, C + 14, GOLD_XL, 1)
    heart(d, C, C + 14, 4, PINK)
    return im

def hands():
    im = Image.new("RGBA", (N, N), (0, 0, 0, 0)); d = ImageDraw.Draw(im)
    def hand(angle_deg, length, width, tip_heart):
        a = math.radians(angle_deg - 90)
        ex, ey = C + math.cos(a) * length, C + math.sin(a) * length
        bx, by = C - math.cos(a) * 8, C - math.sin(a) * 8
        nx, ny = -math.sin(a) * width, math.cos(a) * width
        d.polygon([(bx, by), (C + nx, C + ny), (ex, ey), (C - nx, C - ny)], fill=GOLD, outline=GOLD_D)
        d.line([(C, C), (ex, ey)], fill=GOLD_XL)
        if tip_heart: heart(d, ex, ey, 6, PINK, PINK_D)
        else: d.ellipse([ex - 2.5, ey - 2.5, ex + 2.5, ey + 2.5], fill=GOLD_L, outline=GOLD_D)
    hand((6 + 21 / 60) * 30, 30, 3.2, False)            # hour hand  -> 18:21, the island's frozen hour
    hand(21 * 6, 44, 2.4, True)                          # minute hand, heart-tipped
    d.ellipse([C - 5, C - 5, C + 5, C + 5], fill=GOLD, outline=GOLD_D)
    heart(d, C, C - .5, 4, PINK, PINK_D)
    return im

def back():
    im = Image.new("RGBA", (N, N), (0, 0, 0, 0)); d = ImageDraw.Draw(im)
    d.ellipse([C - 63, C - 63, C + 63, C + 63], fill=GOLD_D)
    d.ellipse([C - 60, C - 60, C + 60, C + 60], fill=(120, 80, 24, 255))
    for r in (52, 44, 20):
        d.ellipse([C - r, C - r, C + r, C + r], outline=GOLD, width=1)
    for k in range(24):
        a = k * math.pi / 12
        d.line([(C + math.cos(a) * 44, C + math.sin(a) * 44), (C + math.cos(a) * 52, C + math.sin(a) * 52)], fill=GOLD_L)
    text(d, "L", C - 16, C, GOLD_XL, 3); text(d, "M", C + 16, C, GOLD_XL, 3)
    heart(d, C, C + 1, 7, PINK, PINK_D)
    return im

def orrery_ring():
    im = Image.new("RGBA", (N, N), (0, 0, 0, 0)); d = ImageDraw.Draw(im)
    ring(d, 58, 63, GOLD)
    d.ellipse([C - 63, C - 63, C + 63, C + 63], outline=GOLD_D, width=1)
    d.ellipse([C - 58, C - 58, C + 58, C + 58], outline=GOLD_XL, width=1)
    for k in range(16):                                 # small circles hanging inward (circular script)
        a = k * 2 * math.pi / 16
        x, y = C + math.cos(a) * 55, C + math.sin(a) * 55
        r = 3 if k % 2 else 2
        d.ellipse([x - r, y - r, x + r, y + r], outline=GOLD_L)
        if k % 4 == 0:
            d.ellipse([x - 1.5, y - 1.5, x + 1.5, y + 1.5], fill=PINK)
    return im

def giant_ring():
    """256 px ring for the huge armillary rings around the island: thin gold band, circular script, gems."""
    G = 256; c = G / 2
    im = Image.new("RGBA", (G, G), (0, 0, 0, 0)); d = ImageDraw.Draw(im)
    d.ellipse([c - 127, c - 127, c + 127, c + 127], fill=GOLD)
    d.ellipse([c - 120, c - 120, c + 120, c + 120], fill=(0, 0, 0, 0))
    d.ellipse([c - 127, c - 127, c + 127, c + 127], outline=GOLD_D, width=1)
    d.ellipse([c - 120, c - 120, c + 120, c + 120], outline=GOLD_D, width=1)
    d.ellipse([c - 123.5, c - 123.5, c + 123.5, c + 123.5], outline=GOLD_XL, width=1)
    for k in range(72):                                  # engraved ticks along the band
        a = k * 2 * math.pi / 72
        d.line([(c + math.cos(a) * 121, c + math.sin(a) * 121), (c + math.cos(a) * 122.5, c + math.sin(a) * 122.5)], fill=GOLD_D)
    for k in range(24):                                  # circular-script words hanging inward
        a = k * 2 * math.pi / 24 + .13
        x, y = c + math.cos(a) * 113, c + math.sin(a) * 113
        r = 5 if k % 3 == 0 else 3.5
        d.ellipse([x - r, y - r, x + r, y + r], outline=GOLD_L, width=1)
        if k % 3 == 0:
            d.ellipse([x - 2, y - 2, x + 2, y + 2], outline=GOLD_L)
            d.line([(x, y), (c + math.cos(a) * 120, c + math.sin(a) * 120)], fill=GOLD_L)
        else:
            d.point((x + 1, y - 1), fill=GOLD_XL)
    for k in range(12):                                  # gems set in the band
        a = k * 2 * math.pi / 12
        x, y = c + math.cos(a) * 123.5, c + math.sin(a) * 123.5
        d.ellipse([x - 2.5, y - 2.5, x + 2.5, y + 2.5], fill=PINK if k % 2 else (170, 120, 255, 255), outline=GOLD_D)
    return im

def star(letter, main, light, dark, gem, ink):
    """a five-pointed bevelled star with a halo, a gem heart and the friend's initial."""
    im = Image.new("RGBA", (N, N), (0, 0, 0, 0)); px = im.load()
    for y in range(N):                                   # soft halo
        for x in range(N):
            d = math.hypot(x - C + .5, y - C + .5)
            a = max(0.0, 1 - d / 63) ** 2.2
            if a > .02: px[x, y] = light[:3] + (int(a * 150),)
    d = ImageDraw.Draw(im)
    pts = []
    for k in range(10):
        a = math.radians(-90 + k * 36); r = 54 if k % 2 == 0 else 22
        pts.append((C + math.cos(a) * r, C + math.sin(a) * r))
    for k in range(10):                                  # bevel: each half-branch lit or shaded
        tri = [(C, C), pts[k], pts[(k + 1) % 10]]
        d.polygon(tri, fill=light if k % 2 == 0 else main)
    d.polygon(pts, outline=dark)
    for k in range(0, 10, 2): d.line([(C, C), pts[k]], fill=dark)
    d.ellipse([C - 15, C - 15, C + 15, C + 15], fill=dark)
    d.ellipse([C - 13, C - 13, C + 13, C + 13], fill=gem)
    d.ellipse([C - 9, C - 11, C - 3, C - 5], fill=tuple(min(255, v + 90) for v in gem[:3]) + (255,))
    text(d, letter, C, C + 1, ink, 3)
    return im

def light_thread():
    im = Image.new("RGBA", (16, 16), (0, 0, 0, 0)); px = im.load()
    for y in range(16):
        for x in range(16):
            v = 1 - abs(x - 7.5) / 8
            px[x, y] = (255, int(220 + 35 * v), int(150 + 90 * v), int(120 + 135 * v))
    return im

def png(im):
    b = io.BytesIO(); im.save(b, "PNG", optimize=True); return b.getvalue()

def build():
    f = {}
    t = "assets/chroma/textures/item/"
    f[t + "horloge_face.png"] = png(face())
    f[t + "horloge_hands.png"] = png(hands())
    f[t + "horloge_back.png"] = png(back())
    f[t + "anneau_eternel.png"] = png(orrery_ring())
    f[t + "anneau_geant.png"] = png(giant_ring())
    f[t + "etoile_l.png"] = png(star("L", (226, 176, 64, 255), (255, 236, 160, 255), (150, 100, 30, 255), (60, 90, 220, 255), GOLD_XL))
    f[t + "etoile_m.png"] = png(star("M", (226, 226, 238, 255), (255, 255, 255, 255), (140, 140, 170, 255), (255, 120, 180, 255), (255, 255, 255, 255)))
    f[t + "fil_lumiere.png"] = png(light_thread())
    plate = lambda z0, z1, north, south: {"from": [0, 0, z0], "to": [16, 16, z1], "faces": {
        **({"north": {"uv": [0, 0, 16, 16], "texture": north}} if north else {}),
        **({"south": {"uv": [0, 0, 16, 16], "texture": south}} if south else {})}}
    f["assets/chroma/models/item/horloge_eternelle.json"] = json.dumps({
        "textures": {"face": "chroma:item/horloge_face", "hands": "chroma:item/horloge_hands", "back": "chroma:item/horloge_back",
                     "particle": "chroma:item/horloge_face"},
        "elements": [plate(7.75, 8.25, "#face", "#back"), plate(7.3, 7.3, "#hands", None)]}).encode()
    f["assets/chroma/models/item/anneau_eternel.json"] = json.dumps({
        "textures": {"ring": "chroma:item/anneau_eternel", "particle": "chroma:item/anneau_eternel"},
        "elements": [plate(8, 8, "#ring", "#ring")]}).encode()
    f["assets/chroma/models/item/anneau_geant.json"] = json.dumps({
        "textures": {"ring": "chroma:item/anneau_geant", "particle": "chroma:item/anneau_geant"},
        "elements": [plate(8, 8, "#ring", "#ring")]}).encode()
    for st in ("etoile_l", "etoile_m"):
        f["assets/chroma/models/item/%s.json" % st] = json.dumps({
            "textures": {"s": "chroma:item/" + st, "particle": "chroma:item/" + st},
            "elements": [plate(8, 8, "#s", "#s")]}).encode()
    f["assets/chroma/models/item/fil_lumiere.json"] = json.dumps({
        "textures": {"t": "chroma:item/fil_lumiere", "particle": "chroma:item/fil_lumiere"},
        "elements": [{"from": [7.5, 7.5, 0], "to": [8.5, 8.5, 16], "faces": {k: {"uv": [0, 0, 16, 16], "texture": "#t"}
                      for k in ("north", "south", "east", "west", "up", "down")}}]}).encode()
    for name in ("horloge_eternelle", "anneau_eternel", "anneau_geant", "etoile_l", "etoile_m", "fil_lumiere"):
        f["assets/chroma/items/%s.json" % name] = json.dumps({"model": {"type": "minecraft:model", "model": "chroma:item/" + name}}).encode()
    return f, {"face": face(), "hands": hands(), "back": back(), "ring": orrery_ring(), "giant": giant_ring()}

if __name__ == "__main__":
    import os, sys
    _, ims = build()
    sheet = Image.new("RGBA", (N * 4 + 30, N), (40, 40, 60, 255))
    combo = ims["face"].copy(); combo.alpha_composite(ims["hands"])
    for i, k in enumerate((combo, ims["back"], ims["ring"], ims["face"])):
        sheet.alpha_composite(k, (i * (N + 10), 0))
    sheet.resize((sheet.width * 2, sheet.height * 2), Image.NEAREST).save(os.path.join(sys.argv[1], "horloge_preview.png"))
    ims["giant"].save(os.path.join(sys.argv[1], "anneau_geant_preview.png"))
    st = Image.new("RGBA", (N * 2 + 10, N), (40, 40, 60, 255))
    st.alpha_composite(star("L", (226, 176, 64, 255), (255, 236, 160, 255), (150, 100, 30, 255), (60, 90, 220, 255), GOLD_XL), (0, 0))
    st.alpha_composite(star("M", (226, 226, 238, 255), (255, 255, 255, 255), (140, 140, 170, 255), (255, 120, 180, 255), (255, 255, 255, 255)), (N + 10, 0))
    st.resize((st.width * 2, st.height * 2), Image.NEAREST).save(os.path.join(sys.argv[1], "etoiles_preview.png"))
    print("ok")
