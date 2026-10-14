"""frost flowers — typo poem (20 x 20 cm)

Three sketches and one final composition, written as SVG, built from the
typographic factors taught in the course (case, typeface, size,
weight, width, outline), in compositions of our own:

  sketch 1   the student's own reference artwork, kept as is (text runs re-set)
  sketch 2   white page, few groups: stepped lines, big F + raised italic f,
             one large line, a rattling line, a caption up the left edge
  sketch 3   a heavy y with lines flush to its contour, arcs, tone, strike
  final      sketch 2 refined

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
# QUIET — white page, a handful of separate groups, each with one role:
# a stepped group, a big letter pair, one large line, one small play, and a
# caption. Few groups, generous space between them.
# ---------------------------------------------------------------------------
from PIL import Image, ImageDraw
import numpy as np

SERIF = "font-family=\"'EB Garamond', serif\""
SERIF_I = "font-family=\"'EB Garamond', serif\" font-style=\"italic\""
_gr = ImageFont.truetype(FONTDIR + "/EBGaramond-Regular.ttf", 1000)
_gi = ImageFont.truetype(FONTDIR + "/EBGaramond-Italic.ttf", 1000)
_bod = ImageFont.truetype(FONTDIR + "/BodoniModa-DisplayItalic.ttf", 1000)
_heavy_file = FONTDIR + "/ArchivoStep7.ttf"
LIGHT = "#d9d9d9"


def w_r(s, size):
    return _gr.getlength(s) * size / 1000


def T2(x, y, size, txt, attrs=SERIF, fill=INK, anchor=None, extra=""):
    a = f' text-anchor="{anchor}"' if anchor else ""
    return f'<text x="{f(x)}" y="{f(y)}" font-size="{f(size)}" fill="{fill}" {attrs}{a}{extra}>{txt}</text>'


def vertical(x, y, size, txt, attrs=SERIF, fill=INK):
    """Text running up the page from (x, y)."""
    return (f'<text x="0" y="0" font-size="{size}" fill="{fill}" {attrs} '
            f'transform="translate({f(x)} {f(y)}) rotate(-90)">{txt}</text>')


# ---------------------------------------------------------------------------
# SKETCH 2 / FINAL — "F f"
# ---------------------------------------------------------------------------
def big_f(final=False):
    doc = Doc("frost flowers — final" if final else "frost flowers — sketch 2")
    doc.layer("Paper", f'<rect width="200" height="200" fill="{PAPER}"/>')
    S = 3.3

    # 1 · stepped group: right-aligned, stepping down to the left
    g1 = [T2(184 - i * 5.6, 20 + i * 5.4, S, line.rstrip(","), anchor="end")
          for i, line in enumerate(POEM[:8])]
    doc.layer("Stepped", "\n".join(g1))

    # 2 · big roman F, small raised italic f, a word column, a hairline line
    Fx, Fy, Fs = 26, 160, 100
    Fw = w_r("F", Fs)
    fx, fy, fs = Fx + Fw + 2, Fy - Fs * 0.42, 40
    g2 = [T2(Fx, Fy, Fs, "F"), T2(fx, fy, fs, "f", FACES["bodoni"][0])]
    col_x = fx + _bod.getlength("f") * fs / 1000 + 5
    for k, wd in enumerate(POEM[11].rstrip(",").split()):  # I move from seat to seat to look
        g2.append(T2(col_x, fy - fs * 0.6 + k * 4.0, 2.9, wd, fill="#444"))
    rule_y = Fy - Fs * 0.25
    g2.append(f'<line x1="{f(Fx + Fw + 1)}" y1="{f(rule_y)}" x2="184" y2="{f(rule_y)}" stroke="{INK}" stroke-width="0.2"/>')
    g2.append(T2(Fx + Fw + 3, rule_y - 1.3, S, POEM[17] + " " + POEM[18], SERIF_I))
    doc.layer("Letter_pair", "\n".join(g2))

    # 3 · one large line
    doc.layer("Large_line", T2(26, 180, 7.6, POEM[14]))
    # 4 · one small play: a line that rattles (set twice, a hair apart)
    hx, hy = 72, 193
    doc.layer("Rattle", T2(hx + 0.7, hy + 0.35, 4.2, POEM[19], fill="#9a9a9a") + T2(hx, hy, 4.2, POEM[19]))
    if final:
        doc.layer("Aside", T2(184, 166, 2.9, POEM[15], SERIF_I, anchor="end", fill="#555"))

    # 5 · caption up the left edge, with its hairline
    cap = "friend, you walked the road beside me for so long, and now I am not even allowed to visit you."
    doc.layer("Caption", vertical(11, 186, 2.6, cap) +
              f'<line x1="13.2" y1="186" x2="13.2" y2="{f(186 - w_r(cap, 2.6))}" stroke="{INK}" stroke-width="0.15"/>')
    return doc


# ---------------------------------------------------------------------------
# SKETCH 3 — "y"
# ---------------------------------------------------------------------------
def heavy_mask(ch, x, y, size, px=4):
    im = Image.new("L", (200 * px, 200 * px), 0)
    ImageDraw.Draw(im).text((x * px, y * px), ch, fill=255, anchor="ls",
                            font=ImageFont.truetype(_heavy_file, int(size * px)))
    return np.array(im) > 127, px


def big_y():
    doc = Doc("frost flowers — sketch 3")
    doc.layer("Paper", f'<rect width="200" height="200" fill="{PAPER}"/>')
    yx, yy, ys = 84, 146, 190
    doc.layer("Big_y", f'<text x="{yx}" y="{yy}" font-size="{ys}" fill="{INK}" font-family="ArchivoStep7">y</text>')

    # 1 · lines set flush against the y's left contour
    mask, px = heavy_mask("y", yx, yy, ys)
    S, g1 = 3.2, []
    for i, line in enumerate(POEM[0:4] + POEM[9:14]):
        by = 66 + i * 6.0
        band = mask[int((by - S * 0.8) * px):int((by + 0.6) * px)].any(axis=0)
        cols = np.nonzero(band)[0]
        edge = (cols.min() / px if len(cols) else 186) - 3
        g1.append(T2(edge, by, S, line, anchor="end"))
    doc.layer("Along_the_y", "\n".join(g1))

    # 2 · two lines curving like a pair of parentheses
    cx, cy, r = 34, 30, 17
    doc.defs.append(f'<path id="arcTop" d="M{cx - r} {cy} A{r} {r} 0 0 1 {cx + r} {cy}"/>')
    doc.defs.append(f'<path id="arcBot" d="M{cx - r - 3} {cy + 3} A{r + 3} {r + 3} 0 0 0 {cx + r + 3} {cy + 3}"/>')
    top_s = min(2.9, math.pi * r * 0.95 / (_gi.getlength(POEM[16]) / 1000))
    bot_txt = POEM[17] + " on the glass."
    bot_s = min(2.9, math.pi * (r + 3) * 0.95 / w_r(bot_txt, 1))
    doc.layer("Arcs",
              f'<text font-size="{top_s:.2f}" {SERIF_I} fill="{INK}"><textPath href="#arcTop" startOffset="50%" text-anchor="middle">{POEM[16]}</textPath></text>'
              f'<text font-size="{bot_s:.2f}" {SERIF} fill="#555"><textPath href="#arcBot" startOffset="50%" text-anchor="middle">{bot_txt}</textPath></text>')

    # 3 · a pale large word behind a small dark one
    doc.layer("Tone", T2(98, 40, 32, "breath", SERIF_I, fill=LIGHT) + T2(128, 34, 5.2, "sigh", SERIF_I))

    # 4 · the passengers, struck through
    g4, sx, sy = [], 14, 148
    group = [POEM[4], POEM[5], POEM[6]]
    for k, line in enumerate(group):
        y = sy + k * 5.2
        g4.append(T2(sx, y, 3.0, line))
        if k:
            g4.append(f'<line x1="{sx}" y1="{f(y - 1.0)}" x2="{f(sx + w_r(line, 3.0))}" y2="{f(y - 1.0)}" '
                      f'stroke="{INK}" stroke-width="0.25"/>')
    g4.append(T2(sx, sy + 3 * 5.2 + 3, 3.0, POEM[7], SERIF_I))
    doc.layer("Struck", "\n".join(g4))
    doc.layer("Title", T2(186, 192, 3.0, "frost flowers", SERIF_I, anchor="end"))
    return doc


if __name__ == "__main__":
    reference()  # sketch 1: the student's own work, as is
    big_f().save("frost-flowers_1_sketch-2.svg")
    big_y().save("frost-flowers_1_sketch-3.svg")
    big_f(final=True).save("frost-flowers_2_final.svg")
    print("ok")
