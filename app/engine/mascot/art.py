"""Mascot kit v2: softer and richer.

Softer: limbs are one continuous tapered shape through the joint (no seam at elbow/knee), line art is
tinted from each fill colour instead of black, shading is a soft gradient, the head casts a soft
occlusion shadow on the body.
Richer: body types (normal/slim/chubby/kid/elder), more hair, accessories, outfits, iris + lashes.
Same frame as v1: units = 1/1000 character height, hip centre at (0,0), +y down.
"""
import math
from . import parts as K1

INK = '#2a1f2b'
LW = 7
_uid = [0]


def uid(p='c'):
    _uid[0] += 1
    return f'{p}{_uid[0]}'


def line_col(var):
    return f'color-mix(in srgb, var(--{var}) 38%, #1c1220)'


DEFS = '''<defs>
<linearGradient id="shadeH" x1="0" y1="0" x2="1" y2="0"><stop offset="0" stop-color="#fff" stop-opacity=".16"/>
<stop offset=".35" stop-color="#fff" stop-opacity="0"/><stop offset=".62" stop-color="#000" stop-opacity="0"/><stop offset="1" stop-color="#000" stop-opacity=".24"/></linearGradient>
<linearGradient id="shadeV" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="#fff" stop-opacity=".10"/>
<stop offset=".5" stop-color="#000" stop-opacity="0"/><stop offset="1" stop-color="#000" stop-opacity=".18"/></linearGradient>
<radialGradient id="headShade" cx=".38" cy=".32" r=".75"><stop offset="0" stop-color="#fff" stop-opacity=".22"/>
<stop offset=".45" stop-color="#fff" stop-opacity="0"/><stop offset=".8" stop-color="#000" stop-opacity=".06"/><stop offset="1" stop-color="#000" stop-opacity=".2"/></radialGradient>
<filter id="blur8" x="-50%" y="-50%" width="200%" height="200%"><feGaussianBlur stdDeviation="8"/></filter>
<filter id="blur4" x="-50%" y="-50%" width="200%" height="200%"><feGaussianBlur stdDeviation="4"/></filter>
</defs>'''


def soft(d, var, grad='shadeH', lw=LW, extra='', line=None):
    """Fill with a CSS colour var, soft gradient shading, tinted outline."""
    i = uid()
    s = f'<clipPath id="{i}"><path d="{d}"/></clipPath><path d="{d}" fill="var(--{var})"/>'
    if grad:
        s += f'<path d="{d}" fill="url(#{grad})"/>'
    if extra:
        s += f'<g clip-path="url(#{i})">{extra}</g>'
    s += f'<path d="{d}" fill="none" stroke="{line or line_col(var)}" stroke-width="{lw}" stroke-linejoin="round"/>'
    return s


def stroke(d, w=5, col=None, op=1, var=None):
    col = col or (line_col(var) if var else INK)
    return f'<path d="{d}" fill="none" stroke="{col}" stroke-width="{w}" stroke-linecap="round" stroke-linejoin="round" opacity="{op}"/>'


def ell(cx, cy, rx, ry):
    return K1.ell(cx, cy, rx, ry)


def path_from(pts, close=True):
    s = 'M' + ' L'.join(f'{x:.1f} {y:.1f}' for x, y in pts)
    return s + (' Z' if close else '')


# ------------------------------------------------------------------ continuous limbs
def chaikin(pts, n=3):
    for _ in range(n):
        out = [pts[0]]
        for a, b in zip(pts, pts[1:]):
            out += [(0.75 * a[0] + 0.25 * b[0], 0.75 * a[1] + 0.25 * b[1]), (0.25 * a[0] + 0.75 * b[0], 0.25 * a[1] + 0.75 * b[1])]
        out.append(pts[-1])
        pts = out
    return pts


def resample(pts, n=40):
    L = [0]
    for a, b in zip(pts, pts[1:]):
        L.append(L[-1] + math.hypot(b[0] - a[0], b[1] - a[1]))
    out, j = [], 0
    for i in range(n + 1):
        t = L[-1] * i / n
        while j < len(L) - 2 and L[j + 1] < t:
            j += 1
        seg = (L[j + 1] - L[j]) or 1
        k = (t - L[j]) / seg
        a, b = pts[j], pts[j + 1]
        out.append((a[0] + (b[0] - a[0]) * k, a[1] + (b[1] - a[1]) * k))
    return out


def tube(pts, widths, cap0=True, cap1=True):
    """Outline of a smooth tapered tube along pts. widths: list of (t, half_width)."""
    pts = resample(chaikin(pts), 48)
    n = len(pts)

    def w_at(t):
        for (t0, w0), (t1, w1) in zip(widths, widths[1:]):
            if t0 <= t <= t1:
                k = (t - t0) / ((t1 - t0) or 1)
                k = k * k * (3 - 2 * k)
                return w0 + (w1 - w0) * k
        return widths[-1][1]
    L, R = [], []
    for i in range(n):
        a, b = pts[max(0, i - 1)], pts[min(n - 1, i + 1)]
        dx, dy = b[0] - a[0], b[1] - a[1]
        ln = math.hypot(dx, dy) or 1
        nx, ny = -dy / ln, dx / ln
        w = w_at(i / (n - 1))
        L.append((pts[i][0] + nx * w, pts[i][1] + ny * w))
        R.append((pts[i][0] - nx * w, pts[i][1] - ny * w))

    def cap(p, q, w):
        ang = math.atan2(p[1] - q[1], p[0] - q[0])
        return [(p[0] + w * math.cos(ang + math.pi / 2 - math.pi * j / 10), p[1] + w * math.sin(ang + math.pi / 2 - math.pi * j / 10)) for j in range(1, 10)]
    out = L + (cap(pts[-1], pts[-2], w_at(1)) if cap1 else []) + R[::-1] + (cap(pts[0], pts[1], w_at(0)) if cap0 else [])
    return path_from(out), pts


