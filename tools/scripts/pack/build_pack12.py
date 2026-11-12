import zipfile, io, json, sys, os, hashlib
D = sys.argv[1]
files = {}
with zipfile.ZipFile(os.path.join(D, "ChromaEndless-Pack11.zip")) as z:
    for n in z.namelist(): files[n] = z.read(n)
names = ["admin", "modo", "guide", "vipplus", "vip", "joueur"]
for n in names:
    files[f"assets/chroma/textures/font/{n}.png"] = open(os.path.join(D, "ranks_v2", n + ".png"), "rb").read()
font = json.loads(files["assets/minecraft/font/default.json"])
for p in font["providers"]:
    if p.get("file", "").split("/")[-1][:-4] in names: p["ascent"], p["height"] = 7, 8
files["assets/minecraft/font/default.json"] = json.dumps(font, ensure_ascii=True, indent=1).encode()
buf = io.BytesIO()
with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as z:
    for p in sorted(files):
        zi = zipfile.ZipInfo(p, date_time=(2026, 1, 1, 0, 0, 0)); zi.compress_type = zipfile.ZIP_DEFLATED; z.writestr(zi, files[p])
data = buf.getvalue(); open(os.path.join(D, "ChromaEndless-Pack12.zip"), "wb").write(data)
print(hashlib.sha1(data).hexdigest())
