"""Broke Ben channel art with the young-adult Ben as the face of the channel.

Run:  python <skill>/scripts/make_branding.py   (writes ./branding in the current folder)
Writes avatar_800x800.png, banner_2560x1440.jpg, watermark_150x150.png, preview_banner_devices.jpg,
preview_avatar_sizes.png.
Change NAME / TAGLINE / SCHEDULE below and re-run to rebrand.
"""
import math
import os
import sys

ROOT = os.getcwd()
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from PIL import Image, ImageDraw            # noqa: E402
from flatkit import Pen, font, INK          # noqa: E402
import charkit                              # noqa: E402

NAME = 'BROKE BEN'
TAGLINE = "Money, explained before it's gone."
SCHEDULE = 'NEW VIDEOS EVERY WED & SAT'
OUT = os.path.join(ROOT, 'branding')
GREEN, GOLD, RED = (46, 139, 87), (255, 196, 61), (214, 69, 69)
BW, BH = 2560, 1440
SAFE = ((BW - 1546) / 2, (BH - 423) / 2, (BW + 1546) / 2, (BH + 423) / 2)   # visible on every device


def coin(p, cx, cy, r):
    p.circle(cx + r * 0.08, cy + r * 0.1, r, (0, 0, 0, 50))
    p.circle(cx, cy, r, GOLD, INK, r * 0.09)
    p.circle(cx, cy, r * 0.74, None, (214, 150, 30), r * 0.07)
    p.text((cx, cy + r * 0.04), '$', 'display', r * 1.05, (150, 98, 18), anchor='mm')


def circle_mask(img):
    S = img.width
    m = Image.new('L', (S * 4, S * 4), 0)
    ImageDraw.Draw(m).ellipse((0, 0, S * 4, S * 4), fill=255)
    out = Image.new('RGBA', img.size, (0, 0, 0, 0))
    out.paste(img, (0, 0), m.resize(img.size, Image.LANCZOS))
    return out


def avatar():
    """Ben waving, head and shoulders, on the money-green badge. Must read at 36 px."""
    S = 800
    p = Pen(S, S)
    p.circle(S / 2, S / 2, S / 2, (38, 120, 76))
    rays = p.layer()
    for i in range(16):
        a0, a1 = math.radians(i * 22.5), math.radians(i * 22.5 + 11)
        rays.poly([(S / 2, S * 0.4), (S / 2 + S * math.cos(a0), S * 0.4 + S * math.sin(a0)),
                   (S / 2 + S * math.cos(a1), S * 0.4 + S * math.sin(a1))], (255, 255, 255, 18))
    p.paste(rays)
    glow = p.layer()
    glow.circle(S / 2, S * 0.38, S * 0.32, (130, 225, 165, 120))
    p.paste(glow, blur=60)
    img = p.done()
    spr = charkit.ben('wave', 'smile', scale=3)                     # 1800 x 2820
    crop = spr.crop((3 * 80, 3 * 40, 3 * 570, 3 * 600))           # head, waving hand, shoulders, straps
    k = S * 0.9 / crop.width
    crop = crop.resize((int(crop.width * k), int(crop.height * k)), Image.LANCZOS)
    img.alpha_composite(crop, (int(S / 2 - crop.width / 2 + S * 0.02), int(S * 0.09)))
    return circle_mask(img)


