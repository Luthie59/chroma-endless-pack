"""Faithful 3D models of the two homes ('b' and 'd') for the private Instant Éternel world.
Original textures drawn procedurally from on-site observation (16 px per metre), dimensions from the cadastre.
b: 5-level 1960s block, 29 x 8.3 m, gravel-panel concrete, two stairwells with red doors under white canopies.
d: 12-storey tower on pilotis, 21.5 x 16.5 m, orange-red terracotta cladding, dark stair strip, balcony stacks.
build() -> ({pack path: bytes}, {preview name: Image})."""
import io, json, math, random
from PIL import Image, ImageDraw

PPM = 16                      # pixels per metre
R = random.Random(818)

def png(im):
    b = io.BytesIO(); im.save(b, "PNG", optimize=True); return b.getvalue()

def speckle(w, h, base, spread, dots):
    """gravel-render / cladding noise."""
    im = Image.new("RGBA", (w, h), base + (255,)); px = im.load()
    for y in range(h):
        for x in range(w):
            j = R.randint(-spread, spread)
            px[x, y] = tuple(max(0, min(255, c + j)) for c in base) + (255,)
    for _ in range(int(w * h * dots)):
        x, y = R.randrange(w), R.randrange(h)
        c = R.choice([(92, 84, 72), (225, 218, 200), (150, 136, 112), (70, 66, 60)])
        px[x, y] = c + (255,)
    return im

# ======================================================================================== b
B_W, B_D, B_H = 29.0, 8.3, 15.2         # body (cornice added as a separate element)
B_PLINTH = 0.9
B_FLOOR = (B_H - B_PLINTH - 0.25) / 5   # ~2.81 m per level
B_COLS = {"A": .178, "C": .341, "D": .443, "E": .555, "F": .657, "H": .824}
B_STAIRS = (.244, .749)
GLASS_DARK, GLASS_LIGHT = (58, 74, 92), (128, 150, 170)

def window(d, cx, top, w, h, kind, rnd):
    """white PVC window; kind: 'curtain', 'shutter', 'open', 'plain'."""
    x0, x1 = int(cx - w / 2), int(cx + w / 2)
    y0, y1 = int(top), int(top + h)
    d.rectangle([x0 - 2, y0 - 2, x1 + 2, y1 + 3], fill=(236, 236, 230, 255))          # reveal / frame
    d.rectangle([x0 - 2, y1 + 2, x1 + 3, y1 + 4], fill=(205, 205, 198, 255))          # sill
    d.line([(x0 - 2, y1 + 5), (x1 + 3, y1 + 5)], fill=(120, 112, 98, 255))           # sill shadow
    for y in range(y0, y1 + 1):                                                        # glass gradient
        t = (y - y0) / max(1, h)
        c = tuple(int(GLASS_LIGHT[i] * (1 - t) + GLASS_DARK[i] * t) for i in range(3))
        d.line([(x0, y), (x1, y)], fill=c + (255,))
    if kind == "shutter":
        d.rectangle([x0, y0, x1, y1], fill=(238, 238, 234, 255))
        for y in range(y0 + 2, y1, 2): d.line([(x0, y), (x1, y)], fill=(214, 214, 208, 255))
    elif kind == "curtain":                      # lace curtains: light folds over the glass, edges still dark
        for x in range(x0 + 2, x1 - 1):
            if (x - x0) % 3 != 0:
                d.line([(x, y0 + 2), (x, y1 - 1)], fill=(196, 202, 212, 255))
        d.line([(x0 + 1, y0 + 2), (x0 + 1, y1 - 1)], fill=GLASS_DARK + (255,)); d.line([(x1 - 1, y0 + 2), (x1 - 1, y1 - 1)], fill=GLASS_DARK + (255,))
    elif kind == "half":
        d.rectangle([x0, y0, x1, int(y0 + h * .55)], fill=(238, 238, 234, 255))
    d.line([(cx, y0), (cx, y1)], fill=(236, 236, 230, 255), width=2)                   # mullion
    d.rectangle([x0, y0, x1, y1], outline=(244, 244, 240, 255), width=1)

