"""frost flowers — typo poem (20 x 20 cm)

Generates three sketches and one final composition as SVG.
Everything on the page is type, plus minimal points / lines / planes
(no pictures or drawn objects), per the typo_poem brief.

usage: python3 typo_poem.py <font_dir> <out_dir>
"""
import math, random, sys
from PIL import ImageFont

FONTDIR, OUTDIR = sys.argv[1], sys.argv[2]
_ital = ImageFont.truetype(FONTDIR + "/EBGaramond-Italic.ttf", 1000)
_reg = ImageFont.truetype(FONTDIR + "/EBGaramond-Regular.ttf", 1000)


def tw(s, size, italic=True):
    """Advance width of a string in mm at a font size in mm."""
    return (_ital if italic else _reg).getlength(s) * size / 1000


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

ROMAN = "font-family=\"'EB Garamond', 'Adobe Garamond Pro', Garamond, serif\""
ITAL = ROMAN + ' font-style="italic"'


class Doc:
    """Tiny SVG builder: defs + layered groups, units in mm."""

    def __init__(self, name):
        self.name, self.defs, self.layers, self.n = name, [], [], 0

    def uid(self, p="p"):
        self.n += 1
        return f"{p}{self.n}"

    def layer(self, lid, body, attrs=""):
        self.layers.append(f'<g id="{lid}" {attrs}>\n{body}\n</g>')

    def svg(self):
        return (
            '<svg xmlns="http://www.w3.org/2000/svg" width="200mm" height="200mm" viewBox="0 0 200 200">\n'
            f"<title>{self.name}</title>\n<defs>\n" + "\n".join(self.defs) + "\n</defs>\n"
            + "\n".join(self.layers) + "\n</svg>\n"
        )

    def save(self, fn):
        open(f"{OUTDIR}/{fn}", "w").write(self.svg())


class Words:
    """Endless stream of poem text used to 'grow' frost out of type."""

    def __init__(self, lines, seed):
        self.src = " · ".join(lines) + " · "
        self.i = random.Random(seed).randrange(len(self.src))

    def take(self, length, size, italic=False):
        out, w = "", 0.0
        while True:
            ch = self.src[self.i % len(self.src)]
            cw = tw(ch, size, italic)
            if w + cw > length:
                return out.strip() or ch
            out += ch; w += cw; self.i += 1


def type_ray(doc, out, words, rnd, x, y, ang, length, size, depth, colour, op, italic=False):
    """One crystal arm set in type; side arms branch off at ~60 degrees."""
    if length < 1.2 or size < 0.55:
        return
    ex, ey = x + math.cos(ang) * length, y + math.sin(ang) * length
    pid = doc.uid("r")
    doc.defs.append(f'<path id="{pid}" d="M{f(x)} {f(y)}L{f(ex)} {f(ey)}"/>')
    txt = words.take(length, size, italic)
    out.append(f'<text font-size="{size:.2f}" fill="{colour}" opacity="{op:.2f}"><textPath href="#{pid}">{txt}</textPath></text>')
    if depth <= 0:
        return
    n = max(1, int(length / (size * 4.2)))
    for k in range(1, n + 1):
        t = k / (n + 1) + rnd.uniform(-0.04, 0.04)
        bx, by = x + (ex - x) * t, y + (ey - y) * t
        for s in (-1, 1):
            if rnd.random() < 0.8:
                bl = length * (1 - t) * rnd.uniform(0.35, 0.6)
                type_ray(doc, out, words, rnd, bx, by, ang + s * math.radians(rnd.uniform(52, 66)),
                         bl, size * 0.72, depth - 1, colour, op * 0.85, italic)


def type_frost_flower(doc, out, words, rnd, cx, cy, r, size, colour, op, arms=None):
    arms = arms or rnd.choice([5, 6, 6, 7, 8])
    rot = rnd.uniform(0, 2 * math.pi)
    for k in range(arms):
        a = rot + k * 2 * math.pi / arms + rnd.uniform(-0.2, 0.2)
        type_ray(doc, out, words, rnd, cx, cy, a, r * rnd.uniform(0.55, 1.1), size, 2, colour, op)


