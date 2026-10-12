"""Broke Ben channel branding: avatar, banner, watermark and preview sheets.

Run:  python make_branding.py      (writes into ./branding)
Change NAME / TAGLINE / SCHEDULE below and re-run to rebrand.
"""
import math
import os
import random
from PIL import Image, ImageDraw
from flatkit import Pen, Look, draw_char, rim, font, INK

NAME = 'BROKE BEN'
TAGLINE = "Money, explained before it's gone."
SCHEDULE = 'NEW VIDEOS EVERY WED & SAT'

OUT = os.path.join(os.getcwd(), 'branding')
os.makedirs(OUT, exist_ok=True)

# brand palette
CREAM, GREEN, GREEN_D, GOLD, RED = '#F6F1E6', (46, 139, 87), (30, 98, 62), (255, 196, 61), (214, 69, 69)
BEN = Look()   # spiky brown hair, green hoodie: the channel mascot


def coin(p, cx, cy, r, tilt=0):
    p.circle(cx + r * 0.08, cy + r * 0.1, r, (0, 0, 0, 50))
    p.circle(cx, cy, r, GOLD, INK, r * 0.09)
    p.circle(cx, cy, r * 0.74, None, (214, 150, 30), r * 0.07)
    p.text((cx, cy + r * 0.04), '$', 'display', r * 1.05, (150, 98, 18), anchor='mm')


def avatar():
    S = 800
    p = Pen(S, S)
    p.circle(S / 2, S / 2, S / 2, GREEN)
    lay = p.layer()        # soft light behind the head
    lay.circle(S / 2, S * 0.42, S * 0.36, (255, 255, 255, 60))
    p.paste(lay, blur=40)
    R = 205
    draw_char(p, S / 2, S * 0.43 + 4.64 * R, R, BEN, 'stand', 'confident')   # bust: feet far below the frame
    coin(p, S * 0.72, S * 0.71, 80)
    img = p.done()
    mask = Image.new('L', (S * 4, S * 4), 0)
    ImageDraw.Draw(mask).ellipse((0, 0, S * 4, S * 4), fill=255)
    out = Image.new('RGBA', (S, S), (0, 0, 0, 0))
    out.paste(img, (0, 0), mask.resize((S, S), Image.LANCZOS))
    return out


def watermark():
    big = avatar().resize((150, 150), Image.LANCZOS)
    return big


BW, BH = 2560, 1440
SAFE = ((BW - 1546) / 2, (BH - 423) / 2, (BW + 1546) / 2, (BH + 423) / 2)   # visible on every device


def banner():
    p = Pen(BW, BH, bg=CREAM)
    p.vgrad((0, 0, BW, BH), '#FBF7EE', '#ECE3CF')
    for x in range(0, BW, 64):                 # ledger-paper grid
        p.line([(x, 0), (x, BH)], 1.5, (0, 0, 0, 10), caps=False)
    for y in range(0, BH, 64):
        p.line([(0, y), (BW, y)], 1.5, (0, 0, 0, 10), caps=False)
    # rising money line behind everything (decoration outside the safe text block)
    pts = []
    for i in range(41):
        t = i / 40
        pts.append((t * BW, BH * 0.92 - (BH * 0.62) * (math.exp(2.6 * t) - 1) / (math.exp(2.6) - 1)
                    + 28 * math.sin(i * 1.3)))
    lay = p.layer()
    lay.poly(pts + [(BW, BH), (0, BH)], GREEN + (26,))
    p.paste(lay)
    p.line(pts, 10, GREEN + (150,))
    rnd = random.Random(11)
    for cx, cy, r in [(170, 300, 70), (330, 1180, 56), (2300, 260, 84), (2420, 1130, 60), (2160, 1290, 44),
                      (90, 820, 40)]:
        coin(p, cx, cy, r)
    for cx, cy in [(420, 180), (2120, 140), (260, 1000), (2380, 640)]:
        p.text((cx, cy), '$', 'display', rnd.randint(70, 110), GREEN + (70,), anchor='mm')
    # safe block: Ben + name + tagline + schedule
    x0, y0, x1, y1 = SAFE
    R = 64
    w = p.text_w(SCHEDULE, 'bold', 40) + 64
    text_w = max(p.text_w(NAME, 'display', 200), p.text_w(TAGLINE, 'semi', 62), w)
    ben_w, gap = 2.2 * R, 70          # body + pointing arm
    left = (x0 + x1) / 2 - (ben_w + gap + text_w) / 2
    bx = left + 0.75 * R
    rim(p, lambda l: draw_char(l, bx, y1 - 14, R, BEN, 'point_right', 'confident', gaze=(1, 0)), size=10)
    tx = left + ben_w + gap
    p.text((tx, y0 + 20), NAME, 'display', 200, INK)
    p.rect((tx + 4, y0 + 244, tx + 330, y0 + 258), GOLD, r=7)
    p.text((tx, y0 + 312), TAGLINE, 'semi', 62, (70, 66, 60), anchor='lm')
    p.rect((tx, y1 - 66, tx + w, y1 - 8), RED, r=29)
    p.text((tx + w / 2, y1 - 37), SCHEDULE, 'bold', 40, (255, 255, 255), anchor='mm')
    return p.done()


