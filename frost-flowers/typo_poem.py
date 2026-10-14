"""frost flowers — typo poem (20 x 20 cm)

Three sketches and one final composition, written as SVG. The visual
language follows the reference artwork: black / white planes, huge italic
letters cropped by the planes and the page edge, and the poem set as type on
wavy paths.

  sketch 1  the reference artwork itself, kept as is; only its broken text
            runs are re-set with the correct words on the same paths
  sketch 2  horizontal bands: "frost" cropped by a band, "you" cropped by
            the page, the poem on waves between them
  sketch 3  a diagonal plane; "petal" crosses it, inverting black/white
  final     four window panes: f | l·owers | the whole poem | y·o·u

usage: python3 typo_poem.py <font_dir> <reference.svg> <out_dir>
  reference.svg = the reference .ai converted with `pdftocairo -svg`
"""
import math, re, sys
from PIL import ImageFont

FONTDIR, REF_SVG, OUTDIR = sys.argv[1], sys.argv[2], sys.argv[3]

# Type pairings: (svg font attributes, file used to measure text widths).
# Each composition gets its own display face (big letters) and text face
# (the poem on paths). Sketch 1 keeps the reference's Arno Pro.
FACES = {
    "arno": ("font-family=\"'Arno Pro', 'EB Garamond', serif\" font-style=\"italic\"",
             "EBGaramond-Italic.ttf"),
    "bodoni": ("font-family=\"'Bodoni Moda', serif\" font-style=\"italic\" font-weight=\"500\"",
               "BodoniModa-DisplayItalic.ttf"),
    "cormorant": ("font-family=\"'Cormorant Garamond', serif\" font-style=\"italic\" font-weight=\"500\"",
                  "CormorantGaramond-MediumItalic.ttf"),
    "archivo": ("font-family=\"'Archivo Condensed', 'Archivo', sans-serif\" font-weight=\"800\"",
                "Archivo-CondensedExtraBold.ttf"),
    "plexmono": ("font-family=\"'IBM Plex Mono', monospace\" font-style=\"italic\"",
                 "IBMPlexMono-Italic.ttf"),
    "playfair": ("font-family=\"'Playfair Display', serif\" font-style=\"italic\" font-weight=\"700\"",
                 "PlayfairDisplay-BoldItalic.ttf"),
    "caslon": ("font-family=\"'Libre Caslon Text', serif\" font-style=\"italic\"",
               "LibreCaslonText-Italic.ttf"),
}
_metric = {k: ImageFont.truetype(FONTDIR + "/" + v[1], 1000) for k, v in FACES.items()}
TEXT_FACE = "arno"  # face used by tw()/on_path() for the composition being built

INK, PAPER, PANE = "#1a1a1a", "#ffffff", "#212121"
FONT = FACES["arno"][0]  # Arno Pro is the reference's typeface; EB Garamond the open fallback


def tw(s, size, face=None):
    """Advance width of a string at a font size (same unit as size)."""
    return _metric[face or TEXT_FACE].getlength(s) * size / 1000


def f(v):
    return f"{v:.2f}".rstrip("0").rstrip(".")


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


def smooth(pts):
    """Catmull-Rom through points -> cubic Bezier path data."""
    d = f"M{f(pts[0][0])} {f(pts[0][1])}"
    for i in range(len(pts) - 1):
        p0, p1, p2 = pts[max(i - 1, 0)], pts[i], pts[i + 1]
        p3 = pts[min(i + 2, len(pts) - 1)]
        c1 = (p1[0] + (p2[0] - p0[0]) / 6, p1[1] + (p2[1] - p0[1]) / 6)
        c2 = (p2[0] - (p3[0] - p1[0]) / 6, p2[1] - (p3[1] - p1[1]) / 6)
        d += f"C{f(c1[0])} {f(c1[1])} {f(c2[0])} {f(c2[1])} {f(p2[0])} {f(p2[1])}"
    return d


def plen(pts):
    return sum(math.dist(pts[i], pts[i + 1]) for i in range(len(pts) - 1))


