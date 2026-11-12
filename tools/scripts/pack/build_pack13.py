import sys, os, io, json, zipfile, hashlib, math
sys.argv = [sys.argv[0], os.path.join(sys.argv[1], "ranks_v2")] if len(sys.argv) > 1 else sys.argv
D = os.path.dirname(sys.argv[1])
exec(open(os.path.join(D, "ranks_v2.py"), encoding="utf8").read().split("BADGES =")[0])
def fondateur():  # the founder's seal: crowned golden seal, violet heart, star
    im = Image.new("RGBA", (S, S)); d = ImageDraw.Draw(im)
    V1, V2, V3 = (200, 140, 255, 255), (120, 60, 200, 255), (60, 25, 110, 255)
    px(d, [(4, 0), (7, 0), (8, 0), (11, 0)], G1)                       # crown points
    d.polygon([(3, 1), (12, 1), (11, 3), (4, 3)], fill=G2); px(d, [(7, 1), (8, 1)], (230, 40, 60, 255))
    d.ellipse([1, 3, 14, 15], fill=G3); d.ellipse([2, 4, 13, 14], fill=G2)
    d.ellipse([3, 5, 12, 13], fill=V3); d.ellipse([4, 6, 11, 12], fill=V2)
    star = [(7.5, 6), (8.3, 8.2), (10.5, 8.4), (8.8, 9.7), (9.4, 12), (7.5, 10.7), (5.6, 12), (6.2, 9.7), (4.5, 8.4), (6.7, 8.2)]
    d.polygon(star, fill=G1); px(d, [(5, 6)], V1)
    px(d, [(2, 9), (13, 9), (7, 15), (8, 15)], G1)
    return outline(im, (30, 12, 40, 255))
b = fondateur(); b.save(os.path.join(D, "ranks_v2", "fondateur.png"))
prev = Image.new("RGBA", (300, 150), (54, 57, 63, 255)); prev.alpha_composite(b.resize((128, 128), Image.NEAREST), (6, 6)); prev.alpha_composite(b.resize((32, 32), Image.NEAREST), (200, 60)); prev.save(os.path.join(D, "ranks_v2", "_fondateur.png"))
files = {}
with zipfile.ZipFile(os.path.join(D, "ChromaEndless-Pack12.zip")) as z:
    for n in z.namelist(): files[n] = z.read(n)
files["assets/chroma/textures/font/fondateur.png"] = open(os.path.join(D, "ranks_v2", "fondateur.png"), "rb").read()
font = json.loads(files["assets/minecraft/font/default.json"])
font["providers"] = [p for p in font["providers"] if "\ue007" not in p.get("chars", [])]
font["providers"].insert(6, {"type": "bitmap", "file": "chroma:font/fondateur.png", "ascent": 7, "height": 8, "chars": ["\ue007"]})
files["assets/minecraft/font/default.json"] = json.dumps(font, ensure_ascii=True, indent=1).encode()
buf = io.BytesIO()
with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as z:
    for p in sorted(files):
        zi = zipfile.ZipInfo(p, date_time=(2026, 1, 1, 0, 0, 0)); zi.compress_type = zipfile.ZIP_DEFLATED; z.writestr(zi, files[p])
data = buf.getvalue(); open(os.path.join(D, "ChromaEndless-Pack13.zip"), "wb").write(data)
print(hashlib.sha1(data).hexdigest())
