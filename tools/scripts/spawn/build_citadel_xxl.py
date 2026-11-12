"""Chroma Endless - XXL citadel: glass dome city + display-entity models + animated orrery.
Only non-air blocks are written (the area is cleared with /fill before placing)."""
import gzip, json, math, os, random, struct, sys, zlib

OUT = sys.argv[1]
R = 96; W = 2 * R + 1; C = R
FY = 8
DOME = 90.0
H = FY + int(DOME) + 3
DATA_VERSION = 4189
ORIGIN = (-R, 56, -R)

blocks = {}
entities = []
block_nbt = {}
def s(name, **p):
    return "minecraft:%s[%s]" % (name, ",".join("%s=%s" % kv for kv in sorted(p.items()))) if p else "minecraft:" + name
AIR = s("air")
def setb(x, y, z, st):
    if 0 <= x < W and 0 <= y < H and 0 <= z < W:
        if st == AIR: blocks.pop((x, y, z), None)
        else: blocks[(x, y, z)] = st
def get(x, y, z): return blocks.get((x, y, z), AIR)
def fill(x1, y1, z1, x2, y2, z2, st):
    for x in range(min(x1, x2), max(x1, x2) + 1):
        for y in range(min(y1, y2), max(y1, y2) + 1):
            for z in range(min(z1, z2), max(z1, z2) + 1): setb(x, y, z, st)
def dist(x, z, cx=C, cz=C): return math.hypot(x - cx, z - cz)
def rnd(*k): return random.Random(hash(k) & 0xffffffff).random()
def mix(x, y, z, ch):
    r = rnd(x, y, z); a = 0
    for st, w in ch:
        a += w
        if r < a: return st
    return ch[-1][0]
AV = 5
def on_spoke(x, z, half=AV): return abs(x - C) <= half or abs(z - C) <= half
def air_box(x1, z1, x2, z2, y1, y2):
    return all((x, y, z) not in blocks for x in range(x1, x2 + 1) for z in range(z1, z2 + 1) for y in range(y1, y2 + 1))
def dome_h(d): return math.sqrt(max(0.0, DOME ** 2 - d ** 2))
OUTF = {(1, 0): "east", (-1, 0): "west", (0, 1): "south", (0, -1): "north"}
INF = {"east": "west", "west": "east", "south": "north", "north": "south"}
def facing_out(dx, dz): return OUTF[(1 if dx > 0 else -1, 0)] if abs(dx) >= abs(dz) else OUTF[(0, 1 if dz > 0 else -1)]
def ring_cells(px, pz, a, b):
    for x in range(px - int(b) - 1, px + int(b) + 2):
        for z in range(pz - int(b) - 1, pz + int(b) + 2):
            if a < dist(x, z, px, pz) <= b: yield x, z

WHITE = [(s("smooth_quartz"), .45), (s("white_concrete"), .3), (s("calcite"), .25)]
FLOOR = [(s("smooth_quartz"), .55), (s("polished_diorite"), .3), (s("calcite"), .15)]
RED = [(s("crimson_nylium"), .45), (s("red_terracotta"), .25), (s("orange_terracotta"), .15), (s("terracotta"), .15)]
GOLD = s("gold_block"); WIN = s("yellow_stained_glass"); LIGHT = s("ochre_froglight")
ROADS = (28.0, 62.0)
def is_road(x, z):
    d = dist(x, z); return any(abs(d - r) <= 1.6 for r in ROADS)

# ================================================================= ground
for x in range(W):
    for z in range(W):
        d = dist(x, z)
        if d > R + .5: continue
        for y in range(FY - 8, FY): setb(x, y, z, s("stone") if y < FY - 2 else s("dirt"))
        dx, dz = x - C, z - C
        if d > DOME - .5:
            setb(x, FY, z, mix(x, FY, z, RED)); continue
        st = mix(x, FY, z, FLOOR)
        ang = math.degrees(math.atan2(dz, dx)) % 360
        for rr in (21.5, 36.0, 55.0, 75.0):
            if abs(d - rr) < .55: st = s("light_gray_concrete")
        if 21.5 < d < 36 and (ang % 22.5 < .9 or ang % 22.5 > 21.6): st = s("light_gray_concrete")
        if abs(d - 36) < .55 and ang % 10 < 1.2: st = LIGHT
        for k in range(16):
            a = k * math.pi / 8 + math.pi / 16
            cx, cz = C + 55 * math.cos(a), C + 55 * math.sin(a)
            if abs(dist(x, z, cx, cz) - 3.5) < .5: st = s("light_gray_concrete")
            if dist(x, z, cx, cz) < .8: st = GOLD
        if is_road(x, z):
            st = s("white_concrete") if abs(d - min(ROADS, key=lambda r: abs(d - r))) < .9 else s("light_gray_concrete")
        if on_spoke(x, z) and d > 18.5:
            half = dx if abs(dz) > abs(dx) else dz
            if abs(half) == AV: st = s("light_gray_concrete")
            elif half == 0: st = GOLD if (abs(dx) + abs(dz)) % 6 == 0 else s("yellow_terracotta")
            elif abs(half) == 3 and (abs(dx) + abs(dz)) % 8 == 0: st = LIGHT
            else: st = s("white_concrete")
        setb(x, FY, z, st)

# ================================================================= dome
for x in range(W):
    for z in range(W):
        hd = dist(x, z)
        if hd > DOME + 1 or hd < DOME * .25: continue
        for y in range(FY, H):
            r3 = math.sqrt(hd * hd + (y - FY) ** 2)
            if not (DOME - .5 <= r3 < DOME + .6): continue
            a30 = math.degrees(math.atan2(z - C, x - C)) % 30; a10 = a30 % 7.5
            lat = math.degrees(math.asin(min(1, (y - FY) / DOME)))
            major = a30 < .8 or a30 > 29.2
            minor = (a10 < .45 or a10 > 7.05) and lat < 74
            band = next((st_ for L, st_ in ((10, s("smooth_quartz")), (20, s("smooth_quartz")), (30, GOLD), (40, s("smooth_quartz")),
                                            (50, s("smooth_quartz")), (60, GOLD), (70, s("smooth_quartz")), (78, GOLD)) if abs(lat - L) < .7), None)
            if y <= FY + 3: st = s("smooth_quartz") if y < FY + 3 else GOLD
            elif band: st = band
            elif major: st = s("smooth_quartz")
            elif minor: st = s("calcite")
            else: st = s("white_stained_glass") if (x * 3 + y + z * 5) % 13 == 0 and lat > 25 else s("glass")
            if on_spoke(x, z, AV) and y <= FY + 11:
                st = AIR
                if y == FY + 11 or (not on_spoke(x, z, AV - 1) and y >= FY + 1):
                    st = s("quartz_pillar", axis="y") if y < FY + 11 else GOLD
            setb(x, y, z, st)
