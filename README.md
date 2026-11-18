# Team 1 Bookstore — Release 1.0

Đồ án môn Quản lý dự án phần mềm HK261, tiếp tục từ F1 Sprint 1 ở commit `55167a1`.

Nhóm 1: Ngo Khai Luan và Nguyen Thanh Son.

## Phạm vi

F1 gồm đăng ký Customer, đăng nhập/đăng xuất, thông tin và quản lý tài khoản Admin. F2 bổ sung thêm/sửa/ẩn sách, quản lý tác giả/thể loại. F3 cung cấp danh sách công khai 12 sách/trang, mới nhất trước. F4 có chi tiết, 404 cho sách ẩn/không tồn tại và quay lại đúng danh sách. F5 tìm tên sách/tác giả, lọc thể loại và giá kết hợp phân trang. Không có giỏ hàng, thanh toán hoặc đăng nhập mạng xã hội.

CR-01 (ISBN-13) **đã được duyệt theo xác nhận của người dùng** và đã triển khai: ISBN bắt buộc, đúng 13 chữ số, duy nhất, có trên form Admin, chi tiết và tìm kiếm. Xem [release notes](docs/RELEASE_NOTES.md).

Ứng dụng sử dụng Python, Flask, SQLite, Jinja2 và Bootstrap 5. Dùng Python 3.12 trở lên.

## Nâng cấp từ F1 trên máy đã cài

Giữ nguyên `.env`, database và tài khoản. Không chạy lại `Copy-Item .env.example .env` trên máy đã cấu hình. `upgrade-db` tạo bảng/index còn thiếu và nâng cấp ISBN cho bảng sách cũ; `init-db` dùng cùng migration. Dừng server trước khi nâng cấp. Migration tự sao lưu database cũ trong thư mục `backups/` cạnh tệp SQLite trước khi ghi schema (mặc định `instance/backups/before-cr01-*.sqlite3`).

Database cục bộ đã được sao lưu trước khi nâng cấp trong lần thực hiện Release 1.0. Với những lần nâng cấp sau, dừng server bằng Ctrl+C và tạo bản sao SQLite nhất quán trước khi nâng cấp. Đoạn lệnh này đọc đúng cấu hình `DATABASE` đang dùng; bản sao ở `instance/backups/` được Git bỏ qua:

```powershell
Set-Location 'D:\nam4hocky1\Quản lý dự án phần mềm\HK261_Bookstore_Team1'
.\.venv\Scripts\python.exe -c "from bookstore import create_app; from pathlib import Path; import sqlite3, uuid; app=create_app(); folder=Path('instance/backups'); folder.mkdir(parents=True,exist_ok=True); source=sqlite3.connect(Path(app.config['DATABASE']).resolve().as_uri()+'?mode=ro',uri=True); target=sqlite3.connect(folder/('before-upgrade-'+uuid.uuid4().hex+'.sqlite3')); source.backup(target); target.close(); source.close(); print('Backup complete')"
if ($LASTEXITCODE -ne 0) { throw 'Backup failed' }
.\.venv\Scripts\python.exe -m flask --app bookstore upgrade-db
if ($LASTEXITCODE -ne 0) { throw 'Upgrade failed' }
.\.venv\Scripts\python.exe -m flask --app bookstore seed-books
if ($LASTEXITCODE -ne 0) { throw 'Seed failed' }
.\.venv\Scripts\python.exe -m flask --app bookstore run --host 127.0.0.1 --port 5000
```

Mở http://127.0.0.1:5000/books để xem sách mà không cần đăng nhập. Nếu đã có Admin, dùng tài khoản cũ. Nếu chưa có, chạy `create-admin` theo hướng dẫn bên dưới. Không có tài khoản hay mật khẩu mặc định.

