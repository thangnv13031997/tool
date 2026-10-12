"""Kokoro TTS worker.

Runs with the Python that has Kokoro installed (E:\\LocalTTS\\env_en), NOT
with the app's own Python. It reads a job file and writes one WAV per line.

Job file (JSON): {"items": [{"text": "...", "voice": "af_heart", "speed": 1.0, "out": "C:/.../x.wav"}]}
Progress is printed to stdout as JSON lines.
"""
import json
import os
import sys
import time


def say(**kw):
    sys.stdout.write(json.dumps(kw) + '\n')
    sys.stdout.flush()


def main():
    job_path = sys.argv[1]
    with open(job_path, 'r', encoding='utf-8') as f:
        job = json.load(f)
    items = job['items']
    say(stage='loading', total=len(items))
    try:
        import numpy as np
        import soundfile as sf
        from kokoro import KPipeline
    except Exception as e:  # noqa
        say(stage='error', error='Không import được kokoro: %s' % e)
        return 2
    device = job.get('device') or None
    pipes = {}

    def pipe_for(voice):
        lang = voice[0] if voice and voice[0] in 'ab' else 'a'
        if lang not in pipes:
            try:
                pipes[lang] = KPipeline(lang_code=lang, repo_id='hexgrad/Kokoro-82M', device=device)
            except TypeError:
                pipes[lang] = KPipeline(lang_code=lang)
        return pipes[lang]

    t0 = time.time()
    for i, it in enumerate(items):
        try:
            pipe = pipe_for(it['voice'])
            chunks = []
            for res in pipe(it['text'], voice=it['voice'], speed=float(it.get('speed', 1.0)), split_pattern=r'\n+'):
                audio = getattr(res, 'audio', None)
                if audio is None and isinstance(res, (tuple, list)) and len(res) >= 3:
                    audio = res[2]
                if audio is None:
                    continue
                if hasattr(audio, 'detach'):
                    audio = audio.detach().cpu().numpy()
                chunks.append(np.asarray(audio, dtype='float32'))
            if not chunks:
                raise RuntimeError('Kokoro không trả về âm thanh')
            audio = np.concatenate(chunks)
            os.makedirs(os.path.dirname(it['out']), exist_ok=True)
            tmp = it['out'] + '.tmp.wav'
            sf.write(tmp, audio, 24000, subtype='PCM_16')
            os.replace(tmp, it['out'])
            say(stage='line', done=i + 1, total=len(items), secs=round(len(audio) / 24000, 2),
                elapsed=round(time.time() - t0, 1))
        except Exception as e:  # noqa
            say(stage='line_error', index=i, error=str(e)[:300])
    say(stage='done', elapsed=round(time.time() - t0, 1))
    return 0


if __name__ == '__main__':
    sys.exit(main())
