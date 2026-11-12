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
    return top + i + 2
spires = []
SPIRE_TOP = {}
for ring_r, count, base_r, maxh in ((33, 8, 3, 62), (50, 12, 2, 56), (68, 16, 2, 44), (82, 20, 1, 30)):
    for k in range(count):
        a = (k + .5) * 2 * math.pi / count
        sx, sz = C + round(ring_r * math.cos(a)), C + round(ring_r * math.sin(a))
        r = base_r
        if not free(sx, sz, r): continue
        h = int(min(maxh, dome_h(dist(sx, sz) + r + 1) - 10) * (0.72 + 0.28 * rnd(sx, 6, sz)))
        if h < 8: continue
        PLACED.append((sx, sz, r)); SPIRE_TOP[(sx, sz)] = spire(sx, sz, r, h); spires.append((sx, sz, r, h))

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

# ================================================================= EXTRA DETAIL (v2)
def qlook(v):
    """quaternion rotating +Z onto unit vector v"""
    n = math.sqrt(sum(c * c for c in v)); v = tuple(c / n for c in v)
    ax = (-v[1], v[0], 0.0)                       # (0,0,1) x v
    s_ = math.sqrt(ax[0] ** 2 + ax[1] ** 2)
    ang = math.acos(max(-1, min(1, v[2])))
    if s_ < 1e-9: return IDQ if v[2] > 0 else qaxis(1, 0, 0, math.pi)
    return qaxis(ax[0] / s_, ax[1] / s_, 0, ang)
def item_disp(pos, item, scale=.5, q=IDQ, tags=("chroma",), glow=False):
    entities.append({"kind": "item", "pos": pos, "item": item, "q": q, "scale": (scale, scale, scale), "t": (0, 0, 0), "tags": list(tags), "tp": 0, "view": 1.5, "glow": glow})
def text_disp(pos, json_text, scale=1.0, billboard="vertical", tags=("chroma",), width=200, bg=0):
    entities.append({"kind": "text", "pos": pos, "text": json_text, "q": IDQ, "scale": (scale, scale, scale), "t": (0, 0, 0), "tags": list(tags), "tp": 0,
                     "view": 1.5, "glow": True, "billboard": billboard, "width": width, "bg": bg})

# (1) glowing core column inside the tower
for y in range(FY + 1, FY + 72):
    setb(C, y, C, LIGHT if y % 4 == 0 else s("white_stained_glass"))

# (2) floating lights under the dome
nl = 0
for k in range(900):
    if nl >= 180: break
    a = rnd(k, 1, 1) * 2 * math.pi; d = 16 + rnd(k, 2, 2) * 66
    x = C + d * math.cos(a); z = C + d * math.sin(a)
    y = FY + 16 + rnd(k, 3, 3) * (dome_h(d) - 24)
    if any((int(x) + ox, int(y) + oy, int(z) + oz) in blocks for ox in (-1, 0, 1) for oy in (-1, 0, 1) for oz in (-1, 0, 1)): continue
    blk = "minecraft:ochre_froglight" if k % 3 else "minecraft:pearlescent_froglight"
    sz = .3 + .2 * rnd(k, 4, 4)
    display((x, y, z), blk, qmul(qaxis(0, 1, 0, rnd(k, 5, 5) * 3), qaxis(1, 0, 0, .6)), (sz, sz, sz), (0, 0, 0), ("chroma",), view=3.0, glow=True)
    nl += 1

# (3) market goods and stall signs
GOODS = [("Fruits", ["apple", "golden_apple", "melon_slice"]), ("Armes", ["iron_sword", "bow", "shield"]), ("Minerais", ["diamond", "emerald", "gold_ingot"]),
         ("Boulangerie", ["bread", "cake", "cookie"]), ("Outils", ["iron_pickaxe", "iron_axe", "shears"]), ("Livres", ["book", "writable_book", "enchanted_book"]),
         ("Potions", ["glass_bottle", "brewing_stand", "blaze_powder"]), ("Boucherie", ["cooked_beef", "cooked_chicken", "cooked_porkchop"]),
         ("Fleurs", ["poppy", "cornflower", "allium"]), ("Laines", ["red_wool", "blue_wool", "yellow_wool"]), ("Redstone", ["redstone", "repeater", "piston"]),
         ("Rare", ["ender_pearl", "totem_of_undying", "nether_star"])]
for i in range(12):
    a = i * math.pi / 6
    cx, cz = mx + round(9 * math.cos(a)), mz + round(9 * math.sin(a))
    name, its = GOODS[i]
    for j, xo in enumerate((-2, 0, 2)):
        item_disp((cx + xo + .5, FY + 2.3, cz + 1 + .5), "minecraft:" + its[j], .45, qaxis(0, 1, 0, .4 * j))
    text_disp((cx + .5, FY + 5.3, cz + .5), json.dumps({"text": name, "color": "gold", "bold": True}), .9)