`seed-books` thêm 36 sách demo, 6 tác giả và 4 thể loại khi database chưa có dữ liệu mẫu. Khóa `demo_key` duy nhất giúp chạy lại không tạo sách trùng; tên tác giả/thể loại cũng duy nhất. Lệnh không ghi đè nội dung, tồn kho hoặc trạng thái ẩn của sách mẫu đã sửa. Giá demo từ 55.000 đến 230.000 VND. Bìa mẫu dùng SVG đi kèm, không cần tải ảnh ngoài. Cài mới xong cũng có thể chạy `seed-books` trước khi mở web.

## Thêm 16 đầu sách thật (tùy chọn)

Để thêm 16 đầu sách thật vào database đã nâng cấp, chạy lệnh riêng sau. Lệnh này giữ nguyên 36 sách mẫu và các sách/tài khoản đã sửa:

```powershell
.\.venv\Scripts\python.exe -m flask --app bookstore seed-real-books
```

Danh mục gồm 16 đầu sách theo danh sách tham khảo được cung cấp, có mô tả tiếng Anh, tồn kho demo 10 cuốn/sách và bìa mặc định (workspace chưa có bìa riêng phù hợp). Giá là giá tham khảo VND, không phải giá thị trường cập nhật. Lệnh tái sử dụng tác giả/thể loại theo tên, bỏ qua sách có khóa seed hoặc cùng tên + tác giả; không ghi đè dữ liệu. Với database ban đầu chỉ có 36 sách mẫu, lần đầu thêm 16 (tổng 52), lần sau thêm 0. Chưa xác minh đúng ấn bản của 16 sách: lệnh chỉ cấp **mã ISBN demo**, có cờ và nhãn rõ ràng, không coi là ISBN thật.

## CR-01: nâng cấp ISBN trên Windows

Tại thư mục project, dừng Flask cũ bằng Ctrl+C, rồi chạy trong PowerShell:

```powershell
.\.venv\Scripts\python.exe -m flask --app bookstore upgrade-db
if ($LASTEXITCODE -ne 0) { throw 'ISBN migration failed; do not start server' }
.\.venv\Scripts\python.exe -m flask --app bookstore seed-books
if ($LASTEXITCODE -ne 0) { throw 'Demo seed failed' }
.\.venv\Scripts\python.exe -m flask --app bookstore seed-real-books
if ($LASTEXITCODE -ne 0) { throw 'Real-title seed failed' }
.\.venv\Scripts\python.exe -m flask --app bookstore run --host 127.0.0.1 --port 5000
```

- Migration sao lưu trước, sao chép toàn bộ sách cũ vào bảng mới có ISBN đầy đủ rồi mới chuyển bảng trong một giao dịch. ID, giá `price_cents`, tài khoản và mọi cột sách cũ được giữ; không ghi `.env`. Ràng buộc được kiểm tra trước khi commit; lỗi thì rollback. Chạy lại migration không đổi ISBN đã cấp.
- Mọi sách cũ chưa có ISBN, kể cả 16 đầu sách thật chưa xác minh đúng ấn bản, được cấp mã 13 chữ số bắt đầu bằng `000` và `isbn_is_demo=1`. Đây là **mã demo**, không phải mã ISBN được xác nhận/cấp cho ấn bản. Trang chi tiết hiển thị nhãn **Demo code — not a verified edition ISBN**. Cả hai seed cũng tạo mã demo duy nhất, không ghi đè ISBN hoặc dữ liệu sách đã có.
- Admin phải nhập ISBN khi thêm/sửa: chuỗi đúng 13 chữ số ASCII `0–9`, không dấu cách/gạch nối. UNIQUE áp dụng cho cả sách ẩn. Có kiểm tra `required`/`pattern` trên form, kiểm tra server và `NOT NULL`/`UNIQUE`/`CHECK` tại SQLite. Phạm vi CR kiểm tra 13 chữ số, không xác minh checksum hay ấn bản tự động.
- Khi đã xác minh đúng ấn bản, Admin thay mã demo bằng ISBN thật và bỏ chọn **Demo code**. Mã bắt đầu bằng `000` luôn bị đánh dấu demo ở server và database, kể cả khi bỏ chọn ô này.
- Tìm tại `/books` bằng ISBN đầy đủ hoặc một phần trong cùng ô tìm tên/tác giả; thể loại, khoảng giá, phân trang và nút quay lại vẫn kết hợp như trước. Giá VND giữ nguyên đơn vị và cách định dạng.

