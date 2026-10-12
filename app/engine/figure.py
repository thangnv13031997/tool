"""Level-3 stick figures for horror: stick limbs with clothes, hair and big expressive eyes.

Units: u = figure height / 104. Angles in degrees, 0 = pointing down,
+90 = pointing to the side the figure faces, 180 = up.
The skeleton and pose system are shared with Relatable Studio; the drawing is new.
"""
import math
from .gfx import Pen, hex_rgba, shade, mix, lerp

# ---------------------------------------------------------------- skeleton
THIGH = 18.0
SHIN = 18.0
TORSO = 27.0
UPPER = 15.0
FORE = 14.0
HEAD_R = 15.5
ARM_W = 4.0        # sleeve thickness (u)
LEG_W = 4.6
LINE_DARK = hex_rgba('#0E1116')

# Drawing styles. 'stick' = thin stick limbs, small head (the original look).
# 'chibi' = big round head with ears, chunky outlined body, short legs (Relatable-style mascot).
STYLES = {
    'stick': dict(thigh=THIGH, shin=SHIN, torso=TORSO, upper=UPPER, fore=FORE, head_r=HEAD_R,
                  arm_w=ARM_W, leg_w=LEG_W, wt=8.0, wb=6.8, ears=False, ink=0.0, shoe=(3.8, 1.9)),
    'chibi': dict(thigh=12.0, shin=11.0, torso=25.0, upper=12.5, fore=11.5, head_r=18.0,
                  arm_w=8.4, leg_w=8.8, wt=14.0, wb=14.3, ears=True, ink=0.65, shoe=(5.4, 4.0)),
}
STYLE_ALIASES = {'stickman': 'stick', 'thin': 'stick', 'classic': 'stick',
                 'mascot': 'chibi', 'chunky': 'chibi', 'cute': 'chibi', 'relatable': 'chibi'}
DEFAULT_STYLE = 'chibi'   # people; entities (ghosts, shadows...) stay 'stick' so they read as wrong


def resolve_style(name):
    n = (name or '').strip().lower()
    n = STYLE_ALIASES.get(n, n)
    return n if n in STYLES else None

BASE = dict(lean=0, head=0, fu=16, fl=8, bu=-16, bl=-8, lfu=7, lfl=3, lbu=-7, lbl=-3,
            rot=0, air=0, look=0.0, lookup=0.0)


def P(**kw):
    d = dict(BASE)
    d.update(kw)
    return d


SEAT = dict(lfu=90, lfl=0, lbu=84, lbl=-4)
CROUCH = dict(lfu=70, lfl=-60, lbu=60, lbl=-70)

POSES = {
    # everyday
    'idle':        (P(), [('fl', 3, 0.35, 0), ('bl', -3, 0.35, 0)], {}),
    'stand':       (P(), [], {}),
    'talk':        (P(fu=34, fl=96), [('fl', 14, 1.0, 0), ('fu', 5, 1.0, 0.5)], {}),
    'explain':     (P(fu=48, fl=112, bu=-48, bl=-112), [('fl', 10, 0.9, 0), ('bl', -10, 0.9, 1.4)], {}),
    'wave':        (P(fu=108, fl=138), [('fl', 16, 2.2, 0)], {}),
    'point':       (P(fu=88, fl=90, look=1.0), [('fu', 2, 0.6, 0)], {}),
    'think':       (P(fu=42, fl=165, bu=18, bl=84, head=6, lookup=1.0), [('head', 2, 0.4, 0)], {}),
    'shrug':       (P(fu=62, fl=150, bu=-62, bl=-150, head=-6), [], {}),
    'sad':         (P(lean=8, head=16, fu=5, fl=0, bu=-5, bl=0), [('head', 1.5, 0.3, 0)], {}),
    'laugh':       (P(fu=14, fl=78, bu=-24, bl=-30, lean=-8, head=-8), [], {'hop': 1.2, 'hop_hz': 3.5}),
    'phone':       (P(fu=22, fl=142, head=12, lookup=-0.8), [('head', 1.5, 0.4, 0)], {'hold': 'phone'}),
    'call':        (P(fu=28, fl=176, head=4), [], {'hold': 'phone_ear'}),
    'read':        (P(fu=24, fl=118, bu=-24, bl=-118, head=12, lookup=-0.8), [], {'hold': 'paper'}),
    'drink':       (P(fu=26, fl=168, head=-6), [], {'hold': 'cup'}),
    'tired':       (P(lean=9, head=18, fu=4, fl=-2, bu=-4, bl=2), [('lean', 2, 0.35, 0)], {}),
    'cross_arms':  (P(fu=32, fl=-78, bu=-32, bl=78), [], {}),
    'hands_on_hips': (P(fu=52, fl=-32, bu=-52, bl=32, lfu=10, lbu=-10), [], {}),
    'knock':       (P(fu=82, fl=150), [('fl', 18, 3.0, 0)], {}),
    'open_door':   (P(fu=80, fl=80, lean=4), [], {}),
    'reach':       (P(fu=92, fl=92, lean=8, look=1.0), [('fu', 2, 0.5, 0)], {}),
    'walk':        (P(), [], {'cycle': 'walk'}),
    'sneak':       (P(lean=12, head=-4, fu=40, fl=100, bu=20, bl=80), [], {'cycle': 'sneak'}),
    'run':         (P(lean=14), [], {'cycle': 'run'}),
    'run_scared':  (P(lean=16), [], {'cycle': 'run', 'arms_up': True}),
    'sit':         (P(**SEAT), [('fl', 3, 0.35, 0)], {'seat': True}),
    'sit_talk':    (P(**SEAT, fu=40, fl=105), [('fl', 12, 1.0, 0)], {'seat': True}),
    'sit_phone':   (P(**SEAT, fu=24, fl=140, head=14, lookup=-0.8), [], {'seat': True, 'hold': 'phone'}),
    'sit_scared':  (P(**SEAT, fu=30, fl=150, bu=-30, bl=-150, lean=-4), [], {'seat': True, 'tremble': 0.4}),
    'drive':       (P(**SEAT, fu=70, fl=96, bu=60, bl=90, lean=-4), [('fl', 2, 0.6, 0)], {'seat': True, 'wheel': True}),
    'type':        (P(**SEAT, fu=58, fl=96, bu=40, bl=92, head=8), [('fl', 8, 4.0, 0), ('bl', 8, 4.0, 1.6)], {'seat': True}),
    'lie':         (P(fu=4, fl=2, bu=-4, bl=-2, lfu=3, lfl=2, lbu=-3, lbl=-2), [], {'bed': True}),
    'sleep':       (P(fu=4, fl=2, bu=-4, bl=-2, lfu=3, lfl=2, lbu=-3, lbl=-2), [], {'bed': True}),
    'lie_awake':   (P(fu=4, fl=2, bu=-4, bl=-2, lfu=3, lfl=2, lbu=-3, lbl=-2), [], {'bed': True, 'blanket_up': True}),
    # fear
    'hug_self':    (P(fu=34, fl=-100, bu=-34, bl=100, head=6, lfu=4, lbu=-4), [], {'tremble': 0.25}),
    'scared':      (P(fu=70, fl=150, bu=40, bl=130, lean=-8, lfu=12, lbu=-12), [], {'tremble': 0.6}),
    'terrified':   (P(fu=60, fl=172, bu=-60, bl=-172, lean=-10, lfu=14, lbu=-14), [], {'tremble': 0.8}),
    'freeze':      (P(fu=10, fl=4, bu=-10, bl=-4, lfu=4, lbu=-4), [], {}),
    'back_away':   (P(lean=-12, fu=78, fl=70, bu=60, bl=60, look=0.0), [], {'cycle': 'back'}),
    'cover_mouth': (P(fu=40, fl=170, head=4, lean=-4), [], {'tremble': 0.3, 'hand_mouth': True}),
    'shush':       (P(fu=36, fl=172, head=2), [], {'hand_mouth': True}),
    'listen':      (P(fu=40, fl=178, head=-8, look=-0.6), [], {}),
    'peek':        (P(lean=18, head=-10, fu=60, fl=100, look=1.0), [], {}),
    'look_back':   (P(lean=6, head=-6, look=-1.0, fu=16, fl=8), [], {'look_back': True}),
    'hold_head':   (P(fu=58, fl=176, bu=-58, bl=-176, head=4), [], {'tremble': 0.4}),
    'crouch':      (P(**CROUCH, lean=18, head=-6, fu=30, fl=60, bu=-20, bl=40), [], {'low': 22.0}),
    'hide':        (P(**CROUCH, lean=30, head=14, fu=70, fl=176, bu=-70, bl=-176), [], {'low': 24.0, 'tremble': 0.3}),
    'cower':       (P(lfu=120, lfl=-10, lbu=110, lbl=-20, lean=20, head=16, fu=70, fl=40, bu=60, bl=30), [], {'floor': True, 'tremble': 0.35}),
    'flashlight':  (P(fu=82, fl=86, lean=4, look=1.0), [('fu', 1.5, 0.5, 0)], {'hold': 'flashlight'}),
    'phone_light': (P(fu=80, fl=96, lean=2, look=1.0), [], {'hold': 'phone_out'}),
    'scream':      (P(fu=58, fl=176, bu=-58, bl=-176, lean=-10, head=-14, lookup=0.6), [], {'tremble': 0.9}),
    # entities (used by 'type' characters)
    'loom':        (P(fu=8, fl=4, bu=-8, bl=-4, head=8), [('head', 1.2, 0.2, 0)], {}),
    'stand_far':   (P(fu=4, fl=2, bu=-4, bl=-2), [], {}),
    'wave_slow':   (P(fu=100, fl=130), [('fl', 10, 0.5, 0)], {}),
}

