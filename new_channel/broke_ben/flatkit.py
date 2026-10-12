"""FlatKit: a small, precise flat-vector drawing kit (2x supersampled, then downscaled).

All coordinates are logical pixels; Pen multiplies by S internally.
Characters are built from one proportion table (unit R = head radius),
so every pose keeps the same anatomy.
"""
import math
import os
from PIL import Image, ImageDraw, ImageFilter, ImageFont

FONT_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..', 'assets', 'fonts')
_FONTS = {}

INK = (29, 33, 45, 255)


def font(kind, size):
    key = (kind, size)
    if key not in _FONTS:
        name, wght = {'display': ('Anton-Regular.ttf', None), 'bold': ('Oswald-Variable.ttf', 700),
                      'semi': ('Oswald-Variable.ttf', 600), 'body': ('Oswald-Variable.ttf', 400),
                      'type': ('SpecialElite-Regular.ttf', None)}[kind]
        f = ImageFont.truetype(os.path.join(FONT_DIR, name), int(size))
        if wght:
            f.set_variation_by_axes([wght])
        _FONTS[key] = f
    return _FONTS[key]


def rgba(c, a=255):
    if isinstance(c, str):
        c = c.lstrip('#')
        return tuple(int(c[i:i + 2], 16) for i in (0, 2, 4)) + (a,)
    return tuple(c[:3]) + ((c[3] if len(c) > 3 else a),)


def shade(c, k):
    c = rgba(c)
    return tuple(max(0, min(255, int(v * k))) for v in c[:3]) + (c[3],)


class Pen:
    def __init__(self, w, h, S=2, bg=(0, 0, 0, 0)):
        self.w, self.h, self.S = w, h, S
        self.img = Image.new('RGBA', (w * S, h * S), rgba(bg))
        self.d = ImageDraw.Draw(self.img)

    # -- geometry helpers
    def _p(self, pts):
        return [(x * self.S, y * self.S) for x, y in pts]

    def _b(self, box):
        return [v * self.S for v in box]

    def layer(self):
        return Pen(self.w, self.h, self.S)

    def paste(self, other, blur=0, rotate=0, center=None):
        im = other.img
        if rotate:
            c = (center[0] * self.S, center[1] * self.S) if center else None
            im = im.rotate(rotate, resample=Image.BICUBIC, center=c)
        if blur:
            im = im.filter(ImageFilter.GaussianBlur(blur * self.S))
        self.img.alpha_composite(im)
        self.d = ImageDraw.Draw(self.img)

    # -- primitives
    def rect(self, box, fill, outline=None, width=0, r=0):
        if r:
            self.d.rounded_rectangle(self._b(box), r * self.S, fill=rgba(fill) if fill else None,
                                     outline=rgba(outline) if outline else None, width=int(width * self.S))
        else:
            self.d.rectangle(self._b(box), fill=rgba(fill) if fill else None,
                             outline=rgba(outline) if outline else None, width=int(width * self.S))

    def ellipse(self, box, fill, outline=None, width=0):
        self.d.ellipse(self._b(box), fill=rgba(fill) if fill else None,
                       outline=rgba(outline) if outline else None, width=int(round(width * self.S)))

    def circle(self, cx, cy, r, fill, outline=None, width=0):
        self.ellipse((cx - r, cy - r, cx + r, cy + r), fill, outline, width)

    def poly(self, pts, fill, outline=None, width=0):
        self.d.polygon(self._p(pts), fill=rgba(fill) if fill else None)
        if outline and width:
            self.line(list(pts) + [pts[0]], width, outline)

    def line(self, pts, width, fill, caps=True):
        p = self._p(pts)
        self.d.line(p, fill=rgba(fill), width=max(1, int(round(width * self.S))), joint='curve')
        if caps:
            r = width * self.S / 2
            for x, y in (p[0], p[-1]):
                self.d.ellipse((x - r, y - r, x + r, y + r), fill=rgba(fill))

    def arc(self, box, a0, a1, width, fill):
        self.d.arc(self._b(box), a0, a1, fill=rgba(fill), width=max(1, int(round(width * self.S))))

    def chord(self, box, a0, a1, fill, outline=None, width=0):
        self.d.chord(self._b(box), a0, a1, fill=rgba(fill), outline=rgba(outline) if outline else None,
                     width=int(round(width * self.S)))

    def limb(self, pts, width, fill, outline=INK, ow=4):
        self.line(pts, width + 2 * ow, outline)
        self.line(pts, width, fill)

    # -- text
    def text_w(self, s, kind, size):
        return font(kind, size * self.S).getlength(s) / self.S

    def text(self, xy, s, kind, size, fill, anchor='la', stroke=0, stroke_fill=INK):
        self.d.text((xy[0] * self.S, xy[1] * self.S), s, font=font(kind, size * self.S), fill=rgba(fill),
                    anchor=anchor, stroke_width=int(stroke * self.S), stroke_fill=rgba(stroke_fill))

    def vgrad(self, box, top, bot):
        x0, y0, x1, y1 = [int(v * self.S) for v in box]
        top, bot = rgba(top), rgba(bot)
        for y in range(y0, y1):
            t = (y - y0) / max(1, (y1 - y0 - 1))
            self.d.line([(x0, y), (x1, y)], fill=tuple(int(top[i] + (bot[i] - top[i]) * t) for i in range(4)))

    def glow(self, cx, cy, r, color, alpha=120):
        lay = self.layer()
        lay.circle(cx, cy, r * 0.6, rgba(color, alpha))
        self.paste(lay, blur=r * 0.35)

    def done(self):
        return self.img.resize((self.w, self.h), Image.LANCZOS)


