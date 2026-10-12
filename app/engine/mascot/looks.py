"""Map a horror-script character (engine.figure.Look) onto the mascot kit."""
from . import art

HAIR = {'none': 'none', 'bald': 'none', 'short': 'short', 'messy': 'messy', 'side_part': 'short', 'curly': 'curly',
        'long': 'long', 'ponytail': 'ponytail', 'bun': 'bun', 'bob': 'bob', 'buzz': 'buzz', 'bangs': 'bangs'}
TOP = {'hoodie': 'hoodie', 'jacket': 'jacket', 'tshirt': 'tshirt', 'sweater': 'sweater', 'raincoat': 'raincoat',
       'coat': 'raincoat', 'dress': 'dress', 'uniform': 'uniform', 'pajamas': 'sweater', 'suit': 'jacket',
       'flannel': 'jacket', 'scrubs': 'scrubs', 'apron': 'tshirt', 'hi_vis': 'jacket', 'overalls': 'tshirt'}
WEAR = ('glasses', 'cap', 'beanie', 'beard', 'mustache', 'backpack', 'scarf', 'name_tag', 'bus_cap')


def _hex(c):
    if isinstance(c, str):
        return c if c.startswith('#') else '#' + c
    return '#%02x%02x%02x' % tuple(int(v) for v in c[:3])


def _mix(a, b, k):
    a, b = _hex(a).lstrip('#'), _hex(b).lstrip('#')
    pa = [int(a[i:i + 2], 16) for i in (0, 2, 4)]
    pb = [int(b[i:i + 2], 16) for i in (0, 2, 4)]
    return '#%02x%02x%02x' % tuple(int(x + (y - x) * k) for x, y in zip(pa, pb))


def from_look(look):
    spec = getattr(look, 'spec', {}) or {}
    gender = (spec.get('gender') or '').lower()
    age = getattr(look, 'age', 'adult')
    body = spec.get('body') or {'kid': 'kid', 'elder': 'elder', 'teen': 'slim'}.get(age, 'normal')
    if float(spec.get('size', 1.0)) >= 1.15 and body == 'normal':
        body = 'chubby'
    top = TOP.get(look.outfit, 'hoodie')
    wear = [w for w in look.wear if w in WEAR]
    if look.type == 'driver' and 'bus_cap' not in wear:
        wear.append('bus_cap')
    if 'bus_cap' in wear and 'cap' in wear:
        wear.remove('cap')
    outfit = _hex(look.outfit_color)
    colors = dict(skin=_hex(look.skin), top=outfit, top2=('#f4f2ee' if top in ('hoodie', 'jacket') else _mix(outfit, '#000000', .18)),
                  pants=_hex(look.pants_color), shoe=_hex(look.shoe_color), hair=_hex(look.hair_color),
                  acc=_hex(spec.get('accent_color') or ('#1c2533' if 'bus_cap' in wear else '#a33a2a')),
                  eye=_hex(spec.get('eye_color_iris', '#5b3a24')), chair='#3b3f48')
    female = gender == 'female' or look.hair in ('long', 'ponytail', 'bun', 'bob')
    return dict(top=top, hair=HAIR.get(look.hair, 'short'), body=body, wear=tuple(wear), colors=colors,
                lashes=female, iris=True, freckles=bool(spec.get('freckles')))
