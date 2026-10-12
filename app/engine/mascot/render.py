"""Render a mascot character tile (PIL RGBA) with resvg: action + expression + lip-sync + blink + blending."""
import io, math, re
from collections import OrderedDict
from PIL import Image
from . import art, actions as A, looks

try:
    import resvg_py
except ImportError:          # pragma: no cover - reported by the script check / setup
    resvg_py = None

GROUND = None                # set from the first assembled character
CHAR_UNITS = 1086.0          # head top to ground of a 'normal' body
HEAD_ABOVE_GROUND = 902.0    # head centre height of a standing 'normal' body

EXPR = {
    'neutral': ('open', 'normal', 'X'), 'calm': ('open', 'normal', 'smile_closed'), 'happy': ('happy', 'raised', 'smile'),
    'relieved': ('half', 'worried', 'smile_closed'), 'laugh': ('happy', 'raised', 'smile'), 'thinking': ('open', 'raised', 'X'),
    'uneasy': ('open', 'worried', 'X'), 'suspicious': ('half', 'angry', 'X'), 'worried': ('open', 'worried', 'wavy'),
    'scared': ('wide', 'scared', 'wavy'), 'terrified': ('stare', 'scared', 'E'), 'shocked': ('wide', 'raised', 'o'),
    'sad': ('open', 'worried', 'frown'), 'cry': ('closed', 'worried', 'frown'), 'angry': ('half', 'angry', 'frown'),
    'tired': ('half', 'normal', 'X'), 'sleep': ('closed', 'normal', 'X'), 'confused': ('open', 'raised', 'X'),
    'determined': ('half', 'angry', 'X'), 'blank': ('stare', 'normal', 'X'), 'creepy_smile': ('stare', 'normal', 'smile_closed'),
    'stare': ('stare', 'normal', 'X'), 'glow': ('stare', 'normal', 'X'),
}
SWEAT = {'worried', 'scared', 'terrified'}
NUMERIC = ('lean', 'tilt', 'lift', 'thigh_k', 'look', 'wrist_L', 'wrist_R', 'hair_rot')


def expression(emo, speaking, blink, t, pose):
    eyes, brows, mouth = EXPR.get(emo, EXPR['neutral'])
    if speaking > 0.06:
        h = (math.sin(int(t * 12) * 12.9898) * 43758.5453) % 1.0
        mouth = 'B' if speaking < .2 else ('C' if speaking < .42 else 'D')
        if speaking > .3 and h < .22:
            mouth = 'E'
        elif speaking > .15 and h > .86:
            mouth = 'F'
    if pose.get('mouth_force'):
        mouth = pose['mouth_force']
    if pose.get('eyes_force'):
        eyes = pose['eyes_force']
    if blink and eyes in ('open', 'half', 'wide'):
        eyes = 'closed'
    return dict(eyes=eyes, brows=brows, mouth=mouth, sweat=emo in SWEAT)


def build_pose(c, name, t):
    fn = A.ACTIONS.get(name, A.idle)
    p = dict(fn(t))
    p.setdefault('armL', A.IDLE_L)
    p.setdefault('armR', A.IDLE_R)
    p.setdefault('legs', (4, 2, -4, -2))
    return art.solve_arms(c, p)


def blend(p0, p1, k):
    if k >= 1 or p0 is None:
        return p1
    out = dict(p1 if k >= .5 else p0)
    for arm in ('armL', 'armR'):
        a, b = p0[arm], p1[arm]
        out[arm] = ('angles', a[1] + (b[1] - a[1]) * k, a[2] + (b[2] - a[2]) * k)
    out['legs'] = tuple(x + (y - x) * k for x, y in zip(p0['legs'], p1['legs']))
    for key in NUMERIC:
        if key in p0 or key in p1:
            d = 1.0 if key == 'thigh_k' else 0.0
            out[key] = p0.get(key, d) + (p1.get(key, d) - p0.get(key, d)) * k
    return out


# ---------------------------------------------------------------- colour resolution (resvg has no CSS vars)
def _hex(h):
    h = h.lstrip('#')
    return [int(h[i:i + 2], 16) for i in (0, 2, 4)]


