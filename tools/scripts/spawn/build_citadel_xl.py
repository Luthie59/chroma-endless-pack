"""Chroma Endless - XL citadel under a glass dome -> vanilla structure + previews + warp list."""
import gzip, json, math, os, random, struct, sys, zlib

OUT = sys.argv[1]
R = 64; W = 2 * R + 1; C = R
FY = 8
DOME = 60.0
H = FY + int(DOME) + 3
DATA_VERSION = 4189
ORIGIN = (-R, 56, -R)          # world position of index (0,0,0); floor at world y = 64

blocks = {}
def s(name, **p):
    return "minecraft:%s[%s]" % (name, ",".join("%s=%s" % kv for kv in sorted(p.items()))) if p else "minecraft:" + name
AIR = s("air")
def setb(x, y, z, st):
    if 0 <= x < W and 0 <= y < H and 0 <= z < W:
        blocks[(x, y, z)] = st
def get(x, y, z): return blocks.get((x, y, z), AIR)
def fill(x1, y1, z1, x2, y2, z2, st):
    for x in range(min(x1, x2), max(x1, x2) + 1):
        for y in range(min(y1, y2), max(y1, y2) + 1):
            for z in range(min(z1, z2), max(z1, z2) + 1):
                setb(x, y, z, st)
def dist(x, z, cx=C, cz=C): return math.hypot(x - cx, z - cz)
def rnd(*k): return random.Random(hash(k) & 0xffffffff).random()
def mix(x, y, z, ch):
    r = rnd(x, y, z); a = 0
    for st, w in ch:
        a += w
        if r < a: return st
    return ch[-1][0]
AV = 4                                   # avenue half width
def on_spoke(x, z, half=AV): return abs(x - C) <= half or abs(z - C) <= half
def air_box(x1, z1, x2, z2, y1, y2):
    return all(get(x, y, z) == AIR for x in range(x1, x2 + 1) for z in range(z1, z2 + 1) for y in range(y1, y2 + 1))
def dome_h(d):                            # free height above floor at horizontal distance d
    return math.sqrt(max(0.0, DOME ** 2 - d ** 2))
OUTF = {(1, 0): "east", (-1, 0): "west", (0, 1): "south", (0, -1): "north"}
INF = {"east": "west", "west": "east", "south": "north", "north": "south"}
def facing_out(dx, dz):
    return OUTF[(1 if dx > 0 else -1, 0)] if abs(dx) >= abs(dz) else OUTF[(0, 1 if dz > 0 else -1)]
def ring_cells(px, pz, a, b):
    for x in range(px - int(b) - 1, px + int(b) + 2):
        for z in range(pz - int(b) - 1, pz + int(b) + 2):
            if a < dist(x, z, px, pz) <= b: yield x, z

WHITE = [(s("smooth_quartz"), .45), (s("white_concrete"), .3), (s("calcite"), .25)]
FLOOR = [(s("smooth_quartz"), .55), (s("polished_diorite"), .3), (s("calcite"), .15)]
RED = [(s("crimson_nylium"), .45), (s("red_terracotta"), .25), (s("orange_terracotta"), .15), (s("terracotta"), .15)]
GOLD = s("gold_block"); WIN = s("yellow_stained_glass"); LIGHT = s("ochre_froglight")
ROADS = (20.0, 45.0)

# =============================================================== base volume
for x in range(W):
    for z in range(W):
        if dist(x, z) > R + .5: continue
        for y in range(H):
            st = s("stone") if y < FY - 2 else s("dirt") if y < FY else mix(x, y, z, RED) if y == FY else AIR
            blocks[(x, y, z)] = st

# =============================================================== floor
def is_road(x, z):
    d = dist(x, z)
    return any(abs(d - r) <= 1.6 for r in ROADS)
for x in range(W):
    for z in range(W):
        d = dist(x, z); dx, dz = x - C, z - C
        if d > DOME - .5: continue
        st = mix(x, FY, z, FLOOR)
        ang = math.degrees(math.atan2(dz, dx)) % 360
        for rr in (15.5, 26.0, 41.0, 55.0):
            if abs(d - rr) < .55: st = s("light_gray_concrete")
        if 15.5 < d < 26 and (ang % 30 < 1.2 or ang % 30 > 28.8): st = s("light_gray_concrete")
        if abs(d - 26) < .55 and ang % 15 < 1.5: st = LIGHT
        for k in range(12):
            a = k * math.pi / 6 + math.pi / 12
            cx, cz = C + 41 * math.cos(a), C + 41 * math.sin(a)
            if abs(dist(x, z, cx, cz) - 3) < .5: st = s("light_gray_concrete")
            if dist(x, z, cx, cz) < .8: st = GOLD
        if is_road(x, z):
            st = s("white_concrete") if abs(d - min(ROADS, key=lambda r: abs(d - r))) < .9 else s("light_gray_concrete")
        if on_spoke(x, z) and d > 13.5:
            half = dx if abs(dz) > abs(dx) else dz
            if abs(half) == AV: st = s("light_gray_concrete")
            elif half == 0: st = GOLD if (abs(dx) + abs(dz)) % 6 == 0 else s("yellow_terracotta")
            elif abs(half) == 2 and (abs(dx) + abs(dz)) % 8 == 0: st = LIGHT
            else: st = s("white_concrete")
        setb(x, FY, z, st)