def b_facade(front):
    w, h = int(B_W * PPM), int(B_H * PPM)
    im = speckle(w, h, (196, 184, 158), 10, .05)
    d = ImageDraw.Draw(im)
    # panel joints: verticals ~1.45 m, horizontals at sills and lintels of each level
    for x in range(0, w, int(1.45 * PPM)): d.line([(x, 0), (x, h)], fill=(150, 160, 168, 255))
    for lv in range(5):
        top = h - int((B_PLINTH + lv * B_FLOOR + B_FLOOR) * PPM)
        for f in (0.0, .45): d.line([(0, top + int(f * B_FLOOR * PPM)), (w, top + int(f * B_FLOOR * PPM))], fill=(150, 160, 168, 255))
    # plinth
    d.rectangle([0, h - int(B_PLINTH * PPM), w, h], fill=(232, 232, 226, 255))
    d.line([(0, h - int(B_PLINTH * PPM)), (w, h - int(B_PLINTH * PPM))], fill=(196, 196, 188, 255), width=2)
    # regular windows on the 5 levels
    kinds = ["curtain"] * 7 + ["plain"] * 6 + ["half"] * 2 + ["shutter"] * 2
    for col, fx in B_COLS.items():
        ww = 1.9 if col in ("D", "E") else 1.3
        for lv in range(5):
            top = h - int((B_PLINTH + lv * B_FLOOR + 2.15) * PPM)
            window(d, fx * w, top, ww * PPM, 1.55 * PPM, R.choice(kinds), R)
            vx, vy = int(fx * w + (ww / 2 + .45) * PPM), top + int(1.75 * PPM)   # little cross vent
            d.rectangle([vx - 3, vy - 3, vx + 3, vy + 3], fill=(232, 232, 226, 255))
            d.line([(vx - 2, vy - 2), (vx + 2, vy + 2)], fill=(120, 116, 106, 255)); d.line([(vx - 2, vy + 2), (vx + 2, vy - 2)], fill=(120, 116, 106, 255))
    # stairwells: half-level small windows, drainpipe, door + canopy (front) or small window (back)
    for fx in B_STAIRS:
        cx = fx * w
        for lv in range(4):
            top = h - int((B_PLINTH + lv * B_FLOOR + B_FLOOR + 1.6) * PPM)
            window(d, cx, top, 1.05 * PPM, .85 * PPM, "plain", R)
        px_ = int(cx - 1.25 * PPM) if fx < .5 else int(cx + 1.25 * PPM)
        d.rectangle([px_ - 2, 0, px_ + 2, h - int(B_PLINTH * PPM)], fill=(150, 156, 158, 255))
        d.line([(px_ - 1, 0), (px_ - 1, h)], fill=(190, 196, 198, 255))
        if front:
            dx0, dx1 = int(cx - .65 * PPM), int(cx + .65 * PPM)
            dy0 = h - int(2.45 * PPM)
            d.rectangle([dx0 - 10, dy0 - 6, dx1 + 10, h], fill=(236, 236, 230, 255))   # white portal
            d.rectangle([dx0, dy0, dx1, h - 2], fill=(196, 40, 52, 255))               # red door
            d.rectangle([dx0 + 4, dy0 + 5, dx1 - 4, dy0 + int(1.2 * PPM)], fill=(70, 80, 88, 255))
            d.rectangle([dx0 + 2, dy0 + 2, dx1 - 2, h - 4], outline=(160, 28, 40, 255))
            d.rectangle([cx - 4, dy0 - 14, cx + 4, dy0 - 8], fill=(90, 90, 90, 255))   # number plate
            mx = int(cx + (2.0 if fx < .5 else -3.6) * PPM)                            # mailboxes
            d.rectangle([mx, h - int(1.55 * PPM), mx + int(1.6 * PPM), h - int(.95 * PPM)], fill=(108, 124, 130, 255))
            for i in range(4):
                for j in range(2):
                    bx = mx + 2 + i * int(.4 * PPM); by = h - int(1.5 * PPM) + j * int(.27 * PPM)
                    d.rectangle([bx, by, bx + int(.34 * PPM), by + int(.22 * PPM)], outline=(80, 92, 98, 255))
        else:
            window(d, cx, h - int((B_PLINTH + 1.6) * PPM), 1.05 * PPM, .85 * PPM, "plain", R)
    for vx in (int(.05 * w), int(.4 * w), int(.6 * w), int(.95 * w)):                  # plinth vent grilles
        for i in range(3):
            for j in range(3): d.rectangle([vx + i * 4, h - 11 + j * 3, vx + i * 4 + 1, h - 10 + j * 3], fill=(90, 90, 86, 255))
    if front:                                                                          # the satellite dish
        sx, sy = int(.205 * w), h - int(3.1 * PPM)
        d.ellipse([sx - 9, sy - 9, sx + 9, sy + 9], fill=(232, 232, 230, 255), outline=(190, 190, 188, 255))
    return im

