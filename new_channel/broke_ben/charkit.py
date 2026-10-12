"""CharKit: polished mascot sprites (smooth Bezier shapes, two-tone cel shading, sticker outline).

Each character is drawn once on its own small canvas and returned as an RGBA sprite,
so scenes, avatars and banners all reuse exactly the same artwork.
Light comes from the top-right; shadows sit bottom-left.
"""
from PIL import Image, ImageChops, ImageDraw, ImageFilter
from flatkit import Pen, rgba

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


# ================================================================ A. Ben (chibi)
SKIN, SKIN_SH, BLUSH = (255, 217, 184), (240, 186, 150), (255, 135, 125, 110)
HAIR, HAIR_HI = (75, 46, 34), (120, 78, 56)
HOOD, HOOD_SH, HOOD_HI = (63, 163, 107), (44, 128, 82), (110, 200, 145)
PANTS, PANTS_SH = (44, 58, 94), (32, 42, 70)


def ben(pose='idle', mood='smile', scale=1):
    sp = Sprite(600, 780, scale)
    p = sp.pen
    lay = p.layer()                                   # ground shadow
    lay.ellipse((170, 728, 430, 768), (0, 0, 0, 60))
    p.paste(lay, blur=4)

    # shoes + legs
    for x in (255, 345):
        sp.part(lambda q, x=x: q.rect((x - 24, 630, x + 24, 734), PANTS, r=18),
                lambda q, x=x: q.rect((x - 24, 630, x - 4, 734), PANTS_SH), outline=6)
    for x, s in ((250, -1), (350, 1)):
        sp.part(lambda q, x=x, s=s: q.ellipse((x - 46 + s * 8, 712, x + 46 + s * 8, 762), (246, 246, 240)),
                lambda q, x=x, s=s: (q.rect((x - 60, 744, x + 60, 770), (205, 205, 198)),
                                     q.line([(x - 28 + s * 8, 728), (x + 22 + s * 8, 728)], 7, HOOD)), outline=6)

    # back arm (left side of picture) is always relaxed
    arms = {'idle': [((222, 452), (190, 540), (202, 612))],
            'wave': [((222, 452), (190, 540), (202, 612))],
            'point': [((222, 452), (190, 540), (202, 612))]}
    front = {'idle': ((378, 452), (410, 540), (398, 612)),
             'wave': ((378, 452), (470, 420), (512, 330)),
             'point': ((378, 452), (462, 474), (548, 458))}[pose]

    def sleeve(a, b, c):
        sp.part(lambda q: q.line([a, b, c], 50, HOOD),
                lambda q: q.line([(a[0] - 16, a[1] + 6), (b[0] - 16, b[1] + 4), (c[0] - 14, c[1])], 22, HOOD_SH),
                outline=6)

    for a, b, c in arms[pose]:
        sleeve(a, b, c)
        sp.part(lambda q, c=c: q.circle(c[0], c[1] + 8, 27, SKIN), outline=6)

    # hoodie body
    body = path((215, 430), [((250, 405), (350, 405), (385, 430)), ((412, 470), (420, 540), (414, 600)),
                             ((408, 650), (360, 670), (300, 670)), ((240, 670), (192, 650), (186, 600)),
                             ((180, 540), (188, 470), (215, 430))])

    def body_shade(q):
        q.ellipse((120, 470, 300, 760), HOOD_SH)
        q.rect((150, 640, 450, 700), HOOD_SH)
        q.ellipse((330, 440, 410, 500), HOOD_HI + (170,))
    sp.part(lambda q: q.poly(body, HOOD), body_shade, outline=7)
    pocket = path((246, 562), [((280, 556), (320, 556), (354, 562)), ((362, 590), (366, 612), (370, 628)),
                               ((320, 632), (280, 632), (230, 628)), ((234, 612), (238, 590), (246, 562))])
    p.poly(pocket, HOOD_SH)
    p.line(pocket + [pocket[0]], 4, (34, 100, 64))
    # collar + strings
    p.ellipse((212, 412, 388, 458), HOOD_SH, OUTLINE, 5)
    p.ellipse((262, 408, 338, 440), SKIN_SH)
    for x0, x1 in ((282, 276), (318, 324)):
        p.line([(x0, 446), (x1, 506)], 6, (250, 250, 245))
        p.rect((x1 - 5, 500, x1 + 5, 518), (200, 200, 195), r=3)

    # ears, head
    for x in (152, 448):
        sp.part(lambda q, x=x: q.circle(x, 282, 30, SKIN),
                lambda q, x=x: q.arc((x - 15, 267, x + 15, 297), 100 if x < 300 else -80, 260 if x < 300 else 80,
                                     5, SKIN_SH), outline=6)

    def head_shade(q):
        q.ellipse((140, 108, 460, 404), SKIN_SH)
        q.ellipse((170, 96, 470, 384), SKIN)
    sp.part(lambda q: q.ellipse((148, 113, 452, 397), SKIN), head_shade, outline=7)

    # hair
    hair = path((146, 262), [((132, 120), (240, 88), (312, 96)), ((404, 100), (468, 170), (454, 262)),
                             ((436, 206), (404, 196), (372, 212)), ((350, 178), (306, 190), (274, 220)),
                             ((246, 190), (204, 188), (186, 236)), ((172, 246), (160, 256), (146, 262))])
    tuft = path((292, 104), [((280, 58), (322, 40), (350, 56)), ((328, 66), (318, 84), (326, 104))])

    def hair_shade(q):
        hi = path((326, 118), [((382, 114), (424, 150), (434, 196)), ((412, 162), (382, 140), (326, 132))])
        q.poly(hi, HAIR_HI)
        q.ellipse((118, 200, 210, 300), (62, 38, 28))
    sp.part(lambda q: (q.poly(tuft, HAIR), q.poly(hair, HAIR)), hair_shade, outline=7)

    # face
    look = (1, 0) if pose == 'point' else (0, 0)
    for x in (246, 354):
        eye(p, x, 288, look=look)
    if mood == 'shock':
        brow(p, (214, 218), (272, 214))
        brow(p, (328, 214), (386, 218))
    else:
        brow(p, (216, 228), (272, 220))
        brow(p, (328, 220), (384, 228))
    blush = p.layer()
    for x in (212, 388):
        blush.ellipse((x - 28, 330, x + 28, 348), BLUSH)
    p.paste(blush, blur=2)
    p.arc((290, 300, 310, 322), 20, 160, 5, SKIN_SH)
    if mood == 'shock':
        sp.part(lambda q: q.ellipse((282, 340, 318, 384), (107, 34, 48)),
                lambda q: q.ellipse((286, 366, 314, 392), (255, 122, 138)), outline=4)
    else:
        open_smile(sp, 300, 338, 40, 36)

    # front arm on top
    a, b, c = front
    sleeve(a, b, c)
    if pose == 'point':
        sp.part(lambda q: (q.circle(c[0], c[1], 27, SKIN), q.rect((c[0], c[1] - 14, c[0] + 44, c[1] + 2), SKIN, r=8)),
                outline=6)
    else:
        sp.part(lambda q: q.circle(c[0], c[1] + (0 if pose == 'wave' else 8), 27, SKIN), outline=6)
    return sp.done()


# ================================================================ B. Piggy Ben (cracked piggy bank)
PINK, PINK_SH, PINK_HI, PINK_DK = (255, 168, 186), (238, 128, 154), (255, 214, 224), (163, 64, 91)


def piggy(mood='smile', scale=1):
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
        eye(p, x, 320, rx=23, ry=31)
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
    if mood == 'shock':
        sp.part(lambda q: q.ellipse((334, 456, 366, 492), (107, 34, 48)), outline=4)
    else:
        open_smile(sp, 350, 458, 34, 28)
    return sp.done()