def point_at(pts, t):
    return resample(pts, 100)[int(round(t * 100))]


# ------------------------------------------------------------------ body types
BODY = {
    'normal': dict(sw=1.0, hw=1.0, belly=0, leg=1.0, torso=1.0, head=1.0, arm=1.0),
    'slim':   dict(sw=.86, hw=.84, belly=0, leg=1.06, torso=1.04, head=.96, arm=.9),
    'chubby': dict(sw=1.12, hw=1.24, belly=26, leg=.92, torso=1.0, head=1.0, arm=1.12),
    'kid':    dict(sw=.82, hw=.82, belly=6, leg=.72, torso=.74, head=1.04, arm=.82),
    'elder':  dict(sw=.98, hw=1.06, belly=10, leg=.94, torso=.96, head=.98, arm=.95),
}


def torso_path(b):
    SW, HW, by = 188 * b['sw'], 176 * b['hw'], b['belly']
    T = -345 * b['torso']
    s = (f'M{-72 * b["sw"]} {T} C{-SW * .8} {T - 5} {-SW * 1.02} {T + 18} {-SW} {T + 66} '
         f'C{-SW - by * .3} {T * .55} {-HW - by} {-110} {-HW} {-14} C{-HW + 1} 6 {-HW + 12} 14 {-HW + 28} 14 '
         f'L{HW - 28} 14 C{HW - 12} 14 {HW - 1} 6 {HW} -14 C{HW + by} -110 {SW + by * .3} {T * .55} {SW} {T + 66} '
         f'C{SW * 1.02} {T + 18} {SW * .8} {T - 5} {72 * b["sw"]} {T} Z')
    return s, T, SW, HW


# ------------------------------------------------------------------ head
def head(c, pose, b):
    hs = b['head']
    eyes, brows, mouth = pose.get('eyes', 'open'), pose.get('brows', 'normal'), pose.get('mouth', 'X')
    look = pose.get('look', 0)
    d = ('M0 -369 C112 -369 194 -292 194 -190 C194 -84 112 -2 0 -2 C-112 -2 -194 -84 -194 -190 C-194 -292 -112 -369 0 -369 Z')
    s = ''
    for side in (-1, 1):
        x = side * 188
        s += soft(ell(x, -168, 36, 46), 'skin', 'shadeH') + stroke(f'M{x - side * 2} -194 C{x + side * 20} -184 {x + side * 20} -152 {x - side * 2} -144', 5, var='skin', op=.8)
    s += soft(d, 'skin', 'headShade', 7)
    cx, cy = look * 14, -185
    # cheeks
    for side in (-1, 1):
        s += f'<path d="{ell(cx + side * 118, cy + 58, 30, 17)}" fill="#ff6f86" opacity=".2" filter="url(#blur4)"/>'
    if c.get('freckles'):
        for side in (-1, 1):
            for dx, dy in ((-14, -6), (4, 2), (18, -8), (-4, 12)):
                s += f'<circle cx="{cx + side * (118 + dx)}" cy="{cy + 50 + dy}" r="3.2" fill="#a0603e" opacity=".55"/>'
    if b is BODY['elder']:
        for side in (-1, 1):
            s += stroke(f'M{cx + side * 98} {cy + 2} l{side * 16} -8 M{cx + side * 98} {cy + 14} l{side * 18} 2', 3.5, var='skin', op=.7)
    for side in (-1, 1):
        ex = cx + side * 64
        tr = f'translate({ex} {cy + 12})' + (' scale(-1 1)' if side > 0 else '')
        s += f'<g transform="{tr}">{eye2(eyes, c)}</g>'
        btr = f'translate({ex} {cy - 48 - (10 if brows in ("scared", "raised") else 0)})' + (' scale(-1 1)' if side > 0 else '')
        bc = f'color-mix(in srgb, var(--hair) 70%, #1c1220)' if c['hair'] not in ('none', 'buzz') else INK
        s += f'<g transform="{btr}">{K1.brow(brows).replace(K1.INK, bc)}</g>'
    if 'beard' in c.get('wear', ()):
        s += soft('M-170 -160 C-160 -40 -90 8 0 8 C90 8 160 -40 170 -160 C150 -110 110 -96 60 -96 C30 -112 -30 -112 -60 -96 C-110 -96 -150 -110 -170 -160 Z', 'hair', 'shadeV', 5)
    if 'mustache' in c.get('wear', ()) or 'beard' in c.get('wear', ()):
        s += soft(f'M{cx - 54} {cy + 70} C{cx - 30} {cy + 50} {cx - 8} {cy + 56} {cx} {cy + 64} C{cx + 8} {cy + 56} {cx + 30} {cy + 50} {cx + 54} {cy + 70} C{cx + 30} {cy + 74} {cx + 10} {cy + 70} {cx} {cy + 72} C{cx - 10} {cy + 70} {cx - 30} {cy + 74} {cx - 54} {cy + 70} Z', 'hair', None, 4)
    s += f'<g transform="translate({cx} {cy + 86})">{K1.mouth(mouth)}</g>'
    if pose.get('sweat'):
        s += f'<path d="M-150 -300 C-160 -280 -172 -262 -160 -250 C-150 -242 -136 -250 -140 -266 Z" fill="#8cc8f5" stroke="{INK}" stroke-width="4"/>'
    s += hair_front2(c['hair'])
    s += wear_head(c)
    return s


