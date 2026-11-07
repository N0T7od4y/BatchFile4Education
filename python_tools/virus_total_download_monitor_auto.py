"""VirusTotal Download Monitor (Windows 10/11)

Only observes files in a user-selected folder. It does not intercept network
traffic, block execution, or replace endpoint protection.

Requirements: pip install requests watchdog
Run:          python virus_total_download_monitor.py
"""

from __future__ import annotations

import csv
import hashlib
import os
import queue
import threading
import time
import tkinter as tk
import webbrowser
from dataclasses import dataclass, field
from pathlib import Path
from tkinter import filedialog, messagebox, ttk
from urllib.parse import quote, urlparse

import requests
from watchdog.events import FileSystemEventHandler
from watchdog.observers import Observer


API_ROOT = "https://www.virustotal.com/api/v3"
SMALL_LIMIT = 32 * 1024 * 1024
MAX_UPLOAD = 650 * 1024 * 1024
MIN_REQUEST_INTERVAL = 16.0  # 4 calls/minute or less
QUIET_SECONDS = 4.0           # no modification before hashing
POLL_INTERVAL = 30.0         # check uploaded analysis status
MAX_POLLS = 12
TEMP_SUFFIXES = (
    ".crdownload", ".part", ".partial", ".download",
    ".opdownload", ".filepart", ".aria2", ".tmp",
)


class ScanError(Exception):
    pass


class FileChanged(Exception):
    pass


def file_signature(path: Path):
    """Return (size, mtime) only for regular non-symlink files."""
    try:
        if path.is_symlink() or not path.is_file():
            return None
        stat = path.stat()
        return stat.st_size, stat.st_mtime_ns
    except OSError:
        return None


def sha256_file(path: Path, expected_signature, stop_event: threading.Event):
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        while True:
            if stop_event.is_set():
                raise ScanError("Đã dừng giám sát")
            block = handle.read(1024 * 1024)
            if not block:
                break
            digest.update(block)
    if file_signature(path) != expected_signature:
        raise FileChanged("File đã thay đổi trong lúc tính SHA-256")
    return digest.hexdigest()


@dataclass
class PendingFile:
    signature: tuple[int, int]
    last_seen: float
    force: bool = False


@dataclass
class PendingAnalysis:
    analysis_id: str
    sha256: str
    paths: set[str] = field(default_factory=set)
    next_check: float = 0.0
    polls: int = 0


