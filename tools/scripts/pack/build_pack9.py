import io, json, hashlib, sys, os, zipfile
import numpy as np
from PIL import Image
sys.argv = [sys.argv[0], sys.argv[1]]
D = sys.argv[1]
src = os.path.join(D, "ChromaEndless-Pack8.zip"); out = os.path.join(D, "ChromaEndless-Pack9.zip")
ns = {}
code = open(os.path.join(D, "build_pack8.py"), encoding="utf-8").read().split("TEX = {")[0]
exec(code, ns)
painted, to_im = ns["painted"], ns["to_im"]
def side_tex():
    H, W = 128, 64
    col = painted(H, W, 3)
    def panel(x0, y0, x1, y1):
        col[y0:y1, x0:x1] = painted(y1 - y0, x1 - x0, x0 * 5 + y0) * .78
        col[y0:y0 + 1, x0:x1] *= .7; col[y0:y1, x0:x0 + 1] *= .7
        col[y1 - 1:y1, x0:x1] *= 1.3; col[y0:y1, x1 - 1:x1] *= 1.25
    col[:, 29:35] *= 1.06                                  # solid centre stile (no door gap)
    rows = [(6, 34), (38, 66), (70, 98), (102, 124)]
    for i, (y0, y1) in enumerate(rows):
        for (x0, x1) in ((5, 28), (36, 59)):
            if i == 0:
                col[y0:y1, x0:x1] = np.array([236, 236, 230.])
                for px in range(2):
                    for py in range(3):
                        a0 = x0 + 2 + px * 11; b0 = y0 + 2 + py * 9
                        col[b0:b0 + 7, a0:a0 + 9] = np.array([255, 232, 170.]) * np.linspace(1.0, .82, 7)[:, None, None]
            else:
                panel(x0, y0, x1, y1)
    col[:, :1] *= .7; col[:, -1:] *= .7
    return to_im(col)
files = {}
with zipfile.ZipFile(src) as z:
    for n in z.namelist(): files[n] = z.read(n)
b = io.BytesIO(); side_tex().save(b, "PNG", optimize=True); files["assets/chroma/textures/item/box_side.png"] = b.getvalue()
m = json.loads(files["assets/chroma/models/item/portal_box.json"])
m["textures"]["x"] = "chroma:item/box_side"
changed = 0
for e in m["elements"]:
    for fc in ("south", "east", "west"):
        f = e["faces"].get(fc)
        if f and f["texture"] == "#w": f["texture"] = "#x"; changed += 1
files["assets/chroma/models/item/portal_box.json"] = json.dumps(m, indent=1).encode()
buf = io.BytesIO()
with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as z:
    for p in sorted(files):
        zi = zipfile.ZipInfo(p, date_time=(2026, 1, 1, 0, 0, 0)); zi.compress_type = zipfile.ZIP_DEFLATED; z.writestr(zi, files[p])
data = buf.getvalue(); open(out, "wb").write(data)
side_tex().resize((128, 256), Image.NEAREST).save(os.path.join(D, "box_side_preview.png"))
print("faces switched", changed, "sha1", hashlib.sha1(data).hexdigest(), len(data))
