# Team 1 Bookstore — F1

Sản phẩm Sprint 1 của môn Quản lý dự án phần mềm HK261.

Nhóm 1: Ngo Khai Luan và Nguyen Thanh Son.

## Phạm vi

F1 gồm đăng ký Customer (khách hàng), đăng nhập, đăng xuất, xem thông tin tài khoản và quản lý tài khoản dành cho Admin (quản trị viên). Admin có thể xem danh sách, tạo tài khoản, đổi vai trò và khóa hoặc mở khóa tài khoản. F2–F5 và yêu cầu thay đổi ISBN nằm ngoài phạm vi sprint này.

Ứng dụng sử dụng Python, Flask, SQLite, Jinja2 và Bootstrap 5. Dùng Python 3.12 trở lên.

## Cài đặt trên Windows PowerShell

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
  templates/          Các trang Jinja
  static/             CSS và kiểm tra biểu mẫu
tests/                Kiểm thử tích hợp F1
docs/DEMO.md          Hướng dẫn demo 3–5 phút
```

Các tính năng sách sau này có thể dùng Flask blueprint riêng. Hiện chưa có chức năng quản lý sách hoặc mua hàng.

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

Các kiểm thử sử dụng tệp SQLite tạm và vẫn bật CSRF. Phạm vi gồm đăng ký, kiểm tra dữ liệu, băm mật khẩu, đăng nhập/đăng xuất, phân quyền, yêu cầu giả mạo vai trò, tạo tài khoản, khóa tài khoản, vô hiệu hóa phiên, bảo vệ Admin cuối cùng, lệnh CLI và mã hóa ký tự HTML. Kết quả thực tế trong lần triển khai được ghi tại [docs/VALIDATION.md](docs/VALIDATION.md).

## Giới hạn khi chạy demo cục bộ

Đây là ứng dụng Sprint 1 chạy trên máy cá nhân. Máy chủ tích hợp của Flask dành cho phát triển. Bootstrap CSS được tải từ CDN nên cần Internet để hiển thị đầy đủ giao diện. CSS cục bộ và các chức năng trang vẫn tải được khi không có CDN. F1 chưa có đặt lại mật khẩu, xác minh email, giới hạn số lần đăng nhập hoặc nhật ký thao tác. Kiểm tra trên trình duyệt không thay thế kiểm tra tại server.