def eye2(kind, c):
    if kind == 'open' and c.get('iris'):
        s = (f'<path d="{ell(0, 0, 19, 24)}" fill="{INK}"/><path d="{ell(0, 3, 13, 17)}" fill="var(--eye)"/>'
             f'<path d="{ell(0, 4, 7, 9)}" fill="{INK}"/><circle cx="-6" cy="-9" r="6.5" fill="#fff"/><circle cx="6" cy="10" r="2.5" fill="#fff" opacity=".8"/>')
    else:
        s = K1.eye(kind)
    if c.get('lashes') and kind in ('open', 'half', 'wide', 'stare'):
        s += stroke('M-16 -18 L-28 -26 M-19 -9 L-32 -12', 4.5)
    return s


def hair_back2(kind):
    if kind == 'bob':
        return soft('M-206 -230 C-214 -120 -206 -30 -170 -14 L170 -14 C206 -30 214 -120 206 -230 Z', 'hair', 'shadeH', 6)
    if kind == 'bun':
        return soft(ell(0, -392, 74, 62), 'hair', 'shadeH', 6)
    if kind == 'curly':
        s = ''
        for i in range(12):
            a = math.radians(170 + i * 200 / 11)
            s += soft(ell(214 * math.cos(a), -190 + 200 * math.sin(a), 52, 52), 'hair', 'shadeH', 6)
        return s
    return K1.hair_back(kind).replace(f'stroke="{K1.INK}" stroke-width="{K1.LW}"', f'stroke="{line_col("hair")}" stroke-width="6"')


def hair_front2(kind):
    if kind in ('none', '', None):
        return ''
    if kind == 'buzz':
        return f'<path d="M-192 -200 C-190 -310 -110 -370 0 -370 C110 -370 190 -310 192 -200 C150 -260 80 -282 0 -282 C-80 -282 -150 -260 -192 -200 Z" fill="var(--hair)" opacity=".55"/>'
    if kind == 'bangs' or kind == 'bob':
        d = ('M-204 -150 C-216 -300 -120 -380 0 -378 C120 -380 216 -300 204 -150 C196 -200 176 -236 150 -248 '
             'L150 -250 C100 -236 50 -244 20 -262 C-10 -242 -60 -236 -100 -246 C-140 -238 -176 -214 -204 -150 Z')
        return soft(d, 'hair', 'shadeH', 6) + stroke('M-60 -330 C-50 -300 -40 -280 -30 -262 M40 -340 C46 -310 44 -290 40 -266', 4, var='hair', op=.7)
    if kind == 'bun':
        d = ('M-198 -170 C-212 -300 -120 -378 0 -376 C120 -378 212 -300 198 -170 C186 -230 120 -276 0 -282 C-120 -276 -186 -230 -198 -170 Z')
        return soft(d, 'hair', 'shadeH', 6) + stroke('M-120 -330 C-60 -300 0 -296 40 -300 M20 -360 C60 -330 120 -316 160 -300', 4, var='hair', op=.7)
    if kind == 'curly':
        s = ''
        for i in range(9):
            a = math.radians(195 + i * 150 / 8)
            s += soft(ell(176 * math.cos(a), -190 + 178 * math.sin(a), 50, 46), 'hair', 'shadeH', 6)
        return s
    raw = K1.hair_front(kind)
    return raw.replace(f'stroke="{K1.INK}" stroke-width="{K1.LW}"', f'stroke="{line_col("hair")}" stroke-width="6"')


def wear_head(c):
    w = c.get('wear', ())
    s = ''
    if 'glasses' in w:
        for side in (-1, 1):
            s += f'<circle cx="{side * 64}" cy="-173" r="38" fill="#fff" fill-opacity=".12" stroke="{INK}" stroke-width="7"/>'
        s += stroke('M-26 -178 Q0 -190 26 -178 M-102 -178 L-180 -190 M102 -178 L180 -190', 6)
    if 'cap' in w:
        s += soft('M-196 -230 C-200 -330 -110 -386 0 -386 C110 -386 200 -330 196 -230 Z', 'acc', 'shadeH', 7)
        s += soft('M-150 -236 C-80 -262 80 -262 150 -236 C170 -230 176 -214 150 -210 C80 -226 -80 -226 -150 -210 C-176 -214 -170 -230 -150 -236 Z', 'acc', 'shadeV', 6)
        s += f'<circle cx="0" cy="-384" r="12" fill="var(--acc)" stroke="{line_col("acc")}" stroke-width="5"/>'
    if 'bus_cap' in w:
        s += soft('M-200 -236 C-204 -330 -110 -392 0 -392 C110 -392 204 -330 200 -236 Z', 'acc', 'shadeH', 7)
        s += soft('M-206 -250 L206 -250 L206 -214 L-206 -214 Z', 'acc', 'shadeV', 6)
        s += f'<rect x="-34" y="-318" width="68" height="40" rx="8" fill="#c9a23a" stroke="{INK}" stroke-width="5"/>'
        s += soft('M-170 -222 C-90 -244 90 -244 170 -222 C190 -214 190 -196 166 -190 C80 -208 -80 -208 -166 -190 C-190 -196 -190 -214 -170 -222 Z', 'acc', 'shadeV', 6)
        # the brim's shadow hides the driver's eyes
        s += f'<path d="{ell(0, -168, 150, 36)}" fill="#05060a" opacity=".82" filter="url(#blur4)"/>'
    if 'beanie' in w:
        s += soft('M-200 -236 C-204 -340 -110 -400 0 -400 C110 -400 204 -340 200 -236 Z', 'acc', 'shadeH', 7,
                  extra=''.join(f'<path d="M{x} -400 L{x} -240" stroke="#000" stroke-opacity=".12" stroke-width="6"/>' for x in range(-160, 170, 32)))
        s += soft('M-206 -250 L206 -250 L206 -204 C140 -196 -140 -196 -206 -204 Z', 'acc', 'shadeV', 6)
        s += soft(ell(0, -404, 34, 30), 'acc', 'shadeH', 6)
    return s