class VTClient:
    """Serializes and rate-limits API calls from one worker thread."""

    def __init__(self, api_key: str, stopped: threading.Event, log):
        self.api_key = api_key
        self.stopped = stopped
        self.log = log
        self.session = requests.Session()
        self.session.headers.update({
            "x-apikey": api_key,
            "Accept": "application/json",
            "User-Agent": "VT-Download-Monitor/1.0",
        })
        self.next_request = 0.0

    def _wait(self, seconds: float):
        if self.stopped.wait(max(0, seconds)):
            raise ScanError("Giám sát đã dừng")

    def request(self, method: str, url: str, *, allow_404=False, **kwargs):
        for retry in range(4):
            self._wait(self.next_request - time.monotonic())
            self.next_request = time.monotonic() + MIN_REQUEST_INTERVAL
            try:
                response = self.session.request(
                    method, url, timeout=(12, 240), **kwargs
                )
            except requests.RequestException as exc:
                raise ScanError(f"Lỗi mạng/API: {exc}") from exc

            if response.status_code == 429:
                header = response.headers.get("Retry-After", "")
                try:
                    delay = min(300, max(60, int(header)))
                except ValueError:
                    delay = min(300, 60 * (retry + 1))
                self.log(f"API giới hạn yêu cầu (429); thử lại sau {delay}s")
                response.close()
                self._wait(delay)
                continue

            if allow_404 and response.status_code == 404:
                response.close()
                return None
            if response.status_code in (401, 403):
                response.close()
                raise ScanError("API key không hợp lệ hoặc không có quyền truy cập (401/403)")
            if not response.ok:
                status = response.status_code
                try:
                    error_info = response.json().get("error", {}).get("message", "")
                except ValueError:
                    error_info = ""
                response.close()
                raise ScanError(f"VirusTotal HTTP {status}: {str(error_info)[:180]}")
            try:
                payload = response.json()
            except ValueError as exc:
                raise ScanError("API trả về dữ liệu JSON không hợp lệ") from exc
            finally:
                response.close()
            return payload
        raise ScanError("API trả về 429 quá nhiều lần; ngừng thử file này")

    def get_file(self, sha: str):
        return self.request("GET", f"{API_ROOT}/files/{sha}", allow_404=True)

    def upload(self, path: Path, size: int):
        if size > MAX_UPLOAD:
            raise ScanError("File lớn hơn 650 MiB: vượt ngưỡng upload của API")

        target_url = f"{API_ROOT}/files"
        if size > SMALL_LIMIT:
            payload = self.request("GET", f"{API_ROOT}/files/upload_url")
            target_url = payload.get("data", "")
            parsed = urlparse(target_url)
            host = (parsed.hostname or "").lower()
            if parsed.scheme != "https" or not (
                host == "virustotal.com" or host.endswith(".virustotal.com")
            ):
                raise ScanError("URL upload trả về không đáp ứng yêu cầu HTTPS/VirusTotal")

        # IMPORTANT: multipart file handle must be reopened for EACH 429 retry.
        # Do not call request() here with a persistent open handle.
        for retry in range(4):
            self._wait(self.next_request - time.monotonic())
            self.next_request = time.monotonic() + MIN_REQUEST_INTERVAL
            try:
                with path.open("rb") as handle:
                    response = self.session.post(
                        target_url,
                        files={"file": (path.name, handle, "application/octet-stream")},
                        timeout=(12, 600),
                    )
            except (OSError, requests.RequestException) as exc:
                raise ScanError(f"Upload thất bại: {exc}") from exc

            if response.status_code == 429:
                header = response.headers.get("Retry-After", "")
                try:
                    delay = min(300, max(60, int(header)))
                except ValueError:
                    delay = min(300, 60 * (retry + 1))
                response.close()
                self.log(f"Upload bị giới hạn 429; thử lại sau {delay}s")
                self._wait(delay)
                # Large upload URLs are one-time; request a new one on retry.
                if size > SMALL_LIMIT:
                    info = self.request("GET", f"{API_ROOT}/files/upload_url")
                    target_url = info.get("data", "")
                    parsed = urlparse(target_url)
                    host = (parsed.hostname or "").lower()
                    if parsed.scheme != "https" or not (
                        host == "virustotal.com" or host.endswith(".virustotal.com")
                    ):
                        raise ScanError("URL upload mới không an toàn")
                continue
            if response.status_code in (401, 403):
                response.close()
                raise ScanError("API key không hợp lệ hoặc thiếu quyền upload (401/403)")
            if not response.ok:
                code = response.status_code
                response.close()
                raise ScanError(f"Upload thất bại (HTTP {code})")
            try:
                return response.json().get("data", {}).get("id", "")
            except (ValueError, AttributeError) as exc:
                raise ScanError("VirusTotal trả về ID phân tích không hợp lệ") from exc
            finally:
                response.close()
        raise ScanError("Upload bị giới hạn API quá nhiều lần")

    def reanalyse(self, sha: str):
        """Request a fresh AV analysis for an existing VT file with no AV stats."""
        payload = self.request("POST", f"{API_ROOT}/files/{sha}/analyse")
        return payload.get("data", {}).get("id", "")

    def get_analysis(self, analysis_id: str):
        encoded = quote(analysis_id, safe="")
        return self.request("GET", f"{API_ROOT}/analyses/{encoded}")

    def close(self):
        self.session.close()


class DownloadEvents(FileSystemEventHandler):
    def __init__(self, notify):
        self.notify = notify

    def on_created(self, event):
        if not event.is_directory:
            self.notify(event.src_path)

    def on_modified(self, event):
        if not event.is_directory:
            self.notify(event.src_path)

    def on_moved(self, event):
        if not event.is_directory:
            self.notify(event.dest_path)


