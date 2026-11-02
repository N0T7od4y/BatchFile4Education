# Python Packager — đóng gói Python bằng giao diện Tkinter

Hướng dẫn cho file `python_packager.py`.

## 1. Mục đích

Chọn source Python và đóng gói ứng dụng bằng PyInstaller qua giao diện. Trên Windows, đầu ra là EXE. Công cụ hỗ trợ:

- Chọn Python hệ thống hoặc Python trong venv.
- Cài PyInstaller và Pillow vào môi trường đã chọn.
- Đóng gói một file hoặc một thư mục.
- Ẩn/hiện console.
- Chọn ảnh để tự tạo icon ICO trên Windows.
- Thêm dữ liệu đi kèm và hidden imports.
- Hiển thị log trong lúc build và lưu log PyInstaller.

Công cụ không tự tạo venv, không tự cài toàn bộ thư viện của source và không tự sửa source để tương thích với đóng gói.

## 2. Yêu cầu

- Python 3.9 trở lên có Tkinter để chạy giao diện.
- Python dùng để build phải tương thích với phiên bản PyInstaller được cài.
- Các thư viện mà source sử dụng phải có trong môi trường build.
- Internet khi cài công cụ hoặc thư viện chưa có.

Để tạo EXE Windows, chạy công cụ trên Windows. Không dùng bản này để tạo EXE Windows từ Linux.

## 3. Khởi chạy

Mở CMD tại thư mục chứa file:

```bat
python python_packager.py
```

PyInstaller và Pillow chưa cần được cài để mở giao diện; chúng cần cho bước đóng gói/chuyển ảnh.

Kiểm tra Tkinter nếu cửa sổ không mở:

```bat
python -m tkinter
```

## 4. Chuẩn bị venv

Ví dụ dưới đây dùng CMD Windows, tại thư mục dự án:

```bat
python -m venv .venv
```

Nếu dự án có `requirements.txt`, cài thư viện của dự án:

```bat
".venv\Scripts\python.exe" -m pip install -r requirements.txt
```

Trong giao diện, chọn đường dẫn đầy đủ đến:

```text
<thu_muc_du_an>\.venv\Scripts\python.exe
```

Không chọn `pythonw.exe`. Không cần kích hoạt venv khi đã chọn trực tiếp `python.exe` bên trong.

**Nút Cài công cụ dùng đúng Python ở ô Python / venv.** Nếu chọn Python hệ thống thì cài vào môi trường đó; nếu chọn Python của venv thì cài vào venv. Nút này chạy tương đương:

```bat
".venv\Scripts\python.exe" -u -m pip install pyinstaller Pillow
```

Lệnh không có `--upgrade`; công cụ không chủ động nâng cấp những gói đã đáp ứng yêu cầu.

## 5. Quy trình đóng gói nhanh

1. Mở `python_packager.py`.
2. Chọn **Python / venv** đã cài các thư viện của ứng dụng.
3. Bấm **Cài công cụ** lần đầu, chờ log báo thành công.
4. Chọn **Source chính (.py)**: file khởi chạy ứng dụng, có thể là `.py` hoặc `.pyw`.
5. Chọn **Thư mục kết quả** và nhập **Tên ứng dụng**.
6. Chọn **Ảnh / icon** nếu cần.
7. Chọn chế độ một file và console phù hợp.
8. Thêm dữ liệu/hidden imports nếu dự án cần.
9. Bấm **ĐÓNG GÓI**, theo dõi log.
10. Khi thành công, bấm **Mở kết quả**, vào `dist` để lấy ứng dụng.

Chạy thử source bằng chính Python đã chọn trước khi build. Build thành công chưa bảo đảm mọi chức năng của EXE hoạt động; cần chạy thử đầu ra.

## 6. Các trường và nút

