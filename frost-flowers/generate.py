import math, random, sys
from PIL import ImageFont
FONTDIR = sys.argv[1]; OUT = sys.argv[2]
ital = ImageFont.truetype(FONTDIR + "/EBGaramond-Italic.ttf", 1000)
def tw(s, size):  # text width in mm
    return ital.getlength(s) * size / 1000

POEM = """The dawn city bus
runs with its windows decked in some dazzling finery.
The harsher the dead of winter,
the more vividly the frost flowers bloom.
Those who rode this bus yesterday
maidens and bachelors, children and grown-ups,
hairdressers, salesmen, housemaids, the jobless
their breath and their sighs
met in secret overnight and brought forth
this flashing, breathtaking beauty.
As if I had wandered into some exhibition,
I move from seat to seat to look,
and once again I am drunk on a single petal,
on its delicate and cold beauty.
Whose desolate sigh was this?
What warm heart breathed out this breath of passion?
For no reason, carefully, with my breath and my finger,
I wipe away a single frost petal
and press my forehead to the glass.
A haggard face glimmers in the rattling window
friend, you walked the road beside me for so long,
and now I am not even allowed to visit you.""".split("\n")

# strips (mm): A black | B white | C black(poem) | D white
A = (0, 52); B = (52, 84); C = (84, 150); D = (150, 200)
INK = "#1a1a1a"; PAPER = "#ffffff"; FROST_D = "#ffffff"; FROST_L = "#9aa6ad"
WIPE = (117, 158, 15, 7)  # cx, cy, rx, ry : the wiped petal on the window

random.seed(7)
def f(v): return f"{v:.2f}".rstrip("0").rstrip(".")

# ---------- frost (dendritic crystals) ----------
def dendrite(x, y, ang, length, depth, segs):
    ex, ey = x + math.cos(ang) * length, y + math.sin(ang) * length
    segs.append((x, y, ex, ey, depth))
    if depth <= 0 or length < 0.6:
        return
    n = max(2, int(length / 1.1))
    for i in range(1, n):
        t = i / n + random.uniform(-0.05, 0.05)
        bx, by = x + (ex - x) * t, y + (ey - y) * t
        bl = length * (1 - t) * random.uniform(0.25, 0.65)
        for s in (-1, 1):
            if random.random() < 0.7:
                dendrite(bx, by, ang + s * math.radians(60 + random.uniform(-6, 6)), bl, depth - 1, segs)

def frost_flower(cx, cy, r, segs, arms=None):
    arms = arms or random.choice([5, 6, 7, 8])
    rot = random.uniform(0, math.pi)
    for k in range(arms):
        a = rot + k * 2 * math.pi / arms + random.uniform(-0.25, 0.25)
        dendrite(cx, cy, a, r * random.uniform(0.45, 1.15), 3, segs)

def fern(x, y, ang, length, segs):
    # long feathery frost growing in from the window frame
    pts = [(x, y)]; a = ang
    for i in range(int(length / 2)):
        a += random.uniform(-0.22, 0.22)
        nx, ny = pts[-1][0] + math.cos(a) * 2, pts[-1][1] + math.sin(a) * 2
        segs.append((pts[-1][0], pts[-1][1], nx, ny, 3)); pts.append((nx, ny))
        rem = 1 - i / (length / 2)
        for s in (-1, 1):
            if random.random() < 0.9:
                dendrite(nx, ny, a + s * math.radians(random.uniform(45, 65)), (4.5 * rem + 0.6) * random.uniform(0.6, 1.2), 2, segs)

def in_wipe(x, y):
    cx, cy, rx, ry = WIPE
    return ((x - cx) / rx) ** 2 + ((y - cy) / ry) ** 2 < 1

def segs_to_path(segs, skip_wipe=False):
    d = []
    for x1, y1, x2, y2, dep in segs:
        if skip_wipe and (in_wipe(x1, y1) or in_wipe(x2, y2)):
            continue
        d.append(f"M{f(x1)} {f(y1)}L{f(x2)} {f(y2)}")
    return "".join(d)

