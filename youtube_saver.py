import os
import time
import yt_dlp


def download_video(url):
    download_folder = r"C:\Users\profi\Downloads"

    os.makedirs(download_folder, exist_ok=True)

    ydl_opts = {
        "format": "bestvideo[ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]/best",
        "outtmpl": os.path.join(download_folder, "%(title)s.%(ext)s"),
        "embeddedsubtitles": False,
        "writethumbnail": False,
        "postprocessors": []
    }

    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(url, download=True)
        filename = ydl.prepare_filename(info)

    now = time.time()
    os.utime(filename, (now, now))


if __name__ == "__main__":
    url = input("Введите URL: ")
    download_video(url)