| Thành phần | Cách dùng |
| --- | --- |
| Python / venv | Đường dẫn đầy đủ đến Python dùng để cài công cụ và build |
| Source chính (.py) | File đầu vào khởi chạy ứng dụng |
| Thư mục kết quả | Nơi chứa các lần build; mặc định là `packaged` cạnh source nếu ô còn trống khi chọn source |
| Tên ứng dụng | Tên đầu ra; nên nhập không có đuôi `.exe` |
| Ảnh / icon | Tùy chọn; bỏ trống nếu dùng icon mặc định |
| Hidden imports | Tên module cần bổ sung, phân cách bằng dấu phẩy; để trống nếu chưa cần |
| Một file duy nhất | Bật: `--onefile`; tắt: `--onedir` |
| Ẩn console (ứng dụng GUI) | Bật cho Tkinter/GUI; tắt với chương trình dùng `input()` hoặc terminal |
| Thêm file dữ liệu | Thêm file tài nguyên vào gốc bundle |
| Thêm thư mục dữ liệu | Kèm thư mục, giữ tên thư mục được chọn |
| Bỏ dữ liệu đã chọn | Xóa toàn bộ danh sách tài nguyên trong giao diện; không xóa file gốc |
| Cài công cụ | Cài PyInstaller và Pillow vào Python đã chọn |
| ĐÓNG GÓI | Chuyển icon nếu cần, sau đó gọi PyInstaller |
| Mở kết quả | Mở thư mục của lần build gần nhất, kể cả lần build lỗi |

Tên ứng dụng cho phép chữ, số, khoảng trắng, gạch ngang, gạch dưới và dấu chấm theo bộ kiểm tra của source. Tránh tên kết thúc bằng dấu chấm và các tên Windows dành riêng như `CON`, `NUL`, `COM1`.

### Cách dùng từng nút

#### Nút “Chọn…” cạnh Python / venv

1. Bấm nút để mở hộp thoại chọn file.
2. Vào thư mục Python hoặc venv của dự án.
3. Chọn `python.exe`; với venv Windows, file thường nằm tại `.venv\Scripts\python.exe`.
4. Kiểm tra đường dẫn được điền vào ô.

Nút này chỉ chọn môi trường, không tạo venv và không cài thư viện. Môi trường này được dùng cho cả cài công cụ, chuyển icon và đóng gói.

#### Nút “Chọn…” cạnh Source chính (.py)

1. Chọn file `.py` hoặc `.pyw` khởi chạy ứng dụng.
2. Tên ứng dụng tự đổi thành tên file không có phần mở rộng.
3. Nếu ô kết quả đang trống, công cụ điền thư mục `packaged` cạnh source.

Với dự án nhiều file, chọn file đầu vào chính, không cần chọn lần lượt mọi file Python. Những module được import phải truy cập được từ môi trường build. Đổi source không tự xóa icon, hidden imports hoặc danh sách dữ liệu của dự án trước; hãy kiểm tra lại các ô này.

#### Nút “Chọn…” cạnh Thư mục kết quả

Chọn thư mục dùng để lưu các lần build. Mỗi lần đóng gói tạo thư mục con riêng bên trong đó. Nút này không mở đầu ra đã build; dùng **Mở kết quả** cho việc đó.

#### Nút “Chọn…” cạnh Ảnh / icon

Chọn ảnh hoặc file `.ico`. Ở bước này công cụ chỉ lưu đường dẫn; chuyển ảnh sang ICO diễn ra khi bấm **ĐÓNG GÓI** trên Windows. Muốn bỏ icon đã chọn, xóa nội dung ô đường dẫn bằng bàn phím. Không có nút xóa icon riêng.

#### Nút “Thêm file dữ liệu”

1. Bấm nút và chọn một hoặc nhiều file ảnh, JSON, văn bản hoặc tài nguyên cần kèm ứng dụng.
2. Xem số mục và danh sách đường dẫn trong log.
3. Bấm thêm lần nữa nếu cần bổ sung file khác.

Mỗi file được đặt ở gốc bundle theo tên file. Chọn nhiều file bằng Ctrl/Shift trong hộp thoại nếu hệ điều hành hỗ trợ. Không dùng nút này để cài thư viện Python.

#### Nút “Thêm thư mục dữ liệu”

Chọn một thư mục tài nguyên, ví dụ `assets`. Công cụ thêm thư mục đó vào danh sách và giữ tên `assets` bên trong bundle. Bấm lại để thêm thư mục khác. Chỉ chọn thư mục tài nguyên cần thiết; không chọn cả venv hoặc thư mục kết quả build.

#### Nút “Bỏ dữ liệu đã chọn”

Xóa **toàn bộ** danh sách file/thư mục dữ liệu đã thêm, đưa bộ đếm về `0 mục`. Không xóa dữ liệu gốc trên ổ đĩa, không xóa source và không bỏ ảnh/icon ở ô riêng. Bản hiện tại chưa có nút bỏ từng mục: để bỏ một mục, xóa danh sách rồi thêm lại các mục cần giữ.

#### Nút “Cài công cụ”

