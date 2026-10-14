"""frost flowers — typo poem (20 x 20 cm)

Three sketches and one final composition, written as SVG, built from the
experimental typography examples in the course deck:

  sketch 1   the student's own reference artwork, kept as is (text runs re-set)
  sketch 2   staircase of lines landing on the dot of a big i
  sketch 3   f r o s t tumbling on a dark ground, lines broken around letters
  final      sketch 2 completed: a line from the i's stem, a mirrored line

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
# Experimental typography, after the typo-poem examples in the course deck:
# generous white space, small classic text, one or two big letters, and a few
# deliberate plays — a staircase of lines landing on a letter, a mirrored
# line, words broken around letters, scale pairs, a vertical edge caption and
# a small crossed-word marker in the corner.
# ---------------------------------------------------------------------------
GARAMOND = "font-family=\"'EB Garamond', serif\""
GREY = "#8c8c8c"


def tw_g(s, size):
    return _garamond.getlength(s) * size / 1000


_garamond = ImageFont.truetype(FONTDIR + "/EBGaramond-Regular.ttf", 1000)


def edge_caption(lines, fill=INK):
    """Small vertical caption running up the right edge, as in the examples."""
    out = []
    for k, line in enumerate(lines):
        x = 200 - M + 1.5 - (len(lines) - 1 - k) * 3.2
        out.append(f'<text x="0" y="0" font-size="2.2" fill="{fill}" {GARAMOND} '
                   f'transform="translate({f(x)} {200 - M}) rotate(-90)">{line}</text>')
    return "\n".join(out)


def cross_marker(fill=INK, at=(22, 178)):
    """Two tiny words crossing at one point (bottom left by default)."""
    cx, cy, s, ls = at[0], at[1], 2.6, 0.5
    out = []
    for word, rot in (("frost", -28), ("flowers", 62)):
        # both words share their "o": shift each so that letter sits on the crossing
        pre = tw_g(word[:2], s) + 2 * ls + tw_g("o", s) / 2
        out.append(f'<text x="{f(cx - pre)}" y="{f(cy + s * 0.25)}" font-size="{s}" fill="{fill}" {GARAMOND} '
                   f'letter-spacing="{ls}" transform="rotate({rot} {cx} {cy})">{word}</text>')
    return "\n".join(out)


# ---------------------------------------------------------------------------
# SKETCH 2 / FINAL — "staircase to i"
# Lines 1-14 step down and to the right; the last one ends exactly on the dot
# of a big Bodoni "i" (the line's full stop becomes the letter's dot).
# Final adds: a hairline sentence running out from the i's stem (the "H t"
# page), and one line set twice — upright and mirrored — like a reflection.
# ---------------------------------------------------------------------------
def staircase(final=False):
    doc = Doc("frost flowers — final" if final else "frost flowers — sketch 2")
    doc.layer("Paper", f'<rect width="200" height="200" fill="{PAPER}"/>')
    size, x0, y0, dx, dy = 2.9, 22, 30, 4.6, 5.0
    t, last = [], None
    for i, line in enumerate(POEM[:14]):
        x, y = x0 + i * dx, y0 + i * dy + (6 if i == 13 else 0)  # a pause before the landing
        txt = line.rstrip(".,")
        t.append(f'<text x="{f(x)}" y="{f(y)}" font-size="{size}">{txt}</text>')
        last = (x + tw_g(txt, size), y)
    doc.layer("Staircase", "\n".join(t), f'{GARAMOND} fill="{INK}"')

    # the big i: place it so its dot sits just after the last line, on its x-height
    S = 56  # the dot becomes the last line's full stop, sitting on its baseline
    dot_cx, dot_cy = last[0] + 0.067 * S + 0.8, last[1] - 0.067 * S
    ix, iy = dot_cx - 0.237 * S, dot_cy + 0.6885 * S
    doc.layer("Big_i", big(ix, iy, S, "i", INK), FACES["bodoni"][0])

    e = []
    if final:
        # a single thin sentence leaves the foot of the stem and runs to the margin
        run = POEM[14]
        sx = ix + 0.30 * S + 3
        rs = min(2.6, (200 - M - 10 - sx) / tw_g(run, 1))
        e.append(f'<text x="{f(sx)}" y="{f(iy - 0.6)}" font-size="{rs:.2f}" {GARAMOND} fill="{INK}">{run}</text>')
        # mirrored line: upright, then flipped about its baseline
        my, ms, mx = 172, 6.2, 22
        for k, line in enumerate(POEM[15:17]):
            e.append(f'<text x="{mx}" y="{my - 16 + k * 3.6}" font-size="2.3" {GARAMOND} fill="{INK}">{line}</text>')
        e.append(f'<text x="{mx}" y="{my}" font-size="{ms}" {GARAMOND} fill="{INK}">{POEM[17]}</text>')
        e.append(f'<text x="{mx + 9}" y="{my}" font-size="{ms}" {GARAMOND} fill="{INK}" '
                 f'transform="translate(0 {2 * my}) scale(1 -1)">{POEM[18]}</text>')
        e.append(f'<text x="{mx}" y="{my + 14}" font-size="2.2" {GARAMOND} fill="{INK}">{POEM[19]}</text>')
    doc.layer("Plays", "\n".join(e))
    doc.layer("Edge_Caption", edge_caption(POEM[20:] if final else POEM[14:22:2]))
    doc.layer("Marker", cross_marker(at=(22, 20) if final else (22, 178)))
    return doc


# ---------------------------------------------------------------------------
# SKETCH 3 — "f r o s t" on a dark ground
# A huge white f cropped at the top right. The letters r, o, s, t tumble
# diagonally, shrinking; beside each, a few small grey lines of the poem are
# broken open around the letter. Along the bottom, "flowers" is scattered in
# lower/upper-case pairs (fF lL oO ...), as on the "w o r d" page.
# ---------------------------------------------------------------------------
def scatter():
    doc = Doc("frost flowers — sketch 3")
    BG = "#1b1b1b"
    doc.layer("Ground", f'<rect width="200" height="200" fill="{BG}"/>')
    doc.layer("Big_f", big(118, 150, 210, "f", PAPER), FACES["playfair"][0])

    letters = [("r", 34, 52, 15), ("o", 70, 92, 12), ("s", 52, 128, 10), ("t", 96, 150, 8)]
    blocks = [POEM[0:4], POEM[4:8], POEM[8:12], POEM[12:16]]
    t, g = [], []
    for (ch, x, y, s), lines in zip(letters, blocks):
        t.append(big(x, y, s, ch, PAPER))
        gap = tw(ch, s, "playfair") + 3
        for k, line in enumerate(lines):
            ly = y - s * 0.55 + k * 3.4
            words = line.split()
            cut = max(1, len(words) // 2)
            left, right = " ".join(words[:cut]), " ".join(words[cut:])
            g.append(f'<text x="{f(x - 1.5)}" y="{f(ly)}" font-size="2.3" text-anchor="end">{left}</text>')
            g.append(f'<text x="{f(x + gap)}" y="{f(ly)}" font-size="2.3">{right}</text>')
    doc.layer("Tumbling_letters", "\n".join(t), FACES["playfair"][0])
    doc.layer("Broken_lines", "\n".join(g), f'{GARAMOND} fill="{GREY}"')

    # "flowers" in case pairs, drifting along the bottom
    pairs, x = [], 14
    for k, ch in enumerate("flowers"):
        y = 186 - 3 * math.sin(k * 0.9)
        pairs.append(big(x, y, 3.2, ch, GREY, extra=f' {GARAMOND}'))
        pairs.append(big(x + 2.4, y + 1.2, 6.5, ch.upper(), PAPER, extra=f' {GARAMOND}'))
        x += 12 + 3 * (k % 2)
    doc.layer("Case_pairs", "\n".join(pairs))
    # single letters of the last lines falling down the f's curve
    fall = []
    for k, ch in enumerate("sighs"):
        fall.append(big(176 - k * 2.2, 118 + k * 9, 3.2, ch, GREY, extra=f' {GARAMOND}'))
    doc.layer("Falling", "\n".join(fall))
    doc.layer("Edge_Caption", edge_caption(POEM[20:], GREY))
    return doc


if __name__ == "__main__":
    reference()  # sketch 1: the student's own work, as is
    staircase().save("frost-flowers_1_sketch-2.svg")
    scatter().save("frost-flowers_1_sketch-3.svg")
    staircase(final=True).save("frost-flowers_2_final.svg")
    print("ok")
