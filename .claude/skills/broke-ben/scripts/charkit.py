"""CharKit: polished mascot sprites (smooth Bezier shapes, two-tone cel shading, sticker outline).

Each character is drawn once on its own small canvas and returned as an RGBA sprite,
so scenes, avatars and banners all reuse exactly the same artwork.
Light comes from the top-right; shadows sit bottom-left.
"""
import math
from PIL import Image, ImageChops, ImageDraw, ImageFilter
from flatkit import Pen

OUTLINE = (43, 34, 51, 255)


# ---------------------------------------------------------------- geometry
def bez(p0, p1, p2, p3, n=22):
    out = []
    for i in range(n + 1):
        t = i / n
        a, b, c, d = (1 - t) ** 3, 3 * (1 - t) ** 2 * t, 3 * (1 - t) * t ** 2, t ** 3
        out.append((a * p0[0] + b * p1[0] + c * p2[0] + d * p3[0], a * p0[1] + b * p1[1] + c * p2[1] + d * p3[1]))
    return out


def path(start, segs, n=22):
    """segs: list of (c1, c2, end) cubic segments."""
    pts, cur = [start], start
    for c1, c2, e in segs:
        pts += bez(cur, c1, c2, e, n)[1:]
        cur = e
    return pts


# ---------------------------------------------------------------- sprite canvas
class Sprite:
    def __init__(self, w, h, scale=1):
        self.pen = Pen(w, h, 2 * scale)
        self.w, self.h, self.S, self.scale = w, h, 2 * scale, scale

    def part(self, base, shade=None, outline=7):
        """base(pen) draws the flat shape; shade(pen) is clipped to it; outline is a sticker rim."""
        L = self.pen.layer()
        base(L)
        if shade:
            T = self.pen.layer()
            shade(T)
            a = ImageChops.multiply(T.img.getchannel('A'), L.img.getchannel('A'))
            T.img.putalpha(a)
            L.img.alpha_composite(T.img)
        if outline:
            r = outline * self.S
            a = L.img.getchannel('A').filter(ImageFilter.GaussianBlur(r * 0.55))
            a = a.point(lambda v: 255 if v > 18 else 0).filter(ImageFilter.GaussianBlur(1.2))
            o = Image.new('RGBA', L.img.size, OUTLINE)
            o.putalpha(a)
            self.pen.img.alpha_composite(o)
        self.pen.img.alpha_composite(L.img)
        self.pen.d = ImageDraw.Draw(self.pen.img)

    def done(self):
        return self.pen.img.resize((self.w * self.scale, self.h * self.scale), Image.LANCZOS)


def eye(p, x, y, rx=21, ry=29, look=(0, 0)):
    p.ellipse((x - rx, y - ry, x + rx, y + ry), OUTLINE)
    hx, hy = x + look[0] * 4, y + look[1] * 4
    p.circle(hx + rx * 0.33, hy - ry * 0.38, rx * 0.38, (255, 255, 255))
    p.circle(hx - rx * 0.3, hy + ry * 0.38, rx * 0.17, (255, 255, 255))


def closed_eye(p, x, y, rx=21):
    p.arc((x - rx, y - rx * 0.6, x + rx, y + rx * 0.9), 200, 340, 8, OUTLINE)


def mouth(sp, cx, cy, w, h, mood, open_):
    """mood smile/shock; open_=False gives the closed frame used between syllables."""
    p = sp.pen
    if mood == 'shock':
        k = 1.0 if open_ else 0.55
        sp.part(lambda q: q.ellipse((cx - w * 0.45, cy + 2, cx + w * 0.45, cy + 2 + h * 1.25 * k), (107, 34, 48)),
                outline=4)
    elif open_:
        open_smile(sp, cx, cy, w, h)
    else:
        p.arc((cx - w * 0.8, cy - h * 0.9, cx + w * 0.8, cy + h * 0.6), 25, 155, 8, OUTLINE)


def brow(p, a, b, w=12):
    p.line([a, ((a[0] + b[0]) / 2, min(a[1], b[1]) - 6), b], w, OUTLINE)