# ------------------------------------------------------------------ torso + outfits
def torso2(c, b):
    d, T, SW, HW = torso_path(b)
    kind = c['top']
    i = uid()
    s = f'<clipPath id="{i}"><path d="{d}"/></clipPath>'
    ao = f'<path d="{ell(0, T + 30, 150, 46)}" fill="#000" opacity=".22" filter="url(#blur8)"/>'
    folds = stroke(f'M{-HW * .55} -40 Q{-HW * .45} -80 {-HW * .5} -120 M{HW * .6} -30 Q{HW * .52} -70 {HW * .58} -100', 4, var='top', op=.45)
    hem = f'<path d="M{-HW - 40} -24 L{HW + 40} -24 L{HW + 40} 20 L{-HW - 40} 20 Z" fill="#000" opacity=".1"/>' + stroke(f'M{-HW + 4} -26 L{HW - 4} -26', 4, var='top', op=.7)
    if kind in ('hoodie', 'sweater', 'tshirt', 'scrubs'):
        extra = ao + folds + (hem if kind in ('hoodie', 'sweater') else '')
        if kind == 'sweater':
            extra += ''.join(stroke(f'M{x} -22 L{x} 14', 3, var='top', op=.6) for x in range(int(-HW) + 14, int(HW), 16))
            extra += ''.join(stroke(f'M{-SW} {y} Q0 {y + 14} {SW} {y}', 3, var='top', op=.25) for y in range(int(T) + 70, -40, 34))
        s += soft(d, 'top', 'shadeH', LW, extra)
        if kind == 'hoodie':
            s += soft(f'M-78 -150 L78 -150 L102 -58 L-102 -58 Z', 'top', 'shadeV', 5)
            s += soft(f'M-120 {T - 5} C-114 {T + 63} 114 {T + 63} 120 {T - 5} C86 {T - 27} -86 {T - 27} -120 {T - 5} Z', 'top', 'shadeV', 6)
            s += f'<path d="{ell(0, T + 3, 56, 18)}" fill="var(--top2)" stroke="{line_col("top2")}" stroke-width="5"/>'
            for side in (-1, 1):
                s += stroke(f'M{side * 30} {T + 27} C{side * 34} {T + 55} {side * 28} {T + 75} {side * 32} {T + 99}', 6, '#f4f2ee')
                s += f'<rect x="{side * 32 - 5}" y="{T + 95}" width="10" height="16" rx="4" fill="#d9d4cc" stroke="{INK}" stroke-width="3"/>'
        elif kind == 'sweater':
            s += soft(f'M-74 {T + 2} C-60 {T + 38} 60 {T + 38} 74 {T + 2} C40 {T - 12} -40 {T - 12} -74 {T + 2} Z', 'top', 'shadeV', 5)
            s += f'<path d="{ell(0, T + 6, 52, 16)}" fill="var(--skin)" stroke="{line_col("skin")}" stroke-width="4"/>'
        elif kind in ('tshirt', 'scrubs'):
            if kind == 'scrubs':
                s += soft(f'M-60 {T + 2} L0 {T + 78} L60 {T + 2} Z', 'skin', None, 5)
                s += soft(f'M{SW * .25} {T + 110} L{SW * .7} {T + 110} L{SW * .7} {T + 170} L{SW * .25} {T + 170} Z', 'top', 'shadeV', 4)
            else:
                s += f'<path d="{ell(0, T + 5, 60, 24)}" fill="var(--skin)" stroke="{line_col("skin")}" stroke-width="5"/>'
                s += stroke(f'M-64 {T + 14} Q0 {T + 46} 64 {T + 14}', 8, 'var(--top2)')
    elif kind == 'jacket':
        s += soft(d, 'top', 'shadeH', LW, ao + folds)
        s += soft(f'M-46 {T + 1} L46 {T + 1} L40 14 L-40 14 Z', 'top2', 'shadeH', 5)
        for side in (-1, 1):
            s += soft(f'M{side * 46} {T - 1} L{side * 102} {T + 5} L{side * 62} {T + 115} L{side * 44} {T + 75} Z', 'top', 'shadeV', 5)
        s += stroke('M-44 -260 L-42 6 M44 -260 L42 6', 4, var='top', op=.8)
    elif kind == 'raincoat':
        long = d.replace(' 14 ', ' 120 ').replace(' -14 ', ' 92 ')
        d2 = (f'M{-72 * b["sw"]} {T} C{-SW * .8} {T - 5} {-SW * 1.02} {T + 18} {-SW} {T + 66} C{-SW - 6} -150 {-HW - 22} 20 {-HW - 26} 110 '
              f'C{-HW - 20} 126 {HW + 20} 126 {HW + 26} 110 C{HW + 22} 20 {SW + 6} -150 {SW} {T + 66} C{SW * 1.02} {T + 18} {SW * .8} {T - 5} {72 * b["sw"]} {T} Z')
        s += soft(d2, 'top', 'shadeH', LW, ao + stroke(f'M0 {T + 10} L0 120', 5, var='top', op=.8))
        for y in (T + 80, T + 170, T + 260, T + 350):
            s += f'<circle cx="-22" cy="{y}" r="9" fill="color-mix(in srgb, var(--top) 60%, #000)"/>'
        s += soft(f'M-130 {T - 4} C-120 {T + 70} 120 {T + 70} 130 {T - 4} C90 {T - 30} -90 {T - 30} -130 {T - 4} Z', 'top', 'shadeV', 6)
    elif kind == 'uniform':
        s += soft(d, 'top', 'shadeH', LW, ao + folds)
        s += stroke(f'M0 {T + 30} L0 0', 5, var='top', op=.8)
        for y in range(int(T) + 70, -30, 70):
            s += f'<circle cx="0" cy="{y}" r="7" fill="#d9d2bf" stroke="{line_col("top")}" stroke-width="3"/>'
        for side in (-1, 1):
            s += soft(f'M0 {T + 30} L{side * 70} {T - 4} L{side * 96} {T + 40} L{side * 26} {T + 62} Z', 'top', 'shadeV', 5)
            s += soft(f'M{side * 70} {T + 110} L{side * 140} {T + 110} L{side * 140} {T + 170} L{side * 70} {T + 170} Z', 'top', 'shadeV', 4)
        s += f'<path d="M60 {T + 92} l26 -8 l26 8 l-4 30 l-22 14 l-22 -14 Z" fill="#d8b44a" stroke="{INK}" stroke-width="4"/>'
        s += soft(f'M{-HW} -40 L{HW} -40 L{HW} -6 L{-HW} -6 Z', 'pants', None, 5) + f'<rect x="-22" y="-42" width="44" height="38" rx="5" fill="#cfc6a8" stroke="{INK}" stroke-width="4"/>'
    elif kind == 'dress':
        s += soft(d, 'top', 'shadeH', LW, ao)
        s += f'<path d="{ell(0, T + 5, 60, 24)}" fill="var(--skin)" stroke="{line_col("skin")}" stroke-width="5"/>'
        s += soft(f'M{-HW + 4} -40 C{-HW - 40} 40 {-HW - 70} 120 {-HW - 76} 150 C-60 172 60 172 {HW + 76} 150 C{HW + 70} 120 {HW + 40} 40 {HW - 4} -40 Z', 'top', 'shadeH', LW,
                  stroke('M-60 0 Q-70 80 -84 150 M0 10 L0 160 M60 0 Q70 80 84 150', 4, var='top', op=.4))
        s += stroke(f'M{-HW + 6} -40 Q0 -28 {HW - 6} -40', 10, 'color-mix(in srgb, var(--top) 70%, #000)')
    # accessories on the body
    w = c.get('wear', ())
    if 'scarf' in w:
        s += soft(f'M-130 {T + 4} C-120 {T + 58} 120 {T + 58} 130 {T + 4} C110 {T - 22} -110 {T - 22} -130 {T + 4} Z', 'acc', 'shadeV', 6)
        s += soft(f'M40 {T + 40} L84 {T + 40} L90 {T + 170} L46 {T + 170} Z', 'acc', 'shadeH', 5, ''.join(stroke(f'M40 {T + y} L90 {T + y}', 6, '#000', .15) for y in (80, 110, 140)))
    if 'backpack' in w:
        for side in (-1, 1):
            s += soft(f'M{side * 96} {T + 8} C{side * 106} {T + 90} {side * 112} {T + 180} {side * 118} {T + 230} L{side * 146} {T + 226} C{side * 138} {T + 150} {side * 130} {T + 70} {side * 126} {T + 4} Z', 'acc', 'shadeV', 5)
    if 'name_tag' in w:
        s += f'<rect x="{SW * .3}" y="{T + 100}" width="70" height="36" rx="5" fill="#f4f2ee" stroke="{INK}" stroke-width="4"/>' + stroke(f'M{SW * .3 + 12} {T + 118} l46 0', 4, '#8a8f99')
    return s, T


