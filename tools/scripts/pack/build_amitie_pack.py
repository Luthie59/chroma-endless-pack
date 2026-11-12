"""Amitie overlay pack: only sent to players inside the private 'amitie' world (stacked on top of the server pack).
Golden-hour art direction: big radiant sun, peach-pink clouds, 32px blossoming cherry leaves, caustic water,
fine grass, warm path stones, glowing hearts and petals. Everything is original / procedurally drawn or
colour-graded from the vanilla textures of the local client jar."""
import colorsys, io, json, math, os, random, sys, zipfile
from PIL import Image, ImageDraw, ImageFilter

OUT = sys.argv[1]
JAR = os.path.expandvars(r"%APPDATA%\.minecraft\versions\1.21.11\1.21.11.jar")
jar = zipfile.ZipFile(JAR)
def van(path): return Image.open(io.BytesIO(jar.read("assets/minecraft/textures/" + path))).convert("RGBA")
files = {}
def put(path, im):
    b = io.BytesIO(); im.save(b, "PNG", optimize=True); files["assets/minecraft/textures/" + path] = b.getvalue()
def meta(path, obj): files["assets/minecraft/textures/" + path + ".mcmeta"] = json.dumps(obj).encode()
R = random.Random(5959)

def grade(im, sat=1.18, warm=0.04, bright=1.04):
    """golden-hour colour grade: more saturation, a touch warmer and brighter, alpha untouched."""
    px = im.load()
    for y in range(im.height):
        for x in range(im.width):
            r, g, b, a = px[x, y]
            if a == 0: continue
            h, l, s = colorsys.rgb_to_hls(r / 255, g / 255, b / 255)
            s = min(1, s * sat); l = min(1, l * bright)
            r2, g2, b2 = colorsys.hls_to_rgb(h, l, s)
            r2 = min(1, r2 + warm); b2 = max(0, b2 - warm * .6)
            px[x, y] = (int(r2 * 255), int(g2 * 255), int(b2 * 255), a)
    return im

# ----------------------------------------------------------------- sun: radiant disc with halo and soft rays
N = 64
sun = Image.new("RGBA", (N, N), (0, 0, 0, 0)); sp = sun.load()
for y in range(N):
    for x in range(N):
        dx, dy = x - N / 2 + .5, y - N / 2 + .5; d = math.hypot(dx, dy)
        ang = math.atan2(dy, dx)
        core = 1.0 if d < 10 else 0
        glow = max(0.0, 1 - d / 31) ** 1.8
        rays = max(0.0, math.cos(ang * 6)) ** 8 * max(0.0, 1 - d / 30) * .5
        v = max(core, glow * .9 + rays)
        if v <= 0.02: continue
        if core: col = (255, 250, 228)
        else:
            t = min(1, (d - 10) / 20)
            col = (255, int(236 - 70 * t), int(170 - 120 * t))
        sp[x, y] = col + (int(min(1, v) * 255),)
put("environment/celestial/sun.png", sun)

# ----------------------------------------------------------------- clouds: peach-pink, same shapes
clouds = van("environment/clouds.png"); cp = clouds.load()
for y in range(clouds.height):
    for x in range(clouds.width):
        r, g, b, a = cp[x, y]
        if a: cp[x, y] = (255, 220, 232, a)
put("environment/clouds.png", clouds)

# ----------------------------------------------------------------- cherry leaves: 32px blossoms
S = 32
PINKS = [(247, 193, 217), (244, 154, 193), (255, 221, 235), (232, 128, 172), (250, 176, 206)]
leaves = Image.new("RGBA", (S, S), (206, 118, 158, 255)); d = ImageDraw.Draw(leaves)
for _ in range(70):                                  # soft background mass of petals
    x, y = R.randrange(S), R.randrange(S); c = R.choice(PINKS[:2] + [PINKS[3]])
    d.ellipse([x - 2, y - 2, x + 2, y + 2], fill=tuple(int(v * R.uniform(.82, .95)) for v in c) + (255,))
for _ in range(14):                                  # five-petal flowers on top
    x, y = R.randrange(2, S - 2), R.randrange(2, S - 2)
    c = R.choice(PINKS)
    for k in range(5):
        a = k * 2 * math.pi / 5 + R.random()
        px_, py_ = x + math.cos(a) * 1.6, y + math.sin(a) * 1.6
        d.ellipse([px_ - 1.3, py_ - 1.3, px_ + 1.3, py_ + 1.3], fill=c + (255,))
    d.point((x, y), fill=(255, 236, 140, 255))
    d.point((x + 1, y), fill=(214, 90, 140, 255))
for _ in range(6):                                   # a few fresh green leaves
    x, y = R.randrange(S), R.randrange(S)
    d.polygon([(x, y), (x + 2, y - 1), (x + 3, y + 1), (x + 1, y + 2)], fill=(132, 178, 86, 255))
lp = leaves.load()
for _ in range(5):                                   # a few grouped gaps so light passes through the canopy
    x, y = R.randrange(S - 2), R.randrange(S - 2)
    for dx, dy in ((0, 0), (1, 0), (0, 1), (1, 1)):
        if R.random() < .85: lp[x + dx, y + dy] = (0, 0, 0, 0)