def type_fern(doc, out, words, rnd, x, y, ang, length, size, colour, op):
    """Feathery frost growing in from the window frame: a wandering spine of
    type with short side arms of smaller type."""
    step = 5.5
    for i in range(int(length / step)):
        ang += rnd.uniform(-0.16, 0.16)
        rem = 1 - i * step / length
        s = size * (0.55 + 0.45 * rem)
        type_ray(doc, out, words, rnd, x, y, ang, step, s, 0, colour, op)
        x, y = x + math.cos(ang) * step, y + math.sin(ang) * step
        for side in (-1, 1):
            if rnd.random() < 0.85:
                type_ray(doc, out, words, rnd, x, y, ang + side * math.radians(rnd.uniform(48, 64)),
                         (3 + 9 * rem) * rnd.uniform(0.6, 1.1), s * 0.75, 1 if rem > 0.55 else 0,
                         colour, op * 0.85)


def edge_frost(doc, out, words, rnd, colour, spacing=13):
    """Seed ferns along all four edges, pointing inward; corners grow longest."""
    seeds = []
    for k in range(int(200 / spacing) + 1):
        t = k * spacing + rnd.uniform(-3, 3)
        seeds += [(t, 0, math.pi / 2), (t, 200, -math.pi / 2), (0, t, 0), (200, t, math.pi)]
    for x, y, a in seeds:
        corner = min(math.hypot(x - cx, y - cy) for cx in (0, 200) for cy in (0, 200))
        length = 14 + 34 * max(0, 1 - corner / 90) + rnd.uniform(-4, 6)
        type_fern(doc, out, words, rnd, x, y, a + rnd.uniform(-0.7, 0.7), length,
                  rnd.uniform(1.25, 1.6), colour, rnd.uniform(0.45, 0.72))


def clip_rect_minus(doc, cid, ell, holes=(), rect=(0, 0, 200, 200)):
    """Clip to the page minus an ellipse (the wiped petal) and clear rectangles."""
    x, y, w, h = rect
    cx, cy, rx, ry = ell
    d = (f"M{x} {y}H{x+w}V{y+h}H{x}Z"
         f"M{f(cx-rx)} {f(cy)}A{f(rx)} {f(ry)} 0 1 0 {f(cx+rx)} {f(cy)}A{f(rx)} {f(ry)} 0 1 0 {f(cx-rx)} {f(cy)}Z")
    for hx, hy, hw, hh in holes:
        d += f"M{hx} {hy}H{hx+hw}V{hy+hh}H{hx}Z"
    doc.defs.append(f'<clipPath id="{cid}"><path d="{d}" clip-rule="evenodd"/></clipPath>')