class Doc:
    def __init__(self, name):
        self.name, self.defs, self.layers, self.n = name, [], [], 0

    def uid(self, p):
        self.n += 1
        return f"{p}{self.n}"

    def layer(self, lid, body, attrs=""):
        self.layers.append(f'<g id="{lid}" {attrs}>\n{body}\n</g>')

    def clip(self, cid, shape):
        self.defs.append(f'<clipPath id="{cid}">{shape}</clipPath>')

    def save(self, fn):
        svg = ('<svg xmlns="http://www.w3.org/2000/svg" width="200mm" height="200mm" viewBox="0 0 200 200">\n'
               f"<title>{self.name}</title>\n<defs>\n" + "\n".join(self.defs) + "\n</defs>\n"
               + "\n".join(self.layers) + "\n</svg>\n")
        open(f"{OUTDIR}/{fn}", "w").write(svg)


def wave(x0, y0, x1, y1, amp, cycles, phase, n=14):
    """Points of a wavy line from (x0, y0) to (x1, y1)."""
    L = math.dist((x0, y0), (x1, y1))
    ux, uy = (x1 - x0) / L, (y1 - y0) / L
    return [(x0 + ux * L * t - uy * amp * math.sin(phase + t * cycles * 2 * math.pi),
             y0 + uy * L * t + ux * amp * math.sin(phase + t * cycles * 2 * math.pi))
            for t in (k / (n - 1) for k in range(n))]


def on_path(doc, pts, text, size, fill, center=False):
    """Type on a path; shrinks the size only if the text would overrun the path."""
    pid = doc.uid("tp")
    doc.defs.append(f'<path id="{pid}" d="{smooth(pts)}"/>')
    L = plen(pts)
    s = min(size, size * L * 0.98 / tw(text, size))
    off = (L - tw(text, s)) / 2 if center else 0
    return (f'<text font-size="{s:.2f}" fill="{fill}"><textPath href="#{pid}" '
            f'startOffset="{off:.2f}">{text}</textPath></text>')


def big(x, y, size, ch, fill, rot=0, clip=None, extra=""):
    t = f' transform="rotate({f(rot)} {f(x)} {f(y)})"' if rot else ""
    c = f' clip-path="url(#{clip})"' if clip else ""
    return f'<text x="{f(x)}" y="{f(y)}" font-size="{size}" fill="{fill}"{t}{c}{extra}>{ch}</text>'


# ---------------------------------------------------------------------------
# SKETCH 1 — the reference, as is. Everything (planes, outlined f / y / l, the
# R, o, w, e, o, u, "frost") is taken from the reference unchanged; only the
# nine small text runs are re-set, on paths traced from their own glyphs.
# ---------------------------------------------------------------------------
REF_RUNS = [  # same phrases the reference placed on each path, with the
    # dropped spaces, ligatures and typos fixed. The first run sits under the
    # black panel in the reference (never visible), so it is left out.
    None,
    "The dawn city bus runs with its windows decked in some",
    "The harsher the dead of winter, those who rode",
    "their breath and their sighs met in secret",
    "this breathtaking beauty. As if I had wandered",
    "I move from seat to seat to look, and once again",
    "on its delicate and cold beauty. Whose desolate",
    "For no reason, carefully, with my breath",
    "I wipe away a single frost petal with my finger",
]


def reference():
    s = open(REF_SVG).read()
    size = {}
    for gid, d in re.findall(r'<g id="(glyph-\d+-\d+)">\s*<path d="([^"]*)"', s):
        nums = [abs(float(x)) for x in re.findall(r"-?\d+\.?\d*", d)]
        size[gid] = max(nums) if nums else 0
    pat = re.compile(r'<g fill="([^"]+)" fill-opacity="1">\s*<use xlink:href="#(glyph-\d+-\d+)" '
                     r'x="([-\d.]+)" y="([-\d.]+)"/>\s*</g>\n?')
    runs = []

    def drop(m):
        g, x, y = m.group(2), float(m.group(3)), float(m.group(4))
        if size.get(g, 99) >= 14 or x < 100:  # big letters and the "frost" label stay
            return m.group(0)
        if runs and math.dist(runs[-1][-1], (x, y)) <= 18:
            runs[-1].append((x, y))
        else:
            runs.append([(x, y)])
        return ""

    s = pat.sub(drop, s)
    assert len(runs) == len(REF_RUNS), len(runs)

    texts, defs = [], []
    for i, (pts, txt) in enumerate(zip(runs, REF_RUNS)):
        if txt is None:
            continue
        # thin the glyph origins into a smooth path, then extend it a little
        # along its end tangent so the corrected phrase has room
        pts = pts[::3] + ([pts[-1]] if (len(pts) - 1) % 3 else [])
        (ax, ay), (bx, by) = pts[-2], pts[-1]
        L = math.dist((ax, ay), (bx, by)) or 1
        need = max(0, tw(txt, 12, "arno") - plen(pts)) + 4
        pts.append((bx + (bx - ax) / L * need, by + (by - ay) / L * need))
        pid = f"refpath{i + 1}"
        defs.append(f'<path id="{pid}" d="{smooth(pts)}"/>')
        texts.append(f'<text font-size="12" fill="#ffffff"><textPath href="#{pid}">{txt}</textPath></text>')

    s = s.replace("</defs>", "\n".join(defs) + "\n</defs>", 1)
    layer = f'<g id="Poem_on_paths" {FONT}>\n' + "\n".join(texts) + "\n</g>\n"
    s = s.replace("</svg>", layer + "</svg>")
    s = re.sub(r'<svg ([^>]*?)width="[^"]*" height="[^"]*"', r'<svg \1width="200mm" height="200mm"', s, count=1)
    open(f"{OUTDIR}/frost-flowers_1_sketch-1.svg", "w").write(s)