def banner():
    p = Pen(BW, BH)
    p.vgrad((0, 0, BW, BH), '#FBF7EE', '#ECE3CF')
    grid = p.layer()
    for x in range(0, BW, 64):
        grid.line([(x, 0), (x, BH)], 2, (0, 0, 0, 18), caps=False)
    for y in range(0, BH, 64):
        grid.line([(0, y), (BW, y)], 2, (0, 0, 0, 18), caps=False)
    p.paste(grid)
    pts = [(t * BW, BH * 0.92 - (BH * 0.62) * (math.exp(2.6 * t) - 1) / (math.exp(2.6) - 1) + 28 * math.sin(i * 1.3))
           for i, t in ((i, i / 40) for i in range(41))]
    area = p.layer()
    area.poly(pts + [(BW, BH), (0, BH)], GREEN + (26,))
    p.paste(area)
    line = p.layer()
    line.line(pts, 10, GREEN + (150,))
    p.paste(line)
    for cx, cy, r in [(170, 300, 70), (330, 1180, 56), (2300, 260, 84), (2420, 1130, 60), (2160, 1290, 44),
                      (90, 820, 40)]:
        coin(p, cx, cy, r)
    x0, y0, x1, y1 = SAFE
    ben = charkit.ben('point', 'smile', scale=2)
    ben = ben.crop(ben.getbbox())
    kb = 420 / ben.height
    ben = ben.resize((int(ben.width * kb), 420), Image.LANCZOS)
    pig = charkit.piggy('smile', scale=1)
    pig = pig.crop(pig.getbbox())
    kp = 150 / pig.height
    pig = pig.resize((int(pig.width * kp), 150), Image.LANCZOS)
    sched_w = p.text_w(SCHEDULE, 'bold', 40) + 64
    text_w = max(p.text_w(NAME, 'display', 200), p.text_w(TAGLINE, 'semi', 62), sched_w)
    gap = 50
    total = pig.width + 10 + ben.width + gap + text_w
    left = (x0 + x1) / 2 - total / 2
    S = p.S
    for im, x, y in ((pig, left, y1 - pig.height + 4), (ben, left + pig.width + 10, y1 - ben.height + 4)):
        big = im.resize((im.width * S, im.height * S), Image.LANCZOS)
        p.img.alpha_composite(big, (int(x * S), int(y * S)))
    p.d = ImageDraw.Draw(p.img)
    tx = left + pig.width + 10 + ben.width + gap
    p.text((tx, y0 + 20), NAME, 'display', 200, INK)
    p.rect((tx + 4, y0 + 244, tx + 330, y0 + 258), GOLD, r=7)
    p.text((tx, y0 + 312), TAGLINE, 'semi', 62, (70, 66, 60), anchor='lm')
    p.rect((tx, y1 - 66, tx + sched_w, y1 - 8), RED, r=29)
    p.text((tx + sched_w / 2, y1 - 37), SCHEDULE, 'bold', 40, (255, 255, 255), anchor='mm')
    return p.done()


def banner_preview(b):
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
    W, H = 1200, 420
    im = Image.new('RGB', (W, H), (255, 255, 255))
    d = ImageDraw.Draw(im)
    d.rectangle((W / 2, 0, W, H), fill=(15, 15, 15))
    f = font('semi', 26)
    for bg_x, ink in ((0, (20, 20, 20)), (W / 2, (240, 240, 240))):
        x = bg_x + 40
        for s, lab in ((176, 'channel page'), (88, 'video page'), (36, 'comments')):
            sm = a.resize((s, s), Image.LANCZOS)
            im.paste(sm, (int(x), int(200 - s / 2)), sm)
            d.text((x + s / 2, 330), lab, font=f, fill=ink, anchor='mt')
            d.text((x + s / 2, 365), f'{s}px', font=f, fill=(140, 140, 140), anchor='mt')
            x += s + 70
    d.text((40, 24), 'Light mode', font=f, fill=(20, 20, 20))
    d.text((W / 2 + 40, 24), 'Dark mode', font=f, fill=(240, 240, 240))
    return im


def main():
    os.makedirs(OUT, exist_ok=True)
    a = avatar()
    a.save(os.path.join(OUT, 'avatar_800x800.png'))
    a.resize((150, 150), Image.LANCZOS).save(os.path.join(OUT, 'watermark_150x150.png'))
    b = banner()
    b.convert('RGB').save(os.path.join(OUT, 'banner_2560x1440.jpg'), quality=94)
    banner_preview(b).save(os.path.join(OUT, 'preview_banner_devices.jpg'), quality=90)
    avatar_preview(a).save(os.path.join(OUT, 'preview_avatar_sizes.png'))
    print('written to', OUT)


if __name__ == '__main__':
    main()
