"""Citadel-under-a-dome spawn for Chroma Endless -> vanilla structure .nbt + preview."""
import gzip, math, os, random, struct, sys, zlib

OUT = sys.argv[1]
R = 40; W = 2 * R + 1; C = R
FY = 8                      # floor index (world y 64 when origin y = 56)
DOME = 38.0
H = FY + int(DOME) + 4      # 50
DATA_VERSION = 4189

blocks = {}
def s(name, **p):
    return "minecraft:%s[%s]" % (name, ",".join("%s=%s" % kv for kv in sorted(p.items()))) if p else "minecraft:" + name
AIR = s("air")
def setb(x, y, z, st):
    if 0 <= x < W and 0 <= y < H and 0 <= z < W:
        blocks[(x, y, z)] = st
def get(x, y, z):
    return blocks.get((x, y, z), AIR)
def fill(x1, y1, z1, x2, y2, z2, st):
    for x in range(min(x1, x2), max(x1, x2) + 1):
        for y in range(min(y1, y2), max(y1, y2) + 1):
            for z in range(min(z1, z2), max(z1, z2) + 1):
                setb(x, y, z, st)
def dist(x, z, cx=C, cz=C):
    return math.hypot(x - cx, z - cz)
def rnd(*k):
    return random.Random(hash(k) & 0xffffffff).random()
def mix(x, y, z, ch):
    r = rnd(x, y, z); a = 0
    for st, w in ch:
        a += w
        if r < a:
            return st
    return ch[-1][0]
def on_spoke(x, z, half=3):
    return abs(x - C) <= half or abs(z - C) <= half

WHITE = [(s("smooth_quartz"), .45), (s("white_concrete"), .3), (s("calcite"), .25)]
FLOOR = [(s("smooth_quartz"), .55), (s("polished_diorite"), .3), (s("calcite"), .15)]
RED = [(s("crimson_nylium"), .45), (s("red_terracotta"), .25), (s("orange_terracotta"), .15), (s("terracotta"), .15)]
GOLD = s("gold_block")
WIN = s("yellow_stained_glass")

# ------------------------------------------------------------------ base volume
for x in range(W):
    for z in range(W):
        if dist(x, z) > R + .5:
            continue
        for y in range(H):
            if y < FY - 2: st = s("stone")
            elif y < FY: st = s("dirt")
            elif y == FY: st = mix(x, y, z, RED)
            else: st = AIR
            blocks[(x, y, z)] = st

# ------------------------------------------------------------------ plaza floor inside the dome
for x in range(W):
    for z in range(W):
        d = dist(x, z); dx, dz = x - C, z - C
        if d > DOME - .5:
            continue
        st = mix(x, FY, z, FLOOR)
        # concentric "circular script" rings
        for rr in (11.0, 16.5, 22.0, 33.0):
            if abs(d - rr) < .55:
                st = s("light_gray_concrete")
        if abs(d - 16.5) < .55 and (round(math.degrees(math.atan2(dz, dx))) % 30 == 0):
            st = s("ochre_froglight")
        # radial strokes between the inner rings, with gold nodes
        ang = math.degrees(math.atan2(dz, dx)) % 30
        if 11 < d < 22 and (ang < 1.6 or ang > 28.4):
            st = s("light_gray_concrete")
        if abs(d - 27.5) < .5 and (math.degrees(math.atan2(dz, dx)) % 10) < 1.2:
            st = s("light_gray_concrete")
        # small circles on ring 33
        for k in range(8):
            a = k * math.pi / 4 + math.pi / 8
            cx, cz = C + 33 * math.cos(a), C + 33 * math.sin(a)
            if abs(dist(x, z, cx, cz) - 1.8) < .45:
                st = s("light_gray_concrete")
            if dist(x, z, cx, cz) < .6:
                st = s("ochre_froglight")
        # small tangent circles on ring 22
        for k in range(6):
            a = k * math.pi / 3 + math.pi / 6
            cx, cz = C + 22 * math.cos(a), C + 22 * math.sin(a)
            if abs(dist(x, z, cx, cz) - 2.5) < .5:
                st = s("light_gray_concrete")
            if dist(x, z, cx, cz) < .8:
                st = GOLD
        # spokes
        if on_spoke(x, z) and d > 8.5:
            half = dx if abs(dz) > abs(dx) else dz
            if abs(half) == 3: st = s("light_gray_concrete")
            elif half == 0: st = GOLD if (abs(dx) + abs(dz)) % 6 == 0 else s("yellow_terracotta")
            else: st = s("white_concrete")
        setb(x, FY, z, st)

