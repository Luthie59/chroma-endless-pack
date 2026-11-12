"""Themed rank badges for La Citadelle (16x16, shown at text height 8)."""
import io, os, sys, math
import numpy as np
from PIL import Image, ImageDraw

OUT = sys.argv[1]
S = 16

def outline(im, col=(30, 20, 10, 255)):
    a = np.asarray(im).copy()
    al = a[..., 3] > 0
    grow = np.zeros_like(al)
    for dy, dx in ((1, 0), (-1, 0), (0, 1), (0, -1)):
        grow |= np.roll(np.roll(al, dy, 0), dx, 1)
    edge = grow & ~al
    a[edge] = col
    return Image.fromarray(a, "RGBA")

def px(d, pts, c):
    for p in pts: d.point(p, fill=c)

G1, G2, G3, G4 = (255, 236, 150, 255), (246, 200, 80, 255), (205, 150, 48, 255), (140, 92, 26, 255)

def admin():   # golden dome of the citadel with spire and ruby
    im = Image.new("RGBA", (S, S)); d = ImageDraw.Draw(im)
    d.rectangle([7, 1, 8, 4], fill=G2); d.point((7, 1), fill=G1)          # spire
    d.pieslice([2, 4, 13, 15], 180, 360, fill=(120, 190, 235, 255))        # glass dome
    d.arc([2, 4, 13, 15], 180, 360, fill=G2)
    d.line([(7, 5), (7, 9)], fill=G3); d.line([(4, 7), (5, 9)], fill=G3); d.line([(11, 7), (10, 9)], fill=G3)
    px(d, [(5, 6), (6, 6)], (225, 245, 255, 255))                          # glint
    d.rectangle([1, 10, 14, 11], fill=G2); d.line([(1, 10), (14, 10)], fill=G1)
    d.rectangle([2, 12, 13, 14], fill=G3)
    for x in (3, 6, 9, 12): d.line([(x, 12), (x, 14)], fill=G4)            # columns
    d.rectangle([7, 12, 8, 14], fill=(200, 30, 40, 255)); d.point((7, 12), fill=(255, 120, 120, 255))  # ruby gate
    return outline(im)

def modo():    # guardian shield bearing a golden hourglass
    im = Image.new("RGBA", (S, S)); d = ImageDraw.Draw(im)
    B1, B2 = (60, 110, 200, 255), (30, 60, 140, 255)
    d.polygon([(2, 1), (13, 1), (13, 8), (7.5, 14.5), (2, 8)], fill=B1)
    d.polygon([(8, 1), (13, 1), (13, 8), (8, 14)], fill=B2)
    d.line([(2, 1), (13, 1)], fill=G2); d.line([(2, 1), (2, 8)], fill=G2); d.line([(13, 1), (13, 8)], fill=G3)
    d.line([(2, 8), (7, 13)], fill=G2); d.line([(13, 8), (8, 13)], fill=G3); d.point((7, 14), fill=G3); d.point((8, 14), fill=G3)
    GL, SA = (200, 225, 245, 255), (255, 215, 110, 255)                                    # hourglass
    d.line([(4, 2), (11, 2)], fill=G1); d.line([(4, 11), (11, 11)], fill=G2)
    rows = {3: (5, 10), 4: (5, 10), 5: (6, 9), 6: (7, 8), 7: (7, 8), 8: (6, 9), 9: (5, 10), 10: (5, 10)}
    for y, (x0, x1) in rows.items():
        d.line([(x0, y), (x1, y)], fill=GL)
    d.line([(6, 4), (9, 4)], fill=SA); d.line([(7, 5), (8, 5)], fill=SA); d.point((7, 7), fill=SA)
    d.line([(6, 9), (9, 9)], fill=SA); d.line([(6, 10), (9, 10)], fill=SA); d.line([(7, 8), (8, 8)], fill=SA)
    return outline(im, (15, 15, 40, 255))

