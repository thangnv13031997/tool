"""Horror sound: generated music beds, ambiences and SFX, plus the final mix.

Your own files always win: put them in
  library/music/<mood>/*.mp3|wav      (calm_normal, uneasy, tension_rise, dread, chase, aftermath, host)
  library/ambience/<name>.mp3|wav     (rain, forest, bus, hum, ...)
  library/sfx/<name>.mp3|wav          (hit, knock, door_creak, ...)
Generated sounds are cached in library/_generated.
Everything is pure numpy; mp3/m4a are decoded with ffmpeg.
"""
import glob
import hashlib
import os
import random
import subprocess
import sys
import wave
import numpy as np

SR = 48000
NOFLAGS = 0x08000000 if sys.platform == 'win32' else 0
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
LIB = os.path.join(ROOT, 'library')
GEN = os.path.join(LIB, '_generated')
GEN_VERSION = 'v1'


# ------------------------------------------------------------------ io
def write_wav(path, data, sr=SR):
    d = np.asarray(data, np.float32)
    if d.ndim == 1:
        d = np.stack([d, d], axis=1)
    d = (np.clip(d, -1, 1) * 32767).astype(np.int16)
    with wave.open(path, 'wb') as w:
        w.setnchannels(2)
        w.setsampwidth(2)
        w.setframerate(sr)
        w.writeframes(d.tobytes())


def read_any(path, ff='ffmpeg'):
    """Decode any audio file to float32 stereo at SR."""
    if path.lower().endswith('.wav'):
        try:
            with wave.open(path, 'rb') as w:
                if w.getsampwidth() == 2:
                    n, ch, sr = w.getnframes(), w.getnchannels(), w.getframerate()
                    a = np.frombuffer(w.readframes(n), np.int16).astype(np.float32) / 32768.0
                    a = a.reshape(-1, ch)
                    if ch == 1:
                        a = np.repeat(a, 2, axis=1)
                    a = a[:, :2]
                    if sr != SR:
                        idx = np.linspace(0, len(a) - 1, int(len(a) * SR / sr))
                        a = np.stack([np.interp(idx, np.arange(len(a)), a[:, c]) for c in (0, 1)], axis=1).astype(np.float32)
                    return a
        except wave.Error:
            pass
    r = subprocess.run([ff, '-v', 'error', '-i', path, '-f', 'f32le', '-ac', '2', '-ar', str(SR), '-'],
                       capture_output=True, creationflags=NOFLAGS)
    if r.returncode != 0:
        raise RuntimeError('Không đọc được file âm thanh: ' + path)
    return np.frombuffer(r.stdout, np.float32).reshape(-1, 2).copy()


# ------------------------------------------------------------------ dsp
def fft_filter(x, lo=None, hi=None, peak=None, q=4.0, sr=SR):
    n = len(x)
    if n < 16:
        return x
    N = 1 << int(np.ceil(np.log2(n + 1)))
    X = np.fft.rfft(x, N, axis=0)
    f = np.fft.rfftfreq(N, 1 / sr)
    g = np.ones_like(f)
    if lo:
        g *= 1 / (1 + (lo / np.maximum(f, 1)) ** 4)
    if hi:
        g *= 1 / (1 + (f / hi) ** 4)
    if peak:
        g *= 1 + q * np.exp(-((f - peak) / (peak * 0.08)) ** 2)
    if X.ndim == 2:
        g = g[:, None]
    return np.fft.irfft(X * g, N, axis=0)[:n].astype(np.float32)


def noise(n, kind='white', seed=0):
    rnd = np.random.default_rng(seed)
    w = rnd.normal(0, 1, n).astype(np.float32)
    if kind == 'white':
        return w
    if kind == 'pink':
        N = 1 << int(np.ceil(np.log2(n)))
        X = np.fft.rfft(w, N)
        f = np.fft.rfftfreq(N, 1 / SR)
        X /= np.sqrt(np.maximum(f, 20))
        y = np.fft.irfft(X, N)[:n]
        return (y / (np.std(y) + 1e-9)).astype(np.float32)
    if kind == 'brown':
        y = np.cumsum(w)
        y = y - np.convolve(y, np.ones(4801) / 4801, mode='same')
        return (y / (np.std(y) + 1e-9)).astype(np.float32)
    return w


def env_ad(n, a=0.005, d=0.3, sr=SR):
    t = np.arange(n) / sr
    e = np.minimum(1, t / max(a, 1e-4)) * np.exp(-np.maximum(0, t - a) / max(d, 1e-4))
    return e.astype(np.float32)


def tone(freq, secs, kind='sine', sr=SR, phase=0.0):
    t = np.arange(int(secs * sr)) / sr
    if callable(freq):
        ph = 2 * np.pi * np.cumsum(freq(t)) / sr + phase
    else:
        ph = 2 * np.pi * freq * t + phase
    if kind == 'sine':
        return np.sin(ph).astype(np.float32)
    if kind == 'saw':
        return (2 * ((ph / (2 * np.pi)) % 1.0) - 1).astype(np.float32)
    if kind == 'square':
        return np.sign(np.sin(ph)).astype(np.float32)
    if kind == 'tri':
        return (2 * np.abs(2 * ((ph / (2 * np.pi)) % 1.0) - 1) - 1).astype(np.float32)
    return np.sin(ph).astype(np.float32)


def reverb(x, wet=0.3, secs=2.2, decay=2.2, seed=3):
    rnd = np.random.default_rng(seed)
    n = int(secs * SR)
    t = np.arange(n) / SR
    out = []
    xs = x if x.ndim == 2 else x[:, None]
    for c in range(xs.shape[1]):
        ir = rnd.normal(0, 1, n).astype(np.float32) * np.exp(-decay * t)
        ir[:int(0.015 * SR)] = 0
        ir = fft_filter(ir, hi=6000)
        ir /= np.sqrt(np.sum(ir ** 2)) + 1e-9
        L = len(xs) + n - 1
        N = 1 << int(np.ceil(np.log2(L)))
        y = np.fft.irfft(np.fft.rfft(xs[:, c], N) * np.fft.rfft(ir, N), N)[:len(xs)]
        out.append(xs[:, c] * (1 - wet * 0.4) + y.astype(np.float32) * wet * 0.5)
    y = np.stack(out, axis=1)
    return y if x.ndim == 2 else y[:, 0]