def open_smile(sp, cx, cy, w, h):
    """Open mouth with teeth and tongue, clipped and outlined."""
    def base(p):
        p.chord((cx - w, cy - h, cx + w, cy + h), 0, 180, (107, 34, 48))

    def shade(p):
        p.rect((cx - w, cy - 2, cx + w, cy + h * 0.3), (255, 255, 255))
        p.ellipse((cx - w * 0.55, cy + h * 0.45, cx + w * 0.55, cy + h * 1.25), (255, 122, 138))
    sp.part(base, shade, outline=4)


# ================================================================ A. Ben (young adult, v3)
SKIN, SKIN_SH, BLUSH = (255, 217, 184), (238, 184, 148), (255, 140, 125, 45)
HAIR, HAIR_HI, HAIR_SH = (75, 46, 34), (120, 78, 56), (60, 36, 27)
HOOD, HOOD_SH, HOOD_HI = (63, 163, 107), (44, 128, 82), (110, 200, 145)
PANTS, PANTS_SH = (44, 58, 94), (32, 42, 70)
LANYARD, BADGE, BADGE_STRIPE = (40, 90, 160), (250, 250, 247), (46, 139, 87)
CASH, CASH_DK = (126, 190, 120), (70, 130, 70)

BEN_POSES = ['idle', 'wave', 'point', 'hold_head', 'cross_arms', 'phone', 'read', 'count_money', 'shrug',
             'think', 'celebrate', 'thumbs_up', 'facepalm', 'explain', 'sad',
             'sit_desk', 'empty_pockets', 'credit_card', 'shopping_bags', 'coffee', 'calculator', 'beg',
             'throw_money', 'hug_piggy', 'present']
BEN_MOODS = ['smile', 'shock', 'sad', 'worried', 'angry', 'smug', 'money_eyes', 'tired', 'cry']

# arms: (shoulder, elbow, hand, hand_style) for the picture-left (L) and picture-right (R) arm
_SL, _SR = (222, 378), (378, 378)
_IDLE_L, _IDLE_R = (_SL, (198, 482), (206, 578), 'fist'), (_SR, (402, 482), (394, 578), 'fist')
ARMS = {
    'idle':        (_IDLE_L, _IDLE_R),
    'wave':        (_IDLE_L, (_SR, (468, 330), (498, 238), 'open')),
    'point':       (_IDLE_L, (_SR, (468, 404), (556, 388), 'point')),
    'hold_head':   ((_SL, (150, 300), (194, 196), 'open'), (_SR, (450, 300), (406, 196), 'open')),
    'cross_arms':  ((_SL, (214, 500), (350, 466), 'fist'), (_SR, (386, 500), (250, 466), 'fist')),
    'phone':       (_IDLE_L, (_SR, (404, 504), (330, 438), 'phone')),
    'read':        ((_SL, (214, 500), (246, 450), 'fist'), (_SR, (386, 500), (354, 450), 'fist')),
    'count_money': ((_SL, (212, 500), (256, 456), 'cash'), (_SR, (392, 492), (338, 452), 'fist')),
    'shrug':       ((_SL, (160, 430), (128, 352), 'open'), (_SR, (440, 430), (472, 352), 'open')),
    'think':       ((_SL, (226, 500), (330, 500), 'fist'), (_SR, (392, 470), (332, 330), 'fist')),
    'celebrate':   ((_SL, (160, 280), (140, 182), 'fist'), (_SR, (440, 280), (460, 182), 'fist')),
    'thumbs_up':   (_IDLE_L, (_SR, (432, 470), (442, 392), 'thumb')),
    'facepalm':    (_IDLE_L, (_SR, (424, 420), (330, 214), 'open')),
    'explain':     ((_SL, (168, 470), (128, 418), 'open'), (_SR, (432, 470), (472, 418), 'open')),
    'sad':         ((_SL, (214, 482), (232, 578), 'fist'), (_SR, (386, 482), (368, 578), 'fist')),
    # money-life poses
    'sit_desk':      ((_SL, (198, 480), (206, 560), 'fist'), (_SR, (402, 480), (394, 560), 'fist')),
    'empty_pockets': ((_SL, (172, 470), (142, 524), 'open'), (_SR, (428, 470), (458, 524), 'open')),
    'credit_card':   (_IDLE_L, (_SR, (462, 420), (540, 402), 'card')),
    'shopping_bags': ((_SL, (190, 482), (180, 590), 'bag'), (_SR, (410, 482), (420, 590), 'bag2')),
    'coffee':        (_IDLE_L, (_SR, (404, 504), (338, 452), 'cup')),
    'calculator':    ((_SL, (214, 506), (250, 474), 'fist'), (_SR, (386, 506), (350, 474), 'fist')),
    'beg':           ((_SL, (226, 504), (290, 432), 'fist'), (_SR, (374, 504), (310, 432), 'fist')),
    'throw_money':   (_IDLE_L, (_SR, (452, 300), (486, 214), 'cash')),
    'hug_piggy':     ((_SL, (204, 500), (238, 528), 'fist'), (_SR, (396, 500), (362, 528), 'fist')),
    'present':       (_IDLE_L, (_SR, (450, 440), (500, 462), 'pointer')),
}
# arms crossing the body are drawn over the torso; the facepalm hand goes over the face
_OVER_FACE = {'hold_head', 'facepalm', 'think'}


