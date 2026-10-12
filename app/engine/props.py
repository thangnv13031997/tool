"""Horror props and scare entities.

Three groups:
  WORLD    - physical things in the scene, lit by the scene lighting
  GLOW     - things that give off light (drawn after lighting, not darkened)
  INSERT   - close-up overlays (phone chat, notes, rules, CCTV) drawn on top of everything
"""
import math
import random
from PIL import Image
from .gfx import Pen, hex_rgba, shade
from . import textfx

INK = hex_rgba('#0E1014')
PAPER = hex_rgba('#D9D1BD')


def _font(kind, size):
    return textfx.font(kind, max(8, int(size)))


# ------------------------------------------------------------------ world props
def p_footprints(pen, c, s, p, t):
    cx, cy = c
    for i in range(4):
        x = cx - s * 0.9 + i * s * 0.6
        y = cy + (s * 0.12 if i % 2 else -s * 0.12)
        pen.ellipse(x, y, s * 0.13, s * 0.065, fill=hex_rgba(p.get('color', '#9FB0C2'), 150))
        pen.circle(x + s * 0.14, y, s * 0.045, fill=hex_rgba(p.get('color', '#9FB0C2'), 150))


def p_handprint(pen, c, s, p, t):
    cx, cy = c
    col = hex_rgba(p.get('color', '#C8CCD2'), 120)
    pen.ellipse(cx, cy + s * 0.15, s * 0.2, s * 0.24, fill=col)
    for i, a in enumerate((-40, -15, 5, 25)):
        r = math.radians(a)
        ln = s * (0.42 if i in (1, 2) else 0.36)
        pen.line([(cx + math.sin(r) * s * 0.1, cy - s * 0.05), (cx + math.sin(r) * ln, cy - math.cos(r) * ln)], col, s * 0.07)
    pen.line([(cx + s * 0.18, cy + s * 0.18), (cx + s * 0.36, cy + s * 0.02)], col, s * 0.07)


def p_doll(pen, c, s, p, t):
    cx, cy = c
    pen.poly([(cx - s * 0.25, cy + s * 0.5), (cx + s * 0.25, cy + s * 0.5), (cx + s * 0.14, cy), (cx - s * 0.14, cy)], fill=hex_rgba('#7A3A4A'))
    pen.circle(cx, cy - s * 0.15, s * 0.2, fill=hex_rgba('#E6DCD0'))
    pen.rect(cx - s * 0.24, cy - s * 0.36, cx + s * 0.24, cy - s * 0.12, fill=hex_rgba('#3A2A1E'), r=s * 0.1)
    for sx in (-1, 1):
        pen.circle(cx + sx * s * 0.07, cy - s * 0.15, s * 0.04, fill=INK)
    pen.line([(cx - s * 0.05, cy - s * 0.03), (cx + s * 0.05, cy - s * 0.03)], hex_rgba('#7A2020'), s * 0.02)


def p_key(pen, c, s, p, t):
    cx, cy = c
    col = hex_rgba('#B8A27A')
    pen.circle(cx - s * 0.25, cy, s * 0.14, outline=col, width=s * 0.06)
    pen.line([(cx - s * 0.11, cy), (cx + s * 0.35, cy)], col, s * 0.06)
    pen.line([(cx + s * 0.25, cy), (cx + s * 0.25, cy + s * 0.1)], col, s * 0.05)
    pen.line([(cx + s * 0.33, cy), (cx + s * 0.33, cy + s * 0.12)], col, s * 0.05)


def p_joss_paper(pen, c, s, p, t):
    cx, cy = c
    rnd = random.Random(3)
    for i in range(int(p.get('count', 4))):
        x = cx + (rnd.random() - 0.5) * s
        y = cy + (rnd.random() - 0.5) * s * 0.4
        a = rnd.uniform(-25, 25)
        w, h = s * 0.28, s * 0.18
        ca, sa = math.cos(math.radians(a)), math.sin(math.radians(a))
        pts = [(x + dx * ca - dy * sa, y + dx * sa + dy * ca) for dx, dy in ((-w, -h), (w, -h), (w, h), (-w, h))]
        pen.poly(pts, fill=hex_rgba('#D9B23A'))
        pen.circle(x, y, s * 0.06, fill=hex_rgba('#B8402A'))


