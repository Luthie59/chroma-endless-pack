"""Generate the Chroma Endless spawn as a vanilla structure (.nbt) + a top-down preview PNG."""
import gzip, io, math, os, random, struct, sys, zlib

OUT = sys.argv[1]
R = 40                 # outer radius
W = 2 * R + 1          # 81
H = 40
C = R                  # centre index
FY = 8                 # floor level (index)
DATA_VERSION = 4189    # 1.21.4 - upgraded by DFU on newer servers

blocks = {}

def s(name, **props):
    if props:
        return "minecraft:%s[%s]" % (name, ",".join("%s=%s" % kv for kv in sorted(props.items())))
    return "minecraft:" + name

def setb(x, y, z, st):
    if 0 <= x < W and 0 <= y < H and 0 <= z < W:
        blocks[(x, y, z)] = st

def fill(x1, y1, z1, x2, y2, z2, st):
    for x in range(min(x1, x2), max(x1, x2) + 1):
        for y in range(min(y1, y2), max(y1, y2) + 1):
            for z in range(min(z1, z2), max(z1, z2) + 1):
                setb(x, y, z, st)

def dist(x, z, cx=C, cz=C):
    return math.hypot(x - cx, z - cz)

def rnd(*k):
    return random.Random(hash(k) & 0xffffffff).random()

def mix(x, y, z, choices):
    r = rnd(x, y, z); acc = 0
    for st, w in choices:
        acc += w
        if r < acc:
            return st
    return choices[-1][0]

BRICK = [(s("stone_bricks"), .72), (s("mossy_stone_bricks"), .14), (s("cracked_stone_bricks"), .14)]
PLAZA = [(s("polished_andesite"), .6), (s("andesite"), .2), (s("stone"), .2)]
DEEP = [(s("deepslate_bricks"), .7), (s("cracked_deepslate_bricks"), .15), (s("deepslate_tiles"), .15)]
FLOWERS = ["poppy", "dandelion", "cornflower", "allium", "oxeye_daisy", "azure_bluet",
           "red_tulip", "orange_tulip", "white_tulip", "lily_of_the_valley", "blue_orchid"]

def in_circle(x, z, r=R + .5):
    return dist(x, z) <= r

# ---------------------------------------------------------------- base volume
for x in range(W):
    for z in range(W):
        if not in_circle(x, z):
            continue
        for y in range(H):
            if y < FY - 2:
                st = s("stone")
            elif y < FY:
                st = s("dirt")
            elif y == FY:
                st = s("grass_block")
            else:
                st = s("air")
            blocks[(x, y, z)] = st

def on_spoke(x, z, half=3):
    return abs(x - C) <= half or abs(z - C) <= half

# ---------------------------------------------------------------- ground layout
for x in range(W):
    for z in range(W):
        d = dist(x, z)
        if d > 37.5:
            continue
        dx, dz = x - C, z - C
        if d <= 8.5:
            continue  # fountain handled later
        if d <= 13.5:      # fountain plaza
            st = s("polished_blackstone_bricks") if (int(d) % 3) else s("red_nether_bricks")
            if d > 12.5:
                st = s("chiseled_polished_blackstone") if (abs(dx) + abs(dz)) % 4 == 0 else s("polished_deepslate")
        elif on_spoke(x, z):
            half_axis = dx if abs(dz) > abs(dx) else dz
            if abs(half_axis) == 3:
                st = s("polished_deepslate")
            elif half_axis == 0 and (abs(dx) + abs(dz)) % 4 == 0:
                st = s("chiseled_stone_bricks")
            else:
                st = mix(x, FY, z, BRICK)
        elif 28.5 < d <= 31.5:   # ring road
            st = mix(x, FY, z, BRICK) if not (29.5 < d <= 30.5) else s("polished_andesite")
        elif d <= 14.8:
            st = s("polished_deepslate")
        else:
            st = s("grass_block")
        setb(x, FY, z, st)

