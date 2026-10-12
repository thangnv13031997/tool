"""Voice generation with Kokoro (through tts_worker.py) plus horror delivery effects.

- Lines are split at '...' and ' - ' / ' -- ' / em dashes into segments with a dramatic beat between them.
- Voice effects (pure numpy): deep, reverb, phone, radio, distant, echo, whisper, creepy, cold, shaky, loud, demon.
  Effects can be chained with '+', e.g. 'deep_reverb+whisper'.
- Test mode writes silent WAVs with an estimated length.
"""
import hashlib
import json
import os
import re
import subprocess
import sys
import wave
import numpy as np

SR = 24000
HERE = os.path.dirname(os.path.abspath(__file__))

PITCH = {'deep': 0.92, 'deep_reverb': 0.92, 'demon': 0.8, 'creepy': 0.96}


def read_wav(path):
    with wave.open(path, 'rb') as w:
        n = w.getnframes()
        sr = w.getframerate()
        ch = w.getnchannels()
        sw = w.getsampwidth()
        raw = w.readframes(n)
    if sw == 2:
        data = np.frombuffer(raw, dtype=np.int16).astype(np.float32) / 32768.0
    elif sw == 4:
        data = np.frombuffer(raw, dtype=np.int32).astype(np.float32) / 2147483648.0
    else:
        data = (np.frombuffer(raw, dtype=np.uint8).astype(np.float32) - 128) / 128.0
    if ch > 1:
        data = data.reshape(-1, ch).mean(axis=1)
    if sr != SR:
        data = resample(data, sr, SR)
    return data


def resample(x, sr_in, sr_out):
    if sr_in == sr_out or len(x) == 0:
        return x
    n = int(round(len(x) * sr_out / sr_in))
    return np.interp(np.linspace(0, len(x) - 1, n), np.arange(len(x)), x).astype(np.float32)


def write_wav(path, data, sr=SR):
    d = np.clip(data, -1, 1)
    d = (d * 32767).astype(np.int16)
    with wave.open(path, 'wb') as w:
        w.setnchannels(1)
        w.setsampwidth(2)
        w.setframerate(sr)
        w.writeframes(d.tobytes())


def trim_silence(data, thr=0.012, keep=0.04):
    idx = np.where(np.abs(data) > thr)[0]
    if len(idx) == 0:
        return data
    k = int(keep * SR)
    return data[max(0, idx[0] - k): min(len(data), idx[-1] + k)]


def envelope(data, fps):
    hop = SR / fps
    n = int(np.ceil(len(data) / hop))
    if n == 0:
        return np.zeros(0)
    pad = np.zeros(int(n * hop) + 1, np.float32)
    pad[:len(data)] = data
    env = np.array([np.sqrt(np.mean(pad[int(i * hop): int((i + 1) * hop)] ** 2) + 1e-12) for i in range(n)], np.float32)
    ref = np.percentile(env, 92) if n > 4 else env.max()
    if ref <= 1e-5:
        return np.zeros(n)
    env = np.clip(env / ref, 0, 1)
    env[env < 0.18] = 0
    sm = np.copy(env)
    sm[1:] = 0.6 * env[1:] + 0.4 * env[:-1]
    return sm


def estimate_secs(text, speed):
    words = max(1, len(text.split()))
    return words / (2.55 * speed) + 0.25


# ------------------------------------------------------------------ segments
SPLIT_RE = re.compile(r'\s*(?:\.\.\.|…|\s--\s|\s-\s|—)\s*')


def segments(text):
    """'I opened the door... and nobody was there.' -> ['I opened the door...', 'and nobody was there.']"""
    parts = []
    pos = 0
    for m in SPLIT_RE.finditer(text):
        seg = text[pos:m.start()].strip()
        if seg:
            ell = '...' in m.group(0) or '…' in m.group(0)
            parts.append(seg + ('...' if ell else ','))
        pos = m.end()
    tail = text[pos:].strip()
    if tail:
        parts.append(tail)
    parts = [p for p in parts if re.search(r'[A-Za-z0-9]', p)]
    return parts or [text]


# ------------------------------------------------------------------ dsp helpers (numpy only)
def _fft_filter(x, sr, lo=None, hi=None, gain_low=None):
    n = len(x)
    if n < 16:
        return x
    N = 1 << int(np.ceil(np.log2(n + 1)))
    X = np.fft.rfft(x, N)
    f = np.fft.rfftfreq(N, 1 / sr)
    g = np.ones_like(f)
    if lo:
        g *= 1 / (1 + (lo / np.maximum(f, 1)) ** 4)
    if hi:
        g *= 1 / (1 + (f / hi) ** 4)
    if gain_low:
        g *= 1 + (gain_low - 1) / (1 + (f / 220.0) ** 2)
    return np.fft.irfft(X * g, N)[:n].astype(np.float32)


