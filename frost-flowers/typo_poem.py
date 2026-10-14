"""frost flowers — typo poem (20 x 20 cm)

Three sketches and one final composition, written as SVG, built from the
typographic factors taught in the course (case, typeface, size,
weight, width, outline), in compositions of our own:

  sketch 1   the student's own reference artwork, kept as is (text runs re-set)
  sketch 2   "flow / ers" and "you": huge heavy words cropped into one mass
  sketch 3   a huge bright "you" against a dark vertical "flowers"
  final      sketch 2 refined; the poem's last two lines lit

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
# REFERENCE — the reference, as is. Everything (planes, outlined f / y / l, the
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
# The compositions below are driven by the principles of visual grammar
# (balance, emphasis, contrast, harmony, unity, rhythm, proportion,
# movement), not by the poem's imagery; the poem is the material.
#
# Shared system (unity):
#   * grid: 12 mm margins, 6 columns of 26 mm with 4 mm gutters
#   * proportion: every size comes from one modular scale, ratio 1.5
#   * one accent colour, used once per page (emphasis by colour point)
# ---------------------------------------------------------------------------
RED = "#e0322b"
M, COL, GUT = 12, 26, 4
SCALE = [round(2.6 * 1.5 ** k, 2) for k in range(11)]  # 2.6 3.9 5.85 8.78 13.16 19.74 ...


def colx(n):
    """Left edge (mm) of grid column n (0-5)."""
    return M + n * (COL + GUT)


def arc_pts(x0, y0, x1, y1, bulge, n=16):
    """A gentle arc from (x0, y0) to (x1, y1), bulging `bulge` mm upward."""
    pts = []
    for k in range(n):
        t = k / (n - 1)
        x, y = x0 + (x1 - x0) * t, y0 + (y1 - y0) * t
        pts.append((x, y - bulge * 4 * t * (1 - t)))
    return pts


def circle_d(cx, cy, r):
    """Closed circle path starting at the left, running clockwise (over the top)."""
    return (f"M{f(cx - r)} {f(cy)}A{f(r)} {f(r)} 0 1 1 {f(cx + r)} {f(cy)}"
            f"A{f(r)} {f(r)} 0 1 1 {f(cx - r)} {f(cy)}")


# ---------------------------------------------------------------------------
# Typographic factors applied directly to the letters (case, typeface, size,
# weight, width, outline) — the techniques from the course, in compositions
# of our own.
# ---------------------------------------------------------------------------
import numpy as np
from PIL import Image, ImageDraw

GARAMOND = "font-family=\"'EB Garamond', serif\""
STEPS = 8  # Archivo instances: width 62→125, weight 100→900
_step = [ImageFont.truetype(f"{FONTDIR}/ArchivoStep{k}.ttf", 1000) for k in range(STEPS)]
_garamond = ImageFont.truetype(FONTDIR + "/EBGaramond-Regular.ttf", 1000)


def tw_g(s, size):
    return _garamond.getlength(s) * size / 1000


def offset_pts(pts, d):
    """Offset a polyline by d mm along its normal (positive = right of travel)."""
    out = []
    for i, (x, y) in enumerate(pts):
        (ax, ay), (bx, by) = pts[max(i - 1, 0)], pts[min(i + 1, len(pts) - 1)]
        L = math.dist((ax, ay), (bx, by)) or 1
        nx, ny = -(by - ay) / L, (bx - ax) / L
        out.append((x + nx * d, y + ny * d))
    return out


def sample(pts, n=120):
    """Resample a Catmull-Rom curve through pts into n points."""
    out = []
    for i in range(len(pts) - 1):
        p0, p1, p2 = pts[max(i - 1, 0)], pts[i], pts[i + 1]
        p3 = pts[min(i + 2, len(pts) - 1)]
        for k in range(n // (len(pts) - 1)):
            t = k / (n // (len(pts) - 1))
            out.append(tuple(0.5 * ((2 * p1[j]) + (-p0[j] + p2[j]) * t
                                    + (2 * p0[j] - 5 * p1[j] + 4 * p2[j] - p3[j]) * t * t
                                    + (-p0[j] + 3 * p1[j] - 3 * p2[j] + p3[j]) * t ** 3) for j in (0, 1)))
    out.append(pts[-1])
    return out


# the poem's dark mood: a cold near-black ground, type that surfaces from it
NIGHT, DIM, MIST, FROST = "#111418", "#3d434a", "#7b828a", "#e9ecee"


def mix(c0, c1, t):
    a = [int(c0[i:i + 2], 16) for i in (1, 3, 5)]
    b = [int(c1[i:i + 2], 16) for i in (1, 3, 5)]
    return "#" + "".join(f"{round(x + (y - x) * t):02x}" for x, y in zip(a, b))


def gradient_on_path(doc, pts, text, s0, s1):
    """Type on a path whose letters grow in size, weight and width as they go,
    rising out of the dark from dim grey to frost white."""
    pid = doc.uid("grad")
    doc.defs.append(f'<path id="{pid}" d="{smooth(pts)}"/>')
    spans, n = [], len(text)
    for i, ch in enumerate(text):
        t = i / (n - 1)
        k = min(STEPS - 1, int(t * STEPS))
        size = s0 * (s1 / s0) ** t
        ch = "&#160;" if ch == " " else ch
        spans.append(f'<tspan font-family="ArchivoStep{k}" font-size="{size:.2f}" '
                     f'fill="{mix(DIM, FROST, t ** 0.8)}">{ch}</tspan>')
    return f'<text><textPath href="#{pid}">{"".join(spans)}</textPath></text>'


# ---------------------------------------------------------------------------
# MASS — the key words of the poem, "flowers" and "you", set huge in a heavy
# face, cropped by the page and overlapping into one dark block; the poem runs
# across them on waves in a stronger, larger text face.
# ---------------------------------------------------------------------------
BLACK = "font-family=\"'PlayfairBlack', 'Playfair Display'\" font-style=\"italic\" font-weight=\"900\""
TEXT = "font-family=\"'CaslonBold', 'Libre Caslon Text'\" font-style=\"italic\" font-weight=\"700\""
_black = ImageFont.truetype(FONTDIR + "/PlayfairDisplay-BlackItalic.ttf", 1000)
_text = ImageFont.truetype(FONTDIR + "/LibreCaslonText-BoldItalic.ttf", 1000)
SHADE1, SHADE2, LINE = "#2a3036", "#363d45", "#aeb5bc"


def tw_t(s, size):
    return _text.getlength(s) * size / 1000


def word(x, y, size, txt, fill, ls=0, extra=""):
    return (f'<text x="{f(x)}" y="{f(y)}" font-size="{size}" fill="{fill}" letter-spacing="{ls}" '
            f'{BLACK}{extra}>{txt}</text>')


def wave_line(doc, x0, y, x1, line, size, fill, amp=1.0, phase=0.0, center=False, shift=0.0):
    pts = wave(x0, y + 0.8, x1, y - 0.8, amp, 1.2, phase, 16)
    pid = doc.uid("wl")
    doc.defs.append(f'<path id="{pid}" d="{smooth(pts)}"/>')
    L = plen(pts)
    s = min(size, size * L * 0.98 / tw_t(line, size))
    off = (L - tw_t(line, s)) / 2 if center else min(shift, max(0.0, L - tw_t(line, s)))
    return (f'<text font-size="{s:.2f}" fill="{fill}"><textPath href="#{pid}" '
            f'startOffset="{off:.2f}">{line}</textPath></text>')


# ---------------------------------------------------------------------------
# SKETCH 2 / FINAL — "flow / ers" + "you"
# "flow" and "ers" in Playfair Black Italic, 150 mm, overlapping and cropped
# on three sides: two dark tones fused into one mass. A bright "you" breaks
# in from the lower right corner. The poem waves across the mass.
# ---------------------------------------------------------------------------
def mass_flowers(final=False):
    doc = Doc("frost flowers — final" if final else "frost flowers — sketch 2")
    doc.layer("Ground", f'<rect width="200" height="200" fill="{NIGHT}"/>')
    m = [word(-14, 112, 150, "flow", SHADE1, -4),
         word(46, 214, 150, "ers", SHADE2, -4),
         word(98, 204, 92, "you", FROST, -2)]
    doc.layer("Mass", "\n".join(m))

    p = []
    for i, line in enumerate(POEM[:16]):
        y = 16 + i * 6.6
        p.append(wave_line(doc, 10, y, 192, line, 3.4, LINE, 1.0, i * 0.8, center=bool(i % 2)))
    for k, line in enumerate(POEM[16:20]):
        y = 130 + k * 6.6
        p.append(wave_line(doc, 10, y, 96, line, 3.2, LINE, 0.9, k * 0.9))
    lit = FROST if final else LINE
    for k, line in enumerate(POEM[20:]):
        y = 162 + k * 6.6
        p.append(wave_line(doc, 10, y, 96, line, 3.2, lit, 0.9, k * 0.9 + 2))
    doc.layer("Poem_on_paths", "\n".join(p), TEXT)
    if final:
        doc.layer("Title", f'<text x="10" y="196" font-size="3.4" fill="{MIST}" {TEXT}>frost flowers</text>')
    return doc


# ---------------------------------------------------------------------------
# SKETCH 3 — "you" against "flowers"
# A huge bright "you" sunk into the bottom edge; behind it "flowers" runs up
# the right edge in a dark tone, cropped top and bottom. The poem waves over
# the upper half.
# ---------------------------------------------------------------------------
def mass_you():
    doc = Doc("frost flowers — sketch 3")
    doc.layer("Ground", f'<rect width="200" height="200" fill="{NIGHT}"/>')
    m = [f'<text x="0" y="0" font-size="118" fill="{SHADE2}" letter-spacing="-4" {BLACK} '
         f'transform="translate(206 214) rotate(-90)">flowers</text>',
         word(-10, 226, 200, "you", "#dfe3e6", -6)]
    doc.layer("Mass", "\n".join(m))
    p = []
    for i, line in enumerate(POEM):  # starts ripple along a wave: no flush left edge
        y = 11 + i * 4.85
        p.append(wave_line(doc, 8, y, 156, line, 3.1, LINE, 0.8, i * 0.7,
                           shift=22 + 20 * math.sin(i * 0.5)))
    doc.layer("Poem_on_paths", "\n".join(p), TEXT)
    return doc


if __name__ == "__main__":
    reference()  # sketch 1: the student's own work, as is
    mass_flowers().save("frost-flowers_1_sketch-2.svg")
    mass_you().save("frost-flowers_1_sketch-3.svg")
    mass_flowers(final=True).save("frost-flowers_2_final.svg")
    print("ok")
