# VirusTotal Download Monitor — AUTO

Công cụ Python có giao diện **Tkinter** dùng để **theo dõi thư mục tải xuống** trên Windows và tự động kiểm tra các file mới/thay đổi với **VirusTotal API v3**. Khi VirusTotal chưa có báo cáo về file, ứng dụng có thể **tự động gửi file lên để phân tích** (tùy chọn này **bật mặc định**, nhưng cần người dùng xác nhận khi bắt đầu giám sát).

> **Phạm vi chính xác:** Công cụ giám sát hệ thống file trong thư mục bạn chọn, **không chặn luồng tải xuống, không chặn thực thi, không tự xóa/cách ly file và không thay thế phần mềm bảo vệ thiết bị**. Chỉ theo dõi các sự kiện xảy ra **sau khi** bắt đầu giám sát; không tự quét lại toàn bộ file đã có sẵn.

## 1. Chức năng chính

- **Giám sát tự động** thư mục được chọn (mặc định là `Downloads`) và các thư mục con.
- Nhận biết file **được tạo, chỉnh sửa hoặc đổi tên/di chuyển đến vị trí theo dõi**.
- **Đợi file ổn định** trước khi tính mã băm SHA-256 và bắt đầu tra cứu; bỏ qua các file tải tạm có đuôi `.crdownload`, `.part`, `.partial`, `.download`, `.opdownload`, `.filepart`, `.aria2`, `.tmp`.
- **Tra cứu theo SHA-256:** nếu VirusTotal đã có thống kê phát hiện, hiển thị ngay kết quả có sẵn.
- **Tự động gửi file chưa có báo cáo:** khi bật upload và VirusTotal trả về không có hồ sơ file, chương trình gửi file lên VirusTotal, nhận mã phân tích rồi kiểm tra kết quả.
- **Yêu cầu phân tích lại** khi file đã có hồ sơ trên VirusTotal nhưng chưa có thống kê AV, với điều kiện đã bật tùy chọn upload/quét mới.
- **Kiểm tra tiến độ** phân tích, xử lý giới hạn API HTTP 429 có thử lại, ghi nhật ký hoạt động.
- **Quét file thủ công**, **mở báo cáo VirusTotal** từ hàng được chọn và **xuất kết quả CSV**.
- Tránh gửi yêu cầu quét lặp lại cho những file có cùng SHA-256 trong cùng phiên làm việc khi có kết quả hoặc tác vụ đang chạy.

## 2. Yêu cầu hệ thống

- Windows 10/11 (môi trường mục tiêu của ứng dụng).
- Python 3.10 trở lên; nên dùng Python 3.11 hoặc 3.12.
- Kết nối Internet và **VirusTotal API key** có quyền sử dụng các API cần thiết.
- Thư viện ngoài: `requests`, `watchdog`. Tkinter thường được cung cấp cùng bản Python chuẩn trên Windows.

**Lưu ý hạn mức:** Ứng dụng chủ động giãn cách các yêu cầu API ít nhất **16 giây/yêu cầu**. Hạn mức thực tế và quyền upload phụ thuộc tài khoản/API key của bạn; việc giãn cách không bảo đảm tránh mọi lỗi `429`.

## 3. Cấu trúc tệp

```text
VirusTotal-Download-Monitor/
├── virus_total_download_monitor_auto.py   # Ứng dụng chính
├── requirements_virustotal_monitor.txt    # Các thư viện ngoài
└── README_VirusTotal_Download_Monitor_AUTO.md
```

## 4. Cài đặt

### 4.1. Kiểm tra Python

Mở **PowerShell** trong thư mục chứa source:

```powershell
python --version
```