# ---------------------------------------------------------------- fountain
for x in range(W):
    for z in range(W):
        d = dist(x, z)
        if d <= 8.5:
            if d > 7.5:
                setb(x, FY, z, s("polished_blackstone_bricks"))
                setb(x, FY + 1, z, s("polished_blackstone_brick_slab", type="bottom"))
                setb(x, FY - 1, z, s("polished_blackstone_bricks"))
            else:
                setb(x, FY - 2, z, s("sea_lantern") if (x + z) % 3 == 0 else s("prismarine_bricks"))
                setb(x, FY - 1, z, s("water"))
                setb(x, FY, z, s("water"))
        if d <= 4.5:  # tier 2
            for y in range(FY - 1, FY + 3):
                setb(x, y, z, s("polished_blackstone_bricks") if d > 3.5 or y < FY + 2 else s("polished_blackstone_bricks"))
            if d > 3.5:
                setb(x, FY + 3, z, s("polished_blackstone_brick_wall"))
            else:
                setb(x, FY + 3, z, s("water"))
                setb(x, FY + 2, z, s("sea_lantern") if (x + z) % 2 == 0 else s("prismarine_bricks"))
# obelisk
fill(C - 1, FY + 2, C - 1, C + 1, FY + 7, C + 1, s("quartz_bricks"))
for y in (FY + 4, FY + 6):
    for (ox, oz) in ((-1, -1), (1, -1), (-1, 1), (1, 1)):
        setb(C + ox, y, C + oz, s("red_nether_bricks"))
fill(C, FY + 8, C, C, FY + 16, C, s("quartz_pillar"))
setb(C, FY + 17, C, s("ochre_froglight"))
setb(C, FY + 18, C, s("end_rod", facing="up"))
for ox, oz, f in ((1, 0, "east"), (-1, 0, "west"), (0, 1, "south"), (0, -1, "north")):
    setb(C + ox, FY + 17, C + oz, s("end_rod", facing=f))
    setb(C + ox, FY + 8, C + oz, s("quartz_stairs", facing={"east": "west", "west": "east", "south": "north", "north": "south"}[f], half="bottom"))
# lanterns on tier-2 rim cardinal points
for ox, oz in ((4, 0), (-4, 0), (0, 4), (0, -4)):
    setb(C + ox, FY + 4, C + oz, s("lantern"))

# ---------------------------------------------------------------- benches around fountain (d ~ 11)
for k in range(8):
    a = math.pi / 8 + k * math.pi / 4
    bx, bz = C + round(11 * math.cos(a)), C + round(11 * math.sin(a))
    dx, dz = bx - C, bz - C
    face = ("east" if dx > 0 else "west") if abs(dx) > abs(dz) else ("south" if dz > 0 else "north")
    # bench of 3 stairs perpendicular to the radius
    tx, tz = (0, 1) if face in ("east", "west") else (1, 0)
    for i in (-1, 0, 1):
        setb(bx + tx * i, FY + 1, bz + tz * i, s("dark_oak_stairs", facing=face, half="bottom"))
    for sgn in (2, -2):
        setb(bx + tx * sgn, FY + 1, bz + tz * sgn, s("dark_oak_trapdoor", facing=face, half="bottom", open="true"))

# ---------------------------------------------------------------- lamp posts along spokes
def lamp(x, z):
    setb(x, FY + 1, z, s("polished_blackstone_wall"))
    setb(x, FY + 2, z, s("polished_blackstone_wall"))
    setb(x, FY + 3, z, s("dark_oak_fence"))
    setb(x, FY + 4, z, s("lantern"))

for t in range(16, 35, 6):
    for sx, sz in ((4, t), (-4, t), (4, -t), (-4, -t)):
        lamp(C + sx, C + sz)
        lamp(C + sz, C + sx)

