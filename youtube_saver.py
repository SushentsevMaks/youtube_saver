import os
import time
import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import threading
import yt_dlp


class YouTubeDownloaderApp:
    def __init__(self, root):
        self.root = root
        self.root.title("YouTube Downloader")
        self.root.geometry("600x200")

        self.download_folder = tk.StringVar()
        self.url_var = tk.StringVar()
        self.status_var = tk.StringVar()

        self.create_widgets()

    def create_widgets(self):
        url_frame = ttk.Frame(self.root)
        url_frame.pack(pady=10, padx=10, fill='x')

        ttk.Label(url_frame, text="Ссылка на видео:").grid(row=0, column=0, sticky='w')
        self.url_entry = ttk.Entry(url_frame, textvariable=self.url_var, width=50)
        self.url_entry.grid(row=0, column=1, padx=5)

        folder_frame = ttk.Frame(self.root)
        folder_frame.pack(pady=10, padx=10, fill='x')

        ttk.Label(folder_frame, text="Папка сохранения:").grid(row=0, column=0, sticky='w')
        ttk.Entry(folder_frame, textvariable=self.download_folder, state='readonly', width=40).grid(row=0, column=1,
                                                                                                    padx=5)
        ttk.Button(folder_frame, text="Выбрать", command=self.select_folder).grid(row=0, column=2)

        download_frame = ttk.Frame(self.root)
        download_frame.pack(pady=20)
        ttk.Button(download_frame, text="Скачать видео", command=self.start_download).pack()

        status_frame = ttk.Frame(self.root)
        status_frame.pack(pady=10)
        ttk.Label(status_frame, textvariable=self.status_var, foreground='blue').pack()

    def select_folder(self):
        folder = filedialog.askdirectory()
        if folder:
            self.download_folder.set(folder)

    def start_download(self):
        if not self.url_var.get():
            messagebox.showerror("Ошибка", "Введите ссылку на видео")
            return

        if not self.download_folder.get():
            messagebox.showerror("Ошибка", "Выберите папку для сохранения")
            return

        threading.Thread(target=self.download_video, daemon=True).start()
        self.status_var.set("Загрузка начата...")

    def download_video(self):
        try:
            ydl_opts = {
                "format": "bestvideo[ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]/best",
                "outtmpl": os.path.join(self.download_folder.get(), "%(title)s.%(ext)s"),
                "embeddedsubtitles": False,
                "writethumbnail": False,
                "postprocessors": [],
                "progress_hooks": [self.update_progress],
            }

            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(self.url_var.get(), download=True)
                filename = ydl.prepare_filename(info)

            now = time.time()
            os.utime(filename, (now, now))

            self.status_var.set("Загрузка завершена!")
            messagebox.showinfo("Успех", "Видео успешно скачано")

        except Exception as e:
            self.status_var.set("Ошибка загрузки")
            messagebox.showerror("Ошибка", f"Произошла ошибка:\n{str(e)}")

    def update_progress(self, d):
        if d['status'] == 'downloading':
            progress = f"Загружено: {d['_percent_str']} | Скорость: {d['_speed_str']}"
            self.status_var.set(progress)
            self.root.update_idletasks()


if __name__ == "__main__":
    root = tk.Tk()
    app = YouTubeDownloaderApp(root)
    root.mainloop()