def stereo(x, pan=0.0, width=0.0, seed=0):
    if x.ndim == 2:
        return x
    l = x * np.sqrt(0.5 * (1 - pan))
    r = x * np.sqrt(0.5 * (1 + pan))
    if width > 0:
        d = int(0.012 * SR)
        r = np.concatenate([np.zeros(d, np.float32), r[:-d]]) * (1 - width * 0.3) + r * width * 0.3
    return np.stack([l, r], axis=1).astype(np.float32) * 1.41


def loopify(x, fade=1.0):
    """Make a buffer loop seamlessly by crossfading the tail into the head."""
    k = int(fade * SR)
    if len(x) <= 2 * k:
        return x
    head = x[:k]
    tail = x[-k:]
    w = np.linspace(0, 1, k, dtype=np.float32)
    if x.ndim == 2:
        w = w[:, None]
    out = x[:-k].copy()
    out[:k] = head * w + tail * (1 - w)
    return out


def norm(x, peak=0.9):
    m = float(np.max(np.abs(x))) if len(x) else 0
    return (x * (peak / m)).astype(np.float32) if m > 1e-6 else x


def note(midi):
    return 440.0 * 2 ** ((midi - 69) / 12)


# ------------------------------------------------------------------ music beds (32 s loops)
def _pluck(freq, secs, bright=0.5, decay=1.2):
    n = int(secs * SR)
    x = np.zeros(n, np.float32)
    for h, a in ((1, 1.0), (2, 0.45 * bright), (3, 0.22 * bright), (4, 0.1 * bright)):
        x += a * tone(freq * h, secs) * env_ad(n, 0.004, decay / h)
    return x