ALIASES = {
    'stand_still': 'stand', 'speak': 'talk', 'talking': 'talk', 'gesture': 'explain',
    'thinking': 'think', 'worry': 'hug_self', 'worried': 'hug_self', 'stressed': 'hold_head',
    'panic': 'terrified', 'walking': 'walk', 'running': 'run', 'run_away': 'run_scared', 'flee': 'run_scared',
    'walk_in': 'walk', 'enter': 'walk', 'exit': 'walk', 'sitting': 'sit', 'lying': 'lie',
    'sleeping': 'sleep', 'reading': 'read', 'typing': 'type', 'texting': 'phone',
    'arms_crossed': 'cross_arms', 'fear': 'scared', 'afraid': 'scared', 'shock': 'scared', 'shocked': 'scared',
    'hugging_arms': 'hug_self', 'standing_hugging_arms': 'hug_self', 'cold': 'hug_self',
    'hiding': 'hide', 'crouching': 'crouch', 'peeking': 'peek', 'stiff': 'freeze', 'frozen': 'freeze',
    'look_behind': 'look_back', 'turn_around': 'look_back', 'whisper': 'shush', 'quiet': 'shush',
    'torch': 'flashlight', 'phone_flashlight': 'phone_light', 'driving': 'drive', 'step_back': 'back_away',
    'sneaking': 'sneak', 'tiptoe': 'sneak', 'screaming': 'scream', 'curl_up': 'cower', 'knees': 'cower',
    'open': 'open_door', 'reach_out': 'reach', 'awake_in_bed': 'lie_awake', 'in_bed': 'lie_awake',
}

POSE_EMOTION = {
    'sad': 'sad', 'laugh': 'laugh', 'scared': 'scared', 'terrified': 'terrified', 'tired': 'tired',
    'sleep': 'sleep', 'think': 'thinking', 'hold_head': 'scared', 'hug_self': 'uneasy', 'freeze': 'terrified',
    'back_away': 'scared', 'cover_mouth': 'terrified', 'shush': 'uneasy', 'listen': 'suspicious',
    'peek': 'suspicious', 'look_back': 'uneasy', 'crouch': 'scared', 'hide': 'terrified', 'cower': 'terrified',
    'scream': 'terrified', 'run_scared': 'terrified', 'sit_scared': 'scared', 'lie_awake': 'scared',
    'sneak': 'uneasy', 'loom': 'blank', 'stand_far': 'blank', 'wave_slow': 'creepy_smile',
}


def resolve_pose(name):
    n = (name or 'idle').strip().lower().replace(' ', '_').replace('-', '_')
    if n in POSES:
        return n, True
    if n in ALIASES:
        return ALIASES[n], True
    return 'idle', False


def pose_angles(name, t, seed=0.0):
    base, osc, ex = POSES[name]
    a = dict(base)
    for key, amp, hz, ph in osc:
        a[key] = a[key] + amp * math.sin(2 * math.pi * hz * t + ph + seed)
    cyc = ex.get('cycle')
    if cyc:
        hz = {'walk': 1.7, 'run': 2.6, 'sneak': 1.1, 'back': 1.2}[cyc]
        amp = {'walk': 24, 'run': 38, 'sneak': 18, 'back': 14}[cyc]
        p = 2 * math.pi * hz * t + seed
        s1, s2 = math.sin(p), math.sin(p + math.pi)
        lift = 40 if cyc == 'run' else 14
        a['lfu'] = amp * s1
        a['lfl'] = a['lfu'] - lift * max(0.0, math.cos(p))
        a['lbu'] = amp * s2
        a['lbl'] = a['lbu'] - lift * max(0.0, math.cos(p + math.pi))
        if cyc in ('walk', 'run'):
            arm = 20 if cyc == 'walk' else 40
            bend = 18 if cyc == 'walk' else 75
            a['fu'] = arm * s2 + 6
            a['fl'] = a['fu'] + bend
            a['bu'] = arm * s1 - 6
            a['bl'] = a['bu'] + bend
            if ex.get('arms_up'):
                a['fu'] = 70 + 25 * s2
                a['fl'] = 150 + 20 * s2
                a['bu'] = -60 + 25 * s1
                a['bl'] = -150 + 20 * s1
    if ex.get('hop'):
        hz = ex.get('hop_hz', 2.2)
        a['air'] = ex['hop'] * abs(math.sin(math.pi * hz * t + seed))
    if ex.get('tremble'):
        a['tremble'] = ex['tremble'] * math.sin(2 * math.pi * 11 * t + seed)
    return a


def blend(a, b, w):
    out = dict(b)
    for k in BASE:
        if k in a and k in b:
            out[k] = lerp(a[k], b[k], w)
    return out


# ---------------------------------------------------------------- expressions
EXPR = {
    'neutral':     dict(eyes='open', pupil=1.0, brows='flat', mouth='flat'),
    'calm':        dict(eyes='open', pupil=1.0, brows=None, mouth='smile_small'),
    'happy':       dict(eyes='happy', brows=None, mouth='smile'),
    'relieved':    dict(eyes='half', brows='sad', mouth='smile_small'),
    'laugh':       dict(eyes='happy', brows=None, mouth='open_smile'),
    'thinking':    dict(eyes='open', pupil=1.0, brows='one_up', mouth='side'),
    'uneasy':      dict(eyes='open', pupil=0.9, brows='worried', mouth='flat'),
    'suspicious':  dict(eyes='narrow', pupil=1.0, brows='angry', mouth='side'),
    'worried':     dict(eyes='open', pupil=0.85, brows='worried', mouth='wavy', extras=['sweat']),
    'scared':      dict(eyes='wide', pupil=0.6, brows='worried', mouth='wavy', extras=['sweat']),
    'terrified':   dict(eyes='wide', pupil=0.4, brows='worried', mouth='o_big', extras=['sweat', 'pale']),
    'shocked':     dict(eyes='wide', pupil=0.5, brows='raised', mouth='o'),
    'sad':         dict(eyes='open', pupil=1.0, brows='sad', mouth='frown'),
    'cry':         dict(eyes='squeeze', brows='sad', mouth='wail', extras=['tears']),
    'angry':       dict(eyes='narrow', pupil=1.0, brows='angry', mouth='grit'),
    'tired':       dict(eyes='half', brows=None, mouth='flat', extras=['bags']),
    'sleep':       dict(eyes='closed', brows=None, mouth='flat'),
    'confused':    dict(eyes='open', pupil=1.0, brows='one_up', mouth='side'),
    'determined':  dict(eyes='narrow', pupil=1.0, brows='angry', mouth='flat'),
    # entity faces
    'blank':       dict(eyes='black', brows=None, mouth='none'),
    'creepy_smile': dict(eyes='black', brows=None, mouth='wide_smile'),
    'stare':       dict(eyes='stare', pupil=0.3, brows=None, mouth='flat'),
    'glow':        dict(eyes='glow', brows=None, mouth='none'),
}
EXPR_ALIASES = {'fear': 'scared', 'afraid': 'scared', 'panic': 'terrified', 'horrified': 'terrified',
                'shock': 'shocked', 'surprised': 'shocked', 'nervous': 'worried', 'anxious': 'worried',
                'mad': 'angry', 'crying': 'cry', 'upset': 'sad', 'curious': 'thinking', 'confident': 'calm',
                'smile': 'happy', 'exhausted': 'tired', 'empty': 'blank', 'possessed': 'blank',
                'grin': 'creepy_smile', 'staring': 'stare', 'creepy': 'creepy_smile', 'alert': 'suspicious',
                'unsure': 'uneasy', 'tense': 'uneasy', 'whisper': 'uneasy', 'slow': 'uneasy', 'relaxed': 'calm'}


def resolve_expr(name):
    n = (name or '').strip().lower()
    if n in EXPR:
        return n, True
    if n in EXPR_ALIASES:
        return EXPR_ALIASES[n], True
    return 'neutral', n == ''


# ---------------------------------------------------------------- look
HAIRS = ['none', 'short', 'messy', 'side_part', 'curly', 'long', 'ponytail', 'bun', 'bob', 'buzz']
OUTFITS = ['hoodie', 'jacket', 'tshirt', 'sweater', 'raincoat', 'coat', 'dress', 'uniform', 'pajamas', 'suit', 'flannel',
           'scrubs', 'apron', 'hi_vis', 'overalls']
WEARS = ['glasses', 'cap', 'beanie', 'beard', 'mustache', 'backpack', 'scarf', 'name_tag', 'hood_up', 'bus_cap']
SKINS = ['#EAD8C3', '#D9B99B', '#B88A66', '#8D5E3E', '#F2E2D0']
TYPES = ['person', 'driver', 'shadow', 'silhouette', 'raincoat_man', 'pale_man', 'tall_figure', 'mimic', 'child_ghost']


