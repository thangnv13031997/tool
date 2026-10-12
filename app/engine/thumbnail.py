"""High-CTR horror thumbnails (1280x720), three layouts for A/B/C testing.

Rules baked in: one big readable face with strong emotion, one threat element,
2-4 words of text, high contrast, dark background with one accent colour,
and a rim light so the subject pops on a phone screen.
"""
import math
from PIL import Image, ImageDraw, ImageEnhance, ImageFilter, ImageChops
from . import figure as F
from . import props as PR
from . import backgrounds as BG
from . import textfx, fx
from .gfx import Pen, hex_rgba

TW, TH = 1280, 720
ACCENTS = {'red': (235, 40, 40), 'yellow': (255, 212, 59), 'teal': (60, 200, 210), 'green': (90, 230, 120),
           'orange': (255, 140, 40), 'white': (240, 240, 235)}


def _bg(spec):
    name = spec.get('bg', 'forest')
    opts = {'time': spec.get('time', 'night'), 'lights': spec.get('lights', 'on')}
    opts.update(spec.get('opts') or {})
    lay = BG.render_bg(name, TW, TH, opts, S=1)
    img = fx.grade(lay.img, 0.3, (0.9, 0.98, 1.1), 1.08)
    L = fx.Lighting(TW, TH, lay.lights, max(0.3, lay.ambient), lay.tint, vignette=0.75, exposure=1.6)
    img, _ = L.apply(img, 0.0)
    if lay.fg:
        img.paste(lay.fg, (0, 0), lay.fg)
    return img.filter(ImageFilter.GaussianBlur(2.2))


def _rim(tile, color=(255, 255, 255), size=9, alpha=255):
    a = tile.getchannel('A').filter(ImageFilter.MaxFilter(size | 1))
    a = a.filter(ImageFilter.GaussianBlur(2))
    g = Image.new('RGBA', tile.size, color + (alpha,))
    g.putalpha(a.point(lambda v: int(v * alpha / 255)))
    return g


def _glow(img, x, y, r, color, a=150):
    lay = Image.new('RGBA', img.size, (0, 0, 0, 0))
    d = ImageDraw.Draw(lay)
    for i in range(10, 0, -1):
        rr = r * i / 10
        d.ellipse((x - rr, y - rr, x + rr, y + rr), fill=color + (int(a * (1 - i / 10) ** 1.5),))
    img.alpha_composite(lay)


def _figure(info, spec, u, close=False):
    look = info['look'] if info else F.Look({'name': spec.get('name')})
    pose, _ = F.resolve_pose(spec.get('pose', 'terrified'))
    emo, _ = F.resolve_expr(spec.get('emotion', 'terrified'))
    facing = -1 if spec.get('facing') in ('left', -1) else 1
    ang = F.pose_angles(pose, 0.2)
    if 'tremble' in ang:
        ang['tremble'] = 0
    tile, ax, ay = F.draw_figure(look, pose, ang, facing, emo, 0.0, False, 0.2, u=u, S=2, shadow=False)
    bb = tile.getbbox()
    if bb:
        tile = tile.crop(bb)
        ax -= bb[0]
        ay -= bb[1]
    if close:
        h = int(tile.height * 0.55)
        tile = tile.crop((0, 0, tile.width, h))
    return tile, ax, ay


def _threat(img, spec, cast, x, y, scale=1.0):
    th = spec.get('threat')
    if not th:
        return
    if isinstance(th, str):
        th = {'type': th}
    tname = th.get('name')
    key = textfx.re.sub(r'[^a-z0-9]+', '_', (tname or '').lower()).strip('_') if tname else None
    if key and key in cast:
        info = cast[key]
        tile, ax, ay = _figure(info, {'pose': th.get('pose', 'loom'), 'emotion': th.get('emotion', 'creepy_smile'),
                                      'facing': th.get('facing', 'left')}, TH / 104 * 0.62 * scale * float(th.get('scale', 1.0)),
                               close=th.get('full') is not True)
        # keep the threat's head inside the picture with room for the red circle
        y = max(y, 0.13 + tile.height * 0.12 / TH)
        dark = Image.new('RGBA', tile.size, (0, 0, 0, 0))
        tile = Image.alpha_composite(tile, Image.new('RGBA', tile.size, (0, 0, 0, 0)))
        _glow(img, x * TW, y * TH + tile.height * 0.15, tile.height * 0.55, (200, 20, 20), 110)
        px, py = int(x * TW - tile.width / 2), int(y * TH - tile.height * 0.12)
        img.paste(tile, (px, py), tile)
        return (x * TW, py + tile.height * 0.3)
    kind = th.get('type', 'shadow_figure')
    name, group, _ = PR.resolve(kind)
    s = TH * 0.28 * scale * float(th.get('scale', 1.0))
    tile, cx, cy = PR.render({'type': name, 'eyes': True, 'text': th.get('text'),
                              'color': th.get('color', '#FF4A3A' if name == 'eyes' else None)}, s, 0.0, S=2,
                             full=(TW, TH))
    if group == 'glow' and name == 'eyes':
        _glow(img, x * TW, y * TH, s * 0.9, ACCENTS.get(th.get('accent', 'red'), (235, 40, 40)), 120)
        s *= 1.6
    img.paste(tile, (int(x * TW - cx), int(y * TH - cy)), tile)
    return (x * TW, y * TH)