def p_box(pen, c, s, p, t):
    cx, cy = c
    pen.rect(cx - s * 0.4, cy - s * 0.3, cx + s * 0.4, cy + s * 0.3, fill=hex_rgba('#6A5640'), outline=hex_rgba('#4A3B2C'), width=s * 0.03)
    pen.line([(cx - s * 0.4, cy - s * 0.05), (cx + s * 0.4, cy - s * 0.05)], hex_rgba('#C9B48A'), s * 0.05)


def p_chair(pen, c, s, p, t):
    cx, cy = c
    col = hex_rgba('#3A2E25')
    pen.rect(cx - s * 0.3, cy, cx + s * 0.3, cy + s * 0.06, fill=col)
    pen.rect(cx - s * 0.3, cy - s * 0.6, cx - s * 0.24, cy + s * 0.5, fill=col)
    pen.rect(cx + s * 0.24, cy, cx + s * 0.3, cy + s * 0.5, fill=col)
    pen.rect(cx - s * 0.3, cy - s * 0.6, cx + s * 0.05, cy - s * 0.54, fill=col)


def p_shadow_figure(pen, c, s, p, t):
    """Standing silhouette far away (background prop)."""
    cx, cy = c
    col = hex_rgba('#030405')
    h = s * 1.6
    pen.circle(cx, cy - h * 0.42, s * 0.13, fill=col)
    pen.poly([(cx - s * 0.14, cy - h * 0.34), (cx + s * 0.14, cy - h * 0.34), (cx + s * 0.2, cy + h * 0.2), (cx - s * 0.2, cy + h * 0.2)], fill=col)
    pen.line([(cx - s * 0.06, cy + h * 0.15), (cx - s * 0.07, cy + h * 0.5)], col, s * 0.08)
    pen.line([(cx + s * 0.06, cy + h * 0.15), (cx + s * 0.07, cy + h * 0.5)], col, s * 0.08)
    if p.get('eyes', True):
        for sx in (-1, 1):
            pen.circle(cx + sx * s * 0.045, cy - h * 0.43, s * 0.018, fill=hex_rgba('#F2EEE0'))


def p_face_window(pen, c, s, p, t):
    cx, cy = c
    pen.ellipse(cx, cy, s * 0.3, s * 0.38, fill=hex_rgba('#D8D4CC', 230))
    for sx in (-1, 1):
        pen.ellipse(cx + sx * s * 0.11, cy - s * 0.05, s * 0.07, s * 0.09, fill=INK)
    pen.ellipse(cx, cy + s * 0.2, s * 0.06, s * 0.03, fill=INK)
    for sx in (-1, 1):
        pen.ellipse(cx + sx * s * 0.42, cy + s * 0.15, s * 0.1, s * 0.16, fill=hex_rgba('#D8D4CC', 210))


def p_coffee(pen, c, s, p, t):
    cx, cy = c
    pen.poly([(cx - s * 0.18, cy - s * 0.2), (cx + s * 0.18, cy - s * 0.2), (cx + s * 0.14, cy + s * 0.22), (cx - s * 0.14, cy + s * 0.22)],
             fill=hex_rgba('#E2DCCF'))
    pen.rect(cx - s * 0.2, cy - s * 0.26, cx + s * 0.2, cy - s * 0.18, fill=hex_rgba('#3A2A20'), r=s * 0.03)
    pen.rect(cx - s * 0.16, cy - s * 0.02, cx + s * 0.16, cy + s * 0.08, fill=hex_rgba('#8A2A2A'))
    for i in (-1, 0, 1):
        ph = math.sin(t * 2.2 + i) * s * 0.04
        pen.bezier((cx + i * s * 0.07, cy - s * 0.3), (cx + i * s * 0.07 + ph + s * 0.05, cy - s * 0.45),
                   (cx + i * s * 0.07 - ph, cy - s * 0.62), color=(200, 200, 205, 110), width=s * 0.025)


