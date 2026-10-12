"""Write a Horror Studio script with the Claude API (optional, needs your own API key).

Uses only the Python standard library: POST https://api.anthropic.com/v1/messages with streaming.
"""
import json
import os
import re
import urllib.request
import urllib.error

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
API_URL = 'https://api.anthropic.com/v1/messages'
DEFAULT_MODEL = 'claude-sonnet-5-5'


def system_prompt():
    import script_io
    with open(os.path.join(ROOT, 'docs', 'PROMPT_FOR_CLAUDE.md'), 'r', encoding='utf-8') as f:
        doc = f.read()
    lib = script_io.library()
    compact = {
        'backgrounds': lib['backgrounds']['names'], 'background_options': lib['backgrounds']['options'],
        'world_props': lib['props']['world_props'], 'glow_props': lib['props']['glow_props'],
        'inserts': lib['props']['inserts'], 'scare_entities': lib['props']['scare_entities'],
        'cameras': lib['cameras'], 'moods': lib['moods'], 'ambiences': lib['ambiences'],
        'deliveries': lib['deliveries'], 'voice_fx': lib['voice_fx'], 'purposes': lib['purposes'],
        'scares': lib['scares'], 'poses': lib['poses'], 'emotions': lib['emotions'], 'hair': lib['hair'],
        'outfits': lib['outfits'], 'wear': lib['wear'], 'types': lib['types'], 'voices': lib['voices'],
    }
    try:
        import audio
        compact['sfx'] = audio.library_info()['sfx']
    except Exception:
        pass
    return doc + '\n\n## LIBRARY (only these values exist)\n```json\n' + json.dumps(compact, ensure_ascii=False) + '\n```\n'


def user_prompt(idea, genre, minutes, gender, extra=''):
    return (f'Write one complete episode as a single JSON object in the Horror Studio format.\n'
            f'- Story idea: {idea or "(you choose an original idea that fits the genre)"}\n'
            f'- Genre: {genre}\n- Target length: about {minutes} minutes of narration\n'
            f'- Main character gender: {gender}\n{extra}\n'
            'Output ONLY the JSON object, no explanation, no markdown fence.')


def extract_json(text):
    t = text.strip()
    m = re.search(r'```(?:json)?\s*(\{.*\})\s*```', t, re.S)
    if m:
        t = m.group(1)
    a, b = t.find('{'), t.rfind('}')
    if a < 0 or b < 0:
        raise ValueError('Không thấy JSON trong câu trả lời')
    return json.loads(t[a:b + 1])


def write_script(api_key, idea, genre='rules horror', minutes=8, gender='female', model=None, extra='',
                 on_text=None, cancelled=lambda: False, max_tokens=32000):
    body = {
        'model': model or DEFAULT_MODEL,
        'max_tokens': max_tokens,
        'stream': True,
        'system': system_prompt(),
        'messages': [{'role': 'user', 'content': user_prompt(idea, genre, minutes, gender, extra)}],
    }
    req = urllib.request.Request(API_URL, data=json.dumps(body).encode('utf-8'), method='POST', headers={
        'x-api-key': api_key.strip(), 'anthropic-version': '2023-06-01', 'content-type': 'application/json'})
    out = []
    try:
        with urllib.request.urlopen(req, timeout=600) as r:
            for raw in r:
                if cancelled():
                    raise RuntimeError('Đã hủy')
                line = raw.decode('utf-8', 'replace').strip()
                if not line.startswith('data:'):
                    continue
                try:
                    ev = json.loads(line[5:].strip())
                except ValueError:
                    continue
                typ = ev.get('type')
                if typ == 'content_block_delta' and ev.get('delta', {}).get('type') == 'text_delta':
                    piece = ev['delta']['text']
                    out.append(piece)
                    if on_text:
                        on_text(piece)
                elif typ == 'error':
                    raise RuntimeError('Claude API lỗi: ' + json.dumps(ev.get('error', ev))[:400])
    except urllib.error.HTTPError as e:
        detail = e.read().decode('utf-8', 'replace')[:600]
        raise RuntimeError(f'Claude API trả lỗi {e.code}: {detail}')
    except urllib.error.URLError as e:
        raise RuntimeError(f'Không kết nối được Claude API: {e.reason}')
    return ''.join(out)