# =============================================================== dome
for x in range(W):
    for z in range(W):
        hd = dist(x, z)
        if hd > DOME + 1: continue
        for y in range(FY, H):
            r3 = math.sqrt(hd * hd + (y - FY) ** 2)
            if not (DOME - .5 <= r3 < DOME + .6): continue
            a30 = math.degrees(math.atan2(z - C, x - C)) % 30; a10 = a30 % 10
            lat = math.degrees(math.asin(min(1, (y - FY) / DOME)))
            major = a30 < 1.0 or a30 > 29.0
            minor = (a10 < .6 or a10 > 9.4) and lat < 72
            band = next((st_ for L, st_ in ((12, s("smooth_quartz")), (25, s("smooth_quartz")), (38, GOLD), (50, s("smooth_quartz")),
                                            (62, GOLD), (74, s("smooth_quartz"))) if abs(lat - L) < .9), None)
            if y <= FY + 2: st = s("smooth_quartz") if y < FY + 2 else GOLD
            elif band: st = band
            elif major: st = s("smooth_quartz")
            elif minor: st = s("calcite")
            else: st = s("white_stained_glass") if (x * 3 + y + z * 5) % 11 == 0 and lat > 30 else s("glass")
            if lat > 86: st = GOLD
            if on_spoke(x, z, AV) and y <= FY + 8:
                st = AIR
                if y == FY + 8 or (not on_spoke(x, z, AV - 1) and y >= FY + 1):
                    st = s("quartz_pillar", axis="y") if y < FY + 8 else GOLD
            setb(x, y, z, st)
for (ox, oz) in ((0, 1), (0, -1), (1, 0), (-1, 0)):
    for t in range(int(DOME) - 1, R + 1):
        for w in range(-AV, AV + 1):
            x = C + ox * t + (w if ox == 0 else 0); z = C + oz * t + (w if oz == 0 else 0)
            setb(x, FY, z, s("white_concrete") if abs(w) < AV else s("light_gray_concrete"))
    setb(C + ox * int(DOME), FY + 7, C + oz * int(DOME), s("lantern", hanging="true"))

# =============================================================== central tower, pool, colonnade
for x, z in ring_cells(C, C, 9.5, 13.5):
    d = dist(x, z)
    if d > 12.5:
        setb(x, FY, z, s("smooth_quartz")); setb(x, FY + 1, z, s("smooth_quartz_slab", type="bottom"))
    else:
        setb(x, FY, z, s("water")); setb(x, FY - 1, z, s("water")); setb(x, FY - 2, z, s("sea_lantern") if (x + z) % 2 else s("prismarine_bricks"))
tiers = [(9.5, 0, 9), (8.5, 9, 18), (7.5, 18, 26), (6.5, 26, 33), (5.5, 33, 39), (4.5, 39, 44), (3.5, 44, 48), (2.5, 48, 51)]
for (rr, y0, y1) in tiers:
    for x, z in ring_cells(C, C, -1, rr):
        d = dist(x, z)
        for y in range(FY + y0, FY + y1):
            if d > rr - 1:
                st = s("smooth_quartz")
                if (y - FY) % 6 in (2, 3, 4) and ((x - C) % 3 == 0 or (z - C) % 3 == 0): st = WIN
                if y == FY + y1 - 1: st = GOLD
            else:
                st = LIGHT if y == FY + y0 else AIR
            setb(x, y, z, st)
    for x, z in ring_cells(C, C, rr, rr + 1.2):
        if get(x, FY + y1, z) == AIR and y1 < 48:
            setb(x, FY + y1, z, s("smooth_quartz_slab", type="bottom"))
fill(C, FY + 51, C, C, FY + 55, C, s("quartz_pillar", axis="y"))
setb(C, FY + 56, C, s("end_rod", facing="up"))
for (ox, oz), f in OUTF.items():
    setb(C + ox, FY + 54, C + oz, s("end_rod", facing=f))
# tower doors on 4 sides
for (ox, oz) in OUTF:
    for k in range(7, 11):
        for w in (-1, 0, 1):
            x = C + ox * k + (w if ox == 0 else 0); z = C + oz * k + (w if oz == 0 else 0)
            for y in range(FY + 1, FY + 4):
                if dist(x, z) > 8.4: setb(x, y, z, AIR)
# vertical fins
for k in range(8):
    a = math.pi / 8 + k * math.pi / 4
    for (rr, y0, y1) in tiers[:6]:
        x, z = C + round((rr + .8) * math.cos(a)), C + round((rr + .8) * math.sin(a))
        for y in range(FY + y0 + 1, FY + y1 - 1):
            if get(x, y, z) == AIR: setb(x, y, z, s("quartz_pillar", axis="y"))
        if get(x, FY + y1 - 1, z) == AIR: setb(x, FY + y1 - 1, z, s("end_rod", facing="up"))