WORLD = {'coffee': p_coffee, 'footprints': p_footprints, 'handprint': p_handprint, 'doll': p_doll, 'key': p_key,
         'joss_paper': p_joss_paper, 'box': p_box, 'chair': p_chair, 'shadow_figure': p_shadow_figure,
         'face_window': p_face_window}


# ------------------------------------------------------------------ glowing props
def g_eyes(pen, c, s, p, t):
    cx, cy = c
    col = hex_rgba(p.get('color', '#F2EEE0'))
    blink = ((t + p.get('seed', 0)) % 3.1) < 0.12
    for sx in (-1, 1):
        x = cx + sx * s * 0.16
        pen.circle(x, cy, s * 0.16, fill=(col[0], col[1], col[2], 30))
        if blink:
            pen.line([(x - s * 0.06, cy), (x + s * 0.06, cy)], col, s * 0.02)
        else:
            pen.ellipse(x, cy, s * 0.055, s * 0.035, fill=col)


def g_candle(pen, c, s, p, t):
    cx, cy = c
    pen.rect(cx - s * 0.08, cy - s * 0.1, cx + s * 0.08, cy + s * 0.4, fill=hex_rgba('#D8D0BC'))
    k = 1 + 0.12 * math.sin(t * 13) + 0.06 * math.sin(t * 29)
    pen.circle(cx, cy - s * 0.26, s * 0.3, fill=(255, 190, 90, 40))
    pen.ellipse(cx, cy - s * 0.24 * k, s * 0.05, s * 0.12 * k, fill=hex_rgba('#FFC64A'))
    pen.ellipse(cx, cy - s * 0.2 * k, s * 0.025, s * 0.06 * k, fill=hex_rgba('#FFF6D0'))


def g_lantern(pen, c, s, p, t):
    cx, cy = c
    col = hex_rgba(p.get('color', '#C8102E'))
    pen.circle(cx, cy, s * 0.6, fill=(col[0], col[1], col[2], 35))
    pen.ellipse(cx, cy, s * 0.3, s * 0.38, fill=col)
    for i in range(-2, 3):
        pen.line([(cx + i * s * 0.1, cy - s * 0.36), (cx + i * s * 0.12, cy + s * 0.36)], shade(col, 0.6), s * 0.02)
    pen.rect(cx - s * 0.14, cy - s * 0.46, cx + s * 0.14, cy - s * 0.36, fill=hex_rgba('#1A1A1A'))
    pen.rect(cx - s * 0.14, cy + s * 0.36, cx + s * 0.14, cy + s * 0.44, fill=hex_rgba('#1A1A1A'))


def g_clock(pen, c, s, p, t):
    cx, cy = c
    pen.rect(cx - s * 0.55, cy - s * 0.25, cx + s * 0.55, cy + s * 0.25, fill=hex_rgba('#0B0C0E'), r=s * 0.06)
    txt = p.get('text', '3:07')
    blink = p.get('blink', True) and (t % 1.0) < 0.5
    col = hex_rgba(p.get('color', '#FF3B30'))
    pen.text((cx, cy), txt if not blink else txt.replace(':', ' '), _font('bold', s * 0.36), fill=col)


def g_phone(pen, c, s, p, t):
    cx, cy = c
    w, h = s * 0.32, s * 0.6
    pen.circle(cx, cy, s * 0.7, fill=(150, 200, 255, 22))
    pen.rect(cx - w, cy - h, cx + w, cy + h, fill=hex_rgba('#0D0F12'), r=s * 0.06)
    pen.rect(cx - w * 0.88, cy - h * 0.9, cx + w * 0.88, cy + h * 0.9, fill=hex_rgba(p.get('screen', '#A9D2F5')), r=s * 0.04)
    if p.get('text'):
        pen.text((cx, cy - h * 0.5), p['text'], _font('bold', s * 0.14), fill=hex_rgba('#0E1014'))
    if p.get('sub'):
        pen.text((cx, cy - h * 0.3), p['sub'], _font('body', s * 0.07), fill=hex_rgba('#22303A'))


