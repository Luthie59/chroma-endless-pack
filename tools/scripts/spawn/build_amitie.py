"""L'Instant Éternel — floating island at sunset, a tribute to the friendship of Luthie59 & Margot59.
Two cherry trees grow toward each other and meet in an arch over a bench facing the sunset (west),
a frozen golden clock on a pedestal, an engraved plaque, a pond with glowing pickles, fireflies,
glow-berry vines under the island, two 'stars' (one per friend) above the trees and small floating islets.
Writes amitie_vN.nbt (non-air blocks + display entities) and preview PNGs."""
import gzip, json, math, os, random, struct, sys

OUT = sys.argv[1]
VERSION = sys.argv[2] if len(sys.argv) > 2 else "1"
W, H = 81, 72
C = 40                 # island centre (x, z)
Y0 = 44                # grass surface (local y)
DATA_VERSION = 4189    # older data version: the server's data fixer upgrades JSON texts & states
ORIGIN = (-C, 120 - Y0, -C)   # world surface at y = 120

blocks, entities = {}, []
def s(name, **p):
    return "minecraft:%s[%s]" % (name, ",".join("%s=%s" % kv for kv in sorted(p.items()))) if p else "minecraft:" + name
def setb(x, y, z, st, force=True):
    if not (0 <= x < W and 0 <= y < H and 0 <= z < W): return
    if not force and (x, y, z) in blocks: return
    blocks[(x, y, z)] = st
def get(x, y, z): return blocks.get((x, y, z))
def clear(x, y, z): blocks.pop((x, y, z), None)
R = random.Random(5959)
def rnd(*k): return random.Random(hash(k) & 0xffffffff).random()

# ----------------------------------------------------------------- terrain
def island(cx, cz, base_r, top, depth_k, seed, wobble=(3.0, 2.0)):
    """organic floating island: returns the set of top cells."""
    tops = {}
    ph1, ph2 = seed * 1.7, seed * 2.9
    for x in range(int(cx - base_r - 6), int(cx + base_r + 7)):
        for z in range(int(cz - base_r - 6), int(cz + base_r + 7)):
            dx, dz = x - cx, z - cz
            th = math.atan2(dz, dx)
            r = base_r + wobble[0] * math.sin(3 * th + ph1) + wobble[1] * math.sin(5 * th + ph2) + (rnd(seed, x, z) - .5) * .8
            d = math.hypot(dx, dz)
            if d > r: continue
            f = d / r
            ytop = top - (1 if f > .9 else 0)
            depth = int((1 - f ** 1.6) * depth_k * (.85 + .3 * rnd(seed, x, 7, z))) + 1
            for y in range(ytop - depth, ytop + 1):
                k = ytop - y
                if k == 0: st = s("grass_block")
                elif k <= 2: st = s("rooted_dirt") if rnd(x, y, z, 1) < .15 else s("dirt")
                elif k <= 7: st = [s("stone"), s("andesite"), s("tuff"), s("stone")][int(rnd(x, y, z, 2) * 4)]
                else: st = [s("deepslate"), s("tuff"), s("calcite"), s("deepslate"), s("stone")][int(rnd(x, y, z, 3) * 5)]
                if k > 0 and y == ytop - depth and rnd(x, y, z, 4) < .3: st = s("mossy_cobblestone")
                setb(x, y, z, st)
            tops[(x, z)] = (ytop, ytop - depth, f)
    return tops

TOP = island(C, C, 22.0, Y0, 30, 1)
# underside life: glow berries, hanging roots, pale moss
for (x, z), (yt, yb, f) in TOP.items():
    if f < .45: continue
    r = rnd(x, z, 11)
    if r < .10:
        n = 2 + int(rnd(x, z, 12) * 6)
        for i in range(1, n):
            setb(x, yb - i, z, s("cave_vines_plant", berries="true" if rnd(x, i, z) < .5 else "false"))
        setb(x, yb - n, z, s("cave_vines", age="25", berries="true"))
    elif r < .16:
        setb(x, yb - 1, z, s("hanging_roots"))
    elif r < .21:
        n = 1 + int(rnd(x, z, 13) * 3)
        for i in range(1, n): setb(x, yb - i, z, s("pale_hanging_moss", tip="false"))
        setb(x, yb - n, z, s("pale_hanging_moss", tip="true"))