def guide():   # brass astrolabe-compass
    im = Image.new("RGBA", (S, S)); d = ImageDraw.Draw(im)
    d.ellipse([1, 1, 14, 14], fill=G3); d.ellipse([2, 2, 13, 13], fill=(250, 240, 210, 255))
    d.ellipse([1, 1, 14, 14], outline=G2)
    for a in range(0, 360, 45):
        r = 5.6; x = 7.5 + r * math.cos(math.radians(a)); y = 7.5 + r * math.sin(math.radians(a))
        d.point((round(x), round(y)), fill=G4)
    d.polygon([(7.5, 2.5), (9, 7.5), (7.5, 7.5), (6, 7.5)], fill=(200, 40, 40, 255))       # north needle
    d.polygon([(7.5, 12.5), (9, 7.5), (6, 7.5)], fill=(70, 80, 110, 255))
    px(d, [(7, 7), (8, 7), (7, 8), (8, 8)], G2)
    d.point((7, 0), fill=G2); d.point((8, 0), fill=G2)                                   # bail
    return outline(im)

def vipplus(): # armillary orrery: gold core, two crossed cyan rings
    im = Image.new("RGBA", (S, S)); d = ImageDraw.Draw(im)
    C1, C2 = (120, 240, 255, 255), (40, 170, 220, 255)
    d.ellipse([0, 4, 15, 11], outline=C2)
    ring = Image.new("RGBA", (S, S)); dr = ImageDraw.Draw(ring); dr.ellipse([4, 0, 11, 15], outline=C1)
    d.ellipse([4, 4, 11, 11], fill=G3); d.ellipse([5, 5, 10, 10], fill=G2); px(d, [(6, 6), (7, 6), (6, 7)], G1)
    im.alpha_composite(ring)
    d = ImageDraw.Draw(im)
    px(d, [(1, 7), (14, 8)], (255, 255, 255, 255))   # orbiting sparks
    return outline(im, (10, 30, 50, 255))

def vip():     # emerald time-glyph disc (concentric circles, original design)
    im = Image.new("RGBA", (S, S)); d = ImageDraw.Draw(im)
    E1, E2, E3 = (150, 255, 180, 255), (50, 205, 110, 255), (20, 120, 70, 255)
    d.ellipse([1, 1, 14, 14], fill=E3); d.ellipse([1, 1, 14, 14], outline=E2)
    d.ellipse([4, 4, 11, 11], outline=E1)
    d.ellipse([6, 6, 9, 9], fill=G2)
    for a in (30, 150, 270):
        x = 7.5 + 5 * math.cos(math.radians(a)); y = 7.5 + 5 * math.sin(math.radians(a))
        d.ellipse([x - 1.2, y - 1.2, x + 1.2, y + 1.2], fill=E1)
    d.line([(7, 2), (7, 4)], fill=E2)
    return outline(im, (5, 35, 20, 255))

def joueur():  # traveller's pocket watch
    im = Image.new("RGBA", (S, S)); d = ImageDraw.Draw(im)
    S1, S2, S3 = (230, 230, 235, 255), (170, 170, 180, 255), (110, 110, 120, 255)
    d.ellipse([6, 0, 9, 3], outline=S2)                      # ring
    d.ellipse([2, 3, 13, 14], fill=S3); d.ellipse([3, 4, 12, 13], fill=(245, 240, 225, 255))
    d.ellipse([2, 3, 13, 14], outline=S2)
    for (x, y) in ((7, 5), (11, 8), (7, 12), (3, 8)): d.point((x if x != 7 else 7, y), fill=S3)
    d.line([(7, 8), (7, 6)], fill=(40, 40, 50, 255)); d.line([(7, 8), (9, 9)], fill=(40, 40, 50, 255))
    d.point((7, 8), fill=G3)
    return outline(im, (25, 25, 30, 255))

BADGES = {"admin": admin(), "modo": modo(), "guide": guide(), "vipplus": vipplus(), "vip": vip(), "joueur": joueur()}
os.makedirs(OUT, exist_ok=True)
sheet = Image.new("RGBA", (6 * 140, 180), (54, 57, 63, 255))
for i, (n, b) in enumerate(BADGES.items()):
    b.save(os.path.join(OUT, n + ".png"))
    sheet.alpha_composite(b.resize((128, 128), Image.NEAREST), (i * 140 + 6, 6))
    sheet.alpha_composite(b.resize((32, 32), Image.NEAREST), (i * 140 + 54, 142))
sheet.save(os.path.join(OUT, "_preview.png"))
print("ok")
