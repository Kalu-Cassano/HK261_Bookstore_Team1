# Báo cáo kiểm tra F1

## Lần kiểm tra lại theo yêu cầu

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
