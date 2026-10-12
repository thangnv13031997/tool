"""Small drawing helpers on top of Pillow.

Pillow does not anti-alias shapes, so everything is drawn on a tile that is
S times bigger and then shrunk with Image.reduce(S). The Pen class hides the
scale factor: callers work in normal pixels.
"""
import math
from PIL import Image, ImageDraw

INK = (27, 27, 27, 255)
CREAM = (255, 253, 245, 255)


def hex_rgba(h, a=255):
    if isinstance(h, (tuple, list)):
        return tuple(h) if len(h) == 4 else (h[0], h[1], h[2], a)
    h = str(h).lstrip('#')
    if len(h) == 3:
        h = ''.join(c * 2 for c in h)
    try:
        return (int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16), a)
    except ValueError:
        return (27, 27, 27, a)


def mix(c1, c2, t):
    c1 = hex_rgba(c1)
    c2 = hex_rgba(c2)
    return tuple(int(round(c1[i] + (c2[i] - c1[i]) * t)) for i in range(4))


def shade(c, f):
    """f<1 darker, f>1 lighter (towards white)."""
    c = hex_rgba(c)
    if f < 1:
        return (int(c[0] * f), int(c[1] * f), int(c[2] * f), c[3])
    t = min(1.0, f - 1)
    return mix(c, (255, 255, 255, c[3]), t)


_FV = {}


