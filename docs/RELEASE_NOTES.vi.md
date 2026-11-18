# Release 1.0 — 2026-11-09

Tiếp tục từ commit `55167a1` (F1 Sprint 1). F1 giữ nguyên hành vi đăng ký, đăng nhập, tài khoản, phân quyền và quản trị tài khoản. Release này hoàn thành mã nguồn F2–F5 theo phạm vi được giao.

- F2: Admin thêm/sửa sách, ẩn và khôi phục bằng POST có CSRF; thêm/đổi tên tác giả và thể loại. Server kiểm tra tên, giá, tồn kho, quan hệ tác giả/thể loại, mô tả và URL bìa; form có ràng buộc tương ứng. SQLite bật foreign keys và CHECK cho giá/tồn kho. Bìa HTTPS hoặc SVG mặc định đi kèm.
- F3: catalogue công khai, có bìa/tên/tác giả/giá, sắp xếp `created_at DESC, id DESC`, 12 sách/trang; loại sách ẩn trước khi đếm và phân trang. Bootstrap bố cục 1/2/3/4 cột theo kích thước màn hình.
- F4: trang chi tiết có mô tả, thể loại và tồn kho. Sách ẩn/không tồn tại trả 404 có liên kết về catalogue. Nút quay lại dựng từ bộ lọc và trang, không nhận URL điều hướng bên ngoài.
- F5: tìm tên sách/tác giả không phân biệt hoa thường Unicode; lọc thể loại và min/max giá theo điều kiện AND. Giữ bộ lọc qua phân trang và chi tiết. Câu truy vấn dùng tham số; ký tự LIKE được escape.
- `upgrade-db`/`init-db` thêm bảng/index nếu chưa có, giữ tài khoản; `seed-books` thêm 36 sách xác định, chạy lại không ghi đè hoặc tạo trùng. Có test database F1 cũ, sao lưu cục bộ trước khi nâng cấp thật và đối chiếu dữ liệu tài khoản.

## CR-01 — đã duyệt và triển khai

Người dùng đã xác nhận CR-01 được duyệt trong yêu cầu triển khai tiếp theo. Trạng thái chờ ở lần Release trước được thay thế bởi triển khai hiện tại:

- F2: ISBN chuỗi 13 chữ số ASCII, bắt buộc khi thêm/sửa, duy nhất kể cả sách ẩn. Form có required/pattern; server kiểm tra và xử lý xung đột ghi; SQLite có TEXT NOT NULL, UNIQUE, CHECK. Giữ Admin authorization, CSRF và luồng quản lý sách.
- F4: chi tiết có ISBN và nhãn riêng cho mã demo. F5: tìm ISBN đầy đủ/một phần bằng cùng ô tìm tên/tác giả, giữ bộ lọc, phân trang và điều hướng quay lại.
- Migration tự sao lưu trước khi ghi, backfill ISBN rồi chuyển sang bảng có ràng buộc trong một giao dịch; giữ ID, dữ liệu cột cũ, chỉ mục, tài khoản và sequence ID. Không đổi giá hoặc `.env`. Chạy lại không cấp lại ISBN. Cả hai seed giữ mã/dữ liệu đã có.
- Không xác minh đủ thông tin ấn bản của 16 đầu sách thật; toàn bộ 52 sách hiện có dùng mã demo 13 chữ số prefix `000`, cờ `isbn_is_demo=1`, hiển thị **Demo code — not a verified edition ISBN**. Các mã này không được trình bày như ISBN thật. Chỉ thay bằng mã thật khi xác minh ấn bản; chưa kiểm tra checksum/ấn bản tự động.

Hướng dẫn PowerShell và cơ chế backup trong [README](../README.md); kết quả kiểm tra thực tế trong [VALIDATION.md](VALIDATION.md).

## Phạm vi và giới hạn

Không có giỏ hàng, thanh toán hoặc đăng nhập mạng xã hội. Chưa triển khai production/HTTPS hoặc kiểm tra tải nhiều người dùng. Bootstrap tải từ CDN; ảnh HTTPS bên ngoài phụ thuộc máy chủ ảnh. Hình mẫu hoạt động cục bộ. Phép đo server không thay thế đánh giá tải trang trên trình duyệt. Xem kết quả thật và phạm vi kiểm tra giao diện trong [VALIDATION.md](VALIDATION.md).

Không push, tạo tag hay deploy trong công việc Release 1.0 này. Thay đổi giữ trong working tree để người dùng kiểm tra.
