"""Broke Ben branding v2: two polished mascot options, each with avatar + banner + previews.

Option A: Ben (chibi, green hoodie).   Option B: Piggy Ben (cracked piggy bank with a band-aid).
Run:  python make_branding_v2.py      (writes into ./branding/option_A_ben and ./branding/option_B_piggy)
"""
import math
import os
from PIL import Image, ImageDraw
from flatkit import Pen, font, INK
from charkit import ben, piggy
from make_branding import NAME, TAGLINE, SCHEDULE, GREEN, GOLD, RED, CREAM, coin, banner_preview, avatar_preview, \
    BW, BH, SAFE

ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'branding')


def circle_mask(img):
    S = img.width
    m = Image.new('L', (S * 4, S * 4), 0)
    ImageDraw.Draw(m).ellipse((0, 0, S * 4, S * 4), fill=255)
    out = Image.new('RGBA', img.size, (0, 0, 0, 0))
    out.paste(img, (0, 0), m.resize(img.size, Image.LANCZOS))
    return out


def avatar_bg(S=800):
    p = Pen(S, S)
    p.circle(S / 2, S / 2, S / 2, (38, 120, 76))
    lay = p.layer()                                      # soft sunburst
    for i in range(16):
        a0, a1 = math.radians(i * 22.5), math.radians(i * 22.5 + 11)
        lay.poly([(S / 2, S * 0.42), (S / 2 + S * math.cos(a0), S * 0.42 + S * math.sin(a0)),
                  (S / 2 + S * math.cos(a1), S * 0.42 + S * math.sin(a1))], (255, 255, 255, 18))
    p.paste(lay)
    lay = p.layer()
    lay.circle(S / 2, S * 0.42, S * 0.34, (120, 220, 160, 120))
    p.paste(lay, blur=60)
    return p


def avatar_A():
    S = 800
    p = avatar_bg(S)
    img = p.done()
    spr = ben('idle', 'smile', scale=3)                  # 1800 x 2340
    crop = spr.crop((3 * 90, 3 * 30, 3 * 510, 3 * 640))   # head + hoodie
    k = S * 0.86 / crop.width
    crop = crop.resize((int(crop.width * k), int(crop.height * k)), Image.LANCZOS)
    img.alpha_composite(crop, (int(S / 2 - crop.width / 2), int(S * 0.1)))
    return circle_mask(img)


def avatar_B():
    S = 800
    img = avatar_bg(S).done()
    spr = piggy('smile', scale=3)                        # 2100 x 1920
    crop = spr.crop((3 * 60, 3 * 70, 3 * 640, 3 * 640))
    k = S * 0.86 / crop.width
    crop = crop.resize((int(crop.width * k), int(crop.height * k)), Image.LANCZOS)
    img.alpha_composite(crop, (int(S / 2 - crop.width / 2 + S * 0.01), int(S * 0.15)))
    return circle_mask(img)