def _text(img, text, accent, area='right', size=150):
    words = textfx.words_marked((text or '').upper())
    if not words:
        return
    max_w = TW * (0.46 if area == 'br' else 0.5 if area in ('right', 'left') else 0.9)
    fs = size
    max_h = TH * (0.44 if area == 'br' else 0.62)
    while fs > 60:
        fnt = textfx.font('display', fs)
        lines = textfx.wrap_words(words, fnt, max_w)
        asc, desc = fnt.getmetrics()
        if len(lines) <= 3 and all(fnt.getlength(' '.join(w for w, _ in ln)) <= max_w for ln in lines) \
                and (asc + desc) * 0.98 * len(lines) <= max_h:
            break
        fs -= 8
    col = ACCENTS.get(accent, (235, 40, 40))
    timg = textfx.render_words(lines, fnt, fill=(250, 248, 240, 255), hi_fill=col + (255,), danger_fill=col + (255,),
                               stroke=14, stroke_fill=(5, 5, 7, 255), line_gap=0.98,
                               align='center' if area in ('top', 'bottom', 'br') else 'left', shadow=10)
    if area == 'br':
        x, y = int(TW * 0.975 - timg.width), int(TH * 0.97 - timg.height)
    elif area == 'right':
        x, y = int(TW * 0.965 - timg.width), int(TH * 0.5 - timg.height / 2)
    elif area == 'left':
        x, y = int(TW * 0.03), int(TH * 0.5 - timg.height / 2)
    elif area == 'top':
        x, y = int(TW / 2 - timg.width / 2), int(TH * 0.04)
    else:
        x, y = int(TW / 2 - timg.width / 2), int(TH * 0.96 - timg.height)
    img.alpha_composite(timg, (max(0, x), max(0, y)))


def _arrow(img, frm, to, col):
    d = ImageDraw.Draw(img)
    d.line([frm, to], fill=col + (255,), width=16)
    ang = math.atan2(to[1] - frm[1], to[0] - frm[0])
    L = 50
    p1 = (to[0] - L * math.cos(ang - 0.5), to[1] - L * math.sin(ang - 0.5))
    p2 = (to[0] - L * math.cos(ang + 0.5), to[1] - L * math.sin(ang + 0.5))
    d.polygon([to, p1, p2], fill=col + (255,))


def _circle(img, c, r, col):
    d = ImageDraw.Draw(img)
    for w in range(10):
        d.ellipse((c[0] - r - w, c[1] - r * 0.8 - w, c[0] + r + w, c[1] + r * 0.8 + w), outline=col + (255,))