# ------------------------------------------------------------------ dome
for x in range(W):
    for z in range(W):
        for y in range(FY, H):
            r3 = math.sqrt((x - C) ** 2 + (z - C) ** 2 + ((y - FY) * 1.0) ** 2)
            if DOME - .5 <= r3 < DOME + .6:
                ang30 = math.degrees(math.atan2(z - C, x - C)) % 30
                ang15 = ang30 % 15
                lat = math.degrees(math.asin(min(1, (y - FY) / DOME)))
                major = ang30 < 1.4 or ang30 > 28.6
                minor = (ang15 < .8 or ang15 > 14.2) and lat < 70
                bands = {15: s("smooth_quartz"), 30: s("smooth_quartz"), 45: GOLD, 60: s("smooth_quartz"), 74: GOLD}
                band = next((st_ for L, st_ in bands.items() if abs(lat - L) < (1.4 if L > 60 else 1.0)), None)
                if y <= FY + 2:
                    st = s("smooth_quartz") if y < FY + 2 else GOLD
                elif band:
                    st = band
                elif major:
                    st = s("smooth_quartz")
                elif minor:
                    st = s("calcite")
                else:
                    st = s("glass") if lat < 45 else s("white_stained_glass") if (x + y + z) % 7 == 0 else s("glass")
                if lat > 84:
                    st = GOLD
                # gates
                if on_spoke(x, z, 3) and y <= FY + 6:
                    st = AIR
                    if y == FY + 6 or (on_spoke(x, z, 3) and not on_spoke(x, z, 2) and y >= FY + 1):
                        st = s("quartz_pillar", axis="y") if y < FY + 6 else GOLD
                setb(x, y, z, st)
# gate floors through the rim + lintel lights
for ox, oz in ((0, 1), (0, -1), (1, 0), (-1, 0)):
    for t in range(int(DOME) - 1, R + 1):
        for w in range(-3, 4):
            x = C + ox * t + (w if ox == 0 else 0); z = C + oz * t + (w if oz == 0 else 0)
            setb(x, FY, z, s("white_concrete") if abs(w) < 3 else s("light_gray_concrete"))
    gx, gz = C + ox * int(DOME), C + oz * int(DOME)
    setb(gx, FY + 5, gz, s("lantern", hanging="true"))

# ------------------------------------------------------------------ central panopticon tower + pool
for x in range(W):
    for z in range(W):
        d = dist(x, z)
        if d <= 8.5:
            if d > 7.5:
                setb(x, FY, z, s("smooth_quartz")); setb(x, FY + 1, z, s("smooth_quartz_slab", type="bottom"))
            elif d > 6.5:
                setb(x, FY, z, s("water")); setb(x, FY - 1, z, s("water")); setb(x, FY - 2, z, s("sea_lantern"))
tiers = [(6.5, 0, 6), (5.5, 6, 12), (4.5, 12, 18), (3.5, 18, 24), (2.5, 24, 29), (1.5, 29, 33)]
for (rr, y0, y1) in tiers:
    for x in range(C - 7, C + 8):
        for z in range(C - 7, C + 8):
            d = dist(x, z)
            if d <= rr:
                for y in range(FY + y0, FY + y1):
                    edge = d > rr - 1
                    if edge:
                        st = s("smooth_quartz")
                        if (y - FY) % 6 in (2, 3) and (x - C) % 2 == 0 and (z - C) % 2 == 0:
                            st = WIN
                        if y == FY + y1 - 1:
                            st = GOLD
                    else:
                        st = s("ochre_froglight") if y == FY + y0 else AIR
                    setb(x, y, z, st)
    # balcony ring
    for x in range(C - 8, C + 9):
        for z in range(C - 8, C + 9):
            d = dist(x, z)
            if rr <= d < rr + 1 and y1 < 30:
                setb(x, FY + y1, z, s("smooth_quartz_slab", type="bottom"))
fill(C, FY + 33, C, C, FY + 36, C, s("quartz_pillar", axis="y"))
setb(C, FY + 37, C, s("end_rod", facing="up"))
for ox, oz, f in ((1, 0, "east"), (-1, 0, "west"), (0, 1, "south"), (0, -1, "north")):
    setb(C + ox, FY + 35, C + oz, s("end_rod", facing=f))
# entrance to tower on the south side
fill(C - 1, FY + 1, C + 6, C + 1, FY + 3, C + 6, AIR)
fill(C - 1, FY + 1, C + 5, C + 1, FY + 3, C + 5, AIR)

# ------------------------------------------------------------------ spires
FEATURES = [((C + 15, C - 16), 9.5), ((C - 15, C - 15), 8.0), ((C + 18, C + 18), 9.5), ((C - 17, C + 17), 7.0)]
PLACED = []
def free(px, pz, r):
    if on_spoke(px, pz, 4 + int(r)):
        return False
    if any(dist(px, pz, qx, qz) < r + qr + 3 for qx, qz, qr in PLACED):
        return False
    return all(dist(px, pz, fx, fz) > fr + r for (fx, fz), fr in FEATURES)