def frost_group(strip, seeds_flowers, seeds_ferns, colour, width, opacity, skip_wipe=False):
    segs = []
    for (cx, cy, r) in seeds_flowers: frost_flower(cx, cy, r, segs)
    for (x, y, a, l) in seeds_ferns: fern(x, y, a, l, segs)
    thick = [s for s in segs if s[4] >= 2]; thin = [s for s in segs if s[4] < 2]
    return (f'<path d="{segs_to_path(thick, skip_wipe)}" stroke="{colour}" stroke-width="{width}" opacity="{opacity}"/>'
            f'<path d="{segs_to_path(thin, skip_wipe)}" stroke="{colour}" stroke-width="{width*0.6:.3f}" opacity="{opacity*0.8:.2f}"/>')

# ---------- poem on wavy paths ----------
def smooth(pts):
    d = f"M{f(pts[0][0])} {f(pts[0][1])}"
    for i in range(len(pts) - 1):
        p0 = pts[max(i - 1, 0)]; p1 = pts[i]; p2 = pts[i + 1]; p3 = pts[min(i + 2, len(pts) - 1)]
        c1 = (p1[0] + (p2[0] - p0[0]) / 6, p1[1] + (p2[1] - p0[1]) / 6)
        c2 = (p2[0] - (p3[0] - p1[0]) / 6, p2[1] - (p3[1] - p1[1]) / 6)
        d += f"C{f(c1[0])} {f(c1[1])} {f(c2[0])} {f(c2[1])} {f(p2[0])} {f(p2[1])}"
    return d

SIZE = 2.55
defs, poem = [], []
top, gap = 12.5, 8.45
for i, line in enumerate(POEM):
    y = top + i * gap
    w = tw(line, SIZE)
    rise = 5.0 if i % 2 == 0 else 3.2
    amp = 1.1 + 0.5 * (i % 3)
    phase = i * 1.3
    x0 = C[0] + 3.5
    span = C[1] - 3.5 - x0
    pts = []
    for k in range(13):
        t = k / 12
        pts.append((x0 + span * t, y + rise / 2 - rise * t + amp * math.sin(phase + t * math.pi * 2.2)))
    pid = f"line{i+1:02d}"
    defs.append(f'<path id="{pid}" d="{smooth(pts)}" fill="none"/>')
    # measure path length to keep the line inside the strip
    L = sum(math.dist(pts[k], pts[k + 1]) for k in range(12))
    size = SIZE if w < L * 0.97 else SIZE * L * 0.97 / w
    poem.append(f'<text font-size="{size:.2f}"><textPath href="#{pid}" startOffset="{(L - tw(line, size)) / 2 * (i % 2):.2f}">{line}</textPath></text>')

# ---------- assemble ----------
o = []
o.append(f'''<svg xmlns="http://www.w3.org/2000/svg" xmlns:xlink="http://www.w3.org/1999/xlink" width="200mm" height="200mm" viewBox="0 0 200 200">
<title>frost flowers</title>
<defs>
<clipPath id="clipA"><rect x="{A[0]}" y="0" width="{A[1]-A[0]}" height="200"/></clipPath>
<clipPath id="clipB"><rect x="{B[0]}" y="0" width="{B[1]-B[0]}" height="200"/></clipPath>
<clipPath id="clipC"><rect x="{C[0]}" y="0" width="{C[1]-C[0]}" height="200"/></clipPath>
<clipPath id="clipD"><rect x="{D[0]}" y="0" width="{D[1]-D[0]}" height="200"/></clipPath>
{"".join(defs)}
</defs>''')
o.append(f'<g id="Background"><rect width="200" height="200" fill="{PAPER}"/>'
         f'<rect x="{A[0]}" width="{A[1]-A[0]}" height="200" fill="{INK}"/>'
         f'<rect x="{C[0]}" width="{C[1]-C[0]}" height="200" fill="{INK}"/></g>')

