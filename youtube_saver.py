import re
import os
import time
import queue
import threading
import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import yt_dlp
from ttkthemes import ThemedTk


class YouTubeDownloaderApp:
    def __init__(self, root):
        self.root = root
        self.root.title("YouTube Video Downloader")
        self.root.geometry("720x420")

        self.gui_queue = queue.Queue()

        self.style = ttk.Style()
        self.style.theme_use('clam')
        self.configure_styles()

        self.download_folder = tk.StringVar(value=os.path.expanduser("~\\Downloads"))
        self.url_var = tk.StringVar()
        self.progress_var = tk.DoubleVar()

        self.create_widgets()

        self.url_var.trace_add("write", self.validate_url_input)
        self.root.after(100, self.check_queue)

    def configure_styles(self):
        self.style.configure('TFrame', background='#2d2d2d')
        self.style.configure('TLabel', background='#2d2d2d', foreground='white', font=('Segoe UI', 10))
        self.style.configure('TEntry', fieldbackground='#404040', foreground='white', insertcolor='white')
        self.style.configure('TButton', font=('Segoe UI', 10), padding=6)
        self.style.map('TButton',
                       background=[('active', '#45a049'), ('!disabled', '#4CAF50')],
                       foreground=[('!disabled', 'white')]
                       )
        self.style.configure('Title.TLabel', font=('Segoe UI', 14, 'bold'))
        self.style.configure('Progress.Horizontal.TProgressbar',
                             troughcolor='#404040',
                             background='#4CAF50',
                             thickness=20
                             )

        self.style.configure('Error.TEntry',
                             fieldbackground='#ffdddd',
                             foreground='red',
                             bordercolor='#ff4444',
                             lightcolor='#ff4444',
                             darkcolor='#ff4444'
                             )

    def create_widgets(self):
        main_frame = ttk.Frame(self.root)
        main_frame.pack(padx=20, pady=20, fill='both', expand=True)

        ttk.Label(main_frame, text="YouTube Video Downloader", style='Title.TLabel'
                  ).pack(pady=(0, 15))

        url_frame = ttk.Frame(main_frame)
        url_frame.pack(fill='x', pady=5)

        ttk.Label(url_frame, text="Ссылка на видео:").pack(side='left', padx=(0, 10))
        self.url_entry = ttk.Entry(url_frame, textvariable=self.url_var, width=50)
        self.url_entry.pack(side='left', fill='x', expand=True)


        self.error_label = ttk.Label(main_frame, text="", foreground='red')
        self.error_label.pack(pady=2)

        folder_frame = ttk.Frame(main_frame)
        folder_frame.pack(fill='x', pady=5)

        ttk.Label(folder_frame, text="Папка сохранения:").pack(side='left', padx=(0, 10))
        ttk.Entry(folder_frame, textvariable=self.download_folder, state='readonly'
                  ).pack(side='left', fill='x', expand=True)
        ttk.Button(folder_frame, text="Выбрать", command=self.select_folder, width=10
                   ).pack(side='left', padx=(10, 0))

        self.progress_bar = ttk.Progressbar(main_frame,
                                            variable=self.progress_var,
                                            style='Progress.Horizontal.TProgressbar',
                                            maximum=100
                                            )
        self.progress_bar.pack(fill='x', pady=15)

        self.status_label = ttk.Label(main_frame, text="Готово", foreground='#888')
        self.status_label.pack()

        self.download_btn = ttk.Button(main_frame,
                                       text="Скачать видео",
                                       command=self.start_download
                                       )
        self.download_btn.pack(pady=15)

    def select_folder(self):
        folder = filedialog.askdirectory()
        if folder:
            self.download_folder.set(folder)

    def start_download(self):
        if not self.validate_input():
            return

        self.toggle_ui_state(False)
        threading.Thread(target=self.download_video, daemon=True).start()

    def validate_url_input(self, *args):
        """Проверка раскладки в реальном времени"""
        url = self.url_var.get()
        if self.has_russian_chars(url):
            self.show_input_error("Используйте английскую раскладку для URL")
        else:
            self.clear_input_error()

    def validate_input(self):
        """Основная проверка перед загрузкой"""
        url = self.url_var.get().strip()

        if not url:
            self.show_error("Введите ссылку на видео")
            return False

        if self.has_russian_chars(url):
            self.show_input_error("Используйте английскую раскладку")
            return False

        if not self.is_valid_youtube_url(url):
            self.show_error("Некорректная ссылка YouTube")
            return False

        if not self.download_folder.get():
            self.show_error("Выберите папку для сохранения")
            return False

        return True

    def has_russian_chars(self, text):
        """Проверка на наличие русских символов"""
        return any('\u0400' <= char <= '\u04FF' for char in text)

    def is_valid_youtube_url(self, url):
        """Проверка формата YouTube ссылки"""
        pattern = r'^(https?://)?(www\.)?(youtube\.com|youtu\.be)/.+'
        return re.match(pattern, url) is not None

    def show_input_error(self, message):
        """Показать ошибку в поле ввода"""

        def _show():
            self.url_entry.config(style='Error.TEntry')
            self.error_label.config(text=message, foreground='red')

        self.gui_queue.put(_show)

    def clear_input_error(self):
        """Сбросить подсветку ошибки"""

        def _clear():
            self.url_entry.config(style='TEntry')
            self.error_label.config(text="")

        self.gui_queue.put(_clear)

    def toggle_ui_state(self, enabled=True):
        """Блокировка/разблокировка интерфейса"""

        def _toggle():
            state = 'normal' if enabled else 'disabled'
            self.url_entry.config(state=state)
            self.download_btn.config(state=state)
            self.root.config(cursor='watch' if not enabled else '')

        self.gui_queue.put(_toggle)

    def download_video(self):
        """Основная логика загрузки видео"""
        try:
            ydl_opts = {
                "format": "bestvideo[ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]/best",
                "outtmpl": os.path.join(self.download_folder.get(), "%(title)s.%(ext)s"),
                "progress_hooks": [self.update_progress],
                "noprogress": True,
                "quiet": True,
            }

            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(self.url_var.get(), download=True)
                filename = ydl.prepare_filename(info)

            now = time.time()
            os.utime(filename, (now, now))

            self.show_success()

        except Exception as e:
            self.show_error(str(e))
        finally:
            self.toggle_ui_state(True)

    def update_progress(self, d):
        """Обновление прогресса загрузки"""

        def _update():
            if d['status'] == 'downloading':
                percent = float(d['_percent_str'].replace('%', ''))
                self.progress_var.set(percent)
                self.status_label.config(
                    text=f"Загрузка: {d['_percent_str']} | Скорость: {d['_speed_str']}",
                    foreground='white'
                )

        self.gui_queue.put(_update)

    def show_success(self):
        """Показать сообщение об успехе"""

        def _show():
            self.progress_var.set(100)
            self.status_label.config(text="Загрузка завершена!", foreground='#4CAF50')
            messagebox.showinfo("Успех",
                                f"Видео успешно сохранено в:\n{self.download_folder.get()}",
                                parent=self.root
                                )

        self.gui_queue.put(_show)

    def show_error(self, message):
        """Показать сообщение об ошибке"""

        def _show():
            self.progress_var.set(0)
            self.status_label.config(text="Ошибка загрузки", foreground='#ff4444')
            messagebox.showerror("Ошибка",
                                 f"Не удалось скачать видео:\n{message}",
                                 parent=self.root
                                 )

        self.gui_queue.put(_show)

    def check_queue(self):
        """Обработка задач из очереди"""
        while not self.gui_queue.empty():
            try:
                task = self.gui_queue.get_nowait()
                task()
            except queue.Empty:
                pass
        self.root.after(100, self.check_queue)


if __name__ == "__main__":
    root = ThemedTk(theme="equilux")
    app = YouTubeDownloaderApp(root)
    root.mainloop()