# ====================================================================== character
def _dir(a):
    r = math.radians(a)
    return math.sin(r), math.cos(r)


def _step(p, a, length):
    dx, dy = _dir(a)
    return (p[0] + dx * length, p[1] + dy * length)


# absolute limb angles: 0 = down, +90 = screen right, 180 = up
POSES = {
    'stand':     dict(la=(-10, -4), ra=(10, 4), ll=(-4, -2), rl=(4, 2)),
    'hold_head': dict(la=(-150, -176), ra=(150, 176), ll=(-7, -3), rl=(7, 3)),
    'point_left': dict(la=(-92, -88), ra=(40, -39), ll=(-5, -2), rl=(5, 2)),
    'point_right': dict(la=(-40, 39), ra=(92, 88), ll=(-5, -2), rl=(5, 2)),
    'read':      dict(la=(-20, 145), ra=(20, -145), ll=(-4, -2), rl=(4, 2), prop='paper'),
    'arms_up':   dict(la=(-140, -168), ra=(140, 168), ll=(-14, 8), rl=(20, -6)),
    'slump':     dict(la=(-6, 2), ra=(6, -2), ll=(-6, -2), rl=(6, 2)),
    'wave':      dict(la=(-10, -4), ra=(140, 168), ll=(-4, -2), rl=(4, 2)),
}


class Look:
    def __init__(self, hair='spiky', hair_color='#3A2A20', top='hoodie', top_color='#3E8E63',
                 pants_color='#2B3550', skin='#F0D2B6', shoe='#20242E'):
        self.hair, self.hair_color, self.top = hair, rgba(hair_color), top
        self.top_color, self.pants, self.skin, self.shoe = rgba(top_color), rgba(pants_color), rgba(skin), rgba(shoe)


def char_height(R):
    return 5.86 * R   # feet to hair tip