FAM = "font-family=\"'EB Garamond', 'Adobe Garamond Pro', Garamond, serif\" font-style=\"italic\""
# Frost layer
o.append('<g id="Frost" fill="none" stroke-linecap="round">')
o.append('<g clip-path="url(#clipA)">' + frost_group(A,
    [(14, 150, 7), (40, 172, 5), (6, 188, 4), (24, 192, 3), (44, 140, 3)],
    [(0, 200, -1.0, 52), (0, 120, -0.2, 26), (52, 200, -2.3, 34), (30, 200, -1.6, 26), (0, 0, 0.9, 18)],
    FROST_D, 0.11, 0.5) + '</g>')
o.append('<g clip-path="url(#clipB)">' + frost_group(B,
    [(74, 22, 5), (56, 8, 3), (80, 60, 3)],
    [(84, 0, 2.2, 30), (52, 0, 0.9, 22), (84, 40, 2.8, 14)],
    FROST_L, 0.1, 0.75) + '</g>')
o.append('<g clip-path="url(#clipC)">' + frost_group(C,
    [(96, 6, 5), (142, 196, 6), (134, 160, 5), (100, 160, 4.5), (117, 150, 4), (121, 167, 4), (146, 120, 3)],
    [(84, 200, -0.8, 34), (150, 0, 2.5, 30), (150, 200, -2.0, 40), (84, 0, 0.7, 16), (84, 150, -0.3, 14)],
    FROST_D, 0.09, 0.35, skip_wipe=True) + '</g>')
o.append('<g clip-path="url(#clipD)">' + frost_group(D,
    [(192, 110, 4), (160, 140, 3), (196, 8, 3)],
    [(200, 160, -2.6, 26), (200, 0, 2.0, 20), (150, 140, -0.4, 12)],
    FROST_L, 0.1, 0.75) + '</g>')
o.append('</g>')

# Display type layer: f | l + o w e r s | (poem) | y o u
o.append(f'<g id="Display_Type" {FAM}>')
o.append(f'<g clip-path="url(#clipA)"><text x="-30" y="168" font-size="235" fill="{PAPER}">f</text>'
         f'<text x="4" y="40" font-size="6.2" fill="{PAPER}">frost</text></g>')
o.append(f'<g clip-path="url(#clipB)"><text x="44" y="236" font-size="215" fill="{INK}">l</text></g>')
# o w e r s drifting down like petals across strip B
petals = [("o", 58, 44, 11, -14), ("w", 70, 58, 9.5, 12), ("e", 57, 72, 10, -8), ("r", 68, 86, 8.5, 18), ("s", 56, 99, 9, -20)]
for ch, x, y, s, r in petals:
    o.append(f'<text x="{x}" y="{y}" font-size="{s}" fill="{INK}" transform="rotate({r} {x} {y})">{ch}</text>')
o.append(f'<g clip-path="url(#clipD)"><text x="138" y="88" font-size="128" fill="{INK}">y</text>'
         f'<text x="166" y="128" font-size="44" fill="{INK}">o</text>'
         f'<text x="149" y="190" font-size="104" fill="{INK}">u</text></g>')
o.append('</g>')

# Poem layer
o.append(f'<g id="Poem" {FAM} fill="{PAPER}" clip-path="url(#clipC)">' + "".join(poem) + '</g>')

# The wiped petal: a breath-cleared oval, faint rim
cx, cy, rx, ry = WIPE
o.append(f'<g id="Wiped_Petal"><ellipse cx="{cx}" cy="{cy}" rx="{rx}" ry="{ry}" fill="none" stroke="{PAPER}" stroke-width="0.12" stroke-dasharray="0.4 0.9" opacity="0.6"/></g>')

# Title
o.append(f'<g id="Title" {FAM}><text x="153.5" y="9" font-size="4" fill="{INK}" letter-spacing="0.12">frost flowers</text></g>')
o.append('</svg>')
open(OUT, "w").write("\n".join(o))
print("ok")
