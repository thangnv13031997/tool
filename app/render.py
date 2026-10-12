"""Full pipeline: script -> voices -> timeline -> sound mix -> frames -> mp4, Shorts, thumbnails, YouTube text."""
import datetime
import os
import re
import subprocess
import sys
import time
import numpy as np
from PIL import Image

import script_io
import tts
import audio
import notes
import youtube
from engine.scene import SceneRenderer
from engine import thumbnail, textfx

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
NOFLAGS = 0x08000000 if sys.platform == 'win32' else 0
POST = {'jumpscare': 0.9, 'lights_out': 1.0, 'lights_on': 0.4, 'stinger': 0.5, 'reveal': 0.9, 'glitch': 0.4, 'flash': 0.3}
SILENCE = {'jumpscare': 0.8, 'reveal': 0.5, 'lights_out': 0.3, 'stinger': 0.15, 'glitch': 0.0, 'flash': 0.0, 'lights_on': 0.0}


def ffmpeg_exe(cfg):
    p = cfg.get('ffmpeg')
    if p and os.path.exists(p):
        return p
    try:
        import imageio_ffmpeg
        return imageio_ffmpeg.get_ffmpeg_exe()
    except Exception:
        return 'ffmpeg'


_ENC = {}


def pick_encoder(ff, want):
    if want == 'libx264':
        return 'libx264'
    if 'enc' in _ENC:
        return _ENC['enc']
    enc = 'libx264'
    if want in ('auto', 'nvenc', 'h264_nvenc'):
        try:
            r = subprocess.run([ff, '-hide_banner', '-loglevel', 'error', '-f', 'lavfi', '-i', 'color=c=black:s=320x240:d=0.2',
                                '-c:v', 'h264_nvenc', '-f', 'null', '-'], capture_output=True, timeout=30, creationflags=NOFLAGS)
            if r.returncode == 0:
                enc = 'h264_nvenc'
        except Exception:
            pass
    _ENC['enc'] = enc
    return enc


def slugify(s):
    return re.sub(r'[^A-Za-z0-9]+', '-', s).strip('-')[:60] or 'video'


def fmt_ts(sec):
    return youtube.fmt_ts(sec)


def fmt_srt(sec):
    ms = int(round(sec * 1000))
    h, ms = divmod(ms, 3600000)
    m, ms = divmod(ms, 60000)
    s, ms = divmod(ms, 1000)
    return f'{h:02d}:{m:02d}:{s:02d},{ms:03d}'


