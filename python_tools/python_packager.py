"""Python Packager — một file Tkinter, Python 3.9+.
Chạy: python python_packager.py
Chọn đúng python.exe/venv đã cài các thư viện của source.
Bấm Cài công cụ lần đầu (cần mạng), sau đó Đóng gói.
Windows tạo EXE; Linux tạo binary Linux. Không biên dịch chéo hệ điều hành.
Mỗi lần build tạo thư mục riêng, không ghi đè bản cũ.
"""
import os
import queue
import re
import subprocess
import sys
import tempfile
import threading
from pathlib import Path
import tkinter as tk
from tkinter import ttk, filedialog, messagebox
from tkinter.scrolledtext import ScrolledText


# Executed using the selected Python/venv; Pillow is not required to open the GUI.
ICON_CONVERTER = r"""
import sys
from PIL import Image, ImageOps
with Image.open(sys.argv[1]) as source:
    source.seek(0)
    image = ImageOps.exif_transpose(source).convert('RGBA')
    image.thumbnail((256, 256), Image.Resampling.LANCZOS)
    canvas = Image.new('RGBA', (256, 256), (0, 0, 0, 0))
    canvas.alpha_composite(image, ((256-image.width)//2, (256-image.height)//2))
    canvas.save(sys.argv[2], format='ICO', sizes=[(16,16),(24,24),(32,32),(48,48),(64,64),(128,128),(256,256)])
"""


def make_command(python, source, name, job, onefile, windowed, icon, assets, hidden):
    cmd = [python, '-u', '-m', 'PyInstaller', '--noconfirm', '--noupx',
           '--onefile' if onefile else '--onedir', '--name', name,
           '--distpath', str(job / 'dist'), '--workpath', str(job / 'build'),
           '--specpath', str(job)]
    if windowed:
        cmd.append('--windowed')
    if icon:
        cmd.extend(['--icon', icon])
    for asset in assets:
        # Preserve a selected folder's name, place a selected file at bundle root.
        p = Path(asset)
        destination = p.name if p.is_dir() else '.'
        cmd.extend(['--add-data', f'{p}{os.pathsep}{destination}'])
    for module in hidden.split(','):
        if module.strip():
            cmd.extend(['--hidden-import', module.strip()])
    cmd.append(source)
    return cmd