def g_tv_static(pen, c, s, p, t):
    cx, cy = c
    w, h = s * 0.8, s * 0.55
    pen.rect(cx - w, cy - h, cx + w, cy + h, fill=hex_rgba('#0B0D10'), r=s * 0.05)
    rnd = random.Random(int(t * 24))
    cell = s * 0.05
    y = cy - h * 0.9
    while y < cy + h * 0.9:
        x = cx - w * 0.92
        while x < cx + w * 0.92:
            v = rnd.randint(60, 230)
            pen.rect(x, y, x + cell, y + cell, fill=(v, v, v, 255))
            x += cell
        y += cell


def g_lighter(pen, c, s, p, t):
    g_candle(pen, c, s * 0.8, p, t)


GLOW = {'eyes': g_eyes, 'candle': g_candle, 'lantern': g_lantern, 'clock': g_clock, 'phone': g_phone,
        'tv_static': g_tv_static, 'lighter': g_lighter}


# ------------------------------------------------------------------ inserts (overlays)
def i_chat(pen, c, s, p, t):
    """Phone close-up with chat messages. p['messages'] = [{'from':'them'|'me','text':...}]"""
    cx, cy = c
    w, h = s * 1.05, s * 1.7
    pen.rect(cx - w / 2 - 14, cy - h / 2 - 14, cx + w / 2 + 14, cy + h / 2 + 14, fill=hex_rgba('#0A0B0D'), r=s * 0.09)
    pen.rect(cx - w / 2, cy - h / 2, cx + w / 2, cy + h / 2, fill=hex_rgba('#14161B'), r=s * 0.07)
    head = p.get('contact', 'Unknown')
    pen.rect(cx - w / 2, cy - h / 2, cx + w / 2, cy - h / 2 + s * 0.17, fill=hex_rgba('#1E2128'), r=s * 0.07)
    pen.text((cx, cy - h / 2 + s * 0.09), head, _font('bold', s * 0.075), fill=hex_rgba('#E8E8E8'))
    msgs = p.get('messages') or [{'from': 'them', 'text': p.get('text', 'Are you awake?')}]
    reveal = p.get('_reveal', len(msgs))
    y = cy - h / 2 + s * 0.26
    fnt = _font('body', s * 0.07)
    for m in msgs[:max(0, int(reveal))]:
        me = m.get('from') == 'me'
        lines = textfx.wrap_words([(x_, 0) for x_ in m['text'].split()], fnt, w * 0.7)
        bh = len(lines) * s * 0.088 + s * 0.04
        bw = max(fnt.getlength(' '.join(x_[0] for x_ in ln)) for ln in lines) + s * 0.06
        x0 = cx + w / 2 - s * 0.05 - bw if me else cx - w / 2 + s * 0.05
        pen.rect(x0, y, x0 + bw, y + bh, fill=hex_rgba('#2E7CF6' if me else '#2A2E36'), r=s * 0.035)
        for i, ln in enumerate(lines):
            pen.text((x0 + s * 0.03, y + s * 0.02 + i * s * 0.088), ' '.join(x_[0] for x_ in ln), fnt, fill=hex_rgba('#F2F2F2'), anchor='la')
        y += bh + s * 0.04
    if p.get('typing') and (t % 0.9) < 0.6:
        pen.rect(cx - w / 2 + s * 0.05, y, cx - w / 2 + s * 0.22, y + s * 0.08, fill=hex_rgba('#2A2E36'), r=s * 0.035)
        for i in range(3):
            pen.circle(cx - w / 2 + s * 0.09 + i * s * 0.045, y + s * 0.04, s * 0.012, fill=hex_rgba('#A0A4AC'))