def _ir(sr, secs=1.2, decay=3.2, seed=1, pre=0.012):
    rnd = np.random.default_rng(seed)
    n = int(secs * sr)
    t = np.arange(n) / sr
    ir = rnd.normal(0, 1, n).astype(np.float32) * np.exp(-decay * t)
    ir[:int(pre * sr)] = 0
    ir = _fft_filter(ir, sr, hi=5000)
    ir[0] = 0
    return ir / (np.sqrt(np.sum(ir ** 2)) + 1e-9)


def _convolve(x, ir):
    n = len(x) + len(ir) - 1
    N = 1 << int(np.ceil(np.log2(n)))
    y = np.fft.irfft(np.fft.rfft(x, N) * np.fft.rfft(ir, N), N)[:n]
    return y.astype(np.float32)


def reverb(x, sr, wet=0.25, secs=1.2, decay=3.2):
    y = _convolve(x, _ir(sr, secs, decay))
    out = np.zeros(len(y), np.float32)
    out[:len(x)] = x * (1 - wet * 0.5)
    out += y * wet * 0.6
    return out


def pitch_shift(x, p):
    """Lower (p<1) or raise pitch by resampling; the clip gets 1/p longer."""
    if abs(p - 1) < 1e-3:
        return x
    n = int(len(x) / p)
    return np.interp(np.linspace(0, len(x) - 1, n), np.arange(len(x)), x).astype(np.float32)


def apply_fx(x, sr, fxname):
    if not fxname or fxname == 'none':
        return x
    rms_in = float(np.sqrt(np.mean(x ** 2))) if len(x) else 0.0
    for name in fxname.split('+'):
        name = name.strip()
        if name in ('deep', 'deep_reverb'):
            x = _fft_filter(x, sr, gain_low=1.5)
            if name == 'deep_reverb':
                x = reverb(x, sr, 0.22, 1.4, 2.6)
        elif name == 'reverb':
            x = reverb(x, sr, 0.3)
        elif name == 'phone':
            x = _fft_filter(x, sr, lo=320, hi=3300)
            x = np.tanh(x * 2.2) * 0.55
        elif name == 'radio':
            x = _fft_filter(x, sr, lo=500, hi=2800)
            x = np.tanh(x * 3) * 0.5 + np.random.default_rng(2).normal(0, 0.012, len(x)).astype(np.float32)
        elif name == 'distant':
            x = _fft_filter(x, sr, hi=2400) * 0.6
            x = reverb(x, sr, 0.55, 1.8, 2.0)
        elif name == 'echo':
            d = int(0.28 * sr)
            y = np.zeros(len(x) + d * 3, np.float32)
            for i, g in enumerate((1.0, 0.45, 0.22, 0.1)):
                y[i * d:i * d + len(x)] += x * g
            x = y
        elif name == 'whisper':
            x = _fft_filter(x, sr, lo=280) * 0.75
            env = np.abs(x)
            k = int(sr * 0.02)
            env = np.convolve(env, np.ones(k) / k, mode='same')
            noise = _fft_filter(np.random.default_rng(4).normal(0, 1, len(x)).astype(np.float32), sr, lo=1800, hi=7000)
            x = x + noise * env * 0.9
        elif name == 'creepy':
            x = reverb(x, sr, 0.32, 1.6, 2.4)
            t = np.arange(len(x)) / sr
            x = x * (1 - 0.12 * (0.5 + 0.5 * np.sin(2 * np.pi * 5.5 * t)))
        elif name == 'cold':
            x = _fft_filter(x, sr, hi=6000)
            x = reverb(x, sr, 0.14, 0.8, 4)
        elif name == 'shaky':
            t = np.arange(len(x)) / sr
            x = x * (1 - 0.16 * (0.5 + 0.5 * np.sin(2 * np.pi * 6.5 * t + np.sin(t * 3))))
        elif name == 'loud':
            x = np.tanh(x * 1.6) * 0.8
        elif name == 'demon':
            x = _fft_filter(x, sr, gain_low=2.0)
            x = np.tanh(x * 1.8) * 0.7
            x = reverb(x, sr, 0.45, 1.8, 2.2)
    rms_out = float(np.sqrt(np.mean(x ** 2))) if len(x) else 0.0
    if rms_out > 1e-6 and rms_in > 1e-6:
        want = {'whisper': 0.7, 'distant': 0.65}.get(fxname.split('+')[-1], 1.0)
        x = x * min(4.0, rms_in * want / rms_out)
    peak = float(np.max(np.abs(x))) if len(x) else 0
    if peak > 0.98:
        x = x * (0.98 / peak)
    return x.astype(np.float32)