def b_gable():
    w, h = int(B_D * PPM), int(B_H * PPM)
    im = speckle(w, h, (196, 184, 158), 10, .05); d = ImageDraw.Draw(im)
    for x in range(0, w, int(1.45 * PPM)): d.line([(x, 0), (x, h)], fill=(150, 160, 168, 255))
    for y in range(h, 0, -int(B_FLOOR * PPM / 2)): d.line([(0, y), (w, y)], fill=(150, 160, 168, 255))
    d.rectangle([0, h - int(B_PLINTH * PPM), w, h], fill=(232, 232, 226, 255))
    return im

def b_roof():
    w, h = int(B_W * PPM), int(B_D * PPM)
    im = speckle(w, h, (150, 152, 152), 8, .01); d = ImageDraw.Draw(im)
    for x in range(0, w, 16): d.line([(x, 0), (x, h)], fill=(138, 140, 140, 255))
    for fx in B_STAIRS: d.rectangle([fx * w - 6, h * .3, fx * w + 10, h * .3 + 16], fill=(170, 170, 168, 255))
    return im

# ======================================================================================== d
D_W, D_D = 21.5, 16.5
D_PIL, D_FLOORS, D_FL = 3.5, 12, 2.7
D_TOP = D_PIL + D_FLOORS * D_FL + .6           # 36.5 m
BRICK, BRICK_D = (222, 116, 74), (196, 98, 62)

