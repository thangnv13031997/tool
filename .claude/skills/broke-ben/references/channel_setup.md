# Broke Ben: bộ nhận diện và cài đặt kênh

> Trong skill này: các script nằm ở `scripts/`, chạy ở thư mục nào thì ảnh ra `branding/` và `demo/` ở thư mục đó.

Ngách: tài chính cá nhân bằng hoạt hình (Money Explained), tiếng Anh, khán giả Mỹ, Anh, Canada, Úc, 18–40 tuổi.
Linh vật: **Ben**, người que tóc nâu dựng, áo hoodie xanh lá. Ben vừa là người dẫn chuyện vừa là "người tiêu tiền sai" trong các tập truyện.

---

## 1. Tên kênh và handle

| Mục | Giá trị |
|---|---|
| Tên kênh | **Broke Ben** |
| Handle ưu tiên | `@BrokeBen` |
| Handle dự phòng | `@BrokeBenMoney`, `@BrokeBenExplains`, `@ItsBrokeBen` |
| Khẩu hiệu | *Money, explained before it's gone.* |

Lý do chọn tên này:
- Ngắn, dễ nhớ, có vần B–B.
- Nói trúng nỗi đau của người xem ("broke").
- Gắn với một nhân vật, nên kênh có cá tính riêng và không bị coi là "kênh AI vô danh".

Hướng phát triển lâu dài: hành trình "từ broke đến ổn". Tên vẫn dùng được khi kênh chuyển sang chủ đề đầu tư.

> Khi tạo kênh, vào YouTube Studio > Customization > Basic info để kiểm tra handle còn trống không.
> Lúc lập tài liệu này, tìm nhanh chưa thấy kênh nào tên "Broke Ben", nhưng chỉ YouTube mới xác nhận chắc chắn được.

---

## 2. Ảnh kênh (thư mục `branding/`)

| File | Tải lên ở đâu | Thông số |
|---|---|---|
| `avatar_800x800.png` | Customization > Branding > Picture | 800×800, hiển thị dạng tròn |
| `banner_2560x1440.jpg` | Customization > Branding > Banner image | 2560×1440, dưới 6 MB |
| `watermark_150x150.png` | Customization > Branding > Video watermark | 150×150; chọn "Display time: entire video" |
| `preview_banner_devices.jpg` | Không tải lên | Kiểm tra vùng cắt trên TV, máy tính, máy tính bảng, điện thoại |
| `preview_avatar_sizes.png` | Không tải lên | Kiểm tra avatar ở 176, 88, 36 px trên nền sáng và tối |

Tên kênh, khẩu hiệu và lịch đăng nằm gọn trong vùng an toàn 1546×423, nên điện thoại cũng hiển thị đủ.
Muốn đổi chữ thì sửa `NAME`, `TAGLINE`, `SCHEDULE` ở đầu `make_branding.py` rồi chạy:

```
python make_branding.py
```

### Quy chuẩn thương hiệu (tool video phải dùng đúng)

| Vai trò | Màu | Hex |
|---|---|---|
| Chữ chính, viền | Mực | `#1D212D` |
| Màu thương hiệu, tiền tăng | Xanh tiền | `#2E8B57` |
| Nền sáng | Kem | `#F6F1E6` |
| Nhấn mạnh, đồng xu | Vàng | `#FFC43D` |
| Mất tiền, cảnh báo | Đỏ | `#D64545` |

- Font: **Anton** cho tiêu đề và thumbnail, **Oswald** cho phụ đề và nhãn, **Special Elite** cho hóa đơn và giấy tờ. Đều có sẵn trong `assets/fonts`.
- Quy tắc màu: xanh = tiền vào, đỏ = tiền ra. Không bao giờ đảo ngược.

---

## 3. Mô tả kênh (dán vào Customization > Basic info > Description)

YouTube chỉ hiện khoảng 150 ký tự đầu ở nhiều chỗ, nên câu đầu phải nói rõ kênh làm gì.

```
Why are you always broke, even with a decent paycheck? Broke Ben explains money in simple animated stories.

Every video takes one money problem: credit cards, rent, car loans, budgeting, investing, inflation. We break it down with real math and clear pictures, in about ten minutes. No jargon. No get-rich-quick nonsense.

Meet Ben. He makes the money mistakes, so you don't have to.

New videos every Wednesday and Saturday.

What you'll find here:
• Why you're broke: the habits and traps that quietly drain your paycheck
• Money explained: compound interest, credit scores, index funds, taxes
• The math nobody shows you: renting vs buying, new vs used, 401(k) vs nothing
• Ben's stories: one bad money decision at a time

Everything on this channel is for education and entertainment only. It is not financial, tax, or legal advice. Talk to a licensed professional before making financial decisions.

Business inquiries: [your email]
```

---

## 4. Từ khóa kênh (Settings > Channel > Basic info > Keywords)

```
personal finance, money explained, why you're broke, budgeting, how to save money, compound interest, credit score, credit card debt, investing for beginners, index funds, financial literacy, money mistakes, animated finance, broke ben
```

---

## 5. Cài đặt kênh