1. Chọn đúng **Python / venv** trước.
2. Bấm nút để chạy pip cài `pyinstaller` và `Pillow` vào môi trường đó.
3. Chờ trạng thái hoàn tất và dòng thông báo thành công trong log.
4. Nếu lỗi, đọc thông báo pip; kiểm tra mạng, Python và quyền ghi.

Không tự tạo venv, không tự cài `requirements.txt` và không đóng gói ngay sau khi cài xong. Khi chuyển sang venv khác, cần bảo đảm công cụ cũng được cài trong venv mới.

#### Nút “ĐÓNG GÓI”

1. Kiểm tra source, môi trường Python, tên, thư mục kết quả và các tùy chọn.
2. Bấm nút. Ứng dụng kiểm tra đầu vào, tạo thư mục cho lần build, chuyển icon nếu cần rồi chạy PyInstaller.
3. Theo dõi log; trong lúc xử lý các nút bị khóa để tránh thao tác chồng nhau.
4. Chỉ lấy đầu ra khi log báo **THÀNH CÔNG** và có đường dẫn ứng dụng.

Nút này không tự cài công cụ bị thiếu. Nếu thiếu, bấm **Cài công cụ** sau khi lần build kết thúc rồi đóng gói lại. Không có thanh phần trăm tiến độ hoặc nút hủy trong bản hiện tại.

#### Nút “Mở kết quả”

Mở thư mục của lần build gần nhất trong phiên chạy hiện tại. Vào thư mục `dist` để lấy ứng dụng. Nút không tự chạy EXE và không mở trực tiếp thư mục `dist`.

Nếu lần build gần nhất lỗi, nút vẫn có thể mở thư mục lần đó để xem dữ liệu/log còn lại. Nếu chưa build hoặc vừa khởi động lại trình đóng gói, chương trình báo chưa có thư mục build; nó không tự tìm các kết quả từ phiên trước.

### Hai ô chọn chế độ

- **Một file duy nhất:** bật để tạo một file thực thi chính; tắt để tạo ứng dụng dạng thư mục. Khi tắt, cần giữ và phân phối cả thư mục ứng dụng trong `dist`.
- **Ẩn console (ứng dụng GUI):** bật cho ứng dụng giao diện như Tkinter. Tắt khi source dùng `input()`, cần xem `print()` hoặc cần đọc lỗi chạy từ terminal.

Thay đổi các ô này chỉ có hiệu lực ở lần build tiếp theo; không sửa ứng dụng đã build trước đó.

## 7. Tạo icon từ ảnh

Trên Windows:

1. Chọn PNG, JPG/JPEG, WebP, BMP hoặc GIF trong ô **Ảnh / icon**.
2. Bấm **ĐÓNG GÓI**.
3. Pillow đọc ảnh, xử lý hướng ảnh theo EXIF, chuyển RGBA và đặt ảnh vào khung vuông 256×256.
4. Ảnh giữ tỷ lệ; vùng dư trong suốt. Ảnh nhỏ không được chủ động phóng lớn để lấp đầy khung.
5. Lưu `application.ico` với các kích thước 16, 24, 32, 48, 64, 128 và 256 pixel.
6. Truyền ICO đã tạo cho PyInstaller.

GIF dùng khung hình đầu tiên. File `.ico` được sử dụng trực tiếp. Ảnh gốc không bị sửa.

Chức năng tự chuyển sang ICO chỉ chạy trên Windows. Việc đọc định dạng ảnh còn phụ thuộc Pillow trong môi trường đã chọn.

Icon này được gắn vào file thực thi. Icon cửa sổ Tkinter khi chạy có thể cần được đặt riêng bằng `iconbitmap()` hoặc `iconphoto()` trong source ứng dụng; trình đóng gói không chèn lệnh đó vào source.

## 8. Dữ liệu đi kèm và hidden imports

Ví dụ:

- Chọn riêng `settings.json`: file được đưa vào gốc bundle.
- Chọn thư mục `assets`: nội dung nằm dưới `assets` trong bundle.
- Chọn riêng `assets/logo.png`: file được đưa vào gốc bundle, không tự giữ đường dẫn `assets/logo.png`.

Chọn cả thư mục nếu source cần giữ cấu trúc thư mục đó. Tránh chọn nhiều tài nguyên có cùng đường dẫn đích. Công cụ không có chức năng đặt lại đường dẫn đích hoặc xử lý xung đột tài nguyên.

Source cần tự xác định đường dẫn tài nguyên đúng khi chạy sau đóng gói. Thêm dữ liệu không tự sửa các lệnh mở file đang dùng đường dẫn tuyệt đối hoặc phụ thuộc thư mục làm việc.

