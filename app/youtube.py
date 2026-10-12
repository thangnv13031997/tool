"""Title scoring and YouTube text for high CTR horror videos.

The score is a checklist of what usually works for English horror story
channels. It cannot predict CTR exactly; use YouTube's Test & Compare with the
3 thumbnails and the top titles.
"""
import re

POWER = ['never', "don't", 'do not', 'rule', 'rules', 'last', 'night', 'alone', 'why', 'what', 'who', 'something',
         'someone', 'shouldn\'t', 'should not', 'wrong', 'strange', 'weird', 'creepy', 'scary', 'dark', 'found',
         'knock', 'door', 'basement', 'attic', 'window', 'neighbor', 'babysit', 'stranger', 'camping', 'woods',
         'motel', 'gas station', 'night shift', 'stop', 'warned', 'warning', 'wasn\'t', 'was not', 'still',
         'again', 'every night', 'behind', 'inside', 'watching', 'followed', 'missing', 'disappeared', 'hiding']
CURIOSITY = ['why', 'what', 'who', 'never', "don't", 'one rule', 'one strange', 'wasn\'t', 'shouldn\'t', 'still don\'t',
             'something', 'someone', 'the reason', 'turned out', 'found out', 'realized', 'crossed out', 'missing',
             'one was', 'came back', 'wasn\'t there', 'strange', 'only one', 'last rule', 'nobody', 'no one',
             'should have', 'still there', 'shouldn\'t have', 'didn\'t', 'gone']
SPOILER_HINTS = ['was a ghost', 'was dead', 'twist', 'ending explained', 'it was him', 'it was her', 'the killer was']
BANNED = ['true story', '100% real', 'real footage', 'not fake', 'gone wrong', 'police']


def score_title(title, thumb_text=''):
    t = (title or '').strip()
    low = t.lower()
    notes = []
    score = 50
    n = len(t)
    if 35 <= n <= 60:
        score += 12
    elif n <= 70:
        score += 4
        notes.append(f'{n} ký tự: hơi dài, điện thoại có thể cắt sau ~60 ký tự')
    else:
        score -= 10
        notes.append(f'{n} ký tự: quá dài, nên <= 60')
    if n < 25:
        score -= 6
        notes.append('quá ngắn, thiếu tình huống gây tò mò')
    pw = [w for w in POWER if w in low]
    score += min(15, 5 * len(pw))
    if not pw:
        notes.append('thiếu từ khóa gây tò mò/kinh dị (rule, never, night, door, neighbor...)')
    cu = [w for w in CURIOSITY if w in low]
    if cu:
        score += 8
    else:
        notes.append('nên có yếu tố bí ẩn chưa giải thích (why / never / something...)')
    if re.search(r'\b(i|my|me)\b', low):
        score += 6
    else:
        notes.append('ngôi thứ nhất ("I", "My") thường tạo cảm giác chuyện thật, dễ đồng cảm')
    if re.search(r'\d', t):
        score += 3
    if t.isupper() or sum(1 for w in t.split() if len(w) > 3 and w.isupper()) > 2:
        score -= 8
        notes.append('không viết hoa toàn bộ, chỉ 1 từ nếu cần')
    for b in BANNED:
        if b in low:
            score -= 25
            notes.append(f'bỏ "{b}": truyện hư cấu, ghi vậy là gây hiểu lầm và dễ bị YouTube phạt')
    for sp in SPOILER_HINTS:
        if sp in low:
            score -= 15
            notes.append('tiêu đề đang lộ twist, người xem không cần bấm vào nữa')
    if thumb_text:
        tw = set(re.findall(r"[a-z']+", thumb_text.lower()))
        ttw = set(re.findall(r"[a-z']+", low))
        common = {w for w in tw & ttw if len(w) > 3}
        if len(common) >= 2:
            score -= 6
            notes.append('chữ trên thumbnail trùng tiêu đề; nên bổ sung ý mới thay vì lặp lại')
    if t.endswith('?') or '...' in t:
        score += 2
    return max(0, min(100, score)), notes


def score_thumb_text(text):
    words = re.findall(r"[A-Za-z0-9']+", (text or '').replace('*', ''))
    notes = []
    s = 100
    if len(words) > 4:
        s -= 15 * (len(words) - 4)
        notes.append(f'{len(words)} từ: nên 2-4 từ để đọc được trên điện thoại')
    if not words:
        s -= 30
        notes.append('không có chữ: thumbnail kinh dị thường cần 2-4 chữ gây tò mò')
    return max(0, s), notes


