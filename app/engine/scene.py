"""Compose one horror video frame from a normalised scene at time t."""
import math
from collections import OrderedDict
from PIL import Image, ImageChops
from . import figure as F
from . import props as PR
from . import backgrounds as BG
from . import textfx
from . import fx
from .gfx import ease_out_back, ease_in_out, lerp

WORLD_K = 1.12
FIG_H = 0.5
ENTER_T = 1.2
EXIT_T = 1.1
BLEND_T = 0.3
PROP_K = 0.12


class LRU(OrderedDict):
    def __init__(self, n):
        super().__init__()
        self.n = n

    def get2(self, k):
        if k in self:
            self.move_to_end(k)
            return self[k]
        return None

    def put(self, k, v):
        self[k] = v
        self.move_to_end(k)
        while len(self) > self.n:
            self.popitem(last=False)


def _hash(i, s=0.0):
    x = math.sin(i * 12.9898 + s * 78.233) * 43758.5453
    return x - math.floor(x)


class SceneRenderer:
    def __init__(self, out_w=1920, out_h=1080, quality=2, captions=True):
        self.OW, self.OH = out_w, out_h
        self.WW, self.WH = int(out_w * WORLD_K), int(out_h * WORLD_K)
        self.S = quality
        self.captions = captions
        self.layer_cache = OrderedDict()
        self.fig_cache = LRU(260)
        self.prop_cache = LRU(120)
        self.scare_cache = {}
        self.text = textfx.CaptionCache(out_w, out_h)
        self.u = FIG_H * self.WH / 104.0
        self._grain = None
        self._vhs = None
        self._fog = {}
        self._rain = {}
        self.cur_key = None
        self.cur = None

    # ------------------------------------------------------------ per scene setup
    def _scene_key(self, sc):
        return (sc['bg'], tuple(sorted((k, str(v)) for k, v in sc.get('bg_opts', {}).items())),
                tuple(sorted(sc.get('fx', []))), round(sc.get('darkness', 1.0), 2), sc.get('grade', 'cold'))

    def setup(self, sc):
        key = self._scene_key(sc)
        if key == self.cur_key:
            return self.cur
        hit = self.layer_cache.get(key)
        if hit is None:
            lay = BG.render_bg(sc['bg'], self.WW, self.WH, sc.get('bg_opts'), S=self.S)
            g = sc.get('grade', 'cold')
            if g == 'cold':
                img = fx.grade(lay.img, 0.28, (0.92, 0.98, 1.08), 1.05)
            elif g == 'warm':
                img = fx.grade(lay.img, 0.15, (1.06, 0.98, 0.88), 1.04)
            elif g == 'sepia':
                img = fx.grade(lay.img, 0.75, (1.08, 0.96, 0.78), 1.0)
            else:
                img = lay.img
            lights = list(lay.lights) + list(sc.get('extra_lights', []))
            light = fx.Lighting(self.WW, self.WH, lights, lay.ambient, lay.tint,
                                vignette=0.5, seed=(sc.get('index', 0) * 1.37) % 7, darkness=sc.get('darkness', 1.0))
            hit = {'img': img, 'fg': lay.fg, 'light': light, 'ground': lay.ground}
            self.layer_cache[key] = hit
            while len(self.layer_cache) > 4:
                self.layer_cache.popitem(last=False)
        self.cur_key, self.cur = key, hit
        return hit

    def fog(self, density):
        k = round(density, 2)
        if k not in self._fog:
            self._fog[k] = fx.Fog(self.WW, self.WH, density=k)
        return self._fog[k]

    def rain(self, heavy=False):
        if heavy not in self._rain:
            self._rain[heavy] = fx.Rain(self.WW, self.WH, heavy=heavy)
        return self._rain[heavy]

    # ------------------------------------------------------------ tiles
    def _fig_tile(self, look, pose, ang, facing, emo, mouth, blink, t, scale):
        key = (id(look), round(scale, 3), pose, tuple(int(round(ang.get(k, 0))) for k in sorted(F.BASE)),
               round(ang.get('air', 0), 1), round(ang.get('tremble', 0), 1), facing, emo, round(mouth, 1), blink)
        hit = self.fig_cache.get2(key)
        if hit:
            return hit
        img, ax, ay = F.draw_figure(look, pose, ang, facing, emo, mouth, blink, t, u=self.u * scale, S=self.S)
        bb = img.getbbox()
        if bb:
            img = img.crop(bb)
            ax -= bb[0]
            ay -= bb[1]
        v = (img, ax, ay)
        self.fig_cache.put(key, v)
        return v

    def _tint(self, img, rgb):
        q = tuple(max(0, min(255, int(round(c * 20)) * 255 // 20)) for c in rgb)
        if q == (255, 255, 255):
            return img
        rgbimg = ImageChops.multiply(img.convert('RGB'), Image.new('RGB', img.size, q))
        rgbimg.putalpha(img.getchannel('A'))
        return rgbimg

    def _prop_tile(self, p, s, t):
        name, group, _ = PR.resolve(p.get('type'))
        animated = name in ('coffee', 'eyes', 'candle', 'clock', 'tv_static', 'lantern', 'lighter', 'chat', 'cctv')
        key = (name, int(s), str(p.get('text')), str(p.get('messages')), p.get('_reveal'), p.get('highlight'),
               p.get('strike'), p.get('tilt'), round(t * 12) / 12.0 if animated else 0)
        hit = self.prop_cache.get2(key)
        if hit:
            return hit
        img, cx, cy = PR.render(p, s, t, S=self.S, full=(self.OW, self.OH))
        if name != 'cctv':
            bb = img.getbbox()
            if bb:
                img = img.crop(bb)
                cx -= bb[0]
                cy -= bb[1]
        v = (img, cx, cy)
        self.prop_cache.put(key, v)
        return v

    # ------------------------------------------------------------ characters
    def char_state(self, sc, c, t, idx):
        dur = sc['duration']
        x = c['x']
        pose = c['pose']
        facing = c['facing']
        moving = False
        enter_t = c.get('enter_t', ENTER_T)
        if c.get('enter') and t < enter_t:
            x0 = -0.12 if c['enter'] == 'left' else 1.12
            k = ease_in_out(t / enter_t)
            x = lerp(x0, c['x'], k)
            pose = c.get('move_pose') or ('walk' if abs(c['x'] - x0) < 0.7 else 'run')
            facing = 1 if c['x'] > x0 else -1
            moving = True
        elif c.get('exit') and t > dur - EXIT_T:
            x1 = -0.14 if c['exit'] == 'left' else 1.14
            k = ease_in_out((t - (dur - EXIT_T)) / EXIT_T)
            x = lerp(c['x'], x1, k)
            pose = c.get('move_pose') or 'walk'
            facing = 1 if x1 > c['x'] else -1
            moving = True
        speaking = 0.0
        for ln in sc['lines']:
            if ln.get('speaker_key') == c['key'] and ln['start'] <= t < ln['end']:
                env = ln.get('env')
                if env is not None and len(env):
                    i = int((t - ln['start']) * ln.get('env_fps', 30))
                    speaking = float(env[min(i, len(env) - 1)])
                else:
                    speaking = max(0.0, math.sin(t * 17)) * 0.7
                if not moving and pose in ('idle', 'stand'):
                    pose = 'talk'
                elif not moving and pose == 'sit':
                    pose = 'sit_talk'
                break
        seed = c.get('seed', idx * 1.7)
        ang = F.pose_angles(pose, t, seed)
        prev = c.get('prev')
        if not moving and prev and t < BLEND_T:
            ang = F.blend(F.pose_angles(prev['pose'], prev['t'], seed), ang, ease_in_out(t / BLEND_T))
        emo = c['emotion']
        blink = False
        if emo not in ('sleep', 'blank', 'creepy_smile', 'stare', 'glow'):
            period = 3.2 + (seed % 1.3)
            blink = ((t + seed * 2.1) % period) < 0.12
        return x, pose, ang, facing, emo, speaking, blink

    def _char_alpha(self, c, t):
        a = 1.0
        if c.get('appear_at') is not None:
            t0 = c['appear_at']
            fade = c.get('appear_fade', 0.0)
            if t < t0:
                return 0.0
            if fade > 0:
                a = min(1.0, (t - t0) / fade)
        if c.get('vanish_at') is not None and t >= c['vanish_at']:
            return 0.0
        return a

    # ------------------------------------------------------------ camera
    def camera(self, sc, t):
        dur = max(0.1, sc['duration'])
        cam = sc.get('camera', 'slow_push')
        t_abs = t
        t0 = 0.0
        fx_, fy_ = sc.get('focus_x', 0.5), sc.get('focus_y', 0.5)
        cuts = sc.get('cuts') or []
        for c in cuts:
            if t >= c['t']:
                cam, (fx_, fy_), t0 = c['camera'], c['focus'], c['t']
        if t0 > 0:
            nxt = [c['t'] for c in cuts if c['t'] > t0]
            dur = max(0.1, (nxt[0] if nxt else sc['duration']) - t0)
            t = t - t0
        k = ease_in_out(t / dur)
        z, cx, cy = 1.0, 0.5, 0.5
        if cam in ('slow_push', 'push_in'):
            amt = 0.08 if cam == 'slow_push' else 0.2
            z = lerp(1.0, 1.0 + amt, k)
            cx, cy = lerp(0.5, fx_, k * 0.8), lerp(0.5, fy_, k * 0.8)
        elif cam in ('pull_out', 'zoom_out'):
            z = lerp(1.18, 1.0, k)
            cx, cy = lerp(fx_, 0.5, k), lerp(fy_, 0.5, k)
        elif cam == 'pan_right':
            z = 1.08
            cx = lerp(0.46, 0.54, k)
        elif cam == 'pan_left':
            z = 1.08
            cx = lerp(0.54, 0.46, k)
        elif cam == 'drift':
            z = 1.05
            cx = 0.5 + 0.03 * math.sin(t * 0.35)
            cy = 0.5 + 0.015 * math.sin(t * 0.27)
        elif cam == 'close':
            z = lerp(1.32, 1.38, k)
            cx, cy = fx_, fy_
        elif cam == 'extreme_close':
            z = lerp(1.7, 1.8, k)
            cx, cy = fx_, fy_
        elif cam == 'punch':
            z = lerp(1.0, 1.22, ease_out_back(min(1.0, t / 0.3)))
            cx, cy = fx_, fy_
        elif cam == 'static':
            z = 1.0
        sx = sy = 0.0
        # handheld breathing on every shot except static
        if cam != 'static':
            sx += 0.0025 * math.sin(t_abs * 1.3 + 1) + 0.0012 * math.sin(t_abs * 3.1)
            sy += 0.002 * math.sin(t_abs * 1.7) + 0.001 * math.sin(t_abs * 2.6 + 2)
        shake = sc.get('shake_amt', 0.0)
        for ev in sc.get('events', []):
            if ev['kind'] in ('jumpscare', 'stinger') and ev['t'] <= t_abs < ev['t'] + 0.6:
                shake = max(shake, 1.0 - (t_abs - ev['t']) / 0.6)
                if ev['kind'] == 'stinger':
                    z *= 1 + 0.12 * ease_out_back(min(1.0, (t_abs - ev['t']) / 0.25))
        if cam == 'shake':
            shake = max(shake, 0.5)
        if shake > 0:
            sx += math.sin(t_abs * 61) * 0.014 * shake
            sy += math.cos(t_abs * 47) * 0.012 * shake
            z = max(z, 1.04)
        z = max(1.0, z)
        w = self.WW / z
        h = self.WH / z
        # safe framing: on close shots keep the main character's head in the upper half of the picture
        wgt = max(0.0, min(1.0, (z - 1.04) / 0.1))
        if wgt > 0:
            tgt = self._frame_target(sc, t_abs)
            if tgt is not None:
                hx, hy, hr = tgt
                top = cy * self.WH - h / 2
                lo, hi = top + h * 0.24, top + h * 0.52
                cy2, cx2 = cy, cx
                if hy < lo:
                    cy2 = (hy - h * 0.24 + h / 2) / self.WH
                elif hy > hi:
                    cy2 = (hy - h * 0.52 + h / 2) / self.WH
                cx_px = cx * self.WW
                if abs(hx - cx_px) > w * 0.3:
                    cx2 = (hx - math.copysign(w * 0.3, hx - cx_px)) / self.WW
                cy, cx = lerp(cy, cy2, wgt), lerp(cx, cx2, wgt)
        x0 = cx * self.WW - w / 2 + sx * self.WW
        y0 = cy * self.WH - h / 2 + sy * self.WH
        x0 = max(0, min(self.WW - w, x0))
        y0 = max(0, min(self.WH - h, y0))
        return (x0, y0, x0 + w, y0 + h)

    def _frame_target(self, sc, t):
        """(x px, head y px) of the speaking / first main character, or None."""
        chars = [c for c in sc['chars'] if c.get('scale', 1.0) >= 0.7 and self._char_alpha(c, t) > 0.5]
        if not chars:
            return None
        spk = None
        for ln in sc['lines']:
            if ln['start'] - 0.3 <= t < ln['end'] + 0.3:
                spk = next((c for c in chars if c['key'] == ln.get('speaker_key')), None)
                if spk:
                    break
        c = spk or chars[0]
        try:
            hh = F.head_height(c['look'], c['pose'])
        except Exception:
            return None
        ground = (self.cur['ground'] if self.cur else BG.GROUND_Y)
        gy = c.get('y', ground) * self.WH
        u = self.u * c.get('scale', 1.0)
        return c['x'] * self.WW, gy - hh * u, c['look'].head_r * u

    # ------------------------------------------------------------ frame
    def frame(self, sc, t, captions=None, inserts=True):
        L = self.setup(sc)
        WW, WH = self.WW, self.WH
        canvas = L['img'].copy()
        ground = L['ground'] * WH
        # world props
        for p in sc['props']:
            if p['group'] == 'world':
                self._paste_prop(canvas, p, t, WW, WH)
        # lighting
        canvas, lvl = L['light'].apply(canvas, t, sc.get('events'))
        for p in sc['props']:
            if p['group'] == 'glow':
                self._paste_prop(canvas, p, t, WW, WH)
        # characters
        for i, c in enumerate(sc['chars']):
            a = self._char_alpha(c, t)
            if a <= 0.01:
                continue
            x, pose, ang, facing, emo, mouth, blink, = self.char_state(sc, c, t, i)
            scale = c.get('scale', 1.0)
            img, ax, ay = self._fig_tile(c['look'], pose, ang, facing, emo, mouth, blink, t, scale)
            if not c['look'].entity or c['look'].type in ('raincoat_man', 'pale_man', 'mimic', 'child_ghost'):
                rgb = L['light'].sample(x, c.get('y', L['ground']) - 0.25 * scale, lvl)
                lo = c.get('min_light', 0.62 if not c['look'].entity else 0.4)
                rgb = [min(1.0, max(lo, v * 1.15)) for v in rgb]
                img = self._tint(img, rgb)
            if a < 0.99:
                img = img.copy()
                img.putalpha(img.getchannel('A').point(lambda v, a=a: int(v * a)))
            gy = c.get('y', L['ground']) * WH
            canvas.paste(img, (int(round(x * WW - ax)), int(round(gy - ay))), img)
        # foreground parallax layer
        box = self.camera(sc, t)
        if L['fg'] is not None:
            cxn = (box[0] + box[2]) / 2 / WW - 0.5
            off = int(-cxn * WW * 0.35)
            fgl = L['fg']
            canvas.paste(fgl, (off, 0), fgl)
        fxs = sc.get('fx', ())
        if 'fog' in fxs or 'fog_heavy' in fxs:
            self.fog(0.55 if 'fog_heavy' in fxs else 0.32).apply(canvas, t)
        if 'rain' in fxs or 'rain_heavy' in fxs:
            self.rain('rain_heavy' in fxs).apply(canvas, t)
        frame = canvas.resize((self.OW, self.OH), Image.BILINEAR, box=box)
        # film look
        if 'grain' in fxs:
            if self._grain is None:
                self._grain = fx.Grain(self.OW, self.OH, 0.035)
            frame = self._grain.apply(frame, t)
        if 'vhs' in fxs:
            if self._vhs is None:
                self._vhs = fx.VHS(self.OW, self.OH)
            frame = self._vhs.apply(frame, t)
        # events
        for ev in sc.get('events', []):
            dt = t - ev['t']
            if ev['kind'] == 'jumpscare' and 0 <= dt < ev.get('dur', 0.5):
                frame = self._jumpscare(frame, ev, dt)
            elif ev['kind'] == 'glitch' and 0 <= dt < ev.get('dur', 0.35):
                frame = fx.glitch(frame, t, 1.2)
            elif ev['kind'] in ('flash', 'stinger') and 0 <= dt < 0.18:
                frame = fx.flash(frame, (1 - dt / 0.18) * (0.75 if ev['kind'] == 'flash' else 0.25))
        # inserts (close-up overlays)
        if inserts:
            for p in sc['props']:
                if p['group'] == 'insert':
                    frame = self._paste_insert(frame, p, t, sc)
        # captions
        if captions if captions is not None else self.captions:
            cap = self.caption_at(sc, t)
            if cap:
                img = self.text.caption(cap)
                frame.paste(img, (int(self.OW / 2 - img.width / 2), int(self.OH * 0.88 - img.height / 2)), img)
        # transitions
        tr = sc.get('transition', 'cut')
        if tr in ('fade', 'fade_black') and t < 0.45:
            frame = fx.fade_black(frame, 1 - ease_in_out(t / 0.45))
        elif tr == 'flash' and t < 0.2:
            frame = fx.flash(frame, 1 - t / 0.2)
        out_t = sc.get('end_black', 0.0)
        if out_t and t > sc['duration'] - out_t:
            frame = fx.fade_black(frame, 1.0)
        elif sc.get('fade_out') and t > sc['duration'] - 0.6:
            frame = fx.fade_black(frame, ease_in_out((t - sc['duration'] + 0.6) / 0.6))
        return frame

    def _jumpscare(self, frame, ev, dt):
        kind = ev.get('entity', 'face')
        if kind not in self.scare_cache:
            self.scare_cache[kind] = PR.scare_face(self.OW, self.OH, kind)
        img = self.scare_cache[kind]
        z = 1.0 + 0.25 * min(1.0, dt / ev.get('dur', 0.5))
        w, h = int(self.OW / z), int(self.OH / z)
        sx = int((math.sin(dt * 70) * 0.02) * self.OW)
        x0 = (self.OW - w) // 2 + sx
        y0 = (self.OH - h) // 2
        crop = img.crop((x0, y0, x0 + w, y0 + h)).resize((self.OW, self.OH), Image.BILINEAR)
        base = fx.fade_black(frame, 0.75)
        base.paste(crop, (0, 0), crop)
        if dt < 0.06:
            base = fx.flash(base, 0.85)
        return fx.glitch(base, dt + ev['t'], 0.6) if dt < 0.15 else base

    def _paste_prop(self, canvas, p, t, WW, WH):
        t0 = p.get('t0', 0.0)
        if t < t0 or (p.get('t1') is not None and t > p['t1']):
            return
        s = PROP_K * WH * p.get('scale', 1.0)
        img, cx, cy = self._prop_tile(p, s, t)
        k = 1.0
        if p.get('pop', False):
            k = ease_out_back(min(1.0, (t - t0) / 0.3))
            if k < 0.02:
                return
            if abs(k - 1) > 0.01:
                img = img.resize((max(1, int(img.width * k)), max(1, int(img.height * k))), Image.BILINEAR)
                cx, cy = cx * k, cy * k
        fade = p.get('fade_in', 0.0)
        if fade and t - t0 < fade:
            a = (t - t0) / fade
            img = img.copy()
            img.putalpha(img.getchannel('A').point(lambda v, a=a: int(v * a)))
        canvas.paste(img, (int(round(p['x'] * WW - cx)), int(round(p['y'] * WH - cy))), img)

    def _paste_insert(self, frame, p, t, sc):
        t0 = p.get('t0', 0.0)
        if t < t0 or (p.get('t1') is not None and t > p['t1']):
            return frame
        name = PR.resolve(p.get('type'))[0]
        if name == 'chat' and p.get('messages'):
            n = len(p['messages'])
            gap = p.get('message_gap', 1.1)
            p = dict(p)
            p['_reveal'] = min(n, 1 + int((t - t0) / gap))
        s = self.OH * (0.4 if name == 'chat' else 0.32) * p.get('scale', 1.0)
        img, cx, cy = self._prop_tile(p, s, t)
        k = ease_in_out(min(1.0, (t - t0) / 0.35))
        if name == 'cctv':
            frame.paste(img, (0, 0), img)
            return frame
        if name == 'card':
            frame = fx.fade_black(frame, 0.85 * k)
        else:
            frame = fx.fade_black(frame, 0.45 * k)
        x = p.get('x', 0.5) * self.OW - cx
        y = p.get('y', 0.47) * self.OH - cy + (1 - k) * self.OH * 0.08
        if k < 0.99:
            img = img.copy()
            img.putalpha(img.getchannel('A').point(lambda v, a=k: int(v * a)))
        frame.paste(img, (int(x), int(y)), img)
        return frame

    @staticmethod
    def caption_at(sc, t):
        for ln in sc['lines']:
            if ln['start'] <= t < ln['end'] + 0.05:
                chunks = ln.get('chunks') or []
                for c in chunks:
                    if c['start'] <= t < c['end']:
                        return c['words']
                if chunks and t >= chunks[-1]['start']:
                    return chunks[-1]['words']
        return None
