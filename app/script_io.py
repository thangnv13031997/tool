"""Load a horror script (JSON), fill defaults, carry scene settings forward and check retention.

Every problem found is written to notes/IMPROVEMENTS.md so the tool and the
scripts get better over time.
"""
import json
import re
import zlib
from engine import figure as F
from engine import props as PR
from engine import backgrounds as BG
from engine import textfx

ALL_VOICES = ['af_heart', 'af_bella', 'af_nicole', 'af_sarah', 'af_sky', 'af_nova', 'af_river', 'af_alloy', 'af_aoede',
              'af_jessica', 'af_kore', 'am_michael', 'am_fenrir', 'am_puck', 'am_echo', 'am_eric', 'am_liam', 'am_onyx',
              'am_adam', 'bf_emma', 'bf_isabella', 'bf_alice', 'bf_lily', 'bm_george', 'bm_fable', 'bm_lewis', 'bm_daniel']
VOICES_FEMALE = ['af_bella', 'af_sarah', 'bf_emma', 'af_nicole', 'bf_isabella']
VOICES_MALE = ['am_michael', 'am_fenrir', 'bm_george', 'bm_lewis', 'am_puck']
VOICES_KID = ['af_sky', 'am_puck']

# delivery -> speed multiplier, voice effect, pause after (s)
DELIVERY = {
    'normal':  (1.00, None, 0.18),
    'calm':    (0.96, None, 0.22),
    'warm':    (0.97, None, 0.2),
    'slow':    (0.86, None, 0.45),
    'whisper': (0.88, 'whisper', 0.4),
    'tense':   (1.0, None, 0.25),
    'scared':  (1.05, 'shaky', 0.2),
    'panic':   (1.14, 'shaky', 0.08),
    'shout':   (1.08, 'loud', 0.15),
    'sad':     (0.9, None, 0.35),
    'deadpan': (0.92, None, 0.3),
    'cold':    (0.9, 'cold', 0.35),
    'creepy':  (0.82, 'creepy', 0.4),
    'excited': (1.08, None, 0.12),
    'relieved': (0.95, None, 0.3),
}
DELIVERY_ALIASES = {'whispering': 'whisper', 'quiet': 'whisper', 'fear': 'scared', 'afraid': 'scared', 'nervous': 'scared',
                    'terrified': 'panic', 'fast': 'panic', 'yell': 'shout', 'scream': 'shout', 'flat': 'deadpan',
                    'emotionless': 'deadpan', 'ominous': 'slow', 'dramatic': 'slow', 'mysterious': 'slow',
                    'happy': 'warm', 'friendly': 'warm', 'uneasy': 'tense', 'serious': 'tense'}
VOICE_FX = ['none', 'deep', 'deep_reverb', 'reverb', 'phone', 'radio', 'distant', 'echo', 'whisper', 'creepy', 'cold',
            'shaky', 'loud', 'demon']

MOODS = ['calm_normal', 'uneasy', 'tension_rise', 'dread', 'chase', 'silence', 'aftermath', 'host']
MOOD_ALIASES = {'calm': 'calm_normal', 'normal': 'calm_normal', 'creepy': 'uneasy', 'tension': 'tension_rise',
                'suspense': 'tension_rise', 'scary': 'dread', 'horror': 'dread', 'run': 'chase', 'action': 'chase',
                'none': 'silence', 'quiet': 'silence', 'sad': 'aftermath', 'ending': 'aftermath', 'outro': 'host',
                'intro': 'host'}
AMBIENCES = ['none', 'room_tone', 'night_outside', 'forest', 'rain', 'wind', 'bus', 'car', 'highway', 'hum',
             'fridge', 'clock', 'fire', 'tv_static', 'crowd_far', 'basement', 'storm']
AMB_ALIASES = {'room': 'room_tone', 'house': 'room_tone', 'indoor': 'room_tone', 'night': 'night_outside',
               'crickets': 'night_outside', 'street': 'night_outside', 'woods': 'forest', 'bus_engine': 'bus',
               'engine': 'car', 'road': 'highway', 'electric': 'hum', 'buzz': 'hum', 'fluorescent': 'hum',
               'campfire': 'fire', 'fireplace': 'fire', 'static': 'tv_static', 'thunder': 'storm', 'cellar': 'basement'}
