# Báo cáo kiểm tra F1

## CR-01 ISBN-13 — đã duyệt và triển khai

Trạng thái phê duyệt theo xác nhận trực tiếp của người dùng trong yêu cầu triển khai CR-01. Không commit, push hoặc deploy; tiếp tục trên toàn bộ code Release 1.0 đang có tại máy, không quay về commit F1.

### Kết quả kiểm thử mới nhất

```text
135 passed in 51.40s
```

Chạy toàn bộ `tests/` bằng Python trong `.venv`, `--basetemp` mới dưới `.test-tmp/`, `-p no:cacheprovider`; mã thoát 0, CSRF bật, không cảnh báo hoặc test bỏ qua. Gồm toàn bộ F1–F5, giá VND/16 sách thật và CR-01.

Test ISBN bao gồm thiếu/rỗng, 12/14 ký tự, chữ, chữ số Unicode/gạch nối/khoảng trắng; trùng mã kể cả sách ẩn; sửa giữ nguyên mã của chính sách; form required/pattern; hiển thị ISBN/nhãn demo; tìm ISBN kết hợp thể loại/giá/phân trang/quay lại; ràng buộc SQLite NOT NULL/UNIQUE/CHECK (kể cả BLOB và chuỗi chứa NUL); seed lặp không đổi ISBN. Test migration dùng 52 sách cũ, xác minh backup còn schema cũ, giữ mọi cột dữ liệu cũ, tài khoản, index riêng, sequence ID và SQLite integrity; chạy migration lần hai giữ nguyên.

### Nâng cấp database cục bộ thực tế

- Tệp backup trước migration thành công: `instance/backups/before-cr01-4b186025246d427183f7f7dd07eb5917.sqlite3`, chỉ cục bộ và được Git bỏ qua.
- Trước/sau: **52 sách**. Mọi cột cũ của `books`, mọi bản ghi `users`, `authors`, `genres` và sequence ID đã đối chiếu giống nhau; `.env` có SHA-256 trước/sau giống nhau. Giá vẫn lưu đơn vị 1/100 VND. `foreign_key_check` không có lỗi; `integrity_check` trả `ok`.
- Cấp 52 mã dạng TEXT, đúng 13 chữ số, không trùng, tất cả `isbn_is_demo=1`. Chưa xác minh đủ thông tin ấn bản của 16 sách thật; **không gắn ISBN thật theo suy đoán**. Mã demo dùng prefix `000`, giao diện ghi rõ **Demo code — not a verified edition ISBN**. SQLite và server buộc mã prefix `000` phải có cờ demo.
- Chạy lại `upgrade-db`: không đổi mã/dữ liệu. Chạy `seed-books` và `seed-real-books` mỗi lệnh hai lần: cả bốn lần đều `Inserted 0`; toàn bộ 52 bản ghi sau đó giống ngay sau migration.
- Lần CLI đầu gặp lỗi mã hóa Windows `cp1258` khi in đường dẫn backup có tiếng Việt; lỗi xảy ra sau backup nhưng trước khi ghi schema, database cũ còn nguyên. Đã sửa thông báo in đường dẫn tương đối ASCII và thêm regression test thực thi CLI trong đường dẫn tiếng Việt với `PYTHONIOENCODING=cp1258`. Lần chạy lại thành công như trên.

### HTTP thực tế và giới hạn

Khởi động lại Flask tại `http://127.0.0.1:5000`, debug tắt. HTTP 200 và nội dung đúng cho tìm mã demo Bitcoin `0000000000037` kết hợp thể loại + min=max=464550, trang chi tiết hiển thị mã và nhãn demo, quay lại giữ toàn bộ tham số. Lọc max=464549 không có Bitcoin; `/books?q=000&page=2` có 12 sách. Tìm tên/tác giả vẫn hoạt động; catalogue có 52 sách; giá Bitcoin `464.550 ₫`, Demo 36 `230.000 ₫` giữ đúng định dạng.