def draw_char(pen, x, y, R, look, pose='stand', emo='neutral', gaze=(0, 0), extras=()):
    """Feet baseline at (x, y). R = head radius in px."""
    P = POSES[pose]
    ow = 0.075 * R
    # shadow
    sh = pen.layer()
    sh.ellipse((x - 0.95 * R, y - 0.12 * R, x + 0.95 * R, y + 0.14 * R), (0, 0, 0, 55))
    pen.paste(sh, blur=R * 0.04)

    def pt(dx, dy):
        return (x + dx * R, y + dy * R)

    hipL, hipR = pt(-0.27, -1.86), pt(0.27, -1.86)
    shL, shR = pt(-0.46, -3.26), pt(0.46, -3.26)
    head = pt(0, -4.64)

    # legs + shoes
    for hip, (a1, a2), side in ((hipL, P['ll'], -1), (hipR, P['rl'], 1)):
        knee = _step(hip, a1, 0.94 * R)
        foot = _step(knee, a2, 0.94 * R)
        pen.limb([hip, knee, foot], 0.38 * R, look.pants, ow=ow)
        fx = foot[0] + side * 0.12 * R
        pen.ellipse((fx - 0.3 * R, foot[1] - 0.12 * R, fx + 0.3 * R, foot[1] + 0.16 * R), look.shoe, INK, ow)

    # torso
    pen.rect((x - 0.58 * R, y - 3.52 * R, x + 0.58 * R, y - 1.72 * R), look.top_color, INK, ow, r=0.32 * R)
    pen.rect((x - 0.58 * R, y - 2.02 * R, x + 0.58 * R, y - 1.66 * R), look.pants, INK, ow, r=0.12 * R)
    dark = shade(look.top_color, 0.78)
    if look.top == 'hoodie':
        pen.rect((x - 0.32 * R, y - 2.62 * R, x + 0.32 * R, y - 2.2 * R), dark, INK, ow * 0.7, r=0.1 * R)
        for s in (-1, 1):
            pen.line([pt(s * 0.13, -3.42), pt(s * 0.15, -2.95)], 0.05 * R, (245, 245, 240))
            pen.circle(x + s * 0.15 * R, y - 2.93 * R, 0.05 * R, (245, 245, 240))
    else:  # jacket
        pen.line([pt(0, -3.45), pt(0, -2.05)], 0.05 * R, dark)
        for s in (-1, 1):
            pen.poly([pt(s * 0.04, -3.5), pt(s * 0.36, -3.5), pt(s * 0.08, -3.05)], (238, 238, 232), INK, ow * 0.6)

    # neck, ears, head
    pen.rect((x - 0.15 * R, y - 3.78 * R, x + 0.15 * R, y - 3.42 * R), look.skin, INK, ow * 0.8)
    for s in (-1, 1):
        pen.circle(head[0] + s * 0.98 * R, head[1] + 0.1 * R, 0.17 * R, look.skin, INK, ow)
    pen.circle(head[0], head[1], R, look.skin, INK, ow)
    _hair(pen, head, R, look, ow)
    _face(pen, head, R, look, emo, gaze, ow)
    if 'sweat' in extras:
        _drop(pen, head[0] + 1.12 * R, head[1] - 0.35 * R, 0.17 * R)
        _drop(pen, head[0] - 1.2 * R, head[1] - 0.05 * R, 0.12 * R)

    # arms
    hands = []
    for sh_, (a1, a2) in ((shL, P['la']), (shR, P['ra'])):
        el = _step(sh_, a1, 0.86 * R)
        hand = _step(el, a2, 0.8 * R)
        pen.limb([sh_, el, hand], 0.31 * R, look.top_color, ow=ow)
        hands.append(hand)
    if P.get('prop') == 'paper':
        (lx, ly), (rx, ry) = hands
        pen.rect((lx - 0.12 * R, ly - 0.35 * R, rx + 0.12 * R, ly + 0.8 * R), (250, 250, 245), INK, ow * 0.8,
                 r=0.05 * R)
        for i in range(4):
            yy = ly - 0.12 * R + i * 0.22 * R
            pen.line([(lx + 0.15 * R, yy), (rx - 0.15 * R - (0.2 * R if i == 3 else 0), yy)], 0.04 * R,
                     (170, 172, 178))
    for hx, hy in hands:
        pen.circle(hx, hy, 0.17 * R, look.skin, INK, ow)
    return dict(head=head, hands=hands, top=y - char_height(R))


def _drop(pen, x, y, s):
    pen.poly([(x, y - 1.6 * s), (x + 0.82 * s, y - 0.1 * s), (x - 0.82 * s, y - 0.1 * s)], (120, 200, 255))
    pen.circle(x, y, s, (120, 200, 255))
    pen.circle(x - 0.3 * s, y - 0.1 * s, 0.25 * s, (235, 248, 255))


def _hair(pen, c, R, look, ow):
    cx, cy = c
    pts = []
    if look.hair == 'spiky':
        n = 16
        for i in range(n + 1):
            th = math.radians(168 - 156 * i / n)
            r = R * (1.24 if i % 2 else 1.02)
            pts.append((cx + r * math.cos(th), cy - r * math.sin(th)))
        fr = [(cx + 0.97 * R, cy - 0.22 * R)]
        k = 7
        for i in range(1, k):
            fx = cx + R * (0.85 - 1.7 * i / k)
            fr.append((fx, cy - (0.48 + (0.13 if i % 2 else 0)) * R))
        fr.append((cx - 0.97 * R, cy - 0.22 * R))
        pts += fr
    else:  # 'side' sweep
        for i in range(25):
            th = math.radians(8 + 164 * i / 24)
            pts.append((cx + 1.07 * R * math.cos(th), cy - 1.07 * R * math.sin(th)))
        pts += [(cx - 1.0 * R, cy - 0.18 * R), (cx - 0.7 * R, cy - 0.5 * R), (cx - 0.2 * R, cy - 0.62 * R),
                (cx + 0.45 * R, cy - 0.5 * R), (cx + 0.9 * R, cy - 0.28 * R), (cx + 1.04 * R, cy - 0.12 * R)]
    pen.poly(pts, look.hair_color, INK, ow)