# ---------------------------------------------------------------------------
# SKETCH 1 / FINAL — "a single frost petal": the dawn window, frosted in type,
# with one oval wiped clear by breath and finger.
# ---------------------------------------------------------------------------
def window(final=False):
    name = "frost flowers — final" if final else "frost flowers — sketch 1"
    doc = Doc(name)
    rnd = random.Random(11)
    BG, FROST, INK, WARM = "#11171e", "#e4ecf2", "#f4f7f9", "#e9a27c"
    WIPE = (104, 112, 50, 31) if final else (100, 104, 52, 34)

    doc.layer("Background", f'<rect width="200" height="200" fill="{BG}"/>')

    # frost: yesterday's passengers' breath (lines 1-16) crystallised as type
    words = Words(POEM[:16], 3)
    out = []
    edge_frost(doc, out, words, rnd, FROST, 12 if final else 15)
    # a few small blooms drifting toward the clearer middle of the glass
    blooms = [(58, 50, 9), (150, 56, 8), (52, 156, 9), (150, 160, 10)]
    if final:
        blooms += [(96, 34, 5), (128, 176, 6), (32, 112, 5), (176, 96, 5)]
    for cx, cy, r in blooms:
        type_frost_flower(doc, out, words, rnd, cx, cy, r, 1.0, FROST, 0.5)
    holes = [(7, 5, 42, 17), (110, 178, 86, 21)] if final else [(7, 5, 38, 12), (114, 180, 82, 15)]
    clip_rect_minus(doc, "wipe", WIPE, holes)
    doc.layer("Frost_Type", "\n".join(out), f'{ROMAN} clip-path="url(#wipe)"')

    cx, cy, rx, ry = WIPE
    # the edge of the wiped petal: a single hairline (line element)
    doc.layer("Wiped_Petal",
              f'<ellipse cx="{cx}" cy="{cy}" rx="{rx}" ry="{ry}" fill="none" stroke="{FROST}" '
              f'stroke-width="0.12" opacity="0.35"/>')

    t = []
    L = lambda x, y, s, txt, op=1, fill=INK, extra="": t.append(
        f'<text x="{f(x)}" y="{f(y)}" font-size="{s}" fill="{fill}" opacity="{op}" {extra}>{txt}</text>')
    top = cy - ry
    L(cx - 38, top + 13, 2.3, POEM[16], 0.75)                          # For no reason, carefully...
    L(cx - 38, top + 24, 4.6, "I wipe away")
    L(cx - 22, top + 37, 9.5, "a single frost petal")
    L(cx + 6, top + 44.5, 2.6, "and press my forehead to the glass.", 0.85)
    # rattling window: the same line, duplicated and shaken
    for dx, dy, op in ((0, 0, 0.9), (0.45, -0.25, 0.35), (-0.5, 0.3, 0.22), (0.9, 0.15, 0.12)):
        L(cx - 30 + dx, top + 52 + dy, 2.5, POEM[19], op)
    # a warm breath inside the cold: the one coloured line
    L(cx - 26, top + 59.5 if final else top + 61, 1.9, POEM[15], 0.9, WARM)
    doc.layer("Wiped_Text", "\n".join(t), ITAL)

    # outside the glass: the friend
    e = []
    if final:
        e.append(f'<text x="10" y="13" font-size="5.2" fill="{INK}" {ITAL}>frost flowers</text>')
        e.append(f'<line x1="10" y1="15.5" x2="44" y2="15.5" stroke="{INK}" stroke-width="0.15" opacity="0.6"/>')
        e.append(f'<text x="10" y="19.5" font-size="1.7" fill="{INK}" opacity="0.7" {ROMAN} letter-spacing="0.3">THE DAWN CITY BUS</text>')
        e.append(f'<text x="190" y="184" font-size="2.3" fill="{INK}" text-anchor="end" {ITAL}>{POEM[20]}</text>')
        e.append(f'<text x="190" y="189" font-size="2.3" fill="{INK}" text-anchor="end" {ITAL}>'
                 f'and now I am not even allowed to visit</text>')
        e.append(f'<text x="191.5" y="196" font-size="6" fill="{WARM}" text-anchor="end" {ITAL}>you.</text>')
    else:
        e.append(f'<text x="10" y="13" font-size="4.6" fill="{INK}" {ITAL}>frost flowers</text>')
        e.append(f'<text x="190" y="186" font-size="2.3" fill="{INK}" text-anchor="end" {ITAL}>{POEM[20]}</text>')
        e.append(f'<text x="190" y="191" font-size="2.3" fill="{INK}" text-anchor="end" {ITAL}>{POEM[21]}</text>')
    doc.layer("Title_and_Ending", "\n".join(e))
    return doc


