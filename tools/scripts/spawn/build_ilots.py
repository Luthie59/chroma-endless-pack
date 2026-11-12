"""Islets 'b' (north) and 'd' (south) of the Instant Éternel: terrain, faithful surroundings and invisible barrier
volumes matching the 3D building models (the buildings themselves are item displays summoned on top).
Writes b_ilot.nbt / d_ilot.nbt (origin = world corner given in the JSON) + preview PNGs."""
import gzip, json, math, os, random, struct, sys
from PIL import Image

OUT = sys.argv[1]
DATA_VERSION = 4189
TOP_Y = 120                          # grass surface, same level as the main island

def s(name, **p):
    return "minecraft:%s[%s]" % (name, ",".join("%s=%s" % kv for kv in sorted(p.items()))) if p else "minecraft:" + name
def rnd(*k): return random.Random(hash(k) & 0xffffffff).random()

class Islet:
    def __init__(self, cx, cz, rx, rz, seed):
        self.blocks = {}
        self.cx, self.cz, self.rx, self.rz, self.seed = cx, cz, rx, rz, seed
        m = 8
        self.x0, self.z0 = int(cx - rx - m), int(cz - rz - m)
        self.W, self.D = int(2 * (rx + m)) + 1, int(2 * (rz + m)) + 1
        self.y0 = TOP_Y - 34
        self.H = 34 + 46
        self.tops = {}
    def set(self, x, y, z, st):                      # world coordinates
        lx, ly, lz = x - self.x0, y - self.y0, z - self.z0
        if 0 <= lx < self.W and 0 <= ly < self.H and 0 <= lz < self.D: self.blocks[(lx, ly, lz)] = st
    def get(self, x, y, z): return self.blocks.get((x - self.x0, y - self.y0, z - self.z0))
    def terrain(self):
        sd = self.seed
        for x in range(self.x0, self.x0 + self.W):
            for z in range(self.z0, self.z0 + self.D):
                dx, dz = (x - self.cx) / self.rx, (z - self.cz) / self.rz
                th = math.atan2(dz, dx)
                r = 1 + .08 * math.sin(3 * th + sd) + .05 * math.sin(5 * th + 2 * sd) + (rnd(sd, x, z) - .5) * .03
                d = math.hypot(dx, dz)
                if d > r: continue
                f = d / r
                ytop = TOP_Y - (1 if f > .92 else 0)
                depth = int((1 - f ** 1.6) * 26 * (.85 + .3 * rnd(sd, x, 7, z))) + 1
                for y in range(ytop - depth, ytop + 1):
                    k = ytop - y
                    if k == 0: st = s("grass_block")
                    elif k <= 2: st = s("dirt")
                    elif k <= 7: st = [s("stone"), s("andesite"), s("tuff")][int(rnd(x, y, z, 2) * 3)]
                    else: st = [s("deepslate"), s("tuff"), s("calcite"), s("stone")][int(rnd(x, y, z, 3) * 4)]
                    self.set(x, y, z, st)
                self.tops[(x, z)] = (ytop, ytop - depth, f)
        for (x, z), (yt, yb, f) in self.tops.items():           # glow berries & roots underneath
            r = rnd(sd, x, z, 11)
            if f > .45 and r < .09:
                n = 2 + int(rnd(x, z, 12) * 5)
                for i in range(1, n): self.set(x, yb - i, z, s("cave_vines_plant", berries="true" if rnd(x, i, z) < .5 else "false"))
                self.set(x, yb - n, z, s("cave_vines", age="25", berries="true"))
            elif f > .45 and r < .14: self.set(x, yb - 1, z, s("hanging_roots"))
    def surface(self, x, z, st):
        if (x, z) in self.tops: self.set(x, self.tops[(x, z)][0], z, st)
    def above(self, x, z, st, dy=1):
        if (x, z) in self.tops: self.set(x, self.tops[(x, z)][0] + dy, z, st)
    def barrier(self, x0, x1, z0, z1, y0, y1):
        for x in range(x0, x1 + 1):
            for z in range(z0, z1 + 1):
                for y in range(y0, y1 + 1): self.set(x, y, z, s("barrier"))
    def grass_decor(self, keep):
        for (x, z), (yt, yb, f) in self.tops.items():
            if keep(x, z) or self.get(x, yt, z) != s("grass_block") or self.get(x, yt + 1, z): continue
            r = rnd(self.seed, x, z, 30)
            if r < .22: self.set(x, yt + 1, z, s("short_grass"))
            elif r < .26: self.set(x, yt + 1, z, s(["dandelion", "oxeye_daisy", "white_tulip", "azure_bluet"][int(rnd(x, z, 31) * 4)]))
    def tree(self, x, z, kind="spruce", h=9):
        y = TOP_Y + 1
        log, leaf = (s("spruce_log"), s("spruce_leaves", persistent="true")) if kind == "spruce" else \
                    (s("birch_log"), s("birch_leaves", persistent="true")) if kind == "poplar" else (s("oak_log"), s("oak_leaves", persistent="true"))
        for i in range(h): self.set(x, y + i, z, log)
        for i in range(2, h + 2):
            if kind == "spruce": rad = max(0, (h + 2 - i) / (h) * 3.2)
            elif kind == "poplar": rad = 1.6 if i < h else 1.0
            else: rad = 2.8 if h - 4 < i < h + 1 else 0
            for dx in range(-4, 5):
                for dz in range(-4, 5):
                    if math.hypot(dx, dz) <= rad and (dx or dz or i >= h) and rnd(x + dx, i, z + dz) < .9:
                        if not self.get(x + dx, y + i, z + dz): self.set(x + dx, y + i, z + dz, leaf)
        self.set(x, y + h, z, leaf); self.set(x, y + h + 1, z, leaf)
    def lamp(self, x, z, h=5, post="spruce_fence"):
        for i in range(1, h + 1): self.above(x, z, s(post), i)
        self.above(x, z, s("lantern", hanging="false"), h + 1)
    def write(self, name, entities=()):
        def nstr(v): b = v.encode(); return struct.pack(">H", len(b)) + b
        def tag(t, n, p): return bytes([t]) + nstr(n) + p
        def comp(items): return b"".join(items) + b"\x00"
        def ilist(v): return bytes([3]) + struct.pack(">i", len(v)) + b"".join(struct.pack(">i", i) for i in v)
        def pe(st):
            nm, _, rest = st.partition("[")
            it = [tag(8, "Name", nstr(nm))]
            if rest: it.append(tag(10, "Properties", comp([tag(8, k, nstr(v)) for k, v in (p.split("=") for p in rest.rstrip("]").split(","))])))
            return comp(it)
        pal, pidx, bl = [], {}, []
        for (x, y, z), st in sorted(self.blocks.items()):
            if st not in pidx: pidx[st] = len(pal); pal.append(st)
            bl.append(comp([tag(9, "pos", ilist([x, y, z])), tag(3, "state", struct.pack(">i", pidx[st]))]))
        root = comp([tag(3, "DataVersion", struct.pack(">i", DATA_VERSION)), tag(9, "size", ilist([self.W, self.H, self.D])),
                     tag(9, "palette", bytes([10]) + struct.pack(">i", len(pal)) + b"".join(pe(p) for p in pal)),
                     tag(9, "blocks", bytes([10]) + struct.pack(">i", len(bl)) + b"".join(bl)),
                     tag(9, "entities", bytes([0]) + struct.pack(">i", 0))])
        open(os.path.join(OUT, name + ".nbt"), "wb").write(gzip.compress(tag(10, "", root), 6))
        # top-view preview
        col = {"grass_block": (110, 170, 70), "gray_concrete": (70, 72, 76), "smooth_stone": (170, 170, 170), "barrier": (220, 120, 120),
               "white_concrete": (235, 235, 235), "spruce_leaves": (40, 90, 50), "birch_leaves": (120, 160, 70), "oak_leaves": (70, 130, 50),
               "polished_andesite": (150, 152, 150), "stone_bricks": (130, 130, 130), "iron_bars": (60, 90, 200), "green_concrete": (60, 110, 40)}
        best = {}
        for (x, y, z), st in self.blocks.items():
            if (x, z) not in best or y > best[(x, z)][0]: best[(x, z)] = (y, st)
        S = 5; im = Image.new("RGB", (self.W * S, self.D * S), (255, 170, 110)); px = im.load()
        for (x, z), (y, st) in best.items():
            c = col.get(st.split("[")[0].split(":")[1], (160, 160, 160))
            for a in range(S):
                for b in range(S): px[x * S + a, z * S + b] = c
        im.save(os.path.join(OUT, name + "_top.png"))
        return {"origin": [self.x0, self.y0, self.z0], "size": [self.W, self.H, self.D], "blocks": len(self.blocks)}

