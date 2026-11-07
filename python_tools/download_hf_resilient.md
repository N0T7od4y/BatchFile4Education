# Hugging Face Resilient Downloader

Công cụ dòng lệnh Python để tải **toàn bộ repository**, **một hoặc nhiều thư mục (đệ quy)**, hoặc **các file cụ thể** từ Hugging Face Hub. Script được thiết kế cho trường hợp số lượng file lớn, kết nối không ổn định và việc tải cần được tiếp tục qua nhiều lần chạy.

**Script:** `download_hf_resilient(1).py`  
**Loại repository hỗ trợ:** Dataset (`dataset`), Model (`model`), Space (`space`).  
**Mặc định:** tải từ nhánh `main`, dùng 4 worker và lưu trong `./downloaded_data`.

> Tài liệu này mô tả những chức năng có trong chính file Python đi kèm. Các giá trị đường dẫn, tên repository và kết quả minh họa bên dưới là **ví dụ sử dụng**, không phải kết quả chạy thực tế.

## 1. Chức năng chính

- Tải toàn bộ repository (`--all`), thư mục và tất cả thư mục con (`--folder`), file riêng lẻ (`--file`) hoặc tự nhận diện loại đường dẫn (`--path`).
- Chọn đồng thời nhiều thư mục/file bằng cách lặp lại tham số; loại bỏ đường dẫn file trùng trong danh sách tải.
- Lọc đường dẫn bằng mẫu glob `--include`, `--exclude` (loại trừ có độ ưu tiên cao hơn).
- Tải song song nhiều file với `--workers`.
- **Tiếp tục sau gián đoạn:** nếu file đích đã tồn tại và kích thước khớp kích thước do Hub công bố, bỏ qua file đó khi chạy lại.
- **Thử lại khi gặp lỗi tạm thời:** lỗi kết nối, timeout, một số mã HTTP (`408`, `425`, `5xx`) và `FileExistsError`.
- **Xử lý HTTP 429:** các worker dùng chung cơ chế chờ; mặc định thử lại vô hạn cho đến khi yêu cầu thành công, gặp lỗi khác, hoặc người dùng dừng chạy.
- Nếu một file vẫn lỗi sau số lần thử cho phép, ghi lỗi và **chuyển sang file tiếp theo**, không dừng toàn bộ đợt tải.
- Xuất danh sách lỗi dạng JSONL để kiểm tra và chạy lại.
- Cho phép xem trước danh sách file và tổng dung lượng bằng `--dry-run`.
- Hỗ trợ token Hugging Face có sẵn, đăng nhập bằng token trong terminal hoặc tải repository công khai bằng `--anonymous`.

### Phạm vi và giới hạn quan trọng

- Tiếp tục tải hoạt động ở **mức file**: file đã hợp lệ được bỏ qua; việc tiếp tục tải dở từng byte của một file phụ thuộc vào cơ chế cache/download bên dưới của thư viện `huggingface_hub`.
- Script kiểm tra file sẵn có bằng **kích thước**, không tự so sánh checksum/hash nội dung. File sai nội dung nhưng trùng kích thước có thể bị coi là hợp lệ.
- Khi chạy lại, nên giữ **cùng `--output` và cùng `--revision`/commit**. Nếu nhánh `main` thay đổi giữa hai lần chạy, script có thể chọn commit khác; file cũ có kích thước bằng file mới vẫn có thể được bỏ qua.
- Script tải **file gốc của repository**, không tự nén cả repository thành một file ZIP và không tự giải nén archive đã tải.
- Các lỗi khi **xác thực, xác định repository hoặc liệt kê file** có thể kết thúc chương trình; chế độ bỏ qua lỗi áp dụng ở giai đoạn tải từng file.

## 2. Yêu cầu môi trường