Form và quyền Admin được kiểm tra bằng Flask test client với tài khoản test trong SQLite riêng; không sửa tài khoản thật. Không thực hiện QA trực quan bằng trình duyệt mới. CR này kiểm tra đúng 13 chữ số và tính duy nhất theo yêu cầu; không xác minh checksum/ấn bản tự động. Các phần dưới đây là lịch sử trước CR-01 và không thay thế kết quả mới nhất phía trên.

## Bổ sung 16 đầu sách thật và định dạng VND (lịch sử trước CR-01)

- Đọc schema và xác minh `price_cents` lưu VND × 100. Thêm lệnh riêng `seed-real-books`, không sửa lệnh tạo 36 sách mẫu. Giá tham khảo theo dữ liệu người dùng cung cấp; mô tả tiếng Anh ngắn, tồn kho demo 10, bìa SVG mặc định do workspace không có bìa riêng phù hợp. Không thêm ISBN.
- Sao lưu SQLite trước khi seed tại `instance/backups/before-real-books-868c56d971bd4d1aaf73a0b7c4b63479.sqlite3` (chỉ cục bộ, Git bỏ qua). Ban đầu 36 sách; lần seed 1 thêm 16, tổng 52; lần seed 2 thêm 0, tổng 52. Đối chiếu toàn bộ các bản ghi cũ trong `users`, `books`, `authors`, `genres` không đổi; SHA-256 `.env` trước/sau không đổi; SQLite integrity `ok`.
- Bộ lọc `money` dùng chung hiển thị `230.000 ₫` và `464.550 ₫` trên catalogue, chi tiết và bảng Admin. Không thay đổi dữ liệu giá hay logic lọc. Nếu giá cũ có phần lẻ, giữ chính xác, ví dụ `125.000,50 ₫`, không làm tròn mất dữ liệu.
- Chạy lại toàn bộ pytest với SQLite tạm, CSRF bật, cacheprovider tắt: **114 passed in 44.64s**, không cảnh báo/test bỏ qua. Test mới kiểm tra đủ 16 mức giá, seed lặp, giữ sách đã sửa/ẩn, bỏ qua sách nhập tay, tái sử dụng tác giả/thể loại, định dạng trên cả 3 nơi, ô nhập dạng số và biên lọc giá.
- Khởi động lại Flask tại `127.0.0.1:5000`. HTTP thực tế xác nhận cả danh sách và chi tiết của Bookstore Demo 36 là `230.000 ₫`, Bitcoin Is for Everyone là `464.550 ₫`. Catalogue báo 52 sách; tìm Michele Cagan trả 2 sách; tìm Bitcoin kết hợp min=max=464550 có sách, max=464549 không có; ô lọc giữ giá trị `464550`.
- Bảng Admin và ô sửa giá được kiểm tra bằng Flask test client với đăng nhập Admin trong database test riêng, không đăng nhập hoặc sửa tài khoản thật. Không thực hiện kiểm tra trực quan trình duyệt mới. Không commit/push.

## Release 1.0 — F1–F5, ngày 2026-11-09

Trạng thái trước khi sửa: `main` ở commit `55167a1`, working tree sạch; code cục bộ chỉ có F1. Không tìm thấy hồ sơ phê duyệt CR-01, nên ISBN giữ trạng thái chờ duyệt. Giữ Flask, SQLite, Jinja2, Bootstrap và code F1 hiện có.

### Kiểm thử tự động thực tế

Chạy toàn bộ `tests/` với `.venv/Scripts/python.exe`, một thư mục `--basetemp` mới trong `.test-tmp/` và `-p no:cacheprovider`, CSRF vẫn bật:

```text
104 passed in 41.55s
```

Gồm 40 test F1 cũ và 64 trường hợp mới. Test F2–F5 kiểm tra quyền GET/POST cho khách và Customer, Admin hợp lệ, CSRF thiếu/sai, tạo/sửa/ẩn/khôi phục sách, giá/tồn kho sai, tác giả/thể loại không tồn tại, URL bìa không an toàn, quản lý tác giả/thể loại, phân trang/mới nhất trước, sách ẩn/ID thiếu trả 404, tìm Unicode/tên tác giả, escape LIKE và HTML, lọc kết hợp, trang tiếp giữ bộ lọc và quay lại đúng danh sách. Kiểm tra thêm seed lặp không trùng/không ghi đè, nâng cấp database F1 cũ giữ nguyên mọi cột tài khoản, foreign keys và CHECK giá/tồn kho.