BG_AMBIENCE = {'bus_stop': 'night_outside', 'bus_interior': 'bus', 'bus_front': 'bus', 'road_night': 'car',
               'car_interior': 'car', 'gas_station': 'hum', 'store_night': 'hum', 'store_counter': 'hum', 'forest': 'forest', 'campsite': 'fire',
               'suburban_street': 'night_outside', 'house_exterior': 'night_outside', 'front_door': 'night_outside',
               'living_room': 'room_tone', 'kitchen': 'fridge', 'hallway': 'room_tone', 'bedroom': 'clock',
               'basement_door': 'room_tone', 'basement': 'basement', 'attic': 'wind', 'bathroom': 'room_tone',
               'office_night': 'hum', 'parking_garage': 'hum', 'motel_room': 'room_tone', 'elevator': 'hum',
               'school_hallway': 'hum', 'cornfield': 'wind', 'cemetery': 'wind', 'window_view': 'room_tone',
               'cabin': 'fire', 'staircase': 'room_tone', 'plain_dark': 'none'}
EXTERIOR = {'bus_stop', 'road_night', 'gas_station', 'forest', 'campsite', 'suburban_street', 'house_exterior',
            'front_door', 'cornfield', 'cemetery'}
CAMERAS = ['slow_push', 'push_in', 'pull_out', 'pan_left', 'pan_right', 'drift', 'close', 'extreme_close', 'punch',
           'static', 'shake']
CAM_ALIASES = {'zoom_in': 'push_in', 'slow_zoom': 'slow_push', 'zoom_out': 'pull_out', 'pan': 'pan_right',
               'handheld': 'drift', 'closeup': 'close', 'close_up': 'close', 'ecu': 'extreme_close'}
SCARES = ['jumpscare', 'stinger', 'lights_out', 'lights_on', 'glitch', 'reveal', 'flash']
TRANSITIONS = ['cut', 'fade', 'flash', 'hard_cut_black']
PURPOSES = ['hook', 'host_intro', 'setup', 'open_loop', 'red_flag', 'rehook', 'tension', 'climax', 'scare', 'twist',
            'ending', 'host_outro', 'cta', 'breather']


class Issue:
    def __init__(self, kind, msg, scene=None, weight=1):
        self.kind, self.msg, self.scene, self.weight = kind, msg, scene, weight

    def __str__(self):
        where = f' (cảnh {self.scene + 1})' if self.scene is not None else ''
        return f'[{self.kind}] {self.msg}{where}'


def load(path):
    with open(path, 'r', encoding='utf-8-sig') as f:
        return json.load(f)


def _key(name):
    return re.sub(r'[^a-z0-9]+', '_', (name or '').strip().lower()).strip('_') or 'narrator'


def _res(name, table, aliases, default):
    n = (name or '').strip().lower().replace(' ', '_').replace('-', '_')
    if n in table:
        return n, True
    if n in aliases:
        return aliases[n], True
    return default, n == ''


def _when(v):
    """Parse a timing spec into {'at': s} / {'at_line': k} / {'after_line': k}."""
    if v is None:
        return None
    if isinstance(v, (int, float)):
        return {'at': float(v)}
    if isinstance(v, str):
        if v in ('scare', 'event'):
            return {'scare': True}
        if v.startswith('line'):
            return {'at_line': int(re.sub(r'\D', '', v) or 0)}
        try:
            return {'at': float(v)}
        except ValueError:
            return None
    if isinstance(v, dict):
        return {k: v[k] for k in ('at', 'at_line', 'after_line', 'scare') if k in v}
    return None