### 4.2. Tạo môi trường ảo (khuyên dùng)

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements_virustotal_monitor.txt
```

Nếu chưa đặt file `requirements_virustotal_monitor.txt` vào cùng thư mục, cài trực tiếp:

```powershell
python -m pip install "requests>=2.31" "watchdog>=4.0"
```

**Không bắt buộc kích hoạt** `.venv`; có thể dùng thẳng file Python trong môi trường ảo. Cách này cũng tránh lỗi PowerShell chặn `Activate.ps1`.

### 4.3. Chạy chương trình

Khi có `.venv`:

```powershell
.\.venv\Scripts\python.exe virus_total_download_monitor_auto.py
```

Hoặc khi đã cài thư viện vào Python đang sử dụng:

```powershell
python virus_total_download_monitor_auto.py
```

## 5. Lấy VirusTotal API key

1. Đăng nhập VirusTotal tại <https://www.virustotal.com/>.
2. Mở trang API key: <https://www.virustotal.com/gui/my-apikey>.
3. Sao chép API key và nhập vào ô **VirusTotal API key** trên giao diện.

**Giữ API key bí mật.** Không dán key vào mã nguồn, không đưa vào GitHub hoặc ảnh chụp màn hình. Ứng dụng hiện nhập key tại giao diện mỗi lần chạy, không cung cấp chức năng lưu key ra file cấu hình.

## 6. Hướng dẫn dùng giao diện

| Thành phần | Công dụng |
| --- | --- |
| **VirusTotal API key** | Nhập khóa API dùng để tra cứu/upload. |
| **Thư mục theo dõi** | Nhập đường dẫn thư mục cần giám sát, mặc định là `~/Downloads`. |
| **Chọn thư mục** | Mở hộp thoại chọn thư mục. |
| **Tự động gửi file chưa có báo cáo...** | **Mặc định bật**. Cho phép upload file chưa có hồ sơ và yêu cầu quét lại hồ sơ thiếu thống kê AV. |
| **▶ Bắt đầu giám sát** | Bắt đầu quan sát sự kiện file mới/thay đổi; nếu bật upload thì cần xác nhận một lần cho phiên đó. |
| **■ Dừng** | Dừng tiếp nhận sự kiện và kết thúc tiến trình quét đang hoạt động khi có thể. |
| **Quét file thủ công** | Chọn một file bất kỳ để kiểm tra; **chỉ sử dụng khi giám sát đang chạy**. |
| **Xuất CSV** | Lưu các hàng kết quả hiện tại ra `.csv`. |
| **Xem báo cáo VT** | Mở trang detection theo SHA-256 của hàng đang chọn. |
| **Bảng kết quả** | Tên file, dung lượng, trạng thái, số `Malicious`, số `Suspicious`, SHA-256. |
| **Nhật ký** | Các sự kiện, yêu cầu quét và lỗi API. |

Bạn cũng có thể **nhấp đúp vào một dòng** trong bảng để mở báo cáo VirusTotal nếu dòng đó đã có SHA-256.

### Bật giám sát tự động

1. Mở chương trình và nhập API key.
2. Chọn đúng thư mục sẽ chứa file tải xuống (ví dụ `C:\Users\<ten-user>\Downloads`).
3. Để nguyên dấu chọn **Tự động gửi file chưa có báo cáo...** nếu muốn quét tự động toàn bộ các file chưa có hồ sơ VT. **Chỉ bật khi bạn đồng ý gửi nội dung file lên dịch vụ VirusTotal.**
4. Nhấn **▶ Bắt đầu giám sát**; đọc và đồng ý với hộp thoại xác nhận upload.
5. Tải một file mới vào thư mục đó. Sau khi file ổn định, xem trạng thái trong bảng kết quả và nhật ký.
6. Chọn một dòng, nhấn **Xem báo cáo VT** để xem thêm chi tiết trên trình duyệt.

**Ví dụ:** Bạn bắt đầu giám sát `Downloads`, sau đó tải `sample.zip` vào thư mục này. Ứng dụng phát hiện file, chờ file ngừng thay đổi, tính SHA-256, hỏi VirusTotal theo hash. Nếu chưa có báo cáo và đã bật upload, ứng dụng gửi `sample.zip` lên để phân tích và theo dõi kết quả. Đây là ví dụ quy trình, không phải kết quả quét thực tế.

### Quét file có sẵn trước khi chạy ứng dụng

Chương trình **không tự quét toàn bộ file tồn tại trước khi bấm Bắt đầu**. Với file cũ, nhấn **Quét file thủ công** khi giám sát đang chạy để chọn và kiểm tra file đó.

## 7. Luồng hoạt động

```text
Có sự kiện file trong thư mục theo dõi
    │
    ├─ File tạm / không phải file thường / symbolic link → Bỏ qua
    │
    ▼
Đợi file ổn định (ít nhất 4 giây sau sự kiện ghi cuối cùng)
    │
    ▼
Tính SHA-256
    │
    ▼