# colonnade r=15.5
cols = []
for k in range(32):
    a = k * math.pi / 16
    x, z = C + round(15.5 * math.cos(a)), C + round(15.5 * math.sin(a))
    if on_spoke(x, z, AV) or (x, z) in cols: continue
    cols.append((x, z))
    setb(x, FY + 1, z, s("chiseled_quartz_block")); fill(x, FY + 2, z, x, FY + 5, z, s("quartz_pillar", axis="y")); setb(x, FY + 6, z, s("chiseled_quartz_block"))
for x, z in ring_cells(C, C, 14.9, 16.1):
    if get(x, FY + 7, z) == AIR: setb(x, FY + 7, z, s("smooth_quartz"))
    if get(x, FY + 8, z) == AIR: setb(x, FY + 8, z, GOLD if (x + z) % 2 == 0 else s("smooth_quartz_slab", type="bottom"))
    if get(x, FY + 6, z) == AIR and any(dist(x, z, cx, cz) < 1.6 for cx, cz in cols):
        setb(x, FY + 6, z, s("smooth_quartz_slab", type="top"))

# =============================================================== districts
def feat_pos(qx, qz, d=30):
    return C + round(qx * d / math.sqrt(2)), C + round(qz * d / math.sqrt(2))
MARKET, INFO, GARDEN, PORTAL = feat_pos(1, -1), feat_pos(-1, -1), feat_pos(1, 1), feat_pos(-1, 1)
FEATURES = [(MARKET, 12.0), (INFO, 9.0), (GARDEN, 12.5), (PORTAL, 8.0)]

def stall(cx, cz, wool, face="south"):
    for x in range(cx - 2, cx + 3):
        for z in range(cz - 1, cz + 2): setb(x, FY, z, s("birch_planks"))
    for x in range(cx - 2, cx + 3):
        setb(x, FY + 1, cz + 1, s("barrel", facing="up") if x % 2 else s("smooth_quartz_slab", type="top"))
    for x, z in ((cx - 2, cz - 1), (cx + 2, cz - 1), (cx - 2, cz + 1), (cx + 2, cz + 1)):
        fill(x, FY + 1, z, x, FY + 3, z, s("birch_fence"))
    for x in range(cx - 3, cx + 4):
        for z in range(cz - 2, cz + 3): setb(x, FY + 4, z, s(wool if (x + 99) % 2 else "white_wool"))
    setb(cx, FY + 3, cz, s("lantern", hanging="true"))
    setb(cx - 1, FY + 1, cz - 1, s("chest", facing=face))
mx, mz = MARKET
for x, z in ring_cells(mx, mz, -1, 11.5):
    if not is_road(x, z): setb(x, FY, z, s("birch_planks") if (x + z) % 5 else s("smooth_quartz"))
for i, (ox, oz) in enumerate(((-6, -6), (0, -7), (6, -6), (-7, 0), (7, 0), (-6, 6), (0, 7), (6, 6))):
    stall(mx + ox, mz + oz, ["orange_wool", "yellow_wool", "red_wool", "light_blue_wool", "lime_wool", "magenta_wool", "orange_wool", "cyan_wool"][i])
# market centre: small gilded fountain
for x, z in ring_cells(mx, mz, -1, 2.5):
    setb(x, FY, z, s("water") if dist(x, z, mx, mz) < 1.6 else s("smooth_quartz")); setb(x, FY + 1, z, AIR if dist(x, z, mx, mz) < 1.6 else s("smooth_quartz_slab", type="bottom"))
setb(mx, FY, mz, s("smooth_quartz")); fill(mx, FY + 1, mz, mx, FY + 2, mz, s("quartz_pillar", axis="y")); setb(mx, FY + 3, mz, GOLD); setb(mx, FY + 4, mz, s("lantern"))

ix, iz = INFO
for x, z in ring_cells(ix, iz, -1, 8.5):
    d = dist(x, z, ix, iz)
    setb(x, FY, z, s("smooth_quartz") if d < 7.5 else GOLD if (x + z) % 3 == 0 else s("light_gray_concrete"))
    if 6.5 < d <= 7.5 and (abs(x - ix) == abs(z - iz) or x == ix or z == iz) and not ((z - iz) * (x - ix) == 0 and (z > iz or x > ix)):
        fill(x, FY + 1, z, x, FY + 6, z, s("quartz_pillar", axis="y"))
for x in range(ix - 9, ix + 10):
    for z in range(iz - 9, iz + 10):
        for y in range(FY + 7, FY + 16):
            r3 = math.sqrt((x - ix) ** 2 + (z - iz) ** 2 + (y - FY - 7) ** 2)
            if 7.0 <= r3 < 8.0: setb(x, y, z, GOLD if y == FY + 7 else s("glass") if (y - FY) % 2 else s("smooth_quartz"))
setb(ix, FY + 15, iz, GOLD); setb(ix, FY + 16, iz, s("end_rod", facing="up"))
setb(ix, FY + 1, iz, s("lectern", facing="south")); fill(ix, FY + 10, iz, ix, FY + 12, iz, s("chain", axis="y")); setb(ix, FY + 9, iz, s("lantern", hanging="true"))
for ox, oz in ((-3, 3), (3, 3), (-3, -3), (3, -3)):
    setb(ix + ox, FY + 1, iz + oz, s("birch_stairs", facing=facing_out(ox, oz), half="bottom"))

