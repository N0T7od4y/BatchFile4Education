# Chrome URL Launcher

**Phiên bản: 0.0.1**

Công cụ mở danh sách URL bằng một hồ sơ Google Chrome được chỉ định trên Windows. Người dùng thao tác qua menu dòng lệnh để chọn hồ sơ, mở tất cả liên kết, mở các mục được chọn hoặc cập nhật URL theo tên.

Chương trình được đóng gói trong file `mo_chrome.bat`, sử dụng PowerShell có sẵn trên Windows để xử lý dữ liệu và khởi chạy Chrome.

## Tính năng

- Tự tìm Chrome tại các vị trí cài đặt thông dụng.
- Liệt kê các hồ sơ Chrome theo tên, thư mục và email nếu có.
- Chọn một hồ sơ để mở các URL và ghi nhớ lựa chọn cho lần chạy tiếp theo.
- Mở toàn bộ danh sách hoặc chọn nhiều mục bằng số thứ tự, ví dụ `1,3,5`.
- Sửa URL của một mục và lưu lại vào danh sách.
- Kiểm tra định dạng URL; chỉ chấp nhận địa chỉ HTTP hoặc HTTPS.
- Tạo bản sao danh sách trước khi lưu thay đổi.

## Yêu cầu

- Windows có `powershell.exe` (khuyến nghị Windows 10/11 với Windows PowerShell 5.1).
- Google Chrome bản thường, đã mở và tạo ít nhất một hồ sơ.
- Chrome sử dụng thư mục dữ liệu mặc định của tài khoản Windows hiện tại.
- Có quyền ghi vào thư mục chứa script để lưu cấu hình và cập nhật danh sách.

Không cần cài Python, Node.js hoặc thư viện bổ sung.

## Các file

| File | Vai trò |
| --- | --- |
| `mo_chrome.bat` | Script chính, chứa phần khởi động Batch và phần xử lý PowerShell. |
| `danhsach.txt` | Danh sách tên và URL do người dùng chuẩn bị. |
| `chrome_profile.json` | Tự tạo khi chọn hồ sơ; lưu tên thư mục của hồ sơ đã chọn. |
| `danhsach.txt.bak` | Tự tạo khi cập nhật URL; giữ nội dung danh sách trước lần lưu gần nhất. |
| `README.md` | Hướng dẫn sử dụng. |

Hai file bắt buộc là `mo_chrome.bat` và `danhsach.txt`, đặt cùng thư mục. File `danhsach.txt.tmp` có thể xuất hiện tạm thời trong quá trình lưu.

## Chuẩn bị danh sách

Mỗi dòng trong `danhsach.txt` là một mục theo định dạng `tên,url`. Không thêm dòng tiêu đề.

```text
Google,https://www.google.com
YouTube,https://www.youtube.com
GitHub,https://github.com
PyPI Requests,https://pypi.org/project/requests/
```

Lưu file bằng UTF-8 để hỗ trợ tên tiếng Việt. URL cần bắt đầu bằng `http://` hoặc `https://` và không chứa khoảng trắng trực tiếp; có thể dùng dạng mã hóa URL như `%20` khi cần.

Danh sách được đọc theo định dạng CSV. Nếu tên hoặc URL chứa dấu phẩy, đặt trường đó trong dấu ngoặc kép:

```text
"Tài liệu, hướng dẫn",https://example.com/docs
```

Sau khi sửa URL qua menu, chương trình có thể tự đặt các trường trong dấu ngoặc kép. Đây là định dạng hợp lệ, không phải lỗi.

## Cách sử dụng

1. Đặt script và danh sách trong cùng một thư mục.
2. Nhấp đúp `mo_chrome.bat`.
3. Lần đầu chạy, nhập số tương ứng với hồ sơ Chrome muốn dùng. Đối chiếu tên, email nếu có và thư mục hồ sơ để chọn đúng.
4. Chọn chức năng trong menu.

| Lựa chọn | Chức năng | Cách nhập |
| --- | --- | --- |
| `1` | Mở tất cả URL bằng hồ sơ đang chọn. | Nhập `1`. |
| `2` | Mở các mục được chọn. | Nhập số thứ tự của mục, ví dụ `1,3,5`. |
| `3` | Thay đổi URL của một mục. | Nhập số thứ tự rồi nhập URL mới; Enter để hủy. |
| `4` | Đổi hồ sơ Chrome. | Chọn hồ sơ khác trong danh sách. |
| `0` | Thoát chương trình. | Nhập `0`. |

Chức năng chọn tên sử dụng **số thứ tự bên cạnh tên**, chưa hỗ trợ gõ tên để tìm kiếm. Nếu nhập trùng số trong một lần chọn, mục đó chỉ được mở một lần.

