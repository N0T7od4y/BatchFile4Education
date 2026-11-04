# Hugging Face Downloader — Repository, thư mục và file

## 1. Mục đích

`download_hf_folder.py` tải file từ repository **dataset, model hoặc Space** trên Hugging Face. Script không gắn với dataset cụ thể; `--repo` là tham số bắt buộc.

Có thể tải:

- Toàn bộ file của một repository, kể cả file ở gốc và trong mọi thư mục con.
- Một hoặc nhiều thư mục, duyệt đệ quy không đặt giới hạn độ sâu tùy ý.
- Một hoặc nhiều file riêng lẻ, bất kể extension.
- Kết hợp file và thư mục trong cùng lệnh.
- Phạm vi được lọc bằng mẫu include/exclude.

Script giữ nguyên đường dẫn tương đối từ gốc repository. Nội dung được tải dưới dạng file gốc: không tự giải nén ZIP/TAR, không chạy code, không chuyển đổi định dạng dataset. Công cụ này dành cho repository Hugging Face, không phải trình tải URL bất kỳ hay Hugging Face Storage Bucket.

## 2. Cài đặt

Sử dụng **Python 3.10 trở lên** và cài thư viện:

```powershell
python -m pip install -U "huggingface_hub>=1.0,<2"
```

Nếu môi trường mạng dùng SOCKS proxy và báo thiếu `socksio`, cài thêm `python -m pip install "httpx[socks]"`.

Mở terminal tại thư mục chứa script:

```powershell
python download_hf_folder.py --help
```

### Windows: môi trường riêng không cần activate

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -U "huggingface_hub>=1.0,<2"
.\.venv\Scripts\python.exe download_hf_folder.py --help
```

Thay `python` trong các lệnh sau bằng `.\.venv\Scripts\python.exe` nếu dùng cách này. Không cần thay đổi PowerShell Execution Policy.

### Linux/macOS

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -U 'huggingface_hub>=1.0,<2'
```

## 3. Bắt đầu nhanh

Trong ví dụ, `OWNER/REPO_NAME`, `data`, `README.md` là giá trị minh họa. Thay bằng ID và đường dẫn thực tế; các ví dụ tổng quát không khẳng định repo hay file tương ứng tồn tại.

**Tải toàn bộ repo:**

```powershell
python download_hf_folder.py --repo OWNER/REPO_NAME --all --output ./downloads/my_repo
```

**Tải một thư mục cùng mọi file/thư mục con:**

```powershell
python download_hf_folder.py --repo OWNER/REPO_NAME --folder data --output ./downloads/my_repo
```

**Chỉ tải một file:**

```powershell
python download_hf_folder.py --repo OWNER/REPO_NAME --file data/train.jsonl --output ./downloads/my_repo
```

**Tự nhận diện đường dẫn là file hay thư mục:**

```powershell
python download_hf_folder.py --repo OWNER/REPO_NAME --path data/train --output ./downloads/my_repo
```

Nếu chưa đăng nhập, script yêu cầu nhập token ẩn ngay trong terminal. Không cần chạy `hf auth login` riêng.

## 4. Đăng nhập tích hợp

Luồng mặc định:

1. Lấy token qua thư viện Hugging Face, gồm token đã lưu hoặc `HF_TOKEN`.
2. Kiểm tra tài khoản bằng `whoami()`.
3. Khi không có token hoặc bị từ chối với HTTP 401/403, yêu cầu nhập personal access token bằng `getpass`.
4. Kiểm tra token mới, lưu thông qua `huggingface_hub.login()` rồi tiếp tục tải.