OUTF = {(1, 0): "east", (-1, 0): "west", (0, 1): "south", (0, -1): "north"}
INF = {"east": "west", "west": "east", "south": "north", "north": "south"}

def ring_cells(px, pz, rr_in, rr_out):
    for x in range(px - int(rr_out) - 1, px + int(rr_out) + 2):
        for z in range(pz - int(rr_out) - 1, pz + int(rr_out) + 2):
            d = dist(x, z, px, pz)
            if rr_in < d <= rr_out:
                yield x, z

def spire(px, pz, r, h):
    # plinth: stepped base ring
    for x, z in ring_cells(px, pz, r + .5, r + 1.5):
        dx, dz = x - px, z - pz
        f = OUTF[(1 if dx > 0 else -1, 0)] if abs(dx) >= abs(dz) else OUTF[(0, 1 if dz > 0 else -1)]
        setb(x, FY + 1, z, s("smooth_quartz_stairs", facing=INF[f], half="bottom"))
    # sections that narrow upwards
    nsec = 3 if (r >= 2 and h >= 15) else 2 if h >= 10 else 1
    bounds = [FY + 1 + round(h * k / nsec) for k in range(nsec + 1)]
    cur_r = r
    for si in range(nsec):
        y0, y1 = bounds[si], bounds[si + 1]
        for x in range(px - cur_r - 1, px + cur_r + 2):
            for z in range(pz - cur_r - 1, pz + cur_r + 2):
                d = dist(x, z, px, pz)
                if d > cur_r + .5:
                    continue
                for y in range(y0, y1):
                    if d > cur_r - .5:
                        st = mix(x, y, z, WHITE)
                        axis = (x - px) == 0 or (z - pz) == 0
                        diag = abs(x - px) == abs(z - pz)
                        if (axis or (diag and cur_r >= 2)) and (y - y0) % 4 in (1, 2) and y1 - y > 1:
                            st = WIN
                        if y == y1 - 1:
                            st = GOLD
                    else:
                        st = s("ochre_froglight") if (y - FY) % 8 == 1 else AIR
                    setb(x, y, z, st)
        # balcony + end-rod lamps at section joint
        if si < nsec - 1:
            for x, z in ring_cells(px, pz, cur_r + .5, cur_r + 1.4):
                if get(x, y1 - 1, z) == AIR:
                    setb(x, y1 - 1, z, s("smooth_quartz_slab", type="top"))
            for (ox, oz) in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                setb(px + ox * (cur_r + 1), y1, pz + oz * (cur_r + 1), s("end_rod", facing="up"))
        if si == 0 and h >= 10:
            # buttress fins on the first section
            fh = max(3, (y1 - y0) * 3 // 4)
            for (ox, oz) in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                for k in (1, 2):
                    top_f = y0 + fh - (k - 1) * 2
                    fx, fz = px + ox * (cur_r + k), pz + oz * (cur_r + k)
                    fill(fx, FY + 1, fz, fx, top_f - 1, fz, s("quartz_pillar", axis="y"))
                    setb(fx, top_f, fz, s("smooth_quartz_stairs", facing=INF[OUTF[(ox, oz)]], half="bottom"))
        if cur_r > 1 and si < nsec - 1:
            cur_r -= 1
    # cone roof with alternating gold rings
    top = bounds[-1]
    rr = cur_r + .5; i = 0
    while rr > 0.4:
        for x in range(px - cur_r - 1, px + cur_r + 2):
            for z in range(pz - cur_r - 1, pz + cur_r + 2):
                if dist(x, z, px, pz) <= rr:
                    setb(x, top + i, z, GOLD if i % 3 == 2 else s("smooth_quartz"))
        rr -= .6 if cur_r >= 2 else .9; i += 1
    for (ox, oz), f in OUTF.items():
        setb(px + ox, top + i - 1, pz + oz, s("end_rod", facing=f))
    fill(px, top + i, pz, px, top + i + 1, pz, s("lightning_rod"))
    setb(px, top + i + 2, pz, s("end_rod", facing="up"))
    return top + i + 2

spires = []
for ring_r, count, base_r, maxh in ((26, 32, 2, 26), (15, 12, 1, 18), (20.5, 20, 1, 22), (32, 36, 1, 17)):
    for k in range(count):
        a = (k + .5) * 2 * math.pi / count
        px, pz = C + round(ring_r * math.cos(a)), C + round(ring_r * math.sin(a))
        r = base_r + (1 if rnd(px, 5, pz) < .3 and base_r < 2 else 0)
        if not free(px, pz, r):
            continue
        PLACED.append((px, pz, r))
        dmax = math.sqrt(max(0, DOME ** 2 - (dist(px, pz) + r) ** 2)) - 6
        h = int(min(maxh, dmax) * (0.65 + 0.35 * rnd(px, 6, pz)))
        if h < 6:
            continue
        spire(px, pz, r, h)
        spires.append((px, pz, r, h))

# sky bridges: central tower (balcony level 12) to the tallest spires of ring 25
def bridge(x1, z1, x2, z2, y):
    n = int(max(abs(x2 - x1), abs(z2 - z1)))
    path = [(round(x1 + (x2 - x1) * i / n), round(z1 + (z2 - z1) * i / n)) for i in range(n + 1)]
    walk = set()
    for x, z in path:
        for ox in (-1, 0, 1):
            for oz in (-1, 0, 1):
                walk.add((x + ox, z + oz))
    for (x, z) in walk:
        if get(x, y, z) == AIR:
            setb(x, y, z, s("smooth_quartz_slab", type="top"))
    rails = set()
    for (x, z) in walk:
        for ox, oz in ((1, 0), (-1, 0), (0, 1), (0, -1)):
            if (x + ox, z + oz) not in walk:
                rails.add((x + ox, z + oz))
    for k, (x, z) in enumerate(sorted(rails)):
        if get(x, y, z) == AIR and get(x, y + 1, z) == AIR and dist(x, z) > 8:
            setb(x, y, z, s("smooth_quartz_slab", type="top"))
            setb(x, y + 1, z, s("end_rod", facing="up") if (x + z) % 4 == 0 else s("quartz_slab", type="bottom"))
    for i, (x, z) in enumerate(path):
        if i % 4 == 2 and get(x, y - 1, z) == AIR and get(x, y - 2, z) == AIR:
            setb(x, y - 1, z, s("chain", axis="y"))
            setb(x, y - 2, z, s("lantern", hanging="true"))
for px, pz, r, h in sorted(spires, key=lambda t: -t[3])[:4]:
    if h >= 14:
        bridge(C + round(6 * (px - C) / dist(px, pz)), C + round(6 * (pz - C) / dist(px, pz)), px, pz, FY + 12)

# ------------------------------------------------------------------ features
def stall(cx, cz, wool):
    for x in range(cx - 2, cx + 3):
        for z in range(cz - 1, cz + 2):
            setb(x, FY, z, s("birch_planks"))
    for x in range(cx - 2, cx + 3):
        setb(x, FY + 1, cz + 1, s("barrel", facing="up") if x % 2 else s("smooth_quartz_slab", type="top"))
    for x, z in ((cx - 2, cz - 1), (cx + 2, cz - 1), (cx - 2, cz + 1), (cx + 2, cz + 1)):
        fill(x, FY + 1, z, x, FY + 3, z, s("birch_fence"))
    for x in range(cx - 3, cx + 4):
        for z in range(cz - 2, cz + 3):
            setb(x, FY + 4, z, s(wool if (x + 99) % 2 else "white_wool"))
    setb(cx, FY + 3, cz, s("lantern", hanging="true"))
    setb(cx - 1, FY + 1, cz - 1, s("chest", facing="south"))
for sx, sz, wool in ((10, -20, "orange_wool"), (19, -12, "yellow_wool"), (17, -21, "red_wool"), (11, -11, "light_blue_wool")):
    stall(C + sx, C + sz, wool)

# info pavilion: open quartz rotunda with a gold dome
gx, gz = C - 15, C - 15
for x in range(gx - 7, gx + 8):
    for z in range(gz - 7, gz + 8):
        d = dist(x, z, gx, gz)
        if d <= 5.5:
            setb(x, FY, z, s("smooth_quartz") if d < 4.5 else GOLD if (x + z) % 3 == 0 else s("light_gray_concrete"))
        if 4.5 < d <= 5.5 and (abs(x - gx) == abs(z - gz) or x == gx or z == gz) and not (z > gz and x == gx):
            fill(x, FY + 1, z, x, FY + 4, z, s("quartz_pillar", axis="y"))
        for y in range(FY + 5, FY + 11):
            r3 = math.sqrt((x - gx) ** 2 + (z - gz) ** 2 + ((y - FY - 5) * 1.0) ** 2)
            if 5.0 <= r3 < 6.0:
                setb(x, y, z, GOLD if y == FY + 5 else s("glass") if (y - FY) % 2 else s("smooth_quartz"))
setb(gx, FY + 11, gz, s("end_rod", facing="up"))
setb(gx, FY + 1, gz, s("lectern", facing="south"))
setb(gx, FY + 9, gz, s("lantern", hanging="true"))

# garden with silver trees (pale oak) and a pool
px, pz = C + 18, C + 18
for x in range(px - 9, px + 10):
    for z in range(pz - 9, pz + 10):
        d = dist(x, z, px, pz)
        if d <= 9 and dist(x, z) < DOME - 1.5 and not on_spoke(x, z, 3):
            setb(x, FY, z, s("moss_block") if rnd(x, 4, z) < .3 else s("grass_block"))
            if rnd(x, 1, z) < .3:
                setb(x, FY + 1, z, s(["white_tulip", "lily_of_the_valley", "azure_bluet", "oxeye_daisy", "short_grass"][int(rnd(x, 2, z) * 5)]))
        if d <= 3.5:
            setb(x, FY, z, s("water")); setb(x, FY - 1, z, s("water")); setb(x, FY + 1, z, AIR)
        elif d <= 4.4:
            setb(x, FY, z, s("smooth_quartz")); setb(x, FY + 1, z, AIR)
def silver_tree(tx, tz, h=6):
    fill(tx, FY + 1, tz, tx, FY + h, tz, s("pale_oak_log", axis="y"))
    for x in range(tx - 3, tx + 4):
        for y in range(FY + h - 2, FY + h + 3):
            for z in range(tz - 3, tz + 4):
                if math.hypot(x - tx, (y - FY - h) * 1.3, z - tz) <= 3.1 and get(x, y, z) in (AIR, s("short_grass")):
                    setb(x, y, z, s("pale_oak_leaves", persistent="true"))
    setb(tx, FY, tz, s("dirt"))
for tx, tz in ((C + 11, C + 23), (C + 24, C + 11), (C + 24, C + 23), (C + 12, C + 12)):
    silver_tree(tx, tz)

# blue box (portal to /wild): 3x3, 5 high + lamp
bx, bz = C - 17, C + 17
for x in range(bx - 6, bx + 7):
    for z in range(bz - 6, bz + 7):
        if dist(x, z, bx, bz) <= 6:
            setb(x, FY, z, s("light_gray_concrete") if abs(dist(x, z, bx, bz) - 5) < .6 else mix(x, FY, z, FLOOR))
fill(bx - 1, FY + 1, bz - 1, bx + 1, FY + 5, bz + 1, s("blue_concrete"))
fill(bx - 1, FY + 6, bz - 1, bx + 1, FY + 6, bz + 1, s("blue_concrete"))
for (x, z) in ((bx - 1, bz - 1), (bx + 1, bz - 1), (bx - 1, bz + 1), (bx + 1, bz + 1)):
    fill(x, FY + 1, z, x, FY + 6, z, s("blue_terracotta"))
fill(bx, FY + 1, bz - 1, bx, FY + 5, bz - 1, s("blue_concrete"))
for (x, z) in ((bx, bz - 1), (bx, bz + 1), (bx - 1, bz), (bx + 1, bz)):
    setb(x, FY + 4, z, s("white_stained_glass"))
setb(bx, FY + 5, bz + 1, s("white_concrete"))
fill(bx, FY + 1, bz, bx, FY + 3, bz, s("blue_concrete"))
setb(bx, FY + 7, bz, s("sea_lantern"))
setb(bx, FY + 8, bz, s("light_blue_stained_glass"))

# ------------------------------------------------------------------ outside ring: silver bushes on red ground
for x in range(W):
    for z in range(W):
        d = dist(x, z)
        if DOME + .6 < d <= R + .5 and not on_spoke(x, z, 3) and rnd(x, 7, z) < .16:
            setb(x, FY + 1, z, s("pale_oak_leaves", persistent="true") if rnd(x, 8, z) < .6 else s("pale_hanging_moss") if False else s("pale_moss_carpet"))
# street lamps along spokes inside the dome
for t in range(14, 35, 6):
    for sx, sz in ((4, t), (-4, t), (4, -t), (-4, -t)):
        for (x, z) in ((C + sx, C + sz), (C + sz, C + sx)):
            if get(x, FY + 1, z) == AIR:
                fill(x, FY + 1, z, x, FY + 3, z, s("quartz_pillar", axis="y"))
                setb(x, FY + 4, z, s("end_rod", facing="up"))

# ================================================================== EXTRA DETAIL
def air_box(x1, z1, x2, z2, y1, y2):
    return all(get(x, y, z) == AIR for x in range(x1, x2 + 1) for z in range(z1, z2 + 1) for y in range(y1, y2 + 1))

# 1) colonnade around the pool (r = 10) with entablature and gold frieze
cols = []
for k in range(24):
    a = k * math.pi / 12
    x, z = C + round(10 * math.cos(a)), C + round(10 * math.sin(a))
    if on_spoke(x, z, 3) or (x, z) in cols or not air_box(x, z, x, z, FY + 1, FY + 6):
        continue
    cols.append((x, z))
    setb(x, FY + 1, z, s("chiseled_quartz_block"))
    fill(x, FY + 2, z, x, FY + 4, z, s("quartz_pillar", axis="y"))
    setb(x, FY + 5, z, s("chiseled_quartz_block"))
for x, z in ring_cells(C, C, 9.4, 10.6):
    if get(x, FY + 6, z) == AIR:
        setb(x, FY + 6, z, s("smooth_quartz"))
    if get(x, FY + 7, z) == AIR:
        setb(x, FY + 7, z, GOLD if (x + z) % 2 == 0 else s("smooth_quartz_slab", type="bottom"))
    if get(x, FY + 5, z) == AIR and any(dist(x, z, cx, cz) < 1.6 for cx, cz in cols):
        setb(x, FY + 5, z, s("smooth_quartz_slab", type="top"))

# 2) vertical fins on the central tower
for k in range(8):
    a = math.pi / 8 + k * math.pi / 4
    for (rr, y0, y1) in tiers[:5]:
        x, z = C + round((rr + .8) * math.cos(a)), C + round((rr + .8) * math.sin(a))
        if dist(x, z) <= 6.5 and y0 == 0:
            continue
        for y in range(FY + y0 + 1, FY + y1 - 1):
            if get(x, y, z) == AIR:
                setb(x, y, z, s("quartz_pillar", axis="y"))
        if get(x, FY + y1 - 1, z) == AIR:
            setb(x, FY + y1 - 1, z, s("end_rod", facing="up"))

# 3) arcades along the four avenues (offset 6 each side)
for (ox, oz) in ((1, 0), (-1, 0), (0, 1), (0, -1)):
    out_f = OUTF[(ox, oz)]
    for side in (6, -6):
        px_, pz_ = (0, side) if ox != 0 else (side, 0)
        cells = lambda t: (C + ox * t + px_, C + oz * t + pz_)
        for t in range(13, 36, 4):
            x, z = cells(t)
            if not air_box(x, z, x, z, FY + 1, FY + 5):
                continue
            fill(x, FY + 1, z, x, FY + 4, z, s("quartz_pillar", axis="y"))
            setb(x, FY + 5, z, s("chiseled_quartz_block"))
            setb(x, FY + 6, z, s("end_rod", facing="up"))
            nx, nz = cells(t + 4)
            if t + 4 <= 35 and air_box(nx, nz, nx, nz, FY + 1, FY + 5):
                for u in (1, 2, 3):
                    ax_, az_ = cells(t + u)
                    if get(ax_, FY + 5, az_) == AIR:
                        setb(ax_, FY + 5, az_, s("smooth_quartz"))
                    if u in (1, 3) and get(ax_, FY + 4, az_) == AIR:
                        f = INF[out_f] if u == 1 else out_f
                        setb(ax_, FY + 4, az_, s("smooth_quartz_stairs", facing=f, half="top"))
                    if u == 2 and get(ax_, FY + 4, az_) == AIR:
                        setb(ax_, FY + 4, az_, s("lantern", hanging="true"))

# 4) small domed houses in the free gaps
houses = 0
why = {}
for gx_ in range(4, W - 4, 3):
    for gz_ in range(4, W - 4, 3):
        d = dist(gx_, gz_)
        if not (12 < d < 34) or on_spoke(gx_, gz_, 8):
            continue
        if any(dist(gx_, gz_, fx, fz) < fr + 1 for (fx, fz), fr in FEATURES):
            why["feature"] = why.get("feature", 0) + 1; continue
        if math.sqrt(max(0, DOME ** 2 - (d + 4) ** 2)) < 11:
            why["dome"] = why.get("dome", 0) + 1; continue
        if not air_box(gx_ - 3, gz_ - 3, gx_ + 3, gz_ + 3, FY + 1, FY + 9):
            why["busy"] = why.get("busy", 0) + 1; continue
        if any(get(x, FY, z) in (s("water"),) for x in range(gx_ - 2, gx_ + 3) for z in range(gz_ - 2, gz_ + 3)):
            continue
        # door faces the centre
        dx, dz = C - gx_, C - gz_
        door = (1 if dx > 0 else -1, 0) if abs(dx) >= abs(dz) else (0, 1 if dz > 0 else -1)
        for x in range(gx_ - 2, gx_ + 3):
            for z in range(gz_ - 2, gz_ + 3):
                edge = abs(x - gx_) == 2 or abs(z - gz_) == 2
                corner = abs(x - gx_) == 2 and abs(z - gz_) == 2
                setb(x, FY, z, s("polished_diorite"))
                for y in range(FY + 1, FY + 5):
                    if corner:
                        st = s("quartz_pillar", axis="y")
                    elif edge:
                        st = s("white_concrete")
                        mid = (x == gx_ or z == gz_)
                        if mid and y == FY + 2:
                            st = WIN
                        if y == FY + 4:
                            st = GOLD if mid else s("smooth_quartz")
                    else:
                        st = AIR if y < FY + 4 else s("smooth_quartz")
                    setb(x, y, z, st)
        dxp, dzp = gx_ + door[0] * 2, gz_ + door[1] * 2
        setb(dxp, FY + 1, dzp, AIR); setb(dxp, FY + 2, dzp, AIR)
        setb(dxp + door[0], FY + 3, dzp + door[1], s("lantern", hanging="false") if False else s("end_rod", facing=OUTF[door]))
        setb(gx_, FY + 1, gz_, s("ochre_froglight"))
        for x in range(gx_ - 3, gx_ + 4):
            for z in range(gz_ - 3, gz_ + 4):
                for y in range(FY + 5, FY + 9):
                    r3 = math.sqrt((x - gx_) ** 2 + (z - gz_) ** 2 + (y - FY - 5) ** 2)
                    if 2.2 <= r3 < 3.2:
                        setb(x, y, z, GOLD if y >= FY + 6 else s("smooth_quartz"))
        setb(gx_, FY + 8, gz_, GOLD)
        setb(gx_, FY + 9, gz_, s("end_rod", facing="up"))
        houses += 1

# 5) planters and benches around the inner plaza (r = 14)
for k in range(24):
    a = k * math.pi / 12 + math.pi / 24
    x, z = C + round(14 * math.cos(a)), C + round(14 * math.sin(a))
    if on_spoke(x, z, 3) or not air_box(x, z, x, z, FY + 1, FY + 2):
        continue
    if k % 2 == 0:
        setb(x, FY + 1, z, s("smooth_quartz"))
        setb(x, FY + 2, z, s(["potted_white_tulip", "potted_azure_bluet", "potted_lily_of_the_valley", "potted_oxeye_daisy"][k // 2 % 4]))
    else:
        dx, dz = x - C, z - C
        f = OUTF[(1 if dx > 0 else -1, 0)] if abs(dx) >= abs(dz) else OUTF[(0, 1 if dz > 0 else -1)]
        setb(x, FY + 1, z, s("birch_stairs", facing=f, half="bottom"))

# 6) outside the dome: red vegetation and small silver trees
for x in range(W):
    for z in range(W):
        d = dist(x, z)
        if DOME + .7 < d <= R + .5 and not on_spoke(x, z, 3) and get(x, FY + 1, z) == AIR:
            if get(x, FY, z) == s("crimson_nylium") and rnd(x, 11, z) < .35:
                setb(x, FY + 1, z, s("crimson_roots"))
for k in range(8):
    a = math.pi / 8 + k * math.pi / 4
    tx, tz = C + round(39.5 * math.cos(a)), C + round(39.5 * math.sin(a))
    fill(tx, FY + 1, tz, tx, FY + 3, tz, s("pale_oak_log", axis="y"))
    for x in range(tx - 2, tx + 3):
        for y in range(FY + 3, FY + 6):
            for z in range(tz - 2, tz + 3):
                if math.hypot(x - tx, (y - FY - 4) * 1.4, z - tz) <= 2.2 and get(x, y, z) == AIR and dist(x, z) > DOME + .8:
                    setb(x, y, z, s("pale_oak_leaves", persistent="true"))
# 4b) small column shrines (3x3) in any remaining free spot
shrines = 0
for gx_ in range(3, W - 3, 2):
    for gz_ in range(3, W - 3, 2):
        d = dist(gx_, gz_)
        if not (11 < d < 34) or on_spoke(gx_, gz_, 7) or shrines >= 28:
            continue
        if any(dist(gx_, gz_, fx, fz) < fr + .5 for (fx, fz), fr in FEATURES):
            continue
        if not air_box(gx_ - 2, gz_ - 2, gx_ + 2, gz_ + 2, FY + 1, FY + 6):
            continue
        if get(gx_, FY, gz_) == s("water"):
            continue
        for ox in (-1, 1):
            for oz in (-1, 1):
                fill(gx_ + ox, FY + 1, gz_ + oz, gx_ + ox, FY + 3, gz_ + oz, s("quartz_pillar", axis="y"))
        fill(gx_ - 1, FY + 4, gz_ - 1, gx_ + 1, FY + 4, gz_ + 1, s("smooth_quartz_slab", type="bottom"))
        setb(gx_, FY + 4, gz_, GOLD)
        setb(gx_, FY + 5, gz_, s("end_rod", facing="up"))
        setb(gx_, FY, gz_, s("ochre_froglight"))
        setb(gx_, FY + 1, gz_, s("potted_white_tulip") if shrines % 2 else s("potted_azure_bluet"))
        shrines += 1
print("houses", houses, "shrines", shrines, "columns", len(cols), why)

# ------------------------------------------------------------------ NBT
def nstr(v):
    b = v.encode(); return struct.pack(">H", len(b)) + b
def tag(t, n, p): return bytes([t]) + nstr(n) + p
def comp(items): return b"".join(items) + b"\x00"
def ilist(v): return bytes([3]) + struct.pack(">i", len(v)) + b"".join(struct.pack(">i", i) for i in v)
pal, pidx, bl = [], {}, []
for (x, y, z), st in sorted(blocks.items()):
    if st not in pidx:
        pidx[st] = len(pal); pal.append(st)
    bl.append(comp([tag(9, "pos", ilist([x, y, z])), tag(3, "state", struct.pack(">i", pidx[st]))]))
def pe(st):
    name, _, rest = st.partition("[")
    it = [tag(8, "Name", nstr(name))]
    if rest:
        it.append(tag(10, "Properties", comp([tag(8, k, nstr(v)) for k, v in (p.split("=") for p in rest.rstrip("]").split(","))])))
    return comp(it)
root = comp([tag(3, "DataVersion", struct.pack(">i", DATA_VERSION)), tag(9, "size", ilist([W, H, W])),
             tag(9, "palette", bytes([10]) + struct.pack(">i", len(pal)) + b"".join(pe(p) for p in pal)),
             tag(9, "blocks", bytes([10]) + struct.pack(">i", len(bl)) + b"".join(bl)),
             tag(9, "entities", bytes([0]) + struct.pack(">i", 0))])
data = gzip.compress(tag(10, "", root), 9)
open(os.path.join(OUT, "citadel.nbt"), "wb").write(data)

# ------------------------------------------------------------------ previews: top-down (dome removed) + side elevation
def colour(st):
    n = st.split("[")[0].split(":")[1]
    t = {"smooth_quartz": (236, 230, 222), "white_concrete": (225, 228, 229), "calcite": (222, 223, 220), "polished_diorite": (190, 190, 192),
         "light_gray_concrete": (140, 140, 134), "gold_block": (246, 208, 61), "yellow_terracotta": (186, 133, 35), "ochre_froglight": (250, 220, 140),
         "yellow_stained_glass": (230, 220, 60), "glass": (180, 220, 235), "water": (52, 96, 219), "crimson_nylium": (148, 30, 30),
         "red_terracotta": (143, 61, 46), "orange_terracotta": (161, 83, 37), "terracotta": (152, 94, 67), "blue_concrete": (44, 46, 143),
         "blue_terracotta": (74, 59, 91), "pale_oak_leaves": (200, 205, 195), "pale_oak_log": (120, 110, 105), "grass_block": (95, 159, 53),
         "moss_block": (89, 109, 45), "birch_planks": (192, 175, 121), "white_wool": (235, 235, 235), "orange_wool": (240, 118, 20),
         "yellow_wool": (248, 197, 40), "red_wool": (160, 40, 35), "light_blue_wool": (58, 175, 217), "quartz_pillar": (236, 230, 222),
         "end_rod": (255, 255, 240), "lightning_rod": (200, 120, 80), "smooth_quartz_slab": (230, 225, 215)}
    return t.get(n, (170, 170, 170))
def png(px):
    h = len(px); w = len(px[0])
    raw = b"".join(b"\x00" + b"".join(struct.pack("BBBB", *p) for p in row) for row in px)
    ch = lambda t, d: struct.pack(">I", len(d)) + t + d + struct.pack(">I", zlib.crc32(t + d) & 0xFFFFFFFF)
    return b"\x89PNG\r\n\x1a\n" + ch(b"IHDR", struct.pack(">IIBBBBB", w, h, 8, 6, 0, 0, 0)) + ch(b"IDAT", zlib.compress(raw, 9)) + ch(b"IEND", b"")
S = 5
top = [[(25, 25, 30, 255)] * (W * S) for _ in range(W * S)]
for x in range(W):
    for z in range(W):
        for y in range(H - 1, -1, -1):
            st = get(x, y, z)
            shell = DOME - .6 <= math.sqrt((x - C) ** 2 + (z - C) ** 2 + (y - FY) ** 2) < DOME + .7 and y > FY + 2
            if st != AIR and not shell:
                c = colour(st); f = .7 + .3 * min(1, (y - FY) / 30)
                c = tuple(int(v * f) for v in c)
                for a in range(S):
                    for b in range(S):
                        top[z * S + a][x * S + b] = c + (255,)
                break
open(os.path.join(OUT, "citadel_top.png"), "wb").write(png(top))
side = [[(250, 160, 90, 255) if y < (H * S) // 2 else (250, 190, 120, 255) for x in range(W * S)] for y in range(H * S)]
for x in range(W):
    for y in range(H):
        for z in range(W):  # front view from south (z = max)
            zz = W - 1 - z
            st = get(x, y, zz)
            in_shell = DOME - .6 <= math.sqrt((x - C) ** 2 + (zz - C) ** 2 + (y - FY) ** 2) < DOME + .7 and y > FY
            if st != AIR and not in_shell:
                c = colour(st)
                if "glass" in st:
                    c = tuple(int(v * .5 + 230 * .5) for v in c)
                for a in range(S):
                    for b in range(S):
                        side[(H - 1 - y) * S + a][x * S + b] = c + (255,)
                break
open(os.path.join(OUT, "citadel_side.png"), "wb").write(png(side))
print("blocks", len(blocks), "palette", len(pal), "nbt", len(data), "spires", len(spires))