info = {}
# ======================================================================================== b (north)
B = Islet(0.5, -99.5, 26, 17, 7)
B.terrain()
G = TOP_Y + 1
BX0, BX1, BZ0, BZ1 = -14, 14, -104, -96                           # building footprint (blocks) = barrier volume
for (x, z) in list(B.tops):
    if BX0 - 1 <= x <= BX1 + 1 and BZ1 + 1 <= z <= BZ1 + 2: B.surface(x, z, s("smooth_stone"))          # sidewalk
    elif BX0 - 6 <= x <= BX1 + 4 and BZ1 + 3 <= z <= BZ1 + 9: B.surface(x, z, s("gray_concrete"))     # car park
for x in range(BX0 - 3, BX1 + 2, 3):                                       # parking stall lines
    for z in range(BZ1 + 6, BZ1 + 10): B.surface(x, z, s("white_concrete"))
for x in (BX0 + 2, BX0 + 9, BX1 - 8, BX1 - 1):                              # brown bollards with white tops
    B.above(x, BZ1 + 3, s("spruce_fence")); B.above(x, BZ1 + 3, s("birch_button", face="floor", facing="north"), 2)
B.barrier(BX0, BX1, BZ0, BZ1, G, G + 15)
B.tree(BX0 - 6, BZ0 + 2, "spruce", 10)
for i, x in enumerate((BX0 - 3, BX0 - 2)):                                  # green wheelie bins near the west gable
    B.above(x, BZ1 + 1, s("green_concrete")); B.above(x, BZ1 + 1, s("dark_oak_trapdoor", half="bottom", facing="south"), 2)