# (4) guide board in the info pavilion
guide = [{"text": "⚔ CHROMA ENDLESS ⚔\n", "color": "#FF8A3B", "bold": True},
         {"text": "Guide du joueur\n\n", "color": "gold"},
         {"text": "/f create <nom>", "color": "yellow"}, {"text": "  créer ta faction\n", "color": "white"},
         {"text": "/f join <nom>", "color": "yellow"}, {"text": "  rejoindre une faction\n", "color": "white"},
         {"text": "/f claim", "color": "yellow"}, {"text": "  protéger ton terrain\n", "color": "white"},
         {"text": "/kit depart  /kit quotidien", "color": "yellow"}, {"text": "  tes kits\n", "color": "white"},
         {"text": "/shop  /sell", "color": "yellow"}, {"text": "  acheter et vendre\n", "color": "white"},
         {"text": "/wild", "color": "yellow"}, {"text": "  partir à l'aventure\n", "color": "white"},
         {"text": "/sethome  /home  /spawn", "color": "yellow"}, {"text": "  se déplacer\n", "color": "white"},
         {"text": "/report <joueur>", "color": "yellow"}, {"text": "  signaler un tricheur", "color": "white"}]
text_disp((ix + .5, FY + 4.2, iz + .5), json.dumps(guide, ensure_ascii=False), 1.1, "vertical", width=260, bg=0x60000000)

# (5) robed statues with high collars, on pedestals, around the plaza
def statue(sx, sz, face_ang):
    for x in range(sx - 1, sx + 2):
        for z in range(sz - 1, sz + 2):
            setb(x, FY + 1, z, s("chiseled_quartz_block")); setb(x, FY + 2, z, s("smooth_quartz"))
    setb(sx, FY + 3, sz, s("smooth_quartz_slab", type="bottom"))
    base = (sx + .5, FY + 3.5, sz + .5)
    fq = qaxis(0, 1, 0, face_ang)
    def part(blk, size, c, q=IDQ, glow=False):
        display(base, blk, qmul(fq, q), size, qrot(fq, c), ("chroma",), view=2.5, glow=glow)
    for k, (w, y) in enumerate(((1.5, .4), (1.35, 1.2), (1.2, 2.0), (1.05, 2.7))):
        part("minecraft:white_concrete", (w, .8, w * .8), (0, y, 0))
    part("minecraft:gold_block", (1.55, .12, 1.25), (0, .05, 0))
    part("minecraft:gold_block", (1.1, .1, .9), (0, 3.05, 0))
    part("minecraft:red_concrete", (1.6, .3, .9), (0, 3.2, 0))
    part("minecraft:smooth_quartz", (.55, .6, .55), (0, 3.65, 0))
    part("minecraft:gold_block", (1.9, 1.5, .08), (0, 3.9, -.45), qaxis(1, 0, 0, -.25))
    part("minecraft:gold_block", (.08, 1.1, .7), (.95, 3.75, -.15), qaxis(0, 1, 0, -.5))
    part("minecraft:gold_block", (.08, 1.1, .7), (-.95, 3.75, -.15), qaxis(0, 1, 0, .5))
    part("minecraft:white_concrete", (.3, 1.2, .3), (.75, 2.5, .25), qaxis(1, 0, 0, .35))
    part("minecraft:white_concrete", (.3, 1.2, .3), (-.75, 2.5, .25), qaxis(1, 0, 0, .35))
    part("minecraft:gold_block", (.1, 4.4, .1), (1.05, 2.0, .45))
    part("minecraft:ochre_froglight", (.3, .3, .3), (1.05, 4.3, .45), qaxis(0, 1, 0, .78), glow=True)
for k in range(4):
    a = math.pi / 4 + k * math.pi / 2
    sx, sz = C + round(23.5 * math.cos(a)), C + round(23.5 * math.sin(a))
    statue(sx, sz, math.atan2(C - sx, C - sz))

# (6) flying buttresses around the dome base
nb = 0
for k in range(24):
    ang = k * math.pi / 12
    if k % 6 == 0: continue
    bx, bz = C + 93.5 * math.cos(ang), C + 93.5 * math.sin(ang)
    ix_, iz_ = int(bx), int(bz)
    fill(ix_, FY + 1, iz_, ix_, FY + 6, iz_, s("quartz_pillar", axis="y")); setb(ix_, FY + 7, iz_, GOLD); setb(ix_, FY + 8, iz_, s("end_rod", facing="up"))
    top_r = math.sqrt(DOME ** 2 - 30 ** 2) - .3
    p0 = (ix_ + .5, FY + 6.5, iz_ + .5)
    p1 = (C + .5 + top_r * math.cos(ang), FY + 30.0, C + .5 + top_r * math.sin(ang))
    v = (p1[0] - p0[0], p1[1] - p0[1], p1[2] - p0[2]); L = math.sqrt(sum(c * c for c in v))
    mid = (v[0] / 2, v[1] / 2, v[2] / 2)
    display(p0, "minecraft:smooth_quartz", qlook(v), (1.0, 1.0, L), mid, ("chroma",), view=4.0)
    display(p0, "minecraft:gold_block", qlook(v), (.3, 1.15, L * .98), mid, ("chroma",), view=4.0)
    nb += 1