class Scanner:
    def __init__(self, api_key: str, allow_upload: bool, ui_queue: queue.Queue):
        self.ui_queue = ui_queue
        self.stop_event = threading.Event()
        self.events = queue.Queue()
        self.queued_paths = set()
        self.queued_lock = threading.Lock()
        self.pending: dict[str, PendingFile] = {}
        self.finished_signatures: dict[str, tuple[int, int]] = {}
        self.hash_results: dict[str, tuple] = {}
        self.analyses: dict[str, PendingAnalysis] = {}
        self.sha_to_analysis: dict[str, str] = {}
        self.allow_upload = allow_upload
        self.client = VTClient(api_key, self.stop_event, self.log)
        self.worker = threading.Thread(target=self._run, daemon=True)

    def log(self, message: str):
        self.ui_queue.put(("log", message))

    def update(self, path: str, size=None, status="", malicious="", suspicious="", sha="", tag=""):
        self.ui_queue.put(("update", path, size, status, malicious, suspicious, sha, tag))

    def enqueue(self, raw_path, force=False):
        if self.stop_event.is_set():
            return
        path = os.path.abspath(os.fspath(raw_path))
        if path.lower().endswith(TEMP_SUFFIXES):
            return
        with self.queued_lock:
            if path in self.queued_paths and not force:
                return
            self.queued_paths.add(path)
        self.events.put((path, force))

    def start(self):
        self.worker.start()

    def stop(self):
        self.stop_event.set()

    def _accept_event(self, path, force):
        with self.queued_lock:
            self.queued_paths.discard(path)
        sig = file_signature(Path(path))
        if sig is None:
            return
        if not force and self.finished_signatures.get(path) == sig:
            return
        old = self.pending.get(path)
        self.pending[path] = PendingFile(
            sig, time.monotonic(), force or (old.force if old else False)
        )
        if old is None:
            self.update(path, sig[0], "Chờ tải xong")

    def _scan(self, path: str, item: PendingFile):
        file = Path(path)
        size = item.signature[0]
        sha = ""
        self.update(path, size, "Tính SHA-256")
        try:
            sha = sha256_file(file, item.signature, self.stop_event)
            self.update(path, size, "Đang tra cứu VirusTotal", sha=sha)

            if not item.force and sha in self.hash_results:
                status, mal, sus, tag = self.hash_results[sha]
                self.update(path, size, status + " (cache)", mal, sus, sha, tag)
                return
            if sha in self.sha_to_analysis:
                id_ = self.sha_to_analysis[sha]
                self.analyses[id_].paths.add(path)
                self.update(path, size, "Đang phân tích (trùng SHA)", sha=sha)
                return

            report = self.client.get_file(sha)
            if report is not None:
                stats = report.get("data", {}).get("attributes", {}).get(
                    "last_analysis_stats", {}
                )
                if not isinstance(stats, dict) or not stats:
                    if not self.allow_upload:
                        self.update(path, size, "VT chưa có kết quả AV (tắt quét mới)", sha=sha, tag="unknown")
                        return
                    self.update(path, size, "Đang yêu cầu VirusTotal quét mới", sha=sha)
                    analysis_id = self.client.reanalyse(sha)
                    if not analysis_id:
                        raise ScanError("VirusTotal không trả về ID phân tích lại")
                    self._track_analysis(path, sha, analysis_id)
                    self.update(path, size, "Đã gửi; đang chờ quét mới", sha=sha)
                    self.log(f"Đã yêu cầu quét lại: {file.name} | SHA-256: {sha}")
                    return
                self._show_result(path, size, sha, stats, "Báo cáo có sẵn")
                return

            if not self.allow_upload:
                status = "Không có báo cáo VT (đã tắt upload)"
                self.update(path, size, status, sha=sha, tag="unknown")
                self.hash_results[sha] = (status, "", "", "unknown")
                self.log(f"Không gửi file vì đã tắt upload tự động: {file.name}")
                return
            if size > MAX_UPLOAD:
                self.update(path, size, "Quá 650 MiB; không upload", sha=sha, tag="unknown")
                return
            if file_signature(file) != item.signature:
                raise FileChanged("File thay đổi trước khi upload")
            self.update(path, size, "Chưa có báo cáo; đang upload tự động", sha=sha)
            analysis_id = self.client.upload(file, size)
            if not analysis_id:
                raise ScanError("Không nhận được ID phân tích sau upload")
            self._track_analysis(path, sha, analysis_id)
            self.update(path, size, "Đã upload; đang chờ quét", sha=sha)
            self.log(f"Đã upload tự động: {file.name} | SHA-256: {sha}")
        except FileChanged:
            self.log(f"File vẫn đang thay đổi, sẽ thử lại: {file.name}")
            self.enqueue(path, force=True)
        except ScanError as exc:
            if not self.stop_event.is_set():
                self.update(path, size, "Lỗi API", sha=sha, tag="error")
                self.log(f"{file.name}: {exc}")
        except OSError as exc:
            if not self.stop_event.is_set():
                self.update(path, size, "Lỗi đọc file", sha=sha, tag="error")
                self.log(f"{file.name}: {exc}")
        except Exception as exc:
            if not self.stop_event.is_set():
                self.update(path, size, "Lỗi xử lý", sha=sha, tag="error")
                self.log(f"{file.name}: {type(exc).__name__}: {exc}")

    def _track_analysis(self, path: str, sha: str, analysis_id: str):
        self.analyses[analysis_id] = PendingAnalysis(
            analysis_id, sha, {path}, time.monotonic() + POLL_INTERVAL
        )
        self.sha_to_analysis[sha] = analysis_id

    def _show_result(self, path, size, sha, stats, origin):
        mal = int(stats.get("malicious", 0))
        sus = int(stats.get("suspicious", 0))
        if mal:
            status, tag = "Có phát hiện mã độc", "malicious"
        elif sus:
            status, tag = "Có dấu hiệu nghi ngờ", "suspicious"
        elif not sum(int(value) for value in stats.values() if isinstance(value, (int, float))):
            status, tag = "Chưa có kết quả từ AV", "unknown"
        else:
            status, tag = "Chưa bị phát hiện", "clean"
        self.update(path, size, status, str(mal), str(sus), sha, tag)
        self.hash_results[sha] = (status, str(mal), str(sus), tag)
        self.log(f"{origin}: {Path(path).name} | malicious={mal}, suspicious={sus}")

    def _poll_due_analysis(self):
        now = time.monotonic()
        for analysis_id, item in list(self.analyses.items()):
            if now < item.next_check:
                continue
            try:
                result = self.client.get_analysis(analysis_id)
                attributes = result.get("data", {}).get("attributes", {})
                if attributes.get("status") == "completed":
                    stats = attributes.get("stats", {})
                    for path in item.paths:
                        sig = file_signature(Path(path))
                        # The report is tied to SHA; a renamed/deleted file still has
                        # the correct submitted SHA and can retain its result row.
                        self._show_result(
                            path, sig[0] if sig else None,
                            item.sha256, stats, "Phân tích hoàn tất"
                        )
                    del self.analyses[analysis_id]
                    self.sha_to_analysis.pop(item.sha256, None)
                else:
                    item.polls += 1
                    if item.polls >= MAX_POLLS:
                        for path in item.paths:
                            self.update(path, status="Chưa xong; xem trên VT", sha=item.sha256, tag="unknown")
                        self.log(f"Phân tích lâu hơn {MAX_POLLS * int(POLL_INTERVAL)}s: {item.sha256}")
                        del self.analyses[analysis_id]
                        self.sha_to_analysis.pop(item.sha256, None)
                    else:
                        item.next_check = time.monotonic() + POLL_INTERVAL
            except ScanError as exc:
                if not self.stop_event.is_set():
                    self.log(f"Không lấy được trạng thái phân tích: {exc}")
                    item.polls += 1
                    item.next_check = time.monotonic() + max(60, POLL_INTERVAL)
                    if item.polls >= MAX_POLLS:
                        for path in item.paths:
                            self.update(path, status="Lỗi lấy kết quả", sha=item.sha256, tag="error")
                        del self.analyses[analysis_id]
                        self.sha_to_analysis.pop(item.sha256, None)
            return  # One analysis per worker cycle, to keep other files responsive

    def _process_ready_file(self):
        now = time.monotonic()
        for path, item in list(self.pending.items()):
            if now - item.last_seen < QUIET_SECONDS:
                continue
            sig = file_signature(Path(path))
            if sig is None:
                del self.pending[path]
                continue
            if sig != item.signature:
                item.signature = sig
                item.last_seen = now
                continue
            del self.pending[path]
            if not item.force and self.finished_signatures.get(path) == sig:
                continue
            self.finished_signatures[path] = sig
            self._scan(path, item)
            return

    def _run(self):
        try:
            while not self.stop_event.is_set():
                # Collect events rapidly, then process stable files sequentially.
                try:
                    path, force = self.events.get(timeout=0.4)
                    self._accept_event(path, force)
                    for _ in range(199):
                        try:
                            path, force = self.events.get_nowait()
                        except queue.Empty:
                            break
                        self._accept_event(path, force)
                except queue.Empty:
                    pass
                if not self.stop_event.is_set():
                    try:
                        self._poll_due_analysis()
                        self._process_ready_file()
                    except Exception as exc:
                        self.log(f"Lỗi nền: {type(exc).__name__}: {exc}")
        finally:
            self.client.close()
            self.ui_queue.put(("worker_finished",))