def render(spec, cast, default_title=''):
    spec = dict(spec or {})
    layout = spec.get('layout', 'face_threat')
    accent = spec.get('accent', 'red')
    acol = ACCENTS.get(accent, (235, 40, 40))
    img = _bg(spec).convert('RGBA')
    main = spec.get('char') or (spec.get('chars') or [None])[0]
    if not main and cast:
        hero = next((c for c in cast.values() if c.get('role') == 'main'), next(iter(cast.values())))
        main = {'name': hero['name'], 'pose': 'terrified', 'emotion': 'terrified'}
    info = None
    if main:
        key = textfx.re.sub(r'[^a-z0-9]+', '_', (main.get('name') or '').lower()).strip('_')
        info = cast.get(key)
    threat_pt = None
    text_area = spec.get('text_area')
    if layout == 'face_threat':
        threat_pt = _threat(img, spec, cast, spec.get('threat_x', 0.8), spec.get('threat_y', 0.2), 1.25)
        dark = Image.new('RGBA', img.size, (0, 0, 0, 0))
        ImageDraw.Draw(dark).rectangle((0, 0, TW * 0.55, TH), fill=(0, 0, 0, 70))
        img.alpha_composite(dark)
        if main:
            u = TH / 104 * 1.55
            tile, ax, ay = _figure(info, main, u, close=True)
            _glow(img, int(TW * 0.27), int(TH * 0.45), TH * 0.55, (180, 200, 255), 70)
            rim = _rim(tile, (230, 236, 255), 13)
            x = int(TW * 0.27 - tile.width / 2)
            y = int(TH * 0.08)
            img.alpha_composite(rim, (x, y))
            img.alpha_composite(tile, (x, y))
        text_area = text_area or ('br' if threat_pt is not None and threat_pt[1] < TH * 0.5 else 'right')
    elif layout == 'object':
        p = spec.get('prop') or {'type': 'note', 'text': spec.get('prop_text', "DON'T\nOPEN THE\nDOOR")}
        name, group, _ = PR.resolve(p.get('type'))
        s = TH * 0.42 * float(p.get('scale', 1.0))
        tile, cx, cy = PR.render(dict(p, type=name), s, 0.3, S=2, full=(TW, TH))
        if group == 'glow':
            _glow(img, TW * 0.66, TH * 0.52, TH * 0.6, (160, 200, 255), 90)
        img.alpha_composite(_rim(tile, (255, 255, 255), 9, 200), (int(TW * 0.66 - cx), int(TH * 0.54 - cy)))
        img.alpha_composite(tile, (int(TW * 0.66 - cx), int(TH * 0.54 - cy)))
        if main:
            tile, ax, ay = _figure(info, main, TH / 104 * 0.74)
            img.alpha_composite(_rim(tile, (230, 236, 255), 11), (int(TW * 0.2 - ax), int(TH * 1.0 - ay)))
            img.alpha_composite(tile, (int(TW * 0.2 - ax), int(TH * 1.0 - ay)))
        threat_pt = _threat(img, spec, cast, spec.get('threat_x', 0.9), spec.get('threat_y', 0.3), 0.6)
        text_area = text_area or 'top'
    else:  # split: calm left, danger right
        right = img.crop((TW // 2, 0, TW, TH))
        right = ImageEnhance.Brightness(right).enhance(0.55)
        tint = Image.new('RGBA', right.size, acol + (60,))
        right.alpha_composite(tint)
        img.paste(right, (TW // 2, 0))
        d = ImageDraw.Draw(img)
        d.line([(TW // 2, 0), (TW // 2, TH)], fill=(250, 250, 245, 255), width=8)
        if main:
            calm = dict(main, pose='idle', emotion=spec.get('before_emotion', 'neutral'))
            tile, ax, ay = _figure(info, calm, TH / 104 * 0.74)
            img.alpha_composite(_rim(tile, (255, 230, 190), 11), (int(TW * 0.25 - ax), int(TH * 1.0 - ay)))
            img.alpha_composite(tile, (int(TW * 0.25 - ax), int(TH * 1.0 - ay)))
            tile, ax, ay = _figure(info, main, TH / 104 * 0.74)
            img.alpha_composite(_rim(tile, (230, 236, 255), 11), (int(TW * 0.63 - ax), int(TH * 1.0 - ay)))
            img.alpha_composite(tile, (int(TW * 0.63 - ax), int(TH * 1.0 - ay)))
        threat_pt = _threat(img, spec, cast, spec.get('threat_x', 0.88), spec.get('threat_y', 0.45), 0.85)
        text_area = text_area or 'top'
    if spec.get('circle', layout == 'face_threat') and threat_pt:
        _circle(img, threat_pt, TH * 0.15, acol)
    if spec.get('arrow') and threat_pt:
        _arrow(img, (threat_pt[0] - TW * 0.17, threat_pt[1] + TH * 0.22), (threat_pt[0] - TH * 0.12, threat_pt[1] + TH * 0.06), acol)
    _text(img, spec.get('text') or default_title, accent, text_area or 'top')
    out = img.convert('RGB')
    out = ImageEnhance.Contrast(out).enhance(1.12)
    out = ImageEnhance.Color(out).enhance(1.15)
    return out


def phone_preview(thumbs, title, channel='Bus 13: Night Route'):
    """How the thumbnails look small in the mobile feed (dark mode)."""
    W, H = 1180, 120 + 330 * len(thumbs)
    img = Image.new('RGB', (W, H), (15, 15, 15))
    d = ImageDraw.Draw(img)
    f1 = textfx.font('bold', 30)
    f2 = textfx.font('body', 24)
    d.text((24, 30), 'Xem thử trên điện thoại (YouTube nền tối)', font=f1, fill=(240, 240, 240))
    y = 100
    for i, t in enumerate(thumbs):
        small = t.resize((480, 270), Image.LANCZOS)
        img.paste(small, (24, y))
        d.rounded_rectangle((24 + 480 - 70, y + 270 - 34, 24 + 480 - 8, y + 270 - 8), 6, fill=(0, 0, 0))
        d.text((24 + 480 - 64, y + 270 - 32), '10:42', font=f2, fill=(240, 240, 240))
        tiny = t.resize((168, 94), Image.LANCZOS)
        img.paste(tiny, (540, y))
        d.text((540, y + 104), f'{"ABC"[i]} (cỡ nhỏ nhất)', font=f2, fill=(170, 170, 170))
        wrapped = textfx.wrap_words([(w, 0) for w in title.split()], f1, 420)
        for k, ln in enumerate(wrapped[:2]):
            d.text((730, y + 6 + k * 38), ' '.join(w for w, _ in ln), font=f1, fill=(240, 240, 240))
        d.text((730, y + 92), channel + ' · 12K views', font=f2, fill=(170, 170, 170))
        y += 330
    return img