- Python 3 (khuyến nghị **Python 3.10 trở lên**).
- Internet truy cập được `huggingface.co` và hệ thống tải file của Hugging Face.
- Có quyền ghi vào thư mục đích và đủ dung lượng lưu trữ.
- Các thư viện Python: `huggingface_hub` phiên bản `>=1.0,<2`, `tqdm`, `httpx`.

Cài đặt từ PowerShell, CMD hoặc terminal:

```bash
python -m pip install -U "huggingface_hub>=1.0,<2" tqdm httpx
```

Kiểm tra Python:

```bash
python --version
```

> Các module khác mà script import, như `argparse`, `json`, `pathlib`, `threading`, `concurrent.futures`, đều thuộc thư viện chuẩn Python.

### 2.1. Tùy chọn tạo virtual environment (Windows PowerShell)

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -U "huggingface_hub>=1.0,<2" tqdm httpx
.\.venv\Scripts\python.exe ".\download_hf_resilient(1).py" --help
```

Các lệnh trên **không cần kích hoạt** môi trường ảo, nên tránh được lỗi PowerShell chặn `Activate.ps1`.

### 2.2. Linux / Kali

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -U "huggingface_hub>=1.0,<2" tqdm httpx
python 'download_hf_resilient(1).py' --help
```

> Nếu đổi tên file thành `download_hf_resilient.py`, hãy dùng tên mới trong các lệnh tương ứng. Do tên gốc chứa dấu ngoặc tròn, nên đặt tên file trong dấu nháy khi gọi từ terminal.

## 3. Chuẩn bị repository và đăng nhập

### 3.1. Xác định repository ID

Ví dụ URL một dataset:

```text
https://huggingface.co/datasets/IAP492G12/IAP492_Dataset_G12
```

Giá trị đưa vào `--repo` là **ID**, không phải URL:

```text
IAP492G12/IAP492_Dataset_G12
```

Script mặc định coi repository là `dataset`. Đối với model hoặc Space, cần thêm `--repo-type model` hoặc `--repo-type space`.

### 3.2. Đăng nhập tự động qua terminal

Nếu chưa có token hợp lệ, script chạy trong terminal tương tác sẽ hướng dẫn tạo token tại:

<https://huggingface.co/settings/tokens>

Chọn token có quyền **Read** phù hợp với repository cần tải. Sau đó script yêu cầu nhập:

```text
HF token:
```

Token được nhập ẩn bằng `getpass`, được kiểm tra qua tài khoản Hugging Face và lưu bằng cơ chế chính thức của `huggingface_hub`; script không ghi token vào file kết quả.

Để buộc nhập token mới:

```powershell
python ".\download_hf_resilient(1).py" --repo IAP492G12/IAP492_Dataset_G12 --all --force-login
```

Để dùng tài khoản/token đã lưu, **không cần** thêm `--force-login`.

**Bảo mật:** không ghi token trực tiếp vào mã nguồn, README, ảnh chụp màn hình hoặc lệnh chia sẻ công khai. Với môi trường không có terminal tương tác, chuẩn bị token bằng cơ chế `HF_TOKEN`/secret của môi trường chạy trước khi thực thi.

### 3.3. Tải công khai không dùng token

```powershell
python ".\download_hf_resilient(1).py" --repo IAP492G12/IAP492_Dataset_G12 --all --anonymous
```

`--anonymous` chỉ sử dụng được nếu repository và các file cần truy cập là công khai. `--anonymous` và `--force-login` không thể dùng cùng nhau.

## 4. Cú pháp chung

```text
python "download_hf_resilient(1).py" --repo OWNER/REPO [lựa chọn] [cấu hình]
```

**Bắt buộc:** `--repo` và **ít nhất một** trong các tùy chọn chọn dữ liệu: `--all`, `--folder`, `--file`, `--path`.

### 4.1. Bảng tham số

