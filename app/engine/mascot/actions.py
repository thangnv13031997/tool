"""Action library: every script pose maps to exactly one reviewed action.

An action is f(t) -> pose dict for art.char2 (arm specs, legs, lean, tilt, hands, props...).
Expressions are applied separately (see render.expression), so actions only describe the body.
"""
import json, math, os
from . import parts as P

HERE = os.path.dirname(os.path.abspath(__file__))
PHONE = P.phone()
FLASH = P.flashlight()
CUP = ('<rect x="-30" y="-4" width="60" height="70" rx="10" fill="#e8e2d6" stroke="#2a1f2b" stroke-width="6"/>'
       '<path d="M30 12 C52 12 52 46 30 46" fill="none" stroke="#2a1f2b" stroke-width="6"/>'
       '<rect x="-24" y="2" width="48" height="12" rx="4" fill="#6b3b22"/>')
GLOW_PHONE = '<rect x="-26" y="-6" width="52" height="88" rx="10" fill="#22252c" stroke="#2a1f2b" stroke-width="6"/><rect x="-19" y="2" width="38" height="66" rx="5" fill="#dff3ff"/>'

IDLE_L, IDLE_R = ('angles', 10, 6), ('angles', -10, -6)


def S(t, hz, ph=0.0):
    return math.sin(2 * math.pi * hz * t + ph)


def breathe(t):
    return dict(tilt=1.2 * S(t, .3))


def tremble(t, k=1.0):
    return k * (math.sin(t * 61) * 1.6 + math.sin(t * 47) * 1.1)


def arm(a1, a2, d1=0.0, d2=0.0):
    return ('angles', a1 + d1, a2 + d2)


# ---------------------------------------------------------------- mocap loops (baked from CMU BVH)
_MOCAP = {}


def mocap(name, t, speed=1.0):
    if name not in _MOCAP:
        with open(os.path.join(HERE, 'motion', name + '.json')) as f:
            _MOCAP[name] = json.load(f)
    m = _MOCAP[name]
    fr = m['frames']
    x = (t * speed * m['fps']) % len(fr)
    i = int(x)
    k = x - i
    a, b = fr[i], fr[(i + 1) % len(fr)]
    lerp = lambda u, v: [p + (q - p) * k for p, q in zip(u, v)]
    legs = lerp(a['legs'], b['legs'])
    return dict(legs=tuple(legs), armL=('angles',) + tuple(lerp(a['armL'], b['armL'])),
                armR=('angles',) + tuple(lerp(a['armR'], b['armR'])), lean=a['lean'] + (b['lean'] - a['lean']) * k,
                tilt=(a['tilt'] + (b['tilt'] - a['tilt']) * k) * .6, lean_mode='hip')


# ---------------------------------------------------------------- the actions
def idle(t):
    return dict(armL=arm(10, 6, 1.5 * S(t, .3), 2 * S(t, .3, 1)), armR=arm(-10, -6, -1.5 * S(t, .3, .5), -2 * S(t, .3, 2)), **breathe(t))


def talk(t):
    g = S(t, 1.1)
    return dict(armL=IDLE_L, armR=arm(-30, -100, 6 * g, 16 * g), tilt=2 * S(t, 1.6))


def explain(t):
    return dict(armL=arm(40, 110, 8 * S(t, .9), 14 * S(t, .9)), armR=arm(-40, -110, -8 * S(t, .9, 1.4), -14 * S(t, .9, 1.4)),
                tilt=2 * S(t, 1.2))


def wave(t):
    return dict(armL=IDLE_L, armR=arm(-160, -185, 0, 20 * S(t, 2.2)), hands=('open', 'open'), **breathe(t))


def wave_slow(t):
    return dict(armL=IDLE_L, armR=arm(-150, -175, 0, 10 * S(t, .6)))


def point(t):
    return dict(armL=IDLE_L, armR=arm(-90, -92, 1.5 * S(t, .5)), hands=('open', 'point'), look=1, **breathe(t))


def think(t):
    return dict(armL=('at', 'belly', 20, -20, 1), armR=('at', 'chin', 30, 110, 1), hands=('fist', 'fist'),
                wrist_R=170, tilt=6 + 2 * S(t, .25), lookup=1)


def shrug(t):
    k = .5 + .5 * S(t, .5)
    return dict(armL=arm(55, 150, 8 * k), armR=arm(-55, -150, -8 * k), hands=('open', 'open'), tilt=-5)


