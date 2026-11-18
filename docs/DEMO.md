# Demo Release 1.0 - F1-F5

## Demo Release 1.0 — F1–F5 (7–10 phút)

Nâng cấp và tạo 36 sách mẫu theo [README.md](../README.md). Giữ nguyên `.env`, tài khoản cũ và database. Dùng Admin đã có, hoặc tự tạo bằng lệnh `create-admin` với mật khẩu nhập ẩn; không chia sẻ mật khẩu trong báo cáo.

1. **Catalogue công khai (F3):** mở `/books` trong cửa sổ chưa đăng nhập. Chỉ ra bìa, tên, tác giả, giá; đếm 12 sách/trang, sang trang 2 và 3. Sách mới nhất ở trước.
2. **Tìm/lọc (F5):** tìm `Bookstore Demo`; giữ trống thể loại, đặt min `55000`, max `230000`, bấm **Find** rồi sang trang 2. Chỉ ra URL và ô lọc giữ nguyên. Thêm thể loại `Technology` để thu hẹp kết quả. Tìm `Demo Author 1` để demo tìm theo tác giả; tìm chuỗi không có để hiện trạng thái rỗng. Thử min lớn hơn max để kiểm tra lỗi.
3. **Chi tiết và quay lại (F4):** từ trang 2 của kết quả nhiều trang, bấm sách. Chỉ ra mô tả, thể loại, giá và tồn kho. Bấm **Back to books**, xác nhận đúng trang 2 và bộ lọc. Mở `/books/999999` để thấy 404 dễ hiểu và liên kết về catalogue.
4. **Quản trị sách (F2):** đăng nhập Admin, mở **Manage books**. Trong **Authors** và **Genres**, thêm/đổi tên một mục demo. **Add book** với tên, tác giả, thể loại, giá dương, tồn kho 0; để trống bìa để dùng SVG cục bộ. Chỉ ra ràng buộc giá `0` và tồn kho `-1`/`1.5` trên form; sửa thành hợp lệ rồi lưu. Mở trang công khai để thấy sách mới đứng đầu và trạng thái hết hàng.
5. **Sửa và ẩn:** đổi giá/tồn kho, mô tả; kiểm tra chi tiết. Bấm **Hide**, kiểm tra sách biến mất cả khi tìm kiếm; URL chi tiết cũ trả 404. Bấm **Show** để khôi phục bản ghi. Dùng Customer thử `/admin/books`: 403. Chưa đăng nhập thì được chuyển về đăng nhập.
6. **F1:** đăng ký Customer, đăng nhập/đăng xuất, xem tài khoản; Admin xem/tạo/khóa tài khoản. Có thể dùng kịch bản F1 bên dưới để trình bày chi tiết.
7. **Responsive:** kiểm tra các chiều rộng 390, 768 và 1440 px, bao gồm catalogue, form lọc, chi tiết, trang quản trị; xác nhận không tràn ngang ngoài bảng cuộn. Đây là các bước người demo cần thực hiện; kết quả kiểm tra đã thực hiện được ghi riêng tại [VALIDATION.md](VALIDATION.md).
8. **CR-01 đã duyệt:** mở form Admin, thử ISBN rỗng, sai 13 chữ số hoặc trùng rồi sửa hợp lệ. Chi tiết hiển thị ISBN; với dữ liệu mẫu phải chỉ rõ nhãn **Demo code**, không gọi là ISBN thật của ấn bản. Copy mã vào ô tìm, kết hợp thể loại/giá rồi mở chi tiết và quay lại. Chạy lại cả hai seed: `Inserted 0`, ISBN đã có giữ nguyên. Chỉ trình bày kết quả test/hiệu năng đúng phạm vi báo cáo.

Không tạo tài khoản/mật khẩu mẫu cố định trong Git. Các sách mới được thêm thủ công khi demo không bị lệnh seed ghi đè.

## Kịch bản F1 chi tiết (3–5 phút)

Chuẩn bị Admin theo README và khởi động máy chủ. Dùng cửa sổ thường cho Admin và cửa sổ ẩn danh cho Customer; mỗi lần demo dùng email Customer mới và mật khẩu thử nghiệm dài ít nhất 12 ký tự.

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
5. Quay sang kịch bản Release 1.0 để demo F2–F5 và CR-01 ISBN đã duyệt, phân biệt rõ mã demo với ISBN thật.

Dùng đầu ra kiểm thử làm bằng chứng tự động. Chỉ khẳng định đã kiểm tra thủ công trên trình duyệt nếu thực sự thực hiện thao tác đó.