def _H(x, y):
    """Map the v2 head artwork (centre 300,255) onto the smaller adult head (centre 300,200)."""
    return (300 + (x - 300) * 0.8, 200 + (y - 255) * 0.8)


def _Hp(pts):
    return [_H(x, y) for x, y in pts]


def _hand(sp, hx, hy, style):
    if style == 'point':
        sp.part(lambda q: (q.circle(hx, hy, 22, SKIN), q.rect((hx, hy - 11, hx + 38, hy + 2), SKIN, r=7)), outline=6)
    elif style == 'thumb':
        sp.part(lambda q: (q.ellipse((hx - 22, hy - 18, hx + 22, hy + 22), SKIN),
                           q.rect((hx - 6, hy - 46, hx + 8, hy - 8), SKIN, r=7)), outline=6)
    elif style == 'open':
        sp.part(lambda q: (q.ellipse((hx - 25, hy - 22, hx + 25, hy + 22), SKIN),
                           q.ellipse((hx - 30, hy - 6, hx - 14, hy + 10), SKIN)), outline=6)
    elif style == 'phone':
        sp.part(lambda q: q.rect((hx - 30, hy - 66, hx + 18, hy + 14), (35, 40, 52), r=8), outline=5)
        sp.pen.rect((hx - 25, hy - 60, hx + 13, hy + 6), (150, 215, 255), r=5)
        sp.part(lambda q: q.circle(hx, hy + 8, 21, SKIN), outline=6)
    elif style == 'card':
        lay = sp.pen.layer()
        lay.rect((hx - 6, hy - 40, hx + 74, hy + 10), (40, 70, 140), OUTLINE, 4, r=8)
        lay.rect((hx + 2, hy - 30, hx + 22, hy - 16), (230, 190, 90), r=3)
        lay.line([(hx + 4, hy - 4), (hx + 64, hy - 4)], 4, (200, 210, 230), caps=False)
        sp.pen.paste(lay, rotate=-8, center=(hx, hy))
        sp.part(lambda q: q.circle(hx, hy, 22, SKIN), outline=6)
    elif style in ('bag', 'bag2'):
        col = (214, 69, 69) if style == 'bag' else (226, 160, 58)
        sp.part(lambda q: q.arc((hx - 22, hy - 10, hx + 22, hy + 40), 180, 360, 6, (90, 70, 60)), outline=0)
        sp.part(lambda q: q.rect((hx - 46, hy + 16, hx + 46, hy + 120), col, r=8),
                lambda q: q.rect((hx - 46, hy + 16, hx - 26, hy + 120), tuple(int(c * 0.8) for c in col)), outline=6)
        sp.part(lambda q: q.circle(hx, hy, 22, SKIN), outline=6)
    elif style == 'cup':
        sp.part(lambda q: q.poly([(hx - 30, hy - 70), (hx + 18, hy - 70), (hx + 12, hy + 4), (hx - 24, hy + 4)],
                                 (250, 248, 240)),
                lambda q: q.rect((hx - 30, hy - 48, hx + 18, hy - 22), (120, 80, 50)), outline=5)
        sp.part(lambda q: q.rect((hx - 34, hy - 82, hx + 22, hy - 68), (240, 236, 226), r=4), outline=4)
        for k in range(2):
            sp.pen.line([(hx - 14 + k * 14, hy - 92), (hx - 20 + k * 14, hy - 108), (hx - 12 + k * 14, hy - 124)],
                        4, (200, 196, 190))
        sp.part(lambda q: q.circle(hx, hy, 21, SKIN), outline=6)
    elif style == 'pointer':
        sp.part(lambda q: q.line([(hx, hy), (594, 300)], 9, (120, 82, 50)), outline=4)
        sp.pen.circle(594, 300, 6, (214, 69, 69))
        sp.part(lambda q: q.circle(hx, hy, 22, SKIN), outline=6)
    elif style == 'cash':
        for k, ang in enumerate((-28, -10, 8)):
            lay = sp.pen.layer()
            lay.rect((hx - 34, hy - 118, hx + 34, hy - 6), CASH, CASH_DK, 4, r=4)
            lay.circle(hx, hy - 62, 15, None, CASH_DK, 3)
            sp.pen.paste(lay, rotate=ang, center=(hx, hy))
        sp.part(lambda q: q.circle(hx, hy, 22, SKIN), outline=6)
    else:
        sp.part(lambda q: q.circle(hx, hy, 22, SKIN), outline=6)


