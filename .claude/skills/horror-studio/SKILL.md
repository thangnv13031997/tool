---
name: horror-studio
description: Hiểu và lưu repo Horror Studio (tool Python/Tkinter làm video kinh dị người que cho YouTube). Dùng khi cần tìm hiểu cấu trúc tool, sửa/nâng cấp tool, hoặc khi người dùng bảo "lưu repo", "commit", "đẩy lên GitHub", "sao lưu thay đổi".
---

# Horror Studio

Tool desktop (Windows, Python + Tkinter) biến kịch bản JSON thành video kinh dị người que kèm Shorts, 3 thumbnail, nội dung YouTube và phụ đề. Trên máy người dùng nằm ở `E:\HorrorStudio`. Giọng đọc dùng Kokoro ở `E:\LocalTTS` (không có trong repo, môi trường cloud không chạy được).

## Cấu trúc

| Đường dẫn | Vai trò |
|---|---|
| `app/main.py` | Giao diện 4 tab: xuất video, viết kịch bản AI, tiêu đề & thumbnail, âm thanh |
| `app/script_io.py` | Đọc/chuẩn hóa kịch bản JSON, chấm điểm giữ chân (`retention_report`) |
| `app/render.py` | Dựng timeline, dựng hình song song, mã hóa ffmpeg (NVENC/libx264), Shorts dọc |
| `app/engine/` | Vẽ hình: `figure` (người que, thực thể), `backgrounds` (31 bối cảnh), `props`, `fx`, `textfx`, `thumbnail`, `scene` |
| `app/audio.py` | Tự tạo nhạc/âm nền/hiệu ứng, trộn 3 lớp, ưu tiên file người dùng trong `library/` |
| `app/tts.py`, `app/tts_worker.py` | Gọi Kokoro qua tiến trình Python riêng, cache vào `output/_tts_cache` |
| `app/claude_api.py` | Viết kịch bản bằng Claude API |
| `app/youtube.py` | Chấm điểm tiêu đề CTR, tạo `youtube.txt` (mô tả, chương, tags) |
| `app/notes.py` | Ghi vấn đề sau mỗi lần xuất vào `notes/IMPROVEMENTS.md` |
| `docs/SCRIPT_FORMAT.md`, `docs/PROMPT_FOR_CLAUDE.md`, `docs/library.json` | Định dạng kịch bản và danh sách bối cảnh/nhân vật/âm thanh hợp lệ |
| `scripts/*.json` | Kịch bản các tập |
| `config.example.json` | Cấu hình mặc định (đưa lên git). `config.json` là bản riêng trên máy, tự tạo từ bản mẫu khi mở app |

Khi nâng cấp tool: đọc `notes/IMPROVEMENTS.md` trước, cập nhật `docs/` nếu thêm bối cảnh/tư thế/âm thanh mới, và kiểm tra cú pháp bằng `python3 -m py_compile app/*.py app/engine/*.py`.

## Lưu repo (commit + push)

1. `git status` và xem kỹ danh sách file.
2. **Không bao giờ commit** (đã có trong `.gitignore`):
   - `env/` (môi trường Python, tạo lại bằng `setup.bat`), `__pycache__/`
   - `config.json` (có thể chứa `anthropic_api_key`). Muốn đổi giá trị mặc định thì sửa `config.example.json`, và giữ `anthropic_api_key` trống.
   - `output/`, `logs/`, `library/_generated/`, âm thanh riêng trong `library/music|ambience|sfx/`
   Nếu thấy file nào trong số này đang được git theo dõi: `git rm -r --cached <đường dẫn>`.
3. Trước khi commit, quét bí mật: `git diff --cached | grep -iE "sk-ant-|api_key\"\s*:\s*\"[^\"]+"` phải không ra gì.
4. `git add -A`, commit với lời nhắn tiếng Việt ngắn gọn mô tả thay đổi (ví dụ "Thêm nền bệnh viện và tư thế bò").
5. Push lên nhánh đang làm việc: `git push -u origin <nhánh>`. Lỗi mạng thì thử lại tối đa 4 lần (chờ 2s, 4s, 8s, 16s). Không tạo pull request trừ khi người dùng yêu cầu.

## Đồng bộ về máy Windows

Commit đã gỡ `env/`, `output/`, `config.json`... khỏi git. Nếu máy người dùng chạy `git pull` từ phiên bản cũ, git sẽ **xóa** các thư mục đó trên máy. Hướng dẫn người dùng dùng lệnh sau thay cho `git pull` lần đầu (giữ nguyên file trên máy):

```
git fetch origin
git reset origin/<nhánh>
```