# dome cap (top region excluded above for speed)
for x, z in ring_cells(C, C, -1, DOME * .25 + 1):
    hd = dist(x, z)
    y = FY + int(round(math.sqrt(max(0, DOME ** 2 - hd ** 2))))
    for yy in (y - 1, y):
        st = GOLD if hd < 3 or abs(hd - 12) < .6 or abs(hd - 20) < .6 else s("glass")
        a = math.degrees(math.atan2(z - C, x - C)) % 30
        if (a < 2 or a > 28) and hd > 3: st = s("smooth_quartz")
        setb(x, yy, z, st)
for (ox, oz) in OUTF:
    for t in range(int(DOME) - 1, R + 1):
        for w in range(-AV, AV + 1):
            x = C + ox * t + (w if ox == 0 else 0); z = C + oz * t + (w if oz == 0 else 0)
            setb(x, FY, z, s("white_concrete") if abs(w) < AV else s("light_gray_concrete"))
    setb(C + ox * int(DOME), FY + 10, C + oz * int(DOME), s("lantern", hanging="true"))

# ================================================================= central tower with spiral staircase
for x, z in ring_cells(C, C, 13.5, 18.5):
    d = dist(x, z)
    if d > 17.5: setb(x, FY, z, s("smooth_quartz")); setb(x, FY + 1, z, s("smooth_quartz_slab", type="bottom"))
    else:
        setb(x, FY, z, s("water")); setb(x, FY - 1, z, s("water")); setb(x, FY - 2, z, s("sea_lantern") if (x + z) % 2 else s("prismarine_bricks"))
tiers = [(13.5, 0, 10), (12.5, 10, 20), (11.5, 20, 30), (10.5, 30, 39), (9.5, 39, 47), (8.5, 47, 54), (7.5, 54, 60), (6.5, 60, 65), (5.5, 65, 69), (4.5, 69, 72)]
for (rr, y0, y1) in tiers:
    for x, z in ring_cells(C, C, -1, rr):
        d = dist(x, z)
        for y in range(FY + y0, FY + y1):
            if d > rr - 1:
                st = s("smooth_quartz")
                if (y - FY) % 6 in (2, 3, 4) and ((x - C) % 3 == 0 or (z - C) % 3 == 0): st = WIN
                if y == FY + y1 - 1: st = GOLD
            elif y == FY + y0 and d > 1.5:
                st = LIGHT if (x + z) % 4 == 0 else s("smooth_quartz")
            else:
                st = AIR
            setb(x, y, z, st)
    for x, z in ring_cells(C, C, rr, rr + 1.3):
        if (x, FY + y1, z) not in blocks and y1 < 69: setb(x, FY + y1, z, s("smooth_quartz_slab", type="bottom"))
    # doorway onto the terrace (south) for each tier above ground
    if y0 > 0:
        for y in (FY + y0 + 1, FY + y0 + 2):
            for w in (-1, 0, 1):
                for k in range(int(rr) - 1, int(rr) + 1): setb(C + w, y, C + k, AIR)
fill(C, FY + 72, C, C, FY + 78, C, s("quartz_pillar", axis="y"))
setb(C, FY + 79, C, s("end_rod", facing="up"))
for (ox, oz), f in OUTF.items(): setb(C + ox, FY + 77, C + oz, s("end_rod", facing=f))
# spiral staircase around a central column
fill(C, FY + 1, C, C, FY + 71, C, s("quartz_pillar", axis="y"))
ringpath = [(0, -1), (1, -1), (1, 0), (1, 1), (0, 1), (-1, 1), (-1, 0), (-1, -1)]
for i in range(0, 70):
    cx_, cz_ = ringpath[i % 8]; nx_, nz_ = ringpath[(i + 1) % 8]
    face = OUTF[(int(math.copysign(1, nx_ - cx_)) if nx_ != cx_ else 0, int(math.copysign(1, nz_ - cz_)) if nz_ != cz_ else 0)] if (nx_ - cx_ == 0 or nz_ - cz_ == 0) else "north"
    y = FY + 1 + i
    setb(C + cx_, y, C + cz_, s("smooth_quartz_stairs", facing=face, half="bottom"))
    for k in (1, 2, 3):
        if (C + cx_, y + k, C + cz_) in blocks and blocks[(C + cx_, y + k, C + cz_)] != s("quartz_pillar", axis="y"): pass
    if i % 8 == 4: setb(C, y + 1, C, s("ochre_froglight"))
# clear head room above each step (floors at tier bases skip the stair ring: d <= 1.42)
for i in range(0, 70):
    cx_, cz_ = ringpath[i % 8]
    for k in (1, 2):
        pos = (C + cx_, FY + 1 + i + k, C + cz_)
        if pos in blocks and "stairs" not in blocks[pos]: del blocks[pos]
# doors on 4 sides at ground
for (ox, oz) in OUTF:
    for k in range(11, 15):
        for w in (-1, 0, 1):
            x = C + ox * k + (w if ox == 0 else 0); z = C + oz * k + (w if oz == 0 else 0)
            for y in range(FY + 1, FY + 4):
                if dist(x, z) > 12.4: setb(x, y, z, AIR)
