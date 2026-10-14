"""frost flowers — typo poem (20 x 20 cm)

Three sketches and one final composition, written as SVG, built from the
principles of visual grammar rather than from the poem's imagery:

  reference  the original reference artwork, kept as is (text runs re-set)
  sketch 1   balance · emphasis · contrast: a crescent of type around a big g
  sketch 2   movement · rhythm: the lines travel a Z over a black triangle
  sketch 3   harmony · rhythm: arcs rippling out from a big cropped o
  final      sketch 1 refined

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
    open(f"{OUTDIR}/frost-flowers_0_reference.svg", "w").write(s)


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
# No rectangular text blocks: every composition lets the lines of the poem
# form a shape — a crescent, a Z, a ripple — around one large cropped letter.
# ---------------------------------------------------------------------------
def arc_d(cx, cy, r, a0, a1, n=48):
    """Arc (degrees, clockwise on screen) as a smooth path."""
    pts = [(cx + r * math.cos(math.radians(a0 + (a1 - a0) * k / (n - 1))),
            cy + r * math.sin(math.radians(a0 + (a1 - a0) * k / (n - 1)))) for k in range(n)]
    return smooth(pts), pts


def visible_span(cx, cy, r, a0, a1, box=(8, 8, 192, 192), step=0.5):
    """Longest run of angles in [a0, a1] whose arc points lie inside box."""
    best, cur = None, None
    a = a0
    while a <= a1 + 1e-9:
        x, y = cx + r * math.cos(math.radians(a)), cy + r * math.sin(math.radians(a))
        inside = box[0] <= x <= box[2] and box[1] <= y <= box[3]
        if inside:
            cur = (cur[0], a) if cur else (a, a)
            if best is None or cur[1] - cur[0] > best[1] - best[0]:
                best = cur
        else:
            cur = None
        a += step
    return best


def arc_line(doc, cx, cy, r, a0, a1, text, size, fill, offset_frac=0.0):
    """One poem line on an arc; slides along the arc by offset_frac of the slack."""
    span = visible_span(cx, cy, r, a0, a1)
    if not span or span[1] - span[0] < 4:
        return ""
    d, pts = arc_d(cx, cy, r, *span)
    L = plen(pts)
    s = min(size, size * L * 0.97 / tw(text, size))
    pid = doc.uid("arc")
    doc.defs.append(f'<path id="{pid}" d="{d}"/>')
    off = max(0.0, L - tw(text, s)) * offset_frac
    return (f'<text font-size="{s:.2f}" fill="{fill}"><textPath href="#{pid}" '
            f'startOffset="{off:.2f}">{text}</textPath></text>')


# ---------------------------------------------------------------------------
# SKETCH 1 / FINAL — asymmetrical BALANCE, EMPHASIS, CONTRAST
# A huge "g" cropped at the lower left is the heavy mass. The poem hugs its
# bowl on concentric arcs (a crescent of type, never a box) and balances it
# toward the upper right. The single red point sits in the g's counter — the
# focal point at the centre of every arc.
# ---------------------------------------------------------------------------
def crescent(final=False):
    global TEXT_FACE
    TEXT_FACE = "cormorant"
    doc = Doc("frost flowers — final (balance · emphasis · contrast)" if final
              else "frost flowers — sketch 1 (balance · emphasis · contrast)")
    doc.layer("Paper", f'<rect width="200" height="200" fill="{PAPER}"/>')
    gx, gy, gs = -24, 156, SCALE[10]
    doc.layer("Mass", big(gx, gy, gs, "g", INK), FACES["bodoni"][0])
    cx, cy = 27, 113  # centre of the g's bowl
    lines = []
    for i, line in enumerate(POEM):
        r = 54 + i * 4.6
        # each line starts a little further along its arc: the starts form one curve
        frac = 0.08 + 0.85 * (i / 21) ** 1.4
        lines.append(arc_line(doc, cx, cy, r, -96, 8, line, SCALE[1], INK, frac))
    doc.layer("Crescent_on_paths", "\n".join(lines), FACES["cormorant"][0])
    doc.layer("Focal_Point", f'<circle cx="{cx + 2}" cy="{cy + 6}" r="{SCALE[2] / 2}" fill="{RED}"/>')
    t = [big(200 - M, 200 - M, SCALE[2] if final else SCALE[1], "frost flowers", INK, extra=' text-anchor="end"')]
    if final:
        t.append(f'<line x1="{colx(4)}" y1="{200 - M - SCALE[2] - 2.5}" x2="{200 - M}" '
                 f'y2="{200 - M - SCALE[2] - 2.5}" stroke="{INK}" stroke-width="0.2"/>')
    doc.layer("Title", "\n".join(t), FACES["bodoni"][0])
    return doc


# ---------------------------------------------------------------------------
# SKETCH 2 — MOVEMENT (Z path) and RHYTHM
# The eye enters top left, runs along the top line, falls down a diagonal
# edge where each line ends exactly on the diagonal (spacing tight, then a
# pause, then loose), and leaves along the bottom over a black triangle.
# The red point is the end of the path.
# ---------------------------------------------------------------------------
def zpath():
    global TEXT_FACE
    TEXT_FACE = "caslon"
    doc = Doc("frost flowers — sketch 2 (movement · rhythm)")
    A, B = (190, 40), (10, 168)  # the diagonal
    tri = f"M{A[0]} {A[1]}L{B[0]} {B[1]}V200H200V{A[1]}Z"
    doc.layer("Planes", f'<rect width="200" height="200" fill="{PAPER}"/><path d="{tri}" fill="{PANE}"/>')

    def diag_x(y):
        return A[0] + (B[0] - A[0]) * (y - A[1]) / (B[1] - A[1])

    t = []
    # top run (entry), on a gentle wave
    p = [on_path(doc, wave(M, 22, 200 - M, 18, 1.2, 1.0, 0.3), POEM[0] + "  /  " + POEM[1], SCALE[1], INK)]
    # the fall: lines 3-14 end on the diagonal; tight, pause, loose
    ys, y = [], 44
    for k in range(12):
        ys.append(y)
        y += 4.4 if k < 6 else (13 if k == 6 else 7.2)
    for k, yy in enumerate(ys):
        line = POEM[2 + k]
        size = SCALE[1] if k < 7 else SCALE[2] * 0.85
        size = min(size, (diag_x(yy) - 3 - M) / tw(line, 1))  # never past the margin
        t.append(big(diag_x(yy) - 3, yy, f"{size:.2f}", line, INK, extra=' text-anchor="end"'))
    # exit: lines 15-22 along the bottom, white on black, stepping right
    for k in range(4):
        y0 = 171 + k * 7.4
        p.append(on_path(doc, wave(30 + k * 14, y0 + 1.5, 200 - M, y0 - 1.5, 0.9, 1.0, k),
                         POEM[14 + 2 * k] + "  /  " + POEM[15 + 2 * k], SCALE[1] * 0.85, PAPER))
    doc.layer("Movement_on_paths", "\n".join(p), FACES["caslon"][0])
    doc.layer("Fall", "\n".join(t), FACES["caslon"][0])
    big_t = [big(200 - M, 120, SCALE[6], "frost", PAPER, extra=' text-anchor="end"'),
             big(200 - M, 148, SCALE[6], "flowers", PAPER, extra=' text-anchor="end"')]
    doc.layer("Display", "\n".join(big_t), FACES["archivo"][0])
    doc.layer("Focal_Point", f'<circle cx="{200 - M - 2}" cy="{160}" r="{SCALE[2] / 2}" fill="{RED}"/>')
    return doc


# ---------------------------------------------------------------------------
# SKETCH 3 — HARMONY and RHYTHM: ripples
# A big "o" cropped at the lower-left corner; the lines of the poem run on
# quarter-circle arcs sharing its centre (form harmony). Each line starts at
# a different point along its arc, so together they draw a wave (rhythm).
# One line is red.
# ---------------------------------------------------------------------------
def ripples():
    global TEXT_FACE
    TEXT_FACE = "caslon"
    doc = Doc("frost flowers — sketch 3 (harmony · rhythm)")
    doc.layer("Paper", f'<rect width="200" height="200" fill="{PAPER}"/>')
    cx, cy, osz = 4, 196, SCALE[9] * 1.1
    fo = ImageFont.truetype(FONTDIR + "/" + FACES["playfair"][1], 1000)
    l, t_, r_, b_ = fo.getbbox("o", anchor="ls")  # centre the o on the arcs' centre
    ox, oy = cx - (l + r_) / 2 * osz / 1000, cy - (t_ + b_) / 2 * osz / 1000
    doc.layer("Mass", big(ox, oy, f"{osz:.2f}", "o", INK), FACES["playfair"][0])
    lines = []
    for i, line in enumerate(POEM):
        r = osz * 0.36 + 10 + i * 5.6
        frac = 0.5 + 0.5 * math.sin(i * 0.42 - 0.6)
        lines.append(arc_line(doc, cx, cy, r, -92, 2, line, SCALE[1], RED if i == 15 else INK, frac))
    doc.layer("Ripples_on_paths", "\n".join(lines), FACES["caslon"][0])
    doc.layer("Title", big(200 - M, M + SCALE[2], SCALE[2], "frost flowers", INK, extra=' text-anchor="end"'),
              FACES["playfair"][0])
    return doc


if __name__ == "__main__":
    reference()
    crescent().save("frost-flowers_1_sketch-1.svg")
    zpath().save("frost-flowers_1_sketch-2.svg")
    ripples().save("frost-flowers_1_sketch-3.svg")
    crescent(final=True).save("frost-flowers_2_final.svg")
    print("ok")
