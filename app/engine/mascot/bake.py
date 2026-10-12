"""Dev tool: bake a looping gait from a CMU BVH file into motion/<name>.json (front-view rig angles).

python -m engine.mascot.bake 07_01.bvh walk 1.0
"""
import json, math, os, sys
from . import bvh

HERE = os.path.dirname(os.path.abspath(__file__))
FPS = 30


def bake(path, name, start=1.0):
    j, d, ft = bvh.load(path)
    fr = bvh.to_pose(j, d, ft, FPS, start=start, dur=4.5)
    key = lambda f: list(f['legs']) + list(f['armL']) + list(f['armR'])
    best, per = 1e9, None
    for p in range(int(.8 * FPS), int(2.8 * FPS)):
        dist = sum((a - b) ** 2 for a, b in zip(key(fr[0]), key(fr[p]))) + \
            sum((a - b) ** 2 for a, b in zip(key(fr[1]), key(fr[p + 1])))
        if dist < best:
            best, per = dist, p
    loop = fr[:per]
    # cross-fade the last few frames into the first ones so the loop has no pop
    n = 4
    for i in range(n):
        k = (i + 1) / (n + 1)
        a, b = loop[per - n + i], fr[per + i - n] if False else loop[i]
        for f in ('legs', 'armL', 'armR'):
            loop[per - n + i][f] = tuple(x + (y - x) * k * .5 for x, y in zip(loop[per - n + i][f], b[f]))
    out = dict(source=os.path.basename(path), credit='CMU Graphics Lab Motion Capture Database (mocap.cs.cmu.edu)',
               fps=FPS, frames=[dict(legs=[round(x, 2) for x in f['legs']], armL=[round(x, 2) for x in f['armL']],
                                     armR=[round(x, 2) for x in f['armR']], lean=round(f['lean'], 2), tilt=round(f['tilt'], 2)) for f in loop])
    os.makedirs(os.path.join(HERE, 'motion'), exist_ok=True)
    with open(os.path.join(HERE, 'motion', name + '.json'), 'w') as f:
        json.dump(out, f)
    print(name, 'period', per / FPS, 's, error', round(best, 1))


if __name__ == '__main__':
    bake(sys.argv[1], sys.argv[2], float(sys.argv[3]) if len(sys.argv) > 3 else 1.0)