# ---------------------------------------------------------------- walls, gates, towers
for x in range(W):
    for z in range(W):
        d = dist(x, z)
        if 35.5 < d <= 37.5:
            gate = on_spoke(x, z, 3)
            for y in range(FY, FY + 5):
                if gate and y < FY + 5:
                    if y == FY:
                        setb(x, y, z, mix(x, y, z, BRICK))
                    continue
                setb(x, y, z, mix(x, y, z, BRICK))
            if gate:
                fill(x, FY + 5, z, x, FY + 6, z, mix(x, FY + 5, z, BRICK))
                setb(x, FY + 7, z, s("stone_brick_wall") if (x + z) % 2 == 0 else s("air"))
            else:
                setb(x, FY + 5, z, s("stone_brick_wall") if (x + z) % 2 == 0 else s("air"))
            if 36.5 < d <= 37.5 and not gate:
                setb(x, FY + 3, z, s("red_nether_bricks") if (x * 7 + z * 3) % 11 == 0 else blocks[(x, FY + 3, z)])

def tower(cx, cz, r=3, h=11):
    for x in range(cx - r - 1, cx + r + 2):
        for z in range(cz - r - 1, cz + r + 2):
            d = dist(x, z, cx, cz)
            if d <= r + .5:
                for y in range(FY - 2, FY + h):
                    if d > r - .5:
                        st = mix(x, y, z, DEEP)
                        if y == FY + h - 3:
                            st = s("red_nether_bricks")
                        if y in (FY + 4, FY + 8) and (x == cx or z == cz) and d > r - .5:
                            st = s("air") if y < FY + h - 1 else st
                        setb(x, y, z, st)
                    else:
                        setb(x, y, z, s("dark_oak_planks") if y in (FY, FY + 6) else s("air"))
                # crenellation
                if d > r - .5:
                    setb(x, FY + h, z, mix(x, FY + h, z, DEEP) if (x + z) % 2 == 0 else s("air"))
    # inner light
    setb(cx, FY + 1, cz, s("lantern"))
    # pointed roof
    base = FY + h + 1
    for i, rr in enumerate((r + .5, r - .3, r - 1.1, r - 1.9, .6)):
        for x in range(cx - r - 1, cx + r + 2):
            for z in range(cz - r - 1, cz + r + 2):
                if dist(x, z, cx, cz) <= rr:
                    setb(x, base + i, z, s("deepslate_tiles") if i < 4 else s("deepslate_tile_wall"))
    setb(cx, base + 5, cz, s("lightning_rod"))

for ox, oz in ((6, 36), (-6, 36), (6, -36), (-6, -36)):
    tower(C + ox, C + oz)
    tower(C + oz, C + ox)
for sx in (1, -1):
    for sz in (1, -1):
        tower(C + round(sx * 26), C + round(sz * 26))

# gate arches: lanterns hanging under lintel
for ox, oz in ((0, 37), (0, -37), (37, 0), (-37, 0)):
    for k in (-2, 2):
        x = C + (k if ox == 0 else ox); z = C + (oz if ox == 0 else k)
        setb(x, FY + 4, z, s("lantern", hanging="true"))

# ---------------------------------------------------------------- quadrants
def flower_bed(x, z):
    if rnd(x, 1, z) < .45:
        setb(x, FY + 1, z, s(FLOWERS[int(rnd(x, 2, z) * len(FLOWERS))]))
    elif rnd(x, 3, z) < .3:
        setb(x, FY + 1, z, s("short_grass"))

def quad_points(qx, qz):
    for x in range(W):
        for z in range(W):
            dx, dz = x - C, z - C
            d = dist(x, z)
            if 15.5 < d < 28.5 and dx * qx > 4 and dz * qz > 4:
                yield x, z, dx, dz, d

# --- NE : market (qx=+1, qz=-1)
for x, z, dx, dz, d in quad_points(1, -1):
    setb(x, FY, z, mix(x, FY, z, [(s("spruce_planks"), .5), (s("stripped_spruce_wood", axis="y"), .2), (s("dirt_path"), .3)]))

