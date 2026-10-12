"""Improvement notes: every render appends what went wrong or could be better.

notes/IMPROVEMENTS.md has two parts:
  1. "Ghi chú của bạn" - the owner writes feedback here by hand.
  2. "Nhật ký tự động" - the tool appends one block per render.
When the owner asks Claude to upgrade the tool, Claude reads this file.
"""
import os
import datetime

HEADER = """# Ghi chú cải thiện Horror Studio

Khi muốn nâng cấp tool, bảo Claude: "đọc E:\\HorrorStudio\\notes\\IMPROVEMENTS.md và nâng cấp".

## Ghi chú của bạn
(Viết ở đây những gì bạn thấy chưa đẹp sau khi xem video. Ví dụ:)
- [ ] Tay nhân vật khi vẫy còn cứng
- [ ] Cần thêm nền: siêu thị

## Nhật ký tự động
"""


def append(notes_dir, title, issues, stats):
    os.makedirs(notes_dir, exist_ok=True)
    path = os.path.join(notes_dir, 'IMPROVEMENTS.md')
    if not os.path.exists(path):
        with open(path, 'w', encoding='utf-8') as f:
            f.write(HEADER)
    now = datetime.datetime.now().strftime('%Y-%m-%d %H:%M')
    lines = [f'\n### {now} - {title}']
    for k, v in stats.items():
        lines.append(f'- {k}: {v}')
    if issues:
        seen = {}
        for it in issues:
            seen.setdefault(str(it.kind) + '|' + it.msg, []).append(it.scene)
        lines.append('- Vấn đề phát hiện:')
        for key, scenes in seen.items():
            kind, msg = key.split('|', 1)
            sc = [s + 1 for s in scenes if s is not None]
            where = f' (cảnh {", ".join(map(str, sc[:12]))}{"..." if len(sc) > 12 else ""})' if sc else ''
            lines.append(f'  - [{kind}] {msg}{where}')
    else:
        lines.append('- Không phát hiện vấn đề tự động. Hãy xem video và ghi chú ở phần trên.')
    with open(path, 'a', encoding='utf-8') as f:
        f.write('\n'.join(lines) + '\n')
    return path