Giá hiển thị chung ở catalogue, chi tiết và bảng Admin: `230.000 ₫`, `464.550 ₫`. Không hiện phần `,00`; nếu dữ liệu cũ có phần lẻ thì giữ phần lẻ, ví dụ `125.000,50 ₫`. SQLite vẫn lưu `price_cents` = VND × 100; ô nhập và lọc dùng số chưa định dạng như `230000`, không nhập dấu phân cách hàng nghìn hoặc ký hiệu tiền.

## Cài mới trên Windows PowerShell (chỉ khi chưa có `.env`)

Chạy các lệnh sau trong thư mục dự án. Không cần kích hoạt môi trường ảo nên không cần thay đổi chính sách chạy script của PowerShell.

```powershell
Set-Location 'D:\nam4hocky1\Quản lý dự án phần mềm\HK261_Bookstore_Team1'
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
Copy-Item .env.example .env
$bookstoreSecret = & .\.venv\Scripts\python.exe -c "import secrets; print(secrets.token_hex(32))"
(Get-Content .env) -replace '^SECRET_KEY=$', "SECRET_KEY=$bookstoreSecret" | Set-Content -Encoding utf8 .env
Remove-Variable bookstoreSecret
.\.venv\Scripts\python.exe -m flask --app bookstore init-db
.\.venv\Scripts\python.exe -m flask --app bookstore create-admin
.\.venv\Scripts\python.exe -m flask --app bookstore run --host 127.0.0.1 --port 5000
```

Mở http://127.0.0.1:5000 trên trình duyệt. Nhấn Ctrl+C để dừng máy chủ.

Chỉ thực hiện phần cài đặt lần đầu một lần. Không ghi đè nếu đã có tệp `.env`. Giữ nguyên khóa bí mật giữa các lần chạy. Những lần sau chỉ cần chạy:

```powershell
.\.venv\Scripts\python.exe -m flask --app bookstore run --host 127.0.0.1 --port 5000
```

Nếu không tìm thấy `python`, hãy cài Python và chọn tùy chọn thêm Python vào PATH. Dùng `python` vì trình khởi chạy `py` trên Windows có thể trỏ đến một bản cài đặt khác.

## Tạo Admin đầu tiên

Lệnh `create-admin` yêu cầu nhập tên, email và mật khẩu. Mật khẩu không hiển thị khi nhập và phải nhập hai lần để xác nhận. Dùng mật khẩu dài từ 12 đến 128 ký tự. Dự án không cung cấp sẵn tài khoản hoặc mật khẩu Admin mặc định. Không truyền mật khẩu qua tùy chọn dòng lệnh hoặc lưu mật khẩu vào Git.

Chạy `init-db` trước `create-admin`. Lệnh này tạo các bảng còn thiếu và giữ lại tài khoản đã có. Các lệnh CLI sử dụng cùng cấu hình database và khóa bí mật với ứng dụng web.

## Cấu hình

Sao chép `.env.example` thành `.env` và đặt `SECRET_KEY` ngẫu nhiên. Biến môi trường hệ thống được ưu tiên hơn giá trị trong `.env`.

| Biến | Mục đích |
| --- | --- |
| `SECRET_KEY` | Khóa bắt buộc để ký phiên đăng nhập và token CSRF. Cần giữ bí mật. |
| `DATABASE` | Đường dẫn tệp SQLite, không bắt buộc. Mặc định: `instance/bookstore.sqlite3`. |
| `SESSION_COOKIE_SECURE` | Mặc định `false` cho HTTP trên máy cá nhân. Đặt `true` khi dùng HTTPS. |

