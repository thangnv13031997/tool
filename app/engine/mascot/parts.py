"""Mascot character kit (v1 parts, reused by art.py): every body part as an SVG snippet in its own local frame.

Frame: units = 1/1000 of the character height. Each part's pivot is (0, 0) and limbs hang
down along +y, so rotating a part = rotating around its joint. Colours come from CSS variables
(--skin, --top, --top2, --pants, --shoe, --hair), so one drawing serves every character:
shading is a translucent dark layer clipped to the part, not a baked colour.
"""
import math, json

INK = '#1d1b24'
LW = 8          # outer line
LW2 = 5         # inner detail line

_uid = [0]


def uid(p='c'):
    _uid[0] += 1
    return f'{p}{_uid[0]}'


def shaded(d, fill, shade_d=None, hl_d=None, lw=LW, extra=''):
    """Filled outlined shape; optional shadow / highlight paths clipped inside it."""
    i = uid()
    s = f'<clipPath id="{i}"><path d="{d}"/></clipPath>'
    s += f'<path d="{d}" fill="{fill}"/>'
    if shade_d:
        s += f'<path d="{shade_d}" fill="#000" opacity=".16" clip-path="url(#{i})"/>'
    if hl_d:
        s += f'<path d="{hl_d}" fill="#fff" opacity=".22" clip-path="url(#{i})"/>'
    s += extra
    s += f'<path d="{d}" fill="none" stroke="{INK}" stroke-width="{lw}" stroke-linejoin="round"/>'
    return s


def line(d, w=LW2, col=INK, op=1):
    return f'<path d="{d}" fill="none" stroke="{col}" stroke-width="{w}" stroke-linecap="round" stroke-linejoin="round" opacity="{op}"/>'


def ell(cx, cy, rx, ry):
    return f'M{cx - rx} {cy} A{rx} {ry} 0 1 0 {cx + rx} {cy} A{rx} {ry} 0 1 0 {cx - rx} {cy} Z'


# ------------------------------------------------------------------ head (pivot = neck)
HC = (0, -185)          # head centre relative to the neck
HRX, HRY = 192, 184


def head_base():
    d = ell(HC[0], HC[1], HRX, HRY)
    sh = f'M60 -380 C230 -330 250 -120 90 0 L400 0 L400 -400 Z'
    hl = ell(-95, -300, 55, 32)
    return shaded(d, 'var(--skin)', sh, hl)


def ear(side):
    x = side * 186
    d = ell(x, -170, 36, 46)
    inner = f'M{x + side * -2} -196 C{x + side * 22} -186 {x + side * 22} -152 {x + side * -2} -144'
    return shaded(d, 'var(--skin)', ell(x + side * 14, -160, 30, 44)) + line(inner, LW2, INK, .55)


# ---- eyes (left eye drawn at origin; caller mirrors / places)
def eye(kind):
    if kind == 'open':
        return f'<path d="{ell(0, 0, 16, 22)}" fill="{INK}"/><circle cx="-5" cy="-9" r="6" fill="#fff"/>'
    if kind == 'half':
        return (f'<path d="{ell(0, 4, 16, 18)}" fill="{INK}"/><circle cx="-5" cy="-1" r="5" fill="#fff"/>'
                f'<path d="M-26 -6 L26 -6 L26 -30 L-26 -30 Z" fill="var(--skin)"/>' + line('M-22 -5 Q0 -9 22 -5', 6))
    if kind == 'closed':
        return line('M-20 0 Q0 12 20 0', 7)
    if kind == 'happy':
        return line('M-20 6 Q0 -16 20 6', 7)
    if kind == 'wide':
        return (f'<path d="{ell(0, -2, 27, 31)}" fill="#fff" stroke="{INK}" stroke-width="6"/>'
                f'<circle cx="2" cy="2" r="9" fill="{INK}"/><circle cx="-1" cy="-2" r="3" fill="#fff"/>')
    if kind == 'stare':
        return (f'<path d="{ell(0, -2, 26, 27)}" fill="#fff" stroke="{INK}" stroke-width="6"/>'
                f'<circle cx="0" cy="0" r="4.5" fill="{INK}"/>' + line('M-18 22 Q0 28 18 22', 4, INK, .5))
    raise KeyError(kind)