# ------------------------------------------------------------------ timeline
def build_timeline(script, cfg, fps, estimate=False):
    """Fill start/end of every line, events, props, sfx and scene durations.

    estimate=True uses word-count estimates (for previews without audio)."""
    t_global = 0.0
    sfx_events = []
    for si, sc in enumerate(script['scenes']):
        t = 0.05 if si == 0 else 0.2
        if sc['transition'] in ('fade',):
            t = 0.35
        events = []
        line_times = []
        scare = sc.get('scare_raw')
        raw_events = list(sc.get('events_raw', []))
        if scare:
            if isinstance(scare, str):
                scare = {'type': scare}
            raw_events.append(dict(scare, _main=True))
        pending = []
        for ev in raw_events:
            kind = ev.get('type', ev.get('kind', 'jumpscare'))
            if kind not in script_io.SCARES:
                kind = 'jumpscare'
            e = {'kind': kind, 'entity': ev.get('entity', 'face'), 'dur': float(ev.get('dur', 0.5)),
                 'silence': float(ev.get('silence', SILENCE.get(kind, 0.3)))}
            if 'at' in ev:
                e['t'] = float(ev['at'])
                events.append(e)
            elif 'at_line' in ev:
                pending.append(('at', int(ev['at_line']), e))
            else:
                k = int(ev.get('after_line', len(sc['lines']) - 1))
                pending.append(('after', k, e))
        for li, ln in enumerate(sc['lines']):
            for mode, k, e in pending:
                if mode == 'at' and k == li:
                    e['t'] = t
                    events.append(e)
            if estimate:
                d = tts.estimate_secs(ln['tts_text'], ln['speed'])
            else:
                d = len(ln['audio']) / tts.SR
            ln['start'] = t
            ln['end'] = t + d
            line_times.append((t, t + d))
            words = textfx.words_marked(ln['text'])
            chunks = textfx.chunk_words(words, int(cfg.get('caption_words', 5)))
            total_chars = sum(sum(len(w) + 1 for w, _ in c) for c in chunks) or 1
            ct = t
            ln['chunks'] = []
            for c in chunks:
                cd = d * sum(len(w) + 1 for w, _ in c) / total_chars
                ln['chunks'].append({'words': c, 'start': ct, 'end': ct + cd})
                ct += cd
            pause = sc['pause'] if sc.get('pause') is not None else ln['pause_after']
            t = ln['end'] + pause
            for mode, k, e in pending:
                if mode == 'after' and k == li:
                    t = ln['end'] + e['silence']
                    e['t'] = t
                    events.append(e)
                    t += POST.get(e['kind'], 0.5)
        if not sc['lines']:
            for mode, k, e in pending:
                t = max(t, e['silence'] + 0.3)
                e['t'] = t
                events.append(e)
                t += POST.get(e['kind'], 0.5)
        sc['events'] = sorted(events, key=lambda e: e['t'])
        # auto camera cut: long scenes change angle when the next line starts (keeps the eye busy)
        sc['cuts'] = []
        if cfg.get('auto_cuts', True) and len(sc['lines']) >= 2 and t > 7.0 and not sc.get('no_cuts'):
            for li in range(1, len(sc['lines'])):
                ln = sc['lines'][li]
                if ln['start'] - (sc['cuts'][-1]['t'] if sc['cuts'] else 0) < 3.0:
                    continue
                spk = next((c for c in sc['chars'] if c['key'] == ln['speaker_key']), None)
                tgt = spk or (sc['chars'][0] if sc['chars'] else None)
                base = sc['camera']
                if base in ('close', 'extreme_close'):
                    cam = 'slow_push'
                    fxy = (0.5, 0.5)
                elif tgt is not None:
                    cam = 'close'
                    fxy = (tgt['x'], sc.get('focus_y', 0.5) if tgt is (sc['chars'][0] if sc['chars'] else None) else 0.5)
                else:
                    cam = 'push_in' if base != 'push_in' else 'pull_out'
                    fxy = (sc.get('focus_x', 0.5), sc.get('focus_y', 0.5))
                sc['cuts'].append({'t': ln['start'] - 0.08, 'camera': cam, 'focus': fxy})
        dur = max(t + 0.15, sc['hold'], 1.0)
        if any(c.get('enter') for c in sc['chars']):
            dur = max(dur, 1.5)
        if sc['events']:
            dur = max(dur, sc['events'][-1]['t'] + POST.get(sc['events'][-1]['kind'], 0.5))
        dur += sc.get('end_black', 0.0)
        n = max(1, int(round(dur * fps)))
        sc['frames'] = n
        sc['duration'] = n / fps
        sc['start'] = t_global

        def resolve(w, default=None):
            if not w:
                return default
            if w.get('scare'):
                return sc['events'][0]['t'] if sc['events'] else default
            if 'at' in w:
                return float(w['at'])
            if 'at_line' in w and line_times:
                return line_times[max(0, min(len(line_times) - 1, int(w['at_line'])))][0]
            if 'after_line' in w and line_times:
                return line_times[max(0, min(len(line_times) - 1, int(w['after_line'])))][1]
            return default

        for c in sc['chars']:
            c['appear_at'] = resolve(c.get('appear_raw'))
            c['vanish_at'] = resolve(c.get('vanish_raw'))
        for p in sc['props']:
            p['t0'] = resolve(p.get('when'), 0.0 if p['group'] != 'insert' else 0.15)
            p['t1'] = resolve(p.get('until'))
            if p['group'] == 'insert' and p.get('until') and 'at_line' in p['until'] and line_times:
                p['t1'] = line_times[max(0, min(len(line_times) - 1, int(p['until']['at_line'])))][1]
        for e in sc.get('sfx_raw', []):
            if isinstance(e, str):
                e = {'name': e}
            name, ok = audio.resolve_sfx(e.get('name'))
            w = _when_sfx(e)
            at = resolve(w, 0.1)
            sfx_events.append({'name': name, 't': t_global + at, 'volume': e.get('volume', 1.0), 'ok': ok,
                               'scene': si, 'raw': e.get('name')})
        t_global += sc['duration']
    sl = script['scenes']
    for prev, sc in zip(sl, sl[1:]):
        pm = {c['key']: c for c in prev['chars']}
        for c in sc['chars']:
            pc = pm.get(c['key'])
            if c.get('continues') and pc and not pc.get('exit') and abs(pc['x'] - c['x']) < 0.05:
                c['prev'] = {'pose': pc['pose'], 't': prev['duration']}
    if sl:
        sl[-1]['fade_out'] = True
    script['total'] = t_global
    script['sfx_events'] = sfx_events
    return t_global


