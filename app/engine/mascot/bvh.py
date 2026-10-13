"""Tiny BVH reader + forward kinematics, and conversion to the mascot's front-view 2D angles."""
import math
import numpy as np


def load(path):
    toks = open(path).read().split()
    i = 0
    joints, stack = [], []
    while toks[i] != 'MOTION':
        t = toks[i]
        if t in ('ROOT', 'JOINT'):
            joints.append(dict(name=toks[i + 1], parent=stack[-1] if stack else None, offset=None, channels=[]))
            i += 2
        elif t == 'End':
            joints.append(dict(name=joints[stack[-1]]['name'] + '_end', parent=stack[-1], offset=None, channels=[]))
            i += 2
        elif t == '{':
            stack.append(len(joints) - 1); i += 1
        elif t == '}':
            stack.pop(); i += 1
        elif t == 'OFFSET':
            joints[stack[-1]]['offset'] = np.array([float(x) for x in toks[i + 1:i + 4]]); i += 4
        elif t == 'CHANNELS':
            n = int(toks[i + 1]); joints[stack[-1]]['channels'] = toks[i + 2:i + 2 + n]; i += 2 + n
        else:
            i += 1
    i += 1
    nf = int(toks[i + 1]); ft = float(toks[i + 4]); i += 5
    nch = sum(len(j['channels']) for j in joints)
    data = np.array(toks[i:i + nf * nch], dtype=float).reshape(nf, nch)
    return joints, data, ft


def rot(axis, deg):
    r = math.radians(deg); c, s = math.cos(r), math.sin(r)
    if axis == 'X':
        return np.array([[1, 0, 0], [0, c, -s], [0, s, c]])
    if axis == 'Y':
        return np.array([[c, 0, s], [0, 1, 0], [-s, 0, c]])
    return np.array([[c, -s, 0], [s, c, 0], [0, 0, 1]])


def positions(joints, frame):
    out, R, P = {}, [None] * len(joints), [None] * len(joints)
    k = 0
    for ji, j in enumerate(joints):
        local_t = j['offset'].copy()
        local_r = np.eye(3)
        for ch in j['channels']:
            v = frame[k]; k += 1
            if ch.endswith('position'):
                local_t['XYZ'.index(ch[0])] += v
            else:
                local_r = local_r @ rot(ch[0], v)
        if j['parent'] is None:
            R[ji], P[ji] = local_r, local_t
        else:
            p = j['parent']
            R[ji] = R[p] @ local_r
            P[ji] = P[p] + R[p] @ local_t
        out[j['name']] = P[ji]
    return out


def ang(a, b):
    """Rig angle of the screen-space direction a->b (0 = down, clockwise positive)."""
    dx, dy = b[0] - a[0], b[1] - a[1]
    return math.degrees(math.atan2(-dx, dy))


def front_view(p, right):
    """Project to a camera standing in front of the character: screen x, screen y (down)."""
    hip = p['Hips']
    up = np.array([0, 1, 0])
    return lambda q: (-float(np.dot(q - hip, right)), -float(np.dot(q - hip, up)))


def to_pose(joints, data, ft, fps=24, start=0.0, dur=None, facing=None):
    """Sample a clip and return per-frame rig angles + root motion."""
    nf = len(data)
    t_end = nf * ft if dur is None else min(nf * ft, start + dur)
    frames = []
    t = start
    while t < t_end:
        p = positions(joints, data[min(nf - 1, int(t / ft))])
        r = p['RightUpLeg'] - p['LeftUpLeg']; r[1] = 0; r /= (np.linalg.norm(r) or 1)
        S = front_view(p, r)
        hip, neck, head = S(p['Hips']), S(p['Neck1']), S(p['Head'])
        lean = math.degrees(math.atan2(neck[0] - hip[0], -(neck[1] - hip[1])))
        tilt = math.degrees(math.atan2(head[0] - neck[0], -(head[1] - neck[1]))) - lean
        # screen-left limbs are the character's right side
        legs = (ang(S(p['RightUpLeg']), S(p['RightLeg'])), ang(S(p['RightLeg']), S(p['RightFoot'])),
                ang(S(p['LeftUpLeg']), S(p['LeftLeg'])), ang(S(p['LeftLeg']), S(p['LeftFoot'])))
        armL = (ang(S(p['RightArm']), S(p['RightForeArm'])) - lean, ang(S(p['RightForeArm']), S(p['RightHand'])) - lean)
        armR = (ang(S(p['LeftArm']), S(p['LeftForeArm'])) - lean, ang(S(p['LeftForeArm']), S(p['LeftHand'])) - lean)
        fwd = np.cross(r, np.array([0, 1, 0]))
        frames.append(dict(t=t - start, legs=legs, armL=armL, armR=armR, lean=lean, tilt=tilt,
                           root=p['Hips'].copy(), fwd=fwd, hip_h=float(p['Hips'][1])))
        t += 1.0 / fps
    return frames
