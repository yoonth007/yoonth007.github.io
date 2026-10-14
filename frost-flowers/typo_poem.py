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

    # frosted glass: yesterday's passengers' breath (lines 1-16) set as plain,
    # faint rows of type — denser toward the top and bottom of the window
    words = Words(POEM[:16], 3)
    out, size, lead = [], 1.45, 3.1
    y = 4.0
    while y < 199:
        edge = abs(y - 100) / 100
        op = 0.06 + 0.32 * edge ** 1.6
        out.append(f'<text x="4" y="{f(y)}" font-size="{size}" fill="{FROST}" opacity="{op:.2f}">'
                   f'{words.take(192, size)}</text>')
        y += lead
    holes = [(7, 5, 42, 17), (110, 178, 86, 21)] if final else [(7, 5, 38, 12), (114, 180, 82, 15)]
    clip_rect_minus(doc, "wipe", WIPE, holes)
    doc.layer("Frosted_Glass", "\n".join(out), f'{ROMAN} clip-path="url(#wipe)"')

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
# edges and pile into one loose cluster of letters.
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
    words = []
    for w, (sx, sy), s, it in people:
        # curved route to the meeting point
        mx, my = (sx + C[0]) / 2 + rnd.uniform(-30, 30), (sy + C[1]) / 2 + rnd.uniform(-30, 30)
        pid = doc.uid("w")
        doc.defs.append(f'<path id="{pid}" d="M{f(sx)} {f(sy)}Q{f(mx)} {f(my)} {f(C[0])} {f(C[1])}"/>')
        words.append(f'<text font-size="{s}" fill="{INK}" {ITAL if it else ROMAN}>'
                     f'<textPath href="#{pid}" startOffset="2">{w}</textPath></text>')
    doc.layer("Passengers", "\n".join(words))

    # the bloom: letters of breath / sighs crowding the meeting point
    bloom, letters = [], "breathsighfrostflowers"
    for i in range(260):
        r = 2.5 + abs(rnd.gauss(0, 11)) + (rnd.random() < 0.12) * rnd.uniform(6, 18)
        a = rnd.uniform(0, 2 * math.pi)
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
# poem on wavy lines.
# ---------------------------------------------------------------------------
def panes():
    doc = Doc("frost flowers — sketch 3")
    INK, PAPER = "#1a1a1a", "#ffffff"
    A, B, C, D = (0, 52), (52, 84), (84, 150), (150, 200)
    for k, (a, b) in zip("ABCD", (A, B, C, D)):
        doc.defs.append(f'<clipPath id="clip{k}"><rect x="{a}" y="0" width="{b-a}" height="200"/></clipPath>')
    doc.layer("Background", f'<rect width="200" height="200" fill="{PAPER}"/>'
              f'<rect x="{A[0]}" width="{A[1]-A[0]}" height="200" fill="{INK}"/>'
              f'<rect x="{C[0]}" width="{C[1]-C[0]}" height="200" fill="{INK}"/>')

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