Lần chạy đầu có `1 failed, 103 passed in 41.12s`: công thức kỳ vọng ID trong test phân trang viết sai. Đã sửa kỳ vọng test; ứng dụng vốn trả đúng thứ tự 36 xuống 25 ở trang đầu. Kết quả 104 đạt phía trên là lần chạy lại toàn bộ sau sửa, mã thoát 0, không cảnh báo hoặc test bỏ qua.

### Database thật và bảo toàn dữ liệu

- Sao lưu bằng SQLite backup API trước khi nâng cấp tại `instance/backups/pre-release1-bbcbe19356c6458c92bd9373c768d982.sqlite3`. Bản sao chỉ lưu cục bộ, được `.gitignore` bỏ qua.
- `upgrade-db` tạo bảng/index còn thiếu. Đối chiếu toàn bộ bản ghi `users` và cấu trúc bảng trước/sau giống nhau; không tạo hay đổi tài khoản/mật khẩu thật. SHA-256 nội dung `.env` trước/sau giống nhau; không ghi đè `.env`.
- `seed-books`: lần đầu `Inserted 36 demo books`, lần hai `Inserted 0 demo books`; database thực tế có 36 sách sau bước chuẩn bị. `PRAGMA integrity_check` trả `ok`.
- Không xóa database, cache hoặc các thư mục test cũ. Dữ liệu phát sinh trong test/benchmark dùng SQLite riêng trong `.test-tmp/`.

### Kiểm tra HTTP và giao diện

Flask chạy tại `127.0.0.1:5000`, debug tắt. Kiểm tra HTTP thực tế bằng Python urllib:

- `/`, `/books`, `/books?page=2`, `/books?page=3`, `/books/36?page=2&q=Bookstore`, `/login`, `/register`: HTTP 200.
- `/books/999999`: HTTP 404; `/books?min_price=2&max_price=1`: HTTP 400; kết quả rỗng `/books?min_price=999999999`: HTTP 200.
- `/static/cover.svg`, `/static/forms.js`, `/static/style.css`: HTTP 200.

Công cụ trình duyệt đã được thử nhưng kernel thoát với lỗi `windows sandbox failed: orchestrator_helper_exit_nonzero`. **Chưa kiểm tra trực quan bằng trình duyệt** trên desktop/tablet/điện thoại; chưa xác minh giao diện thực tế, tải CDN/ảnh ngoài, fallback ảnh hoặc validation HTML/JavaScript bằng thao tác trình duyệt. Mã có viewport, lưới Bootstrap 1/2/3/4 cột và CSS cho ảnh/văn bản dài, nhưng đó không phải bằng chứng QA giao diện. Các bước kiểm tra thủ công có trong [DEMO.md](DEMO.md).

### Phép đo catalogue có 36 sách

Chạy `scripts/measure_catalog.py`: SQLite mới riêng, 36 sách, 12 thẻ/trang, người chưa đăng nhập; Flask test client, một tiến trình, 100 GET tuần tự `/books`, không tải mạng/tài nguyên ngoài. Môi trường Windows 11 `10.0.26200`, Python 3.12.10, Flask 3.1.3, SQLite 3.49.1, bộ xử lý báo `Intel64 Family 6 Model 191 Stepping 2, GenuineIntel`.

| Phép đo | Thời gian |
| --- | ---: |
| Yêu cầu đầu, có biên dịch template | 17,245 ms |
| Trung vị 100 yêu cầu tiếp | 1,260 ms |
| p95 | 1,530 ms |
| Lớn nhất trong 100 yêu cầu | 1,951 ms |

