# Ghi chú cải thiện Horror Studio

Khi muốn nâng cấp tool, bảo Claude: "đọc E:\HorrorStudio\notes\IMPROVEMENTS.md và nâng cấp".

## Ghi chú của bạn
(Viết ở đây những gì bạn thấy chưa đẹp sau khi xem video. Ví dụ:)
- [ ] Giọng Mr. Long còn vang quá
- [ ] Cần thêm nền: bệnh viện

## Việc nên làm tiếp (Claude ghi khi làm bản 1.0)
- [ ] Giọng chưa được nghe thử trên máy thật (môi trường của Claude không chạy được Kokoro). Lần đầu hãy xuất "Xem thử 40 giây đầu" và ghi nhận xét về giọng, nhấn nhá, độ lớn nhạc nền ở đây.
- [ ] Nhạc, âm nền và hiệu ứng đang là âm thanh tự tạo. Nếu thấy chưa đủ "điện ảnh", bỏ nhạc từ YouTube Audio Library vào library\music\<mood>.
- [ ] Kokoro chạy bằng CPU (torch bản CPU trong E:\LocalTTS\env_en). Bản CUDA sẽ nhanh hơn nhờ GTX 1650 Super nhưng phải sửa môi trường LocalTTS, cần bạn đồng ý.
- [ ] Nhân vật đứng ngoài cửa kính (store_counter, window_view) đang vẽ đè lên khung cửa, chưa có hiệu ứng kính mờ / phản chiếu.
- [ ] Thêm nền: bệnh viện, nhà vệ sinh trạm xăng, trong lều, thang máy hỏng, cầu thang thoát hiểm.
- [ ] Thêm tư thế: bò, leo cửa sổ, nhìn qua lỗ khóa, ngã.

## Nhật ký tự động

### 2026-10-12 09:20 - My Night Shift Had 7 Rules. Rule 7 Was Crossed Out.
- Thư mục: E:\HorrorStudio\output\20261012_0919_My-Night-Shift-Had-7-Rules-Rule-7-Was-Crossed-Out_PREVIEW
- Thời lượng video: 0:37 (7 cảnh)
- Điểm giữ chân (ước lượng): 79/100
- Thời gian dựng hình: 0:46 (24.4 khung/giây)
- Bộ mã hóa: h264_nvenc
- Chế độ: xem thử 40s
- Tổng thời gian: 1:38
- Vấn đề phát hiện:
  - [Chương YouTube] cần >=3 chương, mỗi chương >=10 giây, đã bỏ chương