def cladding(w, h):
    im = speckle(w, h, BRICK, 7, 0); d = ImageDraw.Draw(im)
    for y in range(0, h, 5):                                     # terracotta strips
        d.line([(0, y), (w, y)], fill=BRICK_D + (255,))
    for y in range(0, h, 5):
        off = (y // 5) % 2 * 9
        for x in range(off, w, 18): d.point((x, y + 2), fill=(178, 86, 56, 255))
    return im

def d_window(d, cx, top, w, h, shutter):
    x0, x1, y0, y1 = int(cx - w / 2), int(cx + w / 2), int(top), int(top + h)
    d.rectangle([x0 - 2, y0 - 5, x1 + 2, y0 - 1], fill=(150, 46, 30, 255))          # dark red lintel band
    d.rectangle([x0 - 2, y0, x1 + 2, y1 + 2], fill=(240, 240, 236, 255))
    d.rectangle([x0, y0 + 1, x1, y1], fill=(50, 58, 66, 255))
    for y in range(y0 + 1, y0 + 4): d.line([(x0, y), (x1, y)], fill=(110, 124, 136, 255))
    if shutter: d.rectangle([x0, y0 + 1, x1, int(y0 + (y1 - y0) * .6)], fill=(232, 232, 228, 255))
    d.line([(cx, y0), (cx, y1)], fill=(240, 240, 236, 255), width=2)
    d.line([(x0 - 2, y1 + 3), (x1 + 3, y1 + 3)], fill=(120, 60, 40, 255))

def d_bands(d, w, h):
    for z in (D_FL, 7 * D_FL, D_FLOORS * D_FL + .3):            # dark horizontal bands
        y = h - int(z * PPM)
        d.rectangle([0, y - 2, w, y + 1], fill=(48, 52, 64, 255))
        d.line([(0, y + 4), (w, y + 4)], fill=(48, 52, 64, 255))

def d_face(kind):
    """kind: 'north' (stair strip + entrance side), 'south', 'side' (central balcony stack)."""
    width = D_W if kind in ("north", "south") else D_D
    w, h = int(width * PPM), int((D_TOP - D_PIL) * PPM)
    im = cladding(w, h); d = ImageDraw.Draw(im)
    if kind == "side":
        bx0, bx1 = int(w * .31), int(w * .69)                     # recessed loggia stack
        d.rectangle([bx0, 0, bx1, h], fill=(176, 172, 164, 255))
        for f in range(D_FLOORS):
            y0 = h - int((f + 1) * D_FL * PPM)
            d.rectangle([bx0 + 6, y0 + 8, bx1 - 6, y0 + int(D_FL * PPM) - 4], fill=(96, 98, 104, 255))   # loggia back wall
            for k in range(3):
                gx = bx0 + 10 + k * (bx1 - bx0 - 20) // 3
                d.rectangle([gx, y0 + 12, gx + (bx1 - bx0 - 30) // 3, y0 + int(D_FL * PPM) - 6], fill=(150, 168, 180, 255))
            d.rectangle([bx0, y0 + int(D_FL * PPM) - 3, bx1, y0 + int(D_FL * PPM)], fill=(236, 236, 232, 255))
        cols = (.14, .86)
    elif kind == "north":
        sx0, sx1 = int(w * .43), int(w * .57)                     # dark stair strip with louvres
        d.rectangle([sx0, 0, sx1, h], fill=(42, 46, 54, 255))
        for y in range(0, h, 6): d.line([(sx0, y), (sx1, y)], fill=(70, 76, 86, 255))
        for f in range(D_FLOORS):
            y0 = h - int((f + .55) * D_FL * PPM)
            d.rectangle([sx0 + 6, y0 - 8, sx1 - 6, y0 + 8], fill=(88, 104, 118, 255))
        cols = (.10, .27, .73, .90)
    else:
        cols = (.10, .27, .5, .73, .90)
    for f in range(D_FLOORS):
        top = h - int((f * D_FL + 2.05) * PPM)
        for c in cols:
            big = c in (.27, .73, .5)
            d_window(d, c * w, top, (1.5 if big else .95) * PPM, 1.3 * PPM, R.random() < .22)
    d_bands(d, w, h)
    d.rectangle([0, 0, w, 7], fill=(46, 50, 60, 255))           # top cornice
    return im

def d_ground(front):
    w, h = int((D_W - 2.4 if front else D_D - 2.4) * PPM), int(D_PIL * PPM)
    im = Image.new("RGBA", (w, h), (64, 68, 74, 255)); d = ImageDraw.Draw(im)
    for x in range(0, w, 24): d.line([(x, 0), (x, h)], fill=(56, 60, 66, 255))
    if front:                                                    # glazed entrance hall with white lattice
        ex0, ex1 = int(w * .4), int(w * .6)
        d.rectangle([ex0, 6, ex1, h], fill=(140, 160, 172, 255))
        for x in range(ex0, ex1, 6): d.line([(x, 6), (x, h)], fill=(240, 240, 240, 255))
        for y in range(8, h, 9): d.line([(ex0, y), (ex1, y)], fill=(240, 240, 240, 255))
        d.rectangle([int(w * .66), 12, int(w * .76), h], fill=(232, 232, 228, 255))
        d.rectangle([int(w * .2), 12, int(w * .3), h - 4], fill=(110, 130, 140, 255))
    return im

def plain(rgb, size=16, spread=6):
    return speckle(size, size, rgb, spread, 0)

# ======================================================================================== models
def box(frm, to, faces):
    return {"from": [round(v, 3) for v in frm], "to": [round(v, 3) for v in to],
            "faces": {k: {"uv": [0, 0, 16, 16], "texture": t} for k, t in faces.items()}}

def b_model():
    k = 16 / 30.0                        # metres -> model units (cornice overhang included)
    ox, oz = (16 - B_W * k) / 2, (16 - B_D * k) / 2
    E = lambda x0, y0, z0, x1, y1, z1, f: box([ox + x0 * k, y0 * k, oz + z0 * k], [ox + x1 * k, y1 * k, oz + z1 * k], f)
    els = [E(0, 0, 0, B_W, B_H, B_D, {"north": "#front", "south": "#back", "east": "#gable", "west": "#gable", "up": "#roof", "down": "#white"})]
    els.append(E(-.3, B_H, -.3, B_W + .3, B_H + .35, B_D + .3, {f: "#white" for f in ("north", "south", "east", "west", "up", "down")}))
    for fx in B_STAIRS:                  # canopies on two round-ish columns, mailboxes (front = north face)
        cx = fx * B_W
        els.append(E(cx - 1.0, 2.55, -1.1, cx + 1.0, 2.75, 0, {f: "#white" for f in ("north", "south", "east", "west", "up", "down")}))
        for dx in (-.85, .55):
            els.append(E(cx + dx, 0, -1.0, cx + dx + .3, 2.55, -.7, {f: "#white" for f in ("north", "south", "east", "west")}))
        for fx2 in B_STAIRS:
            pass
        rx = cx - .6
        els.append(E(rx, B_H + .35, 2.5, rx + 1.2, B_H + 1.1, 3.7, {f: "#hatch" for f in ("north", "south", "east", "west", "up")}))
    return {"textures": {"front": "chroma:item/b_front", "back": "chroma:item/b_back", "gable": "chroma:item/b_gable",
                         "roof": "chroma:item/b_roof", "white": "chroma:item/b_white", "hatch": "chroma:item/b_hatch",
                         "particle": "chroma:item/b_front"}, "elements": els}

def d_model():
    k = 16 / 40.0
    ox, oz = (16 - D_W * k) / 2, (16 - D_D * k) / 2
    E = lambda x0, y0, z0, x1, y1, z1, f: box([ox + x0 * k, y0 * k, oz + z0 * k], [ox + x1 * k, y1 * k, oz + z1 * k], f)
    allf = lambda t: {f: t for f in ("north", "south", "east", "west", "up", "down")}
    els = [E(0, D_PIL, 0, D_W, D_TOP, D_D, {"north": "#north", "south": "#south", "east": "#side", "west": "#side", "up": "#roof", "down": "#soffit"})]
    els.append(E(1.2, 0, 1.2, D_W - 1.2, D_PIL, D_D - 1.2, {"north": "#gfront", "south": "#gside", "east": "#gside", "west": "#gside"}))
    for x in (.6, 5.6, 10.6, 15.6, 20.6):                       # pilotis (dark grey)
        for z in (.6, D_D - 1.0):
            els.append(E(x, 0, z, x + .4, D_PIL, z + .4, {f: "#pillar" for f in ("north", "south", "east", "west")}))
    for z in (5.5, 10.6):
        for x in (.6, D_W - 1.0):
            els.append(E(x, 0, z, x + .4, D_PIL, z + .4, {f: "#pillar" for f in ("north", "south", "east", "west")}))
    for f in range(D_FLOORS):                                   # balcony slabs + glass railings on both sides
        y = D_PIL + f * D_FL
        for x0, x1 in ((-1.2, 0), (D_W, D_W + 1.2)):
            els.append(E(x0, y, D_D * .31, x1, y + .18, D_D * .69, allf("#slab")))
            rx = x0 if x0 < 0 else x1 - .05
            els.append(E(rx, y + .18, D_D * .31, rx + .05, y + 1.05, D_D * .69, {f2: "#rail" for f2 in ("east", "west", "up")}))
    els.append(E(-.2, D_TOP, -.2, D_W + .2, D_TOP + .45, D_D + .2, allf("#cornice")))
    els.append(E(D_W / 2 - 2, D_TOP + .45, D_D / 2 - 1.5, D_W / 2 + 2, D_TOP + 3, D_D / 2 + 1.5, {f: "#machine" for f in ("north", "south", "east", "west", "up")}))
    return {"textures": {"north": "chroma:item/d_north", "south": "chroma:item/d_south", "side": "chroma:item/d_side",
                         "roof": "chroma:item/d_roof", "soffit": "chroma:item/d_soffit", "gfront": "chroma:item/d_ground_front",
                         "gside": "chroma:item/d_ground_side", "pillar": "chroma:item/d_pillar", "slab": "chroma:item/b_white",
                         "rail": "chroma:item/d_rail", "cornice": "chroma:item/d_cornice", "machine": "chroma:item/d_machine",
                         "particle": "chroma:item/d_north"}, "elements": els}

def build():
    t = "assets/chroma/textures/item/"
    ims = {
        "b_front": b_facade(True), "b_back": b_facade(False), "b_gable": b_gable(), "b_roof": b_roof(),
        "b_white": plain((234, 234, 228)), "b_hatch": plain((176, 176, 172)),
        "d_north": d_face("north"), "d_south": d_face("south"), "d_side": d_face("side"),
        "d_roof": plain((90, 92, 96), 32), "d_soffit": plain((200, 200, 196)), "d_ground_front": d_ground(True),
        "d_ground_side": d_ground(False), "d_pillar": plain((60, 64, 70)), "d_cornice": plain((46, 50, 60)),
        "d_machine": plain((214, 214, 210)),
    }
    rail = Image.new("RGBA", (16, 16), (150, 170, 180, 150))
    ImageDraw.Draw(rail).rectangle([0, 0, 15, 1], fill=(200, 200, 204, 255))
    ims["d_rail"] = rail
    f = {t + n + ".png": png(im) for n, im in ims.items()}
    f["assets/chroma/models/item/b_immeuble.json"] = json.dumps(b_model()).encode()
    f["assets/chroma/models/item/d_tour.json"] = json.dumps(d_model()).encode()
    for n in ("b_immeuble", "d_tour"):
        f["assets/chroma/items/%s.json" % n] = json.dumps({"model": {"type": "minecraft:model", "model": "chroma:item/" + n}}).encode()
    return f, ims

if __name__ == "__main__":
    import os, sys
    _, ims = build()
    out = sys.argv[1]
    for n in ("b_front", "d_north", "d_side"):
        im = ims[n]; s = 2 if im.width < 500 else 1
        im.resize((im.width * s, im.height * s), Image.NEAREST).save(os.path.join(out, "prev_" + n + ".png"))
    print("ok", {k: v.size for k, v in ims.items() if v.width > 16})