for k in range(8):
    a = math.pi / 8 + k * math.pi / 4
    for (rr, y0, y1) in tiers[:8]:
        x, z = C + round((rr + .8) * math.cos(a)), C + round((rr + .8) * math.sin(a))
        for y in range(FY + y0 + 1, FY + y1 - 1):
            if (x, y, z) not in blocks: setb(x, y, z, s("quartz_pillar", axis="y"))
        if (x, FY + y1 - 1, z) not in blocks: setb(x, FY + y1 - 1, z, s("end_rod", facing="up"))
cols = []
for k in range(40):
    a = k * math.pi / 20
    x, z = C + round(21.5 * math.cos(a)), C + round(21.5 * math.sin(a))
    if on_spoke(x, z, AV) or (x, z) in cols: continue
    cols.append((x, z))
    setb(x, FY + 1, z, s("chiseled_quartz_block")); fill(x, FY + 2, z, x, FY + 6, z, s("quartz_pillar", axis="y")); setb(x, FY + 7, z, s("chiseled_quartz_block"))
for x, z in ring_cells(C, C, 20.9, 22.1):
    if (x, FY + 8, z) not in blocks: setb(x, FY + 8, z, s("smooth_quartz"))
    if (x, FY + 9, z) not in blocks: setb(x, FY + 9, z, GOLD if (x + z) % 2 == 0 else s("smooth_quartz_slab", type="bottom"))
    if (x, FY + 7, z) not in blocks and any(dist(x, z, cx, cz) < 1.6 for cx, cz in cols): setb(x, FY + 7, z, s("smooth_quartz_slab", type="top"))

# ================================================================= districts
def feat_pos(qx, qz, d=44): return C + round(qx * d / math.sqrt(2)), C + round(qz * d / math.sqrt(2))
MARKET, INFO, GARDEN, PORTAL = feat_pos(1, -1), feat_pos(-1, -1), feat_pos(1, 1), feat_pos(-1, 1)
FEATURES = [(MARKET, 15.0), (INFO, 11.0), (GARDEN, 16.0), (PORTAL, 10.0)]
def stall(cx, cz, wool):
    for x in range(cx - 2, cx + 3):
        for z in range(cz - 1, cz + 2): setb(x, FY, z, s("birch_planks"))
    for x in range(cx - 2, cx + 3): setb(x, FY + 1, cz + 1, s("barrel", facing="up") if x % 2 else s("smooth_quartz_slab", type="top"))
    for x, z in ((cx - 2, cz - 1), (cx + 2, cz - 1), (cx - 2, cz + 1), (cx + 2, cz + 1)): fill(x, FY + 1, z, x, FY + 3, z, s("birch_fence"))
    for x in range(cx - 3, cx + 4):
        for z in range(cz - 2, cz + 3): setb(x, FY + 4, z, s(wool if (x + 99) % 2 else "white_wool"))
    setb(cx, FY + 3, cz, s("lantern", hanging="true")); setb(cx - 1, FY + 1, cz - 1, s("chest", facing="south"))
mx, mz = MARKET
for x, z in ring_cells(mx, mz, -1, 14.5):
    if not is_road(x, z): setb(x, FY, z, s("birch_planks") if (x + z) % 5 else s("smooth_quartz"))
wools = ["orange_wool", "yellow_wool", "red_wool", "light_blue_wool", "lime_wool", "magenta_wool", "cyan_wool", "pink_wool"]
for i in range(12):
    a = i * math.pi / 6
    stall(mx + round(9 * math.cos(a)), mz + round(9 * math.sin(a)), wools[i % 8])
for x, z in ring_cells(mx, mz, -1, 3.5):
    setb(x, FY, z, s("water") if dist(x, z, mx, mz) < 2.6 else s("smooth_quartz"))
    if dist(x, z, mx, mz) >= 2.6: setb(x, FY + 1, z, s("smooth_quartz_slab", type="bottom"))
setb(mx, FY, mz, s("smooth_quartz")); fill(mx, FY + 1, mz, mx, FY + 3, mz, s("quartz_pillar", axis="y")); setb(mx, FY + 4, mz, GOLD); setb(mx, FY + 5, mz, s("lantern"))
ix, iz = INFO
for x, z in ring_cells(ix, iz, -1, 10.5):
    d = dist(x, z, ix, iz)
    setb(x, FY, z, s("smooth_quartz") if d < 9.5 else GOLD if (x + z) % 3 == 0 else s("light_gray_concrete"))
    if 8.5 < d <= 9.5 and (abs(x - ix) == abs(z - iz) or x == ix or z == iz) and not ((z - iz) * (x - ix) == 0 and (z > iz or x > ix)):
        fill(x, FY + 1, z, x, FY + 8, z, s("quartz_pillar", axis="y"))
for x in range(ix - 11, ix + 12):
    for z in range(iz - 11, iz + 12):
        for y in range(FY + 9, FY + 20):
            r3 = math.sqrt((x - ix) ** 2 + (z - iz) ** 2 + (y - FY - 9) ** 2)
            if 9.0 <= r3 < 10.0: setb(x, y, z, GOLD if y == FY + 9 else s("glass") if (y - FY) % 2 else s("smooth_quartz"))
setb(ix, FY + 19, iz, GOLD); setb(ix, FY + 20, iz, s("end_rod", facing="up"))
setb(ix, FY + 1, iz, s("lectern", facing="south")); fill(ix, FY + 13, iz, ix, FY + 17, iz, s("chain", axis="y")); setb(ix, FY + 12, iz, s("lantern", hanging="true"))
for ox, oz in ((-4, 4), (4, 4), (-4, -4), (4, -4), (0, 5), (0, -5), (5, 0), (-5, 0)):
    setb(ix + ox, FY + 1, iz + oz, s("birch_stairs", facing=facing_out(ox, oz), half="bottom"))
gx, gz = GARDEN
for x, z in ring_cells(gx, gz, -1, 16):
    if is_road(x, z) or on_spoke(x, z, AV + 3): continue
    d = dist(x, z, gx, gz)
    setb(x, FY, z, s("moss_block") if rnd(x, 4, z) < .25 else s("grass_block"))
    if d <= 6.5: setb(x, FY, z, s("water")); setb(x, FY - 1, z, s("water"))
    elif d <= 7.4: setb(x, FY, z, s("smooth_quartz"))
    elif rnd(x, 1, z) < .35: setb(x, FY + 1, z, s(["white_tulip", "lily_of_the_valley", "azure_bluet", "oxeye_daisy", "short_grass", "pink_tulip"][int(rnd(x, 2, z) * 6)]))
    if d <= 6.5 and rnd(x, 9, z) < .2: setb(x, FY + 1, z, s("lily_pad"))
