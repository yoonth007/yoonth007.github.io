"""frost flowers — typo poem (20 x 20 cm)

Three sketches and one final composition, written as SVG, built from the
typographic factors taught in the course (case, typeface, size,
weight, width, outline), in compositions of our own:

  sketch 1   the student's own reference artwork, kept as is (text runs re-set)
  sketch 2   icicles: lines hang from the top edge, last words broken off
  sketch 3   funnel: lines narrow and squeeze downward, words drip out,
             a big "you" sinks into the bottom edge
  final      sketch 3 refined

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


def heavy_mask(ch, x, y, size, px=4):
    im = Image.new("L", (200 * px, 200 * px), 0)
    ImageDraw.Draw(im).text((x * px, y * px), ch, fill=255, anchor="ls",
                            font=ImageFont.truetype(_heavy_file, int(size * px)))
    return np.array(im) > 127, px


# ---------------------------------------------------------------------------
# DESCENT — everything falls: line gaps widen as if accelerating, lines tilt
# further as they drop, words come loose one by one, and the big letters sink
# below the bottom edge.
# ---------------------------------------------------------------------------
def falling(n, start, gap0, accel=1.13):
    """Positions for n items whose gaps grow each step (an accelerating fall)."""
    ys, y, g = [], start, gap0
    for _ in range(n):
        ys.append(y)
        y += g
        g *= accel
    return ys


# a slight gloom: the page dims toward the bottom, and falling type fades
DUSK_TOP, DUSK_BOTTOM = "#eeeeec", "#9a9da1"


def dusk(doc):
    doc.defs.append(f'<linearGradient id="dusk" x1="0" y1="0" x2="0" y2="1">'
                    f'<stop offset="0" stop-color="{DUSK_TOP}"/><stop offset="0.45" stop-color="#e2e2e0"/>'
                    f'<stop offset="1" stop-color="{DUSK_BOTTOM}"/></linearGradient>')
    return '<rect width="200" height="200" fill="url(#dusk)"/>'


def fade(t):
    """Ink that greys as it falls (t: 0 → 1)."""
    return mix("#1c1c1c", "#6e7175", t)


def tilt(x, y, deg):
    return f' transform="rotate({deg:.2f} {f(x)} {f(y)})"' if deg else ""


# ---------------------------------------------------------------------------
# Restrained typographic play inside the shapes: only two or three key words
# per page step up into Bodoni italic; everything else stays plain.
# ---------------------------------------------------------------------------
BODONI_I = "font-family=\"'Bodoni Moda', serif\" font-style=\"italic\""


HEAVY_I = "font-family=\"'PlayfairBlack', 'Playfair Display'\" font-style=\"italic\" font-weight=\"900\""
EMPH_SCALE = 2.6


def emph(line, size, keys=(), used=None):
    """Line markup with just the given key words stepped up: heavy, large, dark.
    Each key word is stepped up only the first time it appears (`used`)."""
    out = []
    for w in line.split(" "):
        core = w.strip(",.?—").lower()
        if core in keys and (used is None or core not in used):
            if used is not None:
                used.add(core)
            out.append(f'<tspan {HEAVY_I} font-size="{size * EMPH_SCALE:.2f}" fill="#141516">{w}</tspan>')
        else:
            out.append(w)
    return " ".join(out)


# ---------------------------------------------------------------------------
# SKETCH 2 — "icicles"
# Every line of the poem hangs straight down from the top edge. Their lengths
# make a ragged fringe of tips; the last word of each line has broken off and
# fallen below its tip. "flowers" lies sunk at the bottom of the page.
# ---------------------------------------------------------------------------
# ---------------------------------------------------------------- Text Wrap --
from PIL import ImageFilter

PXW = 4  # wrap mask resolution, px per mm


def word_mask(txt, x, y, size, font_file, anchor="ls", pad=2.0):
    """Mask of a big word (as placed on the page), grown by `pad` mm."""
    im = Image.new("L", (200 * PXW, 200 * PXW), 0)
    ImageDraw.Draw(im).text((x * PXW, y * PXW), txt, fill=255, anchor=anchor,
                            font=ImageFont.truetype(font_file, int(size * PXW)))
    k = int(pad * PXW) * 2 + 1
    return np.array(im.filter(ImageFilter.MaxFilter(k))) > 127


def spaced_mask(txt, x, y, size, font_file, spacing, pad=2.0):
    """Mask of a letter-spaced word, letter by letter."""
    fo = ImageFont.truetype(font_file, 1000)
    m = np.zeros((200 * PXW, 200 * PXW), bool)
    for ch in txt:
        m |= word_mask(ch, x, y, size, font_file, pad=pad)
        x += fo.getlength(ch) * size / 1000 + spacing
    return m


def box_mask(x0, y0, x1, y1):
    m = np.zeros((200 * PXW, 200 * PXW), bool)
    m[int(y0 * PXW):int(y1 * PXW), int(x0 * PXW):int(x1 * PXW)] = True
    return m


def wrap_paragraph(text, mask, x0, x1, y0, y1, size, lead, fill, min_w=6.0):
    """Text Wrap: flow a paragraph into the free spans of each row around
    `mask`, word by word, left to right and top to bottom."""
    words, out, y = text.split(), [], y0
    while words and y <= y1:
        r0, r1 = int((y - size * 0.75) * PXW), int((y + size * 0.25) * PXW) + 1
        band = mask[max(r0, 0):min(r1, 200 * PXW)].any(axis=0)
        c, end = int(x0 * PXW), int(x1 * PXW)
        while c < end and words:
            while c < end and band[c]:
                c += 1
            start = c
            while c < end and not band[c]:
                c += 1
            sx, ex = start / PXW, c / PXW
            if ex - sx < min_w:
                continue
            seg = []
            while words and w_r(" ".join(seg + [words[0]]), size) <= ex - sx:
                seg.append(words.pop(0))
            if seg:
                out.append(T2(sx, y, size, " ".join(seg), fill=fill))
        y += lead
    return "\n".join(out)


BLACK_FILE = FONTDIR + "/PlayfairDisplay-BlackItalic.ttf"
ICICLE_KEYS = {"frost", "breath", "sigh"}
FUNNEL_KEYS = {"flowers", "sighs", "petal"}


def icicles(final=False):
    doc = Doc("frost flowers — final" if final else "frost flowers — sketch 2")
    doc.layer("Paper", dusk(doc))
    S, top, x0, step = 2.9, 10, 16, 8.0
    hang, drops, used = [], [], set()
    for k, line in enumerate(POEM):
        words = line.rstrip(",.").split()
        body, last = " ".join(words[:-1]), words[-1]
        x = x0 + k * step
        ink = fade(0.15 + 0.6 * (k / 21))
        before = len(used)
        markup = emph(body, S, ICICLE_KEYS, used)
        hang.append(f'<text x="0" y="0" font-size="{S}" fill="{ink}" {SERIF} '
                    f'transform="translate({f(x)} {top}) rotate(90)">{markup}</text>')
        tip = top + w_r(body, S) + (len(used) - before) * S * 2.6
        gap = 5 + 9 * abs(math.sin(k * 1.7))  # each piece fell a different distance
        drops.append(T2(x - 0.6, tip + gap, S + 0.3, last, SERIF_I, fill=fade(0.45 + 0.4 * (k / 21)),
                        extra=tilt(x - 0.6, tip + gap, 90 - 25 * math.sin(k * 0.9))))
    doc.layer("Eave", f'<line x1="10" y1="{top - 2.5}" x2="190" y2="{top - 2.5}" stroke="{INK}" stroke-width="0.35"/>')
    doc.layer("Hanging_lines", "\n".join(hang))
    doc.layer("Fallen_words", "\n".join(drops))
    LS = 9  # letters pulled apart so the text can wrap between them
    doc.layer("Sunk", T2(-4, 204, 60, "flowers", HEAVY_I, fill="#161718", extra=f' letter-spacing="{LS}"'))
    # Text Wrap: the passage flows into the gaps between the letters
    m = spaced_mask("flowers", -4, 204, 60, BLACK_FILE, LS)
    doc.layer("Wrapped", wrap_paragraph(" ".join(POEM[14:20]), m, 6, 196, 175, 198, 2.4, 3.3, "#2b2d30", 4.0))
    if final:
        doc.layer("Title", T2(186, 192, 3.0, "frost flowers", SERIF_I, anchor="end", fill="#eeeeec"))
    return doc


# ---------------------------------------------------------------------------
# SKETCH 3 / FINAL — "funnel"
# The lines narrow downward into an inverted triangle, their letters squeezed
# tighter the lower they sit. Below the tip, words drip out one at a time,
# farther and farther apart, and a big "you" sinks into the bottom edge.
# ---------------------------------------------------------------------------
def funnel(final=False):
    doc = Doc("frost flowers — final" if final else "frost flowers — sketch 3")
    doc.layer("Paper", dusk(doc))
    cx, n, y = 100, 14, 20
    g, used = [], set()
    for k, line in enumerate(POEM[:n]):
        t = k / (n - 1)
        size = 3.6 - 1.0 * t
        width = 150 * (1 - t) + 30 * t  # every line held to the funnel's width
        adjust = "spacing" if width >= w_r(line, size) else "spacingAndGlyphs"  # widen, or squeeze
        before = len(used)
        markup = emph(line, size, FUNNEL_KEYS, used)
        big = len(used) > before
        if big:
            y += size * 1.3  # room above a stepped-up word
        g.append(f'<text x="{f(cx - width / 2)}" y="{f(y)}" font-size="{size:.2f}" fill="{fade(0.1 + 0.5 * t)}" '
                 f'textLength="{width:.2f}" lengthAdjust="{adjust}" {SERIF}>{markup}</text>')
        y += 6.0 - 2.4 * t + (size * 0.9 if big else 0)
    doc.layer("Funnel", "\n".join(g))

    drip = []
    words = (POEM[14] + " " + POEM[16] + " " + POEM[17]).replace(",", "").split()
    for k, (wd, yy) in enumerate(zip(words, falling(len(words), y + 4, 3.2, 1.11))):
        if yy > 150:
            break
        drip.append(T2(cx + 1.5 * math.sin(k * 1.3), yy, 2.8, wd, SERIF_I, anchor="middle",
                       fill=fade(0.55 + 0.03 * k)))
    doc.layer("Drip", "\n".join(drip))
    doc.layer("Sunk_you", T2(cx, 214, 120, "you", HEAVY_I, anchor="middle", fill="#161718"))
    # Text Wrap: the poem's last lines flow around the drip and into the gaps of "you"
    m = word_mask("you", cx, 214, 120, BLACK_FILE, anchor="ms") | box_mask(cx - 13, y, cx + 13, 152)
    doc.layer("Wrapped", wrap_paragraph(" ".join(POEM[18:22] + POEM[15:16]), m, 6, 196, 160, 198, 2.4, 3.6, "#2b2d30", 4.0))
    if final:
        doc.layer("Title", T2(14, 11, 3.0, "frost flowers", SERIF_I))
    return doc


if __name__ == "__main__":
    reference()  # sketch 1: the student's own work, as is
    icicles().save("frost-flowers_1_sketch-2.svg")
    funnel().save("frost-flowers_1_sketch-3.svg")
    funnel(final=True).save("frost-flowers_2_final.svg")
    print("ok")