def stall(cx, cz, wool):
    # 5 x 3 footprint, counter on front (towards plaza centre)
    for x in range(cx - 2, cx + 3):
        for z in range(cz - 1, cz + 2):
            setb(x, FY, z, s("spruce_planks"))
    for x in range(cx - 2, cx + 3):
        setb(x, FY + 1, cz + 1, s("barrel", facing="up") if x % 2 else s("spruce_slab", type="top"))
    for x, z in ((cx - 2, cz - 1), (cx + 2, cz - 1), (cx - 2, cz + 1), (cx + 2, cz + 1)):
        fill(x, FY + 1, z, x, FY + 3, z, s("spruce_fence"))
    for x in range(cx - 3, cx + 4):
        for z in range(cz - 2, cz + 3):
            setb(x, FY + 4, z, s(wool if (x + 99) % 2 else "white_wool"))
    setb(cx, FY + 3, cz, s("lantern", hanging="true"))
    setb(cx - 1, FY + 1, cz - 1, s("chest", facing="south"))
    setb(cx + 1, FY + 2, cz + 1, s("flower_pot"))

for (sx, sz, wool) in ((10, -20, "red_wool"), (19, -12, "orange_wool"), (17, -21, "yellow_wool"), (11, -11, "lime_wool")):
    stall(C + sx, C + sz, wool)

# --- NW : info gazebo (qx=-1, qz=-1)
gx, gz = C - 15, C - 15
for x, z, dx, dz, d in quad_points(-1, -1):
    setb(x, FY, z, s("grass_block")); flower_bed(x, z)
for x in range(gx - 6, gx + 7):
    for z in range(gz - 6, gz + 7):
        dd = dist(x, z, gx, gz)
        if dd <= 5.5:
            setb(x, FY, z, s("polished_andesite") if dd < 4.5 else s("dark_oak_planks"))
            setb(x, FY + 1, z, s("air"))
        if 4.5 < dd <= 5.5 and (abs(x - gx) == abs(z - gz) or x == gx or z == gz):
            fill(x, FY + 1, z, x, FY + 4, z, s("dark_oak_log", axis="y"))
for i, rr in enumerate((6.6, 5.4, 4.2, 3.0, 1.8, .7)):
    for x in range(gx - 7, gx + 8):
        for z in range(gz - 7, gz + 8):
            dd = dist(x, z, gx, gz)
            if dd <= rr and (i == 5 or dd > rr - 1.3):
                setb(x, FY + 5 + i, z, s("dark_oak_planks") if i < 5 else s("dark_oak_log", axis="y"))
setb(gx, FY + 11, gz, s("lantern"))
setb(gx, FY + 4, gz, s("lantern", hanging="true"))
setb(gx, FY + 1, gz, s("lectern", facing="south"))
for x, z in ((gx - 2, gz + 2), (gx + 2, gz + 2)):
    setb(x, FY + 1, z, s("dark_oak_stairs", facing="north", half="bottom"))

# --- SE : garden (qx=+1, qz=+1)
for x, z, dx, dz, d in quad_points(1, 1):
    setb(x, FY, z, s("grass_block")); flower_bed(x, z)
px, pz = C + 18, C + 18
for x in range(px - 5, px + 6):
    for z in range(pz - 5, pz + 6):
        dd = dist(x, z, px, pz)
        if dd <= 3.5:
            setb(x, FY, z, s("water")); setb(x, FY - 1, z, s("water")); setb(x, FY + 1, z, s("air"))
            if rnd(x, 9, z) < .25:
                setb(x, FY + 1, z, s("lily_pad"))
        elif dd <= 4.5:
            setb(x, FY, z, s("mossy_cobblestone")); setb(x, FY + 1, z, s("air"))

def cherry(tx, tz, h=5):
    fill(tx, FY + 1, tz, tx, FY + h, tz, s("cherry_log", axis="y"))
    for x in range(tx - 3, tx + 4):
        for y in range(FY + h - 1, FY + h + 3):
            for z in range(tz - 3, tz + 4):
                cur = blocks.get((x, y, z), s("air"))
                replaceable = cur == s("air") or cur == s("short_grass") or cur.split("[")[0].split(":")[1] in FLOWERS
                if math.hypot(x - tx, (y - (FY + h)) * 1.4, z - tz) <= 3.2 and replaceable:
                    setb(x, y, z, s("cherry_leaves", persistent="true"))
    setb(tx, FY, tz, s("dirt"))

