"""frost flowers — typo poem (20 x 20 cm)

Three sketches and one final composition, written as SVG.
Restrained on purpose: only three techniques are used —
  * Type on a Path
  * Text Wrap (body text flowing around a large letter / a frame)
  * Crop (large letters cut off by the page edge or a frame)
Black and white, one typeface (EB Garamond), no other effects.

usage: python3 typo_poem.py <font_dir> <out_dir>
"""
import math, sys
import numpy as np
from PIL import Image, ImageDraw, ImageFont, ImageFilter

FONTDIR, OUTDIR = sys.argv[1], sys.argv[2]
ITAL_TTF = FONTDIR + "/EBGaramond-Italic.ttf"
_ital = ImageFont.truetype(ITAL_TTF, 1000)

PX = 4  # mask resolution, pixels per mm
INK, PAPER = "#161616", "#ffffff"


def tw(s, size):
    """Advance width (mm) of an italic string at a font size in mm."""
    return _ital.getlength(s) * size / 1000


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

FONT = "font-family=\"'EB Garamond', 'Adobe Garamond Pro', Garamond, serif\" font-style=\"italic\""


class Doc:
    def __init__(self, name):
        self.name, self.defs, self.layers = name, [], []

    def layer(self, lid, body, attrs=""):
        self.layers.append(f'<g id="{lid}" {attrs}>\n{body}\n</g>')

    def save(self, fn):
        svg = ('<svg xmlns="http://www.w3.org/2000/svg" width="200mm" height="200mm" viewBox="0 0 200 200">\n'
               f"<title>{self.name}</title>\n<defs>\n" + "\n".join(self.defs) + "\n</defs>\n"
               f'<rect id="Paper" width="200" height="200" fill="{PAPER}"/>\n'
               + "\n".join(self.layers) + "\n</svg>\n")
        open(f"{OUTDIR}/{fn}", "w").write(svg)


def T(x, y, size, txt, anchor=None, fill=INK):
    a = f' text-anchor="{anchor}"' if anchor else ""
    return f'<text x="{f(x)}" y="{f(y)}" font-size="{f(size)}" fill="{fill}"{a}>{txt}</text>'


# ---------------------------------------------------------------- Text Wrap --
def glyph_mask(ch, x, y, size, canvas=200):
    """Boolean mask (PX per mm) of a big italic glyph whose baseline-left is x, y.
    `canvas` can exceed the page so a cropped glyph is still measured whole."""
    im = Image.new("L", (canvas * PX, canvas * PX), 0)
    ImageDraw.Draw(im).text((x * PX, y * PX), ch, fill=255, anchor="ls",
                            font=ImageFont.truetype(ITAL_TTF, int(size * PX)))
    return np.array(im) > 127


def rect_mask(x, y, w, h):
    m = np.zeros((200 * PX, 200 * PX), bool)
    m[int(y * PX):int((y + h) * PX), int(x * PX):int((x + w) * PX)] = True
    return m


def dilate(mask, mm):
    k = int(mm * PX) * 2 + 1
    im = Image.fromarray(mask.astype(np.uint8) * 255).filter(ImageFilter.MaxFilter(k))
    return np.array(im) > 127


def free_spans(mask, y, size, x0, x1, min_w):
    """Horizontal spans on a text row that the wrap object does not cover."""
    r0, r1 = int((y - size * 0.75) * PX), int((y + size * 0.25) * PX) + 1
    band = mask[max(r0, 0):min(r1, 200 * PX), :].any(axis=0)
    spans, start = [], None
    for c in range(int(x0 * PX), int(x1 * PX)):
        if not band[c] and start is None:
            start = c
        if (band[c] or c == int(x1 * PX) - 1) and start is not None:
            if (c - start) / PX >= min_w:
                spans.append((start / PX, c / PX))
            start = None
    return spans


def as_paragraph(lines):
    """The poem run in as one paragraph, line breaks marked with a slash."""
    return [" / ".join(lines)]