def i_note(pen, c, s, p, t):
    cx, cy = c
    w, h = s * 1.2, s * 0.8
    a = math.radians(p.get('tilt', -3))
    ca, sa = math.cos(a), math.sin(a)
    pts = [(cx + dx * ca - dy * sa, cy + dx * sa + dy * ca) for dx, dy in ((-w / 2, -h / 2), (w / 2, -h / 2), (w / 2, h / 2), (-w / 2, h / 2))]
    pen.poly([(x + 10, y + 12) for x, y in pts], fill=(0, 0, 0, 120))
    pen.poly(pts, fill=PAPER)
    fnt = _font('type', s * 0.075)
    lines = p.get('text', 'DON\'T TURN AROUND').split('\n')
    for i, ln in enumerate(lines):
        pen.text((cx, cy - h * 0.25 + i * s * 0.11), ln, fnt, fill=hex_rgba(p.get('ink', '#2A1C14')))


def i_rules(pen, c, s, p, t):
    cx, cy = c
    rules = p.get('rules') or p.get('text', '1. Lock the door.\n2. Do not answer.').split('\n')
    fnt = _font('type', s * 0.075)
    tw = max(fnt.getlength(r) for r in rules) if rules else s
    w = max(s * 1.2, tw + s * 0.2)
    h = s * (0.34 + 0.12 * len(rules))
    pen.rect(cx - w / 2 + 12, cy - h / 2 + 14, cx + w / 2 + 12, cy + h / 2 + 14, fill=(0, 0, 0, 120))
    pen.rect(cx - w / 2, cy - h / 2, cx + w / 2, cy + h / 2, fill=PAPER)
    pen.text((cx, cy - h / 2 + s * 0.12), p.get('title', 'RULES'), _font('type', s * 0.1), fill=hex_rgba('#2A1C14'))
    hi = p.get('highlight')
    strike = p.get('strike')
    for i, r in enumerate(rules):
        y = cy - h / 2 + s * 0.29 + i * s * 0.12
        col = hex_rgba('#8A1010') if hi is not None and i == int(hi) else hex_rgba('#2A1C14')
        pen.text((cx - w / 2 + s * 0.08, y), r, fnt, fill=col, anchor='lm')
        if strike is not None and i == int(strike):
            for k in range(3):
                pen.line([(cx - w / 2 + s * 0.06, y - s * 0.02 + k * s * 0.02), (cx + w / 2 - s * 0.1, y - s * 0.03 + k * s * 0.02)], hex_rgba('#1A1010'), s * 0.022)


def i_cctv(pen, c, s, p, t):
    """Security / doorbell camera frame. Draws only the HUD; the scene shows through."""
    W, H = pen.w, pen.h
    col = hex_rgba('#F2F2E8')
    m = H * 0.05
    L_ = H * 0.08
    for (x, y, dx, dy) in ((m, m, 1, 1), (W - m, m, -1, 1), (m, H - m, 1, -1), (W - m, H - m, -1, -1)):
        pen.line([(x, y + dy * L_), (x, y), (x + dx * L_, y)], col, H * 0.006)
    if (t % 1.0) < 0.6:
        pen.circle(m + H * 0.05, m + H * 0.06, H * 0.014, fill=hex_rgba('#E53935'))
    fnt = _font('bold', H * 0.04)
    pen.text((m + H * 0.08, m + H * 0.06), p.get('label', 'REC'), fnt, fill=col, anchor='lm')
    pen.text((W - m - H * 0.02, H - m - H * 0.05), p.get('text', '03:07:14 AM'), fnt, fill=col, anchor='rm')
    pen.text((m + H * 0.02, H - m - H * 0.05), p.get('cam', 'FRONT DOOR'), fnt, fill=col, anchor='lm')


