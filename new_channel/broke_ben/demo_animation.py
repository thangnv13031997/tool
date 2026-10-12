"""9-second animation test with the v2 mascots (no voice): proves the art style animates.

Techniques shown: breathing (squash/stretch), blinking, lip flaps, pose switch, pop-in card,
count-down number, bounce entrance, falling coin with impact squash.
Run:  python demo_animation.py      -> demo/demo_9s.mp4 + demo/frames.jpg
"""
import math
import os
import subprocess
from PIL import Image, ImageDraw
from charkit import ben, piggy
from flatkit import Pen, font
from make_branding import coin, GREEN, RED, GOLD

W, H, FPS, DUR = 1280, 720, 30, 9.0
OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'demo')
os.makedirs(OUT, exist_ok=True)
INK = (29, 33, 45)

_cache = {}


def sprite(kind, **kw):
    key = (kind, tuple(sorted(kw.items())))
    if key not in _cache:
        im = (ben if kind == 'ben' else piggy)(**kw)
        _cache[key] = im.crop(im.getbbox())
    return _cache[key]


def ease_out_back(t):
    c = 1.70158
    return 1 + (c + 1) * (t - 1) ** 3 + c * (t - 1) ** 2


def ease_in_out(t):
    return 0.5 - 0.5 * math.cos(math.pi * max(0, min(1, t)))


def clamp01(t):
    return max(0.0, min(1.0, t))


def place(frame, im, cx, base_y, height, sx=1.0, sy=1.0, rot=0):
    """Paste a sprite with its feet at (cx, base_y), scaled to `height`, with squash/stretch."""
    k = height / im.height
    w, h = max(1, int(im.width * k * sx)), max(1, int(im.height * k * sy))
    s = im.resize((w, h), Image.BICUBIC)
    if rot:
        s = s.rotate(rot, resample=Image.BICUBIC, expand=True)
    frame.alpha_composite(s, (int(cx - s.width / 2), int(base_y - s.height)))


def background():
    p = Pen(W, H, S=1, bg='#F6F1E6')
    p.vgrad((0, 0, W, H), '#FBF7EE', '#ECE3CF')
    for x in range(0, W, 40):
        p.line([(x, 0), (x, H)], 1, (0, 0, 0, 12), caps=False)
    for y in range(0, H, 40):
        p.line([(0, y), (W, y)], 1, (0, 0, 0, 12), caps=False)
    p.rect((0, 600, W, H), (226, 214, 190))
    p.rect((0, 596, W, 602), (205, 190, 160))
    return p.img


def caption(frame, text, hi):
    d = ImageDraw.Draw(frame)
    f = font('semi', 38)
    words = text.split(' ')
    sp = f.getlength(' ')
    total = sum(f.getlength(w) for w in words) + sp * (len(words) - 1)
    lay = Image.new('RGBA', frame.size, (0, 0, 0, 0))
    ImageDraw.Draw(lay).rounded_rectangle((W / 2 - total / 2 - 26, 640, W / 2 + total / 2 + 26, 700), 30,
                                          fill=(14, 16, 22, 220))
    frame.alpha_composite(lay)
    x = W / 2 - total / 2
    for w in words:
        d.text((x, 670), w, font=f, fill=GOLD if w.strip('.,!?') in hi else (250, 250, 245), anchor='lm')
        x += f.getlength(w) + sp


def money_card(frame, t_pop, value, label, col):
    if t_pop <= 0:
        return
    s = ease_out_back(clamp01(t_pop / 0.35))
    cw, ch = 420 * s, 230 * s
    cx, cy = 900, 300
    lay = Image.new('RGBA', frame.size, (0, 0, 0, 0))
    d = ImageDraw.Draw(lay)
    d.rounded_rectangle((cx - cw / 2 + 8, cy - ch / 2 + 10, cx + cw / 2 + 8, cy + ch / 2 + 10), 28 * s,
                        fill=(0, 0, 0, 50))
    d.rounded_rectangle((cx - cw / 2, cy - ch / 2, cx + cw / 2, cy + ch / 2), 28 * s, fill=(255, 255, 252),
                        outline=INK, width=max(1, int(5 * s)))
    if s > 0.6:
        d.text((cx, cy - 58 * s), label, font=font('bold', int(30 * s)), fill=(120, 116, 108), anchor='mm')
        d.text((cx, cy + 22 * s), f'${value:,.0f}', font=font('display', int(110 * s)), fill=col, anchor='mm')
    frame.alpha_composite(lay)