EYES = ['open', 'half', 'closed', 'happy', 'wide', 'stare']


def brow(kind):
    # left brow; +x is towards the face centre
    return {
        'normal': line('M-24 2 Q0 -8 24 0', 9),
        'worried': line('M-24 6 Q2 0 24 -14', 9),
        'scared': line('M-24 0 Q4 -14 24 -22', 9),
        'angry': line('M-24 -14 Q0 -8 24 6', 9),
        'raised': line('M-24 2 Q0 -20 24 2', 9),
    }[kind]


BROWS = ['normal', 'worried', 'scared', 'angry', 'raised']

MOUTH_DARK = '#4a1a22'
TONGUE = '#e8848e'


def _open(d, tongue=None, teeth_top=None, teeth_bot=None):
    i = uid('m')
    s = f'<clipPath id="{i}"><path d="{d}"/></clipPath><path d="{d}" fill="{MOUTH_DARK}"/>'
    if tongue:
        s += f'<path d="{tongue}" fill="{TONGUE}" clip-path="url(#{i})"/>'
    if teeth_top:
        s += f'<path d="{teeth_top}" fill="#fff" clip-path="url(#{i})"/>'
    if teeth_bot:
        s += f'<path d="{teeth_bot}" fill="#fff" clip-path="url(#{i})"/>'
    return s + f'<path d="{d}" fill="none" stroke="{INK}" stroke-width="6" stroke-linejoin="round"/>'


def mouth(kind):
    m = {
        # Rhubarb Lip Sync shapes
        'X': lambda: line('M-24 0 Q0 7 24 0', 7),                                         # rest
        'A': lambda: line('M-26 2 Q0 -2 26 2', 9),                                        # M B P (closed, pressed)
        'B': lambda: _open('M-28 -6 Q0 -12 28 -6 Q26 12 0 14 Q-26 12 -28 -6 Z', None, 'M-40 -20 L40 -20 L40 -2 L-40 -2 Z'),
        'C': lambda: _open('M-30 -10 Q0 -16 30 -10 Q28 24 0 26 Q-28 24 -30 -10 Z', 'M-30 30 Q0 4 30 30 Z', 'M-40 -24 L40 -24 L40 -4 L-40 -4 Z'),
        'D': lambda: _open('M-32 -14 Q0 -20 32 -14 Q32 40 0 44 Q-32 40 -32 -14 Z', 'M-34 50 Q0 14 34 50 Z', 'M-40 -30 L40 -30 L40 -6 L-40 -6 Z'),
        'E': lambda: _open(ell(0, 6, 20, 26), 'M-24 40 Q0 18 24 40 Z'),
        'F': lambda: _open(ell(0, 4, 12, 13)),
        'G': lambda: _open('M-26 -4 Q0 -10 26 -4 Q24 14 0 15 Q-24 14 -26 -4 Z', None, 'M-40 -20 L40 -20 L40 4 L-40 4 Z'),
        'H': lambda: _open('M-28 -8 Q0 -14 28 -8 Q26 22 0 24 Q-26 22 -28 -8 Z', 'M-18 30 Q0 -10 18 30 Z', 'M-40 -24 L40 -24 L40 -6 L-40 -6 Z'),
        # expressions
        'smile': lambda: _open('M-34 -8 Q0 -4 34 -8 Q30 34 0 36 Q-30 34 -34 -8 Z', 'M-24 40 Q0 14 24 40 Z'),
        'smile_closed': lambda: line('M-30 -4 Q0 22 30 -4', 7),
        'frown': lambda: line('M-24 8 Q0 -8 24 8', 7),
        'o': lambda: _open(ell(0, 4, 13, 16)),
        'wavy': lambda: line('M-28 2 Q-21 -6 -14 2 T0 2 T14 2 T28 2', 6),
        'scream': lambda: _open('M-30 -16 Q0 -22 30 -16 Q36 60 0 66 Q-36 60 -30 -16 Z', 'M-26 70 Q0 40 26 70 Z', 'M-40 -30 L40 -30 L40 -8 L-40 -8 Z'),
    }
    return m[kind]()


