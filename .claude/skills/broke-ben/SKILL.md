---
name: broke-ben
description: "Kênh Broke Ben (tài chính cá nhân hoạt hình, tiếng Anh, linh vật Ben chibi và Piggy Ben): chọn đề tài, viết kịch bản giữ chân với số liệu tính bằng script, tiêu đề/thumbnail CTR, mô tả/tags/bình luận ghim, cài đặt kênh, ảnh kênh (avatar, banner, watermark), vẽ nhân vật và cảnh minh họa, dựng tool Money Studio. Dùng skill này bất cứ khi nào người dùng nhắc tới Broke Ben, Piggy Ben, kênh tài chính / money explained / personal finance của họ, hoặc muốn ý tưởng video, kịch bản, thumbnail, tiêu đề, ảnh kênh hay tool video cho kênh tiền bạc, kể cả khi không gọi đúng tên kênh."
---

# Broke Ben

Broke Ben là kênh YouTube tiếng Anh giải thích tiền bạc bằng hoạt hình phẳng, cho người 18–40 tuổi ở Mỹ, Anh, Canada, Úc,
những người có lương nhưng vẫn thấy thiếu tiền. Người làm kênh là người Việt: trao đổi với họ bằng tiếng Việt,
còn nội dung video (kịch bản, tiêu đề, mô tả) viết bằng tiếng Anh.

## Nhận diện kênh (giữ nhất quán ở mọi việc)

| | |
|---|---|
| Tên / handle | **Broke Ben** · `@BrokeBen` (dự phòng `@BrokeBenMoney`) |
| Khẩu hiệu | *Money, explained before it's gone.* |
| Linh vật | **Ben** (đã chốt, là avatar kênh): người trẻ đi làm, mặt tròn thân thiện, tóc rối kiểu hiện đại, hoodie xanh, **thẻ nhân viên đeo cổ** (không balo); 25 dáng, 9 cảm xúc (xem `references/art_style.md`). **Piggy Ben** (heo đất nứt dán băng) là vai phụ hài hước. |
| Lịch đăng | Thứ Tư và Thứ Bảy, 9:00–11:00 sáng giờ miền Đông Mỹ (khoảng 20:00–22:00 giờ Việt Nam) |
| Màu | mực `#1D212D`, xanh tiền `#2E8B57`, kem `#F6F1E6`, vàng `#FFC43D`, đỏ mất tiền `#D64545`. Xanh = tiền vào, đỏ = tiền ra. |
| Font | Anton (tiêu đề, số lớn), Oswald (phụ đề), Special Elite (hóa đơn) |
| Chuyên mục / ngôn ngữ | Education · English · Not made for kids |

Kênh sống nhờ hai thứ: **số liệu đúng** (người xem tài chính soi rất kỹ) và **một nhân vật có cá tính** (để không bị
YouTube coi là nội dung AI sản xuất hàng loạt, vốn bị phạt theo cả kênh). Mọi gợi ý nên phục vụ hai điều đó.

## Làm gì theo từng loại yêu cầu

**Ý tưởng / đề tài / lịch đăng** → đọc `references/topics.md`. Đề xuất theo tỷ lệ các nhóm chủ đề, không để hai video
liền nhau cùng nhóm. Mỗi đề tài kèm tiêu đề nháp, chữ thumbnail, câu mở đầu.

**Kịch bản** → đọc `references/script_guide.md`. Trước khi viết, tính mọi con số bằng `scripts/money_math.py`
(lãi kép, khoản vay, thẻ tín dụng, lạm phát, ngân sách) và giữ dòng "Assumptions" để đưa vào mô tả video.
Viết ở dạng bảng cảnh như hướng dẫn. Chỉ dùng tài sản hình ảnh đang có; cái nào chưa có thì ghi "needs new asset".
Số liệu thống kê thật mà không có nguồn thì đánh dấu `[SOURCE NEEDED: ...]` để người làm kênh kiểm tra.

**Tiêu đề, thumbnail, mô tả, tags, bình luận ghim** → công thức và mẫu ở `references/script_guide.md`.
Luôn đưa 4 tiêu đề xếp hạng và 3 phương án chữ thumbnail (để thử bằng Test & Compare).

**Cài đặt kênh, mô tả kênh, danh sách phát, trailer** → `references/channel_setup.md` có sẵn văn bản để dán.

**Ảnh kênh, nhân vật, cảnh minh họa, video thử** → đọc `references/art_style.md`, rồi chạy script trong `scripts/`
(cần Python 3 + Pillow; video cần ffmpeg). Ví dụ:
```
python <skill>/scripts/make_branding.py        # avatar (Ben vẫy tay), banner, watermark -> ./branding/
python <skill>/scripts/demo_animation.py       # video thử 9 giây -> ./demo/
```
Sau khi dựng bất kỳ hình nào, mở ảnh ra xem và sửa chỗ chồng chữ, lệch khung trước khi giao.
Dùng bảng màu và font ở trên; không tự đổi phong cách nhân vật nếu người làm kênh không yêu cầu.

**Tool Money Studio** (repo GitHub `thangnv13031997/broke-ben`, trên máy người dùng ở `E:\MoneyStudio`):
app Windows (Tkinter) dùng giọng Kokoro có sẵn ở `E:\LocalTTS\env_en` qua `app/tts_worker.py`, giống Horror Studio.
Xuất video 1080p + Shorts + 3 thumbnail + `youtube.txt` + phụ đề `subtitles_en.srt` / `subtitles_vi.srt`; có nút chọn
phụ đề trên video: tiếng Anh (bản đăng), tiếng Việt (bản để người làm kênh xem duyệt) hoặc không.
Có đoạn **Ben's Notebook**: lật trang sổ, bàn tay vẽ biểu đồ từng nét (`show.type = "sketch"`).
- **Kịch bản cho tool** = một object JSON đúng định dạng trong `docs/PROMPT_FOR_CLAUDE.md` của repo (bản sao trong
  `references/script_guide.md`, mục "Script deliverable format"). **Mỗi câu có `text` (tiếng Anh) và `vi` (tiếng Việt)**,
  cộng `youtube.title_vi` / `description_vi`, vì người làm kênh đọc tiếng Anh chưa tốt.
- Nâng cấp tool: đọc `notes/IMPROVEMENTS.md` trong repo; lõi vẽ là `app/engine/charkit.py` + `app/scene.py` + `app/elements.py`.
  Thử nhanh không cần Kokoro: `python app/render.py scripts/ep00_trailer.json --test --subs vi`.

## Giới hạn nội dung
- Chỉ giải thích khái niệm; không khuyên mua/bán cổ phiếu hay tiền ảo cụ thể, không hứa thu nhập, không "làm giàu nhanh".
- Mỗi video có dòng "for educational and entertainment purposes only and is not financial advice".
- Không nói "true story"; Ben là nhân vật hư cấu.
- Khai báo "Altered or synthetic content": No (hoạt hình, không giả người hay sự việc có thật).