def silver_tree(tx, tz, h=8):
    fill(tx, FY + 1, tz, tx, FY + h, tz, s("pale_oak_log", axis="y")); setb(tx, FY, tz, s("dirt"))
    for x in range(tx - 5, tx + 6):
        for y in range(FY + h - 3, FY + h + 4):
            for z in range(tz - 5, tz + 6):
                cur = get(x, y, z)
                if math.hypot(x - tx, (y - FY - h) * 1.3, z - tz) <= 4.2 and (cur == AIR or cur.split("[")[0].split(":")[1] in ("short_grass", "white_tulip", "lily_of_the_valley", "azure_bluet", "oxeye_daisy", "pink_tulip")):
                    setb(x, y, z, s("pale_oak_leaves", persistent="true"))
    for hx, hz in ((tx - 4, tz), (tx + 3, tz + 2), (tx, tz - 4), (tx + 2, tz - 3)):
        if get(hx, FY + h - 4, hz) == AIR and get(hx, FY + h - 3, hz).startswith("minecraft:pale_oak_leaves"):
            setb(hx, FY + h - 4, hz, s("pale_hanging_moss", tip="true"))
for a in range(8):
    t = a * math.pi / 4 + .3
    silver_tree(gx + round(11.5 * math.cos(t)), gz + round(11.5 * math.sin(t)), 7 + a % 3)
for x in range(gx - 7, gx + 8): setb(x, FY + 1, gz, s("birch_slab", type="bottom"))
for x in (gx - 7, gx + 7): setb(x, FY + 1, gz + 1, s("birch_fence")); setb(x, FY + 2, gz + 1, s("lantern"))
px, pz = PORTAL
for x, z in ring_cells(px, pz, -1, 9.5): setb(x, FY, z, s("light_gray_concrete") if abs(dist(x, z, px, pz) - 8) < .6 else mix(x, FY, z, FLOOR))
fill(px - 1, FY + 1, pz - 1, px + 1, FY + 6, pz + 1, s("blue_concrete"))
for (x, z) in ((px - 1, pz - 1), (px + 1, pz - 1), (px - 1, pz + 1), (px + 1, pz + 1)): fill(x, FY + 1, z, x, FY + 6, z, s("blue_terracotta"))
for (x, z) in ((px, pz - 1), (px, pz + 1), (px - 1, pz), (px + 1, pz)): setb(x, FY + 5, z, s("white_stained_glass"))
fill(px - 1, FY + 7, pz - 1, px + 1, FY + 7, pz + 1, s("blue_concrete"))
setb(px, FY + 8, pz, s("sea_lantern")); setb(px, FY + 9, pz, s("light_blue_stained_glass"))
for ox, oz in ((-5, -5), (5, -5), (-5, 5), (5, 5)):
    fill(px + ox, FY + 1, pz + oz, px + ox, FY + 2, pz + oz, s("quartz_pillar", axis="y")); setb(px + ox, FY + 3, pz + oz, s("end_rod", facing="up"))

# ================================================================= spires
PLACED = []
def free(x0, z0, r):
    if on_spoke(x0, z0, AV + 5 + r) or is_road(x0, z0): return False
    if any(dist(x0, z0, qx, qz) < r + qr + 7 for qx, qz, qr in PLACED): return False
    return all(dist(x0, z0, fx, fz) > fr + r + 1 for (fx, fz), fr in FEATURES)
def spire(px_, pz_, r, h):
    for x, z in ring_cells(px_, pz_, r + .5, r + 1.5): setb(x, FY + 1, z, s("smooth_quartz_stairs", facing=INF[facing_out(x - px_, z - pz_)], half="bottom"))
    nsec = 5 if h >= 45 else 4 if h >= 30 else 3 if h >= 15 else 2
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
                else: st = LIGHT if (y - FY) % 8 == 1 else AIR
                setb(x, y, z, st)
        if si < nsec - 1:
            for x, z in ring_cells(px_, pz_, cur + .5, cur + 1.4):
                if (x, y1 - 1, z) not in blocks: setb(x, y1 - 1, z, s("smooth_quartz_slab", type="top"))
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
        rr -= .5 if cur >= 2 else .9; i += 1
    for (ox, oz), f in OUTF.items(): setb(px_ + ox, top + i - 1, pz_ + oz, s("end_rod", facing=f))
    fill(px_, top + i, pz_, px_, top + i + 1, pz_, s("lightning_rod")); setb(px_, top + i + 2, pz_, s("end_rod", facing="up"))
spires = []
for ring_r, count, base_r, maxh in ((33, 8, 3, 62), (50, 12, 2, 56), (68, 16, 2, 44), (82, 20, 1, 30)):
    for k in range(count):
        a = (k + .5) * 2 * math.pi / count
        sx, sz = C + round(ring_r * math.cos(a)), C + round(ring_r * math.sin(a))
        r = base_r
        if not free(sx, sz, r): continue
        h = int(min(maxh, dome_h(dist(sx, sz) + r + 1) - 10) * (0.72 + 0.28 * rnd(sx, 6, sz)))
        if h < 8: continue
        PLACED.append((sx, sz, r)); spire(sx, sz, r, h); spires.append((sx, sz, r, h))