def phone(t):
    return dict(armL=IDLE_L, armR=('at', 'chest', 20, 110, 1), wrist_R=160, hands=('open', 'hold'), props=(None, GLOW_PHONE),
                tilt=8 + S(t, .3), look=.3)


def call(t):
    return dict(armL=IDLE_L, armR=('at', 'ear_R', 20, 70, 1), wrist_R=200, hands=('open', 'hold'), props=(None, PHONE),
                tilt=-4 + 1.5 * S(t, .4), look=-.3)


def read(t):
    return dict(armL=('at', 'chest', -80, 130, -1), armR=('at', 'chest', 80, 130, 1), hands=('fist', 'fist'),
                paper=True, paper_ang=2 * S(t, .3), tilt=9)


def drink(t):
    up = .5 + .5 * S(t, .25)
    return dict(armL=IDLE_L, armR=('at', 'mouth', 40 + 30 * (1 - up), 120 + 60 * (1 - up), 1), wrist_R=180,
                hands=('open', 'hold'), props=(None, CUP), tilt=-3 * up)


def cross_arms(t):
    return dict(armL=('at', 'arm_R', -60, -10, 1), armR=('at', 'arm_L', 70, 30, -1), hands=('fist', 'fist'), **breathe(t))


def hug_self(t):
    tr = tremble(t, .5)
    return dict(armL=('at', 'arm_R', -60, -50 + tr, 1), armR=('at', 'arm_L', 70, -20 - tr, -1), hands=('open', 'open'),
                tilt=5 + tr * .3, legs=(2, 1, -2, -1))


def scared(t):
    tr = tremble(t)
    return dict(armL=('at', 'cheek_L', -30, 40 + tr, -1), armR=('at', 'cheek_R', 30, 40 - tr, 1), hands=('open', 'open'),
                legs=(8, 4, -8, -4), tilt=tr * .4, lean=tr * .2)


def terrified(t):
    tr = tremble(t, 1.4)
    return dict(armL=arm(150, 175, tr, tr * 1.5), armR=arm(-150, -175, -tr, -tr * 1.5), hands=('open', 'open'),
                legs=(10, 6, -10, -6), tilt=-4 + tr * .4)


def freeze(t):
    tr = tremble(t, .25)
    return dict(armL=arm(4, 2, tr), armR=arm(-4, -2, -tr), legs=(2, 1, -2, -1), tilt=tr * .2)


def cover_mouth(t):
    tr = tremble(t, .5)
    return dict(armL=('at', 'belly', 10, 0, 1), armR=('at', 'mouth', 40, 110 + tr, 1), wrist_R=168,
                hands=('fist', 'open'), tilt=3 + tr * .3)


def shush(t):
    return dict(armL=IDLE_L, armR=('at', 'mouth', 30, 120, 1), wrist_R=175, hands=('open', 'point'), tilt=2)


def flashlight(t):
    return dict(armL=IDLE_L, armR=arm(-78, -82, 2 * S(t, .5), 3 * S(t, .5, 1)), hands=('open', 'hold'), props=(None, FLASH),
                beam='R', look=1, **breathe(t))


def phone_light(t):
    return dict(armL=IDLE_L, armR=arm(-82, -96, 2 * S(t, .5)), hands=('open', 'hold'), props=(None, GLOW_PHONE),
                beam='R', beam_len=700, look=1, **breathe(t))


def hold_head(t):
    tr = tremble(t, .6)
    return dict(armL=('at', 'temple_L', -40, 90 + tr, -1), armR=('at', 'temple_R', 40, 90 - tr, 1), hands=('open', 'open'),
                tilt=4 + tr * .4)


def listen(t):
    return dict(armL=IDLE_L, armR=('at', 'ear_R', 70, 70, 1), wrist_R=200, hands=('open', 'open'), tilt=-8, look=-.6)


def knock(t):
    k = abs(S(t, 1.5))
    return dict(armL=IDLE_L, armR=arm(-70, -160, 0, 25 * k), hands=('open', 'fist'), lean=2)


def peek(t):
    return dict(armL=IDLE_L, armR=IDLE_R, lean=12, lean_mode='hip', tilt=6, look=1)


def look_back(t):
    return dict(armL=IDLE_L, armR=IDLE_R, tilt=-8 + S(t, .3), look=-1)


def walk(t):
    return mocap('walk', t)