# ---------------------------------------------------------------------------
# SKETCH 2 — horizontal bands (the bus window seen side-on).
# ---------------------------------------------------------------------------
def bands():
    global TEXT_FACE
    TEXT_FACE = "cormorant"
    doc = Doc("frost flowers — sketch 2")
    doc.clip("bandA", '<rect x="0" y="0" width="200" height="76"/>')
    doc.clip("bandC", '<rect x="0" y="124" width="200" height="76"/>')
    doc.layer("Planes", f'<rect width="200" height="200" fill="{PAPER}"/>'
              f'<rect width="200" height="76" fill="{PANE}"/>'
              f'<rect y="124" width="200" height="76" fill="{PANE}"/>')

    # crop: "frost" sliced by the bottom of the top band, "you" by the page
    t = [big(-2, 98, 112, "frost", PAPER, clip="bandA"),
         big(196, 9, 5, "frost", PAPER, extra=' text-anchor="end"'),
         big(110, 222, 116, "you", PAPER, clip="bandC"),
         big(196, 120.5, 5.5, "flowers", INK, extra=' text-anchor="end"')]
    doc.layer("Display_Type", "\n".join(t), FACES["bodoni"][0])

    p = []
    mid = [POEM[0] + " " + POEM[1], POEM[2] + " " + POEM[3], POEM[4] + " " + POEM[5],
           POEM[6] + " / " + POEM[7], POEM[8] + " " + POEM[9]]
    for i, line in enumerate(mid):
        y = 84 + i * 7.8
        p.append(on_path(doc, wave(6, y + 1.5, 194, y - 1.5, 1.6, 1.3, i * 1.1), line, 3.4, INK))
    low = POEM[10:17] + [POEM[17] + " / " + POEM[18], POEM[19]]
    for i, line in enumerate(low):
        y = 132 + i * 5.6
        p.append(on_path(doc, wave(6, y + 4, 104, y - 4, 1.4, 1.1, i * 0.9), line, 2.9, PAPER))
    p.append(on_path(doc, wave(6, 187, 104, 181, 1.2, 1.0, 0.4), POEM[20], 2.9, PAPER))
    p.append(on_path(doc, wave(6, 194, 104, 188, 1.2, 1.0, 1.4), POEM[21][:-5], 2.9, PAPER))
    doc.layer("Poem_on_paths", "\n".join(p), FACES["cormorant"][0])
    return doc