# ================================================================= houses
houses = []
def house(hx, hz, kind):
    dx, dz = C - hx, C - hz
    door = (1 if dx > 0 else -1, 0) if abs(dx) >= abs(dz) else (0, 1 if dz > 0 else -1)
    hr = 3; wall_h = 5 if kind == 0 else 10
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
                else: st = s("smooth_quartz") if (y == FY + wall_h or (kind == 1 and y == FY + 5)) else AIR
                setb(x, y, z, st)
    setb(hx, FY + 1, hz, s("crafting_table") if kind == 0 else s("bookshelf"))
    setb(hx + 1, FY + 1, hz + 1, s("barrel", facing="up")); setb(hx - 1, FY + wall_h - 1, hz - 1, s("lantern", hanging="true")); setb(hx - 2, FY + 1, hz + 2, s("potted_white_tulip"))
    ddx, ddz = hx + door[0] * hr, hz + door[1] * hr
    setb(ddx, FY + 1, ddz, AIR); setb(ddx, FY + 2, ddz, AIR); setb(ddx + door[0], FY + 3, ddz + door[1], s("end_rod", facing=OUTF[door]))
    side = (door[1], door[0])
    for sg in (2, -2):
        pxp, pzp = ddx + door[0] + side[0] * sg, ddz + door[1] + side[1] * sg
        if (pxp, FY + 1, pzp) not in blocks: setb(pxp, FY + 1, pzp, s("smooth_quartz")); setb(pxp, FY + 2, pzp, s("potted_azure_bluet"))
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
        setb(hx, base + i, hz, s("lightning_rod")); setb(hx, base + i + 1, hz, s("end_rod", facing="up"))
        for x, z in ring_cells(hx, hz, 3.4, 4.6):
            if (x, FY + 5, z) not in blocks: setb(x, FY + 5, z, s("smooth_quartz_slab", type="top"))
cands = [(rnd(hx, 77, hz), hx, hz) for hx in range(6, W - 6, 2) for hz in range(6, W - 6, 2)
         if 24 < dist(hx, hz) < 86 and not on_spoke(hx, hz, AV + 8)]
for _, hx, hz in sorted(cands):
    if len(houses) >= 80: break
    d = dist(hx, hz)
    if dome_h(d + 5) < 14: continue
    if any(dist(hx, hz, fx, fz) < fr + 3 for (fx, fz), fr in FEATURES): continue
    if any(is_road(x, z) for x in range(hx - 3, hx + 4) for z in range(hz - 3, hz + 4)): continue
    if not air_box(hx - 4, hz - 4, hx + 4, hz + 4, FY + 1, FY + 12): continue
    if any(get(x, FY, z) == s("water") for x in range(hx - 3, hx + 4) for z in range(hz - 3, hz + 4)): continue
    kind = 1 if (rnd(hx, 3, hz) < .3 and dome_h(d + 4) > 26) else 0
    house(hx, hz, kind); houses.append((hx, hz, kind))

# ================================================================= arcades, lamps, bridges, furniture
for (ox, oz) in OUTF:
    out_f = OUTF[(ox, oz)]
    for side in (AV + 3, -(AV + 3)):
        p_ = (0, side) if ox != 0 else (side, 0)
        cell = lambda t: (C + ox * t + p_[0], C + oz * t + p_[1])
        for t in range(24, int(DOME) - 3, 4):
            x, z = cell(t)
            if is_road(x, z) or not air_box(x, z, x, z, FY + 1, FY + 7): continue
            fill(x, FY + 1, z, x, FY + 5, z, s("quartz_pillar", axis="y")); setb(x, FY + 6, z, s("chiseled_quartz_block")); setb(x, FY + 7, z, s("end_rod", facing="up"))
            nx, nz = cell(t + 4)
            if is_road(nx, nz) or not air_box(nx, nz, nx, nz, FY + 1, FY + 6): continue
            for u in (1, 2, 3):
                ax_, az_ = cell(t + u)
                if (ax_, FY + 6, az_) not in blocks: setb(ax_, FY + 6, az_, s("smooth_quartz"))
                if u in (1, 3) and (ax_, FY + 5, az_) not in blocks: setb(ax_, FY + 5, az_, s("smooth_quartz_stairs", facing=INF[out_f] if u == 1 else out_f, half="top"))
                if u == 2 and (ax_, FY + 5, az_) not in blocks: setb(ax_, FY + 5, az_, s("lantern", hanging="true"))
for (ox, oz) in OUTF:
    for t in range(22, int(DOME) - 2, 6):
        for side in (AV + 1, -(AV + 1)):
            x = C + ox * t + (side if ox == 0 else 0); z = C + oz * t + (side if oz == 0 else 0)
            if (x, FY + 1, z) not in blocks and not is_road(x, z):
                fill(x, FY + 1, z, x, FY + 3, z, s("quartz_pillar", axis="y")); setb(x, FY + 4, z, s("end_rod", facing="up"))
def bridge(x1, z1, x2, z2, y):
    n = int(max(abs(x2 - x1), abs(z2 - z1)))
    path = [(round(x1 + (x2 - x1) * i / n), round(z1 + (z2 - z1) * i / n)) for i in range(n + 1)]
    walk = {(x + a, z + b) for x, z in path for a in (-1, 0, 1) for b in (-1, 0, 1)}
    for (x, z) in walk:
        if (x, y, z) not in blocks: setb(x, y, z, s("smooth_quartz_slab", type="top"))
    rails = {(x + a, z + b) for x, z in walk for a, b in OUTF if (x + a, z + b) not in walk}
    for (x, z) in rails:
        if (x, y, z) not in blocks and (x, y + 1, z) not in blocks and dist(x, z) > 15:
            setb(x, y, z, s("smooth_quartz_slab", type="top")); setb(x, y + 1, z, s("end_rod", facing="up") if (x + z) % 4 == 0 else s("quartz_slab", type="bottom"))
    for i, (x, z) in enumerate(path):
        if i % 4 == 2 and (x, y - 1, z) not in blocks and (x, y - 2, z) not in blocks:
            setb(x, y - 1, z, s("chain", axis="y")); setb(x, y - 2, z, s("lantern", hanging="true"))
bridges = 0
for sx, sz, r, h in sorted(spires, key=lambda t: -t[3])[:10]:
    if h >= 34:
        d = dist(sx, sz); level = 30 if bridges % 2 == 0 else 20
        tr = [t for t in tiers if t[1] <= level < t[2]][0][0]
        bridge(C + round((tr + 1) * (sx - C) / d), C + round((tr + 1) * (sz - C) / d), sx, sz, FY + level); bridges += 1