class Look:
    def __init__(self, spec=None):
        spec = spec or {}
        self.name = spec.get('name', 'Someone')
        self.type = spec.get('type', 'person')
        self.age = spec.get('age', 'adult')
        self.hair = spec.get('hair', 'short')
        self.hair_color = hex_rgba(spec.get('hair_color', '#2B1E17'))
        self.outfit = spec.get('outfit', 'hoodie')
        self.outfit_color = hex_rgba(spec.get('outfit_color', '#3A4A63'))
        self.pants_color = hex_rgba(spec.get('pants_color', '#232B38'))
        self.shoe_color = hex_rgba(spec.get('shoe_color', '#15181D'))
        self.skin = hex_rgba(spec.get('skin', '#EAD8C3'))
        # second colour of an outfit: apron, vest stripes, overall bib...
        self.accent_color = hex_rgba(spec.get('accent_color', {'apron': '#E9E4D8', 'hi_vis': '#D9F23A',
                                                               'overalls': '#3D5A80'}.get(self.outfit, '#D8D2C0')))
        self.wear = [w for w in spec.get('wear', []) if w]
        self.scale = {'kid': 0.68, 'teen': 0.9, 'elder': 0.96}.get(self.age, 1.0) * float(spec.get('size', 1.0))
        style = resolve_style(spec.get('style'))
        if style is None:
            style = 'stick' if self.type not in ('person', 'driver') else (resolve_style(spec.get('default_style')) or DEFAULT_STYLE)
        self.style = style
        self.d = STYLES[style]
        self.head_r = self.d['head_r'] * (1.16 if self.age == 'kid' else 1.0)
        self.eye_color = hex_rgba(spec.get('eye_color', '#F5F1E8'))
        if self.age == 'elder' and spec.get('hair_color') is None:
            self.hair_color = hex_rgba('#A8A8A8')
        # entity presets
        t = self.type
        if t == 'driver':
            self.outfit = spec.get('outfit', 'uniform')
            self.outfit_color = hex_rgba(spec.get('outfit_color', '#2E3B4E'))
            if 'bus_cap' not in self.wear:
                self.wear.append('bus_cap')
        elif t in ('shadow', 'silhouette', 'tall_figure'):
            self.skin = hex_rgba('#07080B')
            self.outfit = 'coat'
            self.outfit_color = hex_rgba('#07080B')
            self.pants_color = hex_rgba('#07080B')
            self.shoe_color = hex_rgba('#07080B')
            self.hair = 'none'
            self.eye_color = hex_rgba(spec.get('eye_color', '#FFFFFF' if t != 'shadow' else '#E8E2D0'))
            if t == 'tall_figure':
                self.scale *= 1.35
        elif t == 'raincoat_man':
            self.outfit = 'raincoat'
            self.outfit_color = hex_rgba(spec.get('outfit_color', '#C9A227'))
            if 'hood_up' not in self.wear:
                self.wear.append('hood_up')
            self.skin = hex_rgba(spec.get('skin', '#CFC6B8'))
        elif t == 'pale_man':
            self.skin = hex_rgba('#E9E6E0')
            self.outfit = spec.get('outfit', 'suit')
            self.outfit_color = hex_rgba(spec.get('outfit_color', '#1A1D22'))
            self.hair = spec.get('hair', 'side_part')
        elif t == 'child_ghost':
            self.age = 'kid'
            self.scale = 0.68
            self.head_r = self.d['head_r'] * 1.16
            self.skin = hex_rgba('#DCE3E8')
            self.outfit = 'dress'
            self.outfit_color = hex_rgba('#C9D2D8')
            self.hair = spec.get('hair', 'long')
            self.hair_color = hex_rgba('#14161A')
        self.entity = t not in ('person', 'driver')


# ---------------------------------------------------------------- geometry
def vec(a, f):
    r = math.radians(a)
    return (f * math.sin(r), math.cos(r))


def add(p, v, k):
    return (p[0] + v[0] * k, p[1] + v[1] * k)


def skeleton(a, f, look, ex=None):
    ex = ex or {}
    d = look.d
    thigh, shin, torso, upper, fore = d['thigh'], d['shin'], d['torso'], d['upper'], d['fore']
    hip = (0.0, -(thigh + shin))
    kf = add(hip, vec(a['lfu'], f), thigh)
    ff = add(kf, vec(a['lfl'], f), shin)
    kb = add(hip, vec(a['lbu'], f), thigh)
    fb = add(kb, vec(a['lbl'], f), shin)
    lean = a['lean']
    up = vec(180 - lean, f)
    neck = add(hip, up, torso)
    sh = add(hip, up, torso - 4)
    ef = add(sh, vec(a['fu'] - lean, f), upper)
    hf = add(ef, vec(a['fl'] - lean, f), fore)
    eb = add(sh, vec(a['bu'] - lean, f), upper)
    hb = add(eb, vec(a['bl'] - lean, f), fore)
    head = add(neck, vec(180 - lean - a['head'], f), look.head_r + 1.0)
    pts = dict(hip=hip, kf=kf, ff=ff, kb=kb, fb=fb, neck=neck, sh=sh, ef=ef, hf=hf, eb=eb, hb=hb, head=head,
               hip_f=hip, hip_b=hip, sh_f=sh, sh_b=sh)
    low = max(ff[1], fb[1])
    if ex.get('floor'):
        low = hip[1] + 4
    dy = -low - a.get('air', 0.0)
    dx = a.get('tremble', 0.0)
    for k in pts:
        pts[k] = (pts[k][0] + dx, pts[k][1] + dy)
    if ex.get('hand_mouth'):
        hc = pts['head']
        r = look.head_r
        pts['hf'] = (hc[0] + f * r * 0.35, hc[1] + r * 0.45)
        pts['ef'] = (hc[0] + f * r * 0.9, hc[1] + r * 1.6)
    return pts


def _spread_limbs(pts, a, f, look, ex):
    """Move each arm/leg chain sideways so it starts at the edge of a wide torso (chibi style)."""
    pts = dict(pts)
    arm = look.d['wt'] * 0.92
    leg = look.d['wb'] * 0.42
    groups = ((1, arm, ('sh_f', 'ef', 'hf'), None), (-1, arm, ('sh_b', 'eb', 'hb'), None),
              (1, leg, ('hip_f', 'kf', 'ff'), 'lfu'), (-1, leg, ('hip_b', 'kb', 'fb'), 'lbu'))
    for side, k, keys, ang in groups:
        if ang:
            # a leg swung forward (sitting) is seen from the side: no sideways offset
            k *= max(0.0, math.cos(math.radians(a[ang])))
        if keys[0] == 'sh_f' and ex.get('hand_mouth'):
            keys = keys[:1]          # the hand stays on the mouth
        for key in keys:
            x, y = pts[key]
            pts[key] = (x + side * f * k, y)
        if keys[0].startswith('sh'):
            x, y = pts[keys[0]]
            pts[keys[0]] = (x - side * f * 1.2, y + 2.2)
    return pts


def rotate_pts(pts, center, deg):
    r = math.radians(deg)
    c, s = math.cos(r), math.sin(r)
    out = {}
    for k, (x, y) in pts.items():
        x0, y0 = x - center[0], y - center[1]
        out[k] = (center[0] + x0 * c - y0 * s, center[1] + x0 * s + y0 * c)
    return out


# ---------------------------------------------------------------- drawing
TILE_W = 170.0
TILE_TOP = 140.0
TILE_BOT = 12.0


def tile_size(u):
    return int(TILE_W * u), int((TILE_TOP + TILE_BOT) * u)


_HEAD_CACHE = {}


def head_height(look, pose):
    """Head centre height above the ground in figure units (u, before look.scale). Used for camera framing."""
    key = (look.style, look.head_r, pose)
    if key not in _HEAD_CACHE:
        ex = POSES[pose][2]
        if ex.get('bed'):
            h = 22.0
        else:
            pts = skeleton(pose_angles(pose, 0.0), 1, look, ex)
            h = -pts['head'][1]
        _HEAD_CACHE[key] = h
    return _HEAD_CACHE[key] * look.scale


def draw_figure(look, pose, angles, facing, emotion, mouth_open=0.0, blink=False,
                t=0.0, u=6.0, S=2, shadow=True, rim=None):
    """Draw one figure on a transparent tile. Returns (image, anchor_x, anchor_y)."""
    u = u * look.scale
    W, H = tile_size(u)
    pen = Pen(W, H, S)
    ox, oy = W / 2.0, TILE_TOP * u
    f = 1 if facing >= 0 else -1
    a = angles
    ex = POSES[pose][2]
    pts = skeleton(a, f, look, ex)

    def U(p):
        return (ox + p[0] * u, oy + p[1] * u)

    if ex.get('bed'):
        _draw_bed(pen, look, pts, f, a, emotion, mouth_open, blink, t, u, ox, oy, ex)
        return pen.done(), ox, oy

    if shadow and not look.entity:
        pen.ellipse(ox, oy + 0.8 * u, 19 * u, 2.8 * u, fill=(0, 0, 0, 70))
    if ex.get('seat') and not ex.get('wheel'):
        _draw_seat(pen, ox, oy, u, f)

    entity = look.type in ('shadow', 'silhouette', 'tall_figure')
    outline = None if entity else LINE_DARK
    hc = U(pts['head'])
    hr = look.head_r * u
    _hair_back(pen, look, hc, hr, f, u)
    if 'backpack' in look.wear:
        s = U(pts['sh'])
        h = U(pts['hip'])
        bx = (s[0] + h[0]) / 2 - f * 8 * u
        pen.rect(bx - 6 * u, s[1] + 2 * u, bx + 6 * u, h[1] - 2 * u, fill=shade(look.outfit_color, 0.55), r=3 * u)

    chibi = look.d['ink'] and not look.entity
    if chibi:
        # chunky body: limbs hang at the sides of the torso, not from its centre line
        pts = _spread_limbs(pts, a, f, look, ex)
    # back limbs
    _leg(pen, look, U(pts['hip_b']), U(pts['kb']), U(pts['fb']), f, u, back=True)
    _arm(pen, look, U(pts['sh_b']), U(pts['eb']), U(pts['hb']), u, back=True)
    if chibi:
        _leg(pen, look, U(pts['hip_f']), U(pts['kf']), U(pts['ff']), f, u, back=False)
    # torso
    _torso(pen, look, pts, U, f, u, t)
    if not chibi:
        _leg(pen, look, U(pts['hip_f']), U(pts['kf']), U(pts['ff']), f, u, back=False)
    if look.outfit in ('raincoat', 'coat', 'dress'):
        _skirt(pen, look, pts, U, f, u)
    # head
    _ears(pen, look, hc, hr, f, u, outline)
    if entity:
        pen.circle(hc[0], hc[1], hr, fill=look.skin)
    elif chibi:
        pen.circle(hc[0], hc[1], hr, fill=look.skin, outline=outline, width=look.d['ink'] * u)
        _head_shade(pen, look, hc, hr, f)
    else:
        pen.circle(hc[0], hc[1], hr, fill=look.skin, outline=outline, width=0.9 * u)
    _hair_front(pen, look, hc, hr, f, u)
    _beard(pen, look, hc, hr, f, u)
    face_dir = -f if ex.get('look_back') else f
    _face(pen, look, hc, hr, face_dir, a, emotion, mouth_open, blink, t, u)
    _wear_head(pen, look, hc, hr, f, u)
    # front arm and held item
    if ex.get('wheel'):
        _draw_wheel(pen, U(pts['hf']), U(pts['hb']), f, u)
    _arm(pen, look, U(pts['sh_f']), U(pts['ef']), U(pts['hf']), u, back=False)
    hold = ex.get('hold')
    if hold:
        _held(pen, hold, U(pts['hf']), U(pts['hb']), hc, f, u, t)
    img = pen.done()
    return img, ox, oy