def normalize(data, cfg):
    issues = []
    narr = data.get('narrator') or {}
    out = {
        'title': data.get('title', 'Untitled story'),
        'target_minutes': data.get('target_minutes'),
        'youtube': data.get('youtube', {}) or {},
        'shorts': data.get('shorts') or {},
        'speed': float(data.get('speed', cfg.get('speed', 1.0))),
        'cast': {},
        'scenes': [],
        'voices': {},
        'voice_fx': {},
        'host_key': None,
        'music_volume': data.get('music_volume'),
    }
    cast_in = data.get('cast', []) or []
    main = next((c for c in cast_in if c.get('role') == 'main'), None)
    if narr.get('voice'):
        nv = narr['voice']
    elif main and (main.get('gender') or '').lower() == 'female':
        nv = cfg.get('narrator_voice_female', 'af_bella')
    else:
        nv = cfg.get('narrator_voice', 'am_michael')
    out['voices']['narrator'] = nv
    out['voice_fx']['narrator'] = narr.get('fx') or None
    out['narrator_speed'] = float(narr.get('speed', 1.0))
    if nv not in ALL_VOICES:
        issues.append(Issue('Giọng lạ', f'giọng kể "{nv}" không có trong Kokoro, vẫn thử dùng'))

    fig_style = data.get('figure_style') or cfg.get('figure_style') or F.DEFAULT_STYLE
    if not F.resolve_style(fig_style):
        issues.append(Issue('Kiểu vẽ lạ', f'figure_style "{fig_style}" chưa có ({", ".join(F.STYLES)}), dùng "{F.DEFAULT_STYLE}"'))
        fig_style = F.DEFAULT_STYLE
    out['figure_style'] = F.resolve_style(fig_style)

    fi = mi = ki = 0
    for i, c in enumerate(cast_in):
        name = c.get('name') or f'Person {i + 1}'
        spec = dict(c)
        gender = (c.get('gender') or '').lower()
        ctype = c.get('type', 'person')
        if ctype not in F.TYPES:
            issues.append(Issue('Loại nhân vật lạ', f'"{ctype}" của {name} chưa có, dùng "person"'))
            ctype = 'person'
        spec['type'] = ctype
        spec.setdefault('hair', 'long' if gender == 'female' else 'short')
        if spec['hair'] not in F.HAIRS:
            issues.append(Issue('Thiếu kiểu tóc', f'"{spec["hair"]}" của {name} chưa có, dùng "short"'))
            spec['hair'] = 'short'
        if spec.get('outfit') and spec['outfit'] not in F.OUTFITS:
            issues.append(Issue('Thiếu trang phục', f'"{spec["outfit"]}" của {name} chưa có, dùng "hoodie"'))
            spec['outfit'] = 'hoodie'
        wear = []
        for w in spec.get('wear', []) or []:
            if w in F.WEARS:
                wear.append(w)
            elif w and w != 'none':
                issues.append(Issue('Thiếu phụ kiện', f'"{w}" của {name} chưa có, bỏ qua'))
        spec['wear'] = wear
        spec['name'] = name
        if spec.get('style') and not F.resolve_style(spec['style']):
            issues.append(Issue('Kiểu vẽ lạ', f'"{spec["style"]}" của {name} chưa có ({", ".join(F.STYLES)}), dùng mặc định'))
            spec.pop('style')
        spec['default_style'] = fig_style
        look = F.Look(spec)
        voice = c.get('voice')
        if not voice:
            if c.get('role') == 'main':
                voice = nv
            elif c.get('age') == 'kid' or ctype == 'child_ghost':
                voice = VOICES_KID[ki % 2]; ki += 1
            elif gender == 'female':
                voice = VOICES_FEMALE[fi % len(VOICES_FEMALE)]; fi += 1
            elif ctype == 'driver' or c.get('role') == 'host':
                voice = 'bm_george'
            else:
                voice = VOICES_MALE[mi % len(VOICES_MALE)]; mi += 1
        if voice not in ALL_VOICES:
            issues.append(Issue('Giọng lạ', f'"{voice}" của {name} không có trong Kokoro, vẫn thử dùng'))
        vfx = c.get('voice_fx')
        if vfx is None and (ctype == 'driver' or c.get('role') == 'host'):
            vfx = 'deep_reverb'
        if vfx is None and ctype in ('shadow', 'silhouette', 'tall_figure'):
            vfx = 'demon'
        if vfx is None and ctype in ('mimic', 'pale_man', 'child_ghost', 'raincoat_man'):
            vfx = 'creepy'
        if vfx and vfx not in VOICE_FX:
            issues.append(Issue('Hiệu ứng giọng lạ', f'"{vfx}" chưa có ({", ".join(VOICE_FX)})'))
            vfx = None
        k = _key(name)
        out['cast'][k] = {'name': name, 'look': look, 'voice': voice, 'role': c.get('role', ''),
                          'speed': float(c.get('speed', 0.92 if (ctype == 'driver' or c.get('role') == 'host') else 1.0))}
        out['voices'][k] = voice
        out['voice_fx'][k] = vfx
        if c.get('role') == 'host' or (ctype == 'driver' and out['host_key'] is None):
            out['host_key'] = k

    # ---- scenes with carry-forward
    carry = {'bg': 'plain_dark', 'time': 'night', 'lights': 'on', 'weather': 'clear', 'mood': 'uneasy',
             'ambience': None, 'grade': data.get('grade', 'cold'), 'fx': None, 'opts': {}, 'darkness': 1.0}
    prev_chars, prev_bg, prev_raw_chars = {}, None, []
    for si, s in enumerate(data.get('scenes', []) or []):
        if 'bg' in s or 'background' in s:
            bgn, ok = BG.resolve(s.get('bg', s.get('background')))
            if not ok:
                issues.append(Issue('Thiếu nền', f'"{s.get("bg")}" chưa có, dùng "plain_dark"', si))
            if bgn != carry['bg']:
                carry['opts'] = {}
                carry['ambience'] = None
            carry['bg'] = bgn
        for k in ('time', 'lights', 'weather', 'grade', 'darkness'):
            if k in s:
                carry[k] = s[k]
        if 'opts' in s:
            carry['opts'] = dict(s['opts'] or {})
        if 'mood' in s:
            m, ok = _res(s['mood'], MOODS, MOOD_ALIASES, 'uneasy')
            if not ok:
                issues.append(Issue('Nhạc lạ', f'mood "{s["mood"]}" chưa có ({", ".join(MOODS)})', si))
            carry['mood'] = m
        if 'ambience' in s:
            a, ok = _res(s['ambience'], AMBIENCES, AMB_ALIASES, 'room_tone')
            if not ok:
                issues.append(Issue('Âm nền lạ', f'"{s["ambience"]}" chưa có', si))
            carry['ambience'] = a
        if 'fx' in s:
            carry['fx'] = list(s['fx'] or [])
        bg = carry['bg']
        opts = dict(carry['opts'])
        opts['time'] = carry['time']
        opts['lights'] = carry['lights']
        fxs = set(carry['fx'] if carry['fx'] is not None else ['grain'])
        w = carry['weather'] if bg in EXTERIOR else 'clear'
        if w in ('rain', 'storm'):
            fxs.add('rain' if w == 'rain' else 'rain_heavy')
        if w in ('fog', 'mist'):
            fxs.add('fog')
        if w == 'fog_heavy':
            fxs.add('fog_heavy')
        if s.get('flashback') or s.get('found_footage'):
            fxs.add('vhs')
        cam, ok = _res(s.get('camera', 'slow_push'), CAMERAS, CAM_ALIASES, 'slow_push')
        if not ok:
            issues.append(Issue('Camera lạ', f'"{s.get("camera")}" chưa có, dùng slow_push', si))
        purpose = (s.get('purpose') or '').lower()
        if purpose and purpose not in PURPOSES:
            issues.append(Issue('Mục đích cảnh lạ', f'purpose "{purpose}" ({", ".join(PURPOSES)})', si, 0))
        sc = {
            'index': si, 'id': s.get('id', f's{si + 1:02d}'), 'purpose': purpose, 'chapter': s.get('chapter'),
            'bg': bg, 'bg_opts': opts, 'camera': cam, 'fx': sorted(fxs), 'grade': carry['grade'],
            'darkness': float(carry['darkness']), 'mood': carry['mood'],
            'ambience': carry['ambience'] or BG_AMBIENCE.get(bg, 'room_tone'),
            'transition': s.get('transition', 'cut'), 'chars': [], 'props': [], 'lines': [], 'sfx_raw': s.get('sfx', []) or [],
            'hold': float(s.get('hold', 0) or 0), 'pause': s.get('pause'), 'shorts': bool(s.get('shorts')),
            'shake_amt': 0.5 if s.get('shake') else 0.0, 'scare_raw': s.get('scare'), 'events_raw': s.get('events', []) or [],
            'end_black': 1.0 if s.get('transition') == 'hard_cut_black' else 0.0,
            'extra_lights': [], 'music_hit': s.get('music_hit'),
        }
        if sc['transition'] not in TRANSITIONS:
            sc['transition'] = 'cut'
        if sc['transition'] == 'hard_cut_black':
            sc['transition'] = 'cut'
        if carry['weather'] in ('rain', 'storm') and sc['ambience'] in ('night_outside', 'room_tone', 'hum'):
            sc['ambience'] = 'rain' if bg in EXTERIOR or bg in ('window_view', 'attic') else sc['ambience']
        # characters
        chars = s.get('chars', s.get('characters'))
        if chars == 'same':
            chars = prev_raw_chars
        chars = chars or []
        prev_raw_chars = chars
        if len([c for c in chars if not c.get('far')]) > 3:
            issues.append(Issue('Nhiều nhân vật', f'{len(chars)} nhân vật trong 1 cảnh, dễ rối hình (nên <=3)', si))
        cur = {}
        for ci, c in enumerate(chars):
            k = _key(c.get('name'))
            if k not in out['cast']:
                issues.append(Issue('Nhân vật chưa khai báo', f'"{c.get("name")}" không có trong cast, tạo tạm', si))
                look = F.Look({'name': c.get('name'), 'default_style': out['figure_style']})
                out['cast'][k] = {'name': c.get('name'), 'look': look, 'voice': VOICES_MALE[0], 'role': '', 'speed': 1.0}
                out['voices'][k] = VOICES_MALE[0]
                out['voice_fx'][k] = None
            pose, ok = F.resolve_pose(c.get('pose', c.get('action', 'idle')))
            if not ok:
                issues.append(Issue('Thiếu tư thế', f'"{c.get("pose")}" chưa có, dùng "idle"', si))
            raw_emo = c.get('emotion', '')
            emo, ok = F.resolve_expr(raw_emo)
            if not ok:
                issues.append(Issue('Thiếu biểu cảm', f'"{raw_emo}" chưa có, dùng "neutral"', si))
            if not raw_emo:
                emo = F.POSE_EMOTION.get(pose, 'blank' if out['cast'][k]['look'].entity else 'neutral')
            n_main = len([c2 for c2 in chars if not c2.get('far')])
            dx = {1: [0.5], 2: [0.33, 0.67], 3: [0.25, 0.5, 0.75]}.get(n_main, [0.5])
            x = float(c.get('x', dx[min(ci, len(dx) - 1)]))
            x = max(0.06, min(0.94, x))
            far = c.get('far')
            scale = float(c.get('scale', 0.45 if far else 1.0))
            y = c.get('y')
            if y is None and far:
                y = BG.GROUND_Y - 0.22
            enter = c.get('enter')
            if enter is True:
                enter = 'left' if x < 0.5 else 'right'
            exit_ = c.get('exit')
            if exit_ is True:
                exit_ = 'left' if x < 0.5 else 'right'
            facing = c.get('facing', 'auto')
            cc = {'key': k, 'name': out['cast'][k]['name'], 'look': out['cast'][k]['look'], 'x': x, 'pose': pose,
                  'emotion': emo, 'facing_raw': facing, 'enter': enter, 'exit': exit_, 'scale': scale,
                  'continues': (k in prev_chars and prev_bg == bg and not enter),
                  'seed': (zlib.crc32(k.encode()) % 100) / 37.0,
                  'appear_raw': _when(c.get('appear')), 'vanish_raw': _when(c.get('vanish')),
                  'appear_fade': float(c.get('fade', 0.0)), 'move_pose': c.get('move_pose')}
            if y is not None:
                cc['y'] = float(y)
            if c.get('min_light') is not None:
                cc['min_light'] = float(c['min_light'])
            sc['chars'].append(cc)
            cur[k] = cc
            # held lights add real light to the scene
            if pose == 'flashlight':
                fdir = 1 if facing in ('right', 1) or (facing == 'auto' and x < 0.5) else -1
                sc['extra_lights'].append({'kind': 'cone_side', 'x': x + 0.05 * fdir * scale, 'y': (cc.get('y', BG.GROUND_Y)) - 0.3 * scale,
                                           'r': 0.75, 'spread': 0.2, 'col': '#FFF2CC', 'power': 1.15, 'dir': fdir})
            elif pose in ('phone_light',):
                fdir = 1 if facing in ('right', 1) or (facing == 'auto' and x < 0.5) else -1
                sc['extra_lights'].append({'kind': 'cone_side', 'x': x + 0.05 * fdir, 'y': BG.GROUND_Y - 0.32,
                                           'r': 0.55, 'spread': 0.28, 'col': '#F2F6FF', 'power': 0.9, 'dir': fdir})
            elif pose in ('phone', 'sit_phone'):
                sc['extra_lights'].append({'kind': 'point', 'x': x, 'y': (cc.get('y', BG.GROUND_Y)) - 0.36 * scale,
                                           'r': 0.16, 'col': '#A9D2F5', 'power': 0.7})
        xs = sorted(cc['x'] for cc in sc['chars'] if cc['scale'] > 0.7)
        for a, b in zip(xs, xs[1:]):
            if b - a < 0.18:
                issues.append(Issue('Nhân vật sát nhau', f'khoảng cách x chỉ {b - a:.2f} (nên >=0.22)', si))
                break
        for cc in sc['chars']:
            fr = cc['facing_raw']
            if fr in ('left', -1):
                cc['facing'] = -1
            elif fr in ('right', 1):
                cc['facing'] = 1
            else:
                others = [o['x'] for o in sc['chars'] if o is not cc]
                if others:
                    nearest = min(others, key=lambda ox: abs(ox - cc['x']))
                    cc['facing'] = 1 if nearest > cc['x'] else -1
                else:
                    cc['facing'] = 1 if cc['x'] <= 0.5 else -1
        # props
        for pi, p in enumerate(s.get('props', []) or []):
            if isinstance(p, str):
                p = {'type': p}
            name, group, ok = PR.resolve(p.get('type'))
            if not ok:
                issues.append(Issue('Thiếu đồ vật', f'"{p.get("type")}" chưa có, dùng "eyes"', si))
            q = dict(p)
            q['type'] = name
            q['group'] = group
            q['x'] = max(0.02, min(0.98, float(p.get('x', 0.5))))
            q['y'] = max(0.05, min(0.95, float(p.get('y', 0.47 if group == 'insert' else 0.6))))
            q['scale'] = max(0.2, min(4.0, float(p.get('scale', 1.0))))
            q['when'] = _when(p.get('at')) if 'at' in p else ({'at_line': p['at_line']} if 'at_line' in p else None)
            q['until'] = ({'at_line': p['until_line']} if 'until_line' in p else _when(p.get('until')))
            if group == 'glow' and name in ('phone', 'candle', 'lantern', 'tv_static'):
                sc['extra_lights'].append({'kind': 'point', 'x': q['x'], 'y': q['y'], 'r': 0.22 * q['scale'],
                                           'col': {'phone': '#A9D2F5', 'tv_static': '#C8D0DA', 'lantern': p.get('color', '#C8102E')}.get(name, '#FFB45A'),
                                           'power': 0.8, 'flicker': name in ('candle', 'tv_static'), 'flame': name == 'candle'})
            sc['props'].append(q)
        # lines
        for li, ln in enumerate(s.get('lines', []) or []):
            text = (ln.get('text') or '').strip()
            if not text:
                continue
            spk = ln.get('speaker', 'Narrator')
            k = _key(spk)
            if k in ('host', 'mr_long') and out['host_key']:
                k = out['host_key'] if k == 'host' else k
            if k != 'narrator' and k not in out['cast']:
                issues.append(Issue('Người nói lạ', f'"{spk}" không có trong cast, dùng giọng kể', si))
                k = 'narrator'
            d, ok = _res(ln.get('delivery', 'normal'), DELIVERY, DELIVERY_ALIASES, 'normal')
            if not ok:
                issues.append(Issue('Cách đọc lạ', f'delivery "{ln.get("delivery")}" chưa có ({", ".join(DELIVERY)})', si, 0))
            sp, dfx, dpause = DELIVERY[d]
            base_speed = out['narrator_speed'] if k == 'narrator' else out['cast'][k]['speed']
            vfx = ln.get('fx') or dfx or out['voice_fx'].get(k)
            if dfx and out['voice_fx'].get(k) and dfx in ('whisper', 'shaky', 'loud'):
                vfx = out['voice_fx'][k] + '+' + dfx
            nwords = len(textfx.plain(text).split())
            if nwords > 24:
                issues.append(Issue('Câu quá dài', f'{nwords} từ, nên tách đôi (giọng đọc dễ đều đều)', si))
            sc['lines'].append({'speaker': spk, 'speaker_key': k, 'text': text, 'tts_text': textfx.plain(text),
                                'voice': out['voices'].get(k, nv), 'speed': base_speed * sp, 'delivery': d,
                                'vfx': vfx, 'pause_after': float(ln.get('pause_after', dpause))})
        # focus for camera
        f = s.get('focus')
        if isinstance(f, (list, tuple)) and len(f) == 2:
            sc['focus_x'], sc['focus_y'] = float(f[0]), float(f[1])
        elif isinstance(f, (int, float)):
            sc['focus_x'], sc['focus_y'] = float(f), 0.5
        else:
            spk = [cc for cc in sc['chars'] if any(l['speaker_key'] == cc['key'] for l in sc['lines'])]
            tgt = spk[0] if spk else (sc['chars'][0] if sc['chars'] else None)
            sc['focus_x'] = tgt['x'] if tgt else 0.5
            lowp = {'hide': 0.2, 'crouch': 0.22, 'cower': 0.16, 'sit': 0.3, 'sit_phone': 0.3, 'sit_scared': 0.3,
                    'sit_talk': 0.3, 'drive': 0.3, 'lie': 0.12, 'sleep': 0.12, 'lie_awake': 0.12}
            hk = lowp.get(tgt['pose'], 0.38) if tgt else 0.38
            sc['focus_y'] = (tgt.get('y', BG.GROUND_Y) - hk * tgt['scale']) if tgt else 0.5
        if not sc['lines'] and sc['hold'] <= 0:
            sc['hold'] = 1.6
        if not sc['chars'] and not sc['props'] and not sc['lines'] and bg == 'plain_dark':
            issues.append(Issue('Cảnh trống', 'không có nhân vật, đồ vật hay lời', si))
        out['scenes'].append(sc)
        prev_chars, prev_bg = cur, bg

    # pacing checks that need no audio
    run = 1
    for a, b in zip(out['scenes'], out['scenes'][1:]):
        same = a['bg'] == b['bg'] and [c['pose'] for c in a['chars']] == [c['pose'] for c in b['chars']] \
            and a['camera'] == b['camera'] and not b['props']
        if same and b['chars']:
            issues.append(Issue('Hình lặp', 'giống cảnh trước (cùng nền, tư thế, camera)', b['index']))
        run = run + 1 if a['camera'] == 'static' and b['camera'] == 'static' else 1
        if run == 3:
            issues.append(Issue('Hình đứng yên', '3 cảnh liền camera static, nên thêm chuyển động', b['index']))
    if not out['scenes']:
        issues.append(Issue('Kịch bản trống', 'không có cảnh nào'))
    if any(v['look'].style == 'mascot' for v in out['cast'].values()):
        issues += _mascot_checks(out)
    return out, issues


