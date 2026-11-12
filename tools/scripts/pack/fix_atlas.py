import zipfile, io, json, hashlib, sys, os
D = sys.argv[1]; src = os.path.join(D, "ChromaEndless-Pack5.zip"); out = os.path.join(D, "ChromaEndless-Pack6.zip")
files = {}
with zipfile.ZipFile(src) as z:
    for n in z.namelist(): files[n] = z.read(n)
files["assets/chroma/textures/item/marble_block.png"] = files["assets/minecraft/textures/block/quartz_block_bottom.png"]
fixed = []
for n in list(files):
    if n.startswith("assets/chroma/models/item/") and n.endswith(".json"):
        m = json.loads(files[n]); tex = m.get("textures", {})
        if any(v.startswith("minecraft:block/") for v in tex.values()):
            for k, v in tex.items():
                if v == "minecraft:block/quartz_block_bottom": tex[k] = "chroma:item/marble_block"
            files[n] = json.dumps(m, indent=1).encode(); fixed.append(n.split("/")[-1])
# sanity: no model may mix namespaces/atlases any more
bad = []
for n in files:
    if n.startswith("assets/chroma/models/item/"):
        t = json.loads(files[n]).get("textures", {})
        atl = {("block" if v.split(":")[1].startswith("block/") else "item") for v in t.values()}
        if len(atl) > 1: bad.append(n)
        for v in t.values():
            ns, p = v.split(":"); f = f"assets/{ns}/textures/{p}.png"
            if ns == "chroma" and f not in files: bad.append(n + " missing " + v)
buf = io.BytesIO()
with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as z:
    for p in sorted(files):
        zi = zipfile.ZipInfo(p, date_time=(2026, 1, 1, 0, 0, 0)); zi.compress_type = zipfile.ZIP_DEFLATED; z.writestr(zi, files[p])
data = buf.getvalue(); open(out, "wb").write(data)
print("fixed", fixed, "bad", bad, "sha1", hashlib.sha1(data).hexdigest(), len(data))