def _cubic(p0, p1, p2, p3, n=16):
    out = []
    for i in range(n + 1):
        t = i / n
        a, b, c, d = (1 - t) ** 3, 3 * (1 - t) ** 2 * t, 3 * (1 - t) * t * t, t ** 3
        out.append((a * p0[0] + b * p1[0] + c * p2[0] + d * p3[0], a * p0[1] + b * p1[1] + c * p2[1] + d * p3[1]))
    return out


def _chain(*segs):
    out = []
    for sg in segs:
        out += sg if not out else sg[1:]
    return out


def _tube(pts, w0, w1):
    """Outline of a tapered tube along a polyline (half widths w0 -> w1)."""
    left, right = [], []
    n = len(pts)
    for i in range(n):
        a, b = pts[max(0, i - 1)], pts[min(n - 1, i + 1)]
        dx, dy = b[0] - a[0], b[1] - a[1]
        L = math.hypot(dx, dy) or 1
        nx, ny = -dy / L, dx / L
        w = w0 + (w1 - w0) * i / max(1, n - 1)
        left.append((pts[i][0] + nx * w, pts[i][1] + ny * w))
        right.append((pts[i][0] - nx * w, pts[i][1] - ny * w))
    def cap(p, q, w):
        ang = math.atan2(p[1] - q[1], p[0] - q[0])
        return [(p[0] + w * math.cos(ang + math.pi / 2 - math.pi * j / 8), p[1] + w * math.sin(ang + math.pi / 2 - math.pi * j / 8))
                for j in range(1, 8)]
    return left + cap(pts[-1], pts[-2], w1) + list(reversed(right)) + cap(pts[0], pts[1], w0)


def _bend(a, b, c, n=16):
    """Smooth curve from a to c that bends at joint b."""
    return _cubic(a, (a[0] + (b[0] - a[0]) * 0.9, a[1] + (b[1] - a[1]) * 0.9),
                  (c[0] + (b[0] - c[0]) * 0.9, c[1] + (b[1] - c[1]) * 0.9), c, n)


def _ears(pen, look, hc, r, f, u, outline):
    if not look.d['ears'] or look.entity or 'hood_up' in look.wear or look.hair in ('long', 'bob'):
        return
    ink = look.d['ink'] * u
    for s in (-1, 1):
        x = hc[0] + s * r * 0.97 + f * r * 0.04
        pen.ellipse(x, hc[1] + r * 0.1, r * 0.17, r * 0.22, fill=look.skin, outline=outline, width=ink)
        pen.arc(x + s * r * 0.01, hc[1] + r * 0.1, r * 0.07, r * 0.11, -90 if s > 0 else 90, 90 if s > 0 else 270,
                shade(look.skin, 0.7), ink * 0.9)


def _head_shade(pen, look, hc, r, f):
    """Soft crescent of shadow on the far side of a round head."""
    cx, cy = hc
    s = -f
    pen.poly(_chain(_cubic((cx + s * r * 0.5, cy - r * 0.86), (cx + s * r * 1.04, cy - r * 0.35), (cx + s * r * 1.02, cy + r * 0.5), (cx + s * r * 0.4, cy + r * 0.91)),
                    _cubic((cx + s * r * 0.4, cy + r * 0.91), (cx + s * r * 0.84, cy + r * 0.4), (cx + s * r * 0.88, cy - r * 0.3), (cx + s * r * 0.5, cy - r * 0.86))),
             fill=shade(look.skin, 0.93))


def _torso_mascot(pen, look, hip, up, nrm, f, u, ink):
    """Soft one-piece top (hoodie silhouette) in the torso's own frame: x across, y up from the hip."""
    d = look.d
    col = look.outfit_color
    dk = shade(col, 0.78)
    upx, upy = up                 # unit vector hip -> shoulder

    def T(x, y):
        return (hip[0] + nrm[0] * x * u + upx * y * u, hip[1] + nrm[1] * x * u + upy * y * u)

    def TT(pts):
        return [T(x, y) for x, y in pts]
    SW, HW = d['wt'], d['wb']
    yN, yH = d['torso'] - 0.3, -2.0
    half = _chain(_cubic((-5.5, yN), (-SW * 0.9, yN + 0.1), (-SW * 1.08, yN - 2.5), (-SW * 1.04, yN - 10)),
                  _cubic((-SW * 1.04, yN - 10), (-HW * 1.03, yH + 6.5), (-HW * 1.04, yH + 0.5), (-HW * 0.9, yH - 1)))
    body = half + [(-x, y) for x, y in reversed(half)]
    pen.poly(TT(body), fill=col, outline=LINE_DARK, width=ink)
    sb = -f   # shadow on the far side
    pen.poly(TT(_chain(_cubic((sb * HW * 0.5, yN - 3.5), (sb * HW * 0.98, yN - 8), (sb * HW * 1.02, yH + 8), (sb * HW * 0.82, yH + 1)),
                       _cubic((sb * HW * 0.82, yH + 1), (sb * HW * 0.8, yH + 8), (sb * HW * 0.82, yN - 9), (sb * HW * 0.5, yN - 3.5)))),
             fill=shade(col, 0.9))
    o = look.outfit
    if o in ('hoodie', 'sweater', 'pajamas', 'tshirt', 'flannel', 'scrubs', 'hi_vis', 'overalls', 'apron'):
        # waistband / hem
        pen.poly(TT([(-HW * 0.9, yH - 1), (HW * 0.9, yH - 1), (HW * 0.93, yH + 2.4), (-HW * 0.93, yH + 2.4)]),
                 fill=shade(col, 0.85), outline=LINE_DARK, width=ink * 0.8)
    if o == 'hoodie' and 'hood_up' not in look.wear:
        pen.poly(TT([(-6.2, yH + 11), (6.2, yH + 11), (8.2, yH + 3.6), (-8.2, yH + 3.6)]), fill=shade(col, 0.93),
                 outline=dk, width=ink * 0.9)
        hood = _cubic((-10.8, yN + 0.3), (-10, yN - 6.2), (10, yN - 6.2), (10.8, yN + 0.3))
        pen.poly(TT(hood), fill=dk, outline=LINE_DARK, width=ink)
        pen.ellipse(*T(0, yN - 1), 4.2 * u, 1.8 * u, fill=hex_rgba('#F2F2F2'))
        for s in (-1, 1):
            pen.line(TT([(s * 2.5, yN - 3.2), (s * 2.8, yN - 9.5)]), hex_rgba('#F2F2F2'), ink * 1.1)