| Tham số | Ý nghĩa | Mặc định / ghi chú |
|---|---|---|
| `--repo OWNER/NAME` | ID repository Hugging Face | Bắt buộc; không dùng URL |
| `--repo-type TYPE` | `dataset`, `model` hoặc `space` | `dataset` |
| `--revision REV` | Nhánh, tag hoặc mã commit | `main` |
| `--all` | Chọn toàn bộ file trong repository | Không kết hợp với `--folder`, `--file`, `--path` |
| `--folder PATH` | Chọn toàn bộ file trong một thư mục và các thư mục con | Có thể lặp lại |
| `--file PATH` | Chọn đúng một file | Có thể lặp lại |
| `--path PATH` | Tự xác định PATH là file hay thư mục | Có thể lặp lại |
| `--include GLOB` | Chỉ lấy những file khớp mẫu | Có thể lặp lại; xét trên đường dẫn đầy đủ tính từ gốc repo |
| `--exclude GLOB` | Bỏ các file khớp mẫu | Có thể lặp lại; ưu tiên hơn `--include` |
| `--output DIR` | Thư mục gốc trên máy lưu dữ liệu | `./downloaded_data` |
| `--workers N` | Số file tải song song | `4`; tối thiểu `1` |
| `--retries N` | Số lần **thử lại thêm** cho lỗi tạm thời không phải 429 | `5`; tối thiểu `0` |
| `--rate-limit-retries N` | Số lần thử lại thêm khi HTTP 429 | `0` = không giới hạn |
| `--rate-limit-max-wait N` | Giới hạn số giây chờ **mỗi lần** gặp 429 | `180`; tối thiểu `1` |
| `--error-log FILE` | Đường dẫn file JSONL ghi lỗi | Mặc định cạnh thư mục `--output` |
| `--dry-run` | Chỉ liệt kê, thống kê, không tải | Không tạo thư mục tải ở bước này |
| `--force-download` | Tải lại dù file đã có/cached | Không áp dụng cơ chế bỏ qua file theo kích thước |
| `--force-login` | Nhập token mới | Không dùng cùng `--anonymous` |
| `--anonymous` | Không gửi token | Chỉ cho nguồn công khai |
| `--help` | In hướng dẫn tham số của chương trình | Có thể dùng độc lập |

**Quy ước PATH trên Hugging Face:** là đường dẫn **tương đối trong repo**, ví dụ `preprocessed/train/data.jsonl`. Không truyền `https://...`, không truyền đường dẫn ổ `C:\...`, không bắt đầu bằng `/`, không sử dụng `..` để đi lên thư mục. Dấu `\` trong giá trị PATH được chuẩn hóa thành `/`.

## 5. Các ví dụ sử dụng thực tế

Các lệnh ví dụ dùng PowerShell, repository ID `IAP492G12/IAP492_Dataset_G12` và tên file script gốc. Đặt PowerShell tại thư mục chứa script trước khi chạy.

### Ví dụ 1 — Tải toàn bộ dataset

```powershell
python ".\download_hf_resilient(1).py" --repo IAP492G12/IAP492_Dataset_G12 --all --output ".\downloaded_data"
```

Dùng khi muốn tải mọi file của dataset và giữ nguyên cấu trúc thư mục. Không cần dùng `--folder` kèm theo.

### Ví dụ 2 — Tải toàn bộ thư mục `preprocessed`, bao gồm các thư mục con

```powershell
python ".\download_hf_resilient(1).py" --repo IAP492G12/IAP492_Dataset_G12 --folder preprocessed --output ".\downloaded_data"
```

Giả sử repository có cấu trúc:

```text
preprocessed/
├── benign/
│   ├── a.json
│   └── nested/b.json
└── malicious/
    └── c.json
```

Khi tải xong thành công, cấu trúc ở máy sẽ là:

```text
downloaded_data/
└── preprocessed/
    ├── benign/
    │   ├── a.json
    │   └── nested/b.json
    └── malicious/
        └── c.json