# ------------------------------------------------------------------ assembly
LAST = {}          # key points of the last assembled character (for QA)


def _rot(p, deg, c=(0, 0)):
    r = math.radians(deg)
    x, y = p[0] - c[0], p[1] - c[1]
    return (c[0] + x * math.cos(r) - y * math.sin(r), c[1] + x * math.sin(r) + y * math.cos(r))


def landmarks(b, T):
    """Body landmarks in torso coordinates (hip centre = 0,0), used as IK targets."""
    hs = b['head']
    neck = T + 10
    hc = (0, neck - 185 * hs)
    return {
        'head': hc, 'mouth': (0, neck + (-185 + 86) * hs), 'chin': (0, neck - 30 * hs), 'nose': (0, neck - 140 * hs),
        'ear_L': (-188 * hs, neck - 168 * hs), 'ear_R': (188 * hs, neck - 168 * hs),
        'cheek_L': (-140 * hs, neck - 120 * hs), 'cheek_R': (140 * hs, neck - 120 * hs),
        'temple_L': (-170 * hs, neck - 250 * hs), 'temple_R': (170 * hs, neck - 250 * hs),
        'top_L': (-120 * hs, neck - 330 * hs), 'top_R': (120 * hs, neck - 330 * hs),
        'chest': (0, T + 120), 'belly': (0, T + 230), 'arm_L': (-150 * b['sw'], T + 130), 'arm_R': (150 * b['sw'], T + 130),
    }


def ground_off(legs, TH, SH):
    ext = max(TH * math.cos(math.radians(legs[0])) + SH * math.cos(math.radians(legs[1])),
              TH * math.cos(math.radians(legs[2])) + SH * math.cos(math.radians(legs[3])))
    return (TH + SH) - ext


