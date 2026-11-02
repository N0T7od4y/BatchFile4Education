"""Quản lý user.name/user.email của Git bằng Tkinter.
Chạy: python git_identity_manager.py
Yêu cầu: Python 3.9+ có Tkinter, Git trong PATH. Không cần pip.
Global: tài khoản hiện tại. System: cấu hình chung của bản cài Git.
Không thay đổi commit cũ, tài khoản Windows hoặc thông tin đăng nhập.
"""
import os
import queue
import shutil
import subprocess
import tempfile
import threading
import tkinter as tk
from tkinter import ttk, messagebox
from tkinter.scrolledtext import ScrolledText

KEYS = ("user.name", "user.email")


def git_config(scope, *args):
    executable = shutil.which("git")
    if not executable:
        raise RuntimeError("Không tìm thấy Git. Cài Git, thêm vào PATH rồi mở lại ứng dụng.")
    return subprocess.run(
        [executable, "--no-pager", "config", scope, *args],
        cwd=tempfile.gettempdir(), stdin=subprocess.DEVNULL,
        capture_output=True, encoding="utf-8", errors="replace", timeout=15,
        creationflags=subprocess.CREATE_NO_WINDOW if os.name == "nt" else 0,
    )


def read_config(scope):
    values = {}
    for key in KEYS:
        r = git_config(scope, "--includes", "--get", key)
        if r.returncode not in (0, 1):
            raise RuntimeError(r.stderr.strip() or r.stdout.strip() or "Không đọc được cấu hình.")
        values[key] = r.stdout.rstrip("\r\n") if r.returncode == 0 else ""
    r = git_config(scope, "--includes", "--show-origin", "--get-regexp", r"^user\.(name|email)$")
    if r.returncode not in (0, 1):
        raise RuntimeError(r.stderr.strip() or "Không đọc được nguồn cấu hình.")
    return values, r.stdout.strip() or "Không có tên/email trong phạm vi này."


def update_config(scope, key, value=None):
    if key not in KEYS or scope not in ("--global", "--system"):
        raise ValueError("Trường hoặc phạm vi không hợp lệ.")
    deleting = value is None
    if not deleting and (not value.strip() or any(ord(c) < 32 or ord(c) == 127 for c in value)):
        raise ValueError("Giá trị không được rỗng hoặc chứa ký tự điều khiển.")
    args = ("--unset-all", key) if deleting else ("--replace-all", key, value.strip())
    r = git_config(scope, *args)
    if deleting and r.returncode == 5:
        return f"{key}: không có khóa trong file đích."
    if r.returncode != 0:
        raise RuntimeError(r.stderr.strip() or r.stdout.strip() or f"Git trả mã lỗi {r.returncode}.")
    return f"{key}: đã {'xóa khỏi' if deleting else 'ghi vào'} file đích."