Ứng dụng báo lỗi khi khởi động nếu chưa đặt khóa bí mật. `.gitignore` loại trừ database cục bộ, `.env`, môi trường ảo và bộ nhớ đệm Python khỏi Git. Khóa và mật khẩu trong `tests/` chỉ là dữ liệu kiểm thử.

## Quy tắc bảo mật và tài khoản

- Đăng ký công khai luôn tạo Customer, kể cả khi yêu cầu gửi lên có vai trò Admin.
- Werkzeug lưu mật khẩu dưới dạng băm bằng scrypt. Không lưu mật khẩu dạng văn bản gốc.
- Mọi đường dẫn dành cho Admin đều kiểm tra vai trò hiện tại trong database tại server.
- Mỗi yêu cầu kiểm tra trạng thái tài khoản và phiên bản phiên đăng nhập. Khóa tài khoản làm mất hiệu lực tất cả phiên của tài khoản đó. Sau khi mở khóa, người dùng phải đăng nhập lại.
- Mọi thao tác thay đổi dữ liệu đều dùng POST và token CSRF của Flask-WTF. Đăng xuất cũng dùng POST.
- Thay đổi vai trò có hiệu lực từ yêu cầu tiếp theo, kể cả với phiên đã đăng nhập.
- Giao dịch ghi SQLite ngăn việc khóa hoặc hạ quyền Admin hoạt động cuối cùng. Admin bị khóa không được tính là Admin đang hoạt động.
- Email được xóa khoảng trắng ở hai đầu, lưu bằng chữ thường và kiểm tra trùng không phân biệt chữ hoa, chữ thường.
- Ràng buộc HTML và JavaScript kiểm tra dữ liệu trên trình duyệt. Server kiểm tra lại dữ liệu. Jinja mã hóa các ký tự HTML đặc biệt trong nội dung tài khoản trước khi hiển thị.
- Cookie phiên sử dụng HttpOnly và SameSite=Lax. Bật thuộc tính Secure khi dùng HTTPS.

## Cấu trúc dự án

```text
bookstore/
  __init__.py         Tạo ứng dụng, cấu hình và CSRF
  db.py               Kết nối database, cấu trúc bảng và lệnh khởi tạo
  auth.py             Đăng ký, phiên đăng nhập và bảo vệ đường dẫn
  admin.py            Quản lý tài khoản và quy tắc Admin cuối cùng
  catalog.py          Catalogue công khai, quản trị sách và lệnh tạo mẫu
  templates/          Các trang Jinja
  static/             CSS và kiểm tra biểu mẫu
tests/                Kiểm thử tích hợp F1–F5
scripts/measure_catalog.py  Đo thời gian server với SQLite riêng
docs/DEMO.md          Hướng dẫn demo Release 1.0
```

Catalogue dùng blueprint `bookstore/catalog.py`; các trang ở `bookstore/templates/catalog/`. Release này chưa có chức năng mua hàng.

## Kiểm thử

Chạy trong PowerShell thông thường, không cần Administrator. Mỗi lần chạy tạo một thư mục mới trong `.test-tmp/` của dự án, tránh dùng thư mục Temp mặc định đang bị lỗi quyền truy cập. Tắt `cacheprovider` để pytest không ghi vào `.pytest_cache`.

```powershell
$bookstoreTestRun = Join-Path (Get-Location).Path ('.test-tmp\run-' + [guid]::NewGuid().ToString('N'))
New-Item -ItemType Directory -Path $bookstoreTestRun -ErrorAction Stop | Out-Null
[System.IO.File]::WriteAllText((Join-Path $bookstoreTestRun 'write-check.txt'), 'temporary test data')
$bookstoreTestTemp = Join-Path $bookstoreTestRun 'temp'
.\.venv\Scripts\python.exe -m pytest -q tests --basetemp "$bookstoreTestTemp" -p no:cacheprovider
```