def i_polaroid(pen, c, s, p, t):
    cx, cy = c
    w, h = s * 0.8, s * 0.95
    a = math.radians(p.get('tilt', 4))
    ca, sa = math.cos(a), math.sin(a)

    def R(dx, dy):
        return (cx + dx * ca - dy * sa, cy + dx * sa + dy * ca)
    pen.poly([R(-w / 2, -h / 2), R(w / 2, -h / 2), R(w / 2, h / 2), R(-w / 2, h / 2)], fill=hex_rgba('#E8E4DA'))
    pen.poly([R(-w / 2 + 16, -h / 2 + 16), R(w / 2 - 16, -h / 2 + 16), R(w / 2 - 16, h * 0.22), R(-w / 2 + 16, h * 0.22)], fill=hex_rgba('#3A4250'))
    pen.poly([R(-w / 2 + 16, h * 0.05), R(w / 2 - 16, h * 0.0), R(w / 2 - 16, h * 0.22), R(-w / 2 + 16, h * 0.22)], fill=hex_rgba('#2A2E28'))
    for sx in (-0.18, 0.14):
        hx, hy = R(w * sx, -h * 0.12)
        pen.circle(hx, hy, s * 0.05, fill=hex_rgba('#C9BCA8'))
        x0, y0 = R(w * sx - s * 0.05, -h * 0.07)
        x1, y1 = R(w * sx + s * 0.05, h * 0.12)
        pen.rect(min(x0, x1), min(y0, y1), max(x0, x1), max(y0, y1), fill=hex_rgba('#5A4A40'))
    sx, sy = R(w * 0.34, -h * 0.18)
    pen.circle(sx, sy, s * 0.03, fill=hex_rgba('#050506'))
    pen.rect(sx - s * 0.035, sy + s * 0.02, sx + s * 0.035, sy + s * 0.2, fill=hex_rgba('#050506'))
    if p.get('text'):
        pen.text(R(0, h * 0.36), p['text'], _font('type', s * 0.07), fill=hex_rgba('#2A2A2A'))


def i_caption_card(pen, c, s, p, t):
    """Big text card on black ('3 HOURS EARLIER', chapter titles)."""
    cx, cy = c
    fnt = _font(p.get('font', 'display'), s * 0.22)
    pen.text((cx, cy), p.get('text', '3 HOURS EARLIER'), fnt, fill=hex_rgba(p.get('color', '#EDEAE0')))


INSERT = {'chat': i_chat, 'note': i_note, 'rules': i_rules, 'cctv': i_cctv, 'polaroid': i_polaroid,
          'card': i_caption_card}

ALIASES = {'messages': 'chat', 'text_message': 'chat', 'texts': 'chat', 'sms': 'chat', 'paper': 'note', 'letter': 'note',
           'rule_list': 'rules', 'list': 'rules', 'doorbell': 'cctv', 'doorbell_camera': 'cctv', 'camera': 'cctv',
           'security_camera': 'cctv', 'photo': 'polaroid', 'picture': 'polaroid', 'alarm_clock': 'clock',
           'digital_clock': 'clock', 'cellphone': 'phone', 'smartphone': 'phone', 'tv': 'tv_static', 'static': 'tv_static',
           'glowing_eyes': 'eyes', 'eyes_in_dark': 'eyes', 'red_lantern': 'lantern', 'silhouette': 'shadow_figure',
           'figure': 'shadow_figure', 'shadow': 'shadow_figure', 'face': 'face_window', 'money_for_the_dead': 'joss_paper',
           'yellow_paper': 'joss_paper', 'cup': 'coffee', 'mug': 'coffee', 'coffee_cup': 'coffee', 'hand': 'handprint', 'title': 'card', 'text_card': 'card'}


def resolve(name):
    n = (name or '').strip().lower().replace(' ', '_').replace('-', '_')
    n = ALIASES.get(n, n)
    for group, d in (('world', WORLD), ('glow', GLOW), ('insert', INSERT)):
        if n in d:
            return n, group, True
    return 'eyes', 'glow', False


def render(p, s, t, S=2, full=None):
    """Return (tile, cx, cy). Inserts of type cctv need full=(W,H)."""
    name, group, _ = resolve(p.get('type'))
    fn = {**WORLD, **GLOW, **INSERT}[name]
    if name == 'cctv':
        W, H = full
        pen = Pen(W, H, S)
        fn(pen, (W / 2, H / 2), s, p, t)
        return pen.done(), W / 2, H / 2
    size = s * (2.2 if group == 'insert' else 2.0)
    if name == 'rules':
        size = s * 3.2
    pen = Pen(size, size, S)
    fn(pen, (size / 2, size / 2), s, p, t)
    return pen.done(), size / 2, size / 2


