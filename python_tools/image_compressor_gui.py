
import os
import tkinter as tk
from tkinter import filedialog, messagebox
from PIL import Image
from io import BytesIO

class ImageCompressor:
    def __init__(self, root):
        self.root = root
        self.root.title("Image Compressor")
        self.root.geometry("500x350")
        self.root.resizable(False, False)

        self.image_path = None

        # Title
        tk.Label(
            root,
            text="IMAGE COMPRESSOR",
            font=("Arial", 18, "bold")
        ).pack(pady=15)

        # Select image
        tk.Button(
            root,
            text="Chọn ảnh",
            width=20,
            command=self.select_image
        ).pack(pady=5)

        self.file_label = tk.Label(
            root,
            text="Chưa chọn ảnh",
            fg="gray",
            wraplength=450
        )
        self.file_label.pack(pady=5)

        # Original size
        self.original_label = tk.Label(
            root,
            text="Dung lượng ban đầu: --"
        )
        self.original_label.pack(pady=5)

        # Target size
        tk.Label(
            root,
            text="Dung lượng tối đa (MB):"
        ).pack(pady=5)

        self.target_entry = tk.Entry(root, justify="center")
        self.target_entry.insert(0, "1")
        self.target_entry.pack()

        # Compress button
        tk.Button(
            root,
            text="NÉN ẢNH",
            bg="#2563eb",
            fg="white",
            font=("Arial", 11, "bold"),
            width=20,
            command=self.compress_image
        ).pack(pady=15)

        # Result
        self.result_label = tk.Label(
            root,
            text="",
            font=("Arial", 10),
            justify="center"
        )
        self.result_label.pack(pady=5)

    def select_image(self):
        path = filedialog.askopenfilename(
            title="Chọn ảnh",
            filetypes=[
                ("Image files", "*.jpg *.jpeg *.png *.webp *.bmp"),
                ("All files", "*.*")
            ]
        )

        if not path:
            return

        self.image_path = path

        size = os.path.getsize(path)

        self.file_label.config(
            text=os.path.basename(path),
            fg="black"
        )

        self.original_label.config(
            text=f"Dung lượng ban đầu: {size / 1024 / 1024:.2f} MB"
        )

        self.result_label.config(text="")

    def compress_image(self):
        if not self.image_path:
            messagebox.showwarning("Thông báo", "Hãy chọn ảnh trước!")
            return

        try:
            target_mb = float(self.target_entry.get())

            if target_mb <= 0:
                raise ValueError

        except ValueError:
            messagebox.showerror(
                "Lỗi",
                "Dung lượng phải là số lớn hơn 0!"
            )
            return

        target_size = int(target_mb * 1024 * 1024)

        try:
            img = Image.open(self.image_path)
            img.load()

            # Xử lý ảnh có alpha channel
            if img.mode in ("RGBA", "P"):
                img = img.convert("RGBA")
                background = Image.new("RGB", img.size, "white")
                background.paste(
                    img,
                    mask=img.getchannel("A")
                )
                img = background
            else:
                img = img.convert("RGB")

            quality = 90
            scale = 1.0

            while True:
                width = max(1, int(img.width * scale))
                height = max(1, int(img.height * scale))

                resized = img.resize(
                    (width, height),
                    Image.Resampling.LANCZOS
                )

                buffer = BytesIO()

                resized.save(
                    buffer,
                    format="JPEG",
                    quality=quality,
                    optimize=True
                )

                if buffer.tell() < target_size:
                    break

                if quality > 30:
                    quality -= 10
                else:
                    if width == 1 and height == 1:
                        messagebox.showerror(
                            "Lỗi",
                            "Không thể nén ảnh xuống dung lượng yêu cầu."
                        )
                        return

                    scale *= 0.8
                    quality = 80

            # Save output in current folder
            filename = os.path.splitext(
                os.path.basename(self.image_path)
            )[0]

            output_path = os.path.join(
                os.path.dirname(self.image_path),
                filename + "_compressed.jpg"
            )

            with open(output_path, "wb") as f:
                f.write(buffer.getvalue())

            original_size = os.path.getsize(self.image_path)
            final_size = os.path.getsize(output_path)

            reduction = (
                (1 - final_size / original_size) * 100
            )

            self.result_label.config(
                text=(
                    f"NÉN THÀNH CÔNG!\n"
                    f"Dung lượng mới: {final_size / 1024 / 1024:.2f} MB\n"
                    f"Đã giảm: {reduction:.2f}%\n"
                    f"File: {output_path}"
                ),
                fg="green"
            )

            messagebox.showinfo(
                "Thành công",
                f"Đã nén ảnh thành công!\n\n{output_path}"
            )

        except Exception as e:
            messagebox.showerror("Lỗi", str(e))


if __name__ == "__main__":
    root = tk.Tk()
    app = ImageCompressor(root)
    root.mainloop()