def _when_sfx(e):
    for k in ('at', 'at_line', 'after_line'):
        if k in e:
            return {k: e[k]}
    if e.get('on') == 'scare':
        return {'scare': True}
    return None


class Job:
    def __init__(self, cfg, script_path, test_voice=False, preview_secs=None, music=True, shorts=True,
                 report=None, log=print):
        self.cfg = cfg
        self.script_path = script_path
        self.test = test_voice
        self.preview = preview_secs
        self.music_on = music
        self.make_shorts = shorts
        self.report = report or (lambda *a: None)
        self.log = log
        self.cancel = False
        self.fps = int(cfg.get('fps', 30))
        self.W, self.H = cfg.get('width', 1920), cfg.get('height', 1080)

    # ---------------------------------------------------------------- prepare
    def prepare(self):
        raw = script_io.load(self.script_path)
        script, issues = script_io.normalize(raw, self.cfg)
        self.raw, self.script, self.issues = raw, script, issues
        if self.preview:
            est, keep = 0.0, []
            for sc in script['scenes']:
                keep.append(sc)
                est += sum(tts.estimate_secs(l['tts_text'], l['speed']) + l['pause_after'] for l in sc['lines']) + sc['hold'] + 0.4
                if est >= self.preview:
                    break
            script['scenes'] = keep
        voice = tts.Voice(self.cfg, os.path.join(ROOT, 'output', '_tts_cache'), self.log)
        items = []
        gspeed = script['speed']
        for sc in script['scenes']:
            for ln in sc['lines']:
                p = tts.PITCH.get(tts.base_fx(ln.get('vfx')), 1.0)
                sp = max(0.6, min(1.5, ln['speed'] * gspeed / (p ** 0.5)))
                ln['_segs'] = []
                for seg in tts.segments(ln['tts_text']):
                    it = {'text': seg, 'voice': ln['voice'], 'speed': round(sp, 3)}
                    ln['_segs'].append(it)
                    items.append(it)
        self.report('voice', 0.0, 'Đang tạo giọng đọc...')
        errs = voice.synth(items, test=self.test,
                           progress=lambda d, n: self.report('voice', d / max(1, n), f'Giọng đọc {d}/{n}'),
                           cancelled=lambda: self.cancel)
        for e in errs:
            self.issues.append(script_io.Issue('Lỗi giọng', e[:200]))
        for sc in script['scenes']:
            for ln in sc['lines']:
                ln['audio'] = tts.build_line_audio(ln, ln['_segs'], self.test)
                ln['env'] = None if self.test else tts.envelope(ln['audio'], self.fps)
                ln['env_fps'] = self.fps
        self.total = build_timeline(script, self.cfg, self.fps)
        for e in script['sfx_events']:
            if not e['ok']:
                self.issues.append(script_io.Issue('Thiếu âm thanh', f'"{e["raw"]}" chưa có, bỏ qua', e['scene']))
        self.retention, rissues = script_io.retention_report(script)
        if not self.preview:
            self.issues += rissues
        return script

    # ---------------------------------------------------------------- audio
    def build_audio(self, path, ff):
        voice = np.zeros(int(np.ceil(self.total * audio.SR)) + audio.SR, np.float32)
        for sc in self.script['scenes']:
            for ln in sc['lines']:
                a = tts.resample(ln['audio'], tts.SR, audio.SR)
                i0 = int((sc['start'] + ln['start']) * audio.SR)
                n = min(len(a), len(voice) - i0)
                if n > 0:
                    voice[i0:i0 + n] += a[:n]
        peak = float(np.max(np.abs(voice))) if len(voice) else 0
        if peak > 0:
            voice *= min(1.6, 0.92 / peak)
        if self.music_on:
            lib = audio.Library(ff, self.log)
            vol = self.script.get('music_volume')
            cfg = dict(self.cfg)
            if vol is not None:
                cfg['music_volume'] = vol
            mix = audio.mix(self.total, voice, self.script['scenes'], lib, cfg, self.log, self.script['sfx_events'])
        else:
            mix = np.stack([voice, voice], axis=1)[:int(self.total * audio.SR) + 1]
        audio.write_wav(path, mix)

    # ---------------------------------------------------------------- run
    def run(self):
        t_start = time.time()
        self.prepare()
        if self.cancel:
            raise RuntimeError('Đã hủy')
        stamp = datetime.datetime.now().strftime('%Y%m%d_%H%M')
        name = f'{stamp}_{slugify(self.script["title"])}' + ('_PREVIEW' if self.preview else '') + ('_TEST' if self.test else '')
        out_dir = os.path.join(ROOT, 'output', name)
        os.makedirs(out_dir, exist_ok=True)
        self.out_dir = out_dir
        ff = ffmpeg_exe(self.cfg)
        wav = os.path.join(out_dir, 'mix.wav')
        self.report('voice', 1.0, 'Đang trộn nhạc, âm thanh nền, hiệu ứng...')
        self.build_audio(wav, ff)
        enc = pick_encoder(ff, self.cfg.get('encoder', 'auto'))
        self.log(f'Bộ mã hóa video: {enc}')
        total_frames = sum(sc['frames'] for sc in self.script['scenes'])
        t_frames = time.time()
        segs = self.render_video(ff, enc, out_dir, total_frames, t_frames)
        mp4 = os.path.join(out_dir, 'video.mp4')
        self.report('mux', 0.5, 'Đang ghép tiếng và hình...')
        self.mux(ff, segs, wav, mp4)
        for p in segs:
            try:
                os.remove(p)
            except OSError:
                pass
        render_secs = time.time() - t_frames
        self.report('extras', 0.2, 'Đang tạo thumbnail, tiêu đề, phụ đề...')
        self.write_extras(out_dir)
        if self.make_shorts and not self.preview:
            try:
                self.report('extras', 0.6, 'Đang cắt bản Shorts dọc...')
                self.render_shorts(ff, enc, out_dir, wav)
            except Exception as e:  # noqa
                self.issues.append(script_io.Issue('Lỗi Shorts', str(e)[:200]))
        if not self.cfg.get('keep_wav'):
            try:
                os.remove(wav)
            except OSError:
                pass
        stats = {
            'Thư mục': out_dir,
            'Thời lượng video': fmt_ts(self.total) + f' ({len(self.script["scenes"])} cảnh)',
            'Điểm giữ chân (ước lượng)': f'{self.retention}/100',
            'Thời gian dựng hình': fmt_ts(render_secs) + f' ({total_frames / max(0.1, render_secs):.1f} khung/giây)',
            'Bộ mã hóa': enc,
            'Chế độ': ('xem thử %ds' % self.preview if self.preview else 'đầy đủ') + (', không giọng' if self.test else ''),
            'Tổng thời gian': fmt_ts(time.time() - t_start),
        }
        self.notes_path = notes.append(os.path.join(ROOT, 'notes'), self.script['title'], self.issues, stats)
        with open(os.path.join(out_dir, 'render_report.txt'), 'w', encoding='utf-8') as f:
            for k, v in stats.items():
                f.write(f'{k}: {v}\n')
            f.write('\nVấn đề phát hiện:\n')
            for it in self.issues:
                f.write(f'- {it}\n')
        self.report('done', 1.0, 'Xong!')
        return out_dir

    # ---------------------------------------------------------------- video
    def _light_script(self):
        light = dict(self.script)
        light['scenes'] = []
        for sc in self.script['scenes']:
            sc2 = dict(sc)
            sc2['lines'] = [{k: v for k, v in ln.items() if k not in ('audio', '_segs')} for ln in sc['lines']]
            light['scenes'].append(sc2)
        light.pop('sfx_events', None)
        return light

    def render_video(self, ff, enc, out_dir, total_frames, t_frames, scene_ids=None, vertical=False, seg_prefix='_seg'):
        import multiprocessing as mp
        import pickle
        scenes = self.script['scenes']
        ids = scene_ids if scene_ids is not None else list(range(len(scenes)))
        workers = self.cfg.get('workers', 'auto')
        if workers in ('auto', None, 0):
            workers = max(1, min(4, (os.cpu_count() or 2) // 2))
        workers = max(1, min(int(workers), len(ids)))
        groups, cur, acc = [], [], 0
        per = total_frames / workers
        for i in ids:
            cur.append(i)
            acc += scenes[i]['frames']
            if acc >= per * (len(groups) + 1) and len(groups) < workers - 1:
                groups.append(cur)
                cur = []
        if cur:
            groups.append(cur)
        pk = os.path.join(out_dir, '_script.pkl')
        with open(pk, 'wb') as f:
            pickle.dump(self._light_script(), f)
        segs = [os.path.join(out_dir, f'{seg_prefix}{i:02d}.mp4') for i in range(len(groups))]
        base = dict(W=self.W, H=self.H, fps=self.fps, enc=enc, ff=ff, quality=int(self.cfg.get('quality', 2)),
                    x264_preset=self.cfg.get('x264_preset', 'veryfast'), vertical=vertical,
                    shorts=self.script.get('shorts') or {},
                    shorts_offsets={i: sum(scenes[k]['duration'] for k in ids[:n]) for n, i in enumerate(ids)},
                    shorts_total=sum(scenes[i]['duration'] for i in ids),
                    shorts_scale=float(self.cfg.get('shorts_scale', 1.4)))
        if len(groups) == 1:
            _segment_worker(pk, groups[0], segs[0], base, _LocalQ(self, total_frames, t_frames), _Flag(self))
        else:
            ctx = mp.get_context('spawn')
            q = ctx.Queue()
            stop = ctx.Event()
            procs = []
            self.log(f'Dựng hình song song: {len(groups)} luồng')
            for g, sp in zip(groups, segs):
                p = ctx.Process(target=_segment_worker, args=(pk, g, sp, base, q, stop), daemon=True)
                p.start()
                procs.append(p)
            done = finished = 0
            errors = []
            while finished < len(procs):
                if self.cancel:
                    stop.set()
                    for p in procs:
                        p.join(5)
                        if p.is_alive():
                            p.terminate()
                    raise RuntimeError('Đã hủy')
                try:
                    msg = q.get(timeout=0.5)
                except Exception:
                    if all(not p.is_alive() for p in procs) and q.empty():
                        break
                    continue
                if msg[0] == 'p':
                    done += msg[1]
                    el = time.time() - t_frames
                    eta = el / max(1, done) * (total_frames - done)
                    self.report('frames', done / total_frames, f'Dựng hình {done}/{total_frames} khung, còn khoảng {fmt_ts(eta)}')
                elif msg[0] == 'done':
                    finished += 1
                    if msg[1]:
                        errors.append(msg[1])
            for p in procs:
                p.join(10)
            if errors:
                if enc == 'h264_nvenc':
                    _ENC['enc'] = 'libx264'
                    self.log('NVENC lỗi, lần sau sẽ dùng libx264.')
                raise RuntimeError('Lỗi dựng hình:\n' + errors[0][-800:])
        try:
            os.remove(pk)
        except OSError:
            pass
        missing = [s for s in segs if not os.path.exists(s)]
        if missing:
            raise RuntimeError('Thiếu đoạn video: ' + ', '.join(os.path.basename(m) for m in missing))
        return segs

    def mux(self, ff, segs, wav, mp4, start=None, dur=None):
        lst = os.path.join(os.path.dirname(mp4), '_segments.txt')
        with open(lst, 'w', encoding='utf-8') as f:
            for s in segs:
                f.write("file '" + s.replace('\\', '/').replace("'", "'\\''") + "'\n")
        cmd = [ff, '-y', '-hide_banner', '-loglevel', 'error', '-f', 'concat', '-safe', '0', '-i', lst]
        if start is not None:
            cmd += ['-ss', f'{start:.3f}', '-t', f'{dur:.3f}']
        cmd += ['-i', wav, '-map', '0:v', '-map', '1:a', '-c:v', 'copy', '-c:a', 'aac', '-b:a', '192k', '-ar', '48000',
                '-ac', '2', '-shortest', '-movflags', '+faststart', mp4]
        r = subprocess.run(cmd, capture_output=True, creationflags=NOFLAGS)
        try:
            os.remove(lst)
        except OSError:
            pass
        if r.returncode != 0:
            raise RuntimeError('ffmpeg ghép video lỗi:\n' + r.stderr.decode('utf-8', 'replace')[-800:])

    # ---------------------------------------------------------------- shorts
    def shorts_scenes(self):
        sc = self.script['scenes']
        cfgs = self.script.get('shorts') or {}
        ids = []
        lst = cfgs.get('scenes') or []
        if len(lst) == 2 and int(lst[1]) > int(lst[0]) + 1:
            a, b = int(lst[0]) - 1, int(lst[1]) - 1
            ids = [i for i in range(len(sc)) if a <= i <= b]
        elif lst:
            ids = [int(i) - 1 for i in lst if 0 < int(i) <= len(sc)]
        ids = [i for i in ids if sc[i]['purpose'] not in ('host_intro', 'host_outro')]
        if not ids:
            ids = [i for i, s in enumerate(sc) if s.get('shorts')]
        if not ids:
            # auto: the hook scenes
            acc = 0
            for i, s in enumerate(sc):
                if s['purpose'] in ('host_intro',):
                    continue
                ids.append(i)
                acc += s['duration']
                if acc > 40:
                    break
        out, acc = [], 0
        for i in ids:
            if acc + sc[i]['duration'] > 58:
                break
            out.append(i)
            acc += sc[i]['duration']
        return out

    def render_shorts(self, ff, enc, out_dir, wav):
        ids = self.shorts_scenes()
        if not ids:
            return
        sc = self.script['scenes']
        frames = sum(sc[i]['frames'] for i in ids)
        segs = self.render_video(ff, enc, out_dir, frames, time.time(), scene_ids=ids, vertical=True, seg_prefix='_short')
        # audio: the same scenes cut out of the full mix
        full = audio.read_any(wav, ff)
        parts = []
        for i in ids:
            a = int(sc[i]['start'] * audio.SR)
            b = a + int(round(sc[i]['frames'] / self.fps * audio.SR))
            parts.append(full[a:b])
        sw = os.path.join(out_dir, '_shorts.wav')
        audio.write_wav(sw, np.concatenate(parts) if parts else np.zeros((audio.SR, 2), np.float32))
        self.mux(ff, segs, sw, os.path.join(out_dir, 'shorts.mp4'))
        try:
            os.remove(sw)
        except OSError:
            pass
        for p in segs:
            try:
                os.remove(p)
            except OSError:
                pass

    # ---------------------------------------------------------------- extras
    def write_extras(self, out_dir):
        yt = self.script.get('youtube') or {}
        best, text, ranked = youtube.build_text(self.script, self.issues, script_io.Issue)
        th = yt.get('thumbnail') or {}
        variants = th.get('variants') or ([th] if th else [])
        while len(variants) < 3:
            base = dict(variants[0]) if variants else {}
            base['layout'] = ['face_threat', 'object', 'split'][len(variants)]
            variants.append(base)
        thumbs = []
        for i, v in enumerate(variants[:3]):
            try:
                img = thumbnail.render(v, self.script['cast'], default_title=best)
                img.save(os.path.join(out_dir, f'thumbnail_{"ABC"[i]}.jpg'), quality=92)
                if i == 0:
                    img.save(os.path.join(out_dir, 'thumbnail.jpg'), quality=92)
                thumbs.append(img)
            except Exception as e:  # noqa
                self.issues.append(script_io.Issue('Lỗi thumbnail', f'{"ABC"[i]}: {str(e)[:200]}'))
        if thumbs:
            try:
                thumbnail.phone_preview(thumbs, best, yt.get('channel', 'Bus 13: Night Route')).save(
                    os.path.join(out_dir, 'thumbnail_preview_phone.jpg'), quality=90)
            except Exception:
                pass
        with open(os.path.join(out_dir, 'youtube.txt'), 'w', encoding='utf-8') as f:
            f.write(f'Điểm giữ chân ước lượng: {getattr(self, "retention", 0)}/100 (xem render_report.txt)\n\n')
            f.write(text)
        with open(os.path.join(out_dir, 'subtitles.srt'), 'w', encoding='utf-8') as f:
            n = 1
            for sc in self.script['scenes']:
                for ln in sc['lines']:
                    for c in ln['chunks']:
                        f.write(f'{n}\n{fmt_srt(sc["start"] + c["start"])} --> {fmt_srt(sc["start"] + c["end"])}\n')
                        f.write(' '.join(w for w, _ in c['words']) + '\n\n')
                        n += 1


# ------------------------------------------------------------------ previews (no audio)
def prepare_preview(cfg, script_path):
    raw = script_io.load(script_path)
    script, issues = script_io.normalize(raw, cfg)
    for sc in script['scenes']:
        for ln in sc['lines']:
            ln['env'] = None
    build_timeline(script, cfg, int(cfg.get('fps', 30)), estimate=True)
    score, rissues = script_io.retention_report(script)
    return script, issues, score, rissues


def still(cfg, script_path, scene_index, at=0.6, width=960, cache=None):
    if cache and cache.get('path') == script_path and cache.get('mtime') == os.path.getmtime(script_path):
        script = cache['script']
    else:
        script, _, _, _ = prepare_preview(cfg, script_path)
        if cache is not None:
            cache.update(path=script_path, mtime=os.path.getmtime(script_path), script=script)
    if not script['scenes']:
        return None
    scene_index = max(0, min(len(script['scenes']) - 1, scene_index))
    sc = script['scenes'][scene_index]
    h = int(width * 9 / 16)
    R = cache.get('renderer') if cache else None
    if R is None or R.OW != width:
        R = SceneRenderer(width, h, quality=1)
        if cache is not None:
            cache['renderer'] = R
    t = sc['duration'] * at
    if any(c.get('enter') for c in sc['chars']):
        t = max(t, 1.3)
    for c in sc['chars']:
        if c.get('appear_at') is not None:
            t = max(t, c['appear_at'] + 0.1)
    for p in sc['props']:
        t = max(t, min(sc['duration'] - 0.05, (p.get('t0') or 0) + 0.4))
    return R.frame(sc, t)


class _LocalQ:
    def __init__(self, job, total, t0):
        self.job, self.total, self.t0, self.done = job, total, t0, 0

    def put(self, msg):
        if msg[0] == 'p':
            self.done += msg[1]
            el = time.time() - self.t0
            eta = el / max(1, self.done) * (self.total - self.done)
            self.job.report('frames', self.done / max(1, self.total), f'Dựng hình {self.done}/{self.total} khung, còn khoảng {fmt_ts(eta)}')
        elif msg[0] == 'done' and msg[1]:
            raise RuntimeError('Lỗi dựng hình:\n' + msg[1][-800:])


class _Flag:
    def __init__(self, job):
        self.job = job

    def is_set(self):
        return self.job.cancel


def _vertical(R, sc, t, cap, base):
    """9:16 frame: crop the 16:9 frame around the focus, big captions in the middle."""
    from engine import fx
    from engine import props as PR
    frame = R.frame(sc, t, captions=False, inserts=False)
    OW, OH = frame.size
    cw = int(OH * 9 / 16)
    fxp = sc.get('focus_x', 0.5) * OW
    try:
        tgt = R._frame_target(sc, t)
        if tgt is not None:
            box = R.camera(sc, t)
            fxp = (tgt[0] - box[0]) / max(1.0, box[2] - box[0]) * OW
    except Exception:
        pass
    x0 = int(max(0, min(OW - cw, fxp - cw / 2)))
    v = frame.crop((x0, 0, x0 + cw, OH)).resize((1080, 1920), Image.BILINEAR)
    for p in sc['props']:
        if p['group'] != 'insert' or t < (p.get('t0') or 0) or (p.get('t1') is not None and t > p['t1']):
            continue
        q = dict(p)
        if q['type'] == 'chat' and q.get('messages'):
            q['_reveal'] = min(len(q['messages']), 1 + int((t - (p.get('t0') or 0)) / q.get('message_gap', 1.1)))
        if q['type'] == 'cctv':
            img, cx, cy = PR.render(q, 400, t, S=1, full=(1080, 1920))
            v.paste(img, (0, 0), img)
            continue
        s = 420.0 * q.get('scale', 1.0)
        img, cx, cy = PR.render(q, s, t, S=1)
        bb = img.getbbox()
        if bb:
            img = img.crop(bb)
        if img.width > 1000:
            k = 1000 / img.width
            img = img.resize((1000, max(1, int(img.height * k))), Image.BILINEAR)
        v = fx.fade_black(v, 0.45)
        v.paste(img, (int(540 - img.width / 2), int(1920 * 0.42 - img.height / 2)), img)
    words = R.caption_at(sc, t)
    if words:
        img = cap.caption(words)
        v.paste(img, (int(540 - img.width / 2), int(1920 * 0.7 - img.height / 2)), img)
    gt = base['shorts_offsets'].get(sc['index'], 0.0) + t
    hook = (base['shorts'] or {}).get('hook_text')
    if hook and gt < 3.0:
        im = cap.card(hook, 'display', 92)
        v.paste(im, (int(540 - im.width / 2), int(1920 * 0.12)), im)
    end = (base['shorts'] or {}).get('end_text', 'Full story on the channel')
    if gt > base['shorts_total'] - 2.2:
        v = fx.fade_black(v, 0.55)
        im = cap.card(end, 'display', 84)
        v.paste(im, (int(540 - im.width / 2), int(960 - im.height / 2)), im)
    return v


def _segment_worker(pk, scene_ids, seg_path, base, q, stop):
    import pickle
    import traceback
    proc = None
    try:
        with open(pk, 'rb') as f:
            script = pickle.load(f)
        W, H, fps = base['W'], base['H'], base['fps']
        vertical = base.get('vertical')
        OW, OH = (1080, 1920) if vertical else (W, H)
        cmd = [base['ff'], '-y', '-hide_banner', '-loglevel', 'error', '-f', 'rawvideo', '-pix_fmt', 'rgb24',
               '-s', f'{OW}x{OH}', '-r', str(fps), '-i', '-']
        if base['enc'] == 'h264_nvenc':
            cmd += ['-c:v', 'h264_nvenc', '-preset', 'p5', '-rc', 'vbr', '-cq', '24', '-b:v', '0',
                    '-maxrate', '24M', '-bufsize', '48M', '-g', str(fps * 2)]
        else:
            cmd += ['-c:v', 'libx264', '-preset', base['x264_preset'], '-crf', '22', '-g', str(fps * 2)]
        cmd += ['-pix_fmt', 'yuv420p', '-an', seg_path]
        proc = subprocess.Popen(cmd, stdin=subprocess.PIPE, stderr=subprocess.PIPE, creationflags=NOFLAGS)
        k = float(base.get('shorts_scale', 1.4)) if vertical else 1.0
        R = SceneRenderer(int(W * k) // 2 * 2, int(H * k) // 2 * 2, quality=base['quality'])
        cap = textfx.CaptionCache(1080, 1920, size=74, vertical=True) if vertical else None
        n = 0
        for si in scene_ids:
            sc = script['scenes'][si]
            for i in range(sc['frames']):
                if stop.is_set():
                    proc.kill()
                    q.put(('done', 'Đã hủy'))
                    return
                t = i / fps
                img = _vertical(R, sc, t, cap, base) if vertical else R.frame(sc, t)
                proc.stdin.write(img.tobytes())
                n += 1
                if n % 10 == 0:
                    q.put(('p', 10))
        q.put(('p', n % 10))
        proc.stdin.close()
        err = proc.stderr.read().decode('utf-8', 'replace')
        proc.wait()
        q.put(('done', None if proc.returncode == 0 else 'ffmpeg: ' + err))
    except Exception:
        if proc:
            try:
                proc.kill()
            except Exception:
                pass
        q.put(('done', traceback.format_exc()))