def chair(hip_y, ground_y, wide=1.0):
    w = 190 * wide
    s = soft(f'M{-w} {hip_y - 330} L{w} {hip_y - 330} L{w * .95} {hip_y - 40} L{-w * .95} {hip_y - 40} Z', 'chair', 'shadeH', 6)
    s += soft(f'M{-w - 20} {hip_y - 10} L{w + 20} {hip_y - 10} L{w + 26} {hip_y + 36} L{-w - 26} {hip_y + 36} Z', 'chair', 'shadeV', 6)
    for x in (-w + 10, w - 30):
        s += soft(f'M{x} {hip_y + 30} L{x + 20} {hip_y + 30} L{x + 20} {ground_y} L{x} {ground_y} Z', 'chair', None, 5)
    return s


def wheel(cx, cy):
    return (f'<circle cx="{cx}" cy="{cy}" r="120" fill="none" stroke="#1f2228" stroke-width="30"/>'
            f'<circle cx="{cx}" cy="{cy}" r="120" fill="none" stroke="#3a3f48" stroke-width="10"/>'
            f'<path d="M{cx - 110} {cy + 10} Q{cx} {cy + 40} {cx + 110} {cy + 10}" stroke="#1f2228" stroke-width="22" fill="none"/>')


def beam(p, ang, length=900, w0=30, w1=260, col='#fff2c0', op=.22):
    d = (-math.sin(math.radians(ang)), math.cos(math.radians(ang)))
    n = (-d[1], d[0])
    e = (p[0] + d[0] * length, p[1] + d[1] * length)
    pts = [(p[0] + n[0] * w0, p[1] + n[1] * w0), (e[0] + n[0] * w1, e[1] + n[1] * w1),
           (e[0] - n[0] * w1, e[1] - n[1] * w1), (p[0] - n[0] * w0, p[1] - n[1] * w0)]
    i = uid('b')
    return (f'<linearGradient id="{i}" gradientUnits="userSpaceOnUse" x1="{p[0]:.0f}" y1="{p[1]:.0f}" x2="{e[0]:.0f}" y2="{e[1]:.0f}">'
            f'<stop offset="0" stop-color="{col}" stop-opacity="{op}"/><stop offset="1" stop-color="{col}" stop-opacity="0"/></linearGradient>'
            f'<path d="{path_from(pts)}" fill="url(#{i})"/>')


def paper(cx, cy, ang=0):
    return (f'<g transform="translate({cx:.0f} {cy:.0f}) rotate({ang:.0f})"><rect x="-80" y="-104" width="160" height="208" rx="6" fill="#efe9da" stroke="{INK}" stroke-width="6"/>'
            + ''.join(f'<path d="M-56 {y} L56 {y}" stroke="#9a9384" stroke-width="6"/>' for y in (-70, -44, -18, 8, 34)) + '</g>')