Ví dụ: muốn mở Google và GitHub theo danh sách mẫu, chọn chức năng `2`, sau đó nhập `1,3`.

## Cách chọn hồ sơ hoạt động

Chương trình đọc thông tin hồ sơ từ file cục bộ:

```text
%LOCALAPPDATA%\Google\Chrome\User Data\Local State
```

Các thư mục hồ sơ được nhận diện trong phiên bản này gồm `Default` và `Profile N`, chẳng hạn `Profile 2`. Số thứ tự hiển thị trong menu không phải số thư mục hồ sơ.

Khi mở URL, script truyền thư mục dữ liệu và hồ sơ đã chọn cho Chrome bằng các tham số `--user-data-dir` và `--profile-directory`. Những hồ sơ khác đang mở không bị đóng. Chrome có thể dùng cửa sổ sẵn có của hồ sơ được chọn; script không bắt buộc tạo cửa sổ riêng.

Ở lần chạy sau, chương trình dùng lại hồ sơ đã lưu nếu còn tồn tại. Nếu cấu hình không đọc được hoặc hồ sơ không còn trong danh sách, chương trình yêu cầu chọn lại.

## Lưu dữ liệu và sao lưu

- Lựa chọn hồ sơ được lưu trong `chrome_profile.json` dưới dạng tên thư mục, không lưu mật khẩu.
- Thay đổi URL được ghi vào `danhsach.txt`.
- File `danhsach.txt.bak` giữ bản trước lần lưu gần nhất, không phải lịch sử nhiều phiên bản.
- Để khôi phục danh sách, thoát chương trình, giữ lại bản hiện tại nếu cần, rồi sao chép nội dung file `.bak` về `danhsach.txt`.
- Nếu sửa danh sách bằng trình soạn thảo bên ngoài, hãy thoát và mở lại script để nạp dữ liệu mới.

Script đọc thông tin hồ sơ trên máy và yêu cầu Chrome mở URL; không triển khai máy chủ hay dịch vụ đồng bộ riêng.

## Giới hạn của phiên bản 0.0.1

- Giao diện dòng lệnh; thông báo trong script dùng tiếng Việt không dấu.
- Chưa có menu thêm, xóa hoặc đổi tên mục. Có thể chỉnh trực tiếp `danhsach.txt` khi chương trình đã đóng.
- Chỉ đọc hồ sơ của Chrome bản thường trong thư mục dữ liệu mặc định; chưa hỗ trợ Chrome Portable, Beta, Canary hoặc đường dẫn dữ liệu tùy chỉnh.
- Email chỉ hiển thị khi có trong thông tin hồ sơ cục bộ.
- Kiểm tra URL chỉ kiểm tra định dạng, không xác nhận trang tồn tại, tải thành công hoặc an toàn.
- Thông báo “Đã yêu cầu mở” không đồng nghĩa trang đã tải xong.
- Chưa giới hạn số tab khi mở tất cả; danh sách lớn có thể làm tăng mức sử dụng RAM.
- Không tự đăng nhập tài khoản hoặc thay đổi phiên đăng nhập của hồ sơ.

## Xử lý lỗi thường gặp

| Hiện tượng | Cách xử lý |
| --- | --- |
| Không tìm thấy Chrome | Kiểm tra Chrome đã cài tại vị trí thông dụng; bản hiện tại chưa có lựa chọn đường dẫn thủ công. |
| Không tìm thấy `danhsach.txt` | Đặt file cùng thư mục script và kiểm tra đúng phần mở rộng. |
| Không tìm thấy hồ sơ | Mở Chrome, tạo hoặc sử dụng một hồ sơ rồi chạy lại script; kiểm tra có đang dùng bản Chrome hoặc thư mục dữ liệu tùy chỉnh không. |
| Mở bằng hồ sơ không mong muốn | Chọn chức năng `4`, đối chiếu lại tên, email và thư mục hồ sơ. |
| URL bị bỏ qua | Kiểm tra tiền tố HTTP/HTTPS, khoảng trắng và cách đặt dấu ngoặc kép trong CSV. |
| Không lưu được thay đổi | Kiểm tra quyền ghi, thuộc tính chỉ đọc và file có bị chương trình khác khóa hay không. |
| Tên tiếng Việt hiển thị sai | Lưu `danhsach.txt` bằng UTF-8; kiểm tra terminal và font hỗ trợ tiếng Việt. |

## Ghi chú phiên bản

### 0.0.1

Phiên bản đầu tiên gồm quản lý danh sách URL cơ bản, lựa chọn hồ sơ Chrome, ghi nhớ hồ sơ, mở hàng loạt hoặc theo lựa chọn, cập nhật URL và sao lưu trước khi lưu.