B.lamp(BX1 + 6, BZ1 + 4, 6)
B.lamp(BX0 - 7, BZ1 + 6, 6)
B.grass_decor(lambda x, z: False)
info["b"] = B.write("b_ilot")

# ======================================================================================== d (south)
D = Islet(0.5, 99.5, 21, 20, 13)
D.terrain()
DX0, DX1, DZ0, DZ1 = -10, 10, 91, 107                             # tower footprint (blocks)
for (x, z) in list(D.tops):                                        # paved forecourt + path toward the bridge (north)
    if DX0 - 1 <= x <= DX1 + 1 and DZ0 - 3 <= z <= DZ1 + 1: D.surface(x, z, s("polished_andesite"))
    if -1 <= x <= 1 and z < DZ0 - 3: D.surface(x, z, s("stone_bricks"))
D.barrier(DX0 + 1, DX1 - 1, DZ0 + 1, DZ1 - 1, G, G + 3)            # recessed ground floor under the pilotis
D.barrier(DX0, DX1, DZ0, DZ1, G + 4, G + 37)
for x in range(DX0 - 4, DX1 + 5):                                  # blue metal fences round the lawn
    for z in (DZ0 - 6, DZ1 + 4):
        if abs(x) > 2 and (x, z) in D.tops and D.get(x, G, z) is None: D.above(x, z, s("iron_bars", north="false", south="false", east="true", west="true"))
for z in range(DZ0 - 6, DZ1 + 5):
    for x in (DX0 - 4, DX1 + 4):
        if (x, z) in D.tops and D.get(x, G, z) is None: D.above(x, z, s("iron_bars", north="true", south="true", east="false", west="false"))
for (tx, tz) in ((DX1 + 7, DZ0), (DX1 + 8, DZ0 + 8), (DX0 - 7, DZ1 - 2), (DX1 + 6, DZ1 + 6)):
    D.tree(tx, tz, "poplar", 13)
D.tree(DX0 - 8, DZ0 + 4, "oak", 7)
D.lamp(3, DZ0 - 8, 6, "polished_deepslate_wall"); D.lamp(-3, DZ0 - 14, 6, "polished_deepslate_wall")
D.grass_decor(lambda x, z: False)
info["d"] = D.write("d_ilot")
json.dump(info, open(os.path.join(OUT, "ilots.json"), "w"))
print(json.dumps(info))