| Mục | Chọn | Ghi chú |
|---|---|---|
| Country of residence | **Vietnam** | Phải ghi đúng nơi bạn sống. RPM tính theo nơi người xem ở, không theo quốc gia của kênh. |
| Audience | **No, set this channel as not made for kids** | Tài chính cho người lớn |
| Advanced features | **Bật**, xác minh số điện thoại | Mở khóa thumbnail tùy chỉnh, video dài hơn 15 phút, livestream |
| Bảo mật | Bật xác minh 2 bước cho tài khoản Google | Bắt buộc khi xin bật kiếm tiền |
| Loại tài khoản | Nên dùng **Brand Account** | Sau này thêm người quản lý được mà không cần chia sẻ mật khẩu |

---

## 6. Mặc định khi đăng video (Settings > Upload defaults)

| Mục | Giá trị |
|---|---|
| Category | **Education** |
| Video language | English |
| Caption certification | None (đã có phụ đề .srt từ tool) |
| License | Standard YouTube License |
| Comments | Allow all, hold potentially inappropriate for review |
| Altered or synthetic content | **No**: hoạt hình, không giả người hoặc sự việc có thật. Giọng TTS đọc lời nhân vật hoạt hình không thuộc diện phải khai báo. |
| Paid promotion | Chỉ tick khi có tài trợ |

Mẫu mô tả mặc định cho từng video:

```
{1–2 câu tóm tắt, câu đầu chứa từ khóa chính}

Chapters:
0:00 {tool tự điền}

📌 The numbers: {nguồn số liệu hoặc giả định tính toán, ví dụ "7% average yearly return, compounded annually"}

This video is for educational and entertainment purposes only and is not financial advice.

#personalfinance #moneytips #brokeben
```

---

## 7. Danh sách phát (tạo trước khi đăng video đầu)

1. **Why You're Broke**: thói quen và cái bẫy làm cạn tiền lương
2. **Money Explained**: các khái niệm (lãi kép, điểm tín dụng, quỹ chỉ số, thuế)
3. **The Math Nobody Shows You**: so sánh hai lựa chọn bằng con số
4. **The Money Traps**: chiêu trò của thẻ tín dụng, BNPL, đại lý xe, siêu thị
5. **Ben's Stories**: truyện có nhân vật, mỗi tập một bài học
6. **Shorts**: các đoạn cắt dọc

---

## 8. Trang chủ kênh (Customization > Layout)

- **Trailer cho người chưa đăng ký**: video 45–60 giây giới thiệu Ben (nên là video đầu tiên tool xuất ra).
- **Video nổi bật cho người đã đăng ký**: video mới nhất, hoặc video giữ chân tốt nhất.
- **Các mục**: Popular uploads → Why You're Broke → Money Explained → The Math Nobody Shows You → Shorts.

Gợi ý kịch bản trailer (khoảng 45 giây):
> "This is Ben. Ben makes three thousand dollars a month... and has thirty-three dollars left. Sound familiar?
> On this channel, we take one money problem at a time and show you the real math, with pictures.
> Ben makes the mistakes, so you don't have to. New videos every Wednesday and Saturday. Subscribe, and let's fix Ben's money."

---

## 9. Lịch đăng và giờ đăng

- **Thứ Tư và Thứ Bảy.** Tối thiểu 1 video dài mỗi tuần, cộng 2–3 Shorts cắt từ video dài.
- **Giờ đăng:** 9:00–11:00 sáng giờ miền Đông Mỹ, tức khoảng 20:00–22:00 giờ Việt Nam. Tài chính được xem nhiều vào buổi sáng và giờ nghỉ trưa ở Mỹ.
- **Điều kiện bật kiếm tiền:** 1.000 người đăng ký, cộng 4.000 giờ xem trong 12 tháng hoặc 10 triệu lượt xem Shorts trong 90 ngày. Kiểm tra lại con số trong YouTube Studio > Earn vì có thể thay đổi.

---

## 10. Checklist trước khi chuyển sang làm tool

- [ ] Tạo Brand Account, đặt tên **Broke Ben**, giữ handle
- [ ] Bật xác minh 2 bước, xác minh số điện thoại (advanced features)
- [ ] Tải avatar, banner, watermark lên
- [ ] Dán mô tả kênh, từ khóa, email liên hệ
- [ ] Cài Upload defaults theo mục 6
- [ ] Tạo 6 danh sách phát ở mục 7
- [ ] Chọn ngôn ngữ kênh: English; quốc gia: Vietnam
- [ ] Xong các bước trên thì bắt đầu làm tool **Money Studio**: dùng `flatkit.py` làm lõi vẽ, video đầu tiên là trailer.

---

## 11. Nhân vật bản 2 (đang chọn)

`make_branding_v2.py` dùng `charkit.py`: hình vẽ bằng đường cong mượt, đổ bóng hai tông, viền dán đều. Có hai phương án, mỗi phương án đủ avatar, banner, watermark và ảnh kiểm tra:

- `branding/option_A_ben/`: Ben dáng chibi, áo hoodie xanh
- `branding/option_B_piggy/`: Piggy Ben, heo đất bị nứt dán băng cá nhân (đúng chữ "broke")
- `branding/COMPARE_v2.jpg`: hai phương án đặt cạnh nhau

Các file ở thư mục gốc `branding/` là bản 1 (người que), giữ lại để so sánh.