Tra cứu GET /api/v3/files/{sha256}
    │
    ├─ Có báo cáo với thống kê AV → Hiển thị kết quả
    │
    ├─ Có hồ sơ nhưng chưa có thống kê AV
    │       ├─ Đã bật quét mới → POST /files/{sha256}/analyse
    │       └─ Đã tắt → Báo chưa có kết quả AV
    │
    └─ Không có hồ sơ (404)
            ├─ Đã tắt upload → Báo chưa có báo cáo
            ├─ File > 650 MiB → Không upload
            └─ Đã bật upload → POST /files hoặc URL upload lớn
                                     │
                                     ▼
                              Nhận analysis_id
                                     │
                                     ▼
                         GET /analyses/{analysis_id}
                                     │
                                     ▼
                         Hiển thị kết quả khi hoàn tất
```

Ứng dụng đợi ít nhất **4 giây file không thay đổi** trước khi xử lý. Sau khi gửi yêu cầu phân tích, chương trình dự kiến kiểm tra khoảng **30 giây/lần**, tối đa **12 lượt kiểm tra** trong một tác vụ; thời gian thực tế có thể lâu hơn do hàng đợi và giãn cách API. Hết số lượt kiểm tra không có nghĩa file an toàn: có thể xem thêm trên VirusTotal.

## 8. Đọc kết quả

| Trạng thái hiển thị | Ý nghĩa |
| --- | --- |
| **Chờ tải xong** | Đã phát hiện file; đang chờ ổn định. |
| **Tính SHA-256** | Đang tính mã băm. |
| **Đang tra cứu VirusTotal** | Đang kiểm tra hồ sơ theo SHA-256. |
| **Chưa có báo cáo; đang upload tự động** | Đang gửi file chưa từng có báo cáo lên VirusTotal. |
| **Đã upload; đang chờ quét** | Đã nhận ID phân tích và bắt đầu chờ kết quả. |
| **Đã gửi; đang chờ quét mới** | Đã yêu cầu quét lại hồ sơ đã có nhưng thiếu thống kê AV. |
| **Có phát hiện mã độc** | Ít nhất một engine trả về `malicious`. |
| **Có dấu hiệu nghi ngờ** | Không có `malicious` nhưng có ít nhất một engine trả về `suspicious`. |
| **Chưa bị phát hiện** | Thống kê nhận được không có engine gắn `malicious`/`suspicious` và có kết quả thống kê khác 0; **không chứng minh file an toàn**. |
| **Chưa có kết quả từ AV** | Chưa nhận được thống kê phát hiện hữu ích. |
| **Chưa xong; xem trên VT** | Đã hết lượt theo dõi trong ứng dụng, phân tích có thể vẫn tiếp diễn ở VirusTotal. |
| **Lỗi API / Lỗi lấy kết quả** | Có lỗi từ kết nối, quyền API hoặc xử lý. Xem nhật ký. |

`Malicious` và `Suspicious` là **số engine trả về các nhãn tương ứng**, không phải tỷ lệ phần trăm, cũng không đồng nghĩa với đánh giá chắc chắn.

## 9. Xuất dữ liệu CSV

Nhấn **Xuất CSV** để chọn vị trí lưu. File CSV bao gồm các cột:

```text
path,size_bytes,status,malicious,suspicious,sha
```

Mỗi dòng là một đường dẫn file đã xuất hiện trong bảng của phiên chạy. CSV sử dụng UTF-8 BOM (`utf-8-sig`) để dễ mở bằng Excel trên Windows. Chương trình **không tự lưu lịch sử quét vào cơ sở dữ liệu**; nếu cần giữ báo cáo, hãy xuất CSV trước khi đóng.

## 10. Thiết lập kỹ thuật trong source

Có thể điều chỉnh những hằng số ở đầu file `virus_total_download_monitor_auto.py`:

| Hằng số | Giá trị trong bản này | Vai trò |
| --- | --- | --- |
| `API_ROOT` | `https://www.virustotal.com/api/v3` | URL API v3. |
| `QUIET_SECONDS` | `4.0` | Thời gian file không thay đổi trước khi quét. |
| `MIN_REQUEST_INTERVAL` | `16.0` | Khoảng cách tối thiểu giữa hai yêu cầu API. |
| `POLL_INTERVAL` | `30.0` | Khoảng thời gian dự kiến giữa các lần hỏi tiến độ. |
| `MAX_POLLS` | `12` | Số lần hỏi tiến độ tối đa cho mỗi phân tích. |
| `SMALL_LIMIT` | `32 * 1024 * 1024` | Ngưỡng sử dụng endpoint upload nhỏ; file lớn hơn cần lấy upload URL. |
| `MAX_UPLOAD` | `650 * 1024 * 1024` | Giới hạn upload do **source** đặt ra; hạn mức dịch vụ/tài khoản có thể thấp hơn. |
| `TEMP_SUFFIXES` | Các đuôi file tạm | Bỏ qua file tạm; file cuối sau khi đổi tên sẽ được xem xét. |