```

**Lưu ý:** tên thư mục phải đúng như trên Hub. `preprocessed` và `preproccessed` là hai chuỗi khác nhau; script không tự sửa lỗi chính tả.

### Ví dụ 3 — Tải nhiều thư mục cùng lúc

```powershell
python ".\download_hf_resilient(1).py" --repo IAP492G12/IAP492_Dataset_G12 --folder preprocessed --folder raw_original --output ".\dataset_full"
```

Mỗi `--folder` được xử lý đệ quy. Những file có mặt trong nhiều lựa chọn không được tải hai lần trong cùng danh sách công việc.

### Ví dụ 4 — Tải một file cụ thể

```powershell
python ".\download_hf_resilient(1).py" --repo IAP492G12/IAP492_Dataset_G12 --file README_DATASET_PREPROCESSING.md --output ".\downloaded_data"
```

Dùng `--file` nếu đã biết đường dẫn file chính xác.

### Ví dụ 5 — Tải kết hợp file và thư mục

```powershell
python ".\download_hf_resilient(1).py" --repo IAP492G12/IAP492_Dataset_G12 --folder preprocessed --file README_DATASET_PREPROCESSING.md --output ".\downloaded_data"
```

`--file`, `--folder`, `--path` có thể dùng chung; riêng `--all` không được kết hợp với các lựa chọn này.

### Ví dụ 6 — Để script tự nhận diện file hoặc thư mục

```powershell
python ".\download_hf_resilient(1).py" --repo IAP492G12/IAP492_Dataset_G12 --path preprocessed --path README_DATASET_PREPROCESSING.md
```

`--path` tra cứu trên repository: nếu là file thì lấy file, nếu là thư mục thì duyệt đệ quy.

### Ví dụ 7 — Chỉ tải file JSON và JSONL

```powershell
python ".\download_hf_resilient(1).py" --repo IAP492G12/IAP492_Dataset_G12 --folder preprocessed --include "*.json" --include "*.jsonl" --output ".\json_only"
```

Các mẫu `--include` được nối theo điều kiện **HOẶC**: file chỉ cần khớp một trong các mẫu. Mẫu được kiểm tra trên đường dẫn tính từ gốc repo, không chỉ trên basename.

### Ví dụ 8 — Loại bỏ các file không muốn tải

```powershell
python ".\download_hf_resilient(1).py" --repo IAP492G12/IAP492_Dataset_G12 --all --exclude "*.zip" --exclude "*.tar.gz" --output ".\without_archives"
```

Nếu vừa có `--include` vừa có `--exclude`, file khớp loại trừ vẫn bị bỏ qua.

### Ví dụ 9 — Xem trước số lượng và dung lượng trước khi tải

```powershell
python ".\download_hf_resilient(1).py" --repo IAP492G12/IAP492_Dataset_G12 --folder preprocessed --dry-run
```

Ví dụ định dạng hiển thị (giả định):

```text
Repo: IAP492G12/IAP492_Dataset_G12 [dataset] | commit: <commit-sha>
Dang liet ke file...
Da chon: 3 file, 15,000 bytes (0.000 GiB).
Dich: C:\...\downloaded_data
Dung luong tren la tong file duoc chon, khong phai so byte con phai tai.
1000    preprocessed/benign/a.json
4000    preprocessed/benign/nested/b.json
10000   preprocessed/malicious/c.json
```

Dung lượng là **tổng kích thước file đã chọn theo thông tin Hub**, không phải lượng dữ liệu cần tải thêm sau khi trừ các file có sẵn. `--dry-run` vẫn cần truy cập repository để lấy danh sách file, vì vậy vẫn có bước xác thực (trừ khi dùng `--anonymous`).

### Ví dụ 10 — Tải chậm nhưng ổn định hơn khi thường xuyên gặp giới hạn request

```powershell
python ".\download_hf_resilient(1).py" --repo IAP492G12/IAP492_Dataset_G12 --folder preprocessed --workers 2 --retries 10 --rate-limit-retries 0 --rate-limit-max-wait 180 --output ".\downloaded_data"
```

Ý nghĩa: dùng 2 worker thay vì 4; lỗi tạm thời không phải 429 được thử lại tối đa 10 lần; HTTP 429 tiếp tục chờ rồi thử lại không giới hạn; mỗi lần chờ 429 tối đa 180 giây.

> Giảm `--workers` có thể giúp giảm áp lực request nhưng không bảo đảm tránh HTTP 429. Việc server chấp nhận request còn phụ thuộc hạn mức thực tế.

### Ví dụ 11 — Chạy lại sau khi mạng mất hoặc có file lỗi

Chạy **lại đúng lệnh đã dùng**, không đổi thư mục đích:

```powershell
python ".\download_hf_resilient(1).py" --repo IAP492G12/IAP492_Dataset_G12 --folder preprocessed --output ".\downloaded_data"
```

Chương trình sẽ duyệt lại danh sách và:

1. Bỏ qua file có sẵn nếu kích thước khớp (`skipped`).
2. Tải file chưa có hoặc kích thước không khớp.
3. Khi một file tải lỗi sau retry, ghi vào JSONL rồi tiếp tục file khác.

Đây là cách thông thường để tiếp tục một lần tải lớn. Không cần xóa thư mục đã tải trước đó.

### Ví dụ 12 — Buộc tải lại các file

```powershell
python ".\download_hf_resilient(1).py" --repo IAP492G12/IAP492_Dataset_G12 --folder preprocessed --force-download --output ".\downloaded_data"
```

Chỉ dùng khi muốn tải lại thực sự, ví dụ cần thay các file nghi ngờ sai nội dung nhưng có cùng kích thước.

### Ví dụ 13 — Chỉ định file ghi lỗi

```powershell
python ".\download_hf_resilient(1).py" --repo IAP492G12/IAP492_Dataset_G12 --all --output ".\downloaded_data" --error-log ".\logs\hf_failed.jsonl"
```

### Ví dụ 14 — Tải một model thay vì dataset

```powershell
python ".\download_hf_resilient(1).py" --repo OWNER/MODEL_NAME --repo-type model --all --output ".\models\MODEL_NAME"
```

Thay `OWNER/MODEL_NAME` bằng ID model có thật trên Hugging Face. Tương tự, dùng `--repo-type space` cho Space.

### Ví dụ 15 — Cố định commit để tải nhất quán

```powershell
python ".\download_hf_resilient(1).py" --repo IAP492G12/IAP492_Dataset_G12 --revision COMMIT_SHA --folder preprocessed --output ".\downloaded_data"
```

`COMMIT_SHA` phải được thay bằng commit ID thật mà bạn có quyền truy cập. Script tự dùng một commit cố định **trong một lần chạy**, nhưng truyền `--revision` bằng commit giúp đảm bảo lần chạy tiếp theo vẫn tham chiếu đúng phiên bản dữ liệu đó.

## 6. Kết quả đầu ra

Với lệnh:

```powershell
python ".\download_hf_resilient(1).py" --repo IAP492G12/IAP492_Dataset_G12 --folder preprocessed --output ".\downloaded_data"
```

Cấu trúc minh họa:

```text
thu_muc_lam_viec/
├── download_hf_resilient(1).py
├── downloaded_data/
│   ├── preprocessed/
│   │   ├── benign/
│   │   └── malicious/
│   └── .cache/
│       └── huggingface/       # metadata/cache có thể do huggingface_hub quản lý
└── downloaded_data_failed.jsonl
```

- **File tải xuống:** nằm dưới `--output`, giữ đường dẫn tương đối như trên repository.
- **Thư mục `.cache/huggingface`:** thư viện tải có thể tạo metadata quản lý; không nên xóa trong khi tải.
- **File lỗi mặc định:** `<tên thư mục output>_failed.jsonl`, được tạo **cạnh** thư mục output, không nằm trong thư mục output.

Nếu thư mục output là `D:\HF\data`, đường dẫn log mặc định là `D:\HF\data_failed.jsonl`.

### 6.1. Ví dụ thông báo tiến trình và tổng kết

Đây là ví dụ **minh họa định dạng**, không phải kết quả đã đo:

```text
Repo: IAP492G12/IAP492_Dataset_G12 [dataset] | commit: <commit-sha>
Dang liet ke file...
Da chon: 100 file, 1,000,000 bytes (0.001 GiB).
Dich: C:\...\downloaded_data
Files: 100%|...| 100/100 [...]
KET QUA: 98 thanh cong (trong do 60 da ton tai), 2 loi, tong 100 file.
Danh sach file loi: C:\...\downloaded_data_failed.jsonl
Chay lai cung lenh/output de thu lai cac file loi; file du kich thuoc se duoc bo qua.
```

**Cách hiểu số liệu:**

- `100 file`: số file được chọn và đưa vào kết quả thống kê.
- `98 thanh cong`: bao gồm cả file tải thành công và file đã có hợp lệ.
- `60 da ton tai`: thuộc nhóm thành công, được bỏ qua nhờ kiểm tra kích thước.
- `2 loi`: các file bị từ chối do đường dẫn không hợp lệ hoặc lỗi tải sau retry.
- Thanh tiến trình đếm **file đã được xử lý**, gồm thành công, đã có và thất bại; 100% không nhất thiết đồng nghĩa 100% tải thành công.

### 6.2. Nội dung JSONL lỗi

Mỗi dòng là một JSON object riêng:

```jsonl
{"path":"preprocessed/benign/sample1.json","error":"ConnectTimeout"}
{"path":"preprocessed/malicious/sample2.json","error":"HTTPStatusError (HTTP 403)"}
```

Các trường do script xuất:

| Trường | Ý nghĩa |
|---|---|
| `path` | Đường dẫn file trên repository |
| `error` | Nhãn lỗi đã rút gọn, thường gồm tên loại lỗi và HTTP/WinError nếu có |

File log được **mở ở chế độ ghi mới (`w`) trong mỗi lần tải**, nên lần chạy tiếp theo sẽ ghi đè danh sách lỗi của lần trước. Nếu cần lưu lịch sử, hãy đổi `--error-log` hoặc sao lưu log cũ trước khi chạy lại.

## 7. Cơ chế retry, rate limit và bỏ qua lỗi

### 7.1. Lỗi tạm thời thông thường

Script nhận diện các lỗi như mất kết nối, timeout, `FileExistsError`, HTTP `408`, `425` và `500`–`599`, sau đó thử lại theo lịch chờ tăng dần, tối đa **30 giây/lần** cho nhóm lỗi này.

- `--retries 5` nghĩa là tối đa **5 lần thử lại sau lần thử ban đầu**, không phải tổng cộng 5 lần gọi.
- Nếu vẫn lỗi, file được đánh dấu `FAILED (bo qua)` và worker tiếp tục xử lý các file còn lại.
- Những lỗi không thuộc nhóm retry được bỏ qua trực tiếp ở bước tải file và ghi vào log.

### 7.2. HTTP 429 (Too Many Requests)

Khi một worker nhận HTTP 429:

1. Kiểm tra HTTP header `Retry-After` nếu có.
2. Áp dụng khoảng chờ tăng dần, có giới hạn `--rate-limit-max-wait` (mặc định 180 giây cho mỗi lần chờ).
3. Tạm dừng các **yêu cầu mới** từ các worker thông qua cổng chờ dùng chung.
4. Gửi lại request sau khi chờ.

Mặc định `--rate-limit-retries 0` nghĩa là **không giới hạn số lần retry 429**. Có thể giới hạn, ví dụ:

```powershell
python ".\download_hf_resilient(1).py" --repo IAP492G12/IAP492_Dataset_G12 --all --rate-limit-retries 20
```

Khi vượt giới hạn này, lỗi của file tải được ghi nhận và chuyển tiếp tới file khác. Nếu 429 xảy ra khi xác thực hoặc liệt kê repository, việc vượt giới hạn có thể khiến cả chương trình dừng.

**Lưu ý:** các request đang chạy dở không nhất thiết bị hủy ngay khi worker khác nhận 429; cơ chế chờ áp dụng trước các lần gọi tiếp theo.

### 7.3. Lỗi Windows `FileExistsError` / `WinError 183`

Script xem đây là lỗi có thể thử lại. Ngoài ra, nếu lỗi xuất hiện nhưng file đích đã có kích thước hợp lệ (ví dụ một quá trình khác vừa tạo xong file), script coi file đó là hoàn tất. Không bảo đảm xử lý được mọi xung đột quyền ghi hoặc mọi trường hợp chạy song song nhiều tiến trình trên cùng thư mục.

## 8. Quy trình đề xuất cho dataset lớn

**Bước 1.** Mở terminal tại thư mục chứa script, bảo đảm thư viện đã cài.

**Bước 2.** Kiểm tra đúng repo, thư mục và dung lượng bằng `--dry-run`:

```powershell
python ".\download_hf_resilient(1).py" --repo IAP492G12/IAP492_Dataset_G12 --folder preprocessed --dry-run
```

**Bước 3.** Tải vào một thư mục đích cố định, có thể giảm worker nếu thường gặp 429:

```powershell
python ".\download_hf_resilient(1).py" --repo IAP492G12/IAP492_Dataset_G12 --folder preprocessed --output "D:\HF\downloaded_data" --workers 2 --retries 10
```

**Bước 4.** Khi hoàn tất, kiểm tra dòng `KET QUA` và `D:\HF\downloaded_data_failed.jsonl`.

**Bước 5.** Nếu có lỗi hoặc bị gián đoạn, chạy lại **chính lệnh ở Bước 3**. File có kích thước hợp lệ sẽ không bị tải lại.

**Bước 6.** Đối với nghiên cứu cần tái lập chính xác phiên bản dataset, ghi lại giá trị `commit` in ở đầu log và dùng commit đó làm `--revision` ở lần chạy tiếp theo.

## 9. Xử lý sự cố thường gặp

| Hiện tượng | Nguyên nhân có thể | Cách kiểm tra / xử lý |
|---|---|---|
| `ModuleNotFoundError` hoặc `Thieu dependency` | Thiếu thư viện, cài sai Python environment | Chạy `python -m pip install -U "huggingface_hub>=1.0,<2" tqdm httpx` bằng cùng interpreter chạy script |
| `LOI: Khong tim thay: ...` | Sai tên file/thư mục, sai chữ hoa-thường, sai revision | Kiểm tra đường dẫn tương đối và tên trên Hub; ví dụ `preprocessed` thay vì `preproccessed` nếu đó là tên thực tế |
| Repo bị từ chối `401`/`403` | Token thiếu/hết quyền, repo riêng tư hoặc cần được cấp quyền | Kiểm tra quyền Read và quyền truy cập repo; thử `--force-login` với token hợp lệ |
| Script yêu cầu token dù muốn tải công khai | Không có token lưu sẵn; mặc định script chủ động xác thực | Thêm `--anonymous` nếu repo công khai |
| `HTTP 429` xuất hiện nhiều | Vượt giới hạn yêu cầu | Giảm `--workers`, cho script retry/chờ; cân nhắc giới hạn retry tùy yêu cầu vận hành |
| `FAILED (bo qua)` | Một file tải thất bại sau retry hoặc không thể ghi | Đọc JSONL lỗi, sửa nguyên nhân rồi chạy lại với cùng `--output` |
| Một file đã tải không được tải lại | Kích thước file đích trùng kích thước trên Hub | Dùng `--force-download` nếu cần tải lại hoàn toàn |
| Không có file phù hợp | Mẫu include/exclude loại hết hoặc không tồn tại file được chọn | Kiểm tra `--folder`, `--path`, glob và `--revision`; chạy `--dry-run` |
| Tên file không tương thích Windows | Có ký tự/tên thiết bị bị Windows cấm | File bị từ chối và ghi vào log; nên tải trên hệ điều hành hỗ trợ tên đó nếu thực sự cần |
| `--all` báo không được dùng chung với `--folder` | Hai chế độ chọn dữ liệu xung đột | Chỉ dùng `--all`, hoặc bỏ `--all` để chọn từng thư mục |
| Không thấy log lỗi cũ | Script ghi đè log mỗi lần tải | Sao lưu log hoặc dùng `--error-log` với đường dẫn riêng từng lần |
| Chưa có quyền ghi / hết dung lượng | Phân vùng đích không đủ chỗ hoặc thư mục bị chặn | Kiểm tra quyền, dung lượng đĩa và đường dẫn output |

## 10. Lưu ý về dữ liệu và an toàn

- Script tải file nhưng **không tự chạy, import hoặc cài đặt** mã nguồn bên trong repository được tải về.
- Chỉ tải từ repository mà bạn tin cậy. File tải xuống có thể chứa nội dung độc hại; không thực thi hoặc cài đặt chúng nếu chưa đánh giá an toàn.
- Không dùng `--force-download` khi muốn tiết kiệm băng thông và tiếp tục tải từ file đã có.
- Kiểm tra đủ dung lượng trên ổ đĩa, kể cả phần metadata/cache mà thư viện có thể tạo thêm.
- Giữ nguyên thư mục `--output` để tái sử dụng file cũ; không tự di chuyển từng file giữa hai lần tải nếu muốn kiểm tra tiếp tục chính xác.
- Nếu cần kiểm tra tính toàn vẹn theo hash, hãy xây dựng một bước xác minh riêng; script hiện tại **không** cung cấp báo cáo SHA256 cho file đã tải.

## 11. Mã thoát chương trình

| Mã | Ý nghĩa |
|---|---|
| `0` | Chạy thành công hoặc `--dry-run` hoàn tất; không có file lỗi ở lần tải thực tế |
| `1` | Có ít nhất một file lỗi sau tải hoặc gặp lỗi vận hành/dependency khác |
| `2` | Lỗi chọn đường dẫn/tham số hoặc đối tượng cần tải không hợp lệ |
| `130` | Người dùng hủy bằng `Ctrl+C` |

Đối với một đợt tải lớn, luôn đọc **dòng tổng kết và file JSONL**; mã thoát `1` có thể có nghĩa là vẫn có nhiều file tải thành công nhưng một số file còn lỗi.

## 12. Lệnh ngắn cần nhớ

```powershell
# Xem trợ giúp
python ".\download_hf_resilient(1).py" --help