class App:
    def __init__(self, root: tk.Tk):
        self.root = root
        root.title("VirusTotal • Download Monitor")
        root.geometry("1140x690")
        root.minsize(850, 550)
        self.api_key = tk.StringVar()
        self.folder = tk.StringVar(value=str(Path.home() / "Downloads"))
        # Full automatic mode: unknown hashes are uploaded after session consent.
        self.allow_upload = tk.BooleanVar(value=True)
        self.ui_queue = queue.Queue()
        self.scanner: Scanner | None = None
        self.observer: Observer | None = None
        self.rows: dict[str, str] = {}
        self.record_data: dict[str, dict] = {}
        self.alive = True
        self.closing = False
        self._build()
        root.after(150, self._drain_ui)
        root.protocol("WM_DELETE_WINDOW", self._close)

    def _build(self):
        outer = ttk.Frame(self.root, padding=12)
        outer.pack(fill="both", expand=True)
        ttk.Label(outer, text="VIRUSTOTAL DOWNLOAD MONITOR", font=("Segoe UI", 16, "bold")).pack(anchor="w")
        ttk.Label(outer, text="Theo dõi file mới trong thư mục đã chọn • Không chặn thực thi • Không tự xóa file",
                  foreground="#555").pack(anchor="w", pady=(0, 10))

        config = ttk.LabelFrame(outer, text="Cấu hình", padding=10)
        config.pack(fill="x")
        config.columnconfigure(1, weight=1)
        ttk.Label(config, text="VirusTotal API key:").grid(row=0, column=0, sticky="w", padx=(0, 8), pady=4)
        self.key_entry = ttk.Entry(config, textvariable=self.api_key, show="•")
        self.key_entry.grid(row=0, column=1, sticky="ew", pady=4)
        ttk.Label(config, text="Thư mục theo dõi:").grid(row=1, column=0, sticky="w", padx=(0, 8), pady=4)
        self.folder_entry = ttk.Entry(config, textvariable=self.folder)
        self.folder_entry.grid(row=1, column=1, sticky="ew", pady=4)
        self.browse_button = ttk.Button(config, text="Chọn thư mục", command=self._choose_folder)
        self.browse_button.grid(row=1, column=2, padx=(8, 0), pady=4)
        self.upload_checkbox = ttk.Checkbutton(
            config, text="Tự động gửi file chưa có báo cáo lên VirusTotal để quét (mặc định BẬT)",
            variable=self.allow_upload
        )
        self.upload_checkbox.grid(row=2, column=1, columnspan=2, sticky="w", pady=3)

        tools = ttk.Frame(outer)
        tools.pack(fill="x", pady=10)
        self.start_button = ttk.Button(tools, text="▶ Bắt đầu giám sát", command=self._start)
        self.start_button.pack(side="left", padx=(0, 6))
        self.stop_button = ttk.Button(tools, text="■ Dừng", command=self._stop, state="disabled")
        self.stop_button.pack(side="left", padx=(0, 6))
        self.manual_button = ttk.Button(tools, text="Quét file thủ công", command=self._manual)
        self.manual_button.pack(side="left", padx=(0, 6))
        ttk.Button(tools, text="Xuất CSV", command=self._export).pack(side="left", padx=(0, 6))
        ttk.Button(tools, text="Xem báo cáo VT", command=self._open_report).pack(side="left")
        self.run_status = ttk.Label(tools, text="Đã dừng", foreground="#555")
        self.run_status.pack(side="right")

        table_area = ttk.LabelFrame(outer, text="Kết quả phát hiện", padding=6)
        table_area.pack(fill="both", expand=True)
        fields = ("name", "size", "status", "mal", "sus", "sha")
        self.tree = ttk.Treeview(table_area, columns=fields, show="headings", height=12)
        captions = {"name": "Tên file", "size": "Dung lượng", "status": "Trạng thái", "mal": "Malicious", "sus": "Suspicious", "sha": "SHA-256"}
        widths = {"name": 230, "size": 95, "status": 250, "mal": 85, "sus": 90, "sha": 270}
        for field_name in fields:
            self.tree.heading(field_name, text=captions[field_name])
            self.tree.column(field_name, width=widths[field_name], minwidth=70,
                             stretch=field_name in ("name", "status", "sha"))
        self.tree.tag_configure("malicious", foreground="#b00020")
        self.tree.tag_configure("suspicious", foreground="#a86400")
        self.tree.tag_configure("clean", foreground="#18814a")
        self.tree.tag_configure("error", foreground="#a00000")
        self.tree.tag_configure("unknown", foreground="#666666")
        yscroll = ttk.Scrollbar(table_area, orient="vertical", command=self.tree.yview)
        xscroll = ttk.Scrollbar(table_area, orient="horizontal", command=self.tree.xview)
        self.tree.configure(yscrollcommand=yscroll.set, xscrollcommand=xscroll.set)
        self.tree.grid(row=0, column=0, sticky="nsew")
        yscroll.grid(row=0, column=1, sticky="ns")
        xscroll.grid(row=1, column=0, sticky="ew")
        table_area.rowconfigure(0, weight=1)
        table_area.columnconfigure(0, weight=1)
        self.tree.bind("<Double-1>", lambda _evt: self._open_report())

        log_area = ttk.LabelFrame(outer, text="Nhật ký", padding=6)
        log_area.pack(fill="both", pady=(10, 0))
        self.log_text = tk.Text(log_area, height=6, wrap="word", state="disabled", font=("Consolas", 9))
        self.log_text.pack(fill="both", expand=True)
        self._log("Nhập API key rồi Bắt đầu giám sát. File không có báo cáo được tự động gửi đi khi đã xác nhận.")

    def _log(self, line):
        self.log_text.configure(state="normal")
        self.log_text.insert("end", f"[{time.strftime('%H:%M:%S')}] {line}\n")
        self.log_text.see("end")
        self.log_text.configure(state="disabled")

    def _choose_folder(self):
        selected = filedialog.askdirectory(initialdir=self.folder.get())
        if selected:
            self.folder.set(selected)

    def _start(self):
        if self.scanner is not None:
            return
        api_key = self.api_key.get().strip()
        folder = Path(self.folder.get().strip()).expanduser()
        if not api_key:
            messagebox.showerror("Thiếu API key", "Hãy nhập VirusTotal API key.")
            return
        if not folder.is_dir():
            messagebox.showerror("Thư mục không hợp lệ", "Chọn một thư mục đang tồn tại.")
            return
        if self.allow_upload.get():
            proceed = messagebox.askyesno(
                "Xác nhận upload tự động",
                "Khi VirusTotal chưa có báo cáo, ứng dụng sẽ TỰ ĐỘNG tải "
                "toàn bộ nội dung file lên máy chủ VirusTotal để quét.\n\n"
                "File gửi lên có thể được chia sẻ hoặc lưu trữ bởi VirusTotal. "
                "Không giám sát thư mục có dữ liệu riêng tư hoặc nhạy cảm.\n\n"
                "Bạn có đồng ý bật chế độ này cho phiên giám sát hiện tại không?"
            )
            if not proceed:
                return
        scanner = Scanner(api_key, self.allow_upload.get(), self.ui_queue)
        observer = Observer()
        try:
            observer.schedule(DownloadEvents(scanner.enqueue), str(folder), recursive=True)
            observer.start()
            scanner.start()
        except Exception as exc:
            scanner.stop()
            if observer.is_alive():
                observer.stop()
            messagebox.showerror("Không thể giám sát", str(exc))
            return
        self.scanner = scanner
        self.observer = observer
        self.start_button.configure(state="disabled")
        self.stop_button.configure(state="normal")
        self.key_entry.configure(state="disabled")
        self.folder_entry.configure(state="disabled")
        self.browse_button.configure(state="disabled")
        self.upload_checkbox.configure(state="disabled")
        self.run_status.configure(text="● Đang giám sát", foreground="#18814a")
        self._log(f"Theo dõi {folder} (bao gồm thư mục con). Chỉ nhận sự kiện file mới/thay đổi từ lúc bắt đầu.")
        self._log("Tự động upload và quét file chưa có báo cáo: " + ("BẬT" if scanner.allow_upload else "TẮT"))

    def _stop(self):
        if self.scanner is None:
            return
        self.scanner.stop()
        if self.observer is not None:
            self.observer.stop()
            self.observer = None
        self.stop_button.configure(state="disabled")
        self.run_status.configure(text="Đang dừng...", foreground="#666")
        self._log("Yêu cầu dừng đã được gửi. Đang chờ thao tác API hiện tại kết thúc.")
        self.root.after(250, self._finish_stop)

    def _finish_stop(self):
        if self.scanner and self.scanner.worker.is_alive():
            if not self.closing:
                self.root.after(300, self._finish_stop)
            return
        self.scanner = None
        if not self.closing:
            self.start_button.configure(state="normal")
            self.key_entry.configure(state="normal")
            self.folder_entry.configure(state="normal")
            self.browse_button.configure(state="normal")
            self.upload_checkbox.configure(state="normal")
            self.run_status.configure(text="Đã dừng", foreground="#666")
            self._log("Đã dừng giám sát.")

    def _manual(self):
        if self.scanner is None or self.scanner.stop_event.is_set():
            messagebox.showinfo("Chưa chạy", "Hãy bật giám sát trước khi quét thủ công.")
            return
        file = filedialog.askopenfilename(title="Chọn file muốn tra cứu / quét")
        if file:
            self.scanner.enqueue(file, force=True)

    def _selected(self):
        selected = self.tree.selection()
        if not selected:
            messagebox.showinfo("Chưa chọn file", "Hãy chọn một file trong bảng kết quả.")
            return None
        values = self.tree.item(selected[0], "values")
        for path, iid in self.rows.items():
            if iid == selected[0]:
                return self.record_data.get(path)
        return None

    def _open_report(self):
        record = self._selected()
        if not record:
            return
        sha = record.get("sha", "")
        if not sha:
            messagebox.showinfo("Chưa có SHA-256", "File chưa được tính hash.")
            return
        webbrowser.open(f"https://www.virustotal.com/gui/file/{sha}/detection")

    def _export(self):
        if not self.record_data:
            messagebox.showinfo("Chưa có dữ liệu", "Chưa có kết quả để xuất.")
            return
        dest = filedialog.asksaveasfilename(defaultextension=".csv", filetypes=[("CSV", "*.csv")],
                                            initialfile="virustotal_monitor_results.csv")
        if not dest:
            return
        try:
            with open(dest, "w", newline="", encoding="utf-8-sig") as handle:
                writer = csv.DictWriter(handle, fieldnames=["path", "size_bytes", "status", "malicious", "suspicious", "sha"])
                writer.writeheader()
                writer.writerows({key: record.get(key, "") for key in writer.fieldnames}
                                 for record in self.record_data.values())
            self._log(f"Đã xuất CSV: {dest}")
        except OSError as exc:
            messagebox.showerror("Lỗi xuất CSV", str(exc))

    def _drain_ui(self):
        if not self.alive:
            return
        for _ in range(400):
            try:
                msg = self.ui_queue.get_nowait()
            except queue.Empty:
                break
            if msg[0] == "log":
                self._log(msg[1])
            elif msg[0] == "update":
                _, path, size, status, mal, sus, sha, tag = msg
                entry = self.record_data.setdefault(path, {
                    "path": path, "size_bytes": "", "status": "", "malicious": "",
                    "suspicious": "", "sha": ""
                })
                if size is not None:
                    entry["size_bytes"] = size
                if status:
                    entry["status"] = status
                if mal != "":
                    entry["malicious"] = mal
                if sus != "":
                    entry["suspicious"] = sus
                if sha:
                    entry["sha"] = sha
                pretty_size = (f"{entry['size_bytes'] / 1024 / 1024:.2f} MiB"
                               if isinstance(entry["size_bytes"], int) else "")
                values = (Path(path).name, pretty_size, entry["status"],
                          entry["malicious"], entry["suspicious"], entry["sha"])
                if path not in self.rows:
                    self.rows[path] = self.tree.insert("", 0, values=values, tags=(tag,) if tag else ())
                else:
                    iid = self.rows[path]
                    self.tree.item(iid, values=values,
                                   tags=(tag,) if tag else self.tree.item(iid, "tags"))
            elif msg[0] == "worker_finished":
                pass
        self.root.after(150, self._drain_ui)

    def _close(self):
        self.closing = True
        self.alive = False
        if self.scanner is not None:
            self.scanner.stop()
        if self.observer is not None:
            self.observer.stop()
        self.root.destroy()


def main():
    root = tk.Tk()
    try:
        ttk.Style().theme_use("clam")
    except tk.TclError:
        pass
    App(root)
    root.mainloop()


if __name__ == "__main__":
    main()