def char2(c, pose):
    b = BODY[c.get('body', 'normal')]
    top_sleeve = 'short' if c['top'] in ('tshirt', 'scrubs', 'dress') else 'long'
    UP, FO = 150 * b['arm'], 140 * b['arm']
    TH, SH = 150 * b['leg'], 132 * b['leg']
    hipx = 72 * b['hw']
    torso_svg, T = torso2(c, b)
    shoulder = (148 * b['sw'], T + 45)
    foot_y = TH + SH
    lm = landmarks(b, T)
    tk = pose.get('thigh_k', 1.0)          # < 1: thighs point towards the camera (sitting, crouching)

    def dirv(a):
        r = math.radians(a)
        return (-math.sin(r), math.cos(r))

    def limb_pts(base, a1, a2, l1, l2):
        d1, d2 = dirv(a1), dirv(a2)
        j = (base[0] + d1[0] * l1, base[1] + d1[1] * l1)
        e = (j[0] + d2[0] * l2, j[1] + d2[1] * l2)
        return [base, j, e]

    # legs
    legs = pose.get('legs', (4, 2, -4, -2))
    yoff = TH * (1 - tk) + ground_off(legs, TH * tk, SH) + pose.get('lift', 0)
    leg_svg = ''
    feet = []
    for side, (a1, a2) in ((-1, legs[:2]), (1, legs[2:])):
        pts = limb_pts((side * hipx, 0), a1, a2, TH * tk, SH)
        pts = [(side * hipx, -30)] + pts[1:]
        w = 52 * (1.1 if c.get('body') == 'chubby' else 1) * (0.86 if c.get('body') in ('slim', 'kid') else 1)
        if tk < 0.7:
            # foreshortened thigh: a rounded knee bump pointing at the viewer
            knee = pts[1]
            dpath, _ = tube([(side * hipx, -30), knee], [(0, w * 1.02), (1, w * 1.08)])
            spath, _ = tube([knee, pts[2]], [(0, w * .98), (1, w * .84)])
            var = 'skin' if c['top'] == 'dress' else 'pants'
            leg_svg += soft(spath, var, 'shadeH', LW) + soft(dpath, var, 'shadeV', LW)
        else:
            dpath, cpts = tube(pts, [(0, w), (.55, w * .92), (1, w * .84)], cap0=False)
            var = 'skin' if c['top'] == 'dress' else 'pants'
            leg_svg += soft(dpath, var, 'shadeH', LW)
        ank = pts[-1]
        feet.append(ank)
        leg_svg += f'<g transform="translate({ank[0]:.1f} {ank[1]:.1f})">{shoe2()}</g>'
    # arms
    arm_svg = ''
    front_svg = ''
    hands = pose.get('hands', ('open', 'open'))
    props = pose.get('props', (None, None))
    wrists, wangs = {}, {}
    for side, key, hk, prop in ((-1, 'L', hands[0], props[0]), (1, 'R', hands[1], props[1])):
        spec = pose.get('arm' + key, ('angles', side * -10, side * -6))
        sp = (side * shoulder[0], shoulder[1])
        if spec[0] in ('target', 'at'):
            if spec[0] == 'at':
                tx, ty = lm[spec[1]]
                tx, ty = tx + spec[2], ty + spec[3]
                bend = spec[4] if len(spec) > 4 else side
            else:
                tx, ty, bend = spec[1], spec[2], (spec[3] if len(spec) > 3 else side)
            a1, a2 = K1.ik(sp[0], sp[1], tx, ty, UP, FO, bend)
        else:
            a1, a2 = spec[1], spec[2]
        pts = limb_pts(sp, a1, a2, UP, FO)
        wa = 38 * (1.12 if c.get('body') == 'chubby' else 1) * (0.88 if c.get('body') in ('slim', 'kid') else 1)
        if top_sleeve == 'long':
            dpath, cpts = tube(pts, [(0, wa), (.5, wa * .9), (1, wa * .8)])
            cuff_d, _ = tube([point_at(cpts, .86), pts[-1]], [(0, wa * .84), (1, wa * .82)])
            arm_svg += soft(dpath, 'top', 'shadeH', LW) + soft(cuff_d, 'top', 'shadeV', 5)
        else:
            skin_d, cpts = tube(pts, [(0, wa * .66), (1, wa * .58)])
            sl = resample(chaikin(pts), 48)
            k = int(len(sl) * .3)
            sleeve_d, _ = tube(sl[:k + 1], [(0, wa * 1.05), (1, wa * 1.0)])
            arm_svg += soft(skin_d, 'skin', 'shadeH', LW) + soft(sleeve_d, 'top', 'shadeH', LW)
        wr = pts[-1]
        ang = math.degrees(math.atan2(pts[-1][1] - pts[1][1], pts[-1][0] - pts[1][0])) - 90 + pose.get('wrist_' + key, 0)
        wrists[key], wangs[key] = wr, ang
        hp = K1.hand(hk)
        hp = hp.replace(f'stroke="{K1.INK}" stroke-width="{K1.LW}"', f'stroke="{line_col("skin")}" stroke-width="6"').replace(f'stroke="{K1.INK}" stroke-width="{K1.LW2}"', f'stroke="{line_col("skin")}" stroke-width="5"')
        if prop:
            hp = f'<g transform="translate(0 40)">{prop}</g>' + hp
        if side > 0:
            hp = f'<g transform="scale(-1 1)">{hp}</g>'
        arm_svg += f'<g transform="translate({wr[0]:.1f} {wr[1] - 4:.1f}) rotate({ang:.1f})">{hp}</g>'
        if pose.get('beam') == key:
            d = dirv(ang)
            front_svg += beam((wr[0] + d[0] * 110, wr[1] + d[1] * 110), ang, pose.get('beam_len', 1100))
    mid_svg = ''
    if pose.get('paper'):
        cx = (wrists['L'][0] + wrists['R'][0]) / 2
        cy = (wrists['L'][1] + wrists['R'][1]) / 2 + 10
        mid_svg += paper(cx, cy, pose.get('paper_ang', 0))
    if pose.get('wheel'):
        cx = (wrists['L'][0] + wrists['R'][0]) / 2
        cy = (wrists['L'][1] + wrists['R'][1]) / 2 + 30
        front_svg = wheel(cx, cy) + front_svg
    tilt = pose.get('tilt', 0)
    neck = T + 10
    head_svg = head(c, pose, b)
    hs = b['head']
    hb = hair_back2(c['hair'])
    hb_svg = f'<g transform="translate(0 {neck}) rotate({tilt + pose.get("hair_rot", 0)}) scale({hs})">{hb}</g>' if hb else ''
    head_g = f'<g transform="translate(0 {neck}) rotate({tilt}) scale({hs})">{head_svg}</g>'
    head_ao = f'<path d="{ell(0, neck + 6, 130, 30)}" fill="#000" opacity=".18" filter="url(#blur8)"/>'
    style = ';'.join(f'--{k}:{v}' for k, v in c['colors'].items())
    shadow = f'<ellipse cx="0" cy="{foot_y + 52}" rx="{220 * b["hw"]}" ry="26" fill="#000" opacity=".2" filter="url(#blur4)"/>'
    lean = pose.get('lean', 0)
    seat = chair(yoff + 10, foot_y + 50, b['hw']) if pose.get('seat') else ''
    upper = f'{torso_svg}{head_ao}{head_g}{mid_svg}{arm_svg}{front_svg}'
    if pose.get('lean_mode') == 'hip':
        body = f'<g transform="rotate({lean} 0 0)">{hb_svg}</g>' + leg_svg + f'<g transform="rotate({lean} 0 0)">{upper}</g>'
        pivot = (0, 0)
    else:
        pivot = (0, foot_y - yoff)
        body = f'<g transform="rotate({lean} 0 {foot_y - yoff:.1f})">{hb_svg}{leg_svg}{upper}</g>'
    # key points in the final (outer) frame for automatic checks
    def outp(p, upper_part=True):
        q = _rot(p, lean, pivot) if (upper_part or pose.get('lean_mode') != 'hip') else p
        return (q[0], q[1] + yoff)
    hc = lm['head']
    LAST.clear()
    LAST.update(feet=[outp(f, False) for f in feet], ground=foot_y + 50, wrist_L=outp(wrists['L']), wrist_R=outp(wrists['R']),
                wang_L=wangs['L'], wang_R=wangs['R'], mouth=outp(_rot(lm['mouth'], tilt, (0, neck))),
                ear_L=outp(_rot(lm['ear_L'], tilt, (0, neck))), ear_R=outp(_rot(lm['ear_R'], tilt, (0, neck))),
                chin=outp(_rot(lm['chin'], tilt, (0, neck))), head=outp(_rot(hc, tilt, (0, neck))), head_r=190 * hs,
                hands=hands, props=tuple(bool(p) for p in props), seat=bool(pose.get('seat')))
    return f'<g style="{style}">{shadow}{seat}<g transform="translate(0 {yoff:.1f})">{body}</g></g>', foot_y + 55