GLYPHS = [(C + 25 * math.cos(k * math.pi / 4 + math.pi / 8), C + 25 * math.sin(k * math.pi / 4 + math.pi / 8)) for k in range(8)]
for k in range(48):
    a = k * math.pi / 24 + math.pi / 48
    x, z = C + round(24.5 * math.cos(a)), C + round(24.5 * math.sin(a))
    if on_spoke(x, z, AV) or not air_box(x, z, x, z, FY + 1, FY + 2) or is_road(x, z): continue
    if any(math.hypot(x + .5 - gx_ - .5, z + .5 - gz_ - .5) < 3.4 for gx_, gz_ in GLYPHS): continue
    if k % 3 == 0: setb(x, FY + 1, z, s("smooth_quartz")); setb(x, FY + 2, z, s(["potted_white_tulip", "potted_azure_bluet", "potted_lily_of_the_valley", "potted_oxeye_daisy"][k % 4]))
    else: setb(x, FY + 1, z, s("birch_stairs", facing=facing_out(x - C, z - C), half="bottom"))
shrines = 0
for sx in range(4, W - 4, 2):
    for sz in range(4, W - 4, 2):
        d = dist(sx, sz)
        if not (20 < d < 86) or on_spoke(sx, sz, AV + 3) or shrines >= 70 or is_road(sx, sz): continue
        if dome_h(d + 2) < 10 or any(dist(sx, sz, fx, fz) < fr + 1 for (fx, fz), fr in FEATURES): continue
        if not air_box(sx - 2, sz - 2, sx + 2, sz + 2, FY + 1, FY + 6) or get(sx, FY, sz) == s("water"): continue
        for ox in (-1, 1):
            for oz in (-1, 1): fill(sx + ox, FY + 1, sz + oz, sx + ox, FY + 3, sz + oz, s("quartz_pillar", axis="y"))
        fill(sx - 1, FY + 4, sz - 1, sx + 1, FY + 4, sz + 1, s("smooth_quartz_slab", type="bottom"))
        setb(sx, FY + 4, sz, GOLD); setb(sx, FY + 5, sz, s("end_rod", facing="up")); setb(sx, FY, sz, LIGHT)
        setb(sx, FY + 1, sz, s("potted_white_tulip") if shrines % 2 else s("potted_azure_bluet")); shrines += 1
for x in range(W):
    for z in range(W):
        d = dist(x, z)
        if DOME + .7 < d <= R + .5 and not on_spoke(x, z, AV) and (x, FY + 1, z) not in blocks and get(x, FY, z) == s("crimson_nylium") and rnd(x, 11, z) < .35:
            setb(x, FY + 1, z, s("crimson_roots"))
for k in range(24):
    a = math.pi / 24 + k * math.pi / 12
    tx, tz = C + round(93 * math.cos(a)), C + round(93 * math.sin(a))
    if on_spoke(tx, tz, AV + 2): continue
    fill(tx, FY + 1, tz, tx, FY + 5, tz, s("pale_oak_log", axis="y"))
    for x in range(tx - 3, tx + 4):
        for y in range(FY + 4, FY + 8):
            for z in range(tz - 3, tz + 4):
                if math.hypot(x - tx, (y - FY - 6) * 1.4, z - tz) <= 2.8 and (x, y, z) not in blocks and dist(x, z) > DOME + .8:
                    setb(x, y, z, s("pale_oak_leaves", persistent="true"))

# ================================================================= display-entity models
def qmul(a, b):
    ax, ay, az, aw = a; bx, by, bz, bw = b
    return (aw * bx + ax * bw + ay * bz - az * by, aw * by - ax * bz + ay * bw + az * bx, aw * bz + ax * by - ay * bx + az * bw, aw * bw - ax * bx - ay * by - az * bz)
def qaxis(ax, ay, az, ang):
    s_ = math.sin(ang / 2); return (ax * s_, ay * s_, az * s_, math.cos(ang / 2))
def qrot(q, v):
    x, y, z, w = q; vx, vy, vz = v
    # v' = q v q*
    ix = w * vx + y * vz - z * vy; iy = w * vy + z * vx - x * vz; iz = w * vz + x * vy - y * vx; iw = -x * vx - y * vy - z * vz
    return (ix * w + iw * -x + iy * -z - iz * -y, iy * w + iw * -y + iz * -x - ix * -z, iz * w + iw * -z + ix * -y - iy * -x)
def display(pos, block, q, size, center, tags=(), tp=0, view=2.0, glow=False):
    """block display whose box (size) is centred on `center` (relative to entity pos) and rotated by q."""
    half = (size[0] / 2, size[1] / 2, size[2] / 2)
    rh = qrot(q, half)
    t = (center[0] - rh[0], center[1] - rh[1], center[2] - rh[2])
    entities.append({"pos": pos, "block": block, "q": q, "scale": size, "t": t, "tags": list(tags), "tp": tp, "view": view, "glow": glow})
def ring_model(pos, radius, n, thick, block, tilt_q, tags=(), tp=0, view=3.0, glow=False):
    seg = 2 * math.pi * radius / n * 1.08
    for k in range(n):
        phi = 2 * math.pi * k / n
        alpha = -(phi + math.pi / 2)
        q = qmul(tilt_q, qaxis(0, 1, 0, alpha))
        c = qrot(tilt_q, (radius * math.cos(phi), 0, radius * math.sin(phi)))
        display(pos, block, q, (seg, thick, thick), c, tags, tp, view, glow)