RHUBARB = ['X', 'A', 'B', 'C', 'D', 'E', 'F', 'G', 'H']
MOUTHS = RHUBARB + ['smile', 'smile_closed', 'frown', 'o', 'wavy', 'scream']


def face(eyes='open', brows='normal', mouth_kind='X', look=0, sweat=False):
    cx, cy = HC[0] + look * 14, HC[1]
    s = ''
    for side in (-1, 1):
        ex = cx + side * 64
        tr = f'translate({ex} {cy + 12})' + (' scale(-1 1)' if side > 0 else '')
        s += f'<g transform="{tr}">{eye(eyes)}</g>'
        btr = f'translate({ex} {cy - 48 - (10 if brows in ("scared", "raised") else 0)})' + (' scale(-1 1)' if side > 0 else '')
        s += f'<g transform="{btr}">{brow(brows)}</g>'
    s += f'<g transform="translate({cx} {cy + 82})">{mouth(mouth_kind)}</g>'
    # cheeks
    for side in (-1, 1):
        s += f'<path d="{ell(cx + side * 118, cy + 56, 26, 14)}" fill="#ff7a8a" opacity=".18"/>'
    if sweat:
        s += f'<path d="M-150 -300 C-160 -280 -172 -262 -160 -250 C-150 -242 -136 -250 -140 -266 Z" fill="#8cc8f5" stroke="{INK}" stroke-width="4"/>'
    return s


# ---- hair (head frame)
def hair_back(kind):
    if kind == 'long':
        return shaded('M-205 -230 C-215 -100 -210 40 -150 70 L150 70 C210 40 215 -100 205 -230 Z', 'var(--hair)',
                      'M60 -260 L260 -260 L260 100 L60 100 Z')
    if kind == 'ponytail':
        return shaded('M150 -290 C260 -300 290 -160 250 -40 C232 10 200 30 190 0 C220 -80 210 -200 140 -240 Z', 'var(--hair)',
                      'M200 -300 L320 -300 L320 40 L200 40 Z')
    return ''


def hair_front(kind):
    if kind in ('none', '', None):
        return ''
    if kind == 'short':
        d = ('M-196 -175 C-210 -300 -120 -378 0 -376 C120 -378 210 -300 196 -175 C186 -200 170 -228 150 -240 '
             'C120 -246 90 -232 70 -250 C40 -236 0 -232 -30 -252 C-60 -236 -110 -240 -140 -232 C-170 -224 -186 -200 -196 -175 Z')
        return shaded(d, 'var(--hair)', 'M60 -400 L260 -400 L260 -150 L60 -150 Z', 'M-120 -350 C-60 -372 20 -372 40 -362 C-20 -352 -80 -340 -120 -330 Z')
    if kind in ('long', 'ponytail'):
        d = ('M-200 -150 C-214 -300 -120 -378 0 -376 C120 -378 214 -300 200 -150 C196 -190 180 -232 150 -250 '
             'C80 -240 20 -272 -10 -300 C-40 -260 -120 -246 -170 -236 C-188 -210 -196 -180 -200 -150 Z')
        return shaded(d, 'var(--hair)', 'M60 -400 L260 -400 L260 -120 L60 -120 Z', 'M-130 -340 C-60 -372 10 -372 40 -362 C-30 -350 -90 -336 -130 -322 Z')
    if kind == 'messy':
        d = ('M-196 -170 C-230 -260 -170 -330 -150 -340 C-160 -380 -90 -400 -60 -372 C-40 -410 40 -410 60 -372 '
             'C100 -400 170 -380 160 -330 C200 -320 230 -250 196 -170 C180 -226 150 -262 110 -266 C80 -280 40 -268 0 -290 '
             'C-40 -268 -80 -280 -110 -266 C-150 -262 -180 -226 -196 -170 Z')
        return shaded(d, 'var(--hair)', 'M60 -420 L260 -420 L260 -150 L60 -150 Z')
    raise KeyError(kind)