put("block/cherry_leaves.png", leaves)
meta("block/cherry_leaves.png", {"texture": {"mipmap_strategy": "dark_cutout"}})

# ----------------------------------------------------------------- water: animated caustics (greyscale, biome-tinted)
FR, WS = 32, 32
water = Image.new("RGBA", (WS, WS * FR))
for f in range(FR):
    t = f / FR * 2 * math.pi
    for y in range(WS):
        for x in range(WS):
            u, v = x / WS * 2 * math.pi, y / WS * 2 * math.pi
            c = (math.sin(u * 2 + t) + math.sin(v * 2 - t) + math.sin((u + v) * 1 + t) + math.sin((u - v) * 2 + 2 * t)) / 4
            caust = max(0.0, 1 - abs(c) * 3.2) ** 2
            l = int(150 + 70 * caust + 15 * math.sin(u + v + t))
            water.putpixel((x, f * WS + y), (l, l, l, int(150 + 40 * caust)))
put("block/water_still.png", water)
meta("block/water_still.png", {"animation": {"frametime": 2}})

# ----------------------------------------------------------------- grass top: fine blades (greyscale, biome-tinted)
grass = Image.new("RGBA", (S, S))
gp = grass.load()
for y in range(S):
    for x in range(S):
        n = .62 + .12 * math.sin(x * .9 + y * .4) * math.sin(y * .7 - x * .3) + R.uniform(-.08, .08)
        l = int(max(0, min(1, n)) * 255); gp[x, y] = (l, l, l, 255)
gd = ImageDraw.Draw(grass)
for _ in range(90):
    x, y = R.randrange(S), R.randrange(S); l = R.randrange(200, 250)
    gd.line([(x, y), (x + R.choice((-1, 0, 1)), y - R.randrange(1, 3))], fill=(l, l, l, 255))
for _ in range(40):
    x, y = R.randrange(S), R.randrange(S); l = R.randrange(95, 130)
    gp[x, y] = (l, l, l, 255)
put("block/grass_block_top.png", grass)

# ----------------------------------------------------------------- colour-graded vanilla textures used on the island
for path, kw in [("block/pink_petals.png", dict(sat=1.3, bright=1.08)), ("block/cherry_log.png", {}), ("block/cherry_log_top.png", {}),
                 ("block/cherry_planks.png", dict(sat=1.1, bright=1.06)), ("block/moss_block.png", dict(sat=1.25)),
                 ("block/mossy_cobblestone.png", {}), ("block/allium.png", dict(sat=1.3)), ("block/pink_tulip.png", dict(sat=1.3)),
                 ("block/cornflower.png", dict(sat=1.3)), ("block/azure_bluet.png", {}), ("block/lily_of_the_valley.png", {}),
                 ("block/oxeye_daisy.png", {}), ("block/white_tulip.png", {}), ("block/wildflowers.png", dict(sat=1.3)),
                 ("block/flowering_azalea_leaves.png", dict(sat=1.25)), ("block/lantern.png", dict(sat=1.2, warm=.06, bright=1.1)),
                 ("block/cave_vines_lit.png", dict(sat=1.3, bright=1.1)), ("block/cave_vines_plant_lit.png", dict(sat=1.3, bright=1.1)),
                 ("block/sea_pickle.png", dict(sat=1.3, bright=1.1)), ("block/leaf_litter.png", dict(sat=1.2))]:
    try:
        put(path, grade(van(path), **kw))
        mpath = "assets/minecraft/textures/" + path + ".mcmeta"
        if mpath in jar.namelist(): files[mpath] = jar.read(mpath)
    except KeyError:
        print("absent:", path)

# warm rose path stones
for path in ("block/mud_bricks.png", "block/packed_mud.png"):
    im = van(path); p = im.load()
    for y in range(im.height):
        for x in range(im.width):
            r, g, b, a = p[x, y]
            l = (r + g + b) / 3 / 255
            p[x, y] = (int(150 + 95 * l), int(112 + 80 * l), int(98 + 66 * l), a)
    put(path, im)

# ----------------------------------------------------------------- particles: glowing heart and brighter petals
heart = van("particle/heart.png"); hp = heart.load()
for y in range(heart.height):
    for x in range(heart.width):
        r, g, b, a = hp[x, y]
        if a: hp[x, y] = (255, 120 + (y * 60) // heart.height, 170, a)
put("particle/heart.png", heart)
for i in range(12):
    p = "particle/cherry_%d.png" % i
    try: put(p, grade(van(p), sat=1.3, bright=1.1))
    except KeyError: pass

files["pack.mcmeta"] = json.dumps({"pack": {"description": "§dL'Instant Éternel", "min_format": 75, "max_format": 75}},
                                  ensure_ascii=False).encode("utf-8")
leaves.resize((S * 8, S * 8), Image.NEAREST).save(os.path.join(OUT, "leaves_preview.png"))
sun.resize((N * 4, N * 4), Image.NEAREST).save(os.path.join(OUT, "sun_preview.png"))
out = os.path.join(OUT, "Amitie-Overlay.zip")
with zipfile.ZipFile(out, "w", zipfile.ZIP_DEFLATED) as z:
    for n in sorted(files): z.writestr(n, files[n])
print("ok", out, len(files), "files")