# (7) pennants on the tallest spires
for (sx, sz), top in sorted(SPIRE_TOP.items(), key=lambda t: -t[1])[:20]:
    ang = math.atan2(sz - C, sx - C)
    pos = (sx + .5, top - 1.6, sz + .5)
    fq = qaxis(0, 1, 0, -ang)
    display(pos, "minecraft:red_concrete", fq, (1.8, .7, .05), qrot(fq, (1.0, 0, 0)), ("chroma",), view=4.0)
    display(pos, "minecraft:gold_block", fq, (1.8, .08, .06), qrot(fq, (1.0, .35, 0)), ("chroma",), view=4.0)

# (8) time-vortex rings above the blue box
vpos = (px + .5, FY + 13.0, pz + .5)
for j in range(6):
    ring_model((vpos[0], vpos[1] + j * 1.6, vpos[2]), 1.4 + j * .7, 14 + j * 3, .14,
               "minecraft:light_blue_stained_glass" if j % 2 else "minecraft:purple_stained_glass",
               qmul(qaxis(0, 1, 0, j * .5), qaxis(1, 0, 0, .25 + .08 * j)), ("chroma",), view=3.0, glow=True)
display(vpos, "minecraft:sea_lantern", qaxis(0, 1, 0, .78), (.6, .6, .6), (0, 4, 0), ("chroma",), view=3.0, glow=True)

# (9) chandeliers hanging from the dome on chains
nch = 0
for k in range(12):
    a = k * math.pi / 6 + math.pi / 12
    hd = 44.0
    x, z = round(C + hd * math.cos(a)), round(C + hd * math.sin(a))
    ytop = FY + int(dome_h(hd)) - 1
    ybot = ytop - 16
    if any((x, y, z) in blocks for y in range(ybot - 2, ytop - 1)): continue
    for y in range(ybot, ytop): setb(x, y, z, s("chain", axis="y"))
    setb(x, ybot - 1, z, LIGHT)
    cpos = (x + .5, ybot - .5, z + .5)
    ring_model(cpos, 1.8, 16, .14, "minecraft:gold_block", IDQ, ("chroma",), view=3.0, glow=True)
    for j in range(6):
        th = j * math.pi / 3
        display(cpos, "minecraft:ochre_froglight", IDQ, (.3, .3, .3), (1.8 * math.cos(th), .25, 1.8 * math.sin(th)), ("chroma",), view=3.0, glow=True)
    nch += 1

# (10) silver trees in free spots + rose bushes in the garden
def small_tree(tx, tz, h):
    fill(tx, FY + 1, tz, tx, FY + h, tz, s("pale_oak_log", axis="y"))
    for x in range(tx - 3, tx + 4):
        for y in range(FY + h - 2, FY + h + 3):
            for z in range(tz - 3, tz + 4):
                if math.hypot(x - tx, (y - FY - h) * 1.3, z - tz) <= 2.8 and (x, y, z) not in blocks:
                    setb(x, y, z, s("pale_oak_leaves", persistent="true"))
    for x, z in ring_cells(tx, tz, .5, 1.5):
        if (x, FY + 1, z) not in blocks: setb(x, FY + 1, z, s("moss_carpet"))
ntree = 0
for _, tx, tz in sorted((rnd(x, 55, z), x, z) for x in range(8, W - 8, 3) for z in range(8, W - 8, 3)):
    if ntree >= 45: break
    d = dist(tx, tz)
    if not (20 < d < 84) or on_spoke(tx, tz, AV + 4) or is_road(tx, tz) or dome_h(d + 4) < 14: continue
    if any(dist(tx, tz, fx, fz) < fr + 2 for (fx, fz), fr in FEATURES): continue
    if not air_box(tx - 3, tz - 3, tx + 3, tz + 3, FY + 1, FY + 10): continue
    small_tree(tx, tz, 5 + int(rnd(tx, 6, tz) * 3)); ntree += 1
for x, z in ring_cells(gx, gz, 13, 15.5):
    if (x, FY + 1, z) not in blocks and (x, FY + 2, z) not in blocks and get(x, FY, z) in (s("grass_block"), s("moss_block")) and rnd(x, 21, z) < .3:
        flower = "rose_bush" if rnd(x, 22, z) < .5 else "peony" if rnd(x, 23, z) < .5 else "lilac"
        setb(x, FY + 1, z, s(flower, half="lower")); setb(x, FY + 2, z, s(flower, half="upper"))