HAIRS = ['none', 'short', 'messy', 'ponytail', 'long']


# ------------------------------------------------------------------ torso (pivot = hip centre)
NECK_Y = -345
SHOULDER = (148, -300)


def torso(kind):
    body = ('M-72 -345 C-150 -350 -192 -334 -190 -282 C-188 -200 -180 -50 -178 -12 C-177 6 -166 14 -150 14 '
            'L150 14 C166 14 177 6 178 -12 C180 -50 188 -200 190 -282 C192 -334 150 -350 72 -345 Z')
    sh = 'M90 -360 C200 -330 200 -40 170 30 L260 30 L260 -360 Z'
    hl = 'M-150 -320 C-175 -250 -170 -120 -165 -60 L-140 -60 C-150 -150 -150 -260 -130 -320 Z'
    s = ''
    if kind == 'hoodie':
        s += shaded(body, 'var(--top)', sh, hl,
                    extra=f'<path d="M-170 -24 L170 -24 L172 14 L-172 14 Z" fill="#000" opacity=".12"/>')
        s += line('M-170 -26 L170 -26', LW2, INK, .7)
        s += shaded('M-78 -150 L78 -150 L102 -58 L-102 -58 Z', 'var(--top)', 'M0 -160 L120 -160 L120 -50 L0 -50 Z', lw=LW2)
        s += line('M-78 -150 L-60 -110 M78 -150 L60 -110', 4, INK, .5)
        # hood collar + inner shirt + drawstrings
        s += shaded('M-118 -350 C-112 -282 112 -282 118 -350 C84 -372 -84 -372 -118 -350 Z', 'var(--top)',
                    'M-130 -370 L130 -370 L130 -300 L-130 -300 Z')
        s += f'<path d="{ell(0, -342, 56, 18)}" fill="#f4f2ee" stroke="{INK}" stroke-width="{LW2}"/>'
        for side in (-1, 1):
            s += line(f'M{side * 30} -318 C{side * 34} -290 {side * 28} -270 {side * 32} -246', 6, '#f4f2ee')
            s += f'<rect x="{side * 32 - 5}" y="-250" width="10" height="16" rx="4" fill="#d9d4cc" stroke="{INK}" stroke-width="3"/>'
    elif kind == 'tshirt':
        s += shaded(body, 'var(--top)', sh, hl)
        s += f'<path d="{ell(0, -340, 60, 24)}" fill="var(--skin)" stroke="{INK}" stroke-width="{LW2}"/>'
        s += line('M-66 -332 Q0 -296 66 -332', 9, 'var(--top2)')
        s += line('M-64 -330 Q0 -300 64 -330', LW2, INK, .6)
    elif kind == 'jacket':
        s += shaded(body, 'var(--top)', sh, hl)
        s += shaded('M-46 -344 L46 -344 L40 14 L-40 14 Z', 'var(--top2)', 'M0 -350 L60 -350 L60 20 L0 20 Z', lw=LW2)
        for side in (-1, 1):
            s += shaded(f'M{side * 46} -346 L{side * 100} -340 L{side * 60} -230 L{side * 44} -270 Z', 'var(--top)',
                        'M-200 -400 L200 -400 L200 -200 L-200 -200 Z' if side > 0 else None, lw=LW2)
        s += line('M-44 -260 L-42 6 M44 -260 L42 6', 4, INK, .6)
        for y in (-200, -130, -60):
            s += f'<circle cx="-62" cy="{y}" r="5" fill="{INK}" opacity=".55"/>'
    else:
        raise KeyError(kind)
    return s


TORSOS = ['hoodie', 'tshirt', 'jacket']


