HORROR STUDIO - Tool làm video kinh dị người que cho kênh nước ngoài (Bus 13: Night Route)
=========================================================================================

CÀI LẦN ĐẦU (1 lần duy nhất)
1. Nháy đúp setup.bat. Tool sẽ:
   - tạo môi trường Python riêng (thư mục env), không đụng vào E:\LocalTTS hay E:\RelatableStudio
   - cài Pillow, numpy, ffmpeg (cần Internet)
   - tạo sẵn nhạc, âm thanh nền và hiệu ứng (thư mục library\_generated)
   - tạo lối tắt "Horror Studio" trên Desktop
2. Giọng đọc dùng Kokoro có sẵn ở E:\LocalTTS\env_en (giống Relatable Studio).
   Tập mẫu chỉ dùng giọng máy bạn đã có (af_heart, am_fenrir, am_michael, bm_george, bm_lewis).
   Giọng khác (am_onyx, am_echo...) nếu chưa có sẽ tự tải lần đầu (cần Internet).

DÙNG HẰNG NGÀY
1. Có kịch bản .json trong thư mục scripts (đã có sẵn tập mẫu ep01_night_shift_rules.json).
   Cách lấy kịch bản mới:
   - Miễn phí: tab "2. Viết kịch bản AI" > "Copy prompt + ý tưởng" > dán vào Claude chat > copy JSON trả về
     > "Dán JSON từ clipboard" > "Lưu vào scripts".
   - Tự động: nhập Anthropic API key ở tab 2, bấm "VIẾT KỊCH BẢN" (tính phí theo API).
2. Tab "1. Xuất video": chọn kịch bản, kéo thanh trượt xem từng cảnh. Góc phải có ĐIỂM GIỮ CHÂN (ước lượng).
   Bấm "Kiểm tra kịch bản" để xem lỗi: hook chậm, thiếu re-hook, cảnh dài, quá nhiều jumpscare...
3. Lần đầu nên chọn "Xem thử 40 giây đầu" để nghe giọng và xem hình. Muốn kiểm tra hình thật nhanh: tick "Thử nhanh không giọng".
4. Bấm XUẤT VIDEO. Thư mục output\<ngày>_<tên> gồm:
   - video.mp4               video 1920x1080, 30 khung/giây
   - shorts.mp4              bản dọc 1080x1920 dưới 60 giây (đoạn hook) để kéo người xem
   - thumbnail_A/B/C.jpg     3 thumbnail để thử bằng YouTube Studio > Test & Compare
   - thumbnail_preview_phone.jpg   xem thumbnail trông thế nào trên điện thoại
   - youtube.txt             tiêu đề xếp hạng theo điểm CTR, mô tả có sẵn chương, tags, cài đặt khi đăng
   - subtitles.srt           phụ đề tiếng Anh
   - render_report.txt       điểm giữ chân và các vấn đề phát hiện

HÌNH ẢNH (tự động theo kịch bản)
- Nhân vật cấp 3: người que có tóc, quần áo, mắt to biểu cảm; thực thể: bóng đen, người áo mưa vàng, người mặt trắng, ma trẻ con...
- 31 bối cảnh tối nhiều lớp: trạm xe buýt, trong xe buýt, trạm xăng, cửa hàng đêm, rừng, cắm trại, nhà, hành lang, tầng hầm...
- Ánh sáng thật (đèn đường, đèn trần, đèn pin, màn hình điện thoại), đèn chập chờn, mất điện, sương, mưa, nhiễu phim, VHS.
- Camera luôn chuyển động nhẹ; cảnh dài tự đổi góc máy giữa các câu để giữ mắt người xem.
- Cú hù: jumpscare (khuôn mặt, nụ cười, bóng đen, đôi mắt, bàn tay), stinger, glitch, tắt đèn, hiện dần.
- Cận cảnh: tin nhắn điện thoại, tờ giấy, danh sách luật, camera an ninh, ảnh polaroid, thẻ chương "NIGHT TWO".

ÂM THANH
- Giọng Kokoro có nhấn nhá: thì thầm, run sợ, hoảng loạn, chậm rãi, lạnh lùng... và hiệu ứng giọng: trầm có vang (Mr. Long),
  qua điện thoại, xa xăm, vọng, quỷ dị. Dấu "..." trong câu tạo nhịp ngừng kịch tính.
- 3 lớp: âm nền theo bối cảnh + nhạc theo cảm xúc (mood) + hiệu ứng. Nhạc tự nhỏ lại khi có lời,
  tự im bặt 0,5-1 giây trước jumpscare.
- Âm thanh tự tạo nên không lo bản quyền. Muốn hay hơn: bỏ file của bạn vào
    library\music\<mood>\    (calm_normal, uneasy, tension_rise, dread, chase, aftermath, host)
    library\ambience\rain.mp3, forest.mp3 ...
    library\sfx\knock.wav, hit.wav ...
  File của bạn luôn được ưu tiên. Chỉ dùng nhạc có giấy phép rõ ràng (YouTube Audio Library, Pixabay Music...).

NÂNG CẤP TOOL
- Mỗi lần xuất, tool tự ghi vấn đề vào notes\IMPROVEMENTS.md. Bạn ghi thêm nhận xét vào mục "Ghi chú của bạn".
- Khi muốn nâng cấp, bảo Claude: "đọc E:\HorrorStudio\notes\IMPROVEMENTS.md và nâng cấp tool".

KHI CÓ LỖI
- Chạy "debug (hien loi).bat" để mở app kèm cửa sổ hiện lỗi. Nhật ký: logs\app.log (gửi file này cho Claude).

CẤU HÌNH (config.json)
- kokoro_python / hf_home : nơi có Kokoro (mặc định E:\LocalTTS)
- narrator_voice / narrator_voice_female : giọng kể mặc định khi kịch bản không ghi
- music_volume, ambience_volume, sfx_volume : âm lượng các lớp
- auto_cuts   : tự đổi góc máy trong cảnh dài (true)
- encoder     : auto (dùng card NVIDIA nếu có), hoặc libx264
- workers     : số luồng dựng hình ("auto" hoặc 1-8)
- anthropic_api_key, claude_model : chỉ cần nếu dùng viết kịch bản tự động

Bản quyền font: Anton, Oswald, Creepster (SIL OFL 1.1), Special Elite (Apache 2.0). Đều dùng thương mại được.
