"""frost flowers — typo poem (20 x 20 cm)

Three sketches and one final composition, written as SVG, built from the
principles of visual grammar rather than from the poem's imagery:

  reference  the original reference artwork, kept as is (text runs re-set)
  sketch 1   asymmetrical balance · emphasis · contrast
  sketch 2   rhythm · repetition · movement
  sketch 3   radial balance · harmony (form synchronised with a big "o")
  final      sketch 3 refined: golden-section centre, crop, grid caption

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
# SKETCH 1 — asymmetrical BALANCE, EMPHASIS, CONTRAST
# A huge cropped "g" (large, light-edged mass, lower left) is balanced by a
# small but dense block of type (upper right). Contrast of scale (150 mm vs
# 2.6 mm), of style (Didone vs monospace) and of value. One red point, isolated
# in the white space at a third-line crossing, is the single focal point.
# ---------------------------------------------------------------------------
def balance():
    global TEXT_FACE
    TEXT_FACE = "plexmono"
    doc = Doc("frost flowers — sketch 1 (balance · emphasis · contrast)")
    doc.layer("Paper", f'<rect width="200" height="200" fill="{PAPER}"/>')
    doc.layer("Mass", big(-24, 156, SCALE[10], "g", INK), FACES["bodoni"][0])

    # counterweight: the whole poem, dense, on identical gentle arcs (repetition)
    x0, x1, size, lead = colx(3), 200 - M, SCALE[0] * 0.98, 3.95
    p = []
    for i, line in enumerate(POEM):
        y = 22 + i * lead
        p.append(on_path(doc, arc_pts(x0, y, x1, y, 1.2), line, size, INK))
    doc.layer("Counterweight_on_paths", "\n".join(p), FACES["plexmono"][0])

    # emphasis: one red point at the crossing of the lower and right third lines
    doc.layer("Focal_Point", f'<circle cx="{f(200 * 2 / 3)}" cy="{f(200 * 2 / 3)}" r="{SCALE[3] / 2}" fill="{RED}"/>')
    # small labels aligned to the same column edge as the block (alignment)
    lab = [big(x0, 22 + 22 * lead + SCALE[2], SCALE[1], "frost flowers", INK)]
    doc.layer("Labels", "\n".join(lab), FACES["bodoni"][0])
    return doc


# ---------------------------------------------------------------------------
# SKETCH 2 — RHYTHM, REPETITION, MOVEMENT
# Poem lines become vertical bars. Left: dense, varied sizes (fast tempo).
# Middle: a wide pause of white space. Right: one size, one interval, repeated
# — and one red bar breaks the rule (visual climax). The bars on the right
# run past the page edge (crop). The eye moves left to right, slows, stops.
# ---------------------------------------------------------------------------
def rhythm():
    global TEXT_FACE
    doc = Doc("frost flowers — sketch 2 (rhythm · repetition · movement)")
    doc.layer("Paper", f'<rect width="200" height="200" fill="{PAPER}"/>')

    def bar(x, y, size, txt, face, fill=INK):
        return (f'<text x="0" y="0" font-size="{size}" fill="{fill}" {FACES[face][0]} '
                f'transform="translate({f(x)} {f(y)}) rotate(-90)">{txt}</text>')

    b, x = [], M
    tempo = [SCALE[2], SCALE[0], SCALE[3], SCALE[0], SCALE[1], SCALE[4], SCALE[0],
             SCALE[2], SCALE[1], SCALE[0], SCALE[3], SCALE[0], SCALE[1], SCALE[2]]
    for i, size in enumerate(tempo):  # fast tempo: lines 1-14, mixed sizes, tight
        face = "archivo" if size >= SCALE[2] else "cormorant"
        x += size * 0.78
        b.append(bar(x, 200 - M, size, POEM[i], face))
        x += 0.9
    dense_end = x

    # regular tempo: lines 15-22, one size, one interval; one red bar
    step = SCALE[3] * 0.95
    xs = [200 - M - step * (7 - k) for k in range(8)]
    for k, line in enumerate(POEM[14:]):
        b.append(bar(xs[k], 196, SCALE[3], line, "archivo", RED if k == 5 else INK))
    doc.layer("Bars", "\n".join(b))

    # the pause holds only the title, small and isolated, on the baseline
    mid = (dense_end + xs[0] - SCALE[3]) / 2
    doc.layer("Title", big(mid, 200 - M, SCALE[1], "frost flowers", INK, extra=' text-anchor="middle"'),
              FACES["cormorant"][0])
    return doc


# ---------------------------------------------------------------------------
# SKETCH 3 / FINAL — radial BALANCE, HARMONY, UNITY, PROPORTION
# The poem runs on concentric circles whose radii grow by the 1.5 ratio;
# text size grows with them. A big "o" repeats the circle (form harmony);
# inside it the type inverts to white. One red point marks the centre.
# Final: the centre moves off-axis to the golden section for tension, the
# outer rings crop against the page, and a small caption block aligns to grid.
# ---------------------------------------------------------------------------
def radial(final=False):
    global TEXT_FACE
    TEXT_FACE = "caslon"
    name = "final (radial balance · harmony · unity)" if final else "sketch 3 (radial balance · harmony)"
    doc = Doc("frost flowers — " + name)
    doc.layer("Paper", f'<rect width="200" height="200" fill="{PAPER}"/>')
    cx, cy = (123.6, 106) if final else (100, 100)  # golden section vs. centre

    # rings: primary radii on the 1.5 scale, a secondary ring between each pair
    prim = [10, 15, 22.5, 33.75, 50.6, 75.9, 113.9]
    radii, sizes = [], []
    for k, r in enumerate(prim):
        radii.append(r); sizes.append(SCALE[min(k // 2, 4)] * (1.0 if k < 6 else 1.2))
        if k < len(prim) - 1:
            radii.append(r * 1.225); sizes.append(sizes[-1])
    text = "   ".join(POEM) + "   "
    rings, pos = [], 0
    for r, s in zip(radii, sizes):
        cap = 2 * math.pi * r * 0.985
        chunk = ""
        while tw(chunk + text[pos % len(text)], s) < cap:
            chunk += text[pos % len(text)]; pos += 1
        pid = doc.uid("ring")
        doc.defs.append(f'<path id="{pid}" d="{circle_d(cx, cy, r)}"/>')
        rings.append((pid, s, chunk))

    def ring_layer(fill):
        return "\n".join(f'<text font-size="{s:.2f}" fill="{fill}"><textPath href="#{pid}">{c}</textPath></text>'
                         for pid, s, c in rings)

    O = SCALE[9] * (2.0 if final else 1.8)
    ox, oy = cx - O * 0.24, cy + O * 0.21  # optical centring of the italic o
    o_glyph = f'<text x="{f(ox)}" y="{f(oy)}" font-size="{f(O)}" {FACES["playfair"][0]}>o</text>'
    doc.defs.append(f'<clipPath id="inO">{o_glyph}</clipPath>')
    ring_clip = ""
    if final:  # keep a grid-aligned box clear for the caption
        bw, bh = colx(2) + COL - M + 4, SCALE[2] + SCALE[1] + 12
        doc.clip("free", f'<path clip-rule="evenodd" d="M0 0H200V200H0Z M{M - 4} {M - 4}h{f(bw)}v{f(bh)}h{f(-bw)}Z"/>')
        ring_clip = ' clip-path="url(#free)"'
    doc.layer("Rings", ring_layer(INK), FACES["caslon"][0] + ring_clip)
    doc.layer("Big_o", o_glyph.replace("<text ", f'<text fill="{INK}" ', 1))
    doc.layer("Rings_inverted", ring_layer(PAPER), f'{FACES["caslon"][0]} clip-path="url(#inO)"')
    doc.layer("Focal_Point", f'<circle cx="{f(cx)}" cy="{f(cy)}" r="{SCALE[1] / 2}" fill="{RED}"/>')

    if final:
        cap = [big(M, M + SCALE[2], SCALE[2], "frost flowers", INK),
               f'<line x1="{M}" y1="{M + SCALE[2] + 3}" x2="{colx(1) + COL}" y2="{M + SCALE[2] + 3}" '
               f'stroke="{RED}" stroke-width="0.35"/>',
               big(M, M + SCALE[2] + 3 + SCALE[1] + 1, SCALE[0], "a typo poem in concentric lines", INK)]
        doc.layer("Caption", "\n".join(cap), FACES["playfair"][0])
    return doc


if __name__ == "__main__":
    reference()
    balance().save("frost-flowers_1_sketch-1.svg")
    rhythm().save("frost-flowers_1_sketch-2.svg")
    radial().save("frost-flowers_1_sketch-3.svg")
    radial(final=True).save("frost-flowers_2_final.svg")
    print("ok")