IDQ = (0.0, 0.0, 0.0, 1.0)
# (a) animated orrery around the tower spire
orb = (C + .5, FY + 66.0, C + .5)
for i, (radius, tilt, blk, tag) in enumerate(((9.0, 0.35, "minecraft:gold_block", "chroma_orb_a"),
                                              (12.5, -0.55, "minecraft:smooth_quartz", "chroma_orb_b"),
                                              (16.0, 0.9, "minecraft:gold_block", "chroma_orb_c"))):
    ring_model(orb, radius, 40 + 8 * i, 0.35 if i != 1 else 0.45, blk, qaxis(1, 0, 0, tilt), ("chroma", "chroma_orb", tag), tp=3, view=6.0, glow=True)
    for b in range(3):          # little "planets" riding each ring
        phi = b * 2 * math.pi / 3 + i
        c = qrot(qaxis(1, 0, 0, tilt), (radius * math.cos(phi), 0, radius * math.sin(phi)))
        display(orb, "minecraft:ochre_froglight" if b % 2 else "minecraft:pearlescent_froglight", IDQ, (1.2, 1.2, 1.2), c, ("chroma", "chroma_orb", tag), tp=3, view=6.0, glow=True)
display(orb, "minecraft:pearlescent_froglight", qaxis(0, 1, 0, .785), (2.4, 2.4, 2.4), (0, 0, 0), ("chroma", "chroma_orb", "chroma_orb_core"), tp=3, view=6.0, glow=True)
# (b) circular glyph sculptures lying on the plaza
for k, (gx_, gz_) in enumerate(GLYPHS):
    pos = (gx_ + .5, FY + 1.02, gz_ + .5)
    ring_model(pos, 2.6, 24, .14, "minecraft:gold_block", IDQ, ("chroma",), view=2.0)
    ring_model((pos[0] + .7, pos[1] + .01, pos[2] - .4), 1.2, 16, .12, "minecraft:smooth_quartz", IDQ, ("chroma",), view=2.0)
    ring_model((pos[0] - 1.0, pos[1] + .01, pos[2] + .9), .6, 10, .1, "minecraft:gold_block", IDQ, ("chroma",), view=2.0)
    for j in range(5):
        th = j * 2 * math.pi / 5 + k
        display(pos, "minecraft:gold_block", IDQ, (.22, .22, .22), (2.0 * math.cos(th), .1, 2.0 * math.sin(th)), ("chroma",), view=2.0)
    display(pos, "minecraft:gold_block", qaxis(0, 1, 0, k * .4), (3.8, .1, .1), (0, .05, 0), ("chroma",), view=2.0)
# (c) standing golden rings above each dome gate, and (d) floating ring over the market / garden
for (ox, oz) in OUTF:
    gpos = (C + ox * (DOME - 2) + .5, FY + 17.0, C + oz * (DOME - 2) + .5)
    tilt = qaxis(1, 0, 0, math.pi / 2) if ox == 0 else qaxis(0, 0, 1, math.pi / 2)
    ring_model(gpos, 4.5, 32, .3, "minecraft:gold_block", tilt, ("chroma",), view=4.0, glow=True)
    ring_model(gpos, 3.2, 24, .2, "minecraft:smooth_quartz", tilt, ("chroma",), view=4.0)
for (fx, fz), y_ in ((MARKET, 14.0), (GARDEN, 15.0)):
    ring_model((fx + .5, FY + y_, fz + .5), 5.0, 36, .25, "minecraft:gold_block", qaxis(1, 0, 0, .25), ("chroma", "chroma_orb", "chroma_orb_a"), tp=3, view=4.0, glow=True)

# ================================================================= hidden command blocks (animation)
cb_y = FY - 5
cmds = ["execute as @e[type=minecraft:block_display,tag=chroma_orb_a] at @s run rotate @s ~0.6 ~",
        "execute as @e[type=minecraft:block_display,tag=chroma_orb_b] at @s run rotate @s ~-0.45 ~",
        "execute as @e[type=minecraft:block_display,tag=chroma_orb_c] at @s run rotate @s ~0.3 ~",
        "execute as @e[type=minecraft:block_display,tag=chroma_orb_core] at @s run rotate @s ~1.5 ~"]
for i, c in enumerate(cmds):
    pos = (C - 2 + i, cb_y, C + 6)
    setb(*pos, s("repeating_command_block", facing="up", conditional="false"))
    block_nbt[pos] = c

# ================================================================= NBT writer
def nstr(v): b = v.encode(); return struct.pack(">H", len(b)) + b
def tag(t, n, p): return bytes([t]) + nstr(n) + p
def comp(items): return b"".join(items) + b"\x00"
def ilist(v): return bytes([3]) + struct.pack(">i", len(v)) + b"".join(struct.pack(">i", i) for i in v)
def dlist(v): return bytes([6]) + struct.pack(">i", len(v)) + b"".join(struct.pack(">d", i) for i in v)
def flist(v): return bytes([5]) + struct.pack(">i", len(v)) + b"".join(struct.pack(">f", i) for i in v)
def slist(v): return bytes([8]) + struct.pack(">i", len(v)) + b"".join(nstr(i) for i in v)
pal, pidx, bl = [], {}, []
for (x, y, z), st in sorted(blocks.items()):
    if st not in pidx: pidx[st] = len(pal); pal.append(st)
    items = [tag(9, "pos", ilist([x, y, z])), tag(3, "state", struct.pack(">i", pidx[st]))]
    if (x, y, z) in block_nbt:
        items.append(tag(10, "nbt", comp([tag(8, "id", nstr("minecraft:command_block")), tag(8, "Command", nstr(block_nbt[(x, y, z)])),
                                          tag(1, "auto", b"\x01"), tag(1, "TrackOutput", b"\x00"), tag(1, "powered", b"\x00"), tag(1, "conditionMet", b"\x01")])))
    bl.append(comp(items))
def pe(st):
    name, _, rest = st.partition("[")
    it = [tag(8, "Name", nstr(name))]
    if rest: it.append(tag(10, "Properties", comp([tag(8, k, nstr(v)) for k, v in (p.split("=") for p in rest.rstrip("]").split(","))])))
    return comp(it)