Tạo token tại [Hugging Face — Tokens](https://huggingface.co/settings/tokens). Dùng quyền Read hoặc fine-grained có quyền đọc repo đích. Repo private cần tài khoản được cấp quyền; repo gated có thể yêu cầu chấp nhận điều kiện hoặc được duyệt trước.

Bản này đăng nhập bằng **token nhập ẩn**, không tự mở trình duyệt. Không truyền token bằng tham số dòng lệnh, không ghi token vào source. Thư viện lưu thông tin đăng nhập tại vị trí cấu hình Hugging Face của người dùng, ngoài thư mục tải.

### Đổi token hoặc tài khoản

```powershell
python download_hf_folder.py --repo OWNER/REPO_NAME --all --output ./downloads/my_repo --force-login
```

`--force-login` bỏ qua token cũ cho lần chạy này và yêu cầu nhập token mới. Script truyền token vừa nhập trực tiếp vào các yêu cầu API; không sửa `HF_TOKEN` của terminal/hệ thống. Nếu terminal vẫn có `HF_TOKEN` cũ, lần chạy sau không dùng `--force-login` có thể sử dụng lại token đó.

### Tải repo công khai không cần đăng nhập

```powershell
python download_hf_folder.py --repo OWNER/REPO_NAME --all --output ./downloads/public_repo --anonymous
```

`--anonymous` không gửi token ngay cả khi máy đã đăng nhập. Không kết hợp với `--force-login`.

### Chạy tự động / CI / tác vụ không tương tác

Cấp `HF_TOKEN` qua cơ chế secrets của môi trường chạy hoặc sử dụng token đã lưu dưới đúng tài khoản hệ điều hành. Sau đó chạy lệnh tải thông thường. Repo công khai có thể dùng `--anonymous`.

Nếu thiếu token hợp lệ và không có terminal tương tác, script báo lỗi thay vì chờ nhập. Không dùng `--force-login` trong trường hợp này. Lỗi mạng khi kiểm tra token không bị coi mặc định là token sai.

## 5. Chọn đúng repository và đường dẫn

| Loại | Ví dụ URL repo | `--repo` | `--repo-type` |
| --- | --- | --- | --- |
| Dataset | `https://huggingface.co/datasets/OWNER/NAME` | `OWNER/NAME` | `dataset` |
| Model | `https://huggingface.co/OWNER/NAME` | `OWNER/NAME` | `model` |
| Space | `https://huggingface.co/spaces/OWNER/NAME` | `OWNER/NAME` | `space` |

`--repo` nhận ID, không nhận URL đầy đủ. Với đường dẫn xem file dạng `.../blob/main/data/a.json`, dùng `--file data/a.json --revision main`. Với thư mục `.../tree/main/data`, dùng `--folder data --revision main`.

Đường dẫn trên Hub phân biệt chữ hoa/thường; dùng dấu `/` giữa các cấp. Không tự sửa chính tả. Ví dụ `preprocessed` và `preproccessed` là hai tên khác nhau. Khi nhập sai, script dừng trước bước tải.

## 6. Các lệnh usage

### Nhiều thư mục, bao gồm thư mục sâu

```powershell
python download_hf_folder.py --repo OWNER/REPO_NAME --folder data/train --folder data/test --output ./downloads/my_repo
```

### Nhiều file riêng lẻ

```powershell
python download_hf_folder.py --repo OWNER/REPO_NAME --file README.md --file data/train.jsonl --output ./downloads/my_repo
```

### Kết hợp thư mục và file

```powershell
python download_hf_folder.py --repo OWNER/REPO_NAME --folder data/train --file README.md --output ./downloads/my_repo
```

### Nhiều đường dẫn tự nhận diện

```powershell
python download_hf_folder.py --repo OWNER/REPO_NAME --path data/train --path README.md --output ./downloads/my_repo
```

Lặp lại cờ cho mỗi đường dẫn; không ghép tên bằng dấu phẩy. File nằm trong nhiều phạm vi chỉ được đưa vào kế hoạch tải một lần. Nếu một đường dẫn được yêu cầu không tồn tại hoặc sai kiểu file/folder, script dừng trước khi tải nội dung.

### Tải cả repository model hoặc Space

```powershell
python download_hf_folder.py --repo OWNER/MODEL_NAME --repo-type model --all --output ./downloads/my_model
python download_hf_folder.py --repo OWNER/SPACE_NAME --repo-type space --all --output ./downloads/my_space
```

Đây là tải file tại một revision, không phải clone lịch sử Git. Tải file model không đồng nghĩa cài đặt/chạy model; tải Space không đồng nghĩa triển khai Space.

### Tải tất cả file từ gốc

Ưu tiên `--all`. Các cách tương đương được hỗ trợ:

```powershell
python download_hf_folder.py --repo OWNER/REPO_NAME --folder . --output ./downloads/my_repo
python download_hf_folder.py --repo OWNER/REPO_NAME --path / --output ./downloads/my_repo
```

Không kết hợp `--all` với `--folder`, `--file` hoặc `--path`. Nếu không chọn phạm vi, script báo lỗi, không tự tải toàn bộ repo.

### Chỉ lấy một số loại file

```powershell
python download_hf_folder.py --repo OWNER/REPO_NAME --all --include "*.jsonl" --include "*.parquet" --output ./downloads/selected
```

### Bỏ qua một số đường dẫn

```powershell
python download_hf_folder.py --repo OWNER/REPO_NAME --folder data --exclude "data/tmp/*" --exclude "*.zip" --output ./downloads/selected
```

Quy tắc lọc:

- Chọn phạm vi file/thư mục trước, sau đó mới áp dụng bộ lọc.
- Nhiều `--include` có quan hệ **hoặc**; không có include nghĩa là giữ tất cả file trong phạm vi.
- `--exclude` được ưu tiên: file khớp exclude luôn bị loại.
- Mẫu khớp với **đường dẫn đầy đủ tương đối từ gốc repo**, dùng `fnmatchcase`, phân biệt chữ hoa/thường.
- `*` khớp cả dấu `/`: `*.json` có thể khớp file JSON ở mọi cấp. Đây không phải cơ chế glob của shell; không cần `**` để duyệt sâu.
- Bọc mẫu trong dấu nháy để shell không mở rộng chúng trước.
- `--file`/`--folder`/`--path` là tên chính xác, không phải glob. Ví dụ `--file "a[1].txt"` chỉ chọn tên đó.

### Xem trước danh sách và dung lượng

```powershell
python download_hf_folder.py --repo OWNER/REPO_NAME --folder data --dry-run --output ./downloads/my_repo
```

`--dry-run` vẫn kết nối Hub và xác thực, nhưng không tải nội dung file hoặc tạo thư mục output. Đăng nhập có thể lưu token. Tổng bytes là dung lượng tất cả file được chọn, không phải dung lượng còn phải tải, dung lượng sau giải nén hay yêu cầu đĩa chính xác gồm file tạm.

### Branch, tag và commit

```powershell
python download_hf_folder.py --repo OWNER/REPO_NAME --all --revision BRANCH_NAME --output ./downloads/branch_copy
python download_hf_folder.py --repo OWNER/REPO_NAME --all --revision TAG_NAME --output ./downloads/tag_copy
python download_hf_folder.py --repo OWNER/REPO_NAME --all --revision COMMIT_SHA --output ./downloads/commit_copy
```

Thay các giá trị viết hoa bằng revision thực tế. Script chuyển revision thành commit SHA một lần rồi dùng cùng SHA cho việc liệt kê và tải, tránh lấy lẫn phiên bản nếu branch thay đổi giữa chừng.

### Folder lớn và tải lại sau gián đoạn

```powershell
python download_hf_folder.py --repo OWNER/REPO_NAME --folder data --output "D:\HF Downloads\my_repo" --workers 4 --retries 3
```

- API duyệt cây file có phân trang; chỉ duyệt cây thư mục được chọn thay vì buộc liệt kê toàn repo khi chọn một nhánh.
- Lập danh sách metadata trước khi tải; bộ nhớ tăng theo số file, không theo tổng bytes nội dung. Không có cam kết hỗ trợ số lượng file vô hạn.
- Tối đa `--workers` tác vụ tải file đang được lên lịch đồng thời. Cơ chế tải nội bộ/Xet có thể tạo thêm kết nối mạng; workers không phải giới hạn băng thông.
- Retry bổ sung cho lỗi transport, timeout, HTTP 429 và 5xx, với khoảng chờ tăng dần tối đa 30 giây. Thư viện có thể có retry riêng.
- Lỗi riêng một file được in dưới dạng `FAILED: ...`; các file khác tiếp tục. Lỗi trong bước lập danh sách làm dừng trước tải.
- Sau gián đoạn, chạy lại cùng lệnh và output; thư viện tận dụng dữ liệu tải trước đó. Giữ metadata cache để hỗ trợ việc này. Không có cờ `--resume` riêng.
- Để tiếp tục đúng phiên bản trước, lấy SHA đã in và truyền `--revision SHA_DO`. Chạy lại với `main` có thể lấy commit mới.
- Ctrl+C dừng lên lịch tiếp; tác vụ đang truyền có thể cần thời gian kết thúc trước khi chương trình thoát.

### Buộc tải lại

```powershell
python download_hf_folder.py --repo OWNER/REPO_NAME --file data/train.jsonl --output ./downloads/my_repo --force-download
```

Cờ này có thể tải lại file dù đã có cache. Nó không xóa file dư ở output.

### Ví dụ với dataset đã dùng trước đây

```powershell
python download_hf_folder.py --repo IAP492G12/IAP492_Dataset_G12 --folder preprocessed --output ./downloaded_data
```

Hoặc tải toàn bộ repository đó:

```powershell
python download_hf_folder.py --repo IAP492G12/IAP492_Dataset_G12 --all --output ./downloaded_data/full_repo
```

## 7. Bảng tham số

| Tham số | Mặc định | Chức năng |
| --- | --- | --- |
| `--repo` | Bắt buộc | ID repository |
| `--repo-type` | `dataset` | `dataset`, `model`, `space` |
| `--revision` | `main` | Branch, tag hoặc commit |
| `--all` | Tắt | Toàn bộ repo |
| `--folder` | Không có | Thư mục đệ quy; lặp được |
| `--file` | Không có | File chính xác; lặp được |
| `--path` | Không có | Tự nhận diện file/folder; lặp được |
| `--include` | Không lọc | Mẫu đường dẫn cần giữ; lặp được |
| `--exclude` | Không lọc | Mẫu đường dẫn cần loại; lặp được |
| `--output` | `./downloaded_data` | Thư mục cha lưu file |
| `--workers` | `4` | Số tác vụ tải file song song; tối thiểu 1 |
| `--retries` | `3` | Số lần thử thêm khi lỗi tạm thời; tối thiểu 0 |
| `--dry-run` | Tắt | Liệt kê kế hoạch, không tải nội dung |
| `--force-download` | Tắt | Buộc thư viện tải lại |
| `--force-login` | Tắt | Nhập token mới |
| `--anonymous` | Tắt | Không gửi token, chỉ dành cho truy cập công khai |
| `-h`, `--help` | — | In hướng dẫn |

## 8. Đầu ra và xác minh

| File trên Hub | Output | File trên máy |
| --- | --- | --- |
| `README.md` | `./copy` | `./copy/README.md` |
| `data/train/a.json` | `./copy` | `./copy/data/train/a.json` |

Ngay cả khi chỉ chọn `--folder data/train`, cấu trúc `data/train/` vẫn được giữ. `--output` luôn là thư mục, không phải tên file đích. Bọc đường dẫn có dấu cách trong dấu nháy.

Sau mỗi lượt tải, script kiểm tra file tồn tại và kích thước bytes bằng metadata của Hub. Nếu không khớp, thử tải buộc lại một lượt, rồi báo lỗi nếu vẫn sai. Đây **không phải kiểm tra checksum nội dung độc lập**: file hỏng nhưng cùng kích thước có thể không được phát hiện bởi phép kiểm tra này.

Hugging Face có thể tạo metadata tải xuống dưới `output/.cache/huggingface/`. Script không xóa các file cũ ngoài phạm vi tải. Dùng output riêng cho repo/revision khác nhau để tránh ghi đè file trùng tên.

## 9. Giới hạn và xử lý lỗi

- Không tái tạo thư mục rỗng không được Hub biểu diễn bằng file.
- Không sửa tên sai, không tự đổi tên file để hợp Windows. Tên bị Windows cấm và một số đường dẫn không an toàn sẽ làm dừng; không bỏ qua âm thầm.
- File có tên không biểu diễn được trên hệ thống file đích có thể tải thất bại. Repo hợp lệ trên Linux không nhất thiết lưu nguyên tên được trên Windows.
- Không hỗ trợ flatten cấu trúc, đổi tên file đích, giải nén, đồng bộ xóa file dư hoặc tải lịch sử Git.
- Không báo tổng tiến độ theo bytes toàn repo; có thanh tiến độ số file và tiến độ do thư viện cung cấp.
- Repo chứa đường dẫn `.cache/huggingface` bị từ chối để tránh đè metadata tải xuống.

| Lỗi | Cách kiểm tra |
| --- | --- |
| Thiếu dependency | Cài bằng đúng Python dùng chạy script |
| HTTP 401/403 | Kiểm tra token, quyền repo/gated; dùng `--force-login` trong terminal tương tác |
| Repository/revision/path không tìm thấy | Kiểm tra repo ID, repo-type, revision và đường dẫn; HTTP 404 cũng có thể liên quan quyền truy cập |
| Không có file phù hợp | Kiểm tra include/exclude hoặc thư mục không có file |
| HTTP 429/5xx, timeout | Retry có giới hạn; nếu còn lỗi, kiểm tra mạng, chạy lại hoặc giảm workers |
| Lỗi ghi file/OSError | Kiểm tra dung lượng, quyền ghi và tên/độ dài đường dẫn |
| Không có terminal tương tác | Cấp token qua secrets hoặc dùng `--anonymous` cho repo công khai |

Thông báo lỗi mạng chỉ in loại lỗi và mã HTTP nếu có; không in nguyên exception để tránh lộ token hoặc URL tải có chữ ký.

| Exit code | Ý nghĩa |
| --- | --- |
| `0` | Thành công, dry-run thành công hoặc help |
| `1` | Lỗi dependency/API/tải/ghi file hoặc có file tải thất bại |
| `2` | Lỗi tham số, lựa chọn hoặc không có file phù hợp; không thể đăng nhập tương tác |
| `130` | Hủy bằng Ctrl+C trong quá trình xử lý |

PowerShell xem mã thoát bằng `$LASTEXITCODE`; Bash dùng `echo $?` ngay sau lệnh.

## 10. Kiểm thử và tham khảo

Đã kiểm tra cú pháp Python và chạy 15 kiểm thử tự động bằng API giả lập: chọn toàn repo, đệ quy, nhiều phạm vi trùng nhau, tên file chứa ký tự glob, lọc, sai kiểu, đường dẫn không an toàn, cố định commit, kiểm tra kích thước/tải sửa, tiếp tục sau lỗi file, retry, anonymous, lỗi xác thực do mạng và dry-run không tạo output.

Chạy kiểm thử trong bộ ZIP:

```powershell
python -m unittest -v test_hf_downloader.py
```

Tài liệu chính thức dùng để đối chiếu API:

- [HfApi: repo_info, get_paths_info, list_repo_tree](https://huggingface.co/docs/huggingface_hub/package_reference/hf_api)
- [hf_hub_download](https://huggingface.co/docs/huggingface_hub/package_reference/file_download)
- [Authentication](https://huggingface.co/docs/huggingface_hub/package_reference/authentication)

**Thay đổi so với bản trước:** bắt buộc chỉ định repo và phạm vi; bỏ mặc định gắn với dataset riêng; bổ sung tải cả repo/file/nhiều đường dẫn, lọc, dry-run, anonymous, retry và kiểm tra kích thước. Các lệnh cũ có đủ `--repo --folder --output` vẫn dùng được.