def ben_state(t):
    """Pose, mood, blink, talk for Ben at time t."""
    pose = 'point' if 3.2 <= t < 5.8 else 'idle'
    mood = 'shock' if 5.0 <= t < 5.8 else 'smile'
    blink = any(b <= t < b + 0.12 for b in (1.6, 4.2, 7.6))
    speaking = (0.2 <= t < 2.9) or (3.3 <= t < 4.9) or (6.0 <= t < 8.6)
    talk = speaking and int(t * FPS / 4) % 2 == 0          # lip flap every 4 frames
    if mood == 'shock':
        talk = True
    return dict(pose=pose, mood=mood, blink=blink, talk=talk)


def frame_at(bg, i):
    t = i / FPS
    fr = bg.copy()
    # --- Ben (left), breathing
    st = ben_state(t)
    br = math.sin(t * 2 * math.pi * 0.8)
    jump = 0
    if 5.0 <= t < 5.35:                                      # startled hop when the money hits $33
        jump = -60 * math.sin(math.pi * (t - 5.0) / 0.35)
    place(fr, sprite('ben', **st), 330, 604 + jump, 430, 1 - 0.012 * br, 1 + 0.012 * br)

    # --- money card: $3,000 pops in, counts down to $33, slides away
    if t < 6.2:
        if t < 3.4:
            val, col, lab = 3000, GREEN, 'MONTHLY PAY'
        else:
            k = ease_in_out((t - 3.4) / 1.6)
            val = 3000 - (3000 - 33) * k
            col, lab = (RED if k > 0.02 else GREEN), ('LEFT OVER' if k > 0.02 else 'MONTHLY PAY')
        off = ease_in_out((t - 5.8) / 0.4) if t > 5.8 else 0
        lay = Image.new('RGBA', fr.size, (0, 0, 0, 0))
        money_card(lay, t - 0.7, val, lab, col)
        fr.alpha_composite(lay, (0, int(-off * 520)))

    # --- Piggy Ben bounces in from the right, a coin drops into the slot
    if t >= 6.0:
        tt = t - 6.0
        x = 1400 - (1400 - 930) * ease_in_out(tt / 0.9)
        hop = -abs(math.sin(tt * math.pi * 3.3)) * 70 * max(0, 1 - tt / 0.9)
        sx = sy = 1.0
        mood = 'smile'
        coin_y = None
        if tt >= 1.2:
            ct = tt - 1.2
            coin_y = -60 + 0.5 * 2600 * ct ** 2                # gravity
            land = 246                                         # slot height above the piggy feet (300px tall)
            if coin_y >= 604 - land:
                coin_y = None
                it = ct - math.sqrt(2 * (604 - land + 60) / 2600)
                if it < 0.35:                                  # impact squash, then settle
                    a = math.exp(-it * 9) * math.cos(it * 30)
                    sx, sy = 1 + 0.10 * a, 1 - 0.10 * a
                    mood = 'shock'
        place(fr, sprite('piggy', mood=mood, blink=(8.3 <= t < 8.42), talk=True), x, 604 + hop, 300, sx, sy)
        if coin_y is not None:
            p = Pen(W, H, S=1)
            coin(p, x, coin_y, 26)
            fr.alpha_composite(p.img)

    # --- captions
    if t < 3.2:
        caption(fr, 'This is Ben. He makes $3,000 a month.', {'$3,000'})
    elif t < 5.9:
        caption(fr, 'After bills... thirty-three dollars left.', {'thirty-three'})
    else:
        caption(fr, 'So Ben starts saving. One coin at a time.', {'saving'})
    return fr.convert('RGB')


def main():
    bg = background()
    n = int(DUR * FPS)
    path = os.path.join(OUT, 'demo_9s.mp4')
    enc = subprocess.Popen(['ffmpeg', '-y', '-loglevel', 'error', '-f', 'rawvideo', '-pix_fmt', 'rgb24',
                            '-s', f'{W}x{H}', '-r', str(FPS), '-i', '-', '-c:v', 'libx264', '-preset', 'medium',
                            '-crf', '20', '-pix_fmt', 'yuv420p', '-movflags', '+faststart', path],
                           stdin=subprocess.PIPE)
    keep = {int(s * FPS): None for s in (1.0, 4.4, 5.2, 6.5, 7.75, 8.6)}
    for i in range(n):
        f = frame_at(bg, i)
        enc.stdin.write(f.tobytes())
        if i in keep:
            keep[i] = f
    enc.stdin.close()
    enc.wait()
    # contact sheet of key frames
    tw, th = 640, 360
    sheet = Image.new('RGB', (tw * 3 + 40, th * 2 + 30), (18, 19, 23))
    for k, (i, f) in enumerate(sorted(keep.items())):
        sheet.paste(f.resize((tw, th), Image.LANCZOS), (10 + (k % 3) * (tw + 10), 10 + (k // 3) * (th + 10)))
    sheet.save(os.path.join(OUT, 'frames.jpg'), quality=90)
    print('wrote', path)


if __name__ == '__main__':
    main()