def _arm_chibi(pen, look, sh, el, hand, u, w, sleeve, skin):
    ink = look.d['ink'] * u
    hw = w / 2
    path = _bend(sh, el, hand)
    if look.outfit in ('tshirt', 'dress', 'scrubs'):
        n = len(path) // 2
        pen.poly(_tube(path[n - 1:], hw * 0.62, hw * 0.55), fill=skin, outline=LINE_DARK, width=ink)
        pen.poly(_tube(path[:n + 1], hw, hw * 0.9), fill=sleeve, outline=LINE_DARK, width=ink)
    else:
        pen.poly(_tube(path, hw, hw * 0.8), fill=sleeve, outline=LINE_DARK, width=ink)
        if look.outfit == 'flannel':
            pen.line(path[len(path) // 2:], shade(sleeve, 0.8), w * 0.25)
    a, b = path[-3], path[-1]
    L = math.hypot(b[0] - a[0], b[1] - a[1]) or 1
    hx, hy = b[0] + (b[0] - a[0]) / L * hw * 0.6, b[1] + (b[1] - a[1]) / L * hw * 0.6
    pen.circle(hx, hy, hw * 0.78, fill=skin, outline=LINE_DARK, width=ink)


def _limb_colors(look, back):
    k = (0.86 if look.d['ink'] and not look.entity else 0.72) if back else 1.0
    return shade(look.outfit_color, k), shade(look.pants_color, k), shade(look.skin, 0.85 if back else 1.0)


def _arm(pen, look, sh, el, hand, u, back):
    sleeve, _, skin = _limb_colors(look, back)
    w = look.d['arm_w'] * u
    if look.d['ink'] and not look.entity:
        _arm_chibi(pen, look, sh, el, hand, u, w, sleeve, skin)
        return
    if look.outfit in ('tshirt', 'dress') and not look.entity:
        mid = (sh[0] + (el[0] - sh[0]) * 0.55, sh[1] + (el[1] - sh[1]) * 0.55)
        if not back:
            pen.line([sh, mid], shade(sleeve, 0.55), w * 1.05 + 0.9 * u)
            pen.line([mid, el, hand], shade(skin, 0.6), w * 0.62 + 0.7 * u)
        pen.line([sh, mid], sleeve, w * 1.05)
        pen.line([mid, el, hand], skin, w * 0.62)
    else:
        if not back and not look.entity:
            pen.line([sh, el, hand], shade(sleeve, 0.55), w + 0.9 * u)
        pen.line([sh, el, hand], sleeve, w)
        if look.outfit == 'flannel':
            pen.line([el, hand], shade(sleeve, 0.8), w * 0.35)
    pen.circle(hand[0], hand[1], w * 0.55, fill=skin)


def _leg(pen, look, hip, knee, foot, f, u, back):
    _, pants, _ = _limb_colors(look, back)
    w = look.d['leg_w'] * u
    shoe = shade(look.shoe_color, 0.8 if back else 1.0)
    if look.d['ink'] and not look.entity:
        ink = look.d['ink'] * u
        sx, sy = look.d['shoe']
        L = math.hypot(foot[0] - knee[0], foot[1] - knee[1]) or 1
        end = (foot[0] - (foot[0] - knee[0]) / L * 2.2 * u, foot[1] - (foot[1] - knee[1]) / L * 2.2 * u)
        path = _bend(hip, knee, end)
        pen.poly(_tube(path, w / 2, w * 0.44), fill=pants, outline=LINE_DARK, width=ink)
        bx, by = foot[0] + f * 1.3 * u, foot[1] + 0.5 * u
        dome = [(bx + sx * u * math.cos(math.radians(a_)), by - sy * u * math.sin(math.radians(a_)) ** 0.8) for a_ in range(0, 181, 10)]
        pen.poly(dome, fill=shoe, outline=LINE_DARK, width=ink)
        pen.poly([(bx - sx * u, by - 0.9 * u), (bx + sx * u, by - 0.9 * u), (bx + sx * u, by), (bx - sx * u, by)],
                 fill=shade(shoe, 1.35), outline=LINE_DARK, width=ink * 0.8)
        return
    if not back and not look.entity:
        pen.line([hip, knee, foot], shade(pants, 0.6), w + 0.8 * u)
    pen.line([hip, knee, foot], pants, w)
    shoe = shade(look.shoe_color, 0.8 if back else 1.0)
    pen.ellipse(foot[0] + f * 2.2 * u, foot[1] + 0.4 * u, 3.8 * u, 1.9 * u, fill=shoe)


def _torso(pen, look, pts, U, f, u, t):
    sh = U(pts['sh'])
    hip = U(pts['hip'])
    neck = U(pts['neck'])
    col = look.outfit_color
    dx, dy = sh[0] - hip[0], sh[1] - hip[1]
    L = math.hypot(dx, dy) or 1
    nx, ny = -dy / L, dx / L     # normal
    wt, wb = look.d['wt'] * u, look.d['wb'] * u
    k = wt / (8.0 * u)          # detail scale relative to the stick style
    top = (sh[0] - dx * 0.12, sh[1] - dy * 0.12)
    bot = (hip[0] - dx * 0.05, hip[1] - dy * 0.05)

    ink = 0 if look.entity else look.d['ink'] * u
    o = look.outfit
    cx = (top[0] + bot[0]) / 2
    if ink:
        _torso_mascot(pen, look, hip, (dx / L, dy / L), (nx, ny), f, u, ink)
        if o == 'hoodie':
            return
    else:
        body = [(top[0] + nx * wt, top[1] + ny * wt), (top[0] - nx * wt, top[1] - ny * wt),
                (bot[0] - nx * wb, bot[1] - ny * wb), (bot[0] + nx * wb, bot[1] + ny * wb)]
        if look.outfit == 'hoodie' or 'hood_up' in look.wear:
            if 'hood_up' not in look.wear:
                pen.ellipse(neck[0] - f * 2.5 * u, neck[1] + 1.0 * u, 6.5 * u, 3.6 * u, fill=shade(col, 0.75))
        pen.poly(body, fill=col)
        pen.circle(top[0], top[1] + 0.5 * u, wt * 0.98, fill=col)
    if look.entity and look.type in ('shadow', 'silhouette', 'tall_figure'):
        return
    if o == 'hoodie':
        pen.rect(cx - 4.2 * u, bot[1] - 8 * u, cx + 4.2 * u, bot[1] - 3.5 * u, fill=shade(col, 0.82), r=1.5 * u)
        for s in (-1, 1):
            pen.line([(neck[0] + s * 1.6 * u, neck[1] + 2 * u), (neck[0] + s * 1.9 * u, neck[1] + 8 * u)],
                     shade(col, 1.35), 0.55 * u)
    elif o == 'jacket':
        pen.poly([(neck[0] - 2.4 * u, neck[1] + 1.5 * u), (neck[0] + 2.4 * u, neck[1] + 1.5 * u),
                  (cx + 1.6 * u, bot[1]), (cx - 1.6 * u, bot[1])], fill=hex_rgba('#C9C4BA'))
        pen.line([(neck[0] - 2.4 * u, neck[1] + 1.5 * u), (cx - 1.6 * u, bot[1])], shade(col, 0.7), 0.8 * u)
        pen.line([(neck[0] + 2.4 * u, neck[1] + 1.5 * u), (cx + 1.6 * u, bot[1])], shade(col, 0.7), 0.8 * u)
    elif o == 'uniform':
        pen.line([(neck[0], neck[1] + 1 * u), (cx, bot[1])], shade(col, 0.7), 0.6 * u)
        for i in range(3):
            pen.circle(neck[0] + (cx - neck[0]) * (0.25 + 0.25 * i), neck[1] + 4 * u + i * 5.5 * u, 0.5 * u, fill=shade(col, 1.5))
        if 'name_tag' in look.wear or look.type == 'driver':
            pen.rect(cx + f * 1.5 * u, neck[1] + 4.5 * u, cx + f * 5.5 * u, neck[1] + 6.5 * u, fill=hex_rgba('#D8D2C0'), r=0.4 * u)
    elif o == 'sweater':
        for i in range(2):
            y = bot[1] - (1.5 + i * 1.6) * u
            pen.line([(cx - 5.5 * u, y), (cx + 5.5 * u, y)], shade(col, 0.8), 0.5 * u)
    elif o == 'suit':
        pen.poly([(neck[0] - 2 * u, neck[1] + 1.2 * u), (neck[0] + 2 * u, neck[1] + 1.2 * u), (cx, neck[1] + 11 * u)],
                 fill=hex_rgba('#E6E3DC'))
        pen.poly([(neck[0] - 0.7 * u, neck[1] + 2.5 * u), (neck[0] + 0.7 * u, neck[1] + 2.5 * u), (cx, neck[1] + 10 * u)],
                 fill=hex_rgba('#5E1016'))
    elif o == 'flannel':
        for i in range(3):
            x = cx - 4 * u + i * 4 * u
            pen.line([(x, neck[1] + 2 * u), (x, bot[1])], shade(col, 0.7), 0.6 * u)
        for i in range(3):
            y = neck[1] + 4 * u + i * 6 * u
            pen.line([(cx - 6 * u, y), (cx + 6 * u, y)], shade(col, 0.72), 0.6 * u)
    elif o == 'pajamas':
        for i in range(4):
            pen.circle(cx - 3 * u + (i % 2) * 6 * u, neck[1] + 5 * u + i * 4 * u, 0.9 * u, fill=shade(col, 1.25))
    elif o == 'scrubs':
        pen.poly([(neck[0] - 2.6 * u * k, neck[1] + 1.2 * u), (neck[0] + 2.6 * u * k, neck[1] + 1.2 * u),
                  (neck[0], neck[1] + 6.5 * u * k)], fill=shade(col, 0.7))
        pen.rect(cx + f * 1.2 * u * k, neck[1] + 7 * u * k, cx + f * 4.6 * u * k, neck[1] + 10.5 * u * k,
                 fill=shade(col, 0.88), r=0.5 * u)
    elif o in ('apron', 'overalls'):
        ac = look.accent_color
        top_y = neck[1] + (5.5 if o == 'apron' else 7.5) * u * k
        bw = (wb * 0.78) if o == 'apron' else (wb * 0.62)
        for s_ in (-1, 1):
            pen.line([(cx + s_ * bw * 0.7, top_y), (neck[0] + s_ * 4.2 * u * k, neck[1] + 0.8 * u)], shade(ac, 0.85), 1.2 * u * k)
        pen.rect(cx - bw, top_y, cx + bw, bot[1] + (6 if o == 'apron' else 1) * u * k, fill=ac, r=1.5 * u * k,
                 outline=LINE_DARK if ink else None, width=ink * 0.6)
        if o == 'overalls':
            for s_ in (-1, 1):
                pen.circle(cx + s_ * bw * 0.65, top_y + 1.4 * u * k, 0.7 * u * k, fill=hex_rgba('#C9B37A'))
        else:
            pen.rect(cx - bw * 0.5, top_y + 6 * u * k, cx + bw * 0.5, top_y + 10 * u * k, fill=shade(ac, 0.9), r=0.6 * u)
    elif o == 'hi_vis':
        ac = look.accent_color
        pen.poly([(neck[0] - 3.5 * u * k, neck[1] + 0.8 * u), (neck[0] - 7 * u * k, neck[1] + 2 * u),
                  (cx - wb * 0.95, bot[1]), (cx + wb * 0.95, bot[1]), (neck[0] + 7 * u * k, neck[1] + 2 * u),
                  (neck[0] + 3.5 * u * k, neck[1] + 0.8 * u), (cx, neck[1] + 9 * u * k)], fill=ac)
        for i in range(2):
            y = bot[1] - (3.5 + i * 5.5) * u * k
            pen.line([(cx - wb * 0.9, y), (cx + wb * 0.9, y)], hex_rgba('#E4E6E8'), 1.4 * u * k)
    elif o == 'raincoat':
        pen.line([(neck[0], neck[1] + 1 * u), (cx, bot[1] + 8 * u)], shade(col, 0.72), 0.6 * u)
        for i in range(3):
            pen.circle(neck[0] + (cx - neck[0]) * (0.2 + 0.3 * i) + f * 1.2 * u, neck[1] + 4 * u + i * 6 * u, 0.6 * u, fill=shade(col, 0.6))


def _skirt(pen, look, pts, U, f, u):
    hip = U(pts['hip'])
    col = look.outfit_color
    k = look.d['wb'] / 6.8
    ln = {'raincoat': 14, 'coat': 16, 'dress': 13}[look.outfit] * u * (look.d['thigh'] + look.d['shin']) / 36.0
    if look.type == 'tall_figure':
        ln *= 1.6
    ink = 0 if look.entity else look.d['ink'] * u
    pen.poly([(hip[0] - 6.4 * u * k, hip[1] - 1.5 * u), (hip[0] + 6.4 * u * k, hip[1] - 1.5 * u),
              (hip[0] + 9.5 * u * k, hip[1] + ln), (hip[0] - 9.5 * u * k, hip[1] + ln)], fill=col,
             outline=LINE_DARK if ink else None, width=ink)


def _draw_seat(pen, ox, oy, u, f):
    col = hex_rgba('#2C333D')
    seat_y = oy - 18 * u
    bx = ox - f * 13 * u
    pen.rect(min(bx, bx - f * 6 * u), seat_y - 30 * u, max(bx, bx - f * 6 * u), seat_y + 2 * u, fill=col, r=2 * u)
    pen.rect(ox - 14 * u, seat_y - 1.6 * u, ox + 14 * u, seat_y + 3 * u, fill=shade(col, 1.15), r=1.5 * u)
    pen.line([(ox, seat_y + 3 * u), (ox, oy)], shade(col, 0.7), 2 * u)


def _draw_wheel(pen, hf, hb, f, u):
    cx = (hf[0] + hb[0]) / 2 + f * 2 * u
    cy = (hf[1] + hb[1]) / 2
    pen.ellipse(cx, cy, 3.2 * u, 9 * u, outline=hex_rgba('#101215'), width=2.2 * u)
    pen.line([(cx, cy), (cx + f * 12 * u, cy + 10 * u)], hex_rgba('#101215'), 2.4 * u)


def _draw_bed(pen, look, pts0, f, a, emotion, mouth_open, blink, t, u, ox, oy, ex):
    bed_top = oy - 20 * u
    x0, x1 = ox - 64 * u, ox + 64 * u
    frame = hex_rgba('#2E2620')
    pen.rect(x0, bed_top, x1, oy - 6 * u, fill=hex_rgba('#3A3029'), r=2 * u)
    pen.line([(x0 + 3 * u, oy - 6 * u), (x0 + 3 * u, oy)], frame, 2.4 * u)
    pen.line([(x1 - 3 * u, oy - 6 * u), (x1 - 3 * u, oy)], frame, 2.4 * u)
    hb = x0 if f > 0 else x1
    pen.rect(hb - 3 * u, bed_top - 24 * u, hb + 3 * u, oy - 6 * u, fill=frame, r=2 * u)
    pen.rect(x0, bed_top - 4 * u, x1, bed_top + 4 * u, fill=hex_rgba('#C8C3B8'), r=3 * u)
    px = x0 + 15 * u if f > 0 else x1 - 15 * u
    pen.ellipse(px, bed_top - 6 * u, 12 * u, 5 * u, fill=hex_rgba('#DDD8CC'))
    pts = rotate_pts(pts0, pts0['hip'], -90 * f)
    head = pts['head']
    target = ((px - ox) / u, (bed_top - 11 * u - oy) / u)
    dx, dy = target[0] - head[0], target[1] - head[1]
    pts = {k: (x + dx, y + dy) for k, (x, y) in pts.items()}
    hc = (ox + pts['head'][0] * u, oy + pts['head'][1] * u)
    hr = look.head_r * u
    _hair_back(pen, look, hc, hr, f, u)
    _ears(pen, look, hc, hr, f, u, LINE_DARK)
    pen.circle(hc[0], hc[1], hr, fill=look.skin, outline=LINE_DARK, width=0.9 * u)
    _hair_front(pen, look, hc, hr, f, u)
    lookup = dict(a)
    lookup['lookup'] = 1.0 if ex.get('blanket_up') else 0.0
    _face(pen, look, hc, hr, f, lookup, emotion, mouth_open, blink, t, u)
    bx0 = hc[0] + f * (hr * (0.35 if ex.get('blanket_up') else 1.0) + 2 * u)
    bx1 = x1 - 3 * u if f > 0 else x0 + 3 * u
    lo, hi = min(bx0, bx1), max(bx0, bx1)
    blanket = shade(look.outfit_color, 0.9)
    top_y = bed_top - (17 if ex.get('blanket_up') else 13) * u
    pen.rect(lo, top_y, hi, bed_top + 6 * u, fill=blanket, r=5 * u)
    if ex.get('blanket_up'):
        pen.ellipse(hc[0] + f * hr * 0.6, hc[1] + hr * 0.75, hr * 0.9, hr * 0.45, fill=blanket)


# ---- hair
def _cap_pts(cx, cy, r, a0, a1, steps=26):
    return [(cx + r * math.cos(math.radians(a0 + (a1 - a0) * i / steps)),
             cy + r * math.sin(math.radians(a0 + (a1 - a0) * i / steps))) for i in range(steps + 1)]


def _hair_back(pen, look, hc, r, f, u):
    h = look.hair
    col = look.hair_color
    cx, cy = hc
    if 'hood_up' in look.wear:
        pen.circle(cx - f * r * 0.12, cy - r * 0.05, r * 1.32, fill=shade(look.outfit_color, 0.8))
        return
    if h == 'long':
        pen.rect(cx - r * 1.1, cy - r * 0.3, cx + r * 1.1, cy + r * (2.4 if look.type == 'child_ghost' else 1.9), fill=col, r=r * 0.6)
    elif h == 'bob':
        pen.rect(cx - r * 1.14, cy - r * 0.4, cx + r * 1.14, cy + r * 1.05, fill=col, r=r * 0.6)
    elif h == 'ponytail':
        bx = cx - f * r * 1.05
        pen.ellipse(bx - f * r * 0.25, cy + r * 0.3, r * 0.4, r * 0.95, fill=col)
    elif h == 'bun':
        pen.circle(cx - f * r * 0.15, cy - r * 1.1, r * 0.45, fill=col)


def _hair_front(pen, look, hc, r, f, u):
    h = look.hair
    if h in ('none', 'bald', '', None) or 'hood_up' in look.wear:
        if 'hood_up' in look.wear:
            col = shade(look.outfit_color, 0.8)
            pen.poly(_cap_pts(hc[0] - f * r * 0.1, hc[1], r * 1.3, 180, 360) +
                     [(hc[0] + r * 1.1, hc[1] - r * 0.25), (hc[0] - r * 1.1, hc[1] - r * 0.25)], fill=col)
        return
    col = look.hair_color
    cx, cy = hc
    R = r * 1.04
    if h == 'curly':
        for i in range(9):
            ang = math.radians(195 + i * 150 / 8)
            pen.circle(cx + R * 0.92 * math.cos(ang), cy + R * 0.92 * math.sin(ang), r * 0.33, fill=col)
        pen.poly(_cap_pts(cx, cy, R, 190, 350), fill=col)
        return
    if h == 'buzz':
        pen.poly(_cap_pts(cx, cy, R, 195, 345) + [(cx + R * 0.94, cy - r * 0.5), (cx - R * 0.94, cy - r * 0.5)], fill=col)
        return
    if h in ('long', 'bob', 'ponytail', 'bun'):
        cap = _cap_pts(cx, cy, R, 178, 362)
        fr = [(cx + R, cy - r * 0.05), (cx + r * 0.2 * f, cy - r * 0.5), (cx - R, cy - r * 0.05)]
        if look.type == 'child_ghost':
            fr = [(cx + R, cy + r * 0.2), (cx, cy + r * 0.05), (cx - R, cy + r * 0.2)]
        pen.poly(cap + fr, fill=col)
        if h in ('long', 'bob'):
            ln = 0.95 if h == 'long' else 0.6
            pen.rect(cx - R - 0.2 * u, cy - r * 0.2, cx - R + r * 0.3, cy + r * ln, fill=col, r=r * 0.15)
            pen.rect(cx + R - r * 0.3, cy - r * 0.2, cx + R + 0.2 * u, cy + r * ln, fill=col, r=r * 0.15)
        return
    if h == 'messy':
        cap = _cap_pts(cx, cy, R, 186, 354)
        pen.poly(cap + [(cx + R * 0.95, cy - r * 0.3), (cx - R * 0.95, cy - r * 0.3)], fill=col)
        for i in range(6):
            ang = math.radians(200 + i * 28)
            bx, by = cx + R * 0.9 * math.cos(ang), cy + R * 0.9 * math.sin(ang)
            tx, ty = cx + R * 1.28 * math.cos(ang + 0.2 * f), cy + R * 1.28 * math.sin(ang + 0.2 * f)
            n = (-math.sin(ang) * r * 0.22, math.cos(ang) * r * 0.22)
            pen.poly([(bx - n[0], by - n[1]), (tx, ty), (bx + n[0], by + n[1])], fill=col)
        return
    if h == 'side_part':
        cap = _cap_pts(cx, cy, R, 185, 355)
        sweep = [(cx + R * 0.98, cy - r * 0.2), (cx + f * r * 0.1, cy - r * 0.62), (cx - f * r * 0.6, cy - r * 0.15)]
        pen.poly(cap + sweep, fill=col)
        return
    cap = _cap_pts(cx, cy, R, 188, 352)
    tuft = [(cx + R * 0.97, cy - r * 0.32), (cx + f * r * 0.5, cy - r * 0.5),
            (cx + f * r * 0.1, cy - r * 0.36), (cx - f * r * 0.4, cy - r * 0.54), (cx - R * 0.97, cy - r * 0.32)]
    pen.poly(cap + tuft, fill=col)


# ---- face
INK = hex_rgba('#121418')
MOUTH_DARK = hex_rgba('#3A0E10')
TEAR = hex_rgba('#7FB3E0')


def _face(pen, look, hc, r, f, a, emotion, mouth_open, blink, t, u):
    spec = EXPR.get(emotion, EXPR['neutral'])
    cx, cy = hc
    mascot = look.style == 'chibi' and not look.entity
    fx = cx + f * r * (0.1 if mascot else 0.22) + a.get('look', 0.0) * r * 0.1 * f
    fy = cy + a.get('head', 0) * 0.01 * r
    look_up = a.get('lookup', 0.0)
    gap = r * 0.34
    ey = fy - r * 0.08
    eyes = spec['eyes']
    if blink and eyes in ('open', 'wide', 'narrow'):
        eyes = 'closed'
    lw = (0.055 if mascot else 0.1) * r
    er = 0.2 * r
    if mascot:
        gap = r * 0.32
        ey = fy + r * 0.06
    pupil_k = spec.get('pupil', 1.0)
    sclera = look.eye_color
    entity_type = look.type
    for s in (-1, 1):
        x = fx + s * gap
        y = ey
        if mascot and eyes in ('open', 'narrow', 'half'):
            # bead eyes with a highlight, like the mascot reference
            ry = er * {'open': 0.52, 'narrow': 0.3, 'half': 0.34}[eyes]
            ex_, ey_ = x + f * er * 0.12, y - look_up * er * 0.25 + (er * 0.12 if eyes == 'half' else 0)
            pen.ellipse(ex_, ey_, er * 0.37, ry, fill=INK)
            pen.circle(ex_ - er * 0.12, ey_ - ry * 0.4, er * 0.13, fill=(255, 255, 255, 255))
            if eyes == 'half':
                pen.line([(ex_ - er * 0.6, ey_ - ry * 0.75), (ex_ + er * 0.6, ey_ - ry * 0.75)], INK, lw)
        elif mascot and eyes in ('wide', 'stare'):
            pen.ellipse(x, y, er * 0.75, er * 0.92, fill=sclera, outline=INK, width=lw * 0.8)
            pen.circle(x + f * er * 0.1, y - look_up * er * 0.25, er * (0.28 if eyes == 'wide' else 0.18) * pupil_k, fill=INK)
        elif eyes == 'open':
            pen.ellipse(x, y, er, er * 1.15, fill=sclera, outline=INK, width=lw * 0.6)
            pen.circle(x + f * er * 0.25, y - look_up * er * 0.35 + er * 0.1, er * 0.55 * pupil_k, fill=INK)
            pen.circle(x + f * er * 0.25 - er * 0.18, y - er * 0.12, er * 0.16, fill=(255, 255, 255, 255))
        elif eyes == 'wide':
            pen.ellipse(x, y - er * 0.1, er * 1.2, er * 1.4, fill=sclera, outline=INK, width=lw * 0.6)
            pen.circle(x + f * er * 0.1, y - look_up * er * 0.3, er * 0.55 * pupil_k, fill=INK)
        elif eyes == 'stare':
            pen.ellipse(x, y, er * 1.15, er * 1.15, fill=sclera, outline=INK, width=lw * 0.5)
            pen.circle(x, y, er * 0.3, fill=INK)
        elif eyes == 'narrow':
            pen.ellipse(x, y + er * 0.15, er, er * 0.6, fill=sclera, outline=INK, width=lw * 0.6)
            pen.circle(x + f * er * 0.2, y + er * 0.18, er * 0.42, fill=INK)
        elif eyes == 'half':
            pen.ellipse(x, y + er * 0.25, er, er * 0.55, fill=sclera, outline=INK, width=lw * 0.6)
            pen.circle(x + f * er * 0.2, y + er * 0.35, er * 0.4, fill=INK)
            pen.line([(x - er * 1.1, y - er * 0.15), (x + er * 1.1, y - er * 0.15)], INK, lw)
        elif eyes == 'happy':
            pen.arc(x, y + er * 0.5, er * 0.9, er * 0.8, 200, 340, INK, lw)
        elif eyes == 'closed':
            pen.arc(x, y - er * 0.2, er * 0.9, er * 0.6, 20, 160, INK, lw)
        elif eyes == 'squeeze':
            pen.line([(x - s * er * 0.8, y - er * 0.6), (x + s * er * 0.7, y), (x - s * er * 0.8, y + er * 0.6)], INK, lw)
        elif eyes == 'black':
            pen.ellipse(x, y, er * 1.05, er * 1.25, fill=hex_rgba('#030304'))
            if entity_type in ('shadow', 'silhouette', 'tall_figure'):
                pen.circle(x, y, er * 0.28, fill=look.eye_color)
        elif eyes == 'glow':
            pen.ellipse(x, y, er * 0.9, er * 0.55, fill=look.eye_color)
    br = spec.get('brows')
    by = ey - r * (0.3 if mascot else 0.4)
    bl = r * (0.13 if mascot else 0.2)
    if br and not look.entity:
        bcol = shade(look.hair_color, 0.8) if look.hair not in ('none',) else INK
        for s in (-1, 1):
            x = fx + s * gap
            inner = -s
            if br in ('sad', 'worried'):
                p0 = (x + inner * bl * 0.3, by - bl * (0.6 if br == 'worried' else 0.45))
                p1 = (x - inner * bl * 1.0, by + bl * 0.15)
            elif br == 'angry':
                p0 = (x + inner * bl * 0.3, by + bl * 0.5)
                p1 = (x - inner * bl * 1.0, by - bl * 0.25)
            elif br == 'raised':
                pen.arc(x, by - bl * 0.2, bl * 1.0, bl * 0.6, 200, 340, bcol, lw * 1.1)
                continue
            elif br == 'one_up':
                if s == f:
                    pen.arc(x, by - bl * 0.35, bl * 1.0, bl * 0.6, 200, 340, bcol, lw * 1.1)
                else:
                    pen.line([(x - bl, by + bl * 0.15), (x + bl, by + bl * 0.15)], bcol, lw * 1.1)
                continue
            else:
                p0 = (x - bl, by + bl * 0.1)
                p1 = (x + bl, by + bl * 0.1)
            pen.line([p0, p1], bcol, lw * 1.1)
    mx = fx + f * r * 0.03
    my = fy + r * 0.45
    mw = r * 0.3
    mouth = spec['mouth']
    if mouth_open > 0.06 and mouth not in ('none', 'wide_smile'):
        k = min(1.0, mouth_open)
        oh = r * (0.05 + 0.2 * k)
        ow = mw * (0.6 + 0.2 * k)
        pen.ellipse(mx, my, ow, oh, fill=MOUTH_DARK, outline=INK, width=lw * 0.5)
    elif mouth == 'smile_small':
        pen.arc(mx, my - mw * 0.35, mw * 0.65, mw * 0.5, 30, 150, INK, lw)
    elif mouth in ('smile', 'open_smile') and mascot:
        pts = _cubic((mx - mw * 0.62, my - mw * 0.15), (mx - mw * 0.48, my + mw * 0.85), (mx + mw * 0.48, my + mw * 0.85), (mx + mw * 0.62, my - mw * 0.15))
        pen.poly(pts, fill=MOUTH_DARK, outline=INK, width=lw * 0.9)
        pen.ellipse(mx, my + mw * 0.42, mw * 0.3, mw * 0.17, fill=hex_rgba('#E8838A'))
    elif mouth == 'smile':
        pen.arc(mx, my - mw * 0.5, mw * 0.9, mw * 0.8, 25, 155, INK, lw)
    elif mouth == 'open_smile':
        pts = [(mx + mw * 0.95 * math.cos(math.radians(i * 10)), my - mw * 0.2 + mw * 0.8 * math.sin(math.radians(i * 10))) for i in range(19)]
        pen.poly(pts, fill=MOUTH_DARK, outline=INK, width=lw * 0.6)
    elif mouth == 'frown':
        pen.arc(mx, my + mw * 0.5, mw * 0.75, mw * 0.5, 205, 335, INK, lw)
    elif mouth == 'flat':
        pen.line([(mx - mw * 0.5, my), (mx + mw * 0.5, my)], INK, lw)
    elif mouth == 'o':
        pen.ellipse(mx, my + mw * 0.1, mw * 0.32, mw * 0.42, fill=MOUTH_DARK, outline=INK, width=lw * 0.5)
    elif mouth == 'o_big':
        pen.ellipse(mx, my + mw * 0.15, mw * 0.45, mw * 0.62, fill=MOUTH_DARK, outline=INK, width=lw * 0.5)
    elif mouth == 'wavy':
        pts = [(mx - mw * 0.7 + i * mw * 1.4 / 12, my + math.sin(i * math.pi / 3) * mw * 0.14) for i in range(13)]
        pen.line(pts, INK, lw)
    elif mouth == 'grit':
        pen.rect(mx - mw * 0.6, my - mw * 0.2, mx + mw * 0.6, my + mw * 0.25, fill=(235, 232, 225, 255), outline=INK, width=lw * 0.6, r=mw * 0.1)
    elif mouth == 'wail':
        pen.ellipse(mx, my + mw * 0.2, mw * 0.65, mw * 0.5, fill=MOUTH_DARK, outline=INK, width=lw * 0.5)
    elif mouth == 'side':
        pen.line([(mx - mw * 0.45, my + mw * 0.1), (mx + f * mw * 0.55, my - mw * 0.12)], INK, lw)
    elif mouth == 'wide_smile':
        w = r * 0.82
        pts = [(cx + w * math.cos(math.radians(a_)), my - r * 0.12 + r * 0.32 * math.sin(math.radians(a_))) for a_ in range(10, 171, 8)]
        pen.poly(pts, fill=hex_rgba('#050506'))
        for i in range(1, 9):
            x = cx - w * 0.8 + i * w * 1.6 / 9
            pen.line([(x, my - r * 0.08), (x, my + r * 0.04)], hex_rgba('#D9D4C8'), r * 0.06)
    extras = spec.get('extras', [])
    if 'sweat' in extras:
        x, y = cx - f * r * 0.8, cy - r * 0.5
        pen.poly([(x, y - r * 0.2), (x + r * 0.1, y + r * 0.02), (x - r * 0.1, y + r * 0.02)], fill=TEAR)
        pen.circle(x, y + r * 0.04, r * 0.1, fill=TEAR)
    if 'tears' in extras:
        ph = (t * 1.5) % 1.0
        for s in (-1, 1):
            x = fx + s * gap
            pen.line([(x, ey + er), (x, ey + r * 0.8)], TEAR, r * 0.08)
            pen.circle(x, ey + r * (0.6 + 0.5 * ph), r * 0.08, fill=TEAR)
    if 'bags' in extras:
        for s in (-1, 1):
            pen.arc(fx + s * gap, ey + er * 1.4, er * 0.9, er * 0.4, 20, 160, (90, 80, 100, 200), lw * 0.6)


def _wear_head(pen, look, hc, r, f, u):
    cx, cy = hc
    mascot = look.style == 'chibi' and not look.entity
    if 'glasses' in look.wear:
        fx = cx + f * r * (0.1 if mascot else 0.22)
        gap = r * (0.32 if mascot else 0.34)
        gy = cy + (r * 0.06 if mascot else -r * 0.08)
        gw = r * (0.045 if mascot else 0.07)
        for s in (-1, 1):
            pen.circle(fx + s * gap, gy, r * 0.22 if mascot else r * 0.27, outline=INK, width=gw)
        pen.line([(fx - gap + r * 0.22, gy - r * 0.02), (fx + gap - r * 0.22, gy - r * 0.02)], INK, gw)
    if 'mustache' in look.wear:
        fx = cx + f * r * (0.12 if mascot else 0.26)
        for s in (-1, 1):
            pen.ellipse(fx + s * r * 0.14, cy + r * 0.3, r * 0.16, r * 0.07, fill=look.hair_color)
    if 'cap' in look.wear or 'bus_cap' in look.wear:
        bus = 'bus_cap' in look.wear
        col = hex_rgba('#1C2533') if bus else hex_rgba('#7A2A22')
        R = r * 1.06
        if not bus:
            cy = cy - r * 0.22
        pen.poly(_cap_pts(cx, cy - r * 0.12, R, 180, 360), fill=col)
        if bus:
            pen.rect(cx - R, cy - r * 0.55, cx + R, cy - r * 0.1, fill=col)
            pen.rect(cx - r * 0.25, cy - r * 0.62, cx + r * 0.25, cy - r * 0.38, fill=hex_rgba('#B8962A'), r=r * 0.05)
        bx = cx + f * R * 0.3
        pen.poly([(bx - f * R * 0.8, cy - r * 0.15), (bx + f * r * 1.05, cy - r * 0.05), (bx + f * r * 1.0, cy + r * 0.08),
                  (bx - f * R * 0.8, cy + (r * 0.02))], fill=shade(col, 0.7))
        if bus:
            # shadow over the eyes: the driver's face stays hidden
            pen.ellipse(cx + f * r * 0.2, cy + r * 0.02, r * 0.95, r * 0.28, fill=(5, 6, 9, 235))
    if 'beanie' in look.wear:
        col = look.outfit_color
        pen.poly(_cap_pts(cx, cy - r * 0.1, r * 1.08, 180, 360), fill=shade(col, 1.1))
        pen.rect(cx - r * 1.1, cy - r * 0.35, cx + r * 1.1, cy - r * 0.05, fill=shade(col, 0.85), r=r * 0.1)
    if 'scarf' in look.wear:
        pen.ellipse(cx - f * r * 0.1, cy + r * 1.15, r * 0.85, r * 0.3, fill=hex_rgba('#7A2630'))


def _beard(pen, look, hc, r, f, u):
    if 'beard' not in look.wear:
        return
    cx, cy = hc
    R = r * 1.02
    top = cy + r * 0.25
    pts = [(cx + R * math.cos(math.radians(i * 180 / 24)), cy + R * math.sin(math.radians(i * 180 / 24))) for i in range(25)]
    pts = [p for p in pts if p[1] >= top]
    if len(pts) > 2:
        pen.poly([(pts[0][0], top)] + pts + [(pts[-1][0], top)], fill=look.hair_color)
    pen.ellipse(cx + f * r * 0.26, cy + r * 0.45, r * 0.24, r * 0.1, fill=look.skin)


# ---- held items
def _held(pen, what, hf, hb, hc, f, u, t):
    x, y = hf
    if what == 'phone':
        pen.rect(x - 2.6 * u, y - 5 * u, x + 2.6 * u, y + 3.6 * u, fill=hex_rgba('#0D0F12'), r=0.9 * u)
        pen.rect(x - 2.0 * u, y - 4.3 * u, x + 2.0 * u, y + 2.9 * u, fill=hex_rgba('#BFE3FF'), r=0.5 * u)
    elif what == 'phone_out':
        pen.rect(x - 1.2 * u, y - 4.5 * u, x + 1.2 * u, y + 2.5 * u, fill=hex_rgba('#0D0F12'), r=0.6 * u)
        pen.circle(x + f * 1.2 * u, y - 3.5 * u, 0.8 * u, fill=hex_rgba('#FFFDE8'))
    elif what == 'phone_ear':
        hx = hc[0] - f * 0.6 * u
        pen.rect(hx - 1.8 * u, y - 5 * u, hx + 1.8 * u, y + 3.5 * u, fill=hex_rgba('#0D0F12'), r=0.8 * u)
    elif what == 'flashlight':
        ex, ey = x + f * 6 * u, y
        pen.line([(x - f * 2 * u, y), (ex, ey)], hex_rgba('#2A2F36'), 2.6 * u)
        pen.rect(min(ex, ex + f * 2.4 * u), ey - 2.1 * u, max(ex, ex + f * 2.4 * u), ey + 2.1 * u, fill=hex_rgba('#3A414B'), r=0.6 * u)
        pen.circle(ex + f * 2.4 * u, ey, 1.6 * u, fill=hex_rgba('#FFF6D0'))
    elif what == 'paper':
        cx = (hf[0] + hb[0]) / 2
        cy = (hf[1] + hb[1]) / 2 - 3 * u
        pen.rect(cx - 7 * u, cy - 9 * u, cx + 7 * u, cy + 6 * u, fill=hex_rgba('#D8D0BC'), r=0.6 * u)
        for i in range(5):
            pen.line([(cx - 5 * u, cy - 6 * u + i * 2.6 * u), (cx + 4.5 * u, cy - 6 * u + i * 2.6 * u)], hex_rgba('#6B6455'), 0.45 * u)
    elif what == 'cup':
        pen.rect(x - 2.6 * u, y - 5 * u, x + 2.6 * u, y + 1.5 * u, fill=hex_rgba('#C9C2B4'), r=0.6 * u)


def library():
    return {
        'poses': sorted(POSES.keys()),
        'pose_aliases': ALIASES,
        'emotions': sorted(EXPR.keys()),
        'hair': HAIRS,
        'styles': list(STYLES),
        'outfits': OUTFITS,
        'wear': WEARS,
        'types': TYPES,
        'age': ['adult', 'teen', 'kid', 'elder'],
    }