# small floating islets around
ISLETS = [(C - 31, C - 17, 3.5, Y0 - 6), (C + 27, C - 27, 3.0, Y0 + 5), (C + 30, C + 22, 4.0, Y0 - 9), (C - 24, C + 30, 2.5, Y0 + 2)]
islet_tops = []
for i, (ix, iz, ir, it) in enumerate(ISLETS):
    t = island(ix, iz, ir, it, 7, 20 + i, wobble=(.6, .4))
    islet_tops.append(t)
    deco = [s("firefly_bush"), s("flowering_azalea"), s("pink_tulip"), s("lily_of_the_valley")][i]
    setb(ix, it + 1, iz, deco)
    for (x, z), (yt, yb, f) in t.items():
        if (x, z) != (ix, iz) and rnd(x, z, 40) < .35:
            setb(x, yt + 1, z, s("pink_petals", flower_amount=str(1 + int(rnd(x, z, 41) * 4)), facing="north"))
        if f > .5 and rnd(x, z, 42) < .3:
            setb(x, yb - 1, z, s("cave_vines", age="25", berries="true"))

# ----------------------------------------------------------------- the two cherry trees and their arch
NT, ST = (C, C - 8), (C, C + 8)          # north / south trunks; arch runs along z, bench faces west
ARCH_TOP = Y0 + 9
def log(x, y, z, axis="y"): setb(x, y, z, s("cherry_log", axis=axis))
arch = []
for trunk, sign in ((NT, 1), (ST, -1)):
    tx, tz = trunk
    for y in range(Y0 + 1, Y0 + 5): log(tx, y, tz)
    log(tx + 1, Y0 + 1, tz, "x"); log(tx - 1, Y0 + 1, tz, "x"); log(tx, Y0 + 1, tz - sign, "z")   # root flare
    prev = (tx, Y0 + 4, tz)
    for i in range(1, 9):
        t = i / 8
        z = tz + sign * i
        y = Y0 + 4 + round(math.sin(t * math.pi / 2) * (ARCH_TOP - Y0 - 4))
        for yy in range(prev[1], y + 1): log(tx, yy, z if yy == y else prev[2], "y" if yy < y else "z")
        log(tx, y, z, "z")
        arch.append((tx, y, z))
        prev = (tx, y, z)
    # outer side branch
    for k in range(1, 4): log(tx, Y0 + 4 + k // 2, tz - sign * k, "z")
    arch.append((tx, Y0 + 6, tz - sign * 3))
def leaf_blob(cx, cy, cz, r):
    for x in range(int(cx - r - 1), int(cx + r + 2)):
        for y in range(int(cy - r), int(cy + r + 1)):
            for z in range(int(cz - r - 1), int(cz + r + 2)):
                d = math.sqrt((x - cx) ** 2 + ((y - cy) * 1.35) ** 2 + (z - cz) ** 2)
                if d <= r and rnd(x, y, z, 50) < (1 - (d / r) ** 3) + .15:
                    setb(x, y, z, s("cherry_leaves", persistent="true"), force=False)
for (x, y, z) in arch[::2]:
    leaf_blob(x, y + 1, z, 3.3)
for (x, y, z) in arch:
    for dx in (-2, 2):
        if rnd(x, z, dx) < .6: leaf_blob(x + dx, y, z, 2.0)
# keep a clear passage under the arch (people sit below it)
for x in range(C - 3, C + 4):
    for z in range(C - 6, C + 7):
        for y in range(Y0 + 1, Y0 + 6):
            if get(x, y, z) == s("cherry_leaves", persistent="true"): clear(x, y, z)
# petals hanging from the canopy
for (x, y, z), st in list(blocks.items()):
    if st.startswith("minecraft:cherry_leaves") and get(x, y - 1, z) is None and y > Y0 + 5 and rnd(x, y, z, 60) < .12:
        setb(x, y - 1, z, s("cherry_leaves", persistent="true"))

# ----------------------------------------------------------------- bench under the arch, facing the sunset (west)
for z in (C - 1, C, C + 1): setb(C + 1, Y0 + 1, z, s("cherry_stairs", facing="east", half="bottom", shape="straight"))
for z in (C - 2, C + 2):
    setb(C + 1, Y0 + 1, z, s("cherry_fence")); setb(C + 1, Y0 + 2, z, s("lantern", hanging="false"))
for z in range(C - 2, C + 3): setb(C + 2, Y0 + 1, z, s("flowering_azalea_leaves", persistent="true"))

# ----------------------------------------------------------------- path to the west overlook + pedestal with the frozen clock
PED = (C - 6, C)
for x in range(C - 20, C):
    z = C + round(math.sin(x * .45) * .6)
    if (x, z) in TOP and rnd(x, 70) < .85:
        setb(x, TOP[(x, z)][0], z, s("mud_bricks") if x % 2 else s("packed_mud"))
setb(PED[0], Y0 + 1, PED[1], s("chiseled_quartz_block"))
setb(PED[0], Y0 + 2, PED[1], s("quartz_slab", type="bottom"))
for dx, dz in ((1, 0), (-1, 0), (0, 1), (0, -1)):
    setb(PED[0] + dx, Y0 + 1, PED[1] + dz, s("quartz_stairs", facing={(1, 0): "west", (-1, 0): "east", (0, 1): "north", (0, -1): "south"}[(dx, dz)], half="bottom", shape="straight"))
# overlook balcony on the west rim
west = min(x for (x, z) in TOP if z == C)
for a in range(-60, 61, 12):
    rad = math.radians(a)
    x = int(round(west + 2 - math.cos(rad) * 3)); z = int(round(C + math.sin(rad) * 4))
    if (x, z) in TOP:
        setb(x, TOP[(x, z)][0] + 1, z, s("cherry_fence"))
        if abs(a) in (60, 0): setb(x, TOP[(x, z)][0] + 2, z, s("lantern", hanging="false"))

# ----------------------------------------------------------------- pond with lily pads and glowing sea pickles (east of the bench)
PX, PZ, PR = C + 9, C, 3.4
for x in range(int(PX - 5), int(PX + 6)):
    for z in range(int(PZ - 5), int(PZ + 6)):
        d = math.hypot(x - PX, z - PZ)
        if d <= PR:
            setb(x, Y0, z, s("water")); setb(x, Y0 - 1, z, s("water")); setb(x, Y0 - 2, z, s("clay"))
            if rnd(x, z, 80) < .18: setb(x, Y0 - 1, z, s("sea_pickle", pickles="3", waterlogged="true"))
            elif rnd(x, z, 81) < .25: setb(x, Y0 + 1, z, s("lily_pad"))
        elif d <= PR + 1.2:
            setb(x, Y0, z, s("moss_block") if rnd(x, z, 82) < .6 else s("mossy_cobblestone"))
            if rnd(x, z, 83) < .35: setb(x, Y0 + 1, z, s("firefly_bush"))

# ----------------------------------------------------------------- arrival gate on the east rim + stepping stones to the bench
east = max(x for (x, z) in TOP if z == C)
GATE = (east - 2, C)
for dz in (-2, 2):
    setb(GATE[0], Y0 + 1, C + dz, s("cherry_fence")); setb(GATE[0], Y0 + 2, C + dz, s("cherry_fence"))
    setb(GATE[0], Y0 + 3, C + dz, s("cherry_fence"))
for dz in range(-2, 3): setb(GATE[0], Y0 + 4, C + dz, s("cherry_slab", type="bottom"))
setb(GATE[0], Y0 + 3, C, s("lantern", hanging="true"))
for x in range(C + 3, GATE[0] + 1):
    for z in (C - 4, C + 4) if x < PX + 6 else (C,):
        pass
path = [(x, C + (4 if PX - 5 <= x <= PX + 5 else 0)) for x in range(C + 3, GATE[0] + 1)]
for (x, z) in path:
    if (x, z) in TOP and get(x, Y0, z) == s("grass_block") and rnd(x, z, 90) < .8:
        setb(x, Y0, z, s("mud_bricks") if (x + z) % 2 else s("packed_mud"))

# ----------------------------------------------------------------- ground cover: petals, wildflowers, leaf litter, flowers, fireflies
FLOWERS = ["allium", "pink_tulip", "lily_of_the_valley", "azure_bluet", "cornflower", "oxeye_daisy", "white_tulip"]
for (x, z), (yt, yb, f) in TOP.items():
    if get(x, yt, z) != s("grass_block") or get(x, yt + 1, z) is not None: continue
    dn = min(math.hypot(x - NT[0], z - NT[1]), math.hypot(x - ST[0], z - ST[1]))
    r = rnd(x, z, 100)
    face = ["north", "south", "east", "west"][int(rnd(x, z, 101) * 4)]
    amt = str(1 + int(rnd(x, z, 102) * 4))
    if dn < 6 and r < .55: setb(x, yt + 1, z, s("pink_petals", flower_amount=amt, facing=face))
    elif dn < 8 and r < .25: setb(x, yt + 1, z, s("leaf_litter", segment_amount=amt, facing=face))
    elif r < .10: setb(x, yt + 1, z, s("wildflowers", flower_amount=amt, facing=face))
    elif r < .16: setb(x, yt + 1, z, s(FLOWERS[int(rnd(x, z, 103) * len(FLOWERS))]))
    elif r < .19 and f > .5: setb(x, yt + 1, z, s("firefly_bush"))
    elif r < .32: setb(x, yt + 1, z, s("short_grass"))
# lanterns along the paths
for x in range(C - 18, C - 1, 5):
    z = C + 2
    if (x, z) in TOP: setb(x, Y0 + 1, z, s("cherry_fence")); setb(x, Y0 + 2, z, s("lantern", hanging="false"))

# ----------------------------------------------------------------- display entities
def text(pos, json_text, scale=1.0, billboard="center", width=220, bg=0x00000000):
    entities.append({"kind": "text", "pos": pos, "text": json_text, "billboard": billboard, "width": width, "bg": bg,
                     "q": (0, 0, 0, 1), "t": (0, 0, 0), "scale": (scale, scale, scale), "tags": ["amitie"], "view": 2.5, "tp": 0, "glow": True})
def item(pos, item_id, scale, tags):
    entities.append({"kind": "item", "pos": pos, "item": item_id, "q": (0, 0, 0, 1), "t": (0, 0, 0), "scale": (scale, scale, scale),
                     "tags": ["amitie"] + tags, "view": 3.0, "tp": 2, "glow": True})
def W_(x, y, z): return (x + ORIGIN[0], y + ORIGIN[1], z + ORIGIN[2])
plaque = json.dumps([
    {"text": "✿ L'Instant Éternel ✿\n", "color": "gold", "bold": True},
    {"text": "Luthie59 ", "color": "#FFB7D5", "bold": True}, {"text": "& ", "color": "gray"},
    {"text": "Margot59\n\n", "color": "#FFB7D5", "bold": True},
    {"text": "Ici, le temps s'est arrêté\npour garder un instant précieux :\n", "color": "#E8E0F0", "italic": True},
    {"text": "une amitié qui traverse les époques.", "color": "#E8E0F0", "italic": True}], ensure_ascii=False)
text(W_(PED[0] + .5, Y0 + 4.6, PED[1] + .5), plaque, scale=.9, width=260, bg=0x9A140A28)
item(W_(PED[0] + .5, Y0 + 3.0, PED[1] + .5), "minecraft:clock", 1.3, ["amitie_horloge"])
for (tx, tz) in (NT, ST):
    item(W_(tx + .5, ARCH_TOP + 5.5, tz + .5), "minecraft:nether_star", 1.1, ["amitie_etoile"])

# ----------------------------------------------------------------- NBT writer (same format as the citadel structures)
def nstr(v): b = v.encode(); return struct.pack(">H", len(b)) + b
def tag(t, n, p): return bytes([t]) + nstr(n) + p
def comp(items): return b"".join(items) + b"\x00"
def ilist(v): return bytes([3]) + struct.pack(">i", len(v)) + b"".join(struct.pack(">i", i) for i in v)
def dlist(v): return bytes([6]) + struct.pack(">i", len(v)) + b"".join(struct.pack(">d", i) for i in v)
def flist(v): return bytes([5]) + struct.pack(">i", len(v)) + b"".join(struct.pack(">f", i) for i in v)
def slist(v): return bytes([8]) + struct.pack(">i", len(v)) + b"".join(nstr(i) for i in v)
def pe(st):
    name, _, rest = st.partition("[")
    it = [tag(8, "Name", nstr(name))]
    if rest: it.append(tag(10, "Properties", comp([tag(8, k, nstr(v)) for k, v in (p.split("=") for p in rest.rstrip("]").split(","))])))
    return comp(it)
pal, pidx, bl = [], {}, []
for (x, y, z), st in sorted(blocks.items()):
    if st not in pidx: pidx[st] = len(pal); pal.append(st)
    bl.append(comp([tag(9, "pos", ilist([x, y, z])), tag(3, "state", struct.pack(">i", pidx[st]))]))
ents = []
for e in entities:
    wx, wy, wz = e["pos"]; lx, ly, lz = wx - ORIGIN[0], wy - ORIGIN[1], wz - ORIGIN[2]
    if e["kind"] == "item":
        head = [tag(8, "id", nstr("minecraft:item_display")), tag(10, "item", comp([tag(8, "id", nstr(e["item"])), tag(3, "count", struct.pack(">i", 1))])),
                tag(8, "item_display", nstr("fixed"))]
    else:
        bg = e["bg"] - (1 << 32) if e["bg"] >= (1 << 31) else e["bg"]
        head = [tag(8, "id", nstr("minecraft:text_display")), tag(8, "text", nstr(e["text"])), tag(8, "billboard", nstr(e["billboard"])),
                tag(3, "line_width", struct.pack(">i", e["width"])), tag(3, "background", struct.pack(">i", bg)), tag(1, "shadow", b"\x01")]
    nbt = head + [tag(10, "transformation", comp([tag(9, "left_rotation", flist(list(e["q"]))), tag(9, "right_rotation", flist([0, 0, 0, 1])),
                                                  tag(9, "translation", flist(list(e["t"]))), tag(9, "scale", flist(list(e["scale"])))])),
                  tag(9, "Tags", slist(e["tags"])), tag(5, "view_range", struct.pack(">f", e["view"])),
                  tag(9, "Rotation", flist([0.0, 0.0])), tag(9, "Pos", dlist([lx, ly, lz]))]
    if e["tp"]: nbt.append(tag(3, "teleport_duration", struct.pack(">i", e["tp"])))
    if e["glow"]: nbt.append(tag(10, "brightness", comp([tag(3, "sky", struct.pack(">i", 15)), tag(3, "block", struct.pack(">i", 15))])))
    ents.append(comp([tag(9, "pos", dlist([lx, ly, lz])), tag(9, "blockPos", ilist([int(math.floor(lx)), int(math.floor(ly)), int(math.floor(lz))])),
                      tag(10, "nbt", comp(nbt))]))
root = comp([tag(3, "DataVersion", struct.pack(">i", DATA_VERSION)), tag(9, "size", ilist([W, H, W])),
             tag(9, "palette", bytes([10]) + struct.pack(">i", len(pal)) + b"".join(pe(p) for p in pal)),
             tag(9, "blocks", bytes([10]) + struct.pack(">i", len(bl)) + b"".join(bl)),
             tag(9, "entities", bytes([10]) + struct.pack(">i", len(ents)) + b"".join(ents))])
name = "amitie_v%s.nbt" % VERSION
open(os.path.join(OUT, name), "wb").write(gzip.compress(tag(10, "", root), 6))

# ----------------------------------------------------------------- previews (top view + side view from the east)
from PIL import Image
COL = {"grass_block": (110, 170, 70), "cherry_leaves": (240, 170, 205), "cherry_log": (90, 50, 50), "water": (60, 110, 220),
       "mud_bricks": (150, 115, 85), "packed_mud": (140, 105, 75), "pink_petals": (245, 160, 200), "firefly_bush": (90, 120, 50),
       "cherry_stairs": (225, 175, 170), "cherry_fence": (225, 175, 170), "lantern": (255, 210, 110), "chiseled_quartz_block": (235, 230, 220),
       "quartz_slab": (235, 230, 220), "quartz_stairs": (235, 230, 220), "flowering_azalea_leaves": (120, 150, 60), "lily_pad": (40, 130, 40),
       "moss_block": (90, 115, 45), "mossy_cobblestone": (110, 120, 100), "cave_vines": (255, 190, 80), "cave_vines_plant": (100, 120, 50),
       "stone": (125, 125, 125), "andesite": (135, 135, 135), "tuff": (105, 105, 95), "deepslate": (70, 70, 75), "calcite": (220, 220, 215),
       "dirt": (130, 90, 60), "rooted_dirt": (140, 100, 70), "cherry_slab": (225, 175, 170), "leaf_litter": (170, 120, 60),
       "wildflowers": (240, 220, 90), "pale_hanging_moss": (190, 195, 185), "hanging_roots": (150, 110, 80)}
def colour(st):
    n = st.split("[")[0].split(":")[1]
    return COL.get(n, (200, 120, 200) if n in FLOWERS else (160, 160, 160))
S = 6
top = Image.new("RGB", (W * S, W * S), (255, 170, 110)); px = top.load()
best = {}
for (x, y, z), st in blocks.items():
    if (x, z) not in best or y > best[(x, z)][0]: best[(x, z)] = (y, st)
for (x, z), (y, st) in best.items():
    c = colour(st); f = .65 + .35 * min(1, max(0, (y - Y0 + 10) / 22))
    for a in range(S):
        for b in range(S): px[x * S + a, z * S + b] = tuple(int(v * f) for v in c)
top.save(os.path.join(OUT, "amitie_top.png"))
side = Image.new("RGB", (W * S, H * S), (255, 160, 100)); ps = side.load()
front = {}
for (x, y, z), st in blocks.items():         # look from the east (+x) toward the west: horizontal axis = z
    if (z, y) not in front or x > front[(z, y)][0]: front[(z, y)] = (x, st)
for (z, y), (x, st) in front.items():
    c = colour(st); f = .55 + .45 * (x / W)
    for a in range(S):
        for b in range(S): ps[z * S + a, (H - 1 - y) * S + b] = tuple(int(v * f) for v in c)
side.save(os.path.join(OUT, "amitie_side.png"))
print(json.dumps({"nbt": name, "blocks": len(blocks), "palette": len(pal), "entities": len(entities),
                  "origin": ORIGIN, "arrival": W_(GATE[0] - 1 + .5, Y0 + 1, C + .5), "centre": W_(C + .5, Y0 + 1, C + .5),
                  "stars": [W_(t[0] + .5, ARCH_TOP + 5.5, t[1] + .5) for t in (NT, ST)], "clock": W_(PED[0] + .5, Y0 + 3.0, PED[1] + .5)}))