def rank_titles(options, thumb_text=''):
    out = []
    for t in options:
        if not t:
            continue
        s, n = score_title(t, thumb_text)
        out.append((s, t, n))
    out.sort(key=lambda x: -x[0])
    return out


def fmt_ts(sec):
    sec = int(sec)
    h, m, s = sec // 3600, (sec % 3600) // 60, sec % 60
    return f'{h}:{m:02d}:{s:02d}' if h else f'{m}:{s:02d}'


def build_text(script, issues_out, Issue):
    yt = script.get('youtube') or {}
    options = list(dict.fromkeys([yt.get('title')] + list(yt.get('title_options') or []) + [script['title']]))
    thumb = yt.get('thumbnail') or {}
    vars_ = thumb.get('variants') or ([thumb] if thumb else [])
    tt = (vars_[0].get('text') if vars_ else '') or ''
    ranked = rank_titles([o for o in options if o], tt)
    best = ranked[0][1] if ranked else script['title']
    chapters = []
    for sc in script['scenes']:
        if sc.get('chapter'):
            chapters.append((sc['start'], sc['chapter']))
    if chapters and chapters[0][0] > 0.5:
        chapters.insert(0, (0.0, yt.get('first_chapter', 'Intro')))
    ok_ch = len(chapters) >= 3 and all(b[0] - a[0] >= 10 for a, b in zip(chapters, chapters[1:]))
    if chapters and not ok_ch:
        issues_out.append(Issue('Chương YouTube', 'cần >=3 chương, mỗi chương >=10 giây, đã bỏ chương'))
    desc = (yt.get('description') or '').strip()
    parts = [desc]
    if ok_ch:
        parts.append('\n'.join(f'{fmt_ts(t)} {n}' for t, n in chapters))
    parts.append(yt.get('disclaimer', 'This story is a work of fiction. Any resemblance to real people or events is coincidental.'))
    hashtags = yt.get('hashtags') or ['horrorstories', 'scarystories', 'animation']
    parts.append(' '.join(h if h.startswith('#') else '#' + h for h in hashtags[:5]))
    full_desc = '\n\n'.join(p for p in parts if p)
    lines = ['=== TIÊU ĐỀ ĐỀ XUẤT (điểm cao nhất) ===', best, '']
    lines.append('=== XẾP HẠNG TIÊU ĐỀ (điểm /100 + gợi ý) ===')
    for s, t, n in ranked:
        lines.append(f'{s:3d}  {t}')
        for x in n:
            lines.append(f'      - {x}')
    lines.append('')
    if vars_:
        lines.append('=== CHỮ TRÊN THUMBNAIL ===')
        for i, v in enumerate(vars_[:3]):
            s, n = score_thumb_text(v.get('text', ''))
            lines.append(f'{"ABC"[i]}: {v.get("text", "")}  ({s}/100) ' + ('; '.join(n)))
        lines.append('Mẹo: dùng YouTube Studio > Test & Compare để thử cả 3 thumbnail, giữ cái thắng.')
        lines.append('')
    lines += ['=== MÔ TẢ (Description) ===', full_desc, '']
    tags = yt.get('tags') or ['scary stories', 'horror stories', 'animated horror stories', 'creepy stories']
    lines += ['=== THẺ (Tags) ===', ', '.join(tags), '']
    lines += ['=== CÀI ĐẶT KHI ĐĂNG ===',
              '- Thumbnail: thumbnail_A.jpg (thử B, C bằng Test & Compare)',
              '- Phụ đề: tải subtitles.srt (English)',
              "- Audience: No, it's not made for kids",
              '- Video language: English | Category: ' + yt.get('category', 'Film & Animation'),
              '- Altered or synthetic content: No (hoạt hình người que, không giả người thật)',
              '- Giờ đăng gợi ý: 19:00-21:00 giờ miền Đông Mỹ (khoảng 6:00-8:00 sáng giờ Việt Nam)',
              '- Gắn video vào playlist của kênh và đặt màn hình kết thúc trỏ tới tập kế tiếp']
    if yt.get('pinned_comment'):
        lines += ['', '=== BÌNH LUẬN GHIM ===', yt['pinned_comment']]
    return best, '\n'.join(lines) + '\n', ranked