def resolve(svg, colors):
    def cm(m):
        a = _hex(colors.get(m.group(1), '#888888'))
        b = _hex(m.group(3))
        k = float(m.group(2)) / 100
        return '#%02x%02x%02x' % tuple(int(x * k + y * (1 - k)) for x, y in zip(a, b))
    svg = re.sub(r'color-mix\(in srgb, var\(--([a-z0-9]+)\) (\d+)%, (#[0-9a-fA-F]{6})\)', cm, svg)
    svg = re.sub(r'var\(--([a-z0-9]+)\)', lambda m: colors.get(m.group(1), '#888888'), svg)
    return re.sub(r' style="(?:--[a-z0-9]+:[^;"]+;?)+"', '', svg)


def svg_of(c, pose, expr, facing=1):
    p = dict(pose)
    p.update(expr)
    svg, _ = art.char2(c, p)
    ground = art.LAST['ground']
    wide = 1300 if p.get('beam') else 560
    x0, x1, y0, y1 = -wide, wide, ground - 1260, ground + 60
    inner = resolve(svg, c['colors'])
    if facing < 0:
        inner = f'<g transform="scale(-1 1)">{inner}</g>'
    return inner, (x0, y0, x1, y1), ground


def rasterize(inner, box, ppu):
    x0, y0, x1, y1 = box
    w, h = max(2, int((x1 - x0) * ppu)), max(2, int((y1 - y0) * ppu))
    doc = (f'<svg xmlns="http://www.w3.org/2000/svg" width="{w}" height="{h}" viewBox="{x0} {y0} {x1 - x0} {y1 - y0}">'
           f'{art.DEFS}{inner}</svg>')
    png = resvg_py.svg_to_bytes(svg_string=doc)
    return Image.open(io.BytesIO(bytes(png))).convert('RGBA')


class Renderer:
    """Caches mascot looks and rendered tiles. One per SceneRenderer."""

    def __init__(self, cache=240, anim_fps=15):
        self.looks = {}
        self.tiles = OrderedDict()
        self.n = cache
        self.anim_fps = anim_fps

    def look(self, look):
        k = id(look)
        if k not in self.looks:
            self.looks[k] = looks.from_look(look)
        return self.looks[k]

    def tile(self, look, pose_name, t, facing, emo, speaking, blink, ppu, prev=None):
        """prev = (pose_name, t_prev, k) to blend from the previous scene's pose."""
        c = self.look(look)
        tq = round(t * self.anim_fps) / self.anim_fps if pose_name in A.ANIMATED else 0.0
        sq = round(speaking * 8) / 8.0
        pk = (prev[0], round(prev[2], 1)) if prev and prev[2] < 1 else None
        key = (id(look), pose_name, tq, facing, emo, sq, blink, round(ppu, 4), pk)
        hit = self.tiles.get(key)
        if hit:
            self.tiles.move_to_end(key)
            return hit
        pose = build_pose(c, pose_name, tq)
        if pk:
            pose = blend(build_pose(c, prev[0], prev[1]), pose, prev[2])
        expr = expression(emo, sq, blink, tq, pose)
        inner, box, ground = svg_of(c, pose, expr, facing)
        img = rasterize(inner, box, ppu)
        bb = img.getbbox()
        ax, ay = -box[0] * ppu, (ground - box[1]) * ppu
        if bb:
            img = img.crop(bb)
            ax -= bb[0]
            ay -= bb[1]
        v = (img, ax, ay)
        self.tiles[key] = v
        while len(self.tiles) > self.n:
            self.tiles.popitem(last=False)
        return v


def head_height_units(look):
    """Head centre above the ground, in the stick engine's units (figure height = 104)."""
    c = looks.from_look(look)
    b = art.BODY[c['body']]
    _, T, _, _ = art.torso_path(b)
    ground = 150 * b['leg'] + 132 * b['leg'] + 50
    head = T + 10 - 185 * b['head']
    return (ground - head) / CHAR_UNITS * 104.0