def _arm(sp, arm):
    a, b, c, style = arm
    sp.part(lambda q: q.line([a, b, c], 44, HOOD),
            lambda q: q.line([(a[0] - 14, a[1] + 6), (b[0] - 14, b[1] + 4), (c[0] - 12, c[1])], 18, HOOD_SH),
            outline=6)
    _hand(sp, c[0], c[1], style)


def _face(sp, pose, mood, blink, talk):
    p = sp.pen
    look = {'point': (1, 0), 'phone': (0, 1.2), 'read': (0, 1.2), 'count_money': (0, 1), 'think': (1, -1),
            'sad': (0, 1), 'sit_desk': (0, 0.8), 'calculator': (0, 1.2), 'coffee': (0, 0.4),
            'credit_card': (1, 0), 'present': (1, 0), 'hug_piggy': (0, 1)}.get(pose, (0, 0))
    ex = (_H(246, 0)[0], _H(354, 0)[0])
    ey = _H(0, 290)[1]
    for i, x in enumerate(ex):
        if blink:
            closed_eye(p, x, ey, 17)
        elif mood == 'money_eyes':
            p.text((x, ey + 2), '$', 'display', 56, (46, 139, 87), anchor='mm', stroke=3, stroke_fill=OUTLINE)
        elif mood == 'tired':
            eye(p, x, ey, 17, 23, (0, 0.6))
            p.chord((x - 19, ey - 26, x + 19, ey + 4), 180, 360, SKIN)
            p.line([(x - 18, ey), (x + 18, ey)], 6, OUTLINE)
            p.arc((x - 16, ey + 14, x + 16, ey + 30), 20, 160, 4, SKIN_SH)
        elif mood == 'cry':
            p.arc((x - 17, ey - 10, x + 17, ey + 14), 200, 340, 7, OUTLINE)
        elif mood == 'smug':
            eye(p, x, ey, 17, 23, look)
            p.chord((x - 19, ey - 26, x + 19, ey + 2), 180, 360, SKIN)
            p.line([(x - 18, ey - 4), (x + 18, ey - 4)], 6, OUTLINE)
        else:
            eye(p, x, ey, 17, 23, look)
    by = ey - 42
    if mood == 'shock':
        brows = [((ex[0] - 24, by - 8), (ex[0] + 22, by - 10)), ((ex[1] - 22, by - 10), (ex[1] + 24, by - 8))]
    elif mood in ('sad', 'worried', 'cry', 'tired'):
        brows = [((ex[0] - 24, by + 6), (ex[0] + 20, by - 6)), ((ex[1] - 20, by - 6), (ex[1] + 24, by + 6))]
    elif mood == 'angry':
        brows = [((ex[0] - 24, by - 6), (ex[0] + 20, by + 8)), ((ex[1] - 20, by + 8), (ex[1] + 24, by - 6))]
    else:
        brows = [((ex[0] - 22, by + 2), (ex[0] + 22, by - 2)), ((ex[1] - 22, by - 2), (ex[1] + 22, by + 2))]
    for a, b in brows:
        p.line([a, b], 9, OUTLINE)
    blush = p.layer()
    for x in (_H(214, 0)[0], _H(386, 0)[0]):
        blush.ellipse((x - 20, ey + 34, x + 20, ey + 46), BLUSH)
    p.paste(blush, blur=3)
    nx, ny = _H(300, 312)
    p.arc((nx - 8, ny - 9, nx + 8, ny + 9), 20, 160, 4, SKIN_SH)
    mx, my = _H(300, 342)
    if mood == 'cry':                                   # tear streams
        tears = p.layer()
        for x in ex:
            tears.line([(x - 4, ey + 12), (x - 8, ey + 60), (x - 4, ey + 86)], 9, (120, 190, 255, 220))
        p.paste(tears)
    if mood == 'cry':
        sp.part(lambda q: q.chord((mx - 24, my - 4, mx + 24, my + 34), 180, 360, (107, 34, 48)), outline=4)
    elif mood == 'tired':
        p.line([(mx - 16, my + 12), (mx + 16, my + 10)], 6, OUTLINE)
    elif mood == 'money_eyes':
        mouth(sp, mx, my, 30, 26, 'smile', True)
    elif mood == 'shock':
        mouth(sp, mx, my, 30, 26, 'shock', talk)
    elif mood in ('sad', 'worried'):
        if talk:
            sp.part(lambda q: q.chord((mx - 16, my + 2, mx + 16, my + 26), 180, 360, (107, 34, 48)), outline=4)
        elif mood == 'sad':
            p.arc((mx - 22, my + 4, mx + 22, my + 30), 200, 340, 6, OUTLINE)
        else:
            p.line([(mx - 20 + 8 * k, my + 10 + (4 if k % 2 else -4)) for k in range(6)], 5, OUTLINE)
    elif mood == 'angry':
        if talk:
            sp.part(lambda q: q.rect((mx - 22, my, mx + 22, my + 20), (255, 255, 255), r=6), outline=4)
            p.line([(mx - 20, my + 10), (mx + 20, my + 10)], 3, (190, 180, 180))
        else:
            p.line([(mx - 18, my + 10), (mx + 18, my + 8)], 6, OUTLINE)
    elif mood == 'smug':
        p.arc((mx - 10, my - 16, mx + 30, my + 14), 20, 140, 6, OUTLINE)
    else:
        mouth(sp, mx, my, 30, 26, 'smile', talk)


