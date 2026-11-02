# Git Identity Manager — Python Tkinter

Hướng dẫn cho file `git_identity_manager.py`.

## 1. Mục đích

Ứng dụng có giao diện để xem, thay đổi và xóa hai trường cấu hình Git:

- `user.name`: tên tác giả được dùng cho commit mới.
- `user.email`: email tác giả được dùng cho commit mới.

Đây là cấu hình Git, không phải tên tài khoản Windows hay email đăng nhập GitHub. Chương trình không sửa thông tin trong commit cũ, không đăng xuất GitHub và không xóa mật khẩu, token hay SSH key.

## 2. Yêu cầu

- Python 3.9 trở lên, có Tkinter.
- Git đã được cài và có trong `PATH`.
- Môi trường desktop để hiển thị cửa sổ.

Source chỉ dùng thư viện chuẩn Python, không cần `pip install` thêm thư viện.

Kiểm tra bằng CMD hoặc PowerShell:

```bat
python --version
git --version
python -m tkinter
```

Lệnh cuối mở cửa sổ thử Tkinter. Nếu thiếu Tkinter trên Windows, sửa/cài lại Python có thành phần Tcl/Tk.

## 3. Khởi chạy

Mở terminal tại thư mục chứa source:

```bat
python git_identity_manager.py
```

Nếu sử dụng venv, có thể gọi trực tiếp từ CMD:

```bat
".venv\Scripts\python.exe" git_identity_manager.py
```

Chương trình tự đọc cấu hình Global khi mở. Không tự thay đổi hoặc xóa cấu hình lúc khởi động.

## 4. Chọn phạm vi

| Phạm vi | Ý nghĩa | Quyền truy cập |
| --- | --- | --- |
| Global — tài khoản hiện tại | Cấu hình Git của tài khoản hệ điều hành đang chạy ứng dụng | Thường không cần Administrator |
| System — bản cài Git | Cấu hình chung của bản cài Git được tìm thấy trong PATH | Có thể cần Administrator |

Chuyển phạm vi sẽ đọc lại tên và email của phạm vi mới.

**System không đồng nghĩa với ghi đè mọi danh tính Git trên toàn thiết bị.** Cấu hình riêng của tài khoản, repository, file include hoặc biến môi trường có thể làm Git sử dụng giá trị khác. Ứng dụng không quét tất cả tài khoản hay repository.

Nếu cần sửa System và bị từ chối quyền ghi, mở CMD bằng **Run as administrator**, rồi chạy source bằng đường dẫn đầy đủ. Kiểm tra đúng tài khoản đang chạy vì Global thuộc tài khoản đó.

## 5. Các nút trên giao diện

| Nút | Chức năng |
| --- | --- |
| Đọc lại | Nạp lại giá trị và file cấu hình nguồn; ghi đè nội dung chưa lưu trong ô nhập |
| Lưu cạnh một trường | Ghi riêng trường đó |
| Xóa cạnh một trường | Hỏi xác nhận rồi xóa khóa khỏi file cấu hình đích |
| Lưu cả hai | Ghi tên và email lần lượt |
| Xóa cả hai | Hỏi xác nhận rồi xóa hai khóa lần lượt |

### Đổi tên và email

1. Chọn Global hoặc System.
2. Nhập tên vào `user.name`, email vào `user.email`.
3. Bấm **Lưu cả hai**, hoặc **Lưu** cạnh trường cần sửa.
4. Đọc kết quả từng trường trong khung log.

Không để trống trường cần lưu. Muốn bỏ giá trị, dùng nút **Xóa**. Source kiểm tra giá trị rỗng và ký tự điều khiển; không kiểm tra email tồn tại hay thuộc tài khoản GitHub nào.

### Xóa thông tin

1. Chọn đúng phạm vi.
2. Bấm **Xóa** hoặc **Xóa cả hai**.
3. Xác nhận trong hộp thoại.
4. Kiểm tra lại giá trị và nguồn được hiển thị.

Nếu giá trị vẫn xuất hiện, xem đường dẫn nguồn: giá trị có thể được đọc từ file khác hoặc include mà thao tác xóa không sửa tới.

## 6. Cách xử lý và kết quả

Ứng dụng gọi Git bằng `subprocess`, không sửa file cấu hình bằng cách thay thế chuỗi thủ công.

Các thao tác chính tương đương:

```bat
git config --global --includes --get user.name
git config --global --includes --show-origin --get-regexp "^user\.(name|email)$"
git config --global --replace-all user.name "Ten cua ban"
git config --global --unset-all user.name
```

Phạm vi System dùng `--system` thay cho `--global`.

- Log trên giao diện hiển thị kết quả thao tác, giá trị và file nguồn.
- Log không được tự lưu thành file.
- Mỗi lệnh Git có thời gian chờ tối đa 15 giây.
- Hai trường được xử lý độc lập. Một trường có thể thành công trong khi trường còn lại lỗi; không có giao dịch hay tự hoàn tác.
- Không có chức năng sao lưu/khôi phục tự động.
- Khi đang xử lý, các điều khiển bị khóa và ứng dụng yêu cầu chờ trước khi đóng.

## 7. Lỗi thường gặp

| Hiện tượng | Cách xử lý |
| --- | --- |
| Không tìm thấy Git | Kiểm tra `git --version`, cài Git/thêm PATH rồi mở lại ứng dụng |
| Không ghi được System | Kiểm tra quyền file; chạy bằng quyền quản trị nếu cần |
| Giá trị không hợp lệ | Không để trống hoặc nhập ký tự điều khiển; dùng Xóa để bỏ khóa |
| Hết thời gian chờ | Bấm Đọc lại trước khi thử tiếp để biết cấu hình hiện tại |
| Xóa rồi vẫn thấy giá trị | Xem file nguồn/include trong log |
| Commit vẫn dùng tên khác | Kiểm tra cấu hình tại repository cụ thể và biến môi trường |

Để kiểm tra trong một repository, mở terminal tại repository đó rồi chạy:

```bat
git config --show-origin --show-scope --get-regexp "^user\.(name|email)$"
```

Ứng dụng không chọn repository và đọc cấu hình từ thư mục tạm, nên không đại diện đầy đủ cho các điều kiện include phụ thuộc repository.

