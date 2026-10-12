"""Painted dark backgrounds for horror scenes.

Every background returns a Layered result:
  img    - RGB painting (painted fairly bright; the lighting pass darkens it)
  fg     - optional RGBA foreground layer that moves faster (parallax)
  lights - light sources used by fx.Lighting
  ambient- how bright unlit areas stay (0..1)
Coordinates of lights are fractions of width/height.
"""
import math
import random
import numpy as np
from PIL import Image, ImageDraw, ImageFilter
from .gfx import Pen, hex_rgba, shade, mix

GROUND_Y = 0.88


class Layered:
    def __init__(self, img, fg=None, lights=None, ambient=0.42, ground=GROUND_Y, tint=(1.0, 1.0, 1.0)):
        self.img = img
        self.fg = fg
        self.lights = lights or []
        self.ambient = ambient
        self.ground = ground
        self.tint = tint


# ------------------------------------------------------------------ helpers
def gradient(w, h, top, bottom, mid=None, mid_at=0.6):
    t = np.linspace(0, 1, h, dtype=np.float32)[:, None]
    a = np.array(hex_rgba(top)[:3], np.float32)
    b = np.array(hex_rgba(bottom)[:3], np.float32)
    if mid is not None:
        m = np.array(hex_rgba(mid)[:3], np.float32)
        k1 = np.clip(t / mid_at, 0, 1)
        k2 = np.clip((t - mid_at) / (1 - mid_at), 0, 1)
        col = np.where(t < mid_at, a + (m - a) * k1, m + (b - m) * k2)
    else:
        col = a + (b - a) * t
    arr = np.broadcast_to(col.reshape(h, 1, 3), (h, w, 3))
    rgba = np.concatenate([arr, np.full((h, w, 1), 255, np.float32)], axis=2)
    return Image.fromarray(rgba.astype(np.uint8), 'RGBA')


DESIGN_W = 1075.0
_R = [2]


def _pen(W, H, S):
    return Pen(W, H, S, reduce=_R[0])


def new_pen(W, H, S, top, bottom, mid=None, mid_at=0.6):
    pen = _pen(W, H, S)
    pen.img = gradient(int(W * S), int(H * S), top, bottom, mid, mid_at)
    pen.d = ImageDraw.Draw(pen.img)
    return pen


def L(kind, x, y, r=0.3, col='#FFD9A0', flicker=False, power=1.0, **kw):
    d = dict(kind=kind, x=x, y=y, r=r, col=col, flicker=flicker, power=power)
    d.update(kw)
    return d


def stars(pen, W, H, n=90, ymax=0.5, seed=3):
    rnd = random.Random(seed)
    for _ in range(n):
        x, y = rnd.random() * W, rnd.random() * H * ymax
        pen.circle(x, y, rnd.choice((0.8, 1.0, 1.3)) * W / 1920, fill=(200, 210, 230, rnd.randint(70, 190)))


def moon(pen, W, H, x=0.82, y=0.16, r=0.045, phase=True):
    pen.circle(x * W, y * H, r * H * 2.2, fill=(160, 175, 210, 18))
    pen.circle(x * W, y * H, r * H * 1.4, fill=(170, 185, 215, 30))
    pen.circle(x * W, y * H, r * H, fill=hex_rgba('#D8DCE6'))
    if phase:
        pen.circle(x * W - r * H * 0.3, y * H + r * H * 0.25, r * H * 0.18, fill=hex_rgba('#C3C8D4'))
        pen.circle(x * W + r * H * 0.25, y * H - r * H * 0.3, r * H * 0.12, fill=hex_rgba('#C3C8D4'))


def haze(pen, W, H, y, h, col='#2A3550', a=110):
    c = hex_rgba(col)
    steps = 14
    for i in range(steps):
        k = 1 - abs(i - steps / 2) / (steps / 2)
        yy = y * H - h * H / 2 + i * h * H / steps
        pen.rect(0, yy, W, yy + h * H / steps + 1, fill=(c[0], c[1], c[2], int(a * k)))


def pine(pen, x, base, h, col, w=None):
    w = w or h * 0.32
    layers = 5
    for i in range(layers):
        y0 = base - h * (0.18 + i * 0.17)
        ww = w * (1 - i * 0.16)
        pen.poly([(x - ww / 2, y0), (x + ww / 2, y0), (x, y0 - h * 0.3)], fill=col)
    pen.rect(x - w * 0.05, base - h * 0.2, x + w * 0.05, base, fill=col)


def tree_line(pen, W, H, base, hmin, hmax, col, seed=1, step=0.035):
    rnd = random.Random(seed)
    x = -0.02
    while x < 1.04:
        h = rnd.uniform(hmin, hmax) * H
        pine(pen, x * W, base * H, h, col)
        x += step * rnd.uniform(0.7, 1.3)


def bare_tree(pen, x, base, h, col, seed=0, width=None):
    rnd = random.Random(seed)
    w = width or h * 0.035

    def branch(x0, y0, ang, ln, wd, depth):
        x1 = x0 + math.sin(ang) * ln
        y1 = y0 - math.cos(ang) * ln
        pen.line([(x0, y0), (x1, y1)], col, wd)
        if depth > 0:
            for d in (-1, 1):
                branch(x1, y1, ang + d * rnd.uniform(0.3, 0.7), ln * rnd.uniform(0.55, 0.75), wd * 0.62, depth - 1)
    branch(x, base, rnd.uniform(-0.05, 0.05), h * 0.42, w, 4)


def window(pen, x0, y0, x1, y1, lit=False, frame='#2A2F38', glass='#1A2436', light='#E8C77A', curtain=None, blinds=False):
    pen.rect(x0 - 6, y0 - 6, x1 + 6, y1 + 6, fill=hex_rgba(frame))
    pen.rect(x0, y0, x1, y1, fill=hex_rgba(light if lit else glass))
    if not lit:
        pen.poly([(x0, y1), (x0 + (x1 - x0) * 0.35, y0), (x0 + (x1 - x0) * 0.55, y0), (x0 + (x1 - x0) * 0.2, y1)],
                 fill=(255, 255, 255, 14))
    mx = (x0 + x1) / 2
    my = (y0 + y1) / 2
    pen.line([(mx, y0), (mx, y1)], hex_rgba(frame), 5)
    pen.line([(x0, my), (x1, my)], hex_rgba(frame), 5)
    if blinds:
        for i in range(1, 12):
            y = y0 + (y1 - y0) * i / 12
            pen.line([(x0, y), (x1, y)], (0, 0, 0, 70), 3)
    if curtain:
        c = hex_rgba(curtain)
        pen.poly([(x0 - 14, y0 - 10), (x0 + (x1 - x0) * 0.22, y0 - 10), (x0 + (x1 - x0) * 0.12, y1 + 20), (x0 - 14, y1 + 20)], fill=c)
        pen.poly([(x1 + 14, y0 - 10), (x1 - (x1 - x0) * 0.22, y0 - 10), (x1 - (x1 - x0) * 0.12, y1 + 20), (x1 + 14, y1 + 20)], fill=c)


def door(pen, x0, y0, x1, y1, col='#4A3B30', frame='#2B231D', ajar=0.0, inside='#06070A', knob='#B8A27A', panels=True):
    pen.rect(x0 - 10, y0 - 10, x1 + 10, y1, fill=hex_rgba(frame))
    pen.rect(x0, y0, x1, y1, fill=hex_rgba(inside))
    w = (x1 - x0) * (1 - ajar)
    pen.rect(x0, y0, x0 + w, y1, fill=hex_rgba(col))
    if panels and w > (x1 - x0) * 0.4:
        for (a, b) in ((0.08, 0.42), (0.52, 0.92)):
            pen.rect(x0 + w * 0.15, y0 + (y1 - y0) * a, x0 + w * 0.85, y0 + (y1 - y0) * b, outline=shade(hex_rgba(col), 0.75), width=4)
    pen.circle(x0 + w * 0.86, y0 + (y1 - y0) * 0.55, (x1 - x0) * 0.035, fill=hex_rgba(knob))


def floorboards(pen, W, H, y0, col, n=10, perspective=True):
    pen.rect(0, y0, W, H, fill=hex_rgba(col))
    dark = shade(hex_rgba(col), 0.8)
    for i in range(1, 7):
        y = y0 + (H - y0) * (i / 7) ** 1.4
        pen.line([(0, y), (W, y)], dark, 2)
    if perspective:
        for i in range(-n, n + 1):
            xb = W / 2 + i * W / n * 1.4
            xt = W / 2 + i * W / n * 0.5
            pen.line([(xt, y0), (xb, H)], dark, 2)


