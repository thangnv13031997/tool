"""Lighting and atmosphere: light maps, flicker, fog, rain, grain, VHS, flash.

Heavy maths happens once per scene (numpy, low resolution); per-frame work is
a few Pillow C operations so rendering stays fast.
"""
import math
import random
import numpy as np
from PIL import Image, ImageChops, ImageFilter
from .gfx import hex_rgba


# ------------------------------------------------------------------ flicker
def _hash(i, seed):
    x = math.sin(i * 12.9898 + seed * 78.233) * 43758.5453
    return x - math.floor(x)


def flicker(t, seed=0.0, mode='electric', amount=1.0):
    """Light level 0..1 at time t."""
    if mode == 'flame':
        v = 0.86 + 0.08 * math.sin(t * 11 + seed) + 0.05 * math.sin(t * 23.7 + seed * 2) + 0.03 * math.sin(t * 41 + seed)
        return 1 - (1 - v) * amount
    seg = int(t / 0.07)
    r = _hash(seg, seed)
    v = 1.0
    if r < 0.10:
        v = 0.15 + 0.35 * _hash(seg + 999, seed)
    elif r < 0.14:
        v = 0.03
    burst = int(t / 1.6)
    if _hash(burst, seed + 5) < 0.35 and (t % 1.6) < 0.25:
        v = min(v, 0.1 + 0.8 * _hash(int(t / 0.04), seed + 9))
    v = v * (0.97 + 0.03 * math.sin(t * 60))
    return 1 - (1 - v) * amount


# ------------------------------------------------------------------ light maps
def _falloff(kind, lt, X, Y, aspect):
    x, y, r = lt['x'], lt['y'], max(0.02, lt.get('r', 0.3))
    dx = (X - x) * aspect
    dy = Y - y
    if kind == 'point':
        d = np.sqrt(dx * dx + dy * dy)
        f = np.clip(1 - d / r, 0, 1) ** 1.7
        halo = np.clip(1 - d / (r * 0.14), 0, 1) ** 2
        return f, halo
    if kind in ('cone', 'cone_up'):
        if kind == 'cone_up':
            dy = -dy
        spread = lt.get('spread', 0.25)
        half = 0.02 + spread * np.clip(dy, 0, None)
        inside = np.clip(1 - np.abs(dx) / half, 0, 1) ** 0.9
        depth = np.clip(1 - dy / r, 0, 1) ** 1.1
        f = np.where(dy > -0.01, inside * depth, 0.0)
        d = np.sqrt(dx * dx + dy * dy)
        f = np.maximum(f, np.clip(1 - d / (r * 0.18), 0, 1) ** 2 * 0.8)
        halo = np.clip(1 - d / (r * 0.06), 0, 1) ** 2
        return f, halo
    if kind == 'cone_side':
        direction = lt.get('dir', 1)
        ddx = dx * direction
        spread = lt.get('spread', 0.18)
        half = 0.02 + spread * np.clip(ddx, 0, None)
        inside = np.clip(1 - np.abs(dy) / half, 0, 1) ** 0.8
        depth = np.clip(1 - ddx / r, 0, 1) ** 1.0
        f = np.where(ddx > -0.005, inside * depth, 0.0)
        d = np.sqrt(dx * dx + dy * dy)
        halo = np.clip(1 - d / 0.03, 0, 1) ** 2
        return f, halo
    if kind == 'rect':
        w = lt.get('w', 0.1) * aspect / 2
        h = lt.get('h', 0.1) / 2
        ex = np.clip(np.abs(dx) - w, 0, None)
        ey = np.clip(np.abs(dy) - h, 0, None)
        d = np.sqrt(ex * ex + ey * ey)
        f = np.clip(1 - d / r, 0, 1) ** 1.6
        inner = (d <= 0).astype(np.float32)
        return f, inner * 0.5
    return np.zeros_like(X), np.zeros_like(X)