**Hidden imports** dùng cho module được nạp động mà PyInstaller chưa phát hiện. Đây là tên module Python, không phải lệnh `pip`, và không tự cài module vào venv. Chỉ nhập tên module thực sự cần cho dự án.

## 9. Kết quả được lưu ở đâu?

Mỗi lần build tạo một thư mục riêng có dạng `<ten_ung_dung>_<hau_to_ngau_nhien>` trong thư mục kết quả.

| Đường dẫn bên trong lần build | Nội dung |
| --- | --- |
| `dist/<ten>.exe` | EXE Windows ở chế độ một file |
| `dist/<ten>/<ten>.exe` | EXE Windows ở chế độ một thư mục |
| `build/` | Dữ liệu trung gian của PyInstaller |
| `<ten>.spec` | Cấu hình build do PyInstaller sinh |
| `build.log` | Output của tiến trình PyInstaller, khi bước này đã bắt đầu và log được tạo |
| `application.ico` | Icon chuyển đổi từ ảnh trên Windows, nếu có |

Nếu dùng chế độ một thư mục, phân phối **toàn bộ thư mục `dist/<ten>`**, không chỉ file EXE.

Log cài đặt công cụ và lỗi chuyển icon chỉ hiển thị trong giao diện, không được ghi vào `build.log`. Nếu chuyển icon lỗi trước khi chạy PyInstaller, `build.log` có thể chưa tồn tại dù giao diện có in đường dẫn dự kiến.

## 10. Ví dụ: đóng gói Git Identity Manager

| Trường | Giá trị |
| --- | --- |
| Source chính | `git_identity_manager.py` |
| Tên ứng dụng | `GitIdentityManager` |
| Python / venv | Python của môi trường build đã chuẩn bị |
| Một file duy nhất | Bật |
| Ẩn console | Bật |
| Ảnh / icon | Chọn ảnh bất kỳ phù hợp hoặc để trống |
| Hidden imports | Có thể để trống cho lần build đầu |

Sau khi build, chạy EXE trong `dist`. Máy đích vẫn cần cài Git trong PATH vì Git Identity Manager gọi chương trình Git bên ngoài; PyInstaller không tự đóng gói Git.

## 11. Xử lý lỗi

| Hiện tượng | Kiểm tra và xử lý |
| --- | --- |
| Không tìm thấy Python | Chọn đường dẫn đầy đủ đến `python.exe`, không chỉ nhập `python` |
| Thiếu PyInstaller hoặc Pillow | Chọn đúng Python rồi bấm Cài công cụ |
| Cài công cụ thất bại | Đọc log về pip, mạng và quyền ghi; dùng venv có quyền ghi |
| `ModuleNotFoundError` lúc chạy EXE | Kiểm tra thư viện đã cài trong môi trường build; bổ sung hidden import nếu là import động |
| Chuyển icon lỗi | Kiểm tra ảnh mở được và Pillow đã được cài trong đúng môi trường |
| Chạy EXE không thấy lỗi nhưng tự tắt | Build lại với tùy chọn Ẩn console tắt, rồi chạy từ CMD để xem lỗi |
| Không nhận nhập bàn phím bằng `input()` | Tắt Ẩn console và build lại |
| Thiếu ảnh/config lúc chạy | Kiểm tra tài nguyên đã được thêm và source dùng đúng đường dẫn |
| Chép EXE sang máy khác bị lỗi | Với onedir, chép cả thư mục; kiểm tra các chương trình ngoài và tài nguyên mà ứng dụng cần |

## 12. Giới hạn và kiểm thử

- Không có nút hủy build, tạo venv tự động, ký số EXE hoặc tạo bộ cài đặt.
- Khi đang xử lý, ứng dụng yêu cầu chờ trước khi đóng; tiến trình build/cài đặt không có timeout tổng. Chuyển icon có timeout 90 giây.
- Không tự dọn các thư mục build cũ. Có thể xóa thủ công sau khi đã giữ đầu ra cần dùng.
- Khi bản thân trình đóng gói chạy dưới dạng EXE, ô Python ban đầu để trống; phải chọn một Python đã cài trên máy.
- Đã kiểm tra cú pháp, tạo lệnh build và chuyển ảnh thành ICO nhiều kích thước có nền đệm trong suốt.
- Chưa kiểm thử tạo EXE hoặc giao diện trực tiếp trên Windows.
