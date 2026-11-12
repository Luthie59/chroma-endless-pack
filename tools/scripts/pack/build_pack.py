"""Build the Chroma Endless rank-icon resource pack (font glyphs)."""
import hashlib, io, json, os, struct, sys, zipfile, zlib

OUT = sys.argv[1]

def png(pixels):
    """pixels: list of rows of (r,g,b,a) tuples -> PNG bytes."""
    h = len(pixels); w = len(pixels[0])
    raw = b"".join(b"\x00" + b"".join(struct.pack("BBBB", *p) for p in row) for row in pixels)
    def chunk(t, d):
        c = struct.pack(">I", len(d)) + t + d
        return c + struct.pack(">I", zlib.crc32(t + d) & 0xFFFFFFFF)
    return (b"\x89PNG\r\n\x1a\n" + chunk(b"IHDR", struct.pack(">IIBBBBB", w, h, 8, 6, 0, 0, 0))
            + chunk(b"IDAT", zlib.compress(raw, 9)) + chunk(b"IEND", b""))

def hexc(s):
    s = s.lstrip("#"); return tuple(int(s[i:i+2], 16) for i in (0, 2, 4))

def shade(c, f):
    return tuple(max(0, min(255, int(v * f))) for v in c)

def render(art, palette):
    """art: list of strings. Letters map to palette colors; '.' transparent.
    Uppercase base letters get automatic bevel (light top-left, dark bottom-right)."""
    h = len(art); w = max(len(r) for r in art)
    grid = [r.ljust(w, ".") for r in art]
    out = []
    for y in range(h):
        row = []
        for x in range(w):
            ch = grid[y][x]
            if ch == ".":
                row.append((0, 0, 0, 0)); continue
            base = hexc(palette[ch.upper()])
            if ch.isupper():
                empty = lambda xx, yy: not (0 <= xx < w and 0 <= yy < h) or grid[yy][xx] == "."
                if empty(x, y - 1) or empty(x - 1, y):
                    base = shade(base, 1.25)
                elif empty(x, y + 1) or empty(x + 1, y):
                    base = shade(base, 0.72)
            row.append(base + (255,))
        out.append(row)
    return out

ICONS = {
    # glyph, file, art, palette
    "admin": ("", [
        "X...X...X",
        "XX.XXX.XX",
        "XXXXXXXXX",
        "XXXXXXXXX",
        "XrXXbXXrX",
        "XXXXXXXXX",
        ".XXXXXXX.",
        "DDDDDDDDD",
    ], {"X": "#FFC93C", "R": "#FF3B3B", "B": "#3BA4FF", "D": "#B8811A"}),
    "modo": ("", [
        "s.......s",
        ".s.....s.",
        "..s...s..",
        "...s.s...",
        "....s....",
        "...s.s...",
        ".HH...HH.",
        ".H.....H.",
        "h.......h",
    ], {"S": "#E6EEF7", "H": "#3D7BFF"}),
    "guide": ("", [
        "..XXXX..",
        "..XwwX..",
        "XXXwwXXX",
        "XwwwwwwX",
        "XwwwwwwX",
        "XXXwwXXX",
        "..XwwX..",
        "..XXXX..",
    ], {"X": "#E0A800", "W": "#FFE45C"}),
    "vipplus": ("", [
        "....X....",
        "...XXX...",
        "XXXXwXXXX",
        ".XXwwwXX.",
        "..XXwXX..",
        "..XXXXX..",
        ".XXX.XXX.",
        ".XX...XX.",
    ], {"X": "#32D2FF", "W": "#C8F5FF"}),
    "vip": ("", [
        "..XXXXX..",
        ".XwwXXXX.",
        "XXwXXXXXX",
        ".XXXXXXX.",
        "..XXXXX..",
        "...XXX...",
        "....X....",
    ], {"X": "#33E06B", "W": "#C9FFD9"}),
    "joueur": ("", [
        ".......s",
        "......s.",
        ".....s..",
        "....s...",
        ".h.s....",
        "..h.....",
        ".h.h....",
        "h.......",
    ], {"S": "#C9CED6", "H": "#8A6A45"}),
}

files = {}
providers = []
for name, (glyph, art, pal) in ICONS.items():
    # lowercase letters in art = flat color (no bevel) of the uppercase palette entry
    files[f"assets/chroma/textures/font/{name}.png"] = png(render(art, pal))
    providers.append({"type": "bitmap", "file": f"chroma:font/{name}.png",
                      "ascent": 7, "height": 8, "chars": [glyph]})

files["assets/minecraft/font/default.json"] = json.dumps({"providers": providers}, ensure_ascii=True, indent=2).encode()
files["pack.mcmeta"] = json.dumps({"pack": {
    "description": "§6§lChroma Endless §7- Logos des grades",
    "min_format": 75, "max_format": 75}}, ensure_ascii=False, indent=2).encode("utf-8")

# pack.png: admin crown scaled x8 on dark background (72x64 -> padded 72x72)
crown = render(ICONS["admin"][1], ICONS["admin"][2])
S = 8; size = 9 * S
bg = (24, 20, 28, 255)
icon = [[bg] * size for _ in range(size)]
for y, row in enumerate(crown):
    for x, p in enumerate(row):
        if p[3]:
            for dy in range(S):
                for dx in range(S):
                    icon[y * S + dy + S // 2][x * S + dx] = p
files["pack.png"] = png(icon)

buf = io.BytesIO()
with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as z:
    for path in sorted(files):
        zi = zipfile.ZipInfo(path, date_time=(2026, 1, 1, 0, 0, 0))
        zi.compress_type = zipfile.ZIP_DEFLATED
        z.writestr(zi, files[path])
data = buf.getvalue()
zip_path = os.path.join(OUT, "ChromaEndless-Logos.zip")
open(zip_path, "wb").write(data)
# preview: all icons side by side scaled x10
prev_icons = [render(a, p) for (_, a, p) in ICONS.values()]
S2 = 10; W = sum(len(i[0]) + 2 for i in prev_icons) * S2; H = 11 * S2
prev = [[(54, 57, 63, 255)] * W for _ in range(H)]
ox = S2
for ic in prev_icons:
    for y, row in enumerate(ic):
        for x, p in enumerate(row):
            if p[3]:
                for dy in range(S2):
                    for dx in range(S2):
                        prev[(y + 1) * S2 + dy][ox + x * S2 + dx] = p
    ox += (len(ic[0]) + 2) * S2
open(os.path.join(OUT, "preview.png"), "wb").write(png(prev))
print("zip", zip_path, len(data), "bytes sha1", hashlib.sha1(data).hexdigest())