for tx, tz in ((C + 10, C + 22), (C + 23, C + 10), (C + 24, C + 22), (C + 12, C + 13)):
    cherry(tx, tz)
for x, z, f in ((C + 14, C + 17, "west"), (C + 17, C + 14, "north")):
    for i in (-1, 0, 1):
        setb(x + (0 if f == "west" else i), FY + 1, z + (i if f == "west" else 0), s("spruce_stairs", facing=f, half="bottom"))

# --- SW : wild portal (qx=-1, qz=+1)
for x, z, dx, dz, d in quad_points(-1, 1):
    setb(x, FY, z, mix(x, FY, z, [(s("end_stone_bricks"), .5), (s("purpur_block"), .2), (s("grass_block"), .3)]))
ax, az = C - 17, C + 17   # arch centre, oriented along the diagonal -> use x-aligned arch
for x in range(ax - 4, ax + 5):
    for y in range(FY + 1, FY + 10):
        edge = abs(x - ax) >= 3 or y >= FY + 8
        inner = abs(x - ax) <= 2 and y < FY + 8
        if edge and not (abs(x - ax) == 4 and y >= FY + 8):
            setb(x, y, az, s("crying_obsidian") if (x + y) % 3 == 0 else s("obsidian"))
        elif inner:
            setb(x, y, az, s("purple_stained_glass_pane"))
for x in range(ax - 5, ax + 6):
    for z in range(az - 2, az + 3):
        setb(x, FY, z, s("purpur_block") if (x + z) % 2 else s("end_stone_bricks"))
for ox in (-5, 5):
    setb(ax + ox, FY + 1, az, s("amethyst_block"))
    setb(ax + ox, FY + 2, az, s("amethyst_cluster", facing="up"))
setb(ax, FY + 10, az, s("end_rod", facing="up"))

# ---------------------------------------------------------------- inner bailey (31.5 < d <= 35.5): grass, hedges, bushes
for x in range(W):
    for z in range(W):
        d = dist(x, z)
        if 31.5 < d <= 35.5 and not on_spoke(x, z):
            setb(x, FY, z, s("grass_block"))
            if 34.5 < d:
                setb(x, FY + 1, z, s("oak_leaves", persistent="true"))
            else:
                flower_bed(x, z)
        if 37.5 < d <= 40.5 and not on_spoke(x, z) and rnd(x, 7, z) < .18:
            setb(x, FY + 1, z, s("azalea_leaves", persistent="true") if rnd(x, 8, z) < .6 else s("flowering_azalea_leaves", persistent="true"))

# spokes must stay clear above floor
for x in range(W):
    for z in range(W):
        d = dist(x, z)
        if 8.5 < d <= 40.5 and on_spoke(x, z, 3) and not (35.5 < d <= 37.5):
            for y in range(FY + 1, FY + 4):
                if blocks.get((x, y, z), "").startswith(("minecraft:poppy", "minecraft:short_grass", "minecraft:oak_leaves", "minecraft:azalea", "minecraft:flowering")):
                    setb(x, y, z, s("air"))

# ---------------------------------------------------------------- NBT writer
def nbt_str(v):
    b = v.encode("utf-8"); return struct.pack(">H", len(b)) + b

def tag(t, name, payload):
    return bytes([t]) + nbt_str(name) + payload

def compound(items):  # items: list of encoded tags
    return b"".join(items) + b"\x00"

def int_list(vals):
    return bytes([3]) + struct.pack(">i", len(vals)) + b"".join(struct.pack(">i", v) for v in vals)

palette, pindex = [], {}
blist = []
for (x, y, z), st in sorted(blocks.items()):
    if st not in pindex:
        pindex[st] = len(palette); palette.append(st)
    blist.append(compound([tag(9, "pos", int_list([x, y, z])), tag(3, "state", struct.pack(">i", pindex[st]))]))

def pal_entry(st):
    name, _, rest = st.partition("[")
    items = [tag(8, "Name", nbt_str(name))]
    if rest:
        props = [tag(8, k, nbt_str(v)) for k, v in (p.split("=") for p in rest.rstrip("]").split(","))]
        items.append(tag(10, "Properties", compound(props)))
    return compound(items)