def wrap_flow(lines, mask, x0, x1, y0, y1, size, lead, min_w=12, stanza_gap=()):
    """Set poem lines left-aligned in the free spans around `mask`
    (what Illustrator's Text Wrap does to area type). Each poem line
    starts on a new row; long lines wrap into the next free span."""
    out, y, li = [], y0, 0
    queue = lines[0].split() if lines else []
    while y <= y1 and li < len(lines):
        for sx, ex in free_spans(mask, y, size, x0, x1, min_w):
            seg = []
            while queue and tw(" ".join(seg + [queue[0]]), size) <= ex - sx:
                seg.append(queue.pop(0))
            if seg:
                out.append(T(sx, y, size, " ".join(seg)))
            if not queue:
                break
        if not queue:
            li += 1
            if li < len(lines):
                queue = lines[li].split()
                if li in stanza_gap:
                    y += lead * 0.6
        y += lead
    return out, li


# ------------------------------------------------------------- Type on Path --
def ellipse_path(cx, cy, rx, ry, rot_deg, start_deg=200):
    """Closed path around an ellipse, clockwise on screen, starting at start_deg."""
    pts = []
    for k in range(0, 361, 4):
        t = math.radians(start_deg + k)
        x, y = rx * math.cos(t), ry * math.sin(t)
        r = math.radians(rot_deg)
        pts.append((cx + x * math.cos(r) - y * math.sin(r), cy + x * math.sin(r) + y * math.cos(r)))
    return "M" + "L".join(f"{f(x)} {f(y)}" for x, y in pts)


def counter_of(mask_glyph, seed_xy):
    """Inner counter (hole) of a glyph: flood fill from seed, return coords in mm."""
    h, w = mask_glyph.shape
    sx, sy = int(seed_xy[0] * PX), int(seed_xy[1] * PX)
    seen = np.zeros_like(mask_glyph)
    stack = [(sy, sx)]
    while stack:
        y, x = stack.pop()
        if 0 <= y < h and 0 <= x < w and not seen[y, x] and not mask_glyph[y, x]:
            seen[y, x] = True
            stack += [(y + 1, x), (y - 1, x), (y, x + 1), (y, x - 1)]
    ys, xs = np.nonzero(seen)
    return xs / PX, ys / PX


def fit_ellipse(xs, ys):
    """Centre, semi-axes and rotation of a pixel blob (second moments)."""
    cx, cy = xs.mean(), ys.mean()
    cov = np.cov(np.vstack([xs - cx, ys - cy]))
    vals, vecs = np.linalg.eigh(cov)
    a, b = 2 * math.sqrt(vals[1]), 2 * math.sqrt(vals[0])
    rot = math.degrees(math.atan2(vecs[1, 1], vecs[0, 1]))
    return cx, cy, a, b, rot


# ---------------------------------------------------------------------------
# SKETCH 1 / FINAL — "a single frost petal"
# A giant italic o, cropped by the right edge, is the bus window. The poem
# wraps around it; inside its counter — the spot wiped clear with breath and
# finger — one line runs on a path.
# ---------------------------------------------------------------------------
def petal(final=False):
    doc = Doc("frost flowers — final" if final else "frost flowers — sketch 1")
    O_X, O_Y, O_S = (92, 196, 360) if final else (88, 194, 350)

    whole = glyph_mask("o", O_X, O_Y, O_S, canvas=360)
    doc.layer("Crop_Letter", f'<text x="{O_X}" y="{O_Y}" font-size="{O_S}" fill="{INK}">o</text>', FONT)

    # Type on a Path: inside the wiped-clear counter
    gy, gx = np.nonzero(whole)
    xs, ys = counter_of(whole, ((gx.min() + gx.max()) / 2 / PX, (gy.min() + gy.max()) / 2 / PX))
    cx, cy, a, b, rot = fit_ellipse(xs, ys)
    if rot > 90: rot -= 180
    if rot < -90: rot += 180
    if abs(rot) > 45:  # keep the long axis horizontal-ish
        a, b, rot = b, a, rot - 90 * (1 if rot > 0 else -1)
    k = 0.80
    doc.defs.append(f'<path id="petal" d="{ellipse_path(cx, cy, a * k, b * k, rot)}"/>')
    ps = 3.4 if final else 3.2
    doc.layer("Type_on_a_Path",
              f'<text font-size="{ps}" fill="{INK}"><textPath href="#petal" startOffset="2%">'
              f'I wipe away a single frost petal  —  and press my forehead to the glass.'
              f'</textPath></text>', FONT)

    # Text Wrap: the rest of the poem around the o
    body = [l for i, l in enumerate(POEM) if i not in (17, 18)]
    hole = np.zeros_like(whole)
    hole[(ys * PX).astype(int), (xs * PX).astype(int)] = True
    page = 200 * PX
    wrap = dilate((whole | hole)[:page, :page], 3.2)  # text wraps around the whole o, counter included
    x0, x1 = (14, 188) if final else (12, 188)
    head = []
    if final:
        head = [T(14, 22, 7.2, "frost flowers"), T(14, 28.5, 2.3, "the dawn city bus, a poem in type")]
        y0 = 40
    else:
        y0 = 20
    lines, used = wrap_flow(as_paragraph(body), wrap, x0, x1, y0, 192, 3.9 if final else 3.8,
                            6.4 if final else 6.3, min_w=8)
    doc.layer("Text_Wrap", "\n".join(head + lines), FONT)
    return doc