def music_calm_normal(secs=32, seed=1):
    rnd = random.Random(seed)
    n = int(secs * SR)
    out = np.zeros(n, np.float32)
    prog = [(57, 60, 64), (53, 57, 60), (48, 52, 55), (55, 59, 62)]
    beat = 0.75
    t = 0.0
    i = 0
    while t < secs - 2:
        chord = prog[(i // 8) % 4]
        nt = chord[i % 3] + (12 if i % 4 == 3 else 0)
        p = _pluck(note(nt), 2.6, 0.6, 1.0) * (0.22 + 0.06 * rnd.random())
        a = int(t * SR)
        out[a:a + len(p)] += p[:n - a]
        t += beat
        i += 1
    pad = np.zeros(n, np.float32)
    for k, ch in enumerate(prog):
        seg = int(secs / 4 * SR)
        for m in ch:
            pad[k * seg:(k + 1) * seg] += 0.05 * tone(note(m - 12), secs / 4, 'tri')[:seg]
    pad = fft_filter(pad, hi=900)
    x = reverb(stereo(out + pad, width=0.6), 0.35)
    return norm(loopify(x, 1.5), 0.8)


def music_uneasy(secs=32, seed=2):
    n = int(secs * SR)
    t = np.arange(n) / SR
    d = (tone(note(33), secs, 'saw') + tone(note(33) * 1.006, secs, 'saw') + 0.7 * tone(note(34), secs, 'saw'))
    d = fft_filter(d, hi=380) * (0.55 + 0.45 * np.sin(2 * np.pi * t / secs * 2) ** 2)
    rnd = random.Random(seed)
    hi = np.zeros(n, np.float32)
    for _ in range(6):
        st = rnd.uniform(1, secs - 6)
        f = note(rnd.choice((81, 82, 88, 89)))
        seg = tone(lambda tt, f=f: f * (1 + 0.004 * np.sin(2 * np.pi * 5 * tt)), 5.0) * env_ad(int(5 * SR), 1.5, 1.8)
        a = int(st * SR)
        hi[a:a + len(seg)] += seg[:n - a] * 0.06
    x = stereo(d * 0.35, width=0.8) + stereo(hi, pan=0.3)
    x = reverb(x, 0.4, 3.0, 1.6)
    return norm(loopify(x, 2.0), 0.75)


def music_tension_rise(secs=32, seed=3):
    """Shepard tone (endless rise) + heartbeat pulse."""
    n = int(secs * SR)
    t = np.arange(n) / SR
    x = np.zeros(n, np.float32)
    period = secs
    for k in range(7):
        pos = ((t / period) + k / 7) % 1.0
        f = 55 * 2 ** (pos * 7)
        amp = np.exp(-((pos - 0.5) / 0.22) ** 2)
        ph = 2 * np.pi * np.cumsum(f) / SR
        x += np.sin(ph).astype(np.float32) * amp.astype(np.float32)
    x = fft_filter(x, hi=1800) * 0.16
    bpm = 72
    pulse = np.zeros(n, np.float32)
    beat = 60 / bpm
    b = 0.0
    while b < secs - 0.5:
        for off, g in ((0.0, 1.0), (0.22, 0.7)):
            a = int((b + off) * SR)
            hit = tone(lambda tt: 55 * np.exp(-tt * 8) + 38, 0.35) * env_ad(int(0.35 * SR), 0.004, 0.12) * g
            pulse[a:a + len(hit)] += hit[:n - a]
        b += beat
    y = stereo(x, width=0.7) + stereo(pulse * 0.5)
    return norm(loopify(reverb(y, 0.25), 1.0), 0.8)


def music_dread(secs=32, seed=4):
    n = int(secs * SR)
    t = np.arange(n) / SR
    sub = tone(note(21) * 1.0, secs) * 0.5 + tone(note(28), secs) * 0.3
    sub *= (0.6 + 0.4 * np.sin(2 * np.pi * t / 8) ** 2)
    scrape = fft_filter(noise(n, 'white', seed), lo=900, hi=3000, peak=1500, q=12) * 0.0
    rnd = random.Random(seed)
    for _ in range(5):
        st = rnd.uniform(0, secs - 4)
        ln = rnd.uniform(1.5, 3.0)
        a, b = int(st * SR), int((st + ln) * SR)
        e = np.sin(np.linspace(0, np.pi, b - a)) ** 2
        f0 = rnd.uniform(600, 1400)
        seg = fft_filter(noise(b - a, 'white', rnd.randint(0, 999)), peak=f0, q=30, lo=300, hi=4000)
        scrape[a:b] += seg * e * 0.12
    cl = sum(tone(note(m), secs, 'tri') for m in (45, 46, 51)) * 0.04
    cl = fft_filter(cl, hi=700) * (0.5 + 0.5 * np.sin(2 * np.pi * t / secs) ** 2)
    x = stereo(sub * 0.6) + stereo(scrape, width=0.9) + stereo(cl, width=0.6)
    return norm(loopify(reverb(x, 0.45, 3.2, 1.4), 2.0), 0.8)


def music_chase(secs=32, seed=5):
    n = int(secs * SR)
    out = np.zeros(n, np.float32)
    bpm = 150
    step = 60 / bpm / 2
    seq = [45, 45, 48, 45, 46, 45, 51, 49]
    t = 0.0
    i = 0
    while t < secs - 0.3:
        f = note(seq[i % 8] - 12)
        s = fft_filter(tone(f, 0.22, 'saw') + tone(f * 1.01, 0.22, 'saw'), hi=900) * env_ad(int(0.22 * SR), 0.003, 0.08)
        a = int(t * SR)
        out[a:a + len(s)] += s[:n - a] * 0.35
        if i % 4 == 0:
            k = tone(lambda tt: 70 * np.exp(-tt * 10) + 45, 0.5) * env_ad(int(0.5 * SR), 0.002, 0.18)
            out[a:a + len(k)] += k[:n - a] * 0.9
        if i % 4 == 2:
            sn = fft_filter(noise(int(0.2 * SR), seed=i), lo=900, hi=6000) * env_ad(int(0.2 * SR), 0.001, 0.05)
            out[a:a + len(sn)] += sn[:n - a] * 0.25
        t += step
        i += 1
    strings = fft_filter(sum(tone(note(m), secs, 'saw') for m in (69, 70)), hi=2500) * 0.05
    x = stereo(out, width=0.4) + stereo(strings, width=0.9)
    return norm(loopify(reverb(x, 0.2, 1.4, 3), 0.5), 0.85)


def music_aftermath(secs=32, seed=6):
    n = int(secs * SR)
    out = np.zeros(n, np.float32)
    mel = [76, 74, 72, 71, 72, 69, 71, 64, 76, 77, 76, 74, 72, 71, 69, 0]
    t = 0.0
    for i, m in enumerate(mel * 2):
        if t > secs - 2:
            break
        if m:
            f = note(m) * (1 + 0.003 * ((i % 3) - 1))
            nn = int(2.2 * SR)
            s = (tone(f, 2.2) + 0.4 * tone(f * 2.76, 2.2) + 0.2 * tone(f * 5.4, 2.2)) * env_ad(nn, 0.002, 0.7)
            a = int(t * SR)
            out[a:a + nn] += s[:n - a] * 0.2
        t += 1.0
    pad = fft_filter(sum(tone(note(m), secs, 'tri') for m in (45, 52, 57)), hi=600) * 0.04
    x = reverb(stereo(out, width=0.7) + stereo(pad), 0.5, 3.0, 1.5)
    return norm(loopify(x, 2.0), 0.7)


def music_host(secs=32, seed=7):
    n = int(secs * SR)
    t = np.arange(n) / SR
    bass = np.zeros(n, np.float32)
    seq = [45, 43, 41, 40]
    for i in range(int(secs / 2)):
        f = note(seq[i % 4] - 12)
        s = tone(f, 2.0, 'tri') * env_ad(int(2.0 * SR), 0.01, 0.8)
        a = int(i * 2.0 * SR)
        bass[a:a + len(s)] += s[:n - a] * 0.4
    crackle = np.zeros(n, np.float32)
    rnd = np.random.default_rng(seed)
    idx = rnd.integers(0, n, int(secs * 14))
    crackle[idx] = rnd.uniform(-0.25, 0.25, len(idx))
    crackle = fft_filter(crackle, lo=1200)
    pad = fft_filter(sum(tone(note(m), secs, 'saw') for m in (57, 60, 64)), hi=700) * 0.03 * (0.7 + 0.3 * np.sin(t))
    x = reverb(stereo(bass + pad, width=0.5), 0.3) + stereo(crackle * 0.4, width=1)
    return norm(loopify(x, 1.0), 0.7)


MUSIC = {'calm_normal': music_calm_normal, 'uneasy': music_uneasy, 'tension_rise': music_tension_rise,
         'dread': music_dread, 'chase': music_chase, 'aftermath': music_aftermath, 'host': music_host}
MUSIC_GAIN = {'calm_normal': 0.5, 'uneasy': 0.85, 'tension_rise': 0.8, 'dread': 0.9, 'chase': 0.75,
              'aftermath': 0.7, 'host': 0.55}


# ------------------------------------------------------------------ ambiences (20 s loops)
def amb_room_tone(secs=20, s=1):
    return stereo(fft_filter(noise(int(secs * SR), 'brown', s), hi=300) * 0.05 + fft_filter(noise(int(secs * SR), 'pink', s + 1), lo=200, hi=2000) * 0.006, width=1)


def amb_hum(secs=20, s=2):
    n = int(secs * SR)
    t = np.arange(n) / SR
    h = (tone(60, secs) * 0.5 + tone(120, secs) * 0.35 + tone(180, secs) * 0.12 + tone(240, secs) * 0.08)
    h *= (0.85 + 0.15 * np.sin(2 * np.pi * 0.3 * t))
    buzz = fft_filter(noise(n, 'white', s), lo=2000, hi=6000) * 0.01 * (0.5 + 0.5 * np.sin(2 * np.pi * 120 * t))
    return stereo(h * 0.07 + buzz, width=0.5) + amb_room_tone(secs, s) * 0.6


def amb_fridge(secs=20, s=3):
    n = int(secs * SR)
    m = fft_filter(noise(n, 'brown', s), hi=180) * 0.06 + tone(50, secs) * 0.03
    return stereo(m, width=0.4) + amb_room_tone(secs, s) * 0.5


def amb_clock(secs=20, s=4):
    out = amb_room_tone(secs, s)[:, 0] * 0.7
    n = len(out)
    for i in range(int(secs)):
        for off, f in ((0.0, 4200), (0.5, 3600)):
            a = int((i + off) * SR)
            tick = fft_filter(noise(int(0.02 * SR), seed=i), lo=f * 0.7, hi=f * 1.3) * env_ad(int(0.02 * SR), 0.0005, 0.004)
            out[a:a + len(tick)] += tick[:n - a] * 0.18
    return stereo(out, pan=0.35)


def amb_night_outside(secs=20, s=5):
    n = int(secs * SR)
    t = np.arange(n) / SR
    wind = fft_filter(noise(n, 'pink', s), hi=700) * 0.05 * (0.6 + 0.4 * np.sin(2 * np.pi * t / 7))
    cr = np.zeros(n, np.float32)
    rnd = random.Random(s)
    for c in range(3):
        f = rnd.uniform(4200, 5200)
        rate = rnd.uniform(2.2, 3.4)
        chirp = tone(f, secs) * (np.sin(2 * np.pi * rate * t + c) > 0.6) * (0.5 + 0.5 * np.sin(2 * np.pi * 40 * t))
        cr += chirp * 0.012
    cr = fft_filter(cr, lo=3000)
    return stereo(wind, width=1) + stereo(cr, pan=0.3, width=0.8)


def amb_forest(secs=20, s=6):
    x = amb_night_outside(secs, s) * 0.7
    n = len(x)
    rnd = random.Random(s)
    for _ in range(int(secs / 4)):
        a = int(rnd.uniform(0, secs - 1) * SR)
        rustle = fft_filter(noise(int(0.6 * SR), seed=rnd.randint(0, 99)), lo=800, hi=5000) * env_ad(int(0.6 * SR), 0.1, 0.25) * 0.05
        x[a:a + len(rustle)] += stereo(rustle, pan=rnd.uniform(-0.7, 0.7))[:n - a]
    n2 = int(secs * SR)
    owl_at = int(secs * 0.6 * SR)
    for k, off in enumerate((0, 0.45, 0.75)):
        hoot = tone(lambda tt: 380 - 30 * tt, 0.35) * env_ad(int(0.35 * SR), 0.05, 0.12) * 0.03
        a = owl_at + int(off * SR)
        x[a:a + len(hoot)] += stereo(reverb(hoot, 0.5), pan=-0.5)[:n2 - a]
    return x


def amb_wind(secs=20, s=7):
    n = int(secs * SR)
    t = np.arange(n) / SR
    w = fft_filter(noise(n, 'pink', s), lo=150, hi=1200, peak=500, q=3) * 0.09 * (0.4 + 0.6 * np.sin(2 * np.pi * t / 9) ** 2)
    howl = fft_filter(noise(n, 'white', s + 1), peak=800, q=40, lo=400, hi=1400) * 0.02 * (np.sin(2 * np.pi * t / 6) ** 4)
    return stereo(w, width=1) + stereo(howl, pan=-0.3, width=0.7)


def amb_rain(secs=20, s=8):
    n = int(secs * SR)
    r = fft_filter(noise(n, 'white', s), lo=400, hi=9000) * 0.05
    drops = np.zeros(n, np.float32)
    rnd = np.random.default_rng(s)
    idx = rnd.integers(0, n, int(secs * 60))
    drops[idx] = rnd.uniform(0.2, 0.6, len(idx))
    drops = fft_filter(drops, lo=1500, hi=7000) * 0.4
    return stereo(r, width=1) + stereo(drops, width=1) + amb_room_tone(secs, s) * 0.5


def amb_storm(secs=20, s=9):
    x = amb_rain(secs, s) * 1.3 + amb_wind(secs, s) * 0.6
    n = len(x)
    a = int(secs * 0.4 * SR)
    th = fft_filter(noise(int(4 * SR), 'brown', s), hi=220) * env_ad(int(4 * SR), 0.15, 1.4) * 0.5
    x[a:a + len(th)] += stereo(th, width=1)[:n - a]
    return x


def _engine(secs, f0, s, rough=0.4):
    n = int(secs * SR)
    t = np.arange(n) / SR
    f = f0 * (1 + 0.02 * np.sin(2 * np.pi * 0.15 * t))
    e = np.sin(2 * np.pi * np.cumsum(f) / SR) * 0.5 + np.sin(4 * np.pi * np.cumsum(f) / SR) * 0.25
    e = e * (1 + rough * fft_filter(noise(n, 'white', s), hi=60))
    road = fft_filter(noise(n, 'pink', s + 1), lo=60, hi=900) * 0.05
    return (fft_filter(e.astype(np.float32), hi=400) * 0.06 + road).astype(np.float32)


def amb_bus(secs=20, s=10):
    x = stereo(_engine(secs, 38, s, 0.6), width=0.6)
    n = len(x)
    rnd = random.Random(s)
    for _ in range(4):
        a = int(rnd.uniform(0, secs - 1) * SR)
        rattle = fft_filter(noise(int(0.3 * SR), seed=rnd.randint(0, 99)), lo=2000, hi=7000) * env_ad(int(0.3 * SR), 0.01, 0.06) * 0.03
        x[a:a + len(rattle)] += stereo(rattle, pan=rnd.uniform(-0.8, 0.8))[:n - a]
    return x


def amb_car(secs=20, s=11):
    return stereo(_engine(secs, 30, s, 0.3), width=0.5)


def amb_highway(secs=20, s=12):
    x = amb_car(secs, s) * 0.6
    n = len(x)
    for k in range(2):
        a = int((4 + k * 9) * SR)
        ln = int(3 * SR)
        e = np.sin(np.linspace(0, np.pi, ln)) ** 2
        p = np.linspace(-0.9, 0.9, ln)
        pas = fft_filter(noise(ln, 'pink', s + k), lo=100, hi=2500) * e * 0.08
        x[a:a + ln, 0] += pas * np.sqrt(0.5 * (1 - p))
        x[a:a + ln, 1] += pas * np.sqrt(0.5 * (1 + p))
    return x


def amb_fire(secs=20, s=13):
    n = int(secs * SR)
    base = fft_filter(noise(n, 'brown', s), hi=500) * 0.06
    cr = np.zeros(n, np.float32)
    rnd = np.random.default_rng(s)
    idx = rnd.integers(0, n, int(secs * 25))
    cr[idx] = rnd.uniform(-0.6, 0.6, len(idx))
    cr = fft_filter(cr, lo=1500, hi=8000) * 0.5
    return stereo(base, width=0.6) + stereo(cr, width=0.8)


def amb_tv_static(secs=20, s=14):
    return stereo(fft_filter(noise(int(secs * SR), 'white', s), lo=200, hi=8000) * 0.05, width=0.3)


def amb_basement(secs=20, s=15):
    x = amb_room_tone(secs, s) * 1.2
    n = len(x)
    for i in range(int(secs / 2.3)):
        a = int((i * 2.3 + 0.7) * SR)
        drip = tone(lambda tt: 1400 + 900 * np.exp(-tt * 40), 0.08) * env_ad(int(0.08 * SR), 0.001, 0.02) * 0.05
        x[a:a + len(drip)] += stereo(reverb(drip, 0.6, 1.0, 3), pan=0.4)[:n - a]
    hum = fft_filter(noise(int(secs * SR), 'brown', s + 3), hi=120) * 0.05
    return x + stereo(hum)


def amb_crowd_far(secs=20, s=16):
    n = int(secs * SR)
    b = fft_filter(noise(n, 'pink', s), lo=250, hi=1800, peak=600, q=2) * 0.02
    return stereo(reverb(b, 0.5), width=1)


AMB = {'room_tone': amb_room_tone, 'hum': amb_hum, 'fridge': amb_fridge, 'clock': amb_clock,
       'night_outside': amb_night_outside, 'forest': amb_forest, 'wind': amb_wind, 'rain': amb_rain, 'storm': amb_storm,
       'bus': amb_bus, 'car': amb_car, 'highway': amb_highway, 'fire': amb_fire, 'tv_static': amb_tv_static,
       'basement': amb_basement, 'crowd_far': amb_crowd_far}


# ------------------------------------------------------------------ sfx
def sfx_hit(s=1):
    n = int(3.0 * SR)
    boom = tone(lambda t: 30 + 110 * np.exp(-t * 6), 3.0) * env_ad(n, 0.002, 0.9)
    crack = fft_filter(noise(n, 'white', s), hi=3000) * env_ad(n, 0.001, 0.08)
    x = boom * 0.9 + crack * 0.35
    return reverb(stereo(x, width=0.5), 0.35, 2.5, 1.8)


def sfx_screech(s=2):
    secs = 1.6
    n = int(secs * SR)
    x = np.zeros(n, np.float32)
    for f in (1180, 1250, 1320, 1870, 2490):
        x += tone(lambda t, f=f: f * (1 + 0.01 * np.sin(2 * np.pi * 7 * t)), secs, 'saw') * 0.12
    x = fft_filter(x, lo=600, hi=6000) * env_ad(n, 0.01, 0.5)
    return reverb(stereo(x, width=0.8), 0.4)


def sfx_riser(s=3):
    secs = 2.5
    n = int(secs * SR)
    t = np.arange(n) / SR
    nz = noise(n, 'white', s)
    chunks = []
    k = 12
    for i in range(k):
        a, b = i * n // k, (i + 1) * n // k
        chunks.append(fft_filter(nz[a:b], lo=200 + i * 300, hi=1200 + i * 900))
    x = np.concatenate(chunks) * (t / secs) ** 2 * 0.6
    x += tone(lambda tt: 200 * 2 ** (tt / secs * 3), secs, 'saw') * (t / secs) ** 3 * 0.1
    return stereo(x, width=1)


def sfx_whoosh(s=4):
    n = int(0.8 * SR)
    x = fft_filter(noise(n, 'pink', s), lo=300, hi=4000) * np.sin(np.linspace(0, np.pi, n)) ** 3 * 0.6
    p = np.linspace(-0.8, 0.8, n)
    return np.stack([x * np.sqrt(0.5 * (1 - p)), x * np.sqrt(0.5 * (1 + p))], axis=1).astype(np.float32) * 1.4


def sfx_knock(s=5, count=3):
    secs = count * 0.42 + 0.6
    n = int(secs * SR)
    x = np.zeros(n, np.float32)
    for i in range(count):
        a = int(i * 0.42 * SR)
        hit = (fft_filter(noise(int(0.15 * SR), 'white', s + i), lo=80, hi=900, peak=180, q=6)
               * env_ad(int(0.15 * SR), 0.001, 0.035))
        x[a:a + len(hit)] += hit * 0.9
    return reverb(stereo(x), 0.25, 0.8, 5)


def sfx_bang(s=6):
    return sfx_knock(s, 1) * 1.6


def sfx_door_creak(s=7):
    secs = 1.8
    n = int(secs * SR)
    t = np.arange(n) / SR
    f = 380 + 160 * np.sin(2 * np.pi * 0.6 * t) + 60 * np.sin(2 * np.pi * 3.1 * t)
    x = tone(lambda tt: 380 + 160 * np.sin(2 * np.pi * 0.6 * tt) + 60 * np.sin(2 * np.pi * 3.1 * tt), secs, 'saw')
    grain = (np.sin(2 * np.pi * 34 * t) > 0.2).astype(np.float32)
    x = fft_filter(x * grain, lo=300, hi=3500) * np.sin(np.linspace(0, np.pi, n)) * 0.3
    return reverb(stereo(x, width=0.3), 0.3, 1.2, 3)


def sfx_footsteps(s=8, count=6, gap=0.55):
    n = int((count * gap + 0.5) * SR)
    x = np.zeros(n, np.float32)
    for i in range(count):
        a = int(i * gap * SR)
        st = fft_filter(noise(int(0.12 * SR), 'pink', s + i), lo=60, hi=1500) * env_ad(int(0.12 * SR), 0.002, 0.03)
        x[a:a + len(st)] += st * (0.6 + 0.1 * (i % 2))
    return reverb(stereo(x), 0.3, 1.0, 4)


def sfx_phone_buzz(s=9):
    n = int(1.6 * SR)
    t = np.arange(n) / SR
    x = tone(175, 1.6, 'square') * ((t % 0.8) < 0.45) * 0.12
    return stereo(fft_filter(x, hi=1200), pan=0.2)


def sfx_notification(s=10):
    n = int(1.0 * SR)
    x = (tone(1318, 1.0) * env_ad(n, 0.002, 0.15) + 0.6 * np.concatenate([np.zeros(int(0.12 * SR)), tone(1760, 0.88) * env_ad(int(0.88 * SR), 0.002, 0.2)]))
    return reverb(stereo(x * 0.3), 0.2)


def sfx_heartbeat(s=11, beats=4, bpm=88):
    gap = 60 / bpm
    n = int((beats * gap + 0.6) * SR)
    x = np.zeros(n, np.float32)
    for i in range(beats):
        for off, g in ((0.0, 1.0), (0.2, 0.7)):
            a = int((i * gap + off) * SR)
            h = tone(lambda tt: 60 * np.exp(-tt * 6) + 35, 0.3) * env_ad(int(0.3 * SR), 0.003, 0.09) * g
            x[a:a + len(h)] += h
    return stereo(x * 0.9)


def sfx_static_burst(s=12):
    n = int(0.6 * SR)
    x = fft_filter(noise(n, 'white', s), lo=300, hi=9000) * env_ad(n, 0.002, 0.25) * 0.5
    return stereo(x, width=0.5)


def sfx_switch(s=13):
    n = int(0.15 * SR)
    x = fft_filter(noise(n, 'white', s), lo=1500, hi=8000) * env_ad(n, 0.0005, 0.008)
    return stereo(x * 0.5)


def sfx_lights_out(s=14):
    a = sfx_switch(s)
    n = int(1.2 * SR)
    t = np.arange(n) / SR
    hum = (tone(120, 1.2) * 0.1 * np.exp(-t * 6)).astype(np.float32)
    out = np.zeros((n, 2), np.float32)
    out[:len(a)] += a
    out += stereo(hum)
    return out


def sfx_thud(s=15):
    n = int(1.0 * SR)
    x = tone(lambda t: 45 + 60 * np.exp(-t * 10), 1.0) * env_ad(n, 0.002, 0.18) + fft_filter(noise(n, 'brown', s), hi=500) * env_ad(n, 0.001, 0.05) * 0.4
    return reverb(stereo(x * 0.9), 0.3, 1.2, 4)


def sfx_glass_tap(s=16, count=3):
    n = int((count * 0.35 + 0.6) * SR)
    x = np.zeros(n, np.float32)
    for i in range(count):
        a = int(i * 0.35 * SR)
        tap = (tone(2900, 0.3) + 0.5 * tone(4600, 0.3)) * env_ad(int(0.3 * SR), 0.0005, 0.05)
        x[a:a + len(tap)] += tap * 0.15
    return reverb(stereo(x), 0.3)


def sfx_bus_brakes(s=17):
    secs = 2.2
    n = int(secs * SR)
    sq = tone(lambda t: 2600 - 400 * t / secs, secs, 'saw') * np.sin(np.linspace(0, np.pi, n)) * 0.05
    sq = fft_filter(sq, lo=1500, hi=5000)
    hiss = fft_filter(noise(n, 'white', s), lo=2500) * np.concatenate([np.zeros(int(1.4 * SR)), env_ad(n - int(1.4 * SR), 0.01, 0.4)]) * 0.12
    return stereo(sq + hiss, width=0.5)


def sfx_door_hiss(s=18):
    n = int(1.0 * SR)
    return stereo(fft_filter(noise(n, 'white', s), lo=2000) * env_ad(n, 0.01, 0.35) * 0.18, width=0.6)


def sfx_car_door(s=19):
    x = sfx_thud(s) * 0.8
    c = sfx_switch(s + 1)
    x[:len(c)] += c
    return x


def sfx_breath(s=20):
    n = int(1.4 * SR)
    t = np.arange(n) / SR
    e = np.sin(np.pi * np.clip(t / 0.6, 0, 1)) ** 2 * (t < 0.6) + 0.7 * np.sin(np.pi * np.clip((t - 0.7) / 0.6, 0, 1)) ** 2 * (t > 0.7)
    x = fft_filter(noise(n, 'pink', s), lo=500, hi=4500) * e * 0.12
    return stereo(x)


def sfx_whispers(s=21):
    n = int(3.0 * SR)
    t = np.arange(n) / SR
    x = np.zeros(n, np.float32)
    for k in range(4):
        e = (0.5 + 0.5 * np.sin(2 * np.pi * (3 + k) * t + k)) * (0.5 + 0.5 * np.sin(2 * np.pi * 0.7 * t + k * 2))
        x += fft_filter(noise(n, 'white', s + k), lo=1200, hi=6000, peak=2500 + k * 400, q=4) * e * 0.04
    return reverb(stereo(x, width=1), 0.5)


def sfx_bell(s=22):
    n = int(4.0 * SR)
    x = sum(tone(220 * r, 4.0) * a for r, a in ((1, 1), (2.4, 0.5), (3.9, 0.3), (5.4, 0.2))) * env_ad(n, 0.003, 1.4)
    return reverb(stereo(x * 0.15), 0.5, 3.0, 1.4)


def sfx_music_box(s=23):
    out = np.zeros(int(3.5 * SR), np.float32)
    for i, m in enumerate((84, 83, 81, 79, 81)):
        nn = int(1.2 * SR)
        a = int(i * 0.45 * SR)
        f = note(m)
        out[a:a + nn] += ((tone(f, 1.2) + 0.4 * tone(f * 2.76, 1.2)) * env_ad(nn, 0.001, 0.35))[:len(out) - a] * 0.15
    return reverb(stereo(out), 0.4)


def sfx_dog_bark(s=24):
    out = np.zeros(int(1.6 * SR), np.float32)
    for k, a in enumerate((0.0, 0.45)):
        n = int(0.22 * SR)
        f = lambda t: 520 - 600 * t
        b = fft_filter(tone(f, 0.22, 'saw') + noise(n, 'white', s + k) * 0.3, lo=300, hi=2500, peak=900, q=3) * env_ad(n, 0.005, 0.07)
        out[int(a * SR):int(a * SR) + n] += b * 0.12
    return reverb(stereo(out, pan=-0.5), 0.6, 2.0, 2)


def sfx_scrape(s=25):
    n = int(2.0 * SR)
    x = fft_filter(noise(n, 'white', s), peak=1100, q=25, lo=500, hi=3000) * np.sin(np.linspace(0, np.pi, n)) * 0.25
    return reverb(stereo(x, width=0.6), 0.4)


SFX = {'hit': sfx_hit, 'screech': sfx_screech, 'riser': sfx_riser, 'whoosh': sfx_whoosh, 'knock': sfx_knock,
       'bang': sfx_bang, 'door_creak': sfx_door_creak, 'footsteps': sfx_footsteps, 'phone_buzz': sfx_phone_buzz,
       'notification': sfx_notification, 'heartbeat': sfx_heartbeat, 'static_burst': sfx_static_burst,
       'switch': sfx_switch, 'lights_out': sfx_lights_out, 'thud': sfx_thud, 'glass_tap': sfx_glass_tap,
       'bus_brakes': sfx_bus_brakes, 'door_hiss': sfx_door_hiss, 'car_door': sfx_car_door, 'breath': sfx_breath,
       'whispers': sfx_whispers, 'bell': sfx_bell, 'music_box': sfx_music_box, 'dog_bark': sfx_dog_bark,
       'scrape': sfx_scrape}
SFX_ALIASES = {'boom': 'hit', 'stinger': 'hit', 'impact': 'hit', 'scream': 'screech', 'violin': 'screech',
               'rise': 'riser', 'swoosh': 'whoosh', 'knocking': 'knock', 'door_knock': 'knock', 'slam': 'bang',
               'door_slam': 'bang', 'creak': 'door_creak', 'door_open': 'door_creak', 'steps': 'footsteps',
               'footstep': 'footsteps', 'vibrate': 'phone_buzz', 'buzz': 'phone_buzz', 'text': 'notification',
               'ding': 'notification', 'message': 'notification', 'heart': 'heartbeat', 'static': 'static_burst',
               'click': 'switch', 'light_switch': 'switch', 'power_out': 'lights_out', 'fall': 'thud',
               'tap': 'glass_tap', 'window_tap': 'glass_tap', 'brakes': 'bus_brakes', 'hiss': 'door_hiss',
               'breathing': 'breath', 'whisper': 'whispers', 'chime': 'bell', 'bark': 'dog_bark',
               'distant_dog': 'dog_bark', 'scratch': 'scrape', 'scratching': 'scrape', 'buzzing_light': 'switch',
               'paper_rustle': 'whoosh', 'hit_low_boom': 'hit'}


AMB_RMS = {'room_tone': 0.02, 'clock': 0.025, 'hum': 0.03, 'fridge': 0.03, 'night_outside': 0.035, 'forest': 0.04,
           'wind': 0.05, 'rain': 0.06, 'storm': 0.07, 'bus': 0.05, 'car': 0.045, 'highway': 0.05, 'fire': 0.045,
           'tv_static': 0.03, 'basement': 0.03, 'crowd_far': 0.025}
SFX_GAIN = {'breath': 0.45, 'whispers': 0.5, 'switch': 0.6, 'phone_buzz': 0.6, 'notification': 0.6, 'glass_tap': 0.7,
            'footsteps': 0.7, 'door_creak': 0.7, 'bell': 0.6, 'music_box': 0.6, 'dog_bark': 0.5, 'heartbeat': 0.8,
            'door_hiss': 0.5, 'bus_brakes': 0.6, 'scrape': 0.6, 'riser': 0.7}


# ------------------------------------------------------------------ library access
class Library:
    def __init__(self, ff='ffmpeg', log=print):
        self.ff = ff
        self.log = log
        self.cache = {}
        os.makedirs(GEN, exist_ok=True)
        for d in ('music', 'ambience', 'sfx'):
            os.makedirs(os.path.join(LIB, d), exist_ok=True)
        for m in MUSIC:
            os.makedirs(os.path.join(LIB, 'music', m), exist_ok=True)

    def _user_file(self, folder, name):
        pats = [os.path.join(LIB, folder, name, '*'), os.path.join(LIB, folder, name + '.*')]
        files = []
        for p in pats:
            files += [f for f in glob.glob(p) if f.lower().endswith(('.wav', '.mp3', '.m4a', '.ogg', '.flac'))]
        return sorted(files)

    def _generated(self, kind, name, fn):
        path = os.path.join(GEN, f'{kind}_{name}_{GEN_VERSION}.wav')
        if not os.path.exists(path):
            self.log(f'Đang tạo âm thanh {kind}: {name}...')
            x = np.asarray(fn(), np.float32)
            if kind == 'amb':
                x = x * (AMB_RMS.get(name, 0.04) / (float(np.sqrt(np.mean(x ** 2))) + 1e-9))
            elif kind == 'music':
                x = x * (0.11 / (float(np.sqrt(np.mean(x ** 2))) + 1e-9))
            else:
                x = norm(x, 0.9) * SFX_GAIN.get(name, 1.0)
            pk = float(np.max(np.abs(x)))
            if pk > 0.98:
                x = x * (0.98 / pk)
            write_wav(path, x)
        return path

    def get(self, kind, name, variant=0):
        key = (kind, name, variant)
        if key in self.cache:
            return self.cache[key]
        folder = {'music': 'music', 'amb': 'ambience', 'sfx': 'sfx'}[kind]
        user = self._user_file(folder, name)
        if user:
            path = user[variant % len(user)]
        else:
            table = {'music': MUSIC, 'amb': AMB, 'sfx': SFX}[kind]
            if name not in table:
                return None
            path = self._generated(kind, name, table[name])
        try:
            data = read_any(path, self.ff)
        except Exception as e:  # noqa
            self.log(f'Lỗi đọc {path}: {e}')
            return None
        if user and len(data):
            # bring your own files to the same loudness as the generated ones
            rms = float(np.sqrt(np.mean(np.asarray(data, np.float32) ** 2))) + 1e-9
            if kind == 'music':
                data = data * min(8.0, 0.11 / rms)
            elif kind == 'amb':
                data = data * min(8.0, AMB_RMS.get(name, 0.04) / rms)
        if len(self.cache) > 40:
            self.cache.pop(next(iter(self.cache)))
        self.cache[key] = data
        return data

    def has_user(self, kind, name):
        folder = {'music': 'music', 'amb': 'ambience', 'sfx': 'sfx'}[kind]
        return bool(self._user_file(folder, name))


def resolve_sfx(name):
    n = (name or '').strip().lower().replace(' ', '_').replace('-', '_')
    n = SFX_ALIASES.get(n, n)
    return n, n in SFX


# ------------------------------------------------------------------ mixing
def _place(track, clip, t0, gain=1.0, fade_in=0.0, fade_out=0.0, length=None):
    a = int(t0 * SR)
    if a >= len(track) or clip is None or len(clip) == 0:
        return
    if a < 0:
        clip = clip[-a:]
        a = 0
    n = min(len(clip), len(track) - a)
    if length is not None:
        n = min(n, int(length * SR))
    c = clip[:n] * gain
    if fade_in > 0:
        k = min(n, int(fade_in * SR))
        c[:k] *= np.linspace(0, 1, k, dtype=np.float32)[:, None]
    if fade_out > 0:
        k = min(n, int(fade_out * SR))
        c[n - k:] *= np.linspace(1, 0, k, dtype=np.float32)[:, None]
    track[a:a + n] += c


def _loop_to(clip, secs, offset=0.0):
    n = int(secs * SR)
    if clip is None or len(clip) == 0 or n <= 0:
        return np.zeros((max(0, n), 2), np.float32)
    off = int(offset * SR) % len(clip)
    reps = int(np.ceil((n + off) / len(clip))) + 1
    return np.tile(clip, (reps, 1))[off:off + n]


def smooth_env(x, attack=0.03, release=0.45, rate=SR):
    """Peak follower on a mono signal, decimated for speed."""
    hop = 240
    m = np.abs(x[:len(x) // hop * hop]).reshape(-1, hop).max(axis=1) if len(x) >= hop else np.abs(x)
    a = np.exp(-1 / (attack * rate / hop))
    r = np.exp(-1 / (release * rate / hop))
    out = np.zeros_like(m)
    v = 0.0
    for i, s in enumerate(m):
        c = a if s > v else r
        v = c * v + (1 - c) * s
        out[i] = v
    full = np.repeat(out, hop)
    if len(full) < len(x):
        full = np.concatenate([full, np.full(len(x) - len(full), full[-1] if len(full) else 0)])
    return full[:len(x)].astype(np.float32)


def mix(total, voice, scenes, lib, cfg, log=print, sfx_events=None):
    """voice: mono float32 at 48 kHz. scenes: normalised scenes with start/duration/mood/ambience/events.
    Returns stereo float32 track."""
    n = int(np.ceil(total * SR)) + SR
    v = np.zeros(n, np.float32)
    v[:len(voice)] = voice[:n]
    music = np.zeros((n, 2), np.float32)
    amb = np.zeros((n, 2), np.float32)
    fxtrack = np.zeros((n, 2), np.float32)
    mvol = float(cfg.get('music_volume', 0.32))
    avol = float(cfg.get('ambience_volume', 0.55))
    sfxvol = float(cfg.get('sfx_volume', 0.9))
    # --- music segments (merge consecutive scenes with the same mood)
    segs = []
    for s in scenes:
        m = s.get('mood', 'uneasy')
        if segs and segs[-1][0] == m:
            segs[-1][2] = s['start'] + s['duration']
        else:
            segs.append([m, s['start'], s['start'] + s['duration']])
    xf = 1.6
    var = {}
    for m, a, b in segs:
        if m == 'silence':
            continue
        clip = lib.get('music', m, var.get(m, 0))
        var[m] = var.get(m, 0) + 1
        if clip is None:
            continue
        g = MUSIC_GAIN.get(m, 0.8) if not lib.has_user('music', m) else 0.7
        seg = _loop_to(clip, b - a + xf, offset=(a * 0.37) % 7)
        _place(music, seg, a, g * mvol, fade_in=xf if a > 0.1 else 0.3, fade_out=xf)
    # --- ambience segments
    segs = []
    for s in scenes:
        m = s.get('ambience') or 'none'
        if segs and segs[-1][0] == m:
            segs[-1][2] = s['start'] + s['duration']
        else:
            segs.append([m, s['start'], s['start'] + s['duration']])
    for m, a, b in segs:
        if m in ('none', None):
            continue
        clip = lib.get('amb', m)
        if clip is None:
            continue
        seg = _loop_to(clip, b - a + 0.8, offset=a % 11)
        _place(amb, seg, a, avol, fade_in=0.8, fade_out=0.8)
    # --- events and sfx
    duck_zero = []
    for s in scenes:
        for ev in s.get('events', []):
            T = s['start'] + ev['t']
            k = ev['kind']
            if k == 'jumpscare':
                sil = ev.get('silence', 0.8)
                duck_zero.append((T - sil - 0.12, T, T + 1.2))
                _place(fxtrack, lib.get('sfx', 'hit'), T, 1.0 * sfxvol)
                _place(fxtrack, lib.get('sfx', 'screech'), T, 0.8 * sfxvol)
            elif k == 'stinger':
                _place(fxtrack, lib.get('sfx', 'hit'), T, 0.75 * sfxvol)
            elif k == 'lights_out':
                _place(fxtrack, lib.get('sfx', 'lights_out'), T, 0.9 * sfxvol)
                duck_zero.append((T - 0.05, T + 0.05, T + 2.5))
            elif k == 'lights_on':
                _place(fxtrack, lib.get('sfx', 'switch'), T, 0.9 * sfxvol)
            elif k == 'glitch':
                _place(fxtrack, lib.get('sfx', 'static_burst'), T, 0.8 * sfxvol)
            elif k == 'reveal':
                _place(fxtrack, lib.get('sfx', 'riser'), T - 2.3, 0.45 * sfxvol)
                _place(fxtrack, lib.get('sfx', 'hit'), T, 0.5 * sfxvol)
            elif k == 'flash':
                _place(fxtrack, lib.get('sfx', 'whoosh'), T, 0.6 * sfxvol)
        if s.get('transition') == 'flash':
            _place(fxtrack, lib.get('sfx', 'whoosh'), s['start'] - 0.2, 0.5 * sfxvol)
    for e in (sfx_events or []):
        clip = lib.get('sfx', e['name'])
        if clip is None:
            log(f'Thiếu âm thanh "{e["name"]}"')
            continue
        _place(fxtrack, clip, e['t'], float(e.get('volume', 1.0)) * sfxvol, length=e.get('length'))
    # --- ducking under the voice
    env = smooth_env(v)
    ref = np.percentile(env[env > 0.01], 70) if np.any(env > 0.01) else 1.0
    d = np.clip(env / (ref + 1e-6), 0, 1)
    mg = 1 - 0.55 * d
    ag = 1 - 0.3 * d
    # silence windows before scares
    for a, b, c in duck_zero:
        ia, ib, ic = int(max(0, a) * SR), int(max(0, b) * SR), int(max(0, c) * SR)
        ib = min(ib, n)
        ic = min(ic, n)
        if ib > ia:
            ramp = np.linspace(1, 0.02, ib - ia, dtype=np.float32)
            mg[ia:ib] *= ramp
            ag[ia:ib] *= np.maximum(ramp, 0.15)
        if ic > ib:
            back = np.linspace(0.02, 1, ic - ib, dtype=np.float32)
            mg[ib:ic] *= back
            ag[ib:ic] *= np.maximum(back, 0.15)
    out = stereo(v) * 1.0 + music * mg[:, None] + amb * ag[:, None] + fxtrack
    return master(out[:int(total * SR) + 1], v[:int(total * SR) + 1])


def master(out, voice=None, speech_rms=0.13, ceiling=0.95):
    """Loudness: bring the speech to a steady level (about -17 dBFS RMS, so YouTube's -14 LUFS
    normalisation barely touches it), then a soft-knee limiter instead of scaling the whole track
    down because of one loud jumpscare."""
    if len(out) == 0:
        return out
    ref = voice if voice is not None and np.any(np.abs(voice) > 0.01) else out.mean(axis=1)
    blk = SR // 10
    nb = len(ref) // blk
    if nb > 4:
        r = np.sqrt(np.mean(ref[:nb * blk].reshape(nb, blk) ** 2, axis=1))
        act = r[r > max(0.008, np.percentile(r, 95) * 0.2)]
        level = float(np.median(act)) if len(act) else float(np.max(r))
        if level > 1e-4:
            out = out * min(6.0, speech_rms / level)
    knee = 0.8
    a = np.abs(out)
    over = a > knee
    if np.any(over):
        room = ceiling - knee
        out[over] = np.sign(out[over]) * (knee + room * np.tanh((a[over] - knee) / room))
    return out.astype(np.float32)


def library_info():
    return {'music_moods': sorted(MUSIC), 'ambiences': sorted(AMB), 'sfx': sorted(SFX), 'sfx_aliases': SFX_ALIASES}