def banner(sprite, sprite_h, extra=None):
    p = Pen(BW, BH, bg=CREAM)
    p.vgrad((0, 0, BW, BH), '#FBF7EE', '#ECE3CF')
    for x in range(0, BW, 64):
        p.line([(x, 0), (x, BH)], 1.5, (0, 0, 0, 10), caps=False)
    for y in range(0, BH, 64):
        p.line([(0, y), (BW, y)], 1.5, (0, 0, 0, 10), caps=False)
    pts = []
    for i in range(41):
        t = i / 40
        pts.append((t * BW, BH * 0.92 - (BH * 0.62) * (math.exp(2.6 * t) - 1) / (math.exp(2.6) - 1)
                    + 28 * math.sin(i * 1.3)))
    lay = p.layer()
    lay.poly(pts + [(BW, BH), (0, BH)], GREEN + (26,))
    p.paste(lay)
    p.line(pts, 10, GREEN + (150,))
    for cx, cy, r in [(170, 300, 70), (330, 1180, 56), (2300, 260, 84), (2420, 1130, 60), (2160, 1290, 44),
                      (90, 820, 40)]:
        coin(p, cx, cy, r)
    x0, y0, x1, y1 = SAFE
    sprite = sprite.crop(sprite.getbbox())
    k = sprite_h / sprite.height
    spr = sprite.resize((int(sprite.width * k), int(sprite.height * k)), Image.LANCZOS)
    w = p.text_w(SCHEDULE, 'bold', 40) + 64
    text_w = max(p.text_w(NAME, 'display', 200), p.text_w(TAGLINE, 'semi', 62), w)
    gap = 60
    left = (x0 + x1) / 2 - (spr.width + gap + text_w) / 2
    sx, sy = int(left), int(y1 - spr.height + 6)
    if extra:
        extra(p, sx, sy, spr.width, spr.height)
    big = sprite.resize((spr.width * p.S, spr.height * p.S), Image.LANCZOS)
    p.img.alpha_composite(big, (sx * p.S, sy * p.S))
    p.d = ImageDraw.Draw(p.img)
    tx = left + spr.width + gap
    p.text((tx, y0 + 20), NAME, 'display', 200, INK)
    p.rect((tx + 4, y0 + 244, tx + 330, y0 + 258), GOLD, r=7)
    p.text((tx, y0 + 312), TAGLINE, 'semi', 62, (70, 66, 60), anchor='lm')
    p.rect((tx, y1 - 66, tx + w, y1 - 8), RED, r=29)
    p.text((tx + w / 2, y1 - 37), SCHEDULE, 'bold', 40, (255, 255, 255), anchor='mm')
    return p.done()


def coin_drop(p, sx, sy, w, h):
    """A coin about to drop into the piggy's slot, with motion lines."""
    cx, cy = sx + w * 0.5, sy - 40
    for dx in (-26, 0, 26):
        p.line([(cx + dx, cy - 110), (cx + dx, cy - 70)], 6, (120, 110, 90, 160))
    coin(p, cx, cy, 34)


def build(name, avatar, spr, spr_h, extra=None):
    out = os.path.join(ROOT, name)
    os.makedirs(out, exist_ok=True)
    avatar.save(os.path.join(out, 'avatar_800x800.png'))
    avatar.resize((150, 150), Image.LANCZOS).save(os.path.join(out, 'watermark_150x150.png'))
    b = banner(spr, spr_h, extra)
    b.convert('RGB').save(os.path.join(out, 'banner_2560x1440.jpg'), quality=94)
    banner_preview(b).save(os.path.join(out, 'preview_banner_devices.jpg'), quality=90)
    avatar_preview(avatar).save(os.path.join(out, 'preview_avatar_sizes.png'))
    return avatar, b


def compare(rows, path):
    W = 40 + 400 + 40 + int(400 * BW / BH) + 40
    img = Image.new('RGB', (W, 120 + len(rows) * 520), (18, 19, 23))
    d = ImageDraw.Draw(img)
    d.text((40, 36), 'BROKE BEN · 2 NHÂN VẬT MỚI', font=font('display', 60), fill=(245, 245, 240))
    for i, (label, av, bn) in enumerate(rows):
        y = 140 + i * 520
        d.text((40, y), label, font=font('semi', 40), fill=(255, 196, 61))
        a = av.resize((400, 400), Image.LANCZOS)
        img.paste(a, (40, y + 70), a)
        b = bn.convert('RGB').resize((int(400 * BW / BH), 400), Image.LANCZOS)
        img.paste(b, (W - b.width - 40, y + 70))
    img.save(path, quality=92)


if __name__ == '__main__':
    a1, b1 = build('option_A_ben', avatar_A(), ben('point', 'smile', scale=2), 410)
    a2, b2 = build('option_B_piggy', avatar_B(), piggy('smile', scale=2), 320, coin_drop)
    compare([('A. Ben (chibi, hoodie xanh)', a1, b1), ('B. Piggy Ben (heo đất nứt dán băng)', a2, b2)],
            os.path.join(ROOT, 'COMPARE_v2.jpg'))
    print('done')