def wallpaper(pen, x0, y0, x1, y1, col, pattern='stripes', seed=2):
    pen.rect(x0, y0, x1, y1, fill=hex_rgba(col))
    d = shade(hex_rgba(col), 0.9)
    if pattern == 'stripes':
        w = (x1 - x0) / 48
        for i in range(0, 48, 2):
            pen.rect(x0 + i * w, y0, x0 + (i + 1) * w, y1, fill=d)
    elif pattern == 'damask':
        rnd = random.Random(seed)
        for yy in range(int(y0), int(y1), 90):
            for xx in range(int(x0), int(x1), 90):
                ox = 45 if (yy // 90) % 2 else 0
                pen.ellipse(xx + ox, yy + 45, 12, 20, fill=d)
    elif pattern == 'tiles':
        s = (x1 - x0) / 26
        for i in range(27):
            pen.line([(x0 + i * s, y0), (x0 + i * s, y1)], d, 2)
        yy = y0
        while yy < y1:
            pen.line([(x0, yy), (x1, yy)], d, 2)
            yy += s


def frame_pic(pen, x, y, w, h, tilt=0, col='#3A2E25'):
    c = math.cos(math.radians(tilt))
    s = math.sin(math.radians(tilt))

    def R(px, py):
        return (x + px * c - py * s, y + px * s + py * c)
    pen.poly([R(-w / 2, -h / 2), R(w / 2, -h / 2), R(w / 2, h / 2), R(-w / 2, h / 2)], fill=hex_rgba(col))
    pen.poly([R(-w / 2 + 10, -h / 2 + 10), R(w / 2 - 10, -h / 2 + 10), R(w / 2 - 10, h / 2 - 10), R(-w / 2 + 10, h / 2 - 10)],
             fill=hex_rgba('#566070'))
    pen.circle(*R(0, -h * 0.08), w * 0.12, fill=hex_rgba('#7D8693'))
    pen.ellipse(*R(0, h * 0.25), w * 0.22, h * 0.16, fill=hex_rgba('#7D8693'))


def lamp_shade(pen, x, y, w, col='#C9B28A', on=True):
    pen.poly([(x - w * 0.35, y), (x + w * 0.35, y), (x + w * 0.5, y + w * 0.55), (x - w * 0.5, y + w * 0.55)], fill=hex_rgba(col))
    if on:
        pen.ellipse(x, y + w * 0.55, w * 0.5, w * 0.08, fill=hex_rgba('#FFF1C9'))


def ceiling_light(pen, x, y, w, on=True, cord=0.0):
    if cord:
        pen.line([(x, 0), (x, y)], hex_rgba('#20242B'), 3)
    pen.poly([(x - w * 0.5, y), (x + w * 0.5, y), (x + w * 0.3, y - w * 0.3), (x - w * 0.3, y - w * 0.3)], fill=hex_rgba('#3A4048'))
    pen.ellipse(x, y + 4, w * 0.2, w * 0.12, fill=hex_rgba('#FFF4D6' if on else '#565A60'))


def soft(img, r):
    return img.filter(ImageFilter.GaussianBlur(r))


# ------------------------------------------------------------------ backgrounds
def bg_plain_dark(W, H, S, o):
    pen = new_pen(W, H, S, '#07090E', '#141A24')
    return Layered(pen.done().convert('RGB'), ambient=0.6)


def _exterior_sky(W, H, S, o, horizon=0.62):
    t = o.get('time', 'night')
    if t == 'dusk':
        pen = new_pen(W, H, S, '#141A33', '#6B4A55', mid='#2E3352', mid_at=0.45)
    elif t == 'day':
        pen = new_pen(W, H, S, '#7C8EA3', '#B7BCC0')
    else:
        pen = new_pen(W, H, S, '#04060B', '#1A2438', mid='#0B1020', mid_at=0.45)
        stars(pen, W, H, ymax=horizon * 0.8)
        if o.get('moon', True):
            moon(pen, W, H, x=o.get('moon_x', 0.8))
    return pen


def _amb(o, base):
    t = o.get('time', 'night')
    return {'day': 0.92, 'dusk': 0.62}.get(t, base)


def bg_bus_stop(W, H, S, o):
    pen = _exterior_sky(W, H, S, o)
    g = GROUND_Y * H
    # far buildings
    rnd = random.Random(5)
    x = 0
    while x < W:
        bw = rnd.uniform(0.07, 0.14) * W
        bh = rnd.uniform(0.18, 0.4) * H
        pen.rect(x, g - 0.18 * H - bh, x + bw, g - 0.1 * H, fill=hex_rgba('#141B28'))
        for wy in range(int(g - 0.17 * H - bh + 20), int(g - 0.14 * H), 46):
            for wx in range(int(x + 14), int(x + bw - 20), 38):
                if rnd.random() < 0.12:
                    pen.rect(wx, wy, wx + 16, wy + 22, fill=hex_rgba('#C9A35A'))
        x += bw + rnd.uniform(4, 30)
    # road + sidewalk
    pen.rect(0, g - 0.1 * H, W, g + 0.02 * H, fill=hex_rgba('#2A303A'))
    for i in range(10):
        pen.rect(i * W / 9, g - 0.05 * H, i * W / 9 + W / 22, g - 0.042 * H, fill=hex_rgba('#8C8770'))
    pen.rect(0, g, W, H, fill=hex_rgba('#3A404A'))
    pen.rect(0, g, W, g + 10, fill=hex_rgba('#555B66'))
    # shelter
    sx0, sx1 = 0.12 * W, 0.42 * W
    top = g - 0.5 * H
    pen.rect(sx0, top, sx1, top + 18, fill=hex_rgba('#2E353F'))
    for xx in (sx0 + 10, sx1 - 18):
        pen.rect(xx, top, xx + 9, g, fill=hex_rgba('#2E353F'))
    pen.rect(sx0 + 20, top + 30, sx1 - 24, g - 0.12 * H, fill=(110, 140, 170, 40))
    pen.rect(sx0 + 30, g - 0.14 * H, sx1 - 34, g - 0.12 * H, fill=hex_rgba('#3A2E25'))
    pen.rect(sx0 + 40, g - 0.12 * H, sx0 + 50, g, fill=hex_rgba('#2A2018'))
    pen.rect(sx1 - 50, g - 0.12 * H, sx1 - 40, g, fill=hex_rgba('#2A2018'))
    # bus sign
    px = 0.52 * W
    pen.rect(px - 5, g - 0.62 * H, px + 5, g, fill=hex_rgba('#3B424C'))
    pen.rect(px - 46, g - 0.62 * H, px + 46, g - 0.53 * H, fill=hex_rgba('#2C5D8F'), r=6)
    pen.rect(px - 30, g - 0.6 * H, px + 30, g - 0.555 * H, fill=hex_rgba('#E8E8E8'), r=3)
    # street light
    lx = 0.72 * W
    pen.rect(lx - 7, g - 0.7 * H, lx + 7, g, fill=hex_rgba('#2B3038'))
    pen.line([(lx, g - 0.7 * H), (lx - 0.06 * W, g - 0.72 * H)], hex_rgba('#2B3038'), 10)
    pen.ellipse(lx - 0.065 * W, g - 0.705 * H, 34, 12, fill=hex_rgba('#FFE7A8'))
    lights = [L('cone', 0.655, (GROUND_Y - 0.7), r=0.75, spread=0.26, col='#FFD58A', flicker=o.get('lights') == 'flicker', power=1.15)]
    return Layered(pen.done().convert('RGB'), lights=lights, ambient=_amb(o, 0.4))


def bg_bus_interior(W, H, S, o):
    pen = new_pen(W, H, S, '#1D232C', '#2A2F36')
    g = GROUND_Y * H
    # windows band
    wy0, wy1 = 0.18 * H, 0.5 * H
    pen.rect(0, wy0 - 30, W, wy1 + 30, fill=hex_rgba('#3B4350'))
    for i in range(5):
        x0 = 0.02 * W + i * 0.2 * W
        pen.rect(x0, wy0, x0 + 0.17 * W, wy1, fill=hex_rgba('#06080D'), r=14)
        if o.get('time', 'night') == 'night':
            rnd = random.Random(i)
            for _ in range(3):
                xx = x0 + rnd.random() * 0.17 * W
                pen.line([(xx, wy0 + 0.6 * (wy1 - wy0)), (xx + 60, wy0 + 0.6 * (wy1 - wy0))], (230, 190, 120, 70), 4)
        pen.rect(x0 + 6, wy0 + 6, x0 + 0.17 * W - 6, wy0 + 26, fill=(255, 255, 255, 10), r=8)
    # ceiling + lights strip
    pen.rect(0, 0, W, 0.12 * H, fill=hex_rgba('#2F353E'))
    for i in range(4):
        x = 0.12 * W + i * 0.25 * W
        pen.rect(x - 0.07 * W, 0.095 * H, x + 0.07 * W, 0.115 * H, fill=hex_rgba('#E9F0E0'), r=6)
    # poles + rails
    pen.line([(0, 0.15 * H), (W, 0.15 * H)], hex_rgba('#9AA2AC'), 8)
    for x in (0.18, 0.5, 0.82):
        pen.line([(x * W, 0.15 * H), (x * W, g)], hex_rgba('#C7B04A'), 9)
    # seats row
    for i in range(6):
        x0 = 0.01 * W + i * 0.17 * W
        pen.rect(x0, g - 0.36 * H, x0 + 0.12 * W, g - 0.16 * H, fill=hex_rgba('#3C4E6B'), r=16)
        pen.rect(x0 - 6, g - 0.17 * H, x0 + 0.14 * W, g - 0.12 * H, fill=hex_rgba('#344560'), r=10)
        pen.rect(x0 + 0.05 * W, g - 0.12 * H, x0 + 0.07 * W, g, fill=hex_rgba('#20252C'))
    floorboards(pen, W, H, g, '#2B2F35', perspective=False)
    lights = []
    flick = o.get('lights') == 'flicker'
    if o.get('lights') != 'off':
        for i in range(4):
            lights.append(L('cone', 0.12 + i * 0.25, 0.11, r=0.85, spread=0.2, col='#DDEBD0', flicker=flick and i % 2 == 1, power=0.8))
    fg = _pen(W, H, S)
    fg.rect(-20, H * 0.9, W * 0.22, H + 20, fill=hex_rgba('#1E2838'), r=30)
    fg.rect(W * 0.8, H * 0.88, W + 20, H + 20, fill=hex_rgba('#1E2838'), r=30)
    return Layered(pen.done().convert('RGB'), fg=fg.done(), lights=lights, ambient=0.5 if o.get('lights') != 'off' else 0.22)


def bg_bus_front(W, H, S, o):
    """Driver area: windshield to the dark road, rear-view mirror."""
    pen = new_pen(W, H, S, '#161B22', '#22272E')
    g = GROUND_Y * H
    pen.rect(0.05 * W, 0.08 * H, 0.95 * W, 0.5 * H, fill=hex_rgba('#05070B'), r=20)
    # road in windshield
    pen.poly([(0.42 * W, 0.3 * H), (0.58 * W, 0.3 * H), (0.9 * W, 0.5 * H), (0.1 * W, 0.5 * H)], fill=hex_rgba('#1A1D22'))
    for i in range(4):
        y = 0.32 * H + i * 0.045 * H
        w = 4 + i * 6
        pen.rect(0.5 * W - w / 2, y, 0.5 * W + w / 2, y + 10 + i * 6, fill=hex_rgba('#D6C88A'))
    tree_line(pen, W, H, 0.31, 0.04, 0.09, hex_rgba('#080A0E'), seed=4, step=0.02)
    # dashboard
    pen.rect(0, 0.5 * H, W, 0.66 * H, fill=hex_rgba('#2A2F36'))
    for i in range(3):
        pen.circle(0.62 * W + i * 0.07 * W, 0.58 * H, 0.025 * H, fill=hex_rgba('#0E1A12'), outline=hex_rgba('#4A5560'), width=4)
        pen.line([(0.62 * W + i * 0.07 * W, 0.58 * H), (0.62 * W + i * 0.07 * W + 14, 0.58 * H - 12)], hex_rgba('#E05040'), 3)
    # mirror
    pen.line([(0.5 * W, 0.0), (0.5 * W, 0.1 * H)], hex_rgba('#30353C'), 10)
    pen.rect(0.4 * W, 0.1 * H, 0.6 * W, 0.18 * H, fill=hex_rgba('#3A3F47'), r=16)
    pen.rect(0.41 * W, 0.112 * H, 0.59 * W, 0.168 * H, fill=hex_rgba('#0B0E13'), r=12)
    pen.rect(0, 0.66 * H, W, H, fill=hex_rgba('#1F2329'))
    lights = [L('rect', 0.5, 0.58, r=0.25, w=0.3, h=0.08, col='#7FD69A', power=0.35),
              L('point', 0.5, 0.05, r=0.5, col='#DDEBD0', power=0.5, flicker=o.get('lights') == 'flicker')]
    return Layered(pen.done().convert('RGB'), lights=lights, ambient=0.38)


def bg_road_night(W, H, S, o):
    pen = _exterior_sky(W, H, S, o, horizon=0.5)
    hz = 0.5 * H
    haze(pen, W, H, 0.46, 0.2)
    tree_line(pen, W, H, 0.52, 0.12, 0.28, hex_rgba('#06080C'), seed=8, step=0.025)
    pen.rect(0, hz + 0.02 * H, W, H, fill=hex_rgba('#0F1216'))
    pen.poly([(0.47 * W, hz + 0.02 * H), (0.53 * W, hz + 0.02 * H), (1.1 * W, H), (-0.1 * W, H)], fill=hex_rgba('#24272C'))
    for i in range(7):
        k = (i / 7) ** 1.7
        y = hz + 0.03 * H + k * (H - hz)
        w = 3 + k * 26
        pen.rect(0.5 * W - w / 2, y, 0.5 * W + w / 2, y + 6 + k * 50, fill=hex_rgba('#D8CB8A'))
    lights = [L('cone_up', 0.5, 1.0, r=0.62, spread=0.55, col='#FFF0C8', power=1.0)]
    return Layered(pen.done().convert('RGB'), lights=lights, ambient=_amb(o, 0.3))


def bg_car_interior(W, H, S, o):
    pen = new_pen(W, H, S, '#0C0F14', '#171B21')
    # windshield view
    pen.poly([(0.08 * W, 0.08 * H), (0.92 * W, 0.08 * H), (0.98 * W, 0.55 * H), (0.02 * W, 0.55 * H)], fill=hex_rgba('#04060A'))
    tree_line(pen, W, H, 0.42, 0.06, 0.16, hex_rgba('#080A0F'), seed=2, step=0.025)
    pen.poly([(0.45 * W, 0.42 * H), (0.55 * W, 0.42 * H), (0.85 * W, 0.55 * H), (0.15 * W, 0.55 * H)], fill=hex_rgba('#25282D'))
    pen.rect(0.495 * W, 0.44 * H, 0.505 * W, 0.47 * H, fill=hex_rgba('#D8CB8A'))
    pen.rect(0.49 * W, 0.49 * H, 0.51 * W, 0.53 * H, fill=hex_rgba('#D8CB8A'))
    # pillars + dash
    pen.poly([(0, 0), (0.1 * W, 0), (0.03 * W, 0.6 * H), (0, 0.6 * H)], fill=hex_rgba('#14171C'))
    pen.poly([(W, 0), (0.9 * W, 0), (0.97 * W, 0.6 * H), (W, 0.6 * H)], fill=hex_rgba('#14171C'))
    pen.rect(0, 0.55 * H, W, 0.7 * H, fill=hex_rgba('#22262C'), r=30)
    pen.rect(0.43 * W, 0.58 * H, 0.57 * W, 0.66 * H, fill=hex_rgba('#0A1A22'), r=10)
    pen.rect(0.45 * W, 0.6 * H, 0.55 * W, 0.64 * H, fill=hex_rgba('#3FA7C9'), r=6)
    # mirror
    pen.rect(0.43 * W, 0.04 * H, 0.57 * W, 0.11 * H, fill=hex_rgba('#2A2F36'), r=14)
    pen.rect(0.44 * W, 0.05 * H, 0.56 * W, 0.1 * H, fill=hex_rgba('#06080C'), r=10)
    pen.rect(0, 0.7 * H, W, H, fill=hex_rgba('#191C21'))
    lights = [L('rect', 0.5, 0.62, r=0.3, w=0.12, h=0.05, col='#7FCBE6', power=0.5),
              L('cone_up', 0.5, 0.56, r=0.2, spread=0.4, col='#FFF0C8', power=0.6)]
    return Layered(pen.done().convert('RGB'), lights=lights, ambient=0.3)


def bg_gas_station(W, H, S, o):
    pen = _exterior_sky(W, H, S, o)
    g = GROUND_Y * H
    tree_line(pen, W, H, 0.62, 0.12, 0.25, hex_rgba('#06080C'), seed=11)
    pen.rect(0, 0.6 * H, W, H, fill=hex_rgba('#2B2F35'))
    # canopy
    pen.rect(0.18 * W, 0.17 * H, 0.98 * W, 0.24 * H, fill=hex_rgba('#D9D4C8'))
    pen.rect(0.18 * W, 0.235 * H, 0.98 * W, 0.255 * H, fill=hex_rgba('#B02A2A'))
    for x in (0.25, 0.6, 0.92):
        pen.rect(x * W - 14, 0.255 * H, x * W + 14, g, fill=hex_rgba('#CFCAC0'))
    for i in range(6):
        x = 0.24 * W + i * 0.12 * W
        pen.rect(x, 0.255 * H, x + 0.08 * W, 0.27 * H, fill=hex_rgba('#F4F3EA'))
    # pumps
    for x in (0.42, 0.76):
        pen.rect(x * W - 46, g - 0.24 * H, x * W + 46, g, fill=hex_rgba('#C9C3B5'), r=8)
        pen.rect(x * W - 34, g - 0.21 * H, x * W + 34, g - 0.15 * H, fill=hex_rgba('#162129'), r=4)
        pen.rect(x * W - 46, g - 0.25 * H, x * W + 46, g - 0.235 * H, fill=hex_rgba('#B02A2A'))
    # store on the left
    pen.rect(-10, 0.3 * H, 0.16 * W, g, fill=hex_rgba('#3F4652'))
    pen.rect(0.01 * W, 0.42 * H, 0.14 * W, 0.72 * H, fill=hex_rgba('#9C9070'))
    for i in range(3):
        pen.rect(0.02 * W, 0.47 * H + i * 0.08 * H, 0.13 * W, 0.48 * H + i * 0.08 * H, fill=hex_rgba('#5A5040'))
    pen.rect(0.03 * W, 0.34 * H, 0.13 * W, 0.39 * H, fill=hex_rgba('#C93A3A'), r=6)
    pen.rect(0, g, W, H, fill=hex_rgba('#33373E'))
    lights = [L('rect', 0.58, 0.26, r=0.75, w=0.8, h=0.04, col='#F2F4EA', power=1.0, flicker=o.get('lights') == 'flicker'),
              L('rect', 0.075, 0.57, r=0.3, w=0.14, h=0.3, col='#F0DFA8', power=0.45)]
    return Layered(pen.done().convert('RGB'), lights=lights, ambient=_amb(o, 0.34))


def bg_store_night(W, H, S, o):
    pen = new_pen(W, H, S, '#2C323A', '#3A3F46')
    g = GROUND_Y * H
    pen.rect(0, 0, W, 0.08 * H, fill=hex_rgba('#23282F'))
    for i in range(3):
        x = 0.18 * W + i * 0.32 * W
        pen.rect(x - 0.11 * W, 0.06 * H, x + 0.11 * W, 0.08 * H, fill=hex_rgba('#F3F6EE'))
    # shelves
    for i in range(3):
        x0 = 0.05 * W + i * 0.31 * W
        pen.rect(x0, 0.22 * H, x0 + 0.26 * W, g, fill=hex_rgba('#353A42'))
        rnd = random.Random(i)
        for r_ in range(5):
            y = 0.25 * H + r_ * 0.12 * H
            pen.rect(x0 + 8, y + 0.08 * H, x0 + 0.26 * W - 8, y + 0.09 * H, fill=hex_rgba('#6A717B'))
            xx = x0 + 14
            while xx < x0 + 0.26 * W - 40:
                bw = rnd.randint(18, 34)
                col = rnd.choice(['#5A4646', '#46525A', '#6A6040', '#4A5A48', '#544A5E', '#6E6A60', '#3E4248'])
                pen.rect(xx, y + 0.08 * H - rnd.randint(30, 60) * H / 1080, xx + bw, y + 0.08 * H, fill=hex_rgba(col))
                xx += bw + 4
    floorboards(pen, W, H, g, '#585E66', perspective=True)
    flick = o.get('lights') == 'flicker'
    lights = [L('cone', 0.18 + i * 0.32, 0.07, r=0.9, spread=0.3, col='#EEF4E8', power=0.8, flicker=flick and i == 1) for i in range(3)]
    if o.get('lights') == 'off':
        lights = []
    return Layered(pen.done().convert('RGB'), lights=lights, ambient=0.55 if lights else 0.2)


def bg_store_counter(W, H, S, o):
    """Night clerk view: cash counter in front, big window to the dark pumps outside, OPEN sign, door bell.
    Put the clerk behind the counter (x 0.25-0.45). Outside figures: x 0.55-0.85 with "far": true, y about 0.62."""
    pen = new_pen(W, H, S, '#262B33', '#30353D')
    g = GROUND_Y * H
    # ceiling + tube lights
    pen.rect(0, 0, W, 0.07 * H, fill=hex_rgba('#1F242B'))
    for x in (0.22, 0.62):
        pen.rect(x * W - 0.1 * W, 0.055 * H, x * W + 0.1 * W, 0.072 * H, fill=hex_rgba('#F3F6EE'))
    # big window to the lot
    wx0, wy0, wx1, wy1 = 0.43 * W, 0.13 * H, 0.97 * W, 0.66 * H
    pen.rect(wx0 - 12, wy0 - 12, wx1 + 12, wy1 + 12, fill=hex_rgba('#3B424C'))
    sky = gradient(int((wx1 - wx0) * S), int((wy1 - wy0) * S), '#03050A', '#151C29').convert('RGBA')
    pen.img.alpha_composite(sky, (int(wx0 * S), int(wy0 * S)))
    pen.d = ImageDraw.Draw(pen.img)
    sub = _pen(wx1 - wx0, wy1 - wy0, S)
    sw, sh = wx1 - wx0, wy1 - wy0
    tree_line(sub, sw, sh, 0.62, 0.18, 0.34, hex_rgba('#05070B'), seed=23, step=0.05)
    sub.rect(0, 0.6 * sh, sw, sh, fill=hex_rgba('#1A1E24'))
    # canopy edge + one pump far away
    sub.rect(0.1 * sw, 0.14 * sh, 1.1 * sw, 0.2 * sh, fill=hex_rgba('#BFBAAE'))
    sub.rect(0.1 * sw, 0.195 * sh, 1.1 * sw, 0.215 * sh, fill=hex_rgba('#9A2626'))
    for x in (0.18, 0.86):
        sub.rect(x * sw - 6, 0.215 * sh, x * sw + 6, 0.84 * sh, fill=hex_rgba('#B5B0A6'))
    sub.rect(0.52 * sw - 24, 0.6 * sh, 0.52 * sw + 24, 0.84 * sh, fill=hex_rgba('#A9A497'), r=4)
    sub.rect(0.52 * sw - 17, 0.63 * sh, 0.52 * sw + 17, 0.7 * sh, fill=hex_rgba('#162129'), r=2)
    sub.rect(0, 0.84 * sh, sw, sh, fill=hex_rgba('#22262C'))
    for i in range(7):
        xx = (0.05 + i * 0.15) * sw
        sub.line([(xx, 0.88 * sh), (xx + 0.05 * sw, 0.88 * sh)], (210, 210, 190, 40), 3)
    pen.img.alpha_composite(sub.img, (int(wx0 * S), int(wy0 * S)))
    pen.d = ImageDraw.Draw(pen.img)
    for k in (0.36, 0.68):
        x = wx0 + (wx1 - wx0) * k
        pen.line([(x, wy0), (x, wy1)], hex_rgba('#3B424C'), 10)
    pen.poly([(wx0 + 30, wy1), (wx0 + 140, wy0), (wx0 + 190, wy0), (wx0 + 80, wy1)], fill=(255, 255, 255, 10))
    # OPEN neon sign in the window
    nx, ny = 0.86 * W, 0.2 * H
    pen.rect(nx - 52, ny - 20, nx + 52, ny + 20, fill=hex_rgba('#2A0D10'), r=10)
    try:
        pen.text((nx, ny), 'OPEN', _font_digits(26), fill=hex_rgba('#FF4A55'))
    except Exception:
        pen.rect(nx - 40, ny - 8, nx + 40, ny + 8, fill=hex_rgba('#FF4A55'))
    # back wall left: cigarette / lottery rack + clock slot + camera monitor
    pen.rect(0.02 * W, 0.12 * H, 0.38 * W, 0.5 * H, fill=hex_rgba('#353A42'))
    rnd = random.Random(31)
    for r_ in range(4):
        y = 0.15 * H + r_ * 0.085 * H
        pen.rect(0.03 * W, y + 0.06 * H, 0.37 * W, y + 0.068 * H, fill=hex_rgba('#6A717B'))
        xx = 0.035 * W
        while xx < 0.36 * W:
            bw = rnd.randint(10, 18)
            col = rnd.choice(['#7A3B3B', '#3B5A7A', '#7A6A3B', '#4A6A4A', '#E0DCCF', '#5A4A6E'])
            pen.rect(xx, y + 0.06 * H - rnd.randint(20, 34) * H / 605, xx + bw, y + 0.06 * H, fill=hex_rgba(col))
            xx += bw + 3
    pen.rect(0.05 * W, 0.53 * H, 0.15 * W, 0.6 * H, fill=hex_rgba('#14181E'), r=3)
    pen.rect(0.056 * W, 0.538 * H, 0.144 * W, 0.592 * H, fill=hex_rgba('#3E5560'))
    # floor
    floorboards(pen, W, H, g - 0.02 * H, '#4E545C', perspective=True)
    # counter in the foreground (separate layer so the clerk stands behind it)
    fg = _pen(W, H, S)
    cy = 0.7 * H
    fg.rect(-20, cy, 0.5 * W, H + 20, fill=hex_rgba('#4A4038'))
    fg.rect(-20, cy - 0.025 * H, 0.52 * W, cy + 0.01 * H, fill=hex_rgba('#6E6458'))
    for i in range(1, 4):
        x = 0.125 * W * i
        fg.line([(x, cy + 0.03 * H), (x, H)], hex_rgba('#3C332C'), 4)
    # register
    rx = 0.08 * W
    fg.rect(rx, cy - 0.12 * H, rx + 0.12 * W, cy - 0.025 * H, fill=hex_rgba('#2B2E33'), r=6)
    fg.rect(rx + 0.012 * W, cy - 0.11 * H, rx + 0.108 * W, cy - 0.07 * H, fill=hex_rgba('#5FA37A'), r=3)
    fg.rect(rx + 0.03 * W, cy - 0.06 * H, rx + 0.1 * W, cy - 0.035 * H, fill=hex_rgba('#3C4046'), r=3)
    # coffee cup + candy rack
    fg.rect(0.36 * W, cy - 0.06 * H, 0.38 * W, cy - 0.025 * H, fill=hex_rgba('#E6E1D6'), r=2)
    fg.rect(0.42 * W, cy - 0.09 * H, 0.49 * W, cy - 0.025 * H, fill=hex_rgba('#3A3F47'), r=3)
    for i in range(3):
        fg.rect(0.425 * W, cy - 0.085 * H + i * 0.02 * H, 0.485 * W, cy - 0.072 * H + i * 0.02 * H,
                fill=hex_rgba(['#B84040', '#D9A441', '#4077B8'][i]))
    flick = o.get('lights') == 'flicker'
    lights = [] if o.get('lights') == 'off' else [
        L('cone', 0.22, 0.07, r=0.9, spread=0.3, col='#EEF4E8', power=0.85, flicker=flick),
        L('cone', 0.62, 0.07, r=0.8, spread=0.3, col='#EEF4E8', power=0.6)]
    lights.append(L('point', 0.86, 0.2, r=0.18, col='#FF4A55', power=0.55, flicker=True))
    lights.append(L('rect', 0.72, 0.3, r=0.35, w=0.5, h=0.1, col='#E8EFE0', power=0.35))
    lights.append(L('point', 0.1, 0.57, r=0.12, col='#7FC8A0', power=0.4))
    return Layered(pen.done().convert('RGB'), fg=fg.done(), lights=lights, ambient=0.5 if o.get('lights') != 'off' else 0.18)


def bg_forest(W, H, S, o):
    pen = _exterior_sky(W, H, S, o, horizon=0.55)
    g = GROUND_Y * H
    haze(pen, W, H, 0.5, 0.35)
    tree_line(pen, W, H, 0.6, 0.25, 0.4, hex_rgba('#0D121A'), seed=21, step=0.03)
    haze(pen, W, H, 0.64, 0.16, a=70)
    tree_line(pen, W, H, 0.72, 0.35, 0.55, hex_rgba('#090D13'), seed=22, step=0.045)
    pen.rect(0, 0.7 * H, W, H, fill=hex_rgba('#141A16'))
    # path
    pen.poly([(0.46 * W, 0.7 * H), (0.54 * W, 0.7 * H), (0.75 * W, H), (0.25 * W, H)], fill=hex_rgba('#2A2620'))
    rnd = random.Random(23)
    for _ in range(60):
        x = rnd.random() * W
        y = 0.72 * H + rnd.random() * 0.28 * H
        pen.line([(x, y), (x + rnd.uniform(-6, 6), y - rnd.uniform(10, 26))], hex_rgba('#1E2A1E'), 3)
    # big trunks at sides (foreground)
    fg = _pen(W, H, S)
    for x, w in ((0.03, 0.06), (0.95, 0.07), (0.16, 0.035)):
        fg.rect(x * W - w * W / 2, -10, x * W + w * W / 2, H + 10, fill=hex_rgba('#05070A'))
    bare_tree(fg, 0.9 * W, 0.05 * H, 0.6 * H, hex_rgba('#05070A'), seed=4)
    lights = [L('point', o.get('moon_x', 0.8), 0.16, r=0.9, col='#9FB2D8', power=0.5)]
    if o.get('flashlight'):
        lights.append(L('cone_side', 0.5, 0.6, r=0.6, spread=0.18, col='#FFF2CC', power=1.2))
    return Layered(pen.done().convert('RGB'), fg=fg.done(), lights=lights, ambient=_amb(o, 0.34), tint=(0.85, 0.95, 1.1))


def bg_campsite(W, H, S, o):
    pen = _exterior_sky(W, H, S, o, horizon=0.55)
    g = GROUND_Y * H
    haze(pen, W, H, 0.52, 0.3)
    tree_line(pen, W, H, 0.62, 0.25, 0.42, hex_rgba('#0B1016'), seed=31, step=0.03)
    tree_line(pen, W, H, 0.7, 0.35, 0.5, hex_rgba('#070A0F'), seed=32, step=0.05)
    pen.rect(0, 0.68 * H, W, H, fill=hex_rgba('#1A1F1A'))
    # tent
    tx = 0.25 * W
    pen.poly([(tx - 0.13 * W, g), (tx, g - 0.32 * H), (tx + 0.13 * W, g)], fill=hex_rgba('#3D6B4F'))
    pen.poly([(tx - 0.04 * W, g), (tx, g - 0.22 * H), (tx + 0.04 * W, g)], fill=hex_rgba('#0B0F0C'))
    # fire
    fx = 0.6 * W
    for i in range(5):
        a = i * math.pi / 5
        pen.line([(fx - 50 * math.cos(a), g - 6), (fx + 50 * math.cos(a), g - 26)], hex_rgba('#3A2A1E'), 12)
    if o.get('fire', True):
        pen.poly([(fx - 34, g - 16), (fx, g - 120), (fx + 34, g - 16)], fill=hex_rgba('#F28C28'))
        pen.poly([(fx - 18, g - 16), (fx + 4, g - 80), (fx + 20, g - 16)], fill=hex_rgba('#FFD45A'))
    for i in range(8):
        a = i * math.pi * 2 / 8
        pen.ellipse(fx + 90 * math.cos(a), g - 6 + 18 * math.sin(a), 18, 10, fill=hex_rgba('#4A4F55'))
    # log seat
    pen.rect(0.72 * W, g - 34, 0.9 * W, g - 4, fill=hex_rgba('#4A3626'), r=14)
    lights = []
    if o.get('fire', True):
        lights.append(L('point', 0.6, GROUND_Y - 0.07, r=0.5, col='#FF9A3C', power=1.2, flicker=True, flame=True))
    lights.append(L('point', 0.8, 0.16, r=0.8, col='#9FB2D8', power=0.35))
    return Layered(pen.done().convert('RGB'), lights=lights, ambient=_amb(o, 0.26))


def bg_suburban_street(W, H, S, o):
    pen = _exterior_sky(W, H, S, o)
    g = GROUND_Y * H
    tree_line(pen, W, H, 0.6, 0.1, 0.2, hex_rgba('#080B11'), seed=41)
    for i, (x, lit) in enumerate(((0.05, True), (0.38, False), (0.7, True))):
        hx = x * W
        hw = 0.26 * W
        top = 0.33 * H
        pen.rect(hx, top + 0.12 * H, hx + hw, g - 0.06 * H, fill=hex_rgba(['#3E4757', '#46404A', '#3B4A4A'][i]))
        pen.poly([(hx - 20, top + 0.13 * H), (hx + hw / 2, top), (hx + hw + 20, top + 0.13 * H)], fill=hex_rgba('#22262E'))
        window(pen, hx + 0.03 * W, top + 0.18 * H, hx + 0.09 * W, top + 0.27 * H, lit=lit and i != 1)
        window(pen, hx + 0.17 * W, top + 0.18 * H, hx + 0.23 * W, top + 0.27 * H, lit=False)
        door(pen, hx + 0.11 * W, top + 0.24 * H, hx + 0.15 * W, g - 0.06 * H, col='#2B2F3A')
    pen.rect(0, g - 0.07 * H, W, g, fill=hex_rgba('#2D3A2E'))
    pen.rect(0, g, W, H, fill=hex_rgba('#3A3E45'))
    pen.rect(0, g, W, g + 8, fill=hex_rgba('#5A5E66'))
    lx = 0.6 * W
    pen.rect(lx - 6, 0.2 * H, lx + 6, g, fill=hex_rgba('#2B3038'))
    pen.ellipse(lx, 0.2 * H, 26, 12, fill=hex_rgba('#FFE7A8'))
    lights = [L('cone', 0.6, 0.2, r=0.75, spread=0.22, col='#FFD58A', power=1.0, flicker=o.get('lights') == 'flicker'),
              L('rect', 0.11, 0.555, r=0.12, w=0.06, h=0.09, col='#E8C77A', power=0.6),
              L('rect', 0.76, 0.555, r=0.12, w=0.06, h=0.09, col='#E8C77A', power=0.6)]
    return Layered(pen.done().convert('RGB'), lights=lights, ambient=_amb(o, 0.36))


def bg_house_exterior(W, H, S, o):
    pen = _exterior_sky(W, H, S, o)
    g = GROUND_Y * H
    tree_line(pen, W, H, 0.6, 0.12, 0.25, hex_rgba('#070A0F'), seed=51)
    bare_tree(pen, 0.88 * W, g, 0.75 * H, hex_rgba('#06080B'), seed=9)
    hx0, hx1 = 0.2 * W, 0.75 * W
    pen.rect(hx0, 0.32 * H, hx1, g, fill=hex_rgba('#4A4F5A'))
    for i in range(14):
        y = 0.34 * H + i * 0.038 * H
        pen.line([(hx0, y), (hx1, y)], hex_rgba('#3D424C'), 3)
    pen.poly([(hx0 - 40, 0.33 * H), ((hx0 + hx1) / 2, 0.1 * H), (hx1 + 40, 0.33 * H)], fill=hex_rgba('#23262D'))
    window(pen, 0.42 * W, 0.17 * H, 0.53 * W, 0.28 * H, lit=o.get('attic_light', False))
    window(pen, 0.25 * W, 0.42 * H, 0.36 * W, 0.6 * H, lit=o.get('lights', 'on') != 'off', curtain='#5A2A2A')
    window(pen, 0.6 * W, 0.42 * H, 0.71 * W, 0.6 * H, lit=False, blinds=True)
    door(pen, 0.43 * W, 0.5 * H, 0.52 * W, g - 0.04 * H, col='#5A2E2A', ajar=o.get('ajar', 0.0))
    pen.rect(0.38 * W, g - 0.04 * H, 0.57 * W, g, fill=hex_rgba('#3A3530'))
    pen.ellipse(0.475 * W, 0.47 * H, 14, 10, fill=hex_rgba('#FFE2A0'))
    pen.rect(0, g, W, H, fill=hex_rgba('#1F2A20'))
    pen.poly([(0.43 * W, g), (0.52 * W, g), (0.6 * W, H), (0.35 * W, H)], fill=hex_rgba('#3E3B37'))
    lights = [L('point', 0.475, 0.47, r=0.32, col='#FFD58A', power=1.0, flicker=o.get('lights') == 'flicker')]
    if o.get('lights', 'on') != 'off':
        lights.append(L('rect', 0.305, 0.51, r=0.16, w=0.11, h=0.18, col='#E8C77A', power=0.7))
    return Layered(pen.done().convert('RGB'), lights=lights, ambient=_amb(o, 0.34))


def bg_front_door(W, H, S, o):
    """Porch seen from outside, door close."""
    pen = new_pen(W, H, S, '#30343C', '#3A3E45')
    g = GROUND_Y * H
    for i in range(22):
        y = i * 0.045 * H
        pen.line([(0, y), (W, y)], hex_rgba('#272B32'), 4)
    door(pen, 0.38 * W, 0.12 * H, 0.62 * W, g, col='#5A2E2A', frame='#22252B', ajar=o.get('ajar', 0.0))
    pen.rect(0.4 * W, 0.18 * H, 0.6 * W, 0.24 * H, fill=hex_rgba('#141A24'), r=4)
    # peephole + number
    pen.circle(0.5 * W, 0.4 * H, 9, fill=hex_rgba('#C8B48A'))
    pen.rect(0.66 * W, 0.42 * H, 0.7 * W, 0.47 * H, fill=hex_rgba('#C8B48A'), r=4)
    # doorbell camera
    pen.rect(0.65 * W, 0.52 * H, 0.675 * W, 0.6 * H, fill=hex_rgba('#15181D'), r=10)
    pen.circle(0.6625 * W, 0.545 * H, 8, fill=hex_rgba('#3FA7C9'))
    pen.circle(0.6625 * W, 0.58 * H, 10, fill=hex_rgba('#D9DDE0'))
    # porch lamp
    pen.rect(0.28 * W, 0.28 * H, 0.32 * W, 0.38 * H, fill=hex_rgba('#20242A'), r=6)
    pen.rect(0.285 * W, 0.3 * H, 0.315 * W, 0.36 * H, fill=hex_rgba('#FFE2A0' if o.get('lights', 'on') != 'off' else '#4A4A44'), r=4)
    pen.rect(0, g, W, H, fill=hex_rgba('#3A3530'))
    pen.rect(0.3 * W, g, 0.7 * W, g + 0.05 * H, fill=hex_rgba('#4A3B30'), r=6)
    lights = []
    if o.get('lights', 'on') != 'off':
        lights.append(L('point', 0.3, 0.33, r=0.55, col='#FFD58A', power=1.0, flicker=o.get('lights') == 'flicker'))
    lights.append(L('point', 0.6625, 0.545, r=0.05, col='#3FA7C9', power=0.6))
    return Layered(pen.done().convert('RGB'), lights=lights, ambient=0.3)


def _room(W, H, S, wall='#4A5263', pattern='stripes', floor='#4A3B30', ceiling=True):
    pen = new_pen(W, H, S, '#20242C', '#20242C')
    g = GROUND_Y * H
    wallpaper(pen, 0, 0, W, g, wall, pattern)
    pen.rect(0, g - 0.025 * H, W, g, fill=hex_rgba('#2A2E35'))
    floorboards(pen, W, H, g, floor)
    if ceiling:
        pen.rect(0, 0, W, 0.04 * H, fill=hex_rgba('#2A2E35'))
    return pen, g


def bg_living_room(W, H, S, o):
    pen, g = _room(W, H, S, '#4C5566', 'damask', '#4A3B30')
    window(pen, 0.08 * W, 0.18 * H, 0.26 * W, 0.55 * H, lit=False, curtain='#5A3030')
    # tv
    pen.rect(0.64 * W, 0.36 * H, 0.86 * W, 0.6 * H, fill=hex_rgba('#0B0D10'), r=6)
    tv_on = o.get('tv', False)
    pen.rect(0.65 * W, 0.375 * H, 0.85 * W, 0.585 * H, fill=hex_rgba('#7A8A9A' if tv_on else '#121519'), r=4)
    pen.rect(0.66 * W, g - 0.24 * H, 0.84 * W, g, fill=hex_rgba('#3A2E25'))
    # couch
    pen.rect(0.3 * W, g - 0.28 * H, 0.58 * W, g - 0.08 * H, fill=hex_rgba('#5A4A6A'), r=26)
    pen.rect(0.28 * W, g - 0.16 * H, 0.6 * W, g - 0.02 * H, fill=hex_rgba('#4E405C'), r=20)
    lamp_shade(pen, 0.9 * W, g - 0.42 * H, 0.08 * W, on=o.get('lights', 'on') != 'off')
    pen.rect(0.9 * W - 5, g - 0.37 * H, 0.9 * W + 5, g, fill=hex_rgba('#2A2420'))
    frame_pic(pen, 0.45 * W, 0.24 * H, 0.1 * W, 0.15 * H, tilt=o.get('tilt', 4))
    lights = []
    if o.get('lights', 'on') != 'off':
        lights.append(L('point', 0.9, GROUND_Y - 0.36, r=0.45, col='#FFC97A', power=1.0, flicker=o.get('lights') == 'flicker'))
    if tv_on:
        lights.append(L('rect', 0.75, 0.48, r=0.5, w=0.2, h=0.21, col='#9FC3E8', power=0.9, flicker=True))
    lights.append(L('rect', 0.17, 0.36, r=0.25, w=0.18, h=0.37, col='#8FA5CC', power=0.35))
    return Layered(pen.done().convert('RGB'), lights=lights, ambient=0.3 if o.get('lights', 'on') != 'off' else 0.18)


def bg_kitchen(W, H, S, o):
    pen, g = _room(W, H, S, '#56606A', 'tiles', '#3D4148')
    pen.rect(0, g - 0.3 * H, 0.7 * W, g, fill=hex_rgba('#3E4A57'))
    pen.rect(0, g - 0.32 * H, 0.72 * W, g - 0.29 * H, fill=hex_rgba('#C9C4B8'))
    for i in range(5):
        x = 0.02 * W + i * 0.14 * W
        pen.rect(x, g - 0.27 * H, x + 0.12 * W, g - 0.02 * H, outline=hex_rgba('#2E3843'), width=4, r=4)
        pen.rect(x + 0.05 * W, g - 0.2 * H, x + 0.07 * W, g - 0.19 * H, fill=hex_rgba('#A8A090'))
        pen.rect(x, 0.08 * H, x + 0.12 * W, 0.3 * H, fill=hex_rgba('#3E4A57'), outline=hex_rgba('#2E3843'), width=4)
    window(pen, 0.26 * W, 0.34 * H, 0.42 * W, 0.5 * H, lit=False)
    # fridge
    pen.rect(0.76 * W, 0.2 * H, 0.94 * W, g, fill=hex_rgba('#C9CDD2'), r=12)
    pen.line([(0.76 * W, 0.45 * H), (0.94 * W, 0.45 * H)], hex_rgba('#9AA0A8'), 5)
    pen.rect(0.78 * W, 0.3 * H, 0.79 * W, 0.4 * H, fill=hex_rgba('#7A8088'))
    pen.rect(0.78 * W, 0.5 * H, 0.79 * W, 0.62 * H, fill=hex_rgba('#7A8088'))
    ceiling_light(pen, 0.4 * W, 0.06 * H, 0.08 * W, on=o.get('lights', 'on') != 'off')
    lights = []
    if o.get('fridge_open'):
        lights.append(L('rect', 0.85, 0.5, r=0.35, w=0.15, h=0.5, col='#E6F0FF', power=1.0))
    if o.get('lights', 'on') != 'off':
        lights.append(L('cone', 0.4, 0.07, r=0.9, spread=0.35, col='#F5E6C8', power=0.9, flicker=o.get('lights') == 'flicker'))
    lights.append(L('rect', 0.34, 0.42, r=0.15, w=0.16, h=0.16, col='#8FA5CC', power=0.3))
    return Layered(pen.done().convert('RGB'), lights=lights, ambient=0.34 if o.get('lights', 'on') != 'off' else 0.16)


def bg_hallway(W, H, S, o):
    pen = new_pen(W, H, S, '#3A4150', '#2A2F38')
    g = GROUND_Y * H
    vx, vy = 0.5 * W, 0.45 * H
    # perspective corridor
    pen.poly([(0, 0), (W, 0), (0.62 * W, 0.3 * H), (0.38 * W, 0.3 * H)], fill=hex_rgba('#2A2F38'))
    pen.poly([(0, 0), (0.38 * W, 0.3 * H), (0.38 * W, 0.62 * H), (0, H)], fill=hex_rgba('#4A5263'))
    pen.poly([(W, 0), (0.62 * W, 0.3 * H), (0.62 * W, 0.62 * H), (W, H)], fill=hex_rgba('#444B5B'))
    pen.poly([(0, H), (0.38 * W, 0.62 * H), (0.62 * W, 0.62 * H), (W, H)], fill=hex_rgba('#4A3B30'))
    pen.rect(0.38 * W, 0.3 * H, 0.62 * W, 0.62 * H, fill=hex_rgba('#1A1D23'))
    door(pen, 0.45 * W, 0.38 * H, 0.55 * W, 0.62 * H, col='#3A2E25', ajar=o.get('ajar', 0.0))
    # side doors in perspective
    pen.poly([(0.1 * W, 0.18 * H), (0.24 * W, 0.24 * H), (0.24 * W, 0.72 * H), (0.1 * W, 0.84 * H)], fill=hex_rgba('#3A2E25'))
    pen.poly([(0.9 * W, 0.18 * H), (0.76 * W, 0.24 * H), (0.76 * W, 0.72 * H), (0.9 * W, 0.84 * H)], fill=hex_rgba('#3A2E25'))
    frame_pic(pen, 0.3 * W, 0.34 * H, 0.05 * W, 0.08 * H, tilt=-6)
    frame_pic(pen, 0.7 * W, 0.34 * H, 0.05 * W, 0.08 * H, tilt=o.get('tilt', 3))
    # runner rug
    pen.poly([(0.44 * W, 0.62 * H), (0.56 * W, 0.62 * H), (0.7 * W, H), (0.3 * W, H)], fill=hex_rgba('#5A2A2A'))
    ceiling_light(pen, 0.5 * W, 0.1 * H, 0.07 * W, on=o.get('lights', 'on') != 'off')
    lights = []
    if o.get('lights', 'on') != 'off':
        lights.append(L('cone', 0.5, 0.11, r=0.9, spread=0.3, col='#F2DDB0', power=0.9, flicker=o.get('lights') == 'flicker'))
    if o.get('ajar'):
        lights.append(L('rect', 0.54, 0.5, r=0.12, w=0.02, h=0.22, col=o.get('door_light', '#C8102E'), power=0.9))
    return Layered(pen.done().convert('RGB'), lights=lights, ambient=0.3 if lights else 0.14)


def bg_bedroom(W, H, S, o):
    pen, g = _room(W, H, S, '#3E4A63', 'stripes', '#4A3B30')
    window(pen, 0.62 * W, 0.16 * H, 0.82 * W, 0.5 * H, lit=False, curtain='#2E3A55', blinds=False)
    # closet
    closet_ajar = o.get('closet_ajar', 0.0)
    door(pen, 0.06 * W, 0.18 * H, 0.22 * W, g, col='#3A2E25', ajar=closet_ajar, panels=True)
    # nightstand + lamp
    pen.rect(0.86 * W, g - 0.16 * H, 0.97 * W, g, fill=hex_rgba('#3A2E25'), r=6)
    lamp_shade(pen, 0.915 * W, g - 0.26 * H, 0.06 * W, on=o.get('lights', 'off') == 'on')
    pen.rect(0.912 * W, g - 0.2 * H, 0.918 * W, g - 0.16 * H, fill=hex_rgba('#2A2420'))
    # alarm clock
    pen.rect(0.87 * W, g - 0.2 * H, 0.9 * W, g - 0.16 * H, fill=hex_rgba('#121417'), r=4)
    frame_pic(pen, 0.4 * W, 0.26 * H, 0.08 * W, 0.12 * H, tilt=o.get('tilt', 0))
    lights = [L('rect', 0.72, 0.33, r=0.38, w=0.2, h=0.34, col='#8FA5CC', power=0.55),
              L('point', 0.885, GROUND_Y - 0.18, r=0.04, col='#E04030', power=0.8)]
    if o.get('lights', 'off') == 'on':
        lights.append(L('point', 0.915, GROUND_Y - 0.22, r=0.4, col='#FFC97A', power=1.0, flicker=o.get('flicker', False)))
    if closet_ajar:
        lights.append(L('rect', 0.2, 0.5, r=0.05, w=0.02, h=0.6, col='#000000', power=0.0))
    return Layered(pen.done().convert('RGB'), lights=lights, ambient=0.22, tint=(0.88, 0.95, 1.12))


def bg_basement_door(W, H, S, o):
    pen, g = _room(W, H, S, '#4A4F58', 'stripes', '#3A3530')
    ajar = o.get('ajar', 0.15)
    door(pen, 0.4 * W, 0.16 * H, 0.6 * W, g, col='#4A3E33', frame='#2A231D', ajar=ajar)
    # lock / chain
    pen.line([(0.56 * W, 0.42 * H), (0.6 * W, 0.45 * H)], hex_rgba('#A8A090'), 4)
    pen.rect(0.18 * W, g - 0.42 * H, 0.3 * W, g - 0.12 * H, fill=hex_rgba('#3A3F47'), r=4)
    for i in range(3):
        pen.rect(0.19 * W, g - 0.4 * H + i * 0.1 * H, 0.29 * W, g - 0.32 * H + i * 0.1 * H, fill=hex_rgba('#2E3238'))
    ceiling_light(pen, 0.5 * W, 0.06 * H, 0.06 * W, on=o.get('lights', 'on') != 'off', cord=True)
    lights = []
    if o.get('lights', 'on') != 'off':
        lights.append(L('cone', 0.5, 0.07, r=0.9, spread=0.28, col='#F2DDB0', power=0.85, flicker=o.get('lights') == 'flicker'))
    if ajar:
        lights.append(L('rect', 0.6 - 0.2 * ajar / 2, 0.55, r=0.14, w=0.2 * ajar, h=0.62, col=o.get('door_light', '#B0221E'), power=0.8))
    return Layered(pen.done().convert('RGB'), lights=lights, ambient=0.3 if o.get('lights', 'on') != 'off' else 0.14)


def bg_basement(W, H, S, o):
    pen = new_pen(W, H, S, '#2A2D33', '#33363B')
    g = GROUND_Y * H
    for yy in range(0, int(g), 60):
        off = 60 if (yy // 60) % 2 else 0
        for xx in range(-60, int(W) + 60, 120):
            pen.rect(xx + off, yy, xx + off + 116, yy + 56, fill=hex_rgba('#3A3E44'))
    # stairs
    for i in range(7):
        x0 = 0.05 * W + i * 0.04 * W
        y = 0.2 * H + i * 0.095 * H
        pen.rect(x0, y, 0.34 * W, y + 0.03 * H, fill=hex_rgba('#4A3E33'))
    pen.line([(0.05 * W, 0.12 * H), (0.34 * W, 0.85 * H)], hex_rgba('#2A231D'), 10)
    # boxes + furnace
    for (x, w, h) in ((0.6, 0.1, 0.14), (0.7, 0.08, 0.1), (0.62, 0.07, 0.08)):
        pen.rect(x * W, g - h * H, (x + w) * W, g, fill=hex_rgba('#6A5640'), outline=hex_rgba('#4A3B2C'), width=4)
    pen.rect(0.82 * W, 0.3 * H, 0.97 * W, g, fill=hex_rgba('#4A4E55'), r=8)
    pen.rect(0.85 * W, 0.62 * H, 0.94 * W, 0.7 * H, fill=hex_rgba('#E06A2A' if o.get('furnace', True) else '#202226'), r=4)
    pen.rect(0, g, W, H, fill=hex_rgba('#2E3034'))
    ceiling_light(pen, 0.5 * W, 0.08 * H, 0.05 * W, on=o.get('lights', 'off') != 'off', cord=True)
    lights = []
    if o.get('lights', 'off') != 'off':
        lights.append(L('cone', 0.5, 0.09, r=0.85, spread=0.24, col='#F2DDB0', power=0.9, flicker=o.get('lights') == 'flicker'))
    if o.get('furnace', True):
        lights.append(L('rect', 0.895, 0.66, r=0.22, w=0.09, h=0.08, col='#FF7A30', power=0.8, flicker=True, flame=True))
    return Layered(pen.done().convert('RGB'), lights=lights, ambient=0.16)


def bg_attic(W, H, S, o):
    pen = new_pen(W, H, S, '#2A241F', '#352D26')
    g = GROUND_Y * H
    pen.poly([(0, 0.55 * H), (0.5 * W, 0.0), (W, 0.55 * H), (W, 0), (0, 0)], fill=hex_rgba('#15110E'))
    for i in range(9):
        x = i * W / 8
        pen.line([(x, g), (0.5 * W, 0.02 * H)], hex_rgba('#3A2E25'), 14)
    pen.circle(0.5 * W, 0.3 * H, 0.07 * H, fill=hex_rgba('#7A8AA8'))
    pen.line([(0.5 * W - 0.07 * H, 0.3 * H), (0.5 * W + 0.07 * H, 0.3 * H)], hex_rgba('#2A241F'), 6)
    pen.line([(0.5 * W, 0.23 * H), (0.5 * W, 0.37 * H)], hex_rgba('#2A241F'), 6)
    # sheet covered furniture + rocking chair
    pen.poly([(0.12 * W, g), (0.14 * W, g - 0.26 * H), (0.3 * W, g - 0.3 * H), (0.34 * W, g)], fill=hex_rgba('#B8B2A6'))
    pen.poly([(0.66 * W, g), (0.7 * W, g - 0.2 * H), (0.82 * W, g - 0.2 * H), (0.86 * W, g)], fill=hex_rgba('#A8A296'))
    floorboards(pen, W, H, g, '#3A2E25')
    lights = [L('point', 0.5, 0.3, r=0.5, col='#9FB2D8', power=0.7)]
    if o.get('flashlight'):
        lights.append(L('cone_side', 0.5, 0.6, r=0.6, spread=0.18, col='#FFF2CC', power=1.2))
    return Layered(pen.done().convert('RGB'), lights=lights, ambient=0.15)


def bg_bathroom(W, H, S, o):
    pen, g = _room(W, H, S, '#6A7480', 'tiles', '#5A6068')
    # mirror cabinet + sink
    pen.rect(0.36 * W, 0.12 * H, 0.64 * W, 0.48 * H, fill=hex_rgba('#2A2F36'), r=8)
    pen.rect(0.38 * W, 0.14 * H, 0.62 * W, 0.46 * H, fill=hex_rgba('#1A2028'), r=6)
    pen.poly([(0.42 * W, 0.46 * H), (0.47 * W, 0.14 * H), (0.5 * W, 0.14 * H), (0.45 * W, 0.46 * H)], fill=(255, 255, 255, 18))
    pen.rect(0.38 * W, g - 0.34 * H, 0.62 * W, g - 0.28 * H, fill=hex_rgba('#D8DCDF'), r=14)
    pen.rect(0.46 * W, g - 0.28 * H, 0.54 * W, g, fill=hex_rgba('#C8CCD0'))
    # shower curtain
    pen.line([(0.72 * W, 0.08 * H), (W, 0.08 * H)], hex_rgba('#9AA0A8'), 8)
    for i in range(10):
        x = 0.72 * W + i * 0.03 * W
        pen.rect(x, 0.08 * H, x + 0.028 * W, g - 0.05 * H, fill=hex_rgba('#7A8A6A' if i % 2 else '#6A7A5A'))
    pen.rect(0.4 * W, 0.08 * H, 0.6 * W, 0.11 * H, fill=hex_rgba('#E8E4D8'), r=6)
    lights = []
    if o.get('lights', 'on') != 'off':
        lights.append(L('rect', 0.5, 0.095, r=0.7, w=0.2, h=0.03, col='#F5ECD8', power=0.9, flicker=o.get('lights') == 'flicker'))
    return Layered(pen.done().convert('RGB'), lights=lights, ambient=0.32 if lights else 0.12)


def bg_office_night(W, H, S, o):
    pen, g = _room(W, H, S, '#4A5262', 'stripes', '#3A3F48')
    window(pen, 0.05 * W, 0.12 * H, 0.95 * W, 0.45 * H, lit=False, frame='#30353D', glass='#0A0F19')
    rnd = random.Random(9)
    for _ in range(40):
        x = 0.06 * W + rnd.random() * 0.88 * W
        y = 0.25 * H + rnd.random() * 0.18 * H
        pen.rect(x, y, x + 10, y + 14, fill=hex_rgba('#C9A35A'))
    for i in range(3):
        x0 = 0.08 * W + i * 0.3 * W
        pen.rect(x0, g - 0.24 * H, x0 + 0.24 * W, g - 0.21 * H, fill=hex_rgba('#5A4A3A'))
        pen.rect(x0 + 0.06 * W, g - 0.38 * H, x0 + 0.17 * W, g - 0.25 * H, fill=hex_rgba('#14171C'), r=6)
        on = i == 1
        pen.rect(x0 + 0.065 * W, g - 0.37 * H, x0 + 0.165 * W, g - 0.26 * H, fill=hex_rgba('#6FA8D8' if on else '#1C2028'), r=4)
        pen.rect(x0 + 0.02 * W, g - 0.21 * H, x0 + 0.03 * W, g, fill=hex_rgba('#2A2420'))
        pen.rect(x0 + 0.21 * W, g - 0.21 * H, x0 + 0.22 * W, g, fill=hex_rgba('#2A2420'))
    lights = [L('rect', 0.415, 0.6, r=0.35, w=0.1, h=0.11, col='#8FC0F0', power=0.9)]
    if o.get('lights', 'off') != 'off':
        lights.append(L('cone', 0.5, 0.05, r=0.95, spread=0.5, col='#E8F0E8', power=0.7, flicker=o.get('lights') == 'flicker'))
    return Layered(pen.done().convert('RGB'), lights=lights, ambient=0.2)


def bg_parking_garage(W, H, S, o):
    pen = new_pen(W, H, S, '#3A3E44', '#2E3136')
    g = GROUND_Y * H
    pen.rect(0, 0, W, 0.12 * H, fill=hex_rgba('#2A2D32'))
    for x in (0.12, 0.42, 0.72):
        pen.rect(x * W, 0.12 * H, x * W + 0.07 * W, g, fill=hex_rgba('#4A4E55'))
        pen.rect(x * W, 0.5 * H, x * W + 0.07 * W, 0.56 * H, fill=hex_rgba('#C9A13B'))
        pen.rect(x * W + 0.01 * W, 0.3 * H, x * W + 0.06 * W, 0.38 * H, fill=hex_rgba('#2A2D32'))
    # cars
    for (x, col) in ((0.22, '#4A5A70'), (0.52, '#6A2A2A'), (0.84, '#3A3E44')):
        pen.rect(x * W, g - 0.16 * H, x * W + 0.16 * W, g - 0.04 * H, fill=hex_rgba(col), r=24)
        pen.rect(x * W + 0.03 * W, g - 0.24 * H, x * W + 0.13 * W, g - 0.15 * H, fill=hex_rgba(col), r=20)
        pen.rect(x * W + 0.04 * W, g - 0.23 * H, x * W + 0.12 * W, g - 0.16 * H, fill=hex_rgba('#0A0D12'), r=14)
        for wx in (0.03, 0.13):
            pen.circle(x * W + wx * W, g - 0.04 * H, 0.035 * H, fill=hex_rgba('#121417'))
    pen.rect(0, g, W, H, fill=hex_rgba('#3A3D42'))
    for i in range(6):
        pen.line([(i * 0.2 * W, g), (i * 0.2 * W - 80, H)], hex_rgba('#C9C3A0'), 5)
    flick = o.get('lights') == 'flicker'
    lights = [L('cone', 0.25 + i * 0.3, 0.12, r=0.85, spread=0.18, col='#E8F0D8', power=0.85, flicker=flick and i == 1) for i in range(3)]
    if o.get('lights') == 'off':
        lights = []
    return Layered(pen.done().convert('RGB'), lights=lights, ambient=0.24 if lights else 0.1)


def bg_motel_room(W, H, S, o):
    pen, g = _room(W, H, S, '#6A5A48', 'damask', '#4A3B35')
    pen.rect(0.1 * W, g - 0.2 * H, 0.55 * W, g - 0.06 * H, fill=hex_rgba('#8A3A3A'), r=10)
    pen.rect(0.08 * W, g - 0.42 * H, 0.12 * W, g, fill=hex_rgba('#3A2E25'))
    pen.rect(0.1 * W, g - 0.24 * H, 0.55 * W, g - 0.18 * H, fill=hex_rgba('#D8D0C0'), r=10)
    window(pen, 0.62 * W, 0.18 * H, 0.86 * W, 0.5 * H, lit=False, curtain='#6A5A30', blinds=True)
    pen.rect(0.88 * W, 0.2 * H, 0.98 * W, g, fill=hex_rgba('#3A2E25'))
    pen.circle(0.9 * W, 0.55 * H, 8, fill=hex_rgba('#C8B48A'))
    lamp_shade(pen, 0.6 * W, g - 0.36 * H, 0.06 * W, on=o.get('lights', 'on') != 'off')
    pen.rect(0.56 * W, g - 0.14 * H, 0.64 * W, g, fill=hex_rgba('#3A2E25'))
    frame_pic(pen, 0.32 * W, 0.26 * H, 0.14 * W, 0.12 * H, tilt=o.get('tilt', 0))
    lights = [L('rect', 0.74, 0.34, r=0.3, w=0.24, h=0.32, col='#D84A4A', power=0.4, flicker=True)]
    if o.get('lights', 'on') != 'off':
        lights.append(L('point', 0.6, GROUND_Y - 0.31, r=0.45, col='#FFC97A', power=0.9, flicker=o.get('lights') == 'flicker'))
    return Layered(pen.done().convert('RGB'), lights=lights, ambient=0.26)


def bg_elevator(W, H, S, o):
    pen = new_pen(W, H, S, '#5A5E64', '#4A4E54')
    g = GROUND_Y * H
    for i in range(6):
        x = i * W / 5
        pen.line([(x, 0), (x, g)], hex_rgba('#6A6E74'), 6)
    pen.rect(0.82 * W, 0.3 * H, 0.9 * W, 0.6 * H, fill=hex_rgba('#3A3E44'), r=8)
    for i in range(6):
        pen.circle(0.86 * W, 0.34 * H + i * 0.045 * H, 12, fill=hex_rgba('#C9C3A0' if i != 2 else '#FF6A3A'))
    pen.rect(0.4 * W, 0.06 * H, 0.6 * W, 0.12 * H, fill=hex_rgba('#14171C'), r=6)
    pen.text((0.5 * W, 0.09 * H), o.get('floor_text', '13'), _font_digits(int(0.05 * H)), fill=hex_rgba('#FF4A2A'))
    pen.rect(0, g, W, H, fill=hex_rgba('#3A3530'))
    lights = [L('cone', 0.5, 0.02, r=0.95, spread=0.6, col='#F2F0E6', power=0.85, flicker=o.get('lights') == 'flicker')]
    return Layered(pen.done().convert('RGB'), lights=lights, ambient=0.3)


def bg_school_hallway(W, H, S, o):
    pen, g = _room(W, H, S, '#5A6A74', 'stripes', '#6A6E70')
    for i in range(12):
        x = 0.02 * W + i * 0.082 * W
        pen.rect(x, 0.22 * H, x + 0.075 * W, g - 0.02 * H, fill=hex_rgba('#3A5A7A'), r=4)
        for k in range(3):
            pen.line([(x + 0.015 * W, 0.26 * H + k * 14), (x + 0.06 * W, 0.26 * H + k * 14)], hex_rgba('#2A4460'), 3)
        pen.rect(x + 0.055 * W, 0.5 * H, x + 0.065 * W, 0.53 * H, fill=hex_rgba('#C9C3A0'))
    flick = o.get('lights') == 'flicker'
    lights = [L('cone', 0.15 + i * 0.35, 0.03, r=0.8, spread=0.25, col='#E8F0E0', power=0.8, flicker=flick and i == 1) for i in range(3)]
    if o.get('lights') == 'off':
        lights = []
    return Layered(pen.done().convert('RGB'), lights=lights, ambient=0.34 if lights else 0.12)


def bg_cornfield(W, H, S, o):
    pen = _exterior_sky(W, H, S, o, horizon=0.5)
    g = GROUND_Y * H
    haze(pen, W, H, 0.5, 0.25)
    rnd = random.Random(61)
    for row in range(4):
        base = (0.55 + row * 0.12) * H
        col = shade(hex_rgba('#3A3A22'), 0.6 + row * 0.12)
        for i in range(int(60 + row * 20)):
            x = rnd.random() * W
            h = (0.12 + row * 0.06) * H * rnd.uniform(0.8, 1.2)
            pen.line([(x, base), (x + rnd.uniform(-8, 8), base - h)], col, 4 + row * 2)
            pen.poly([(x, base - h * 0.6), (x + 40 + row * 10, base - h * 0.5), (x + 4, base - h * 0.55)], fill=col)
    # scarecrow cross far away
    pen.line([(0.72 * W, 0.58 * H), (0.72 * W, 0.4 * H)], hex_rgba('#14120E'), 8)
    pen.line([(0.69 * W, 0.45 * H), (0.75 * W, 0.45 * H)], hex_rgba('#14120E'), 8)
    pen.circle(0.72 * W, 0.385 * H, 18, fill=hex_rgba('#14120E'))
    return Layered(pen.done().convert('RGB'), lights=[L('point', 0.8, 0.16, r=0.9, col='#9FB2D8', power=0.5)],
                   ambient=_amb(o, 0.3))


def bg_cemetery(W, H, S, o):
    pen = _exterior_sky(W, H, S, o)
    g = GROUND_Y * H
    tree_line(pen, W, H, 0.6, 0.1, 0.22, hex_rgba('#06080C'), seed=71)
    bare_tree(pen, 0.15 * W, g - 0.05 * H, 0.75 * H, hex_rgba('#06080B'), seed=3)
    pen.rect(0, 0.6 * H, W, H, fill=hex_rgba('#1A201C'))
    rnd = random.Random(72)
    for row in range(3):
        for i in range(7):
            x = (0.08 + i * 0.14 + row * 0.05) * W
            y = (0.64 + row * 0.1) * H
            w = (0.035 + row * 0.012) * W
            h = (0.06 + row * 0.03) * H
            pen.rect(x - w / 2, y - h, x + w / 2, y, fill=hex_rgba('#5A5E66'), r=w * 0.5 if rnd.random() < 0.6 else 4)
    # iron fence
    for i in range(40):
        x = i * W / 39
        pen.line([(x, g), (x, g - 0.14 * H)], hex_rgba('#0A0C10'), 6)
        pen.poly([(x - 8, g - 0.14 * H), (x + 8, g - 0.14 * H), (x, g - 0.16 * H)], fill=hex_rgba('#0A0C10'))
    pen.line([(0, g - 0.12 * H), (W, g - 0.12 * H)], hex_rgba('#0A0C10'), 6)
    pen.rect(0, g, W, H, fill=hex_rgba('#151A16'))
    return Layered(pen.done().convert('RGB'), lights=[L('point', 0.8, 0.16, r=0.9, col='#9FB2D8', power=0.6)],
                   ambient=_amb(o, 0.3), tint=(0.85, 0.95, 1.1))


def bg_window_view(W, H, S, o):
    """Inside a dark room looking at a big window to the night yard."""
    pen = new_pen(W, H, S, '#14171D', '#1A1E24')
    g = GROUND_Y * H
    x0, y0, x1, y1 = 0.22 * W, 0.1 * H, 0.78 * W, 0.78 * H
    pen.rect(x0 - 20, y0 - 20, x1 + 20, y1 + 20, fill=hex_rgba('#2A2F38'))
    sky = gradient(int((x1 - x0) * S), int((y1 - y0) * S), '#05070C', '#1A2436').convert('RGBA')
    pen.img.alpha_composite(sky, (int(x0 * S), int(y0 * S)))
    pen.d = ImageDraw.Draw(pen.img)
    sub = _pen(x1 - x0, y1 - y0, S)
    tree_line(sub, x1 - x0, y1 - y0, 0.85, 0.2, 0.45, hex_rgba('#06080C'), seed=81, step=0.06)
    sub.rect(0, (y1 - y0) * 0.84, x1 - x0, y1 - y0, fill=hex_rgba('#0C110D'))
    pen.img.alpha_composite(sub.img, (int(x0 * S), int(y0 * S)))
    pen.d = ImageDraw.Draw(pen.img)
    pen.line([((x0 + x1) / 2, y0), ((x0 + x1) / 2, y1)], hex_rgba('#2A2F38'), 14)
    pen.line([(x0, (y0 + y1) / 2), (x1, (y0 + y1) / 2)], hex_rgba('#2A2F38'), 14)
    pen.rect(x0 - 40, y1 + 10, x1 + 40, y1 + 40, fill=hex_rgba('#30353E'))
    pen.poly([(x0 - 60, y0 - 30), (x0 + 60, y0 - 30), (x0 + 20, g), (x0 - 60, g)], fill=hex_rgba('#2E2A3A'))
    pen.poly([(x1 + 60, y0 - 30), (x1 - 60, y0 - 30), (x1 - 20, g), (x1 + 60, g)], fill=hex_rgba('#2E2A3A'))
    pen.rect(0, g, W, H, fill=hex_rgba('#2A2420'))
    return Layered(pen.done().convert('RGB'), lights=[L('rect', 0.5, 0.44, r=0.4, w=0.56, h=0.68, col='#8FA5CC', power=0.5)],
                   ambient=0.16)


def bg_cabin(W, H, S, o):
    pen, g = _room(W, H, S, '#5A4636', 'stripes', '#4A3626')
    for i in range(14):
        y = i * 0.065 * H
        pen.line([(0, y), (W, y)], hex_rgba('#3E3024'), 6)
    window(pen, 0.62 * W, 0.18 * H, 0.82 * W, 0.46 * H, lit=False, frame='#2E241B')
    # fireplace
    pen.rect(0.1 * W, 0.3 * H, 0.38 * W, g, fill=hex_rgba('#5A5E66'))
    pen.rect(0.15 * W, 0.5 * H, 0.33 * W, g, fill=hex_rgba('#0E0B09'))
    fire = o.get('fire', True)
    if fire:
        pen.poly([(0.2 * W, g), (0.24 * W, g - 0.18 * H), (0.28 * W, g)], fill=hex_rgba('#F28C28'))
        pen.poly([(0.22 * W, g), (0.245 * W, g - 0.1 * H), (0.27 * W, g)], fill=hex_rgba('#FFD45A'))
    pen.rect(0.08 * W, 0.28 * H, 0.4 * W, 0.31 * H, fill=hex_rgba('#3A2E25'))
    # mounted antlers
    pen.line([(0.5 * W, 0.2 * H), (0.47 * W, 0.12 * H)], hex_rgba('#C8B898'), 6)
    pen.line([(0.5 * W, 0.2 * H), (0.53 * W, 0.12 * H)], hex_rgba('#C8B898'), 6)
    pen.rect(0.85 * W, g - 0.2 * H, 0.97 * W, g, fill=hex_rgba('#3A2E25'))
    lights = []
    if fire:
        lights.append(L('point', 0.24, GROUND_Y - 0.08, r=0.6, col='#FF9A3C', power=1.1, flicker=True, flame=True))
    lights.append(L('rect', 0.72, 0.32, r=0.25, w=0.2, h=0.28, col='#8FA5CC', power=0.35))
    return Layered(pen.done().convert('RGB'), lights=lights, ambient=0.2)


def bg_staircase(W, H, S, o):
    pen, g = _room(W, H, S, '#4A5263', 'damask', '#4A3B30')
    for i in range(10):
        x0 = 0.25 * W + i * 0.06 * W
        y = g - (i + 1) * 0.07 * H
        pen.rect(x0, y, 0.95 * W, y + 0.07 * H, fill=hex_rgba('#4A3B30'), outline=hex_rgba('#3A2E25'), width=3)
    for i in range(11):
        x = 0.25 * W + i * 0.06 * W
        pen.line([(x + 10, g - i * 0.07 * H), (x + 10, g - i * 0.07 * H - 0.16 * H)], hex_rgba('#2E241B'), 7)
    pen.line([(0.25 * W, g - 0.16 * H), (0.91 * W, g - 0.86 * H)], hex_rgba('#2E241B'), 12)
    pen.rect(0.6 * W, 0.0, 0.98 * W, 0.18 * H, fill=hex_rgba('#0A0B0E'))
    frame_pic(pen, 0.12 * W, 0.3 * H, 0.08 * W, 0.12 * H, tilt=o.get('tilt', -5))
    lights = []
    if o.get('lights', 'on') != 'off':
        lights.append(L('point', 0.1, 0.12, r=0.6, col='#FFC97A', power=0.8, flicker=o.get('lights') == 'flicker'))
    return Layered(pen.done().convert('RGB'), lights=lights, ambient=0.22)


_DIGIT_FONT = {}


def _font_digits(size):
    from . import textfx
    return textfx.font('bold', size)


BGS = {
    'plain_dark': bg_plain_dark, 'bus_stop': bg_bus_stop, 'bus_interior': bg_bus_interior, 'bus_front': bg_bus_front,
    'road_night': bg_road_night, 'car_interior': bg_car_interior, 'gas_station': bg_gas_station,
    'store_night': bg_store_night, 'store_counter': bg_store_counter, 'forest': bg_forest, 'campsite': bg_campsite, 'suburban_street': bg_suburban_street,
    'house_exterior': bg_house_exterior, 'front_door': bg_front_door, 'living_room': bg_living_room,
    'kitchen': bg_kitchen, 'hallway': bg_hallway, 'bedroom': bg_bedroom, 'basement_door': bg_basement_door,
    'basement': bg_basement, 'attic': bg_attic, 'bathroom': bg_bathroom, 'office_night': bg_office_night,
    'parking_garage': bg_parking_garage, 'motel_room': bg_motel_room, 'elevator': bg_elevator,
    'school_hallway': bg_school_hallway, 'cornfield': bg_cornfield, 'cemetery': bg_cemetery,
    'window_view': bg_window_view, 'cabin': bg_cabin, 'staircase': bg_staircase,
}
BG_ALIASES = {
    'black': 'plain_dark', 'void': 'plain_dark', 'dark': 'plain_dark', 'plain': 'plain_dark',
    'bus': 'bus_interior', 'bus_inside': 'bus_interior', 'driver': 'bus_front', 'bus_mirror': 'bus_front',
    'road': 'road_night', 'highway': 'road_night', 'car': 'car_interior', 'gas': 'gas_station',
    'convenience_store': 'store_night', 'counter': 'store_counter', 'register': 'store_counter', 'checkout': 'store_counter', 'store_window': 'store_counter', 'store': 'store_night', 'supermarket': 'store_night', 'woods': 'forest',
    'forest_path': 'forest', 'trail': 'forest', 'camping': 'campsite', 'tent': 'campsite', 'street': 'suburban_street',
    'neighborhood': 'suburban_street', 'house': 'house_exterior', 'porch': 'front_door', 'door': 'front_door',
    'living': 'living_room', 'lounge': 'living_room', 'corridor': 'hallway', 'bed': 'bedroom', 'room': 'bedroom',
    'basement_stairs': 'basement_door', 'cellar': 'basement', 'office': 'office_night', 'garage': 'parking_garage',
    'parking': 'parking_garage', 'motel': 'motel_room', 'hotel_room': 'motel_room', 'airbnb': 'motel_room',
    'school': 'school_hallway', 'farm': 'cornfield', 'field': 'cornfield', 'graveyard': 'cemetery',
    'window': 'window_view', 'yard': 'window_view', 'stairs': 'staircase', 'lodge': 'cabin',
}


def resolve(name):
    n = (name or 'plain_dark').strip().lower().replace(' ', '_').replace('-', '_')
    if n in BGS:
        return n, True
    if n in BG_ALIASES:
        return BG_ALIASES[n], True
    return 'plain_dark', False


def render_bg(name, W, H, opts=None, S=2):
    """Backgrounds are designed at DESIGN_W wide; any output size keeps the same proportions."""
    name, _ = resolve(name)
    D = W / DESIGN_W
    _R[0] = int(S)
    lay = BGS[name](W / D, H / D, S * D, dict(opts or {}))
    if lay.img.size != (int(W), int(H)):
        lay.img = lay.img.resize((int(W), int(H)), Image.LANCZOS)
    if lay.fg is not None and lay.fg.size != (int(W), int(H)):
        lay.fg = lay.fg.resize((int(W), int(H)), Image.LANCZOS)
    return lay


def library():
    return {'names': sorted(BGS.keys()), 'aliases': BG_ALIASES,
            'options': {'time': ['night', 'dusk', 'day'], 'lights': ['on', 'off', 'flicker'],
                        'ajar': '0..1 (door open amount: front_door, hallway, basement_door, house_exterior)',
                        'door_light': 'color of light behind an open door', 'tv': 'true/false (living_room)',
                        'fridge_open': 'true/false (kitchen)', 'closet_ajar': '0..1 (bedroom)', 'fire': 'true/false',
                        'tilt': 'degrees, crooked picture frame', 'floor_text': 'elevator floor number'}}