# ---------------------------------------------------------------------------
# SKETCH 2 — "breath": the whole poem as one breath, a single line of type
# on a path spiralling in toward the last word, "you".
# ---------------------------------------------------------------------------
def breath():
    doc = Doc("frost flowers — sketch 2")
    text = "   ".join(POEM)
    assert text.endswith(" you.")
    text = text[:-5]
    cx, cy, r_out, r_in = 100, 101, 88, 15

    def spiral(turns):
        pts, n = [], int(turns * 120)
        for i in range(n + 1):
            t = i / n
            ang = -math.pi / 2 + t * turns * 2 * math.pi  # start at top, clockwise
            r = r_out - (r_out - r_in) * t
            pts.append((cx + r * math.cos(ang), cy + r * math.sin(ang)))
        return pts

    best = None
    for turns in range(4, 16):
        pts = spiral(turns)
        L = sum(math.dist(pts[i], pts[i + 1]) for i in range(len(pts) - 1))
        s = L * 0.985 / tw(text, 1)
        gap = (r_out - r_in) / turns
        if gap >= 1.55 * s and (best is None or abs(gap / s - 1.9) < abs(best[2] / best[1] - 1.9)):
            best = (pts, s, gap)
    pts, s, _ = best
    doc.defs.append('<path id="breath" d="M' + "L".join(f"{f(x)} {f(y)}" for x, y in pts) + '"/>')
    doc.layer("Type_on_a_Path", f'<text font-size="{s:.2f}" fill="{INK}"><textPath href="#breath">{text}</textPath></text>', FONT)
    doc.layer("Center", T(cx, cy + 3, 10, "you.", "middle"), FONT)
    doc.layer("Title", T(196, 196, 3, "frost flowers", "end"), FONT)
    return doc


# ---------------------------------------------------------------------------
# SKETCH 3 — "window": the word frost cropped inside a bus window; the poem
# wraps around the window frame.
# ---------------------------------------------------------------------------
def window():
    doc = Doc("frost flowers — sketch 3")
    WX, WY, WW, WH = 70, 40, 116, 88
    doc.defs.append(f'<clipPath id="win"><rect x="{WX}" y="{WY}" width="{WW}" height="{WH}"/></clipPath>')
    doc.layer("Crop_Window",
              f'<g clip-path="url(#win)"><text x="{WX - 16}" y="{WY + WH + 18}" font-size="118" fill="{INK}">frost</text></g>'
              f'<rect x="{WX}" y="{WY}" width="{WW}" height="{WH}" fill="none" stroke="{INK}" stroke-width="0.2"/>', FONT)
    lines, _ = wrap_flow(as_paragraph(POEM), dilate(rect_mask(WX, WY, WW, WH), 5), 14, 186, 18, 192,
                         3.4, 5.6, min_w=10)
    doc.layer("Text_Wrap", "\n".join(lines), FONT)
    doc.layer("Caption", T(WX + WW, WY - 2.5, 2.4, "flowers", "end"), FONT)
    return doc


if __name__ == "__main__":
    petal().save("frost-flowers_1_sketch-1.svg")
    breath().save("frost-flowers_1_sketch-2.svg")
    window().save("frost-flowers_1_sketch-3.svg")
    petal(final=True).save("frost-flowers_2_final.svg")
    print("ok")