def run(t):
    p = mocap('walk', t, 1.8)
    p['armL'] = ('angles', p['armL'][1] + 20, p['armL'][2] + 70)
    p['armR'] = ('angles', p['armR'][1] - 20, p['armR'][2] - 70)
    p['lean'] = p.get('lean', 0) + 4
    return p


def sneak(t):
    return mocap('sneak', t)


def back_away(t):
    p = mocap('walk', t, .7)
    p['armL'], p['armR'] = arm(35, 70), arm(-35, -70)
    p['lean'] = p.get('lean', 0) - 6
    p['hands'] = ('open', 'open')
    return p


SIT = dict(seat=True, thigh_k=.28, legs=(12, 2, -12, -2))


def sit(t):
    return dict(SIT, armL=arm(14, 40), armR=arm(-14, -40), hands=('open', 'open'), **breathe(t))


def sit_talk(t):
    d = talk(t)
    d.update(SIT)
    d['armL'] = arm(14, 40)
    return d


def sit_phone(t):
    d = phone(t)
    d.update(SIT)
    d['armL'] = arm(14, 40)
    return d


def sit_scared(t):
    d = scared(t)
    d.update(SIT)
    return d


def drive(t):
    return dict(SIT, seat=False, armL=('at', 'chest', -110, 150, -1), armR=('at', 'chest', 110, 150, 1),
                hands=('fist', 'fist'), wheel=True, tilt=S(t, .2))


def type_(t):
    j = 3 * S(t, 6)
    return dict(SIT, armL=('at', 'belly', -70, 20 + j, -1), armR=('at', 'belly', 70, 20 - j, 1), hands=('fist', 'fist'), tilt=8)


CROUCH = dict(thigh_k=.22, legs=(34, -14, -34, 14))


def crouch(t):
    return dict(CROUCH, armL=arm(30, 70), armR=arm(-30, -70), hands=('open', 'open'), tilt=4, look=.6)


def hide(t):
    tr = tremble(t, .5)
    return dict(CROUCH, armL=('at', 'cheek_L', -40, 0 + tr, -1), armR=('at', 'cheek_R', 40, 0 - tr, 1), hands=('open', 'open'), tilt=10)


def cower(t):
    tr = tremble(t)
    return dict(thigh_k=.18, legs=(40, -18, -40, 18), armL=('at', 'cheek_L', -20, 50 + tr, -1), armR=('at', 'cheek_R', 20, 50 - tr, 1),
                hands=('open', 'open'), tilt=8 + tr * .4)


def scream(t):
    d = terrified(t)
    d['mouth_force'] = 'scream'
    return d


def sleep(t):
    d = sit(t)
    d['eyes_force'] = 'closed'
    d['tilt'] = 12
    return d


ACTIONS = {
    'idle': idle, 'stand': idle, 'talk': talk, 'explain': explain, 'wave': wave, 'wave_slow': wave_slow, 'point': point,
    'think': think, 'shrug': shrug, 'phone': phone, 'call': call, 'read': read, 'drink': drink, 'cross_arms': cross_arms,
    'hug_self': hug_self, 'scared': scared, 'terrified': terrified, 'freeze': freeze, 'cover_mouth': cover_mouth,
    'shush': shush, 'flashlight': flashlight, 'phone_light': phone_light, 'hold_head': hold_head, 'listen': listen,
    'knock': knock, 'open_door': knock, 'reach': point, 'peek': peek, 'look_back': look_back, 'walk': walk, 'run': run,
    'run_scared': run, 'sneak': sneak, 'back_away': back_away, 'sit': sit, 'sit_talk': sit_talk, 'sit_phone': sit_phone,
    'sit_scared': sit_scared, 'drive': drive, 'type': type_, 'crouch': crouch, 'hide': hide, 'cower': cower,
    'scream': scream, 'sad': hug_self, 'laugh': explain, 'tired': idle, 'hands_on_hips': cross_arms,
    # entity poses on a normal person, and bed poses (front view has no bed yet)
    'loom': idle, 'stand_far': idle, 'lie': sleep, 'sleep': sleep, 'lie_awake': sit_scared,
}
# poses that need a substitute in the front view: reported by the script check
SUBSTITUTE = {'lie': 'sleep (ngồi ngủ)', 'sleep': 'sleep (ngồi ngủ)', 'lie_awake': 'sit_scared', 'open_door': 'knock',
              'reach': 'point', 'hands_on_hips': 'cross_arms', 'laugh': 'explain', 'sad': 'hug_self'}
ANIMATED = set(ACTIONS) - {'cross_arms'}