def shoe2():
    d = 'M-62 50 C-64 6 -34 -12 0 -12 C34 -12 64 6 62 50 Z'
    s = soft(d, 'shoe', 'shadeH', 6, f'<path d="{ell(-24, 6, 18, 9)}" fill="#fff" opacity=".25"/>')
    s += soft('M-64 38 L64 38 L64 56 C64 60 -64 60 -64 56 Z', 'shoe', None, 5, '<path d="M-80 30 L80 30 L80 50 L-80 50 Z" fill="#fff" opacity=".35"/>')
    s += stroke('M-14 -2 L14 -2 M-18 10 L18 10', 4, var='shoe', op=.8)
    return s


CAST2 = {
    'Mẫu (ảnh của bạn)': dict(top='hoodie', hair='none', colors=dict(skin='#ffffff', top='#4a86d9', top2='#f4f2ee', pants='#8f949c', shoe='#7d828a', hair='#2b1e17', acc='#333', eye='#5b3a24')),
    'Mia': dict(top='hoodie', hair='ponytail', lashes=True, iris=True, freckles=True, colors=dict(skin='#f6dcc4', top='#b23b48', top2='#f4f2ee', pants='#2f3a4f', shoe='#2b2f36', hair='#5a3420', acc='#333', eye='#6b8e3a')),
    'Dale (lớn tuổi)': dict(top='jacket', hair='short', body='elder', wear=('beard', 'cap'), colors=dict(skin='#eac8a6', top='#6b4a2e', top2='#c9c2b2', pants='#4a4a3a', shoe='#3a2a20', hair='#b5b5b5', acc='#a33a2a', eye='#4a5a6a')),
    'Josh': dict(top='tshirt', hair='curly', body='slim', wear=('backpack',), colors=dict(skin='#a8754f', top='#3c8f5a', top2='#2f7148', pants='#2a3344', shoe='#e9e6e0', hair='#1d1612', acc='#e0a030', eye='#3a2414')),
    'Y tá Rosa': dict(top='scrubs', hair='bun', lashes=True, iris=True, wear=('glasses',), colors=dict(skin='#e8bf9c', top='#5bb0a8', top2='#5bb0a8', pants='#4c9c94', shoe='#f2f2f2', hair='#2a1a14', acc='#333', eye='#3a2414')),
    'Bảo vệ Hank': dict(top='uniform', hair='buzz', body='chubby', wear=('mustache', 'name_tag'), colors=dict(skin='#f0cfb0', top='#2e3b52', top2='#2e3b52', pants='#232b3a', shoe='#15181d', hair='#3a2a20', acc='#333', eye='#3a2a20')),
    'Lily (bé)': dict(top='dress', hair='bob', body='kid', lashes=True, iris=True, colors=dict(skin='#f8e0cc', top='#e98fb0', top2='#e98fb0', pants='#f8e0cc', shoe='#c8406a', hair='#e0b050', acc='#333', eye='#3a7ab8')),
    'Sam': dict(top='raincoat', hair='bangs', wear=('scarf',), colors=dict(skin='#d9a888', top='#e7b72c', top2='#e7b72c', pants='#36404f', shoe='#2b2f36', hair='#6b3a1e', acc='#c0392b', eye='#4a2a1a')),
    'Leo': dict(top='sweater', hair='messy', wear=('beanie',), colors=dict(skin='#f2d2b6', top='#3f6b8f', top2='#3f6b8f', pants='#5a4a3a', shoe='#3a2a20', hair='#2b1e17', acc='#d0703a', eye='#3a2414')),
}

def solve_arms(c, pose):
    """Turn 'at' / 'target' arm specs into plain angles so poses can be blended. Records unreachable targets."""
    b = BODY[c.get('body', 'normal')]
    UP, FO = 150 * b['arm'], 140 * b['arm']
    _, T, _, _ = torso_path(b)
    lm = landmarks(b, T)
    shoulder = (148 * b['sw'], T + 45)
    out = dict(pose)
    far = []
    for side, key in ((-1, 'L'), (1, 'R')):
        spec = pose.get('arm' + key, ('angles', side * -10, side * -6))
        if spec[0] not in ('target', 'at'):
            continue
        if spec[0] == 'at':
            tx, ty = lm[spec[1]]
            tx, ty = tx + spec[2], ty + spec[3]
            bend = spec[4] if len(spec) > 4 else side
        else:
            tx, ty, bend = spec[1], spec[2], (spec[3] if len(spec) > 3 else side)
        sp = (side * shoulder[0], shoulder[1])
        if math.hypot(tx - sp[0], ty - sp[1]) > UP + FO + 2:
            far.append(key)
        a1, a2 = K1.ik(sp[0], sp[1], tx, ty, UP, FO, bend)
        out['arm' + key] = ('angles', a1, a2)
    out['_unreachable'] = far
    return out