# ---------------------------------------------------------------------------
# SKETCH 2 — "met in secret overnight": passengers' words drift in from the
# edges along lines and pile into one bloom of letters.
# ---------------------------------------------------------------------------
def gathering():
    doc = Doc("frost flowers — sketch 2")
    rnd = random.Random(5)
    PAPER, INK, GHOST = "#f3f2ee", "#151515", "#dcdedf"
    C = (132, 66)
    doc.layer("Background", f'<rect width="200" height="200" fill="{PAPER}"/>')

    # huge cropped "breath" behind everything (plane)
    doc.layer("Ghost_Word", f'<text x="-6" y="214" font-size="92" fill="{GHOST}" {ITAL}>breath</text>')

    people = [("maidens", (4, 46), 5.2, True), ("bachelors", (6, 96), 4.2, False),
              ("children", (76, 196), 5.6, True), ("grown-ups", (110, 196), 3.8, False),
              ("hairdressers", (196, 132), 3.4, True), ("salesmen", (196, 104), 4.6, False),
              ("housemaids", (156, 196), 3.6, True), ("the jobless", (196, 176), 3.2, False),
              ("their breath", (54, 4), 3.0, True), ("and their sighs", (196, 8), 2.8, True)]
    lines, words = [], []
    for w, (sx, sy), s, it in people:
        # curved route to the meeting point
        mx, my = (sx + C[0]) / 2 + rnd.uniform(-30, 30), (sy + C[1]) / 2 + rnd.uniform(-30, 30)
        pid = doc.uid("w")
        doc.defs.append(f'<path id="{pid}" d="M{f(sx)} {f(sy)}Q{f(mx)} {f(my)} {f(C[0])} {f(C[1])}"/>')
        lines.append(f'<use href="#{pid}"/>')
        words.append(f'<text font-size="{s}" fill="{INK}" {ITAL if it else ROMAN}>'
                     f'<textPath href="#{pid}" startOffset="2">{w}</textPath></text>')
    doc.layer("Routes", "\n".join(lines), f'fill="none" stroke="{INK}" stroke-width="0.12" opacity="0.45"')
    doc.layer("Passengers", "\n".join(words))

    # the bloom: letters of breath / sighs crowding the meeting point
    bloom, letters = [], "breathsighfrostflowers"
    rot = rnd.uniform(0, math.pi / 3)
    for i in range(260):
        r = 2.5 + abs(rnd.gauss(0, 11)) + (rnd.random() < 0.12) * rnd.uniform(6, 18)
        a = rnd.uniform(0, 2 * math.pi)
        # six-fold bias so the cloud reads as a crystal
        if rnd.random() < 0.75:
            a = rot + round((a - rot) / (math.pi / 3)) * (math.pi / 3) + rnd.gauss(0, 0.07 + 2 / (r + 6))
        x, y = C[0] + math.cos(a) * r, C[1] + math.sin(a) * r
        s = max(0.9, 4.0 - r * 0.11 + rnd.uniform(-0.6, 0.6))
        ch = letters[i % len(letters)]
        bloom.append(f'<text x="{f(x)}" y="{f(y)}" font-size="{s:.2f}" fill="{INK}" '
                     f'transform="rotate({rnd.randint(-180, 180)} {f(x)} {f(y)})">{ch}</text>')
    doc.layer("Bloom", "\n".join(bloom), ROMAN)

    # body: what they brought forth
    body = [POEM[8], POEM[9], "", POEM[10], POEM[11], POEM[12], POEM[13]]
    t = [f'<text x="10" y="{f(128 + i * 4.1)}" font-size="2.35" fill="{INK}">{l}</text>' for i, l in enumerate(body)]
    t.append(f'<text x="10" y="120" font-size="6.5" fill="{INK}">frost flowers</text>')
    doc.layer("Body", "\n".join(t), ITAL)
    return doc