class Packager(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title('Python → ứng dụng | Đóng gói nhanh')
        self.geometry('940x740')
        self.minsize(780, 620)
        self.events = queue.Queue()
        self.busy = False
        self.controls = []
        self.assets = []
        self.last_output = None
        self.python = tk.StringVar(value='' if getattr(sys, 'frozen', False) else sys.executable)
        self.source = tk.StringVar()
        self.output = tk.StringVar()
        self.name = tk.StringVar()
        self.icon = tk.StringVar()
        self.hidden = tk.StringVar()
        self.onefile = tk.BooleanVar(value=True)
        self.windowed = tk.BooleanVar(value=True)
        self.status = tk.StringVar(value='Chọn source để bắt đầu')
        style = ttk.Style(self)
        if 'clam' in style.theme_names(): style.theme_use('clam')
        style.configure('TButton', padding=(10, 6))
        root = ttk.Frame(self, padding=18)
        root.pack(fill='both', expand=True)
        root.columnconfigure(1, weight=1)
        root.rowconfigure(10, weight=1)
        ttk.Label(root, text='Đóng gói Python', font=('Segoe UI', 21, 'bold')).grid(row=0, column=0, columnspan=3, sticky='w', pady=(0, 12))
        self.field(root, 1, 'Python / venv', self.python, self.pick_python)
        self.field(root, 2, 'Source chính (.py)', self.source, self.pick_source)
        self.field(root, 3, 'Thư mục kết quả', self.output, self.pick_output)
        self.field(root, 4, 'Tên ứng dụng', self.name)
        self.field(root, 5, 'Ảnh / icon (tùy chọn)', self.icon, self.pick_icon)
        self.field(root, 6, 'Hidden imports', self.hidden)
        opts = ttk.Frame(root)
        opts.grid(row=7, column=0, columnspan=3, sticky='w', pady=10)
        for label, variable in [('Một file duy nhất', self.onefile), ('Ẩn console (ứng dụng GUI)', self.windowed)]:
            w = ttk.Checkbutton(opts, text=label, variable=variable)
            w.pack(side='left', padx=(0, 20)); self.controls.append(w)
        resources = ttk.Frame(root)
        resources.grid(row=8, column=0, columnspan=3, sticky='ew')
        for title, action in [('Thêm file dữ liệu', self.add_files), ('Thêm thư mục dữ liệu', self.add_folder), ('Bỏ dữ liệu đã chọn', self.clear_assets)]:
            self.button(resources, title, action).pack(side='left', padx=(0, 8))
        self.asset_label = ttk.Label(resources, text='0 mục')
        self.asset_label.pack(side='left')
        actions = ttk.Frame(root)
        actions.grid(row=9, column=0, columnspan=3, sticky='ew', pady=12)
        for title, action in [('Cài công cụ', self.install), ('ĐÓNG GÓI', self.build), ('Mở kết quả', self.open_output)]:
            self.button(actions, title, action).pack(side='left', padx=(0, 10))
        self.log = ScrolledText(root, height=14, state='disabled', wrap='word', font=('Consolas', 10))
        self.log.grid(row=10, column=0, columnspan=3, sticky='nsew')
        ttk.Label(root, textvariable=self.status).grid(row=11, column=0, columnspan=3, sticky='w', pady=8)
        ttk.Label(root, text='Dùng Python đã cài đủ thư viện của source. Hidden imports: tên module cách nhau bằng dấu phẩy.\n'
                  'Bỏ “Ẩn console” nếu chương trình dùng input()/terminal. One-folder thường khởi động nhanh hơn one-file.',
                  wraplength=870).grid(row=12, column=0, columnspan=3, sticky='w')
        self.protocol('WM_DELETE_WINDOW', self.close)
        self.after(80, self.poll)

    def button(self, parent, title, action):
        button = ttk.Button(parent, text=title, command=action)
        self.controls.append(button)
        return button

    def field(self, parent, row, title, variable, browse=None):
        ttk.Label(parent, text=title).grid(row=row, column=0, sticky='w', padx=(0, 14), pady=6)
        entry = ttk.Entry(parent, textvariable=variable)
        entry.grid(row=row, column=1, sticky='ew', pady=6)
        self.controls.append(entry)
        if browse: self.button(parent, 'Chọn…', browse).grid(row=row, column=2, padx=(10, 0))

    def pick_python(self):
        p = filedialog.askopenfilename(title='Chọn python.exe (không chọn pythonw.exe) hoặc Python trong venv')
        if p: self.python.set(p)

    def pick_source(self):
        p = filedialog.askopenfilename(filetypes=[('Python', '*.py *.pyw'), ('Tất cả', '*.*')])
        if p:
            self.source.set(p); self.name.set(Path(p).stem)
            if not self.output.get(): self.output.set(str(Path(p).parent / 'packaged'))

    def pick_output(self):
        p = filedialog.askdirectory()
        if p: self.output.set(p)

    def pick_icon(self):
        p = filedialog.askopenfilename(filetypes=[('Ảnh / icon', '*.ico *.png *.jpg *.jpeg *.webp *.bmp *.gif *.icns'), ('Tất cả', '*.*')])
        if p: self.icon.set(p)

    def add_files(self):
        self.add_assets(filedialog.askopenfilenames())

    def add_folder(self):
        p = filedialog.askdirectory()
        if p: self.add_assets([p])

    def add_assets(self, items):
        for p in items:
            if p not in self.assets: self.assets.append(p)
        self.asset_label.configure(text=f'{len(self.assets)} mục')
        self.append('Dữ liệu được chọn:\n' + '\n'.join(self.assets) + '\n')

    def clear_assets(self):
        self.assets.clear(); self.asset_label.configure(text='0 mục')
        self.append('Đã bỏ danh sách dữ liệu bổ sung.\n')

    def interpreter(self):
        p = Path(self.python.get().strip()).expanduser()
        if not p.is_file(): raise ValueError('Chọn đường dẫn đầy đủ đến Python trong môi trường chạy source.')
        if p.name.lower() == 'pythonw.exe': raise ValueError('Chọn python.exe để đọc được log build.')
        return str(p.resolve())

    def install(self):
        try: python = self.interpreter()
        except Exception as exc: return messagebox.showerror('Lỗi', str(exc))
        self.launch([python, '-u', '-m', 'pip', 'install', 'pyinstaller', 'Pillow'], Path.home(), None)

    def build(self):
        try:
            python = self.interpreter()
            source = Path(self.source.get().strip()).expanduser().resolve()
            if not source.is_file() or source.suffix.lower() not in ('.py', '.pyw'):
                raise ValueError('Chọn file source .py hoặc .pyw hợp lệ.')
            name = self.name.get().strip()
            if not re.fullmatch(r'[\w-][\w .-]*', name) or name.endswith(('.', ' ')):
                raise ValueError('Tên ứng dụng chỉ gồm chữ, số, dấu cách, gạch ngang, gạch dưới và dấu chấm; không kết thúc bằng dấu chấm.')
            if name.split('.')[0].upper() in {'CON', 'PRN', 'AUX', 'NUL', *[f'COM{i}' for i in range(1,10)], *[f'LPT{i}' for i in range(1,10)]}:
                raise ValueError('Tên này được Windows dành riêng.')
            icon = self.icon.get().strip()
            if icon:
                icon = str(Path(icon).expanduser().resolve())
                if not Path(icon).is_file(): raise ValueError('File icon không tồn tại.')
            for p in self.assets:
                if not Path(p).exists(): raise ValueError(f'Dữ liệu không tồn tại: {p}')
            if not self.output.get().strip(): raise ValueError('Chọn thư mục kết quả.')
            out = Path(self.output.get()).expanduser().resolve()
            out.mkdir(parents=True, exist_ok=True)
            # Isolated run directory prevents overwriting an earlier build.
            job = Path(tempfile.mkdtemp(prefix=name + '_', dir=out))
            cmd = make_command(python, str(source), name, job, self.onefile.get(), self.windowed.get(), icon, list(self.assets), self.hidden.get())
            exe = name + ('.exe' if os.name == 'nt' else '')
            artifact = job / 'dist' / exe if self.onefile.get() else job / 'dist' / name / exe
            self.launch(cmd, source.parent, (job, artifact), icon_source=icon)
        except Exception as exc:
            messagebox.showerror('Không thể đóng gói', str(exc))

    def launch(self, cmd, cwd, result, icon_source=''):
        if self.busy: return
        self.busy = True
        for w in self.controls: w.configure(state='disabled')
        self.status.set('Đang đóng gói…' if result else 'Đang cài PyInstaller và Pillow…')
        self.append('\nLệnh: ' + subprocess.list2cmdline(cmd) + '\n')
        def worker():
            code = -1
            try:
                env = os.environ.copy()
                env['PYTHONIOENCODING'] = 'utf-8'; env['PYTHONUNBUFFERED'] = '1'
                if result and icon_source and Path(icon_source).suffix.lower() != '.ico' and os.name == 'nt':
                    converted = result[0] / 'application.ico'
                    self.events.put(('log', 'Đang chuyển ảnh thành ICO…\n'))
                    conversion = subprocess.run(
                        [cmd[0], '-c', ICON_CONVERTER, icon_source, str(converted)],
                        env=env, stdin=subprocess.DEVNULL, capture_output=True,
                        text=True, encoding='utf-8', errors='replace', timeout=90,
                        creationflags=subprocess.CREATE_NO_WINDOW)
                    if conversion.returncode != 0:
                        raise RuntimeError('Không chuyển được icon. Bấm Cài công cụ để cài Pillow.\n' + conversion.stderr)
                    cmd[cmd.index('--icon') + 1] = str(converted)
                    self.events.put(('log', f'Icon đã tạo: {converted}\n'))
                with subprocess.Popen(cmd, cwd=cwd, env=env, stdin=subprocess.DEVNULL,
                                      stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                                      text=True, encoding='utf-8', errors='replace',
                                      creationflags=subprocess.CREATE_NO_WINDOW if os.name == 'nt' else 0) as process:
                    log_file = (result[0] / 'build.log').open('w', encoding='utf-8') if result else None
                    try:
                        for line in process.stdout:
                            if log_file: log_file.write(line)
                            self.events.put(('log', line))
                        code = process.wait()
                    finally:
                        if log_file: log_file.close()
            except Exception as exc: self.events.put(('log', f'LỖI: {exc}\n'))
            self.events.put(('done', (code, result)))
        threading.Thread(target=worker, daemon=True).start()

    def append(self, text):
        self.log.configure(state='normal'); self.log.insert('end', text)
        if int(self.log.index('end-1c').split('.')[0]) > 2500: self.log.delete('1.0', '501.0')
        self.log.see('end'); self.log.configure(state='disabled')

    def poll(self):
        for _ in range(150):
            try: kind, value = self.events.get_nowait()
            except queue.Empty: break
            if kind == 'log': self.append(value)
            else:
                code, result = value
                self.busy = False
                for w in self.controls: w.configure(state='normal')
                success = code == 0 and (result is None or result[1].is_file())
                if result: self.last_output = result[0]
                self.status.set('Hoàn tất' if success else 'Thất bại — xem log')
                if success:
                    self.append(f'\nTHÀNH CÔNG: {result[1]}\n' if result else '\nĐã cài PyInstaller và Pillow. Bạn có thể bấm ĐÓNG GÓI.\n')
                else:
                    self.append(f'\nKhông hoàn tất (mã {code}). Nếu thiếu PyInstaller, bấm Cài công cụ.\n')
                if result: self.append(f'Log đầy đủ: {result[0] / "build.log"}\n')
        self.after(80, self.poll)

    def open_output(self):
        p = self.last_output
        if not p or not p.exists(): return messagebox.showinfo('Kết quả', 'Chưa có thư mục build.')
        try:
            if os.name == 'nt': os.startfile(str(p))
            else: subprocess.Popen(['open' if sys.platform == 'darwin' else 'xdg-open', str(p)])
        except OSError as exc: messagebox.showerror('Lỗi', str(exc))

    def close(self):
        if self.busy: return messagebox.showinfo('Đang xử lý', 'Chờ thao tác hoàn tất trước khi đóng cửa sổ.')
        self.destroy()


if __name__ == '__main__':
    Packager().mainloop()
