"""Automatic checks for every action x body type: feet on the ground, props in a holding hand,
hands where the action says they are, IK targets in reach."""
import math
from . import art, actions as A, render as R

# action -> (landmark key in art.LAST, which wrist, max distance in head radii)
CONTACT = {
    'cover_mouth': ('mouth', 'R', .55), 'shush': ('mouth', 'R', .6), 'call': ('ear_R', 'R', .75), 'drink': ('mouth', 'R', .9),
    'think': ('chin', 'R', .9), 'listen': ('ear_R', 'R', .9),
}
AIRBORNE = set()


def hand_centre(L, side):
    w = L['wrist_' + side]
    a = math.radians(L['wang_' + side])
    return (w[0] - math.sin(a) * 34, w[1] + math.cos(a) * 34)


def check(c, name, ts=(0.0, 0.35, 0.8, 1.3)):
    problems = []
    for t in ts:
        pose = R.build_pose(c, name, t)
        p = dict(pose)
        p.update(R.expression('neutral', 0, False, t, pose))
        art.char2(c, p)
        L = art.LAST
        g = L['ground'] - 50
        low = max(f[1] for f in L['feet'])
        if name not in AIRBORNE and abs(low - g) > 6:
            problems.append(f'chân lệch mặt đất {low - g:+.0f}')
        for i, side in enumerate('LR'):
            if L['props'][i] and L['hands'][i] != 'hold':
                problems.append(f'đồ vật ở tay {side} nhưng bàn tay không cầm')
        if pose.get('_unreachable'):
            problems.append('tay không với tới: ' + ','.join(pose['_unreachable']))
        if name in CONTACT:
            key, side, lim = CONTACT[name]
            hc = hand_centre(L, side)
            d = math.hypot(hc[0] - L[key][0], hc[1] - L[key][1]) / L['head_r']
            if d > lim:
                problems.append(f'tay chưa tới {key} ({d:.2f} > {lim})')
    return sorted(set(problems))


def run_all(cast):
    out = {}
    for cname, c in cast.items():
        for name in A.ACTIONS:
            out[(cname, name)] = check(c, name)
    return out