def _hair_messy(sp):
    """Short, textured modern cut: soft bumps on top and a choppy fringe."""
    cx, cy = 300, 255
    pts = []
    for i in range(61):
        th = math.radians(196 + 148 * i / 60)
        r = 168 + 20 * abs(math.sin(i / 60 * math.pi * 5.5))
        pts.append((cx + r * math.cos(th), cy + r * 1.02 * math.sin(th)))
    fringe = [(458, 250), (430, 214), (408, 236), (382, 196), (352, 222), (322, 186), (292, 216), (262, 184),
              (232, 220), (206, 196), (184, 236), (150, 252)]
    hair = _Hp(pts + fringe)

    def shade(q):
        q.poly(_Hp([(300, 96), (390, 104), (440, 150), (446, 190), (396, 150), (320, 124)]), HAIR_HI)
        q.ellipse((*_H(118, 190), *_H(210, 300)), HAIR_SH)
    sp.part(lambda q: q.poly(hair, HAIR), shade, outline=7)


def _pose_props(sp, pose):
    """Objects in front of Ben that belong to a pose (drawn after the arms)."""
    p = sp.pen
    if pose == 'sit_desk':
        sp.part(lambda q: q.rect((40, 556, 560, 940), (176, 125, 83)),
                lambda q: (q.rect((40, 556, 560, 584), (200, 146, 100)), q.rect((40, 584, 560, 600), (140, 98, 64))),
                outline=7)
        sp.part(lambda q: q.poly([(222, 430), (378, 430), (390, 556), (210, 556)], (170, 176, 186)),
                lambda q: q.poly([(222, 430), (300, 430), (290, 556), (210, 556)], (150, 156, 168)), outline=6)
        p.circle(300, 492, 14, (226, 230, 236))
        for hx in (206, 394):
            sp.part(lambda q, hx=hx: q.circle(hx, 560, 22, SKIN), outline=6)
    elif pose == 'calculator':
        sp.part(lambda q: q.rect((248, 392, 352, 520), (52, 58, 70), r=10), outline=6)
        p.rect((260, 404, 340, 432), (190, 220, 170), r=4)
        p.text((334, 418), '$33', 'semi', 22, (40, 60, 40), anchor='rm')
        for r_ in range(3):
            for c in range(4):
                p.rect((260 + c * 20, 444 + r_ * 24, 274 + c * 20, 460 + r_ * 24),
                       (214, 69, 69) if (r_, c) == (2, 3) else (200, 204, 212), r=3)
        for hx in (250, 350):
            sp.part(lambda q, hx=hx: q.circle(hx, 474, 22, SKIN), outline=6)
    elif pose == 'hug_piggy':
        pig = piggy('smile', scale=1)
        pig = pig.crop(pig.getbbox())
        k = 190 / pig.width
        pig = pig.resize((190, int(pig.height * k)), Image.LANCZOS)
        S = p.S
        big = pig.resize((pig.width * S, pig.height * S), Image.LANCZOS)
        p.img.alpha_composite(big, (int((300 - pig.width / 2) * S), int((548 - pig.height) * S)))
        p.d = ImageDraw.Draw(p.img)
        for hx in (238, 362):
            sp.part(lambda q, hx=hx: q.circle(hx, 528, 22, SKIN), outline=6)
    elif pose == 'throw_money':
        for k, (bx, by, ang) in enumerate([(560, 120, 30), (420, 90, -20), (540, 260, 60), (380, 170, 10)]):
            lay = p.layer()
            lay.rect((bx - 30, by - 16, bx + 30, by + 16), CASH, CASH_DK, 4, r=3)
            lay.circle(bx, by, 8, None, CASH_DK, 3)
            p.paste(lay, rotate=ang, center=(bx, by))