# ---------------------------------------------------------------------------
# SKETCH 3 — a diagonal plane; the word "petal" crosses it and inverts.
# ---------------------------------------------------------------------------
def diagonal():
    global TEXT_FACE
    TEXT_FACE = "plexmono"
    doc = Doc("frost flowers — sketch 3")
    plane = "M0 150L200 52V200H0Z"
    doc.clip("dark", f'<path d="{plane}"/>')
    doc.clip("light", '<path d="M0 0H200V52L0 150Z"/>')
    doc.layer("Planes", f'<rect width="200" height="200" fill="{PAPER}"/><path d="{plane}" fill="{PANE}"/>')

    ang = math.degrees(math.atan2(52 - 150, 200))  # slope of the edge
    t = [f'<g clip-path="url(#light)">{big(10, 160, 84, "petal", INK, ang)}</g>',
         f'<g clip-path="url(#dark)">{big(10, 160, 84, "petal", PAPER, ang)}</g>',
         big(196, 14, 5.5, "frost flowers", INK, extra=' text-anchor="end"'),
         big(196, 194, 40, "you.", PAPER, extra=' text-anchor="end"')]
    doc.layer("Display_Type", "\n".join(t), FACES["archivo"][0])

    ux, uy = math.cos(math.radians(ang)), math.sin(math.radians(ang))
    nx, ny = uy, -ux  # normal pointing up-left, into the white

    def lane(o, i):
        sx, sy = nx * o, 150 + ny * o
        pts = wave(sx - ux * 40, sy - uy * 40, sx + ux * 260, sy + uy * 260, 1.5, 1.6, i * 1.2, 30)
        return [q for q in pts if 2 <= q[0] <= 198 and 2 <= q[1] <= 198]

    p = []
    for i, line in enumerate(POEM[:10]):  # white corner, above the word, parallel to the edge
        pts = lane(100 - i * 4.0, i)
        if len(pts) > 3:
            p.append(on_path(doc, pts, line, 2.2, INK, center=True))
    for i, line in enumerate(POEM[10:20]):  # dark side
        pts = lane(-26 - i * 6.2, i)
        if len(pts) > 3:
            p.append(on_path(doc, pts, line, 3.0, PAPER, center=True))
    p.append(on_path(doc, wave(10, 190, 140, 184, 1.0, 1.0, 0.3), POEM[20], 2.6, PAPER))
    p.append(on_path(doc, wave(10, 196, 140, 191, 1.0, 1.0, 1.3), POEM[21][:-5], 2.6, PAPER))
    doc.layer("Poem_on_paths", "\n".join(p), FACES["plexmono"][0])
    return doc


# ---------------------------------------------------------------------------
# FINAL — four window panes: f | l·o·w·e·r·s | the whole poem | y·o·u
# ---------------------------------------------------------------------------
def panes():
    global TEXT_FACE
    TEXT_FACE = "caslon"
    doc = Doc("frost flowers — final")
    A, B, C, D = (0, 52), (52, 84), (84, 150), (150, 200)
    for k, (a, b) in zip("ABCD", (A, B, C, D)):
        doc.clip(f"clip{k}", f'<rect x="{a}" y="0" width="{b - a}" height="200"/>')
    doc.layer("Planes", f'<rect width="200" height="200" fill="{PAPER}"/>'
              f'<rect x="{A[0]}" width="{A[1] - A[0]}" height="200" fill="{PANE}"/>'
              f'<rect x="{C[0]}" width="{C[1] - C[0]}" height="200" fill="{PANE}"/>')

    t = [big(-18, 150, 190, "f", PAPER, clip="clipA"), big(4, 194, 6.2, "frost", PAPER),
         big(44, 236, 215, "l", INK, clip="clipB")]
    for ch, x, y, s, r in (("o", 58, 44, 11, -14), ("w", 70, 58, 9.5, 12), ("e", 57, 72, 10, -8),
                           ("r", 68, 86, 8.5, 18), ("s", 56, 99, 9, -20)):
        t.append(big(x, y, s, ch, INK, r))
    t += [big(138, 88, 128, "y", INK, clip="clipD"), big(166, 128, 44, "o", INK, clip="clipD"),
          big(149, 190, 104, "u", INK, clip="clipD"), big(153.5, 9, 4, "frost flowers", INK)]
    doc.layer("Display_Type", "\n".join(t), FACES["playfair"][0])

    p = []
    for i, line in enumerate(POEM):
        y = 12.5 + i * 8.45
        rise, amp, ph = (5.0 if i % 2 == 0 else 3.2), 1.1 + 0.5 * (i % 3), i * 1.3
        pts = wave(C[0] + 3.5, y + rise / 2, C[1] - 3.5, y - rise / 2, amp, 1.1, ph, 13)
        p.append(on_path(doc, pts, line, 2.55, PAPER, center=bool(i % 2)))
    doc.layer("Poem_on_paths", "\n".join(p), FACES["caslon"][0])
    return doc


if __name__ == "__main__":
    reference()
    bands().save("frost-flowers_1_sketch-2.svg")
    diagonal().save("frost-flowers_1_sketch-3.svg")
    panes().save("frost-flowers_2_final.svg")
    print("ok")