ents = []
for e in entities:
    x, y, z = e["pos"]
    nbt = [tag(8, "id", nstr("minecraft:block_display")),
           tag(10, "block_state", comp([tag(8, "Name", nstr(e["block"]))])),
           tag(10, "transformation", comp([tag(9, "left_rotation", flist(list(e["q"]))), tag(9, "right_rotation", flist([0, 0, 0, 1])),
                                           tag(9, "translation", flist(list(e["t"]))), tag(9, "scale", flist(list(e["scale"])))])),
           tag(9, "Tags", slist(e["tags"])), tag(5, "view_range", struct.pack(">f", e["view"])),
           tag(9, "Rotation", flist([0.0, 0.0])), tag(9, "Pos", dlist([x, y, z]))]
    if e["tp"]: nbt.append(tag(3, "teleport_duration", struct.pack(">i", e["tp"])))
    if e["glow"]: nbt.append(tag(10, "brightness", comp([tag(3, "sky", struct.pack(">i", 15)), tag(3, "block", struct.pack(">i", 15))])))
    ents.append(comp([tag(9, "pos", dlist([x, y, z])), tag(9, "blockPos", ilist([int(math.floor(x)), int(math.floor(y)), int(math.floor(z))])), tag(10, "nbt", comp(nbt))]))
root = comp([tag(3, "DataVersion", struct.pack(">i", DATA_VERSION)), tag(9, "size", ilist([W, H, W])),
             tag(9, "palette", bytes([10]) + struct.pack(">i", len(pal)) + b"".join(pe(p) for p in pal)),
             tag(9, "blocks", bytes([10]) + struct.pack(">i", len(bl)) + b"".join(bl)),
             tag(9, "entities", (bytes([10]) + struct.pack(">i", len(ents)) + b"".join(ents)) if ents else bytes([0]) + struct.pack(">i", 0))])
data = gzip.compress(tag(10, "", root), 6)
open(os.path.join(OUT, "citadel_xxl.nbt"), "wb").write(data)

def world(x, y, z): return [x + ORIGIN[0], y + ORIGIN[1], z + ORIGIN[2]]
info = {"market": world(MARKET[0], FY, MARKET[1]), "info": world(INFO[0], FY, INFO[1]), "garden": world(GARDEN[0], FY, GARDEN[1]),
        "portal": world(PORTAL[0], FY, PORTAL[1]), "houses": len(houses), "spires": len(spires), "shrines": shrines, "columns": len(cols),
        "bridges": bridges, "entities": len(entities), "blocks": len(blocks)}
json.dump(info, open(os.path.join(OUT, "citadel_xxl.json"), "w"))

# ================================================================= previews
def colour(st):
    n = st.split("[")[0].split(":")[1]
    t = {"smooth_quartz": (236, 230, 222), "white_concrete": (225, 228, 229), "calcite": (222, 223, 220), "polished_diorite": (190, 190, 192),
         "light_gray_concrete": (140, 140, 134), "gold_block": (246, 208, 61), "yellow_terracotta": (186, 133, 35), "ochre_froglight": (250, 220, 140),
         "yellow_stained_glass": (230, 220, 60), "glass": (180, 220, 235), "water": (52, 96, 219), "crimson_nylium": (148, 30, 30),
         "red_terracotta": (143, 61, 46), "orange_terracotta": (161, 83, 37), "terracotta": (152, 94, 67), "blue_concrete": (44, 46, 143),
         "blue_terracotta": (74, 59, 91), "pale_oak_leaves": (200, 205, 195), "pale_oak_log": (120, 110, 105), "grass_block": (95, 159, 53),
         "moss_block": (89, 109, 45), "birch_planks": (192, 175, 121), "white_wool": (235, 235, 235), "quartz_pillar": (236, 230, 222),
         "end_rod": (255, 255, 240), "lightning_rod": (200, 120, 80), "smooth_quartz_slab": (230, 225, 215), "crimson_roots": (126, 8, 41)}
    if n.endswith("_wool"): return (200, 120, 60)
    return t.get(n, (170, 170, 170))
def png(px):
    h = len(px); w = len(px[0])
    raw = b"".join(b"\x00" + b"".join(struct.pack("BBBB", *p) for p in row) for row in px)
    ch = lambda t, d: struct.pack(">I", len(d)) + t + d + struct.pack(">I", zlib.crc32(t + d) & 0xFFFFFFFF)
    return b"\x89PNG\r\n\x1a\n" + ch(b"IHDR", struct.pack(">IIBBBBB", w, h, 8, 6, 0, 0, 0)) + ch(b"IDAT", zlib.compress(raw, 9)) + ch(b"IEND", b"")
def shell(x, y, z): return y > FY + 3 and DOME - .9 <= math.sqrt((x - C) ** 2 + (z - C) ** 2 + (y - FY) ** 2) < DOME + .8
colsz = {}
for (x, y, z), st in blocks.items():
    if shell(x, y, z): continue
    if (x, z) not in colsz or y > colsz[(x, z)][0]: colsz[(x, z)] = (y, st)
S = 3
top = [[(25, 25, 30, 255)] * (W * S) for _ in range(W * S)]
for (x, z), (y, st) in colsz.items():
    f = .7 + .3 * min(1, (y - FY) / 50); c = tuple(int(v * f) for v in colour(st))
    for a in range(S):
        for b in range(S): top[z * S + a][x * S + b] = c + (255,)
open(os.path.join(OUT, "citadel_xxl_top.png"), "wb").write(png(top))
side_best = {}
for (x, y, z), st in blocks.items():
    if shell(x, y, z): continue
    if (x, y) not in side_best or z > side_best[(x, y)][0]: side_best[(x, y)] = (z, st)
S2 = 2
side = [[(250, 160, 90, 255) if y < (H * S2) // 2 else (250, 190, 120, 255) for x in range(W * S2)] for y in range(H * S2)]
for (x, y), (z, st) in side_best.items():
    c = colour(st)
    for a in range(S2):
        for b in range(S2): side[(H - 1 - y) * S2 + a][x * S2 + b] = c + (255,)
# overlay entity models in side view
for e in entities:
    x, y, z = e["pos"]; cx_ = x + e["t"][0]; cy_ = y + e["t"][1]
    px_, py_ = int(cx_ * S2), int((H - cy_) * S2)
    if 0 <= px_ < W * S2 and 0 <= py_ < H * S2: side[py_][px_] = (255, 230, 80, 255)
open(os.path.join(OUT, "citadel_xxl_side.png"), "wb").write(png(side))
print(json.dumps(info), "palette", len(pal), "nbt", len(data))
