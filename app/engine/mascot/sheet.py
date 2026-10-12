"""Contact sheets for review: every action for one character, and every body x outfit."""
import os
from PIL import Image, ImageDraw, ImageFont
from . import art, actions as A, render as R, qa

FONT = os.path.join(os.path.dirname(__file__), '..', '..', '..', 'assets', 'fonts', 'Oswald-Variable.ttf')


def canonical():
    seen, out = set(), []
    for name, fn in A.ACTIONS.items():
        if fn in seen:
            continue
        seen.add(fn)
        out.append(name)
    return out


def cell(c, name, t, emo, w, h, ppu):
    pose = R.build_pose(c, name, t)
    expr = R.expression(emo, 0, False, t, pose)
    inner, box, ground = R.svg_of(c, pose, expr)
    img = R.rasterize(inner, box, ppu)
    bb = img.getbbox()
    img = img.crop(bb) if bb else img
    img.thumbnail((w - 10, h - 40))
    return img


EMO = {'scared': 'scared', 'terrified': 'terrified', 'hide': 'terrified', 'cower': 'terrified', 'hug_self': 'uneasy',
       'freeze': 'terrified', 'cover_mouth': 'terrified', 'hold_head': 'scared', 'sit_scared': 'scared', 'scream': 'terrified',
       'wave': 'happy', 'talk': 'neutral', 'think': 'thinking', 'peek': 'suspicious', 'sneak': 'uneasy', 'back_away': 'scared',
       'flashlight': 'worried', 'phone_light': 'worried', 'listen': 'suspicious', 'sleep': 'sleep', 'drink': 'calm'}


def actions_sheet(c, title, path, cols=8, w=230, h=290):
    names = canonical()
    rows = (len(names) + cols - 1) // cols
    W, H = cols * w, rows * h + 70
    out = Image.new('RGB', (W, H), (236, 235, 231))
    d = ImageDraw.Draw(out)
    f1, f2 = ImageFont.truetype(FONT, 30), ImageFont.truetype(FONT, 17)
    d.text((W // 2, 34), title, font=f1, fill=(29, 27, 36), anchor='mm')
    res = {n: qa.check(c, n) for n in names}
    for i, n in enumerate(names):
        x, y = (i % cols) * w, 70 + (i // cols) * h
        img = cell(c, n, .4, EMO.get(n, 'neutral'), w, h, .2)
        out.paste(img, (x + (w - img.width) // 2, y + h - 40 - img.height), img)
        ok = not res[n]
        d.text((x + w // 2, y + h - 22), ('[OK] ' if ok else '[LỖI] ') + n, font=f2, fill=(30, 120, 60) if ok else (190, 30, 40), anchor='mm')
    out.save(path)
    return res


def bodies_sheet(cast, names, path, w=200, h=280):
    W, H = (len(names) + 1) * w, len(cast) * h + 80
    out = Image.new('RGB', (W, H), (236, 235, 231))
    d = ImageDraw.Draw(out)
    f1, f2 = ImageFont.truetype(FONT, 26), ImageFont.truetype(FONT, 17)
    d.text((W // 2, 22), 'Mọi dáng người và trang phục với các động tác khó (tay chạm mặt, cầm đồ, ngồi, ngồi xổm)', font=f1, fill=(29, 27, 36), anchor='mm')
    for r, (cn, c) in enumerate(cast.items()):
        y = 80 + r * h
        d.text((w // 2, y + h // 2), cn, font=f2, fill=(29, 27, 36), anchor='mm')
        for k, n in enumerate(names):
            img = cell(c, n, .4, EMO.get(n, 'neutral'), w, h, .18)
            x = (k + 1) * w
            out.paste(img, (x + (w - img.width) // 2, y + h - 20 - img.height), img)
            if r == 0:
                d.text((x + w // 2, 66), n, font=f2, fill=(80, 80, 90), anchor='mm')
    out.save(path)