def banner_preview(b):
    """Banner with the device crops drawn on top, to check nothing important is cut."""
    im = b.convert('RGB').copy()
    d = ImageDraw.Draw(im)
    f = font('bold', 36)
    crops = [('TV: full 2560x1440', (0, 0, BW, BH), (120, 120, 120)),
             ('Desktop: 2560x423', (0, (BH - 423) / 2, BW, (BH + 423) / 2), (40, 110, 220)),
             ('Tablet: 1855x423', ((BW - 1855) / 2, (BH - 423) / 2 - 6, (BW + 1855) / 2, (BH + 423) / 2 + 6),
              (230, 140, 20)),
             ('Mobile / safe area: 1546x423', SAFE, (220, 40, 40))]
    for i, (lab, box, col) in enumerate(crops):
        d.rectangle(box, outline=col, width=6)
        d.text((box[0] + 16, box[1] - 46 if i else 16), lab, font=f, fill=col)
    return im.resize((1280, 720), Image.LANCZOS)


def avatar_preview(a):
    """How the avatar reads at the sizes YouTube actually shows it."""
    W, H = 1200, 420
    im = Image.new('RGB', (W, H), (255, 255, 255))
    d = ImageDraw.Draw(im)
    d.rectangle((W / 2, 0, W, H), fill=(15, 15, 15))
    f = font('semi', 26)
    for half, (bg_x, ink) in enumerate([(0, (20, 20, 20)), (W / 2, (240, 240, 240))]):
        x = bg_x + 40
        for s, lab in [(176, 'channel page'), (88, 'video page'), (36, 'comments')]:
            im.paste(a.resize((s, s), Image.LANCZOS), (int(x), int(200 - s / 2)), a.resize((s, s), Image.LANCZOS))
            d.text((x + s / 2, 330), lab, font=f, fill=ink, anchor='mt')
            d.text((x + s / 2, 365), f'{s}px', font=f, fill=(140, 140, 140), anchor='mt')
            x += s + 70
    d.text((40, 24), 'Light mode', font=f, fill=(20, 20, 20))
    d.text((W / 2 + 40, 24), 'Dark mode', font=f, fill=(240, 240, 240))
    return im


if __name__ == '__main__':
    a = avatar()
    a.save(os.path.join(OUT, 'avatar_800x800.png'))
    watermark().save(os.path.join(OUT, 'watermark_150x150.png'))
    b = banner()
    b.convert('RGB').save(os.path.join(OUT, 'banner_2560x1440.jpg'), quality=94)
    banner_preview(b).save(os.path.join(OUT, 'preview_banner_devices.jpg'), quality=90)
    avatar_preview(a).save(os.path.join(OUT, 'preview_avatar_sizes.png'))
    print('written to', OUT)
