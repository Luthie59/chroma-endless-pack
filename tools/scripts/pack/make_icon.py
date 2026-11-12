import math, os, sys
from PIL import Image, ImageDraw, ImageFilter
D = sys.argv[1]
S = 512; c = S / 2
G = (246, 200, 78, 255); GD = (150, 100, 28, 255); GL = (255, 236, 160, 255)
bg = Image.new("RGBA", (S, S), (0, 0, 0, 0))
# soft night-blue disc with a warm glow
glow = Image.new("RGBA", (S, S), (0, 0, 0, 0)); gd = ImageDraw.Draw(glow)
gd.ellipse([c - 250, c - 250, c + 250, c + 250], fill=(12, 16, 36, 255))
gd.ellipse([c - 170, c - 170, c + 170, c + 170], fill=(60, 40, 10, 140))
glow = glow.filter(ImageFilter.GaussianBlur(40)); bg.alpha_composite(glow)
d = ImageDraw.Draw(bg)
def ring(r, w, col): d.ellipse([c - r, c - r, c + r, c + r], outline=col, width=w)
ring(236, 14, G); ring(214, 4, GD); ring(206, 3, G)
for k in range(60):                                   # graduations
    a = k * math.pi / 30; r0, r1 = (208, 226) if k % 5 == 0 else (212, 222)
    d.line([(c + r0 * math.cos(a), c + r0 * math.sin(a)), (c + r1 * math.cos(a), c + r1 * math.sin(a))], fill=GL if k % 5 == 0 else G, width=4 if k % 5 == 0 else 2)
for k in range(6):                                    # rosette of intersecting circles
    a = k * math.pi / 3 + math.pi / 6
    cx, cy = c + 92 * math.cos(a), c + 92 * math.sin(a)
    d.ellipse([cx - 92, cy - 92, cx + 92, cy + 92], outline=G, width=5)
for rot in (-math.pi / 2, math.pi / 2):               # two interlaced triangles
    pts = [(c + 150 * math.cos(rot + k * 2 * math.pi / 3), c + 150 * math.sin(rot + k * 2 * math.pi / 3)) for k in range(3)]
    d.polygon(pts, outline=GL); d.line(pts + [pts[0]], fill=GL, width=6)
ring(150, 6, G); ring(58, 8, GL)
d.ellipse([c - 30, c - 30, c + 30, c + 30], fill=G); d.ellipse([c - 12, c - 12, c + 12, c + 12], fill=GL)
for k in range(12):
    a = k * math.pi / 6; d.ellipse([c + 182 * math.cos(a) - 9, c + 182 * math.sin(a) - 9, c + 182 * math.cos(a) + 9, c + 182 * math.sin(a) + 9], fill=GL)
icon = bg.resize((64, 64), Image.LANCZOS)
out = Image.new("RGB", (64, 64), (10, 12, 26)); out.paste(icon, (0, 0), icon)
out.save(os.path.join(D, "server-icon.png"))
out.resize((256, 256), Image.NEAREST).save(os.path.join(D, "server-icon-preview.png"))
print("ok")