def base_fx(fxname):
    """First effect name (decides pitch)."""
    return (fxname or '').split('+')[0].strip()


# ------------------------------------------------------------------ Kokoro
class Voice:
    def __init__(self, cfg, cache_dir, log=print):
        self.cfg = cfg
        self.cache = cache_dir
        os.makedirs(cache_dir, exist_ok=True)
        self.log = log

    def path_for(self, text, voice, speed, test):
        h = hashlib.sha1(f'{voice}|{speed:.3f}|{text}'.encode('utf-8')).hexdigest()[:16]
        return os.path.join(self.cache, ('test_' if test else '') + f'{voice}_{h}.wav')

    def synth(self, items, test=False, progress=None, cancelled=lambda: False):
        """items: dicts with text, voice, speed. Adds 'wav' to each. Returns list of error strings."""
        todo = []
        seen = set()
        for it in items:
            it['wav'] = self.path_for(it['text'], it['voice'], it['speed'], test)
            if not os.path.exists(it['wav']) and it['wav'] not in seen:
                todo.append(it)
                seen.add(it['wav'])
        if test:
            for it in todo:
                n = int(estimate_secs(it['text'], it['speed']) * SR)
                write_wav(it['wav'], np.zeros(n, dtype=np.float32))
            return []
        if not todo:
            return []
        py = self.cfg.get('kokoro_python')
        if not py or not os.path.exists(py):
            raise RuntimeError('Không tìm thấy Python của Kokoro: %s\nSửa "kokoro_python" trong config.json' % py)
        job = {'items': [{'text': it['text'], 'voice': it['voice'], 'speed': it['speed'], 'out': it['wav']} for it in todo]}
        if self.cfg.get('kokoro_device'):
            job['device'] = self.cfg['kokoro_device']
        job_path = os.path.join(self.cache, '_job.json')
        with open(job_path, 'w', encoding='utf-8') as f:
            json.dump(job, f, ensure_ascii=False)
        env = dict(os.environ)
        if self.cfg.get('hf_home'):
            env['HF_HOME'] = self.cfg['hf_home']
        env['PYTHONIOENCODING'] = 'utf-8'
        env['HF_HUB_DISABLE_TELEMETRY'] = '1'
        errors = []
        for attempt, offline in enumerate((True, False)):
            env['HF_HUB_OFFLINE'] = '1' if offline else '0'
            flags = 0x08000000 if sys.platform == 'win32' else 0
            proc = subprocess.Popen([py, os.path.join(HERE, 'tts_worker.py'), job_path], stdout=subprocess.PIPE,
                                    stderr=subprocess.STDOUT, env=env, creationflags=flags,
                                    encoding='utf-8', errors='replace')
            errors = []
            tail = []
            for line in proc.stdout:
                line = line.strip()
                if cancelled():
                    proc.kill()
                    raise RuntimeError('Đã hủy')
                try:
                    msg = json.loads(line)
                except ValueError:
                    tail = (tail + [line])[-15:]
                    continue
                st = msg.get('stage')
                if st == 'line' and progress:
                    progress(msg['done'], msg['total'])
                elif st in ('line_error', 'error'):
                    errors.append(msg.get('error', ''))
                elif st == 'loading':
                    self.log('Đang nạp Kokoro...')
            proc.wait()
            missing = [it for it in todo if not os.path.exists(it['wav'])]
            if not missing:
                return errors
            if attempt == 0:
                self.log('Thử lại Kokoro có kết nối mạng (có thể thiếu file giọng mới)...')
                continue
            detail = '\n'.join(errors[-3:] or tail[-8:])
            raise RuntimeError('Kokoro không tạo được %d câu.\n%s' % (len(missing), detail))
        return errors


def build_line_audio(line, seg_items, test=False):
    """Join a line's segment WAVs with beats, then pitch + effects. Returns float32 at SR."""
    parts = []
    beat = 0.0 if test else 0.34
    for i, it in enumerate(seg_items):
        a = read_wav(it['wav'])
        if not test:
            a = trim_silence(a)
        parts.append(a)
        if i < len(seg_items) - 1:
            parts.append(np.zeros(int(beat * SR), np.float32))
    x = np.concatenate(parts) if parts else np.zeros(1, np.float32)
    if test:
        return x
    p = PITCH.get(base_fx(line.get('vfx')), 1.0)
    if p != 1.0:
        x = pitch_shift(x, p)
    x = apply_fx(x, SR, line.get('vfx'))
    return x