# ------------------------------------------------------------------ arms (pivot shoulder / elbow / wrist)
UPPER, FORE = 150, 140


def arm_upper(sleeve='long'):
    if sleeve == 'short':
        s = shaded('M-40 -6 C-40 -40 40 -40 40 -6 L42 92 C30 102 -30 102 -42 92 Z', 'var(--top)', 'M8 -60 L80 -60 L80 120 L8 120 Z')
        s = shaded('M-25 80 L25 80 L23 160 C23 172 -23 172 -23 160 Z', 'var(--skin)', 'M6 60 L60 60 L60 180 L6 180 Z') + s
        return s
    return shaded('M-40 -6 C-40 -42 40 -42 40 -6 L35 152 C35 172 -35 172 -35 152 Z', 'var(--top)', 'M8 -60 L80 -60 L80 200 L8 200 Z')


def forearm(sleeve='long'):
    if sleeve == 'short':
        return shaded('M-24 -8 C-24 -24 24 -24 24 -8 L21 138 C21 150 -21 150 -21 138 Z', 'var(--skin)', 'M6 -30 L60 -30 L60 160 L6 160 Z')
    s = shaded('M-35 -10 C-35 -34 35 -34 35 -10 L30 128 C30 144 -30 144 -30 128 Z', 'var(--top)', 'M6 -40 L70 -40 L70 160 L6 160 Z')
    s += shaded('M-31 104 L31 104 L31 132 C31 146 -31 146 -31 132 Z', 'var(--top)', 'M-40 100 L40 100 L40 150 L-40 150 Z', lw=LW2)
    return s


def hand(kind):
    if kind == 'open':
        return shaded(ell(0, 34, 36, 38), 'var(--skin)', ell(18, 44, 30, 38)) + \
            shaded(ell(30, 18, 13, 20), 'var(--skin)', None, lw=LW2)
    if kind == 'fist':
        return shaded(ell(0, 30, 34, 33), 'var(--skin)', ell(18, 40, 28, 34)) + line('M-14 50 Q-6 56 2 50 M4 52 Q12 58 20 50', 4, INK, .6)
    if kind == 'point':
        return shaded('M-10 40 L10 40 L11 108 C11 120 -11 120 -11 108 Z', 'var(--skin)', None, lw=LW2 + 1) + \
            shaded(ell(0, 30, 34, 32), 'var(--skin)', ell(18, 40, 28, 34))
    if kind == 'hold':
        s = shaded(ell(0, 32, 35, 36), 'var(--skin)', ell(18, 42, 28, 36))
        return s + line('M-22 40 Q0 58 22 40', 5, INK, .7) + shaded(ell(-28, 24, 12, 18), 'var(--skin)', None, lw=LW2)
    raise KeyError(kind)


HANDS = ['open', 'fist', 'point', 'hold']


# ------------------------------------------------------------------ legs (pivot hip joint / knee / ankle)
THIGH, SHIN = 150, 132


def thigh():
    return shaded('M-50 -30 L50 -30 L46 150 C46 166 -46 166 -46 150 Z', 'var(--pants)', 'M10 -40 L80 -40 L80 180 L10 180 Z')


def shin():
    return shaded('M-46 -10 L46 -10 L45 128 C45 140 -45 140 -45 128 Z', 'var(--pants)', 'M10 -20 L80 -20 L80 160 L10 160 Z')


def shoe():
    d = 'M-62 50 C-64 6 -34 -12 0 -12 C34 -12 64 6 62 50 Z'
    s = shaded(d, 'var(--shoe)', 'M14 -20 L80 -20 L80 60 L14 60 Z', ell(-24, 6, 18, 9))
    s += shaded('M-64 38 L64 38 L64 56 C64 60 -64 60 -64 56 Z', 'var(--shoe)', None, 'M-80 30 L80 30 L80 50 L-80 50 Z', lw=LW2)
    return s