Đây là thời gian xử lý/kết xuất server, dưới mốc 2.000 ms trong môi trường đo. **Chưa đủ để xác nhận yêu cầu tải trang đầu cuối dưới 2 giây**, vì chưa đo mạng, Bootstrap CDN, ảnh ngoài, trình duyệt hoặc tải đồng thời. Có thể chạy lại script theo README; đầu ra JSON lưu cục bộ trong `.test-tmp/benchmark-*/result.json`.

Không push, tạo tag hoặc deploy Release 1.0. Các phần dưới đây là lịch sử kiểm tra F1, không phải kết quả hiện tại.

## Lần kiểm tra lại theo yêu cầu (lịch sử F1)

### Chạy với thư mục tạm riêng sau lỗi quyền truy cập

Người dùng báo lần chạy trong Terminal gặp `PermissionError: [WinError 5] Access is denied` tại `Temp/pytest-of-ben10`, không ghi được `.pytest_cache`, với 2 cảnh báo và 40 lỗi. Đây là kết quả người dùng cung cấp; không phải kết quả của lần chạy mới dưới đây.

Đã chạy lại trong PowerShell thông thường, không yêu cầu Administrator. Tạo thư mục mới dành riêng cho test và xác nhận quyền ghi bằng tệp `write-check.txt`. Thư mục thực tế của lần chạy:

```text
.test-tmp/run-c75d26eb8a4b45d7b40edbffdb27ada3/temp
```

Lệnh chạy toàn bộ kiểm thử, với `$bookstoreTestTemp` trỏ tới thư mục trên:

```powershell
.\.venv\Scripts\python.exe -m pytest -q tests --basetemp "$bookstoreTestTemp" -p no:cacheprovider
```

Kết quả thực tế mới nhất, mã thoát 0:

```text
40 passed in 15.18s
```

Không có lỗi, cảnh báo hoặc test bị bỏ qua trong lần chạy này. Không sửa mã nguồn ứng dụng hoặc các test, không tắt CSRF. Fixture vẫn sử dụng SQLite tạm dưới `tmp_path`. Không chạy lệnh xóa dữ liệu, sửa quyền truy cập, thay đổi tài khoản hoặc ghi đè `.env`.

`cacheprovider` được tắt nên pytest không ghi vào `.pytest_cache`. Không dùng thư mục `Temp/pytest-of-ben10` cũ. `.test-tmp/` đã được thêm vào `.gitignore`; hướng dẫn trong README tạo đường dẫn mới mỗi lần chạy. Chỉ truyền thư mục `temp` dành riêng cho kiểm thử vào `--basetemp`, vì pytest có thể xóa nội dung đường dẫn này.

Lần chạy thành công xác nhận cách chạy bằng thư mục tạm riêng hoạt động trong môi trường hiện tại. Chưa sửa hoặc xác minh lại quyền truy cập tại thư mục Temp và `.pytest_cache` cũ.

### Đối chiếu server và chỉnh trang chủ

- Đã đối chiếu thư mục làm việc và cấu hình `DATABASE` của tiến trình Flask đang phục vụ cổng 5000 với cấu hình CLI. Cả hai cùng dùng `instance/bookstore.sqlite3` trong workspace.
- Tại thời điểm kiểm tra này: có 1 tài khoản, chưa có Admin. Không xuất thông tin tài khoản cá nhân, mật khẩu, password hash hoặc khóa bí mật.
- Đã sửa trang chủ theo trạng thái đăng nhập và thay nội dung về mua sắm bằng `book catalogue`.
- Chạy lại toàn bộ F1: `40 passed in 11.93s`.
- Kiểm tra kết xuất trang chủ bằng Flask test client cho khách và người đã đăng nhập đều đạt; không thay đổi tài khoản trong database.
- Đã khởi động lại server và xác minh trang chủ thực tế trả HTTP 200 với nội dung mới. Không ghi đè `.env` hoặc xóa dữ liệu.
- Chưa thực hiện thay người dùng các bước demo thủ công trên trình duyệt.

### Lần chạy trước khi chỉnh trang chủ

Chạy lại trên cấu trúc dự án hiện có bằng `.\.venv\Scripts\python.exe -m pytest -q`.

```text
40 passed in 12.37s
```