def _face(pen, c, R, look, emo, gaze, ow):
    cx, cy = c
    big = emo in ('shock',)
    rx, ry = (0.26, 0.32) if big else (0.22, 0.27)
    pr = 0.065 if big else 0.11
    for s in (-1, 1):
        ex, ey = cx + s * 0.36 * R, cy + 0.02 * R
        pen.ellipse((ex - rx * R, ey - ry * R, ex + rx * R, ey + ry * R), (255, 255, 255), INK, ow * 0.8)
        px, py = ex + gaze[0] * 0.08 * R, ey + gaze[1] * 0.08 * R + (0.04 * R if emo == 'tired' else 0)
        pen.circle(px, py, pr * R, INK)
        pen.circle(px - 0.035 * R, py - 0.04 * R, 0.03 * R, (255, 255, 255))
        if emo == 'tired':
            pen.chord((ex - rx * R, ey - ry * R, ex + rx * R, ey + ry * R), 180, 360, look.skin)
            pen.line([(ex - rx * R, ey), (ex + rx * R, ey)], ow * 0.9, INK)
        # brows: outer end first
        o, i_ = ex + s * 0.2 * R, ex - s * 0.17 * R
        if emo == 'worried':
            pen.line([(o, ey - 0.38 * R), (i_, ey - 0.5 * R)], 0.075 * R, INK)
        elif emo == 'shock':
            pen.arc((ex - 0.22 * R, ey - 0.62 * R, ex + 0.22 * R, ey - 0.4 * R), 200, 340, 0.075 * R, INK)
        elif emo == 'tired':
            pen.line([(o, ey - 0.4 * R), (i_, ey - 0.36 * R)], 0.075 * R, INK)
        elif emo == 'confident':
            pen.line([(o, ey - 0.44 * R), (i_, ey - 0.38 * R)], 0.075 * R, INK)
        else:
            pen.arc((ex - 0.2 * R, ey - 0.52 * R, ex + 0.2 * R, ey - 0.36 * R), 200, 340, 0.075 * R, INK)
    my = cy + 0.52 * R
    mouth_dark = (70, 24, 30)
    if emo == 'shock':
        pen.ellipse((cx - 0.13 * R, my - 0.14 * R, cx + 0.13 * R, my + 0.2 * R), mouth_dark, INK, ow * 0.8)
        pen.chord((cx - 0.09 * R, my + 0.02 * R, cx + 0.09 * R, my + 0.18 * R), 0, 180, (220, 90, 100))
    elif emo == 'happy':
        pen.chord((cx - 0.27 * R, my - 0.24 * R, cx + 0.27 * R, my + 0.2 * R), 0, 180, mouth_dark, INK, ow * 0.8)
        pen.chord((cx - 0.13 * R, my + 0.02 * R, cx + 0.13 * R, my + 0.19 * R), 0, 180, (220, 90, 100))
    elif emo == 'confident':
        pen.arc((cx - 0.24 * R, my - 0.3 * R, cx + 0.24 * R, my + 0.08 * R), 25, 155, 0.07 * R, INK)
    elif emo == 'worried':
        w = [(cx + (-0.22 + 0.088 * k) * R, my + (0.04 if k % 2 else -0.04) * R) for k in range(6)]
        pen.line(w, 0.06 * R, INK)
    elif emo == 'tired':
        pen.arc((cx - 0.2 * R, my - 0.02 * R, cx + 0.2 * R, my + 0.22 * R), 200, 340, 0.06 * R, INK)
    else:
        pen.line([(cx - 0.14 * R, my), (cx + 0.14 * R, my)], 0.06 * R, INK)


def rim(pen, draw_fn, color=(255, 255, 255, 255), size=10):
    """Draw something on its own layer with a solid outer rim (thumbnail pop)."""
    lay = pen.layer()
    draw_fn(lay)
    a = lay.img.getchannel('A').filter(ImageFilter.MaxFilter(int(size * pen.S) | 1))
    r = Image.new('RGBA', lay.img.size, rgba(color))
    r.putalpha(a)
    pen.img.alpha_composite(r)
    pen.img.alpha_composite(lay.img)
    pen.d = ImageDraw.Draw(pen.img)


def caption(pen, words, hi, y=1000, size=50):
    """Caption pill in its own band at the bottom; highlighted words in yellow."""
    space = pen.text_w(' ', 'semi', size)
    widths = [pen.text_w(w, 'semi', size) for w in words]
    total = sum(widths) + space * (len(words) - 1)
    lay = pen.layer()
    lay.rect((pen.w / 2 - total / 2 - 34, y - size * 0.95, pen.w / 2 + total / 2 + 34, y + size * 0.85),
             (14, 16, 22, 215), r=size * 0.9)
    pen.paste(lay)
    x = pen.w / 2 - total / 2
    for w, ww in zip(words, widths):
        col = (255, 201, 60) if w.lower().strip('.,!?') in hi else (250, 250, 245)
        pen.text((x, y), w, 'semi', size, col, anchor='lm')
        x += ww + space