Không chỉnh hạn mức gọi API vượt quá quyền của tài khoản.

## 11. Lỗi thường gặp

| Vấn đề | Nguyên nhân cần kiểm tra / cách xử lý |
| --- | --- |
| `ModuleNotFoundError: No module named 'watchdog'` (hoặc `requests`) | Chạy `python -m pip install requests watchdog`, đảm bảo sử dụng đúng Python đã cài thư viện. |
| `401` hoặc `403` | Kiểm tra API key, quyền tài khoản, quyền truy cập endpoint. |
| `429 Too Many Requests` | API đã giới hạn; chương trình thử lại theo `Retry-After` hoặc thời gian chờ dự phòng, nhưng có thể vẫn dừng tác vụ sau nhiều lần lỗi. |
| `Không có báo cáo VT (đã tắt upload)` | Tùy chọn upload đã bị bỏ chọn trước khi bắt đầu giám sát; dừng rồi bật lại và khởi động phiên mới nếu thực sự muốn gửi file. |
| `Chưa xong; xem trên VT` | Phân tích chưa hoàn tất trong số lượt kiểm tra; dùng **Xem báo cáo VT** hoặc kiểm tra lại sau. |
| File không xuất hiện trong bảng | Xác minh file được thêm/sửa **sau khi** bắt đầu, đúng thư mục đang giám sát; file có thể còn ở tên tạm hoặc thuộc loại bị bỏ qua. |
| Không quét được file cũ | Dùng **Quét file thủ công** sau khi bật giám sát. |
| File lớn không được upload | Giới hạn trong code là 650 MiB; tài khoản hoặc API cũng có thể áp dụng giới hạn riêng. |
| Dừng không tức thời | Tác vụ mạng/upload đang thực hiện có thể cần kết thúc hoặc hết timeout trước khi worker dừng. |

## 12. Bảo mật, quyền riêng tư và giới hạn

1. **Chỉ có hash được gửi khi tra cứu báo cáo có sẵn**. Nếu bật upload tự động và file chưa có hồ sơ, **nội dung file** sẽ được gửi lên VirusTotal. Đừng bật tùy chọn này cho thư mục chứa tài liệu riêng tư, khóa API, mã nguồn bí mật, hợp đồng, thông tin cá nhân hoặc dữ liệu công ty chưa được phép chia sẻ.
2. **Không có cơ chế cách ly hay chặn chạy:** file có thể được người dùng hoặc hệ điều hành mở trước khi có kết quả; không xem ứng dụng là giải pháp ngăn mã độc theo thời gian thực.
3. **Không đánh giá được 100% độ an toàn:** không có cảnh báo từ engine vẫn có thể là file độc hại hoặc chưa được phát hiện.
4. **Chỉ quan sát thư mục được chọn:** không giám sát mọi tệp trên Internet hay tải xuống ở các thư mục khác; không theo dõi nội dung mạng trực tiếp.
5. **Chỉ phân tích file được đưa lên:** với file nén, kết quả nhận được gắn với file nén đó; chương trình không tự giải nén, chạy hay quét từng thành phần riêng.
6. **Không bảo đảm hoàn tất tất cả tác vụ:** giới hạn API, mạng, quyền truy cập và thời gian phân tích của VirusTotal có thể làm việc quét bị lỗi hoặc chậm.
7. **Bảo vệ API key:** không chia sẻ key, và tránh lưu ảnh màn hình có chứa thông tin nhạy cảm.

## 13. Tham khảo

- VirusTotal: <https://www.virustotal.com/>
- VirusTotal API v3: <https://docs.virustotal.com/reference/overview>
- VirusTotal API key: <https://www.virustotal.com/gui/my-apikey>

---

**Phiên bản được tài liệu hóa:** `virus_total_download_monitor_auto.py` (bản AUTO). Nội dung README phản ánh logic hiện có trong source, không khẳng định đã thử nghiệm với tài khoản VirusTotal thật.