root = compound([
    tag(3, "DataVersion", struct.pack(">i", DATA_VERSION)),
    tag(9, "size", int_list([W, H, W])),
    tag(9, "palette", bytes([10]) + struct.pack(">i", len(palette)) + b"".join(pal_entry(p) for p in palette)),
    tag(9, "blocks", bytes([10]) + struct.pack(">i", len(blist)) + b"".join(blist)),
    tag(9, "entities", bytes([0]) + struct.pack(">i", 0)),
])
data = gzip.compress(tag(10, "", root), 9)
open(os.path.join(OUT, "spawn.nbt"), "wb").write(data)

# ---------------------------------------------------------------- preview (top-down, highest non-air block)
COL = {}
def col(st):
    n = st.split("[")[0].split(":")[1]
    table = {"grass_block": (95, 159, 53), "water": (52, 96, 219), "polished_blackstone_bricks": (48, 42, 50), "red_nether_bricks": (110, 18, 20),
             "polished_deepslate": (72, 72, 74), "chiseled_polished_blackstone": (60, 54, 62), "quartz_bricks": (235, 229, 222), "quartz_pillar": (235, 229, 222),
             "ochre_froglight": (250, 220, 140), "lantern": (255, 200, 90), "dark_oak_planks": (66, 43, 20), "dark_oak_log": (60, 46, 26), "spruce_planks": (114, 84, 48),
             "deepslate_tiles": (55, 55, 58), "deepslate_tile_wall": (55, 55, 58), "lightning_rod": (200, 120, 80), "oak_leaves": (60, 120, 40),
             "cherry_leaves": (240, 170, 205), "purpur_block": (170, 125, 170), "end_stone_bricks": (220, 222, 160), "obsidian": (20, 18, 30), "crying_obsidian": (60, 20, 100),
             "white_wool": (235, 235, 235), "red_wool": (160, 40, 35), "orange_wool": (240, 118, 20), "yellow_wool": (248, 197, 40), "lime_wool": (112, 185, 25),
             "end_rod": (250, 250, 240), "polished_andesite": (132, 135, 134), "dirt_path": (148, 122, 65), "mossy_cobblestone": (100, 120, 90)}
    if n in table: return table[n]
    if "stone_brick" in n or n in ("stone", "andesite", "stone_bricks"): return (122, 122, 122)
    if "deepslate" in n: return (70, 70, 72)
    if "azalea" in n: return (90, 140, 50)
    if "wall" in n or "slab" in n: return (90, 90, 95)
    if n in FLOWERS or n == "short_grass": return (200, 80, 80) if n != "short_grass" else (95, 159, 53)
    return (160, 160, 160)
S = 6
img = [[(30, 30, 30, 255)] * (W * S) for _ in range(W * S)]
for x in range(W):
    for z in range(W):
        for y in range(H - 1, -1, -1):
            st = blocks.get((x, y, z))
            if st and st != s("air"):
                c = col(st); shade = 0.75 + 0.25 * (y - FY) / 12 if y >= FY else 0.7
                c = tuple(max(0, min(255, int(v * shade))) for v in c)
                for a in range(S):
                    for b in range(S):
                        img[z * S + a][x * S + b] = c + (255,)
                break
def png(pixels):
    h = len(pixels); w = len(pixels[0])
    raw = b"".join(b"\x00" + b"".join(struct.pack("BBBB", *p) for p in row) for row in pixels)
    def chunk(t, d):
        cc = struct.pack(">I", len(d)) + t + d
        return cc + struct.pack(">I", zlib.crc32(t + d) & 0xFFFFFFFF)
    return b"\x89PNG\r\n\x1a\n" + chunk(b"IHDR", struct.pack(">IIBBBBB", w, h, 8, 6, 0, 0, 0)) + chunk(b"IDAT", zlib.compress(raw, 9)) + chunk(b"IEND", b"")
open(os.path.join(OUT, "spawn_preview.png"), "wb").write(png(img))
print("blocks", len(blocks), "palette", len(palette), "nbt bytes", len(data))