def ben(pose='idle', mood='smile', scale=1, blink=False, talk=True):
    """Young-adult Ben (about 3.5 heads tall): messy modern hair, green hoodie with a work ID badge on a lanyard,
    navy jeans, white sneakers."""
    pose = pose if pose in ARMS else 'idle'
    mood = mood if mood in BEN_MOODS else 'smile'
    sp = Sprite(600, 940, scale)
    p = sp.pen
    lay = p.layer()                                   # ground shadow
    lay.ellipse((180, 846, 420, 882), (0, 0, 0, 60))
    p.paste(lay, blur=4)

    # legs + sneakers
    for x in (263, 337):
        sp.part(lambda q, x=x: q.rect((x - 32, 590, x + 32, 836), PANTS, r=22),
                lambda q, x=x: q.rect((x - 32, 590, x - 8, 836), PANTS_SH), outline=6)
    for x, s in ((256, -1), (344, 1)):
        sp.part(lambda q, x=x, s=s: q.ellipse((x - 48 + s * 8, 814, x + 48 + s * 8, 864), (246, 246, 240)),
                lambda q, x=x, s=s: (q.rect((x - 60, 846, x + 60, 870), (205, 205, 198)),
                                     q.line([(x - 28 + s * 8, 830), (x + 22 + s * 8, 830)], 7, HOOD)), outline=6)

    # hoodie torso
    body = path((214, 362), [((250, 344), (350, 344), (386, 362)), ((406, 430), (402, 530), (398, 604)),
                             ((360, 616), (240, 616), (202, 604)), ((198, 530), (194, 430), (214, 362))])

    def body_shade(q):
        q.ellipse((120, 400, 290, 700), HOOD_SH)
        q.rect((150, 578, 450, 640), HOOD_SH)
        q.ellipse((334, 372, 400, 420), HOOD_HI + (160,))
    sp.part(lambda q: q.poly(body, HOOD), body_shade, outline=7)
    pocket = [(250, 520), (350, 520), (360, 576), (240, 576)]
    p.poly(pocket, HOOD_SH)
    p.line(pocket + [pocket[0]], 4, (34, 100, 64))
    # collar + strings
    p.ellipse((240, 340, 360, 378), HOOD_SH, OUTLINE, 5)
    sp.part(lambda q: q.rect((280, 300, 320, 352), SKIN), lambda q: q.rect((280, 300, 320, 318), SKIN_SH), outline=5)
    for x0, x1 in ((286, 282), (314, 318)):
        p.line([(x0, 372), (x1, 420)], 5, (250, 250, 245))
    # work ID badge on a lanyard ("a guy with a paycheck")
    p.line([(272, 352), (296, 470)], 7, LANYARD)
    p.line([(328, 352), (304, 470)], 7, LANYARD)
    sp.part(lambda q: q.rect((268, 466, 332, 548), BADGE, r=6),
            lambda q: (q.rect((268, 466, 332, 484), BADGE_STRIPE), q.circle(300, 512, 11, (200, 196, 190))),
            outline=4)

    if pose == 'empty_pockets':                        # pockets turned inside out
        for x, s in ((222, -1), (378, 1)):
            sp.part(lambda q, x=x, s=s: q.poly([(x - 26, 600), (x + 26, 600), (x + 18 + s * 6, 652),
                                                (x - 18 + s * 6, 652)], (246, 244, 236)), outline=5)
    over = _OVER_FACE.copy()
    L, R = ARMS[pose]
    if pose not in over:
        for arm in (L, R) if pose != 'cross_arms' else (R, L):
            _arm(sp, arm)

    # ears, head, hair
    for x in (152, 448):
        cx, cy = _H(x, 282)
        sp.part(lambda q, cx=cx, cy=cy: q.circle(cx, cy, 24, SKIN), outline=6)

    def head_shade(q):
        q.ellipse((*_H(140, 108), *_H(460, 404)), SKIN_SH)
        q.ellipse((*_H(170, 96), *_H(470, 384)), SKIN)
    sp.part(lambda q: q.ellipse((*_H(148, 113), *_H(452, 397)), SKIN), head_shade, outline=7)
    _hair_messy(sp)
    _face(sp, pose, mood, blink, talk)

    if pose in over:
        for arm in (L, R):
            _arm(sp, arm)
    _pose_props(sp, pose)
    if pose == 'read':                                 # receipt held in both hands
        lay = p.layer()
        zig = [(232 + 136 * i / 8, 556 + (8 if i % 2 else 0)) for i in range(8, -1, -1)]
        lay.poly([(232, 404), (368, 404)] + zig, (252, 250, 244))
        lay.line([(232, 404), (368, 404)] + zig + [(232, 404)], 4, OUTLINE)
        for k in range(5):
            lay.line([(246, 428 + k * 22), (354 - (30 if k == 4 else 0), 428 + k * 22)], 4,
                     (214, 69, 69) if k == 4 else (150, 146, 140))
        p.paste(lay)
        for hx in (246, 354):
            sp.part(lambda q, hx=hx: q.circle(hx, 452, 22, SKIN), outline=6)
    return sp.done()