class Lighting:
    """Per-scene lighting. Call apply(canvas, t) every frame."""

    def __init__(self, W, H, lights, ambient=0.4, tint=(1, 1, 1), vignette=0.45, power=1.0,
                 flicker_mode=None, seed=0.0, scale=4, darkness=1.0, exposure=1.4):
        self.W, self.H = W, H
        self.seed = seed
        self.lights = [dict(l) for l in lights if l.get('power', 1) > 0 and l.get('kind')]
        w, h = max(8, W // scale), max(8, H // scale)
        X, Y = np.meshgrid(np.linspace(0, 1, w, dtype=np.float32), np.linspace(0, 1, h, dtype=np.float32))
        aspect = W / H
        amb = np.array(tint, np.float32) * min(0.95, ambient * exposure) * darkness
        base = np.ones((h, w, 3), np.float32) * amb
        flick = np.zeros((h, w, 3), np.float32)
        glow_base = np.zeros((h, w, 3), np.float32)
        glow_flick = np.zeros((h, w, 3), np.float32)
        self.flame_only = True
        self.has_flicker = False
        for lt in self.lights:
            f, halo = _falloff(lt['kind'], lt, X, Y, aspect)
            col = np.array(hex_rgba(lt.get('col', '#FFD9A0'))[:3], np.float32) / 255.0
            p = lt.get('power', 1.0) * power
            contrib = f[..., None] * col * p
            g = halo[..., None] * col * p * 0.55
            if lt.get('flicker'):
                flick += contrib
                glow_flick += g
                self.has_flicker = True
                if not lt.get('flame'):
                    self.flame_only = False
            else:
                base += contrib
                glow_base += g
        self.mode = flicker_mode or ('flame' if (self.flame_only and self.has_flicker) else 'electric')
        if vignette:
            d = np.sqrt(((X - 0.5) * 1.1) ** 2 + (Y - 0.5) ** 2)
            v = 1 - vignette * np.clip((d - 0.28) / 0.5, 0, 1) ** 1.5
            base *= v[..., None]
            flick *= v[..., None]
        self.low_on = np.clip(base + flick, 0, 1)
        self.low_off = np.clip(base, 0, 1)

        def up(a, smooth=True):
            im = Image.fromarray((np.clip(a, 0, 1) * 255).astype(np.uint8), 'RGB').resize((W, H), Image.BILINEAR)
            return im.filter(ImageFilter.GaussianBlur(2)) if smooth else im

        self.on = up(self.low_on)
        self.off = up(self.low_off) if self.has_flicker else self.on
        self.glow_on = up(glow_base + glow_flick)
        self.glow_off = up(glow_base) if self.has_flicker else self.glow_on
        self.has_glow = float((glow_base + glow_flick).max()) > 0.01
        self.black = Image.new('RGB', (W, H), (0, 0, 0))
        self._dark_cache = None

    def level(self, t, events=None):
        k = flicker(t, self.seed, self.mode) if self.has_flicker else 1.0
        if events:
            for ev in events:
                if ev['kind'] == 'lights_out' and t >= ev['t']:
                    k = 0.0 if t > ev['t'] + 0.25 else min(k, flicker(t * 3, self.seed + 3))
                elif ev['kind'] == 'lights_on' and t < ev['t']:
                    k = 0.0
        return k

    def apply(self, canvas, t, events=None, dim=1.0):
        k = self.level(t, events)
        if not self.has_flicker or k >= 0.995:
            L, G = self.on, self.glow_on
        elif k <= 0.005:
            L, G = self.off, self.glow_off
        else:
            L = Image.blend(self.off, self.on, k)
            G = Image.blend(self.glow_off, self.glow_on, k) if self.has_glow else None
        if dim < 0.999:
            L = Image.blend(self.black, L, max(0.0, dim))
        out = ImageChops.multiply(canvas, L)
        if self.has_glow and G is not None and dim > 0.3:
            out = ImageChops.add(out, G)
        return out, k

    def sample(self, x, y, k=1.0):
        """Light colour (0..1 RGB) at a point, for tinting characters."""
        h, w, _ = self.low_on.shape
        i = int(min(h - 1, max(0, y * h)))
        j = int(min(w - 1, max(0, x * w)))
        on = self.low_on[i, j]
        off = self.low_off[i, j]
        return off + (on - off) * k


# ------------------------------------------------------------------ atmosphere
class Fog:
    def __init__(self, W, H, density=0.35, color=(150, 160, 175), seed=4, low=True):
        self.W, self.H = W, H
        rnd = np.random.default_rng(seed)
        w2 = int(W * 1.6) // 8
        h2 = H // 8
        n = rnd.random((h2, w2)).astype(np.float32)
        im = Image.fromarray((n * 255).astype(np.uint8), 'L').resize((w2 * 8, h2 * 8), Image.BICUBIC)
        im = im.filter(ImageFilter.GaussianBlur(H * 0.05))
        a = np.asarray(im).astype(np.float32) / 255.0
        a = np.clip((a - 0.35) * 2.2, 0, 1)
        if low:
            ys = np.linspace(0, 1, a.shape[0], dtype=np.float32)[:, None]
            a = a * (0.35 + 0.65 * np.clip((ys - 0.35) / 0.5, 0, 1))
        self.mask = Image.fromarray((a * 255 * density).astype(np.uint8), 'L')
        self.color = tuple(int(c) for c in color)

    def apply(self, canvas, t, speed=0.012):
        off = int((t * speed * self.W) % (self.mask.width - self.W))
        m = self.mask.crop((off, 0, off + self.W, self.H))
        canvas.paste(self.color, (0, 0, self.W, self.H), m)
        return canvas


class Rain:
    def __init__(self, W, H, n=420, seed=6, frames=10, heavy=False):
        self.frames = []
        rnd = random.Random(seed)
        drops = [(rnd.random() * W, rnd.random() * H, rnd.uniform(0.6, 1.4)) for _ in range(n * (2 if heavy else 1))]
        for f in range(frames):
            im = Image.new('RGBA', (W, H), (0, 0, 0, 0))
            from PIL import ImageDraw
            d = ImageDraw.Draw(im)
            for x, y, s in drops:
                yy = (y + f * H / frames * 1.3 * s) % H
                xx = (x - f * 6 * s) % W
                ln = 26 * s * H / 1080
                d.line([(xx, yy), (xx - ln * 0.18, yy + ln)], fill=(170, 185, 205, int(70 * s)), width=max(1, int(2 * H / 1080)))
            self.frames.append(im)

    def apply(self, canvas, t, fps=30):
        im = self.frames[int(t * fps) % len(self.frames)]
        canvas.paste(im, (0, 0), im)
        return canvas


class Grain:
    def __init__(self, W, H, amount=0.06, frames=8, seed=7):
        rnd = np.random.default_rng(seed)
        self.frames = []
        sw, sh = W // 2, H // 2
        for _ in range(frames):
            n = rnd.normal(128, 50, (sh, sw)).clip(0, 255).astype(np.uint8)
            self.frames.append(Image.fromarray(n, 'L').resize((W, H), Image.NEAREST).convert('RGB'))
        self.amount = amount

    def apply(self, canvas, t, fps=30):
        g = self.frames[int(t * fps / 2) % len(self.frames)]
        return Image.blend(canvas, g, self.amount)


class VHS:
    def __init__(self, W, H, seed=8):
        self.W, self.H = W, H
        lines = np.ones((H, 1), np.float32)
        lines[::3] = 0.82
        self.scan = Image.fromarray((np.repeat(lines, W, axis=1) * 255).astype(np.uint8), 'L').convert('RGB')
        self.seed = seed

    def apply(self, canvas, t, strength=1.0):
        W, H = self.W, self.H
        r, g, b = canvas.split()
        sh = max(1, int(4 * strength * W / 1920))
        r = ImageChops.offset(r, sh, 0)
        b = ImageChops.offset(b, -sh, 0)
        out = Image.merge('RGB', (r, g, b))
        out = ImageChops.multiply(out, self.scan)
        # tracking band
        band_y = int(((t * 0.37 + _hash(int(t), self.seed) * 0.5) % 1.2) * H)
        if band_y < H:
            bh = int(H * 0.04)
            box = (0, band_y, W, min(H, band_y + bh))
            strip = out.crop(box)
            strip = ImageChops.offset(strip, int(18 * strength * W / 1920), 0)
            strip = Image.blend(strip, Image.new('RGB', strip.size, (200, 200, 200)), 0.12)
            out.paste(strip, box[:2])
        return out

    @staticmethod
    def timestamp(canvas, text, font):
        from PIL import ImageDraw
        d = ImageDraw.Draw(canvas)
        W, H = canvas.size
        d.text((W * 0.05, H * 0.06), 'REC', font=font, fill=(235, 40, 40))
        d.ellipse((W * 0.035 - 14, H * 0.075 - 14, W * 0.035 + 14, H * 0.075 + 14), fill=(235, 40, 40))
        d.text((W * 0.72, H * 0.9), text, font=font, fill=(235, 235, 225))
        return canvas


def grade(img, desat=0.25, tint=(0.92, 0.98, 1.08), contrast=1.06):
    """Cold, slightly desaturated grade (applied once to a background)."""
    a = np.asarray(img.convert('RGB')).astype(np.float32)
    grey = a.mean(axis=2, keepdims=True)
    a = a + (grey - a) * desat
    a = (a - 128) * contrast + 128
    a = a * np.array(tint, np.float32)
    return Image.fromarray(np.clip(a, 0, 255).astype(np.uint8), 'RGB')


def flash(img, amount, color=(255, 255, 255)):
    if amount <= 0.01:
        return img
    return Image.blend(img, Image.new('RGB', img.size, color), min(1.0, amount))


def fade_black(img, amount):
    if amount <= 0.01:
        return img
    return Image.blend(img, Image.new('RGB', img.size, (0, 0, 0)), min(1.0, amount))


def glitch(img, t, strength=1.0, seed=3):
    W, H = img.size
    out = img.copy()
    n = int(6 * strength)
    for i in range(n):
        y = int(_hash(int(t * 30) * 7 + i, seed) * H)
        h = int(H * (0.01 + 0.05 * _hash(i + int(t * 30), seed + 1)))
        dx = int((_hash(i * 3 + int(t * 30), seed + 2) - 0.5) * W * 0.08 * strength)
        box = (0, y, W, min(H, y + h))
        out.paste(ImageChops.offset(img.crop(box), dx, 0), box[:2])
    r, g, b = out.split()
    r = ImageChops.offset(r, int(8 * strength), 0)
    return Image.merge('RGB', (r, g, b))
