# Image Compressor GUI

## 1. Giới thiệu

**Image Compressor GUI** là ứng dụng nén dung lượng hình ảnh được phát triển bằng Python, sử dụng thư viện Tkinter để xây dựng giao diện đồ họa và Pillow để xử lý hình ảnh.

Ứng dụng cho phép người dùng lựa chọn ảnh, thiết lập dung lượng tối đa mong muốn và tự động nén ảnh mà không cần thao tác bằng dòng lệnh.

## 2. Chức năng chính

- Chọn hình ảnh từ máy tính.
- Hiển thị dung lượng ban đầu của hình ảnh.
- Tùy chỉnh dung lượng tối đa sau khi nén (MB).
- Tự động điều chỉnh chất lượng và độ phân giải hình ảnh.
- Lưu ảnh sau khi nén vào cùng thư mục với ảnh gốc.
- Không ghi đè hoặc làm thay đổi ảnh gốc.
- Thông báo kết quả sau khi hoàn tất quá trình nén.

## 3. Công nghệ sử dụng

| Công nghệ | Chức năng |
|---|---|
| Python | Ngôn ngữ lập trình chính |
| Tkinter | Xây dựng giao diện đồ họa |
| Pillow | Đọc, xử lý và nén hình ảnh |
| BytesIO | Lưu dữ liệu ảnh tạm thời trong bộ nhớ |

## 4. Yêu cầu hệ thống

- Python phiên bản 3.8 trở lên.
- Hệ điều hành Windows, Linux hoặc macOS.
- Thư viện Pillow.

## 5. Hướng dẫn cài đặt

**Bước 1: Tải source code**

Clone repository về máy tính:

```bash
git clone <repository-url>
```

Di chuyển vào thư mục dự án:

```bash
cd <repository-folder>
```

**Bước 2: Cài đặt thư viện**

```bash
pip install Pillow
```

Lưu ý: Tkinter thường được tích hợp sẵn trong Python. Trên một số bản phân phối Linux, cần cài đặt thêm gói Tkinter tương ứng.

## 6. Hướng dẫn sử dụng

**Bước 1: Khởi chạy ứng dụng**

Mở Terminal hoặc CMD tại thư mục chứa source code và thực thi:

```bash
python image_compressor_gui.py
```

**Bước 2: Chọn hình ảnh**

- Nhấn nút `Chọn ảnh`.
- Chọn hình ảnh cần nén từ máy tính.
- Dung lượng ban đầu của ảnh sẽ được hiển thị trên giao diện.

**Bước 3: Thiết lập dung lượng**

Nhập dung lượng tối đa mong muốn vào trường:

`Dung lượng tối đa (MB)`

Ví dụ:

- `1` = tối đa 1 MB.
- `0.5` = tối đa 0.5 MB.
- `2` = tối đa 2 MB.

**Bước 4: Tiến hành nén**

Nhấn nút `NÉN ẢNH`.

Chương trình sẽ tự động:
1. Đọc dữ liệu hình ảnh.
2. Chuyển đổi hình ảnh sang định dạng RGB.
3. Điều chỉnh chất lượng JPEG.
4. Giảm độ phân giải nếu cần thiết.
5. Kiểm tra dung lượng đầu ra so với giới hạn đã thiết lập.

**Bước 5: Kiểm tra kết quả**

Sau khi nén thành công, ứng dụng hiển thị:
- Dung lượng ảnh sau khi nén.
- Tỷ lệ dung lượng đã giảm.
- Đường dẫn lưu file kết quả.

## 7. Định dạng hình ảnh hỗ trợ

| Định dạng đầu vào | Định dạng đầu ra |
|---|---|
| JPG | JPEG |
| JPEG | JPEG |
| PNG | JPEG |
| WEBP | JPEG |
| BMP | JPEG |

**Lưu ý:** Ảnh PNG có nền trong suốt sẽ được chuyển sang nền trắng khi xuất sang JPEG.

## 8. Cấu trúc thư mục

```text
Image-Compressor/
│
├── image_compressor_gui.py
│
└── README.md
```

## 9. Kết quả đầu ra

Ví dụ, khi lựa chọn file:

```text
example.png
```

Sau khi nén, chương trình tạo file:

```text
example_compressed.jpg
```

File mới được lưu cùng thư mục với ảnh gốc.

Ảnh gốc vẫn được giữ nguyên, không bị ghi đè.

## 10. Lưu ý khi sử dụng

- Dung lượng thiết lập là giới hạn tối đa, không phải dung lượng đầu ra chính xác.
- Chất lượng hình ảnh có thể giảm khi nén.
- Độ phân giải có thể bị giảm nếu chỉ điều chỉnh chất lượng JPEG chưa đủ để đạt dung lượng yêu cầu.
- Ảnh đầu ra luôn sử dụng định dạng JPEG.
- Với giới hạn dung lượng quá thấp, chất lượng hình ảnh có thể suy giảm đáng kể.

## 11. Mục đích dự án

Dự án được xây dựng nhằm thực hành lập trình Python, xử lý hình ảnh và phát triển ứng dụng desktop có giao diện đồ họa bằng Tkinter.

Ứng dụng phù hợp cho nhu cầu giảm dung lượng hình ảnh trước khi tải lên website, gửi qua email hoặc sử dụng trên các nền tảng có giới hạn kích thước file.