# ------------------------------------------------------------------ props
def phone():
    return (f'<rect x="-26" y="-6" width="52" height="88" rx="10" fill="#22252c" stroke="{INK}" stroke-width="6"/>'
            f'<rect x="-19" y="2" width="38" height="66" rx="5" fill="#9fd4ff"/>')


def flashlight():
    return (f'<rect x="-14" y="-10" width="28" height="70" rx="6" fill="#4b5160" stroke="{INK}" stroke-width="6"/>'
            f'<rect x="-20" y="56" width="40" height="22" rx="5" fill="#6b7280" stroke="{INK}" stroke-width="6"/>')


# ------------------------------------------------------------------ assembly
HIP_X = 72      # leg joints either side of the hip centre
FOOT_GROUND = THIGH + SHIN + 55


def ik(sx, sy, tx, ty, l1, l2, bend):
    """2-bone IK. Returns absolute angles (degrees, 0 = hanging down, clockwise positive) of upper and lower."""
    dx, dy = tx - sx, ty - sy
    d = min(max(math.hypot(dx, dy), 1e-3), l1 + l2 - 1e-3)
    a = math.atan2(dy, dx)
    c = (l1 * l1 + d * d - l2 * l2) / (2 * l1 * d)
    b = math.acos(max(-1, min(1, c)))
    a1 = a + bend * b
    ex, ey = sx + l1 * math.cos(a1), sy + l1 * math.sin(a1)
    a2 = math.atan2(ty - ey, tx - ex)
    to_deg = lambda r: math.degrees(r) - 90           # svg: direction (0,1) is 0
    return to_deg(a1), to_deg(a2)


def g(tr, inner):
    return f'<g transform="{tr}">{inner}</g>'


def character(c, pose):
    """c: look dict; pose: dict with absolute angles or targets."""
    sleeve = 'short' if c['top'] == 'tshirt' else 'long'
    head = (''.join(ear(s) for s in (-1, 1)) + head_base()
            + face(pose.get('eyes', 'open'), pose.get('brows', 'normal'), pose.get('mouth', 'X'), pose.get('look', 0), pose.get('sweat', False))
            + hair_front(c['hair']))

    def leg(side, a_thigh, a_shin):
        return g(f'translate({side * HIP_X} 0) rotate({a_thigh})',
                 thigh() + g(f'translate(0 {THIGH}) rotate({a_shin - a_thigh})',
                              shin() + g(f'translate(0 {SHIN}) rotate({-a_shin})', shoe())))

    def arm(side, a_up, a_lo, hand_kind, prop=None):
        hp = hand(hand_kind)
        if prop:
            hp = g('translate(0 40)', prop) + hp
        h = g(f'scale({-side} 1)', hp) if side > 0 else hp
        return g(f'translate({side * SHOULDER[0]} {SHOULDER[1]}) rotate({a_up})',
                 arm_upper(sleeve) + g(f'translate(0 {UPPER}) rotate({a_lo - a_up})',
                                        forearm(sleeve) + g(f'translate(0 {FORE - 4}) rotate({pose.get("wrist_" + ("R" if side > 0 else "L"), 0)})', h)))

    legs = pose.get('legs', (4, 2, -4, -2))
    arms = {}
    for side, key in ((-1, 'L'), (1, 'R')):
        spec = pose.get('arm' + key, ('angles', side * -10, side * -6))
        if spec[0] == 'target':
            sx, sy = side * SHOULDER[0], SHOULDER[1]
            a1, a2 = ik(sx, sy, spec[1], spec[2], UPPER, FORE, spec[3] if len(spec) > 3 else side)
        else:
            a1, a2 = spec[1], spec[2]
        arms[key] = (a1, a2)
    hands = pose.get('hands', ('open', 'open'))
    props = pose.get('props', (None, None))
    lean = pose.get('lean', 0)
    tilt = pose.get('tilt', 0)
    head_tr = f'translate(0 {NECK_Y + 10}) rotate({tilt})'
    body = (g(f'rotate({lean})', g(head_tr, hair_back(c['hair'])))      # long hair hangs behind the body
            + leg(-1, legs[0], legs[1]) + leg(1, legs[2], legs[3])
            + g(f'rotate({lean})', torso(c['top'])
                + g(head_tr, head)
                + arm(-1, arms['L'][0], arms['L'][1], hands[0], props[0]) + arm(1, arms['R'][0], arms['R'][1], hands[1], props[1])))
    style = ';'.join(f'--{k}:{v}' for k, v in c['colors'].items())
    shadow = f'<ellipse cx="0" cy="{FOOT_GROUND - 2}" rx="230" ry="26" fill="#000" opacity=".22"/>'
    return f'<g style="{style}">{shadow}{body}</g>'