class App(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Git Identity Manager — Tkinter")
        self.geometry("900x620")
        self.minsize(760, 540)
        self.results = queue.Queue()
        self.busy = False
        self.widgets = []
        self.values = {key: tk.StringVar() for key in KEYS}
        style = ttk.Style(self)
        if "clam" in style.theme_names():
            style.theme_use("clam")
        style.configure("TButton", padding=(12, 7))
        style.configure("Title.TLabel", font=("Segoe UI", 20, "bold"))
        body = ttk.Frame(self, padding=22)
        body.pack(fill="both", expand=True)
        body.columnconfigure(0, weight=1)
        body.rowconfigure(5, weight=1)
        ttk.Label(body, text="Quản lý danh tính Git", style="Title.TLabel").grid(row=0, sticky="w", pady=(0, 12))
        ttk.Label(body, text="Global: tài khoản hiện tại. System: cấu hình chung của bản cài Git, có thể cần quyền quản trị.\n"
                  "Repository, file include và biến môi trường có thể ghi đè. Không thay đổi tài khoản Windows hoặc commit cũ.",
                  wraplength=820).grid(row=1, sticky="ew", pady=(0, 14))
        self.scope = ttk.Combobox(body, state="readonly", values=["Global — tài khoản hiện tại", "System — bản cài Git"])
        self.scope.current(0)
        self.scope.grid(row=2, sticky="ew", pady=(0, 14))
        self.scope.bind("<<ComboboxSelected>>", lambda event: self.start_job())
        self.widgets.append(self.scope)
        form = ttk.Frame(body)
        form.grid(row=3, sticky="ew")
        form.columnconfigure(1, weight=1)
        for row, key in enumerate(KEYS):
            ttk.Label(form, text=key).grid(row=row, column=0, padx=(0, 12), pady=8)
            entry = ttk.Entry(form, textvariable=self.values[key], width=40)
            entry.grid(row=row, column=1, sticky="ew", pady=8)
            save = ttk.Button(form, text="Lưu", command=lambda k=key: self.save([k]))
            save.grid(row=row, column=2, padx=8)
            delete = ttk.Button(form, text="Xóa", command=lambda k=key: self.delete([k]))
            delete.grid(row=row, column=3)
            self.widgets.extend([entry, save, delete])
        actions = ttk.Frame(body)
        actions.grid(row=4, sticky="ew", pady=14)
        for label, callback in [("Đọc lại", self.start_job), ("Lưu cả hai", lambda: self.save(KEYS)),
                                ("Xóa cả hai", lambda: self.delete(KEYS))]:
            button = ttk.Button(actions, text=label, command=callback)
            button.pack(side="left", padx=(0, 10))
            self.widgets.append(button)
        self.log = ScrolledText(body, height=12, wrap="word", font=("Consolas", 10), state="disabled")
        self.log.grid(row=5, sticky="nsew")
        self.status = tk.StringVar(value="Sẵn sàng")
        ttk.Label(body, textvariable=self.status).grid(row=6, sticky="w", pady=(10, 0))
        self.protocol("WM_DELETE_WINDOW", self.close)
        self.after(100, self.poll)
        self.start_job()

    def save(self, keys):
        changes = []
        for key in keys:
            value = self.values[key].get().strip()
            if not value or any(ord(c) < 32 or ord(c) == 127 for c in value):
                messagebox.showerror("Giá trị không hợp lệ", f"{key}: nhập giá trị không rỗng, không chứa ký tự điều khiển.", parent=self)
                return
            changes.append((key, value))
        self.start_job(changes)

    def delete(self, keys):
        if messagebox.askyesno("Xác nhận xóa", f"Xóa {', '.join(keys)} trong {self.scope.get()}?", parent=self):
            self.start_job([(key, None) for key in keys])

    def start_job(self, changes=None):
        if self.busy:
            return
        scope = "--global" if self.scope.current() == 0 else "--system"
        self.busy = True
        for widget in self.widgets:
            widget.configure(state="disabled")
        self.status.set("Đang xử lý…")
        # Worker never accesses Tk widgets; all UI changes happen in poll().
        def work():
            messages, errors, state = [], False, None
            for key, value in changes or []:
                try:
                    messages.append(update_config(scope, key, value))
                except Exception as exc:
                    errors = True
                    messages.append(f"LỖI {key}: {exc}")
            try:
                state, details = read_config(scope)
                messages.append(f"\nPhạm vi: {scope}\n{details}")
            except Exception as exc:
                errors = True
                messages.append(f"LỖI đọc cấu hình: {exc}")
            if changes:
                messages.append("\nMỗi trường được xử lý riêng. Kiểm tra kết quả từng trường ở trên.\n"
                                "Git chỉ sửa file đích; giá trị từ file khác/include vẫn có thể còn hoặc ghi đè.")
            if errors:
                messages.append("\nKiểm tra Git trong PATH và quyền truy cập. Với System, có thể cần mở terminal bằng quyền quản trị.\n"
                                "Nếu hết thời gian chờ, đọc lại cấu hình trước khi thử tiếp.")
            self.results.put((state, "\n".join(messages), errors))
        threading.Thread(target=work, daemon=True).start()

    def poll(self):
        try:
            values, text, errors = self.results.get_nowait()
        except queue.Empty:
            pass
        else:
            for key in KEYS:
                self.values[key].set(values.get(key, "") if values is not None else "")
            self.log.configure(state="normal")
            self.log.delete("1.0", "end")
            self.log.insert("end", text)
            self.log.configure(state="disabled")
            for widget in self.widgets:
                widget.configure(state="readonly" if widget is self.scope else "normal")
            self.busy = False
            self.status.set("Có lỗi — xem chi tiết bên trên" if errors else "Hoàn tất")
        self.after(100, self.poll)

    def close(self):
        if self.busy:
            messagebox.showinfo("Đang xử lý", "Chờ thao tác Git hoàn tất trước khi đóng.", parent=self)
            return
        self.destroy()


if __name__ == "__main__":
    App().mainloop()