gx, gz = GARDEN
for x, z in ring_cells(gx, gz, -1, 12):
    if is_road(x, z) or on_spoke(x, z, AV + 3): continue
    d = dist(x, z, gx, gz)
    setb(x, FY, z, s("moss_block") if rnd(x, 4, z) < .25 else s("grass_block"))
    if d <= 4.5: setb(x, FY, z, s("water")); setb(x, FY - 1, z, s("water"))
    elif d <= 5.4: setb(x, FY, z, s("smooth_quartz"))
    elif rnd(x, 1, z) < .35:
        setb(x, FY + 1, z, s(["white_tulip", "lily_of_the_valley", "azure_bluet", "oxeye_daisy", "short_grass", "pink_tulip"][int(rnd(x, 2, z) * 6)]))
    if d <= 4.5 and rnd(x, 9, z) < .2: setb(x, FY + 1, z, s("lily_pad"))
def silver_tree(tx, tz, h=7):
    fill(tx, FY + 1, tz, tx, FY + h, tz, s("pale_oak_log", axis="y")); setb(tx, FY, tz, s("dirt"))
    for x in range(tx - 4, tx + 5):
        for y in range(FY + h - 3, FY + h + 3):
            for z in range(tz - 4, tz + 5):
                if math.hypot(x - tx, (y - FY - h) * 1.3, z - tz) <= 3.6 and get(x, y, z) in (AIR, s("short_grass")) or (
                        math.hypot(x - tx, (y - FY - h) * 1.3, z - tz) <= 3.6 and get(x, y, z).split("[")[0].endswith(("tulip", "valley", "bluet", "daisy"))):
                    setb(x, y, z, s("pale_oak_leaves", persistent="true"))
    for k in range(3):
        hx, hz = tx + [-3, 2, 0][k], tz + [0, 2, -3][k]
        if get(hx, FY + h - 3, hz) == AIR and get(hx, FY + h - 2, hz).startswith("minecraft:pale_oak_leaves"):
            setb(hx, FY + h - 3, hz, s("pale_hanging_moss", tip="true"))
for a in range(6):
    t = a * math.pi / 3 + .4
    silver_tree(gx + round(8.5 * math.cos(t)), gz + round(8.5 * math.sin(t)), 6 + a % 3)
# garden pavilion bridge over the pond
for x in range(gx - 5, gx + 6):
    setb(x, FY + 1, gz, s("birch_slab", type="bottom"))
for x in (gx - 5, gx + 5):
    setb(x, FY + 1, gz + 1, s("birch_fence")); setb(x, FY + 2, gz + 1, s("lantern"))

px, pz = PORTAL
for x, z in ring_cells(px, pz, -1, 7.5):
    setb(x, FY, z, s("light_gray_concrete") if abs(dist(x, z, px, pz) - 6) < .6 else mix(x, FY, z, FLOOR))
fill(px - 1, FY + 1, pz - 1, px + 1, FY + 6, pz + 1, s("blue_concrete"))
for (x, z) in ((px - 1, pz - 1), (px + 1, pz - 1), (px - 1, pz + 1), (px + 1, pz + 1)):
    fill(x, FY + 1, z, x, FY + 6, z, s("blue_terracotta"))
for (x, z) in ((px, pz - 1), (px, pz + 1), (px - 1, pz), (px + 1, pz)):
    setb(x, FY + 5, z, s("white_stained_glass"))
fill(px - 1, FY + 7, pz - 1, px + 1, FY + 7, pz + 1, s("blue_concrete"))
setb(px, FY + 8, pz, s("sea_lantern")); setb(px, FY + 9, pz, s("light_blue_stained_glass"))
for ox, oz in ((-4, -4), (4, -4), (-4, 4), (4, 4)):
    fill(px + ox, FY + 1, pz + oz, px + ox, FY + 2, pz + oz, s("quartz_pillar", axis="y")); setb(px + ox, FY + 3, pz + oz, s("end_rod", facing="up"))

# =============================================================== spires (fewer, taller)
PLACED = []
def free(x0, z0, r):
    if on_spoke(x0, z0, AV + 4 + r) or is_road(x0, z0): return False
    if any(dist(x0, z0, qx, qz) < r + qr + 6 for qx, qz, qr in PLACED): return False
    return all(dist(x0, z0, fx, fz) > fr + r + 1 for (fx, fz), fr in FEATURES)