# ------------------------------------------------------------------ cast + poses for the preview
CAST = {
    'Mẫu (ảnh của bạn)': dict(top='hoodie', hair='none', colors=dict(skin='#ffffff', top='#4a86d9', top2='#f4f2ee', pants='#8f949c', shoe='#7d828a', hair='#2b1e17')),
    'Mia': dict(top='hoodie', hair='ponytail', colors=dict(skin='#f6dcc4', top='#b23b48', top2='#f4f2ee', pants='#2f3a4f', shoe='#2b2f36', hair='#5a3420')),
    'Dale': dict(top='jacket', hair='short', colors=dict(skin='#eac8a6', top='#6b4a2e', top2='#c9c2b2', pants='#4a4a3a', shoe='#3a2a20', hair='#9a9a9a')),
    'Josh': dict(top='tshirt', hair='messy', colors=dict(skin='#c69472', top='#3c8f5a', top2='#2f7148', pants='#2a3344', shoe='#e9e6e0', hair='#1d1612')),
    'Emma': dict(top='hoodie', hair='long', colors=dict(skin='#f3d9c8', top='#7d5ba6', top2='#f4f2ee', pants='#3a3550', shoe='#24222a', hair='#2b1e17')),
}

POSES = {
    'idle': dict(eyes='open', mouth='smile', armL=('angles', 10, 6), armR=('angles', -10, -6)),
    'wave': dict(eyes='happy', brows='raised', mouth='smile', armL=('angles', 10, 6), armR=('angles', -160, -185), wrist_R=0),
    'talk': dict(eyes='open', mouth='C', armL=('angles', 10, 6), armR=('angles', -30, -100), hands=('open', 'open')),
    'point': dict(eyes='open', brows='angry', mouth='o', look=1, armL=('angles', 10, 6), armR=('angles', -90, -92), hands=('open', 'point')),
    'phone': dict(eyes='half', brows='worried', mouth='frown', look=0.3, armL=('angles', 12, 6), armR=('target', 10, -150, 1), wrist_R=160, hands=('open', 'hold'), props=(None, 'phone')),
    'scared': dict(eyes='wide', brows='scared', mouth='wavy', sweat=True, armL=('target', -168, -455, -1), armR=('target', 168, -455, 1), hands=('open', 'open'), legs=(8, 4, -8, -4)),
    'terrified': dict(eyes='stare', brows='scared', mouth='scream', sweat=True, armL=('angles', 150, 175), armR=('angles', -150, -175), hands=('open', 'open'), legs=(10, 6, -10, -6), tilt=-4),
    'hug_self': dict(eyes='half', brows='worried', mouth='wavy', armL=('target', 70, -230, 1), armR=('target', -70, -200, -1), hands=('fist', 'fist')),
    'flashlight': dict(eyes='wide', brows='worried', mouth='o', look=1, armL=('angles', 10, 6), armR=('angles', -75, -80), hands=('open', 'hold'), props=(None, 'flashlight')),
    'cover_mouth': dict(eyes='wide', brows='scared', mouth='X', sweat=True, armL=('angles', 12, 6), armR=('target', 20, -400, 1), wrist_R=180, hands=('open', 'open')),
}
PROPS = {'phone': phone(), 'flashlight': flashlight()}
for p in POSES.values():
    if 'props' in p:
        p['props'] = tuple(PROPS[x] if x else None for x in p['props'])