class Pen:
    """Supersampled drawing surface.

    Pillow writes RGBA values without blending, so any colour with partial
    alpha is drawn on a small temporary layer and alpha-composited. Colours
    with alpha 0 erase (useful for cut-outs).
    """

    def __init__(self, w, h, S=2, bg=(0, 0, 0, 0), reduce=None):
        self.S = S
        self.R = int(reduce or S)
        self.w, self.h = w, h
        self.img = Image.new('RGBA', (int(w * S), int(h * S)), bg)
        self.d = ImageDraw.Draw(self.img)
        self.ox = 0.0
        self.oy = 0.0
        self._sx = 0
        self._sy = 0
        self._layer = False

    # --- coordinate helpers
    def P(self, x, y):
        return ((x + self.ox) * self.S - self._sx, (y + self.oy) * self.S - self._sy)

    def _pts(self, pts):
        return [self.P(x, y) for x, y in pts]

    @staticmethod
    def _soft(*cols):
        for c in cols:
            if c is not None and len(c) == 4 and 0 < c[3] < 255:
                return True
        return False

    def _with_layer(self, x0, y0, x1, y1, fn):
        S = self.S
        X0 = int(max(0, math.floor((x0 + self.ox) * S)))
        Y0 = int(max(0, math.floor((y0 + self.oy) * S)))
        X1 = int(min(self.img.width, math.ceil((x1 + self.ox) * S)))
        Y1 = int(min(self.img.height, math.ceil((y1 + self.oy) * S)))
        if X1 <= X0 or Y1 <= Y0:
            return
        layer = Image.new('RGBA', (X1 - X0, Y1 - Y0), (0, 0, 0, 0))
        saved = self.d
        self.d = ImageDraw.Draw(layer)
        self._sx, self._sy, self._layer = X0, Y0, True
        try:
            fn()
        finally:
            self.d = saved
            self._sx, self._sy, self._layer = 0, 0, False
        self.img.alpha_composite(layer, dest=(X0, Y0))

    # --- primitives
    def line(self, pts, color=INK, width=4, cap=True):
        if len(pts) < 2:
            return
        if not self._layer and self._soft(color):
            xs = [p[0] for p in pts]
            ys = [p[1] for p in pts]
            m = width + 2
            return self._with_layer(min(xs) - m, min(ys) - m, max(xs) + m, max(ys) + m,
                                    lambda: self.line(pts, color, width, cap))
        sp = self._pts(pts)
        wpx = max(1, int(round(width * self.S)))
        self.d.line(sp, fill=color, width=wpx, joint='curve')
        if cap:
            r = width * self.S / 2.0
            for (x, y) in (sp[0], sp[-1]):
                self.d.ellipse((x - r, y - r, x + r, y + r), fill=color)

    def circle(self, cx, cy, r, fill=None, outline=None, width=0):
        self.ellipse(cx, cy, r, r, fill, outline, width)

    def ellipse(self, cx, cy, rx, ry, fill=None, outline=None, width=0):
        if not self._layer and self._soft(fill, outline if width > 0 else None):
            m = width + 2
            return self._with_layer(cx - rx - m, cy - ry - m, cx + rx + m, cy + ry + m,
                                    lambda: self.ellipse(cx, cy, rx, ry, fill, outline, width))
        x, y = self.P(cx, cy)
        RX, RY = rx * self.S, ry * self.S
        if outline is not None and width > 0:
            W = width * self.S
            self.d.ellipse((x - RX - W / 2, y - RY - W / 2, x + RX + W / 2, y + RY + W / 2), fill=outline)
            if fill is not None:
                self.d.ellipse((x - RX + W / 2, y - RY + W / 2, x + RX - W / 2, y + RY - W / 2), fill=fill)
        elif fill is not None:
            self.d.ellipse((x - RX, y - RY, x + RX, y + RY), fill=fill)

    def poly(self, pts, fill=None, outline=None, width=0):
        if not self._layer and self._soft(fill, outline if width > 0 else None):
            xs = [p[0] for p in pts]
            ys = [p[1] for p in pts]
            m = width + 2
            return self._with_layer(min(xs) - m, min(ys) - m, max(xs) + m, max(ys) + m,
                                    lambda: self.poly(pts, fill, outline, width))
        sp = self._pts(pts)
        if fill is not None:
            self.d.polygon(sp, fill=fill)
        if outline is not None and width > 0:
            self.line(list(pts) + [pts[0]], outline, width, cap=True)

    def rect(self, x0, y0, x1, y1, fill=None, outline=None, width=0, r=0):
        if not self._layer and self._soft(fill, outline if width > 0 else None):
            m = width + 2
            return self._with_layer(min(x0, x1) - m, min(y0, y1) - m, max(x0, x1) + m, max(y0, y1) + m,
                                    lambda: self.rect(x0, y0, x1, y1, fill, outline, width, r))
        a = self.P(x0, y0)
        b = self.P(x1, y1)
        box = (min(a[0], b[0]), min(a[1], b[1]), max(a[0], b[0]), max(a[1], b[1]))
        if box[2] - box[0] < 1 or box[3] - box[1] < 1:
            return
        w = int(round(width * self.S)) if outline else 0
        if r > 0:
            rr = min(r * self.S, (box[2] - box[0]) / 2, (box[3] - box[1]) / 2)
            self.d.rounded_rectangle(box, radius=rr, fill=fill, outline=outline, width=w)
        else:
            self.d.rectangle(box, fill=fill, outline=outline, width=w)

    def arc(self, cx, cy, rx, ry, a0, a1, color=INK, width=4, steps=24):
        """Arc as a polyline with round caps. Angles in degrees, 0 = right, 90 = down."""
        pts = []
        for i in range(steps + 1):
            a = math.radians(a0 + (a1 - a0) * i / steps)
            pts.append((cx + rx * math.cos(a), cy + ry * math.sin(a)))
        self.line(pts, color, width)

    def bezier(self, p0, p1, p2, p3=None, color=INK, width=4, steps=24):
        self.line(bezier_pts(p0, p1, p2, p3, steps), color, width)

    def text(self, xy, s, font, fill=INK, anchor='mm', stroke=0, stroke_fill=None):
        if not self._layer and self._soft(fill, stroke_fill if stroke else None):
            bx = font.getbbox(s, anchor=anchor, stroke_width=int(stroke))
            m = 4
            return self._with_layer(xy[0] + bx[0] - m, xy[1] + bx[1] - m, xy[0] + bx[2] + m, xy[1] + bx[3] + m,
                                    lambda: self.text(xy, s, font, fill, anchor, stroke, stroke_fill))
        if self.S != 1:
            key = (id(font), self.S)
            f2 = _FV.get(key)
            if f2 is None:
                f2 = font.font_variant(size=max(1, int(round(font.size * self.S))))
                _FV[key] = f2
            font = f2
        self.d.text(self.P(*xy), s, font=font, fill=fill, anchor=anchor,
                    stroke_width=int(stroke * self.S), stroke_fill=stroke_fill)

    def done(self):
        if self.R == 1:
            return self.img
        return self.img.reduce(self.R)


def bezier_pts(p0, p1, p2, p3=None, steps=24):
    pts = []
    for i in range(steps + 1):
        t = i / steps
        if p3 is None:
            x = (1 - t) ** 2 * p0[0] + 2 * (1 - t) * t * p1[0] + t * t * p2[0]
            y = (1 - t) ** 2 * p0[1] + 2 * (1 - t) * t * p1[1] + t * t * p2[1]
        else:
            x = ((1 - t) ** 3 * p0[0] + 3 * (1 - t) ** 2 * t * p1[0]
                 + 3 * (1 - t) * t * t * p2[0] + t ** 3 * p3[0])
            y = ((1 - t) ** 3 * p0[1] + 3 * (1 - t) ** 2 * t * p1[1]
                 + 3 * (1 - t) * t * t * p2[1] + t ** 3 * p3[1])
        pts.append((x, y))
    return pts


def ease_out_back(t):
    c1 = 1.70158
    c3 = c1 + 1
    t = max(0.0, min(1.0, t))
    return 1 + c3 * (t - 1) ** 3 + c1 * (t - 1) ** 2


def ease_in_out(t):
    t = max(0.0, min(1.0, t))
    return t * t * (3 - 2 * t)


def lerp(a, b, t):
    return a + (b - a) * t