def _mascot_checks(out):
    """Mascot style: every pose must map to a reviewed action; report substitutes and missing renderer."""
    from engine.mascot import actions as MA
    found = []
    try:
        import resvg_py  # noqa: F401
    except ImportError:
        found.append(Issue('Thiếu thư viện', 'kiểu vẽ mascot cần resvg-py: chạy lại setup.bat (pip install resvg-py)'))
    for sc in out['scenes']:
        for c in sc['chars']:
            if c['look'].style != 'mascot':
                continue
            for pn in (c['pose'], c.get('move_pose')):
                if not pn:
                    continue
                if pn in MA.SUBSTITUTE:
                    found.append(Issue('Động tác thay thế', f'{c["look"].name}: "{pn}" chưa có ở góc chính diện, dùng {MA.SUBSTITUTE[pn]}', sc['index']))
                elif pn not in MA.ACTIONS:
                    found.append(Issue('Động tác chưa có', f'{c["look"].name}: "{pn}" chưa có trong thư viện mascot, dùng idle', sc['index']))
    return found


# ------------------------------------------------------------------ retention report (after timing)
def retention_report(script):
    """Return (score 0-100, list of Issue) about hook, open loops, re-hooks, scares, pacing."""
    issues = []
    sc = script['scenes']
    total = sum(s['duration'] for s in sc) or 1
    score = 100

    def bad(kind, msg, w, scene=None):
        nonlocal score
        score -= w
        issues.append(Issue(kind, msg, scene, w))

    first_line = next(((s['start'] + s['lines'][0]['start']) for s in sc if s['lines']), None)
    if first_line is None or first_line > 1.5:
        bad('Hook chậm', f'câu đầu tiên bắt đầu ở giây {first_line or 0:.1f}, nên trong 1 giây đầu', 10)
    hook_end = 0
    for s in sc:
        if s['start'] > 20:
            break
        if s['purpose'] == 'hook':
            hook_end = s['start'] + s['duration']
    if not any(s['purpose'] == 'hook' for s in sc[:4]):
        bad('Thiếu hook', 'không có cảnh purpose "hook" ở đầu video', 12)
    elif hook_end > 18:
        bad('Hook dài', f'phần hook kéo tới giây {hook_end:.0f}, nên <= 15 giây', 6)
    host = script.get('host_key')
    if host:
        host_secs = 0.0
        for s in sc:
            if s['start'] > 45:
                break
            for ln in s['lines']:
                if ln['speaker_key'] == host:
                    host_secs += ln['end'] - ln['start']
        if host_secs > 9:
            bad('Intro người dẫn dài', f'người dẫn nói {host_secs:.0f} giây trong 45 giây đầu, nên <= 8 giây', 6)
    if not any(s['purpose'] == 'open_loop' and s['start'] < 75 for s in sc):
        bad('Thiếu vòng lặp tò mò', 'không có cảnh "open_loop" trong 75 giây đầu (câu hỏi chỉ trả lời ở cuối)', 10)
    if total > 180:
        rh = [s for s in sc if s['purpose'] in ('rehook', 'open_loop', 'red_flag') and 90 <= s['start'] <= 330]
        if not any(s['purpose'] == 'rehook' for s in rh):
            bad('Thiếu re-hook', 'không có cảnh "rehook" ở phút 1.5-5.5 (nơi người xem hay bỏ đi)', 10)
        gaps = sorted([0.0] + [s['start'] for s in sc if s['purpose'] in ('rehook', 'scare', 'red_flag', 'twist', 'climax')] + [total])
        longest = max(b - a for a, b in zip(gaps, gaps[1:]))
        if longest > 180:
            bad('Khoảng lặng dài', f'có đoạn {longest / 60:.1f} phút không có điểm bất ngờ / re-hook nào', 6)
    twist = [s for s in sc if s['purpose'] == 'twist']
    if not twist:
        bad('Thiếu twist', 'không có cảnh "twist"', 8)
    else:
        after = total - twist[-1]['start'] - twist[-1]['duration']
        if after > 45:
            bad('Kết lê thê', f'sau twist còn {after:.0f} giây, nên <= 40 giây (kể cả outro)', 8)
    jumps = [(s, e) for s in sc for e in s.get('events', []) if e['kind'] == 'jumpscare']
    if len(jumps) > 2:
        bad('Quá nhiều jumpscare', f'{len(jumps)} jumpscare, tối đa 2 để không bị nhàm', 6)
    for s, e in jumps:
        if e.get('silence', 0) < 0.4:
            bad('Thiếu khoảng lặng', 'jumpscare cần im lặng 0.5-1 giây ngay trước', 3, s['index'])
    def longest_shot(s):
        marks = [0.0] + [c['t'] for c in s.get('cuts', [])] + [s['duration']]
        return max(b - a for a, b in zip(marks, marks[1:]))
    long_sc = [s for s in sc if longest_shot(s) > 9 and not any(p['group'] == 'insert' for p in s['props'])]
    if long_sc:
        bad('Cảnh dài', f'{len(long_sc)} cảnh dài hơn 9 giây không đổi hình (nên 3-7 giây)', min(10, 2 * len(long_sc)),
            long_sc[0]['index'])
    avg = total / max(1, sum(1 + len(s.get('cuts', [])) for s in sc))
    if avg > 7.5:
        bad('Nhịp chậm', f'trung bình {avg:.1f} giây/cảnh, nên 4-6 giây', 6)
    tm = script.get('target_minutes')
    if tm:
        diff = total / 60 - float(tm)
        if abs(diff) > float(tm) * 0.2:
            bad('Sai thời lượng', f'video {total / 60:.1f} phút, mục tiêu {tm} phút', 3)
    return max(0, score), issues


def library():
    return {
        'backgrounds': BG.library(),
        'props': PR.library(),
        'cameras': CAMERAS,
        'transitions': TRANSITIONS,
        'moods': MOODS,
        'ambiences': AMBIENCES,
        'deliveries': list(DELIVERY),
        'voice_fx': VOICE_FX,
        'purposes': PURPOSES,
        'scares': SCARES,
        'fx': ['grain', 'fog', 'fog_heavy', 'rain', 'rain_heavy', 'vhs'],
        'weather': ['clear', 'rain', 'storm', 'fog', 'fog_heavy'],
        'voices': ALL_VOICES,
        **F.library(),
    }