Lệnh tạo thư mục và tệp `write-check.txt` giúp xác nhận quyền ghi trước khi chạy. Nếu chúng báo lỗi, dừng lại và không chạy lệnh pytest tiếp theo. Chạy lại toàn bộ đoạn lệnh để có thư mục mới cho lần sau. `.test-tmp/` được loại trừ khỏi Git.

**Lưu ý:** pytest có thể xóa nội dung đường dẫn được truyền cho `--basetemp`. Chỉ dùng thư mục `temp` riêng vừa tạo cho test như trên. Không đặt `--basetemp` thành thư mục dự án, `instance`, thư mục chứa database, `.env` hoặc dữ liệu cá nhân. Không cần xóa hay sửa quyền thư mục Temp cũ và `.pytest_cache`.

Các kiểm thử sử dụng SQLite tạm và vẫn bật CSRF. Toàn bộ F1 được giữ lại; `tests/test_catalog.py` bổ sung F2–F5, nâng cấp schema cũ giữ tài khoản, tạo mẫu lặp lại an toàn và ràng buộc database. Kết quả thật trong [docs/VALIDATION.md](docs/VALIDATION.md).

## Sử dụng catalogue và quản trị sách

- Công khai: `/books`; bấm thẻ sách để mở chi tiết. **Back to books** giữ `q`, `genre`, `min_price`, `max_price`, `page`. **Find** bắt đầu lại ở trang 1. Tìm không phân biệt hoa thường Unicode theo tên sách hoặc tác giả; `%` và `_` là ký tự thông thường.
- Admin: **Manage books** (`/admin/books`), **Authors**, **Genres**. Tạo/đổi tên tác giả/thể loại; đổi tên áp dụng cho sách liên kết. Sau đó **Add book**, **Edit**, **Hide**, **Show**. Ẩn không xóa bản ghi. Không xóa tác giả/thể loại để giữ liên kết sách.
- Giá nhập bằng VND, lớn hơn 0, tối đa 999.999.999,99, tối đa 2 chữ số thập phân; dùng dấu chấm khi nhập phần lẻ. Database lưu số nguyên đơn vị 1/100 VND. Tồn kho nguyên 0–2.147.483.647. Tên sách 1–200 ký tự; tác giả/thể loại 2–120; mô tả tối đa 10.000.
- Bìa: URL HTTPS không chứa thông tin đăng nhập; bỏ trống để dùng bìa mặc định. Ảnh ngoài hỏng chuyển sang bìa mặc định. Chưa có tải file ảnh lên. Form có ràng buộc HTML, JavaScript kiểm tra khoảng giá; server kiểm tra lại mọi dữ liệu.
- Sách ẩn không xuất hiện khi tìm, lọc, phân trang hoặc xem chi tiết; truy cập trực tiếp trả 404. Trang vượt tổng số trang trả 404; số trang hoặc bộ lọc không hợp lệ trả 400 kèm giải thích.

Đo lại thời gian xử lý/kết xuất server bằng database riêng:

```powershell
.\.venv\Scripts\python.exe scripts/measure_catalog.py
```

Script tạo SQLite trong `.test-tmp/`, thêm 36 sách, đo 100 GET `/books` qua Flask test client. Phép đo không bao gồm Bootstrap, mạng hoặc hiển thị trình duyệt; không dùng nó để khẳng định thời gian tải trang đầu cuối dưới 2 giây.

## Giới hạn khi chạy demo cục bộ

Đây là Release 1.0 chạy trên máy cá nhân. Máy chủ tích hợp của Flask dành cho phát triển. Bootstrap CSS được tải từ CDN nên cần Internet để hiển thị đầy đủ giao diện. CSS cục bộ và các chức năng trang vẫn tải được khi không có CDN. F1 chưa có đặt lại mật khẩu, xác minh email, giới hạn số lần đăng nhập hoặc nhật ký thao tác. Chưa xác minh trực quan giao diện bằng trình duyệt trong lần thực hiện này; xem VALIDATION.md.
