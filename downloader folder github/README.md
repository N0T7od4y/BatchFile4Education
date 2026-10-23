# GitHub Folder Downloader

Công cụ dòng lệnh dành cho Windows, giúp tải một thư mục được chọn trên GitHub cùng các file và thư mục con bên trong, giữ nguyên cấu trúc tương đối.

## Tính năng

- Nhập trực tiếp link thư mục GitHub.
- Chọn branch hoặc tag cần tải.
- Tùy chọn vị trí lưu trên máy.
- Tạo thư mục kết quả riêng cho mỗi lần chạy để tránh ghi đè dữ liệu cũ.
- Xuất riêng nội dung thư mục đã chọn bằng Git archive, không checkout toàn bộ repository.
- Tự dọn dữ liệu tạm sau khi xử lý.

## Yêu cầu

- Windows có PowerShell, Git và `tar.exe` trong PATH.
- Kết nối Internet.
- Đủ dung lượng và quyền ghi tại nơi lưu dữ liệu.

Nếu chưa có Git, tải tại [Git for Windows](https://git-scm.com/downloads/win).

## Sử dụng

1. Tải file `download_github_folder.bat`.
2. Nhấp đúp vào file hoặc chạy trong CMD:

   ```bat
   .\download_github_folder.bat
   ```

3. Dán link thư mục theo định dạng:

   ```text
   https://github.com/OWNER/REPOSITORY/tree/BRANCH/path/to/folder
   ```

4. Nhập branch/tag hoặc nhấn **Enter** để dùng giá trị gợi ý. Nếu tên branch có dấu `/`, nhập đầy đủ tên branch.
5. Nhập nơi lưu hoặc nhấn **Enter** để dùng thư mục `Downloads` của tài khoản hiện tại.
6. Chờ thông báo `HOAN TAT` và mở đường dẫn kết quả.

## Kết quả

Thư mục đầu ra có dạng:

```text
folder_YYYYMMDD_HHMMSS_xxxxxx
```

Bên trong là các file và thư mục con của thư mục đã chọn. Các thư mục cha trên GitHub không được thêm vào kết quả.

## Lưu ý

- Dùng link thư mục có `/tree/`, không dùng link file có `/blob/`.
- Git vẫn tải metadata của repository để xác định nội dung cần xuất.
- Repository riêng tư yêu cầu Git trên máy đã được thiết lập xác thực phù hợp.
- Công cụ không tự tải nội dung submodule hoặc nội dung thật phía sau Git LFS pointer.
- Tên file không tương thích Windows có thể khiến bước giải nén thất bại. Nếu xuất TAR đã thành công, bản TAR được giữ lại khi giải nén lỗi.
- Giữ nguyên toàn bộ file `.bat`, bao gồm phần khởi động PowerShell ở đầu file.

## Phiên bản

**V2 — Không checkout:** sử dụng `git archive` để xuất riêng thư mục đã chọn, tránh bước checkout gặp đường dẫn không hợp lệ ở những phần khác của repository.