# ---------------------------------------------------------------------------
# SKETCH 3 — "windows": four bus-window panes; big letters f / l·owers / y·o·u,
# poem on wavy lines; frost now set in type, not drawn.
# ---------------------------------------------------------------------------
def panes():
    doc = Doc("frost flowers — sketch 3")
    rnd = random.Random(9)
    INK, PAPER, FD, FL = "#1a1a1a", "#ffffff", "#ffffff", "#8f9aa1"
    A, B, C, D = (0, 52), (52, 84), (84, 150), (150, 200)
    for k, (a, b) in zip("ABCD", (A, B, C, D)):
        doc.defs.append(f'<clipPath id="clip{k}"><rect x="{a}" y="0" width="{b-a}" height="200"/></clipPath>')
    doc.layer("Background", f'<rect width="200" height="200" fill="{PAPER}"/>'
              f'<rect x="{A[0]}" width="{A[1]-A[0]}" height="200" fill="{INK}"/>'
              f'<rect x="{C[0]}" width="{C[1]-C[0]}" height="200" fill="{INK}"/>')

    words = Words(POEM[:10], 1)
    for k, col, seeds in (("A", FD, [(10, 186, 22, 1.4), (46, 150, 10, 1.0), (6, 120, 9, 0.9)]),
                          ("B", FL, [(80, 10, 16, 1.2), (56, 70, 6, 0.8)]),
                          ("C", FD, [(150, 196, 20, 1.2), (86, 4, 12, 1.0), (148, 4, 10, 0.9)]),
                          ("D", FL, [(198, 150, 14, 1.1), (160, 196, 10, 1.0)])):
        out = []
        for cx, cy, r, s in seeds:
            type_frost_flower(doc, out, words, rnd, cx, cy, r, s, col, 0.55)
        doc.layer(f"Frost_{k}", "\n".join(out), f'{ROMAN} clip-path="url(#clip{k})"')

    big = [f'<g clip-path="url(#clipA)"><text x="-30" y="168" font-size="235" fill="{PAPER}">f</text>'
           f'<text x="4" y="40" font-size="6.2" fill="{PAPER}">frost</text></g>',
           f'<g clip-path="url(#clipB)"><text x="44" y="236" font-size="215" fill="{INK}">l</text></g>']
    for ch, x, y, s, r in (("o", 58, 44, 11, -14), ("w", 70, 58, 9.5, 12), ("e", 57, 72, 10, -8),
                           ("r", 68, 86, 8.5, 18), ("s", 56, 99, 9, -20)):
        big.append(f'<text x="{x}" y="{y}" font-size="{s}" fill="{INK}" transform="rotate({r} {x} {y})">{ch}</text>')
    big.append(f'<g clip-path="url(#clipD)"><text x="138" y="88" font-size="128" fill="{INK}">y</text>'
               f'<text x="166" y="128" font-size="44" fill="{INK}">o</text>'
               f'<text x="149" y="190" font-size="104" fill="{INK}">u</text></g>')
    doc.layer("Display_Type", "\n".join(big), ITAL)

    poem = []
    for i, line in enumerate(POEM):
        y = 12.5 + i * 8.45
        rise, amp, ph = (5.0 if i % 2 == 0 else 3.2), 1.1 + 0.5 * (i % 3), i * 1.3
        x0, span = C[0] + 3.5, C[1] - C[0] - 7
        pts = [(x0 + span * k / 12, y + rise / 2 - rise * k / 12 + amp * math.sin(ph + k / 12 * math.pi * 2.2))
               for k in range(13)]
        d = "M" + "L".join(f"{f(px)} {f(py)}" for px, py in pts)
        pid = doc.uid("l")
        doc.defs.append(f'<path id="{pid}" d="{d}"/>')
        Lp = sum(math.dist(pts[k], pts[k + 1]) for k in range(12))
        s = min(2.55, 2.55 * Lp * 0.97 / tw(line, 2.55))
        poem.append(f'<text font-size="{s:.2f}"><textPath href="#{pid}" '
                    f'startOffset="{(Lp - tw(line, s)) / 2 * (i % 2):.2f}">{line}</textPath></text>')
    doc.layer("Poem", "\n".join(poem), f'{ITAL} fill="{PAPER}"')
    doc.layer("Title", f'<text x="153.5" y="9" font-size="4" fill="{INK}" {ITAL}>frost flowers</text>')
    return doc


if __name__ == "__main__":
    window().save("frost-flowers_1_sketch-1.svg")
    gathering().save("frost-flowers_1_sketch-2.svg")
    panes().save("frost-flowers_1_sketch-3.svg")
    window(final=True).save("frost-flowers_2_final.svg")
    print("ok")