Không có kiểm thử thất bại nên không cần sửa mã nguồn. `pip check` trả về `No broken requirements found.`. Giữ nguyên `.env` và các tài khoản hiện có. Kiểm tra database ở chế độ chỉ đọc ghi nhận 0 tài khoản và 0 Admin. Chưa tạo Admin vì người dùng cần tự nhập mật khẩu ẩn qua lệnh `create-admin`.

Ứng dụng đã được khởi động lại tại http://127.0.0.1:5000. Kiểm tra HTTP thực tế với `/`, `/login` và `/register` đều trả về 200. Máy chủ được giữ chạy để người dùng truy cập. Các phần bên dưới ghi lại lần triển khai trước đó.

## Ghi nhận từ lần triển khai trước

Ngày thực hiện: 2026-10-30. Môi trường: Windows PowerShell, Python 3.12.10.

## Kiểm tra tự động

Lệnh chạy kiểm thử cuối cùng trong lần triển khai:

```powershell
.\.venv\Scripts\python.exe -m pytest -q
```

Kết quả thực tế:

```text
40 passed in 15.68s
```

Tức là 40 kiểm thử đạt, thời gian chạy 15,68 giây. Đây là kết quả đã ghi nhận trong lần triển khai, không phải kết quả của một lần chạy mới khi dịch tài liệu.

CSRF vẫn được bật trong suốt quá trình kiểm thử. Các kiểm thử sử dụng database tạm, tách biệt với database của ứng dụng cục bộ. Lần chạy đầu phát hiện các lệnh CLI thiếu Flask application context (38 kiểm thử đạt, 1 kiểm thử thất bại). Lỗi được sửa bằng `with_appcontext`. Một lần chạy toàn bộ sau đó đã đạt, rồi bổ sung thêm kiểm thử ngăn người chưa đăng nhập thay đổi dữ liệu. Kết quả phía trên là của lần chạy toàn bộ cuối cùng.

Các kiểm tra khác đã thực hiện:

- `python -m pip check`: trả về `No broken requirements found.`, tức không phát hiện xung đột phụ thuộc.
- `python -m compileall -q bookstore tests`: hoàn thành với mã thoát 0.
- Máy chủ Flask cục bộ đã khởi động tại `127.0.0.1:5000`, với chế độ debug tắt.
- Các yêu cầu HTTP đến `/`, `/register`, `/login`, `/static/style.css` và `/static/forms.js` đều trả về mã 200.
- `init-db` đã tạo database cục bộ. Máy chủ đã được dừng sau khi kiểm tra HTTP.

Các thư viện phụ thuộc trực tiếp đã dùng khi kiểm thử: Flask 3.1.3, Flask-WTF 1.3.0, python-dotenv 1.2.4 và pytest 9.2.0.

## Những phần chưa xác minh

Công cụ trình duyệt trả về lỗi `The browser access host is unavailable` (không truy cập được dịch vụ điều khiển trình duyệt). Vì vậy, chưa kiểm tra trực quan giao diện desktop, điện thoại, tablet hoặc kiểm tra dữ liệu ngay trên trình duyệt. Các trang có lớp Bootstrap hỗ trợ nhiều kích thước màn hình, thẻ viewport, CSS cục bộ, ràng buộc nhập liệu HTML và script xác nhận mật khẩu; các thành phần này chưa phải bằng chứng kiểm tra trực quan.

Chưa kiểm tra triển khai thực tế lên máy chủ production, HTTPS, tải hệ thống hoặc nhiều yêu cầu đồng thời. Quy tắc bảo vệ Admin cuối cùng sử dụng giao dịch ghi SQLite để tuần tự hóa thao tác. Kiểm thử tự động đã kiểm tra quy tắc này nhưng chưa mô phỏng các yêu cầu chạy đồng thời.

Workspace ban đầu trống và chưa phải kho Git. Không tạo commit. Không ghi nhận hoặc tự đặt số giờ làm việc hay kết quả demo thủ công. Không tạo hoặc lưu thông tin đăng nhập Admin thật. `.venv` và database ứng dụng chưa có tài khoản được `.gitignore` loại trừ khỏi Git.
