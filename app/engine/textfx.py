"""Fonts, captions and big text for horror videos.

Captions: Oswald SemiBold, white with a thick black outline, one or two
key words in yellow (or red for danger words written as **word**).
"""
import os
import re
from PIL import Image, ImageDraw, ImageFont

FONT_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), 'assets', 'fonts')
FONTS = {
    'caption': ('Oswald-Variable.ttf', 600),
    'body': ('Oswald-Variable.ttf', 500),
    'bold': ('Oswald-Variable.ttf', 700),
    'display': ('Anton-Regular.ttf', None),
    'creepy': ('Creepster-Regular.ttf', None),
    'type': ('SpecialElite-Regular.ttf', None),
}
_cache = {}

YELLOW = (255, 214, 64, 255)
RED = (235, 45, 45, 255)
WHITE = (245, 245, 240, 255)


def font(kind='caption', size=48):
    key = (kind, int(size))
    if key not in _cache:
        fname, wght = FONTS.get(kind, FONTS['caption'])
        path = os.path.join(FONT_DIR, fname)
        try:
            f = ImageFont.truetype(path, int(size))
            if wght:
                try:
                    f.set_variation_by_axes([wght])
                except Exception:
                    pass
            _cache[key] = f
        except OSError:
            _cache[key] = ImageFont.load_default(int(size))
    return _cache[key]


def parse_marked(text):
    """'I *never* saw **him**' -> [('I ', 0), ('never', 1), (' saw ', 0), ('him', 2)].

    *word*  = highlight yellow, **word** = danger red.
    """
    out = []
    pos = 0
    for m in re.finditer(r'\*\*([^*]+)\*\*|\*([^*]+)\*', text):
        if m.start() > pos:
            out.append((text[pos:m.start()], 0))
        if m.group(1) is not None:
            out.append((m.group(1), 2))
        else:
            out.append((m.group(2), 1))
        pos = m.end()
    if pos < len(text):
        out.append((text[pos:], 0))
    return out


def plain(text):
    t = re.sub(r'\*\*([^*]+)\*\*', r'\1', text or '')
    t = re.sub(r'\*([^*]+)\*', r'\1', t)
    return t.strip()


def words_marked(text):
    ws = []
    prev_end_space = True
    for seg, hi in parse_marked(text):
        glue = ws and seg and not seg[0].isspace() and not prev_end_space
        prev_end_space = (not seg) or seg[-1].isspace()
        if glue:
            head = seg.split()[0] if seg.split() else ''
            ws[-1] = (ws[-1][0] + head, ws[-1][1])
            seg = seg[len(head):]
        for w in seg.split():
            ws.append((w, hi))
    return ws


def chunk_words(words, max_words=5, max_chars=28):
    chunks, cur, n = [], [], 0
    for w, hi in words:
        add = len(w) + (1 if cur else 0)
        if cur and (len(cur) >= max_words or n + add > max_chars):
            chunks.append(cur)
            cur, n = [], 0
            add = len(w)
        cur.append((w, hi))
        n += add
        if w.endswith(('.', '!', '?', '...')) and len(cur) >= 2:
            chunks.append(cur)
            cur, n = [], 0
    if cur:
        chunks.append(cur)
    if len(chunks) >= 2 and len(chunks[-1]) == 1 and len(chunks[-2]) < max_words + 1:
        last = chunks.pop()
        chunks[-1] = chunks[-1] + last
    return chunks


def wrap_words(words, fnt, max_w, space_extra=0):
    lines, cur = [], []
    for w in words:
        test = cur + [w]
        txt = ' '.join(x[0] for x in test)
        if cur and fnt.getlength(txt) + space_extra * len(test) > max_w:
            lines.append(cur)
            cur = [w]
        else:
            cur = test
    if cur:
        lines.append(cur)
    return lines


def render_words(lines, fnt, fill=WHITE, hi_fill=YELLOW, danger_fill=RED,
                 stroke=8, stroke_fill=(8, 8, 10, 255), line_gap=1.05, align='center', shadow=0,
                 shadow_col=(0, 0, 0, 150)):
    asc, desc = fnt.getmetrics()
    lh = int((asc + desc) * line_gap)
    space = fnt.getlength(' ') + stroke * 0.6
    widths = [sum(fnt.getlength(w) for w, _ in ln) + space * (len(ln) - 1) for ln in lines]
    W = int(max(widths) + stroke * 2 + 8 + shadow)
    H = int(lh * len(lines) + stroke * 2 + 8 + shadow)
    img = Image.new('RGBA', (W, H), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    for pass_ in (('shadow',) if shadow else ()) + ('main',):
        y = stroke + 4
        for ln, lw in zip(lines, widths):
            x = (W - shadow - lw) / 2 if align == 'center' else stroke + 4
            for w, hi in ln:
                if pass_ == 'shadow':
                    d.text((x + shadow, y + shadow), w, font=fnt, fill=shadow_col,
                           stroke_width=stroke, stroke_fill=shadow_col)
                else:
                    col = danger_fill if hi == 2 else (hi_fill if hi else fill)
                    d.text((x, y), w, font=fnt, fill=col, stroke_width=stroke, stroke_fill=stroke_fill)
                x += fnt.getlength(w) + space
            y += lh
    return img


class CaptionCache:
    def __init__(self, width, height, size=62, vertical=False):
        self.W, self.H = width, height
        self.k = (width if vertical else height) / 1080.0
        self.size = size
        self.vertical = vertical
        self.cache = {}

    def caption(self, words):
        key = ('cap', tuple(words))
        if key not in self.cache:
            fnt = font('caption', self.size * self.k)
            lines = wrap_words(words, fnt, self.W * (0.86 if self.vertical else 0.74))
            self.cache[key] = render_words(lines, fnt, stroke=int(7 * self.k), shadow=int(4 * self.k))
            if len(self.cache) > 500:
                self.cache.pop(next(iter(self.cache)))
        return self.cache[key]

    def card(self, text, kind='display', size=110, color=WHITE):
        """Big centered title text (chapter cards, hook text on Shorts)."""
        key = ('card', text, kind, size)
        if key not in self.cache:
            fnt = font(kind, size * self.k)
            words = words_marked(text.upper() if kind == 'display' else text)
            lines = wrap_words(words, fnt, self.W * 0.82)
            self.cache[key] = render_words(lines, fnt, fill=color, stroke=int(8 * self.k), shadow=int(6 * self.k),
                                           line_gap=1.0)
        return self.cache[key]
