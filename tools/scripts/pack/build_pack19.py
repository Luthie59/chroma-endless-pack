"""pack19 = pack18 + the Citadelle Concert models, so players without the mod see the concert gear
(items in hand and the plugin's item-display stand-ins) as real 3D models.

Usage: python build_pack19.py <pack18.zip> <mod resources assets/concert dir> <out.zip>
"""
import os
import sys
import zipfile

src, concert, out = sys.argv[1:4]
added = 0
with zipfile.ZipFile(src) as zin, zipfile.ZipFile(out, "w", zipfile.ZIP_DEFLATED) as zout:
    for info in zin.infolist():
        zout.writestr(info, zin.read(info.filename))
    for sub in ("items", "models/block", "textures/block"):
        folder = os.path.join(concert, sub)
        for name in sorted(os.listdir(folder)):
            path = os.path.join(folder, name)
            if os.path.isfile(path):
                zout.write(path, "assets/concert/" + sub + "/" + name)
                added += 1
print("added", added, "files")