print("lights", nl, "buttresses", nb, "chandeliers", nch, "trees", ntree)

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
    kind = e.get("kind", "block")
    if kind == "block":
        head = [tag(8, "id", nstr("minecraft:block_display")), tag(10, "block_state", comp([tag(8, "Name", nstr(e["block"]))]))]
    elif kind == "item":
        head = [tag(8, "id", nstr("minecraft:item_display")), tag(10, "item", comp([tag(8, "id", nstr(e["item"])), tag(3, "count", struct.pack(">i", 1))])),
                tag(8, "item_display", nstr("fixed"))]
    else:
        head = [tag(8, "id", nstr("minecraft:text_display")), tag(8, "text", nstr(e["text"])), tag(8, "billboard", nstr(e["billboard"])),
                tag(3, "line_width", struct.pack(">i", e["width"])), tag(3, "background", struct.pack(">i", e["bg"] - (1 << 32) if e["bg"] >= (1 << 31) else e["bg"])),
                tag(1, "shadow", b"\x01")]
    nbt = head + [
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
open(os.path.join(OUT, "citadel_xxl2.nbt"), "wb").write(data)

def world(x, y, z): return [x + ORIGIN[0], y + ORIGIN[1], z + ORIGIN[2]]
info = {"market": world(MARKET[0], FY, MARKET[1]), "info": world(INFO[0], FY, INFO[1]), "garden": world(GARDEN[0], FY, GARDEN[1]),
        "portal": world(PORTAL[0], FY, PORTAL[1]), "houses": len(houses), "spires": len(spires), "shrines": shrines, "columns": len(cols),
        "bridges": bridges, "entities": len(entities), "blocks": len(blocks)}
json.dump(info, open(os.path.join(OUT, "citadel_xxl2.json"), "w"))

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
open(os.path.join(OUT, "citadel_xxl2_top.png"), "wb").write(png(top))
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
open(os.path.join(OUT, "citadel_xxl2_side.png"), "wb").write(png(side))
print(json.dumps(info), "palette", len(pal), "nbt", len(data))

# ---- dump positions of pennants / chandeliers / buttresses (world coords)
def W_(p): return [p[0] + ORIGIN[0], p[1] + ORIGIN[1], p[2] + ORIGIN[2]]
pos_dump = {"pennants": [], "chandeliers": [], "buttresses": []}
for (sx, sz), top in sorted(SPIRE_TOP.items(), key=lambda t: -t[1])[:20]:
    pos_dump["pennants"].append({"p": W_((sx + .5, top - 1.6, sz + .5)), "ang": math.atan2(sz - C, sx - C)})
for k in range(12):
    a = k * math.pi / 6 + math.pi / 12; hd = 44.0
    x, z = round(C + hd * math.cos(a)), round(C + hd * math.sin(a))
    ytop = FY + int(dome_h(hd)) - 1; ybot = ytop - 16
    if (x, ybot - 1, z) in blocks and blocks[(x, ybot - 1, z)] == LIGHT:
        pos_dump["chandeliers"].append(W_((x + .5, ybot - .5, z + .5)))
for k in range(24):
    if k % 6 == 0: continue
    ang = k * math.pi / 12
    ix_, iz_ = int(C + 93.5 * math.cos(ang)), int(C + 93.5 * math.sin(ang))
    top_r = math.sqrt(DOME ** 2 - 30 ** 2) - .3
    p0 = (ix_ + .5, FY + 6.5, iz_ + .5); p1 = (C + .5 + top_r * math.cos(ang), FY + 30.0, C + .5 + top_r * math.sin(ang))
    pos_dump["buttresses"].append({"p0": W_(p0), "p1": W_(p1)})
json.dump(pos_dump, open(os.path.join(OUT, "deco_positions.json"), "w"))
print("dump", {k: len(v) for k, v in pos_dump.items()})

# ================================================================= DETAILS PASS 3 (additive structure: only new blocks)
extra = {}
def add(x, y, z, st, force=False):
    if not (0 <= x < W and 0 <= y < H and 0 <= z < W): return False
    if not force and ((x, y, z) in blocks or (x, y, z) in extra): return False
    extra[(x, y, z)] = st; return True
def free(x, y, z): return (x, y, z) not in blocks and (x, y, z) not in extra
cnt = {}
def inc(k): cnt[k] = cnt.get(k, 0) + 1
# 1) doors on every house
for hx, hz, kind in houses:
    dx, dz = C - hx, C - hz
    door = (1 if dx > 0 else -1, 0) if abs(dx) >= abs(dz) else (0, 1 if dz > 0 else -1)
    ddx, ddz = hx + door[0] * 3, hz + door[1] * 3
    if free(ddx, FY + 1, ddz) and free(ddx, FY + 2, ddz):
        f = OUTF[door]
        add(ddx, FY + 1, ddz, s("birch_door", facing=f, half="lower", hinge="left", open="false", powered="false"))
        add(ddx, FY + 2, ddz, s("birch_door", facing=f, half="upper", hinge="left", open="false", powered="false")); inc("doors")
# 2) wall banners on arcade columns, facing the avenue
for (ox, oz) in OUTF:
    for side in (AV + 3, -(AV + 3)):
        p_ = (0, side) if ox != 0 else (side, 0)
        toward = (0, -1 if side > 0 else 1) if ox != 0 else (-1 if side > 0 else 1, 0)
        for i, t in enumerate(range(24, int(DOME) - 3, 4)):
            x, z = C + ox * t + p_[0], C + oz * t + p_[1]
            if blocks.get((x, FY + 3, z)) != s("quartz_pillar", axis="y"): continue
            bx, bz = x + toward[0], z + toward[1]
            if free(bx, FY + 3, bz) and free(bx, FY + 2, bz):
                add(bx, FY + 3, bz, s("red_wall_banner" if i % 2 == 0 else "orange_wall_banner", facing=OUTF[toward])); inc("banners")
# 3) fountains where avenues cross the outer boulevard
for (ox, oz) in OUTF:
    fx, fz = C + ox * 62, C + oz * 62
    for x, z in ring_cells(fx, fz, -1, 2.6):
        dd = dist(x, z, fx, fz)
        if dd > 1.8:
            add(x, FY + 1, z, s("smooth_quartz_slab", type="bottom"), force=True)
        else:
            add(x, FY, z, s("water"), force=True); add(x, FY - 1, z, s("sea_lantern"), force=True)
    add(fx, FY, fz, s("smooth_quartz"), force=True)
    for y in (FY + 1, FY + 2): add(fx, y, fz, s("quartz_pillar", axis="y"), force=True)
    add(fx, FY + 3, fz, GOLD, force=True); add(fx, FY + 4, fz, s("lantern"), force=True); inc("fountains")
# 4) lamps and benches along both ring roads
for rr_, step in ((28.0, 10), (62.0, 6)):
    for a10 in range(0, 360, step):
        a = math.radians(a10 + step / 2)
        for side, kind in ((2.4, "lamp"), (-2.4, "bench")):
            x, z = round(C + (rr_ + side) * math.cos(a)), round(C + (rr_ + side) * math.sin(a))
            if on_spoke(x, z, AV + 1) or not free(x, FY + 1, z) or not free(x, FY + 2, z): continue
            if kind == "lamp":
                if all(free(x, y, z) for y in range(FY + 1, FY + 5)):
                    for y in range(FY + 1, FY + 4): add(x, y, z, s("quartz_pillar", axis="y"))
                    add(x, FY + 4, z, s("lantern")); inc("lamps")
            else:
                add(x, FY + 1, z, s("birch_stairs", facing=facing_out(x - C, z - C), half="bottom")); inc("benches")
# 5) market clutter around the stalls
props = ["barrel[facing=up]", "hay_block[axis=y]", "pumpkin", "melon", "barrel[facing=up]", "chest[facing=north]", "hay_block[axis=x]", "carved_pumpkin[facing=south]"]
for k in range(28):
    a = k * 2 * math.pi / 28
    x, z = round(mx + 13 * math.cos(a)), round(mz + 13 * math.sin(a))
    if is_road(x, z) or not free(x, FY + 1, z): continue
    p = props[k % len(props)]; name, _, rest = p.partition("[")
    st = "minecraft:" + name + ("[" + rest if rest else "")
    add(x, FY + 1, z, st)
    if k % 3 == 0 and free(x, FY + 2, z): add(x, FY + 2, z, s("barrel", facing="up") if k % 2 else s("hay_block", axis="y"))
    inc("props")
# 6) tower ground floor: red carpet ring + bookshelves along the wall
for x, z in ring_cells(C, C, 5.5, 8.0):
    if free(x, FY + 1, z) and blocks.get((x, FY, z)) is not None: add(x, FY + 1, z, s("red_carpet")); inc("carpet")
for x, z in ring_cells(C, C, 11.0, 12.45):
    if abs(x - C) <= 1 or abs(z - C) <= 1: continue
    for y in (FY + 1, FY + 2):
        if free(x, y, z): add(x, y, z, s("bookshelf")); inc("shelves")
# 7) garden hedges along the inner path ring
for x, z in ring_cells(gx, gz, 9.2, 10.2):
    if on_spoke(x, z, AV + 3) or is_road(x, z): continue
    if free(x, FY + 1, z) and rnd(x, 31, z) < .8: add(x, FY + 1, z, s("azalea_leaves", persistent="true") if (x + z) % 3 else s("flowering_azalea_leaves", persistent="true")); inc("hedge")

def write_struct(dct, path):
    pal_, pidx_, bl_ = [], {}, []
    for (x, y, z), st in sorted(dct.items()):
        if st not in pidx_: pidx_[st] = len(pal_); pal_.append(st)
        bl_.append(comp([tag(9, "pos", ilist([x, y, z])), tag(3, "state", struct.pack(">i", pidx_[st]))]))
    root_ = comp([tag(3, "DataVersion", struct.pack(">i", DATA_VERSION)), tag(9, "size", ilist([W, H, W])),
                  tag(9, "palette", bytes([10]) + struct.pack(">i", len(pal_)) + b"".join(pe(p) for p in pal_)),
                  tag(9, "blocks", bytes([10]) + struct.pack(">i", len(bl_)) + b"".join(bl_)),
                  tag(9, "entities", bytes([0]) + struct.pack(">i", 0))])
    open(path, "wb").write(gzip.compress(tag(10, "", root_), 6))
write_struct(extra, os.path.join(OUT, "citadel_details3.nbt"))
# urn positions (world) flanking the four avenue entrances of the plaza
urns = []
for (ox, oz) in OUTF:
    for side in (7.5, -7.5):
        x = C + ox * 19 + (side if ox == 0 else 0); z = C + oz * 19 + (side if oz == 0 else 0)
        urns.append([x + .5 + ORIGIN[0], FY + 1 + ORIGIN[1], z + .5 + ORIGIN[2]])
json.dump({"urns": urns}, open(os.path.join(OUT, "details3.json"), "w"))
print("details", cnt, "blocks", len(extra))

# ================================================================= DETAILS PASS 4 (additive)
ex4 = {}
def free4(x, y, z): return (x, y, z) not in blocks and (x, y, z) not in extra and (x, y, z) not in ex4
def add4(x, y, z, st, force=False):
    if not (0 <= x < W and 0 <= y < H and 0 <= z < W): return False
    if not force and not free4(x, y, z): return False
    ex4[(x, y, z)] = st; return True
c4 = {}
def inc4(k): c4[k] = c4.get(k, 0) + 1
CARPETS = ["red_carpet", "orange_carpet", "yellow_carpet", "white_carpet", "light_gray_carpet"]
# A) tower interior furnishing on every tier floor
for ti, (rr, y0, y1) in enumerate(tiers):
    if y0 == 0: continue
    fy = FY + y0
    for x, z in ring_cells(C, C, 1.6, rr - 1.0):
        d = dist(x, z)
        if blocks.get((x, fy, z)) is None or not free4(x, fy + 1, z): continue
        if rr - 2.0 < d <= rr - 1.0 and not (abs(x - C) <= 1 and z > C):          # shelves along the wall, door gap south
            for y in (fy + 1, fy + 2):
                if free4(x, y, z): add4(x, y, z, s("bookshelf")); inc4("shelves")
        elif 3.0 < d <= 4.4:
            add4(x, fy + 1, z, s(CARPETS[ti % len(CARPETS)])); inc4("carpet")
    for k in range(4):
        a = math.pi / 4 + k * math.pi / 2
        x, z = C + round((rr - 3) * math.cos(a)), C + round((rr - 3) * math.sin(a))
        ytop = FY + y1 - 1
        if free4(x, ytop, z) and (x, ytop + 1, z) in blocks or free4(x, ytop, z):
            add4(x, ytop, z, s("lantern", hanging="true")); inc4("lanterns")
    if ti == len(tiers) - 3:
        add4(C + 3, fy + 1, C, s("enchanting_table")); add4(C - 3, fy + 1, C, s("lectern", facing="east")); add4(C, fy + 1, C - 3, s("lectern", facing="south"))
# B) circular canal just outside the outer boulevard
for x, z in ring_cells(C, C, 64.6, 66.4):
    if on_spoke(x, z, AV + 1): continue
    d = dist(x, z)
    if blocks.get((x, FY + 1, z)) is not None or (x, FY + 1, z) in extra: continue
    if 65.1 < d <= 65.9:
        add4(x, FY, z, s("water"), force=True); add4(x, FY - 1, z, s("water"), force=True); add4(x, FY - 2, z, s("prismarine_bricks"), force=True); inc4("canal")
    else:
        add4(x, FY, z, s("smooth_quartz"), force=True)
        if free4(x, FY + 1, z): add4(x, FY + 1, z, s("smooth_quartz_slab", type="bottom"))
# C) compass-rose medallions inlaid in the avenues
for (ox, oz) in OUTF:
    for t in (42, 76):
        mx_, mz_ = C + ox * t, C + oz * t
        for x, z in ring_cells(mx_, mz_, -1, 4.2):
            if not on_spoke(x, z, AV - 1): continue
            d = dist(x, z, mx_, mz_); a = math.degrees(math.atan2(z - mz_, x - mx_)) % 90
            st = None
            if abs(d - 3.6) < .55: st = GOLD
            elif d < 3.2 and (a < 6 or a > 84): st = s("light_gray_concrete")
            elif d < 2.2 and 40 < a < 50: st = s("yellow_terracotta")
            elif d < .8: st = LIGHT
            if st: add4(x, FY, z, st, force=True); inc4("mosaic")
# D) flower beds around spire bases
FL = ["white_tulip", "lily_of_the_valley", "azure_bluet", "oxeye_daisy", "pink_tulip", "cornflower"]
for sx, sz, r, h in spires:
    for x, z in ring_cells(sx, sz, r + 2.6, r + 3.6):
        if on_spoke(x, z, AV + 1) or is_road(x, z) or not free4(x, FY + 1, z) or blocks.get((x, FY, z)) in (None, s("water")): continue
        if rnd(x, 41, z) < .55:
            add4(x, FY, z, s("grass_block"), force=True)
            add4(x, FY + 1, z, s(FL[int(rnd(x, 42, z) * len(FL))]) if rnd(x, 43, z) < .7 else s("azalea_leaves", persistent="true")); inc4("flowers")
# E) beds and a rug inside every house
for hx, hz, kind in houses:
    if free4(hx - 2, FY + 1, hz) and free4(hx - 2, FY + 1, hz - 1):
        add4(hx - 2, FY + 1, hz, s("red_bed", facing="north", part="foot", occupied="false"))
        add4(hx - 2, FY + 1, hz - 1, s("red_bed", facing="north", part="head", occupied="false")); inc4("beds")
    for x in (hx, hx + 1):
        for z in (hz - 1, hz - 2):
            if free4(x, FY + 1, z) and blocks.get((x, FY, z)) is not None: add4(x, FY + 1, z, s("orange_carpet"))
# F) pedestals for gate statues (models summoned separately)
gate_statues = []
for (ox, oz) in OUTF:
    for side in (8, -8):
        x = C + ox * 82 + (side if ox == 0 else 0); z = C + oz * 82 + (side if oz == 0 else 0)
        for px2 in range(x - 1, x + 2):
            for pz2 in range(z - 1, z + 2):
                add4(px2, FY + 1, pz2, s("chiseled_quartz_block"), force=True); add4(px2, FY + 2, pz2, s("smooth_quartz"), force=True)
        add4(x, FY + 3, z, s("smooth_quartz_slab", type="bottom"), force=True)
        gate_statues.append([x + .5 + ORIGIN[0], FY + 3.5 + ORIGIN[1], z + .5 + ORIGIN[2], -ox, -oz])
# I) pale hanging moss under the sky bridges
for (x, y, z), st in list(blocks.items()):
    if False:
        add4(x, y - 1, z, s("pale_hanging_moss", tip="true")); inc4("moss")
write_struct(ex4, os.path.join(OUT, "citadel_details4.nbt"))
# world positions for entities of this pass
holo = [[C + ox * 62 + .5 + ORIGIN[0], FY + 9.5 + ORIGIN[1], C + oz * 62 + .5 + ORIGIN[2]] for (ox, oz) in OUTF]
signs = []
NAMES = {(0, -1): "Avenue du Nord", (0, 1): "Avenue du Sud", (1, 0): "Avenue de l'Est", (-1, 0): "Avenue de l'Ouest"}
for (ox, oz), nm in NAMES.items():
    for rr_, bn in ((28, "Boulevard des Arches"), (62, "Boulevard des Étoiles")):
        x = C + ox * (rr_ + 3) + (6.5 if ox == 0 else 0); z = C + oz * (rr_ + 3) + (6.5 if oz == 0 else 0)
        signs.append([x + .5 + ORIGIN[0], FY + 4.2 + ORIGIN[1], z + .5 + ORIGIN[2], nm, bn])
json.dump({"gate_statues": gate_statues, "holo": holo, "signs": signs}, open(os.path.join(OUT, "details4.json"), "w"), ensure_ascii=False)
print("details4", c4, "blocks", len(ex4))

# ================================================================= DETAILS PASS 5 (additive, may include explicit air)
ex5 = {}
def occ5(x, y, z): return (x, y, z) in blocks or (x, y, z) in extra or (x, y, z) in ex4 or (x, y, z) in ex5
def add5(x, y, z, st, force=False):
    if not (0 <= x < W and 0 <= y < H and 0 <= z < W): return False
    if not force and occ5(x, y, z): return False
    ex5[(x, y, z)] = st; return True
c5 = {}
def inc5(k): c5[k] = c5.get(k, 0) + 1
# A) golden beacon beam from the tower top through the dome
for y in range(FY + 72, FY + 80): add5(C, y, C, AIR, force=True)
for (ox, oz) in OUTF:
    for y in (FY + 77,): add5(C + ox, y, C + oz, AIR, force=True)
for x in range(C - 1, C + 2):
    for z in range(C - 1, C + 2): add5(x, FY + 72, z, GOLD, force=True)
add5(C, FY + 73, C, s("beacon"), force=True)
for y in range(FY + 84, H):
    if (C, y, C) in blocks: add5(C, y, C, s("yellow_stained_glass"), force=True); inc5("cap")
inc5("beacon")
# B) blue-flame braziers between the pool and the colonnade
for k in range(8):
    a = math.pi / 8 + k * math.pi / 4
    x, z = C + round(19.6 * math.cos(a)), C + round(19.6 * math.sin(a))
    if occ5(x, FY + 1, z): continue
    add5(x, FY + 1, z, s("chiseled_quartz_block")); add5(x, FY + 2, z, s("quartz_pillar", axis="y")); add5(x, FY + 3, z, GOLD)
    add5(x, FY + 4, z, s("soul_campfire", facing="north", lit="true", signal_fire="false", waterlogged="false")); inc5("braziers")
# C) smoking chimneys on a third of the domed houses
for hx, hz, kind in houses:
    if kind != 0 or rnd(hx, 61, hz) > .4: continue
    cx_, cz_ = hx + 2, hz - 2
    if any(occ5(cx_, y, cz_) and blocks.get((cx_, y, cz_)) not in (GOLD, s("smooth_quartz")) for y in range(FY + 6, FY + 10)): pass
    for y in range(FY + 5, FY + 9): add5(cx_, y, cz_, s("bricks"), force=True)
    add5(cx_, FY + 9, cz_, s("campfire", facing="north", lit="true", signal_fire="false", waterlogged="false"), force=True)
    add5(cx_, FY + 10, cz_, AIR, force=True); inc5("chimneys")
# H) banners hanging on the outer wall of every tower tier (except the south door side)
for ti, (rr, y0, y1) in enumerate(tiers):
    if y0 == 0 or y1 - y0 < 5: continue
    for (ox, oz) in ((1, 0), (-1, 0), (0, -1)):
        for w in (-2, 2):
            wx = C + ox * int(rr) + (w if ox == 0 else 0); wz = C + oz * int(rr) + (w if oz == 0 else 0)
            bx, bz = wx + ox, wz + oz
            if blocks.get((wx, FY + y0 + 3, wz)) is None: continue
            if add5(bx, FY + y0 + 3, bz, s("red_wall_banner" if (ti + w) % 4 else "orange_wall_banner", facing=OUTF[(ox, oz)])): inc5("tower_banners")
# D) red Gallifreyan trees outside the dome, between the buttresses
for k in range(24):
    if k % 6 == 0: continue
    a = (k + .5) * math.pi / 12
    tx, tz = C + round(92 * math.cos(a)), C + round(92 * math.sin(a))
    if occ5(tx, FY + 1, tz): continue
    h = 5 + int(rnd(tx, 71, tz) * 3)
    for y in range(FY + 1, FY + h + 1): add5(tx, y, tz, s("crimson_stem", axis="y"))
    for x in range(tx - 3, tx + 4):
        for y in range(FY + h - 1, FY + h + 3):
            for z in range(tz - 3, tz + 4):
                dd = math.hypot(x - tx, (y - FY - h) * 1.4, z - tz)
                if dd <= 2.9 and dist(x, z) > DOME + .9 and not occ5(x, y, z):
                    add5(x, y, z, s("shroomlight") if rnd(x, y, z) < .08 else s("nether_wart_block"))
    inc5("red_trees")
write_struct(ex5, os.path.join(OUT, "citadel_details5.nbt"))
plates = []
for i, (hx, hz, kind) in enumerate(sorted(houses, key=lambda t: (round(math.degrees(math.atan2(t[1] - C, t[0] - C))) % 360, dist(t[0], t[1])))):
    dx, dz = C - hx, C - hz
    door = (1 if dx > 0 else -1, 0) if abs(dx) >= abs(dz) else (0, 1 if dz > 0 else -1)
    px_, pz_ = hx + door[0] * 3.62, hz + door[1] * 3.62
    plates.append([px_ + .5 + ORIGIN[0], FY + 3.6 + ORIGIN[1], pz_ + .5 + ORIGIN[2], i + 1, math.degrees(math.atan2(-door[0], door[1]))])
json.dump({"plates": plates}, open(os.path.join(OUT, "details5.json"), "w"))
print("details5", c5, "blocks", len(ex5))