# Tải toàn bộ repository
python ".\download_hf_resilient(1).py" --repo IAP492G12/IAP492_Dataset_G12 --all

# Tải cả cây thư mục preprocessed
python ".\download_hf_resilient(1).py" --repo IAP492G12/IAP492_Dataset_G12 --folder preprocessed

# Xem trước mà chưa tải
python ".\download_hf_resilient(1).py" --repo IAP492G12/IAP492_Dataset_G12 --folder preprocessed --dry-run

# Tải công khai, không cần đăng nhập
python ".\download_hf_resilient(1).py" --repo IAP492G12/IAP492_Dataset_G12 --all --anonymous

# Tải lại/tiếp tục (lặp lại lệnh tải cũ và cùng --output)
python ".\download_hf_resilient(1).py" --repo IAP492G12/IAP492_Dataset_G12 --folder preprocessed
```

---

**Tóm tắt:** Để tải cả `preprocessed` và tất cả thư mục con, dùng `--folder preprocessed`. Nếu quá trình tải bị ngắt hoặc có file lỗi, **chạy lại lệnh cũ với cùng `--output`**. Script bỏ qua các file có kích thước hợp lệ, retry lỗi tạm thời, chờ khi gặp 429 và ghi những file vẫn thất bại vào `*_failed.jsonl`.
