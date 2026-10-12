# Định dạng kịch bản Horror Studio (JSON)

Hướng dẫn đầy đủ (bằng tiếng Anh, để Claude đọc) nằm ở `docs/PROMPT_FOR_CLAUDE.md`.
Danh sách mọi giá trị hợp lệ (nền, tư thế, biểu cảm, đồ vật, nhạc, âm thanh...) nằm ở `docs/library.json`; app tự xuất lại mỗi lần mở.
Xem tập mẫu `scripts/ep01_night_shift_rules.json` để biết cách viết từng loại cảnh.

## Khung chung
| Trường | Ý nghĩa |
|---|---|
| title | Tên tập (tiếng Anh) |
| target_minutes | Thời lượng mong muốn, tool cảnh báo nếu lệch nhiều |
| narrator | Giọng người kể (hành khách): `voice`, `speed`, `fx` |
| cast | Nhân vật. `role`: main (người kể), host (Mr. Long). `type`: person, driver, shadow, silhouette, tall_figure, raincoat_man, pale_man, mimic, child_ghost |
| youtube | `title_options`, `description`, `tags`, `hashtags`, `pinned_comment`, `thumbnail.variants` (3 bố cục: face_threat, object, split) |
| shorts | `scenes: [từ, đến]` (đánh số từ 1), `hook_text`, `end_text` |
| scenes | Danh sách cảnh |

## Mỗi cảnh (3-7 giây lời đọc)
- **purpose**: hook, host_intro, setup, open_loop, red_flag, rehook, tension, breather, climax, scare, twist, ending, host_outro. Tool dùng để chấm điểm giữ chân.
- **bg / time / lights / weather / mood / ambience / fx**: tự giữ nguyên cho các cảnh sau đến khi bạn đổi.
- **camera**: slow_push, push_in, pull_out, pan_left, pan_right, drift, close, extreme_close, punch, shake, static. `focus: [x, y]` để ngắm.
- **chars**: tên, `x`, `pose`, `emotion`, `facing`, `enter`/`exit`, `far` (ở xa), `appear`/`vanish` (hiện/biến mất), `fade`.
  `"chars": "same"` = giữ nhân vật cảnh trước.
- **props**: đồ vật trong cảnh (coffee, footprints, handprint, doll, key...), đồ phát sáng (clock, phone, candle, lantern, eyes, tv_static),
  cận cảnh phủ lên (chat, note, rules, cctv, polaroid, card). Hẹn giờ bằng `at_line`, `until_line`, `at`.
- **lines**: `speaker` ("Narrator" hoặc tên nhân vật), `text` (bọc `*từ*` để tô vàng, `**từ**` để tô đỏ), `delivery`
  (whisper, scared, panic, slow, cold, creepy...), `fx` (phone, phone+creepy, distant...), `pause_after`.
- **sfx**: `{ "name": "knock", "at_line": 1 }`.
- **scare**: `{ "type": "jumpscare", "entity": "face", "after_line": 0, "silence": 0.8 }`. Tối đa 2 jumpscare mỗi video.
- **transition**: cut, fade, flash, hard_cut_black. **chapter**: tên chương YouTube.