# ------------------------------------------------------------------ scare entities (full-screen pops)
def scare_face(W, H, kind='face', t=0.0, S=1):
    """Big frightening (but non-gory) face/shape filling the frame."""
    pen = Pen(W, H, S)
    cx, cy = W / 2, H * 0.52
    r = H * 0.42
    if kind in ('face', 'pale_face'):
        pen.ellipse(cx, cy, r * 0.78, r, fill=hex_rgba('#E2DED6'))
        for sx in (-1, 1):
            pen.ellipse(cx + sx * r * 0.3, cy - r * 0.15, r * 0.17, r * 0.22, fill=hex_rgba('#050506'))
            pen.circle(cx + sx * r * 0.3, cy - r * 0.15, r * 0.035, fill=hex_rgba('#F4F0E4'))
        pen.ellipse(cx, cy + r * 0.45, r * 0.2, r * 0.26, fill=hex_rgba('#050506'))
        for sx in (-1, 1):
            pen.line([(cx + sx * r * 0.55, cy - r * 0.6), (cx + sx * r * 0.3, cy - r * 0.42)], (90, 85, 80, 160), r * 0.02)
    elif kind == 'smile':
        pen.rect(0, 0, W, H, fill=hex_rgba('#030304'))
        w = r * 1.3
        pts = [(cx + w * math.cos(math.radians(a)), cy + r * 0.05 + r * 0.42 * math.sin(math.radians(a))) for a in range(5, 176, 5)]
        pen.poly(pts, fill=hex_rgba('#E8E2D4'))
        for i in range(1, 16):
            x = cx - w + i * 2 * w / 16
            pen.line([(x, cy), (x, cy + r * 0.3 * math.sin(math.pi * i / 16) + r * 0.02)], hex_rgba('#030304'), r * 0.025)
        for sx in (-1, 1):
            pen.circle(cx + sx * r * 0.55, cy - r * 0.45, r * 0.07, fill=hex_rgba('#E8E2D4'))
    elif kind == 'shadow':
        pen.rect(0, 0, W, H, fill=(0, 0, 0, 0))
        col = hex_rgba('#020203')
        pen.circle(cx, cy - r * 0.35, r * 0.55, fill=col)
        pen.poly([(cx - r * 1.4, H), (cx - r * 0.5, cy + r * 0.1), (cx + r * 0.5, cy + r * 0.1), (cx + r * 1.4, H)], fill=col)
        for sx in (-1, 1):
            pen.circle(cx + sx * r * 0.2, cy - r * 0.4, r * 0.05, fill=hex_rgba('#F2EEE0'))
    elif kind == 'eyes':
        pen.rect(0, 0, W, H, fill=hex_rgba('#020203'))
        for sx in (-1, 1):
            pen.circle(cx + sx * r * 0.42, cy - r * 0.1, r * 0.3, fill=(230, 40, 30, 40))
            pen.ellipse(cx + sx * r * 0.42, cy - r * 0.1, r * 0.16, r * 0.1, fill=hex_rgba('#FF3A2A'))
            pen.circle(cx + sx * r * 0.42, cy - r * 0.1, r * 0.04, fill=hex_rgba('#160303'))
    elif kind == 'hand':
        col = hex_rgba('#D8D2C8')
        pen.ellipse(cx, cy + r * 0.3, r * 0.45, r * 0.5, fill=col)
        for i, a in enumerate((-38, -14, 6, 26)):
            ra = math.radians(a)
            ln = r * (1.05 if i in (1, 2) else 0.9)
            pen.line([(cx + math.sin(ra) * r * 0.2, cy), (cx + math.sin(ra) * ln, cy - math.cos(ra) * ln + r * 0.2)], col, r * 0.16)
        pen.line([(cx + r * 0.38, cy + r * 0.35), (cx + r * 0.8, cy)], col, r * 0.16)
    return pen.done()


def library():
    return {'world_props': sorted(WORLD), 'glow_props': sorted(GLOW), 'inserts': sorted(INSERT), 'aliases': ALIASES,
            'scares': ['jumpscare', 'reveal', 'lights_out', 'stinger', 'glitch'],
            'scare_entities': ['face', 'smile', 'shadow', 'eyes', 'hand']}
