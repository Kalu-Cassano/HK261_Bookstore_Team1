# Hướng dẫn demo F1 (3–5 phút)

Chuẩn bị database và Admin đầu tiên theo [README.md](../README.md), sau đó khởi động máy chủ. Giữ kín mật khẩu Admin. Dùng cửa sổ trình duyệt thông thường cho Admin và cửa sổ ẩn danh cho Customer. Mỗi lần demo nên dùng một email Customer mới. Dùng mật khẩu thử nghiệm dài ít nhất 12 ký tự.

Tên nút và thông báo dưới đây được giữ bằng tiếng Anh để khớp với giao diện website.

## 0:00–0:40 — Trang chủ và đăng ký

1. Mở trang chủ. Giải thích sprint này chỉ thực hiện chức năng tài khoản.
2. Chọn **Create account** (Tạo tài khoản) trong cửa sổ ẩn danh.
3. Thử nhập mật khẩu quá ngắn và email không hợp lệ. Cho thấy trình duyệt báo lỗi.
4. Nhập tên, email hợp lệ và hai mật khẩu giống nhau. Tạo tài khoản.
5. Đăng nhập. Mở **My account** (Tài khoản của tôi) và cho thấy vai trò Customer.

## 0:40–1:20 — Các trường hợp bị từ chối truy cập

1. Khi đang đăng nhập bằng Customer, nhập trực tiếp `/admin/accounts` và `/admin/accounts/new` vào thanh địa chỉ.
2. Cho thấy **Access denied** (Từ chối truy cập). Giải thích server kiểm tra quyền trên từng đường dẫn, ngoài việc ẩn liên kết quản trị trên giao diện.
3. Đăng xuất. Mở `/account` để cho thấy hệ thống yêu cầu đăng nhập.
4. Thử đăng nhập bằng mật khẩu sai và cho thấy thông báo lỗi. Sau đó đăng nhập bằng mật khẩu đúng.

## 1:20–2:30 — Quản trị và khóa tài khoản

1. Đăng nhập bằng Admin đầu tiên trong cửa sổ thông thường.
2. Mở **Manage accounts** (Quản lý tài khoản). Chọn **Create account** để tạo thêm một Customer.
3. Khóa Customer đang đăng nhập trong cửa sổ ẩn danh: chọn trạng thái **Locked**, rồi bấm **Save changes** (Lưu thay đổi).
4. Tải lại **My account** trong cửa sổ ẩn danh. Cho thấy phiên đăng nhập đã mất hiệu lực.
5. Thử đăng nhập lại bằng Customer đó. Tài khoản bị khóa sẽ bị từ chối.
6. Trong cửa sổ Admin, mở khóa Customer bằng cách chọn **Active** rồi lưu. Customer có thể đăng nhập lại để tạo phiên mới.

## 2:30–3:30 — Admin cuối cùng và thay đổi vai trò

1. Khi chỉ có một Admin đang hoạt động, thử khóa chính Admin đó. Cho thấy thông báo từ chối.
2. Thử đổi vai trò của Admin đó thành Customer. Cho thấy hệ thống tiếp tục từ chối.
3. Tạo Admin thứ hai và cho thấy vai trò của tài khoản này trong danh sách.
4. Nếu còn thời gian: đăng nhập bằng Admin thứ hai trong một phiên trình duyệt riêng. Dùng Admin đầu tiên để hạ quyền tài khoản thứ hai thành Customer. Tải lại `/admin/accounts` trong phiên của tài khoản thứ hai và cho thấy **Access denied**.

## 3:30–4:30 — Bằng chứng kiểm thử và màn hình nhỏ

1. Chạy `.\.venv\Scripts\python.exe -m pytest -q` và trình bày kết quả thực tế.
2. Giải thích các kiểm thử có gửi yêu cầu giả mạo vai trò Admin và token CSRF bị thiếu hoặc sai. Đăng ký công khai vẫn chỉ tạo Customer. Lỗi CSRF trả về HTTP 400.
3. Giải thích database lưu mật khẩu dạng băm. Không trình chiếu thông tin đăng nhập thật.
4. Thu nhỏ chiều rộng trình duyệt tương ứng điện thoại và tablet. Trình bày biểu mẫu và các thẻ tài khoản.
5. Nhắc lại F2–F5 và yêu cầu thay đổi ISBN chưa thuộc phạm vi demo này.

Dùng đầu ra kiểm thử làm bằng chứng tự động. Chỉ khẳng định đã kiểm tra thủ công trên trình duyệt nếu thực sự thực hiện thao tác đó.