def spire(px_, pz_, r, h):
    for x, z in ring_cells(px_, pz_, r + .5, r + 1.5):
        setb(x, FY + 1, z, s("smooth_quartz_stairs", facing=INF[facing_out(x - px_, z - pz_)], half="bottom"))
    nsec = 4 if h >= 30 else 3 if h >= 15 else 2
    bounds = [FY + 1 + round(h * k / nsec) for k in range(nsec + 1)]
    cur = r
    for si in range(nsec):
        y0, y1 = bounds[si], bounds[si + 1]
        for x, z in ring_cells(px_, pz_, -1, cur + .5):
            d = dist(x, z, px_, pz_)
            for y in range(y0, y1):
                if d > cur - .5:
                    st = mix(x, y, z, WHITE)
                    if ((x - px_) == 0 or (z - pz_) == 0 or (abs(x - px_) == abs(z - pz_) and cur >= 2)) and (y - y0) % 4 in (1, 2) and y1 - y > 1: st = WIN
                    if y == y1 - 1: st = GOLD
                else:
                    st = LIGHT if (y - FY) % 8 == 1 else AIR
                setb(x, y, z, st)
        if si < nsec - 1:
            for x, z in ring_cells(px_, pz_, cur + .5, cur + 1.4):
                if get(x, y1 - 1, z) == AIR: setb(x, y1 - 1, z, s("smooth_quartz_slab", type="top"))
            for (ox, oz) in OUTF: setb(px_ + ox * (cur + 1), y1, pz_ + oz * (cur + 1), s("end_rod", facing="up"))
        if si == 0 and h >= 10:
            fh = max(3, (y1 - y0) * 3 // 4)
            for (ox, oz) in OUTF:
                for k in (1, 2):
                    top_f = y0 + fh - (k - 1) * 2
                    fx, fz = px_ + ox * (cur + k), pz_ + oz * (cur + k)
                    fill(fx, FY + 1, fz, fx, top_f - 1, fz, s("quartz_pillar", axis="y"))
                    setb(fx, top_f, fz, s("smooth_quartz_stairs", facing=INF[OUTF[(ox, oz)]], half="bottom"))
        if cur > 1 and si < nsec - 1: cur -= 1
    top = bounds[-1]; rr = cur + .5; i = 0
    while rr > .4:
        for x, z in ring_cells(px_, pz_, -1, rr): setb(x, top + i, z, GOLD if i % 3 == 2 else s("smooth_quartz"))
        rr -= .55 if cur >= 2 else .9; i += 1
    for (ox, oz), f in OUTF.items(): setb(px_ + ox, top + i - 1, pz_ + oz, s("end_rod", facing=f))
    fill(px_, top + i, pz_, px_, top + i + 1, pz_, s("lightning_rod")); setb(px_, top + i + 2, pz_, s("end_rod", facing="up"))

spires = []
for ring_r, count, base_r, maxh in ((24, 8, 2, 40), (38, 12, 2, 36), (52, 16, 1, 22)):
    for k in range(count):
        a = (k + .5) * 2 * math.pi / count
        sx, sz = C + round(ring_r * math.cos(a)), C + round(ring_r * math.sin(a))
        r = base_r
        if not free(sx, sz, r): continue
        h = int(min(maxh, dome_h(dist(sx, sz) + r + 1) - 8) * (0.7 + 0.3 * rnd(sx, 6, sz)))
        if h < 8: continue
        PLACED.append((sx, sz, r)); spire(sx, sz, r, h); spires.append((sx, sz, r, h))

# =============================================================== houses (residential rings)
houses = []
def house(hx, hz, kind):
    dx, dz = C - hx, C - hz
    door = (1 if dx > 0 else -1, 0) if abs(dx) >= abs(dz) else (0, 1 if dz > 0 else -1)
    hr = 3                                            # 7x7
    wall_h = 5 if kind == 0 else 10
    for x in range(hx - hr, hx + hr + 1):
        for z in range(hz - hr, hz + hr + 1):
            ex, ez = abs(x - hx) == hr, abs(z - hz) == hr
            setb(x, FY, z, s("polished_diorite") if not (ex or ez) else s("smooth_quartz"))
            for y in range(FY + 1, FY + wall_h + 1):
                if ex and ez: st = s("quartz_pillar", axis="y")
                elif ex or ez:
                    st = s("white_concrete")
                    if (y - FY) % 5 in (2, 3) and (abs(x - hx) == 1 or abs(z - hz) == 1) and y < FY + wall_h: st = WIN
                    if y == FY + wall_h: st = GOLD if (x + z) % 2 else s("smooth_quartz")
                    if kind == 1 and y == FY + 5: st = s("smooth_quartz")
                else:
                    st = s("smooth_quartz") if (y == FY + wall_h or (kind == 1 and y == FY + 5)) else AIR
                setb(x, y, z, st)
    # interior
    setb(hx, FY + 1, hz, s("crafting_table") if kind == 0 else s("bookshelf"))
    setb(hx + 1, FY + 1, hz + 1, s("barrel", facing="up")); setb(hx - 1, FY + wall_h - 1, hz - 1, s("lantern", hanging="true"))
    setb(hx - 2, FY + 1, hz + 2, s("red_bed", facing="north", part="foot")) if False else setb(hx - 2, FY + 1, hz + 2, s("potted_white_tulip"))
    # door + porch light + planters
    ddx, ddz = hx + door[0] * hr, hz + door[1] * hr
    setb(ddx, FY + 1, ddz, AIR); setb(ddx, FY + 2, ddz, AIR)
    setb(ddx + door[0], FY + 3, ddz + door[1], s("end_rod", facing=OUTF[door]))
    side = (door[1], door[0])
    for sg in (2, -2):
        pxp, pzp = ddx + door[0] + side[0] * sg, ddz + door[1] + side[1] * sg
        if get(pxp, FY + 1, pzp) == AIR:
            setb(pxp, FY + 1, pzp, s("smooth_quartz")); setb(pxp, FY + 2, pzp, s("potted_azure_bluet"))
    # roof dome (gold) / spire roof for tower houses
    base = FY + wall_h
    if kind == 0:
        for x in range(hx - 4, hx + 5):
            for z in range(hz - 4, hz + 5):
                for y in range(base, base + 5):
                    r3 = math.sqrt((x - hx) ** 2 + (z - hz) ** 2 + (y - base) ** 2)
                    if 2.6 <= r3 < 3.6: setb(x, y, z, GOLD if y >= base + 1 else s("smooth_quartz"))
        setb(hx, base + 4, hz, s("end_rod", facing="up"))
    else:
        rr = 3.5; i = 1
        while rr > .4:
            for x, z in ring_cells(hx, hz, -1, rr): setb(x, base + i, z, GOLD if i % 2 == 0 else s("smooth_quartz"))
            rr -= .6; i += 1
        fill(hx, base + i, hz, hx, base + i, hz, s("lightning_rod")); setb(hx, base + i + 1, hz, s("end_rod", facing="up"))
        for x, z in ring_cells(hx, hz, 3.4, 4.6):
            if get(x, FY + 5, z) == AIR: setb(x, FY + 5, z, s("smooth_quartz_slab", type="top"))

cands = []
for hx in range(6, W - 6, 2):
    for hz in range(6, W - 6, 2):
        d = dist(hx, hz)
        if not (19 < d < 57) or on_spoke(hx, hz, AV + 7): continue
        cands.append((rnd(hx, 77, hz), hx, hz))
why = {}
def no(k):
    why[k] = why.get(k, 0) + 1
for _, hx, hz in sorted(cands):
    d = dist(hx, hz)
    if dome_h(d + 5) < 14: no("dome"); continue
    if any(dist(hx, hz, fx, fz) < fr + 3 for (fx, fz), fr in FEATURES): no("feature"); continue
    if any(is_road(x, z) for x in range(hx - 3, hx + 4) for z in range(hz - 3, hz + 4)): no("road"); continue
    if not air_box(hx - 4, hz - 4, hx + 4, hz + 4, FY + 1, FY + 12): no("busy"); continue
    if any(get(x, FY, z) == s("water") for x in range(hx - 3, hx + 4) for z in range(hz - 3, hz + 4)): no("water"); continue
    kind = 1 if (rnd(hx, 3, hz) < .25 and dome_h(d + 4) > 26) else 0
    house(hx, hz, kind); houses.append((hx, hz, kind))

# =============================================================== arcades along avenues
for (ox, oz) in OUTF:
    out_f = OUTF[(ox, oz)]
    for side in (AV + 3, -(AV + 3)):
        p_ = (0, side) if ox != 0 else (side, 0)
        cell = lambda t: (C + ox * t + p_[0], C + oz * t + p_[1])
        for t in range(18, int(DOME) - 3, 4):
            x, z = cell(t)
            if is_road(x, z) or not air_box(x, z, x, z, FY + 1, FY + 6): continue
            fill(x, FY + 1, z, x, FY + 4, z, s("quartz_pillar", axis="y")); setb(x, FY + 5, z, s("chiseled_quartz_block")); setb(x, FY + 6, z, s("end_rod", facing="up"))
            nx, nz = cell(t + 4)
            if is_road(nx, nz) or not air_box(nx, nz, nx, nz, FY + 1, FY + 5): continue
            for u in (1, 2, 3):
                ax_, az_ = cell(t + u)
                if get(ax_, FY + 5, az_) == AIR: setb(ax_, FY + 5, az_, s("smooth_quartz"))
                if u in (1, 3) and get(ax_, FY + 4, az_) == AIR:
                    setb(ax_, FY + 4, az_, s("smooth_quartz_stairs", facing=INF[out_f] if u == 1 else out_f, half="top"))
                if u == 2 and get(ax_, FY + 4, az_) == AIR: setb(ax_, FY + 4, az_, s("lantern", hanging="true"))
# avenue lamps
for (ox, oz) in OUTF:
    for t in range(16, int(DOME) - 2, 6):
        for side in (AV + 1, -(AV + 1)):
            x = C + ox * t + (side if ox == 0 else 0); z = C + oz * t + (side if oz == 0 else 0)
            if get(x, FY + 1, z) == AIR and not is_road(x, z):
                fill(x, FY + 1, z, x, FY + 3, z, s("quartz_pillar", axis="y")); setb(x, FY + 4, z, s("end_rod", facing="up"))

# =============================================================== sky bridges
def bridge(x1, z1, x2, z2, y):
    n = int(max(abs(x2 - x1), abs(z2 - z1)))
    path = [(round(x1 + (x2 - x1) * i / n), round(z1 + (z2 - z1) * i / n)) for i in range(n + 1)]
    walk = {(x + a, z + b) for x, z in path for a in (-1, 0, 1) for b in (-1, 0, 1)}
    for (x, z) in walk:
        if get(x, y, z) == AIR: setb(x, y, z, s("smooth_quartz_slab", type="top"))
    rails = {(x + a, z + b) for x, z in walk for a, b in OUTF if (x + a, z + b) not in walk}
    for (x, z) in rails:
        if get(x, y, z) == AIR and get(x, y + 1, z) == AIR and dist(x, z) > 11:
            setb(x, y, z, s("smooth_quartz_slab", type="top")); setb(x, y + 1, z, s("end_rod", facing="up") if (x + z) % 4 == 0 else s("quartz_slab", type="bottom"))
    for i, (x, z) in enumerate(path):
        if i % 4 == 2 and get(x, y - 1, z) == AIR and get(x, y - 2, z) == AIR:
            setb(x, y - 1, z, s("chain", axis="y")); setb(x, y - 2, z, s("lantern", hanging="true"))
for sx, sz, r, h in sorted(spires, key=lambda t: -t[3])[:6]:
    if h >= 20:
        d = dist(sx, sz)
        bridge(C + round(9.5 * (sx - C) / d), C + round(9.5 * (sz - C) / d), sx, sz, FY + 18)

# =============================================================== plaza furniture
for k in range(36):
    a = k * math.pi / 18 + math.pi / 36
    x, z = C + round(18 * math.cos(a)), C + round(18 * math.sin(a))
    if on_spoke(x, z, AV) or not air_box(x, z, x, z, FY + 1, FY + 2) or is_road(x, z): continue
    if k % 3 == 0:
        setb(x, FY + 1, z, s("smooth_quartz")); setb(x, FY + 2, z, s(["potted_white_tulip", "potted_azure_bluet", "potted_lily_of_the_valley", "potted_oxeye_daisy"][k % 4]))
    else:
        setb(x, FY + 1, z, s("birch_stairs", facing=facing_out(x - C, z - C), half="bottom"))
shrines = 0
for sx in range(4, W - 4, 2):
    for sz in range(4, W - 4, 2):
        d = dist(sx, sz)
        if not (14 < d < 56) or on_spoke(sx, sz, AV + 3) or shrines >= 40 or is_road(sx, sz): continue
        if dome_h(d + 2) < 10 or any(dist(sx, sz, fx, fz) < fr + 1 for (fx, fz), fr in FEATURES): continue
        if not air_box(sx - 2, sz - 2, sx + 2, sz + 2, FY + 1, FY + 6) or get(sx, FY, sz) == s("water"): continue
        for ox in (-1, 1):
            for oz in (-1, 1): fill(sx + ox, FY + 1, sz + oz, sx + ox, FY + 3, sz + oz, s("quartz_pillar", axis="y"))
        fill(sx - 1, FY + 4, sz - 1, sx + 1, FY + 4, sz + 1, s("smooth_quartz_slab", type="bottom"))
        setb(sx, FY + 4, sz, GOLD); setb(sx, FY + 5, sz, s("end_rod", facing="up")); setb(sx, FY, sz, LIGHT)
        setb(sx, FY + 1, sz, s("potted_white_tulip") if shrines % 2 else s("potted_azure_bluet"))
        shrines += 1

# =============================================================== outside
for x in range(W):
    for z in range(W):
        d = dist(x, z)
        if DOME + .7 < d <= R + .5 and not on_spoke(x, z, AV) and get(x, FY + 1, z) == AIR and get(x, FY, z) == s("crimson_nylium") and rnd(x, 11, z) < .35:
            setb(x, FY + 1, z, s("crimson_roots"))
for k in range(16):
    a = math.pi / 16 + k * math.pi / 8
    tx, tz = C + round(62 * math.cos(a)), C + round(62 * math.sin(a))
    if on_spoke(tx, tz, AV + 2): continue
    fill(tx, FY + 1, tz, tx, FY + 4, tz, s("pale_oak_log", axis="y"))
    for x in range(tx - 2, tx + 3):
        for y in range(FY + 4, FY + 7):
            for z in range(tz - 2, tz + 3):
                if math.hypot(x - tx, (y - FY - 5) * 1.4, z - tz) <= 2.3 and get(x, y, z) == AIR and dist(x, z) > DOME + .8:
                    setb(x, y, z, s("pale_oak_leaves", persistent="true"))

# =============================================================== NBT
def nstr(v): b = v.encode(); return struct.pack(">H", len(b)) + b
def tag(t, n, p): return bytes([t]) + nstr(n) + p
def comp(items): return b"".join(items) + b"\x00"
def ilist(v): return bytes([3]) + struct.pack(">i", len(v)) + b"".join(struct.pack(">i", i) for i in v)
pal, pidx, bl = [], {}, []
for (x, y, z), st in sorted(blocks.items()):
    if st not in pidx: pidx[st] = len(pal); pal.append(st)
    bl.append(comp([tag(9, "pos", ilist([x, y, z])), tag(3, "state", struct.pack(">i", pidx[st]))]))
def pe(st):
    name, _, rest = st.partition("[")
    it = [tag(8, "Name", nstr(name))]
    if rest: it.append(tag(10, "Properties", comp([tag(8, k, nstr(v)) for k, v in (p.split("=") for p in rest.rstrip("]").split(","))])))
    return comp(it)
root = comp([tag(3, "DataVersion", struct.pack(">i", DATA_VERSION)), tag(9, "size", ilist([W, H, W])),
             tag(9, "palette", bytes([10]) + struct.pack(">i", len(pal)) + b"".join(pe(p) for p in pal)),
             tag(9, "blocks", bytes([10]) + struct.pack(">i", len(bl)) + b"".join(bl)),
             tag(9, "entities", bytes([0]) + struct.pack(">i", 0))])
data = gzip.compress(tag(10, "", root), 6)
open(os.path.join(OUT, "citadel_xl.nbt"), "wb").write(data)

# =============================================================== world coordinates for warps / displays
def world(x, y, z): return (x + ORIGIN[0], y + ORIGIN[1], z + ORIGIN[2])
info = {"market": world(*MARKET[:1], FY, MARKET[1]) if False else world(MARKET[0], FY, MARKET[1]),
        "info": world(INFO[0], FY, INFO[1]), "garden": world(GARDEN[0], FY, GARDEN[1]), "portal": world(PORTAL[0], FY, PORTAL[1]),
        "houses": len(houses), "spires": len(spires), "shrines": shrines, "columns": len(cols)}
json.dump(info, open(os.path.join(OUT, "citadel_xl.json"), "w"))

# =============================================================== previews
def colour(st):
    n = st.split("[")[0].split(":")[1]
    t = {"smooth_quartz": (236, 230, 222), "white_concrete": (225, 228, 229), "calcite": (222, 223, 220), "polished_diorite": (190, 190, 192),
         "light_gray_concrete": (140, 140, 134), "gold_block": (246, 208, 61), "yellow_terracotta": (186, 133, 35), "ochre_froglight": (250, 220, 140),
         "yellow_stained_glass": (230, 220, 60), "glass": (180, 220, 235), "water": (52, 96, 219), "crimson_nylium": (148, 30, 30),
         "red_terracotta": (143, 61, 46), "orange_terracotta": (161, 83, 37), "terracotta": (152, 94, 67), "blue_concrete": (44, 46, 143),
         "blue_terracotta": (74, 59, 91), "pale_oak_leaves": (200, 205, 195), "pale_oak_log": (120, 110, 105), "grass_block": (95, 159, 53),
         "moss_block": (89, 109, 45), "birch_planks": (192, 175, 121), "white_wool": (235, 235, 235), "orange_wool": (240, 118, 20),
         "yellow_wool": (248, 197, 40), "red_wool": (160, 40, 35), "light_blue_wool": (58, 175, 217), "lime_wool": (112, 185, 25),
         "magenta_wool": (190, 70, 180), "cyan_wool": (21, 137, 145), "quartz_pillar": (236, 230, 222), "end_rod": (255, 255, 240),
         "lightning_rod": (200, 120, 80), "smooth_quartz_slab": (230, 225, 215), "crimson_roots": (126, 8, 41)}
    return t.get(n, (170, 170, 170))
def png(px):
    h = len(px); w = len(px[0])
    raw = b"".join(b"\x00" + b"".join(struct.pack("BBBB", *p) for p in row) for row in px)
    ch = lambda t, d: struct.pack(">I", len(d)) + t + d + struct.pack(">I", zlib.crc32(t + d) & 0xFFFFFFFF)
    return b"\x89PNG\r\n\x1a\n" + ch(b"IHDR", struct.pack(">IIBBBBB", w, h, 8, 6, 0, 0, 0)) + ch(b"IDAT", zlib.compress(raw, 9)) + ch(b"IEND", b"")
def shell(x, y, z): return y > FY + 2 and DOME - .6 <= math.sqrt((x - C) ** 2 + (z - C) ** 2 + (y - FY) ** 2) < DOME + .7
S = 4
top = [[(25, 25, 30, 255)] * (W * S) for _ in range(W * S)]
for x in range(W):
    for z in range(W):
        for y in range(H - 1, -1, -1):
            st = get(x, y, z)
            if st != AIR and not shell(x, y, z):
                f = .7 + .3 * min(1, (y - FY) / 40); c = tuple(int(v * f) for v in colour(st))
                for a in range(S):
                    for b in range(S): top[z * S + a][x * S + b] = c + (255,)
                break
open(os.path.join(OUT, "citadel_xl_top.png"), "wb").write(png(top))
S2 = 3
side = [[(250, 160, 90, 255) if y < (H * S2) // 2 else (250, 190, 120, 255) for x in range(W * S2)] for y in range(H * S2)]
for x in range(W):
    for y in range(H):
        for zz in range(W - 1, -1, -1):
            st = get(x, y, zz)
            if st != AIR and not shell(x, y, zz):
                c = colour(st)
                for a in range(S2):
                    for b in range(S2): side[(H - 1 - y) * S2 + a][x * S2 + b] = c + (255,)
                break
open(os.path.join(OUT, "citadel_xl_side.png"), "wb").write(png(side))
print(why, json.dumps(info), "blocks", len(blocks), "palette", len(pal), "nbt", len(data))