# ================================================================ B. Piggy Ben (cracked piggy bank)
PINK, PINK_SH, PINK_HI, PINK_DK = (255, 168, 186), (238, 128, 154), (255, 214, 224), (163, 64, 91)


def piggy(mood='smile', scale=1, blink=False, talk=True):
    sp = Sprite(700, 640, scale)
    p = sp.pen
    lay = p.layer()
    lay.ellipse((150, 590, 560, 632), (0, 0, 0, 60))
    p.paste(lay, blur=4)
    # tail (curl, left)
    tail = [(150, 360)] + bez((150, 360), (90, 350), (80, 290), (120, 280)) + bez((120, 280), (150, 275), (150, 315),
                                                                                  (118, 318))[1:]
    sp.part(lambda q: q.line(tail, 14, PINK), outline=6)
    # legs (back darker, front)
    for x, col in ((210, PINK_SH), (490, PINK_SH), (270, PINK), (430, PINK)):
        sp.part(lambda q, x=x, col=col: q.rect((x - 34, 480, x + 34, 606), col, r=22),
                lambda q, x=x: q.rect((x - 40, 574, x + 40, 612), PINK_DK), outline=6)
    # ears
    for s in (-1, 1):
        ear = path((350 + s * 120, 200), [((350 + s * 130, 120), (350 + s * 170, 96), (350 + s * 200, 100)),
                                          ((350 + s * 214, 140), (350 + s * 200, 196), (350 + s * 176, 236))])
        inner = path((350 + s * 140, 196), [((350 + s * 150, 150), (350 + s * 170, 132), (350 + s * 188, 132)),
                                            ((350 + s * 194, 160), (350 + s * 186, 190), (350 + s * 170, 214))])
        sp.part(lambda q, ear=ear, inner=inner: (q.poly(ear, PINK), q.poly(inner, PINK_SH)), outline=7)

    # body
    def body_shade(q):
        q.ellipse((90, 150, 610, 590), PINK_SH)
        q.ellipse((126, 130, 640, 560), PINK)
        q.ellipse((420, 200, 540, 270), PINK_HI + (200,))
    sp.part(lambda q: q.ellipse((120, 170, 580, 560), PINK), body_shade, outline=8)
    # coin slot
    p.rect((304, 182, 396, 200), PINK_DK, OUTLINE, 4, r=9)
    # crack + band-aid
    crack = [(520, 236), (540, 268), (526, 296), (552, 330), (540, 356)]
    p.line(crack, 6, PINK_DK)
    ba = p.layer()
    cx, cy = 534, 296
    ba.rect((cx - 70, cy - 22, cx + 70, cy + 22), (243, 215, 166), OUTLINE, 5, r=20)
    ba.rect((cx - 24, cy - 18, cx + 24, cy + 18), (226, 188, 130), r=6)
    for dx in (-48, -38, 38, 48):
        for dy in (-8, 8):
            ba.circle(cx + dx, cy + dy, 2.5, (210, 170, 110))
    p.paste(ba, rotate=-62, center=(cx, cy))
    # face
    for x in (272, 428):
        closed_eye(p, x, 320, 23) if blink else eye(p, x, 320, rx=23, ry=31)
    brow(p, (240, 262), (296, 254))
    brow(p, (404, 254), (460, 262))
    blush = p.layer()
    for x in (212, 488):
        blush.ellipse((x - 32, 372, x + 32, 394), (255, 110, 130, 120))
    p.paste(blush, blur=2)
    sp.part(lambda q: q.ellipse((278, 352, 422, 444), (255, 196, 208)),
            lambda q: q.ellipse((278, 380, 422, 452), (246, 170, 186)), outline=6)
    for x in (322, 378):
        p.ellipse((x - 11, 380, x + 11, 414), PINK_DK)
    mouth(sp, 350, 458, 34, 28, mood, talk)
    return sp.done()
