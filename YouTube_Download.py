import tkinter as tk
from tkinter import ttk, messagebox
import yt_dlp
import os
import subprocess
import platform
import threading

# 全局變數以存儲下載的檔案路徑
downloaded_file = ""
downloading = False  # 追蹤下載狀態
video_title = ""  # 用於存儲影片標題

# 進度回調函數
def progress_hook(d):
    global downloaded_file, downloading, video_title
    if d['status'] == 'downloading':
        if d.get('total_bytes'):
            percent = (d['downloaded_bytes'] / d['total_bytes']) * 100
        elif d.get('total_bytes_estimate'):
            percent = (d['downloaded_bytes'] / d['total_bytes_estimate']) * 100
        else:
            percent = 0

        progress_bar['value'] = percent
        percent_label.config(text=f"{percent:.2f}%")
        status_label.config(text=f"正在下載: {video_title} - {percent:.2f}%")  # 保留影片標題
        root.update_idletasks()  # 更新介面以顯示進度

    elif d['status'] == 'finished':
        downloading = False  # 停止下載狀態
        progress_bar['value'] = 100
        percent_label.config(text="100.00%")
        status_label.config(text=f"下載完成: {video_title}")  # 保留影片標題
        downloaded_file = d['filename'] if 'filename' in d else "未知檔案"
        root.update_idletasks()
        open_button.pack(pady=10)

# 檢查檔案是否存在
def check_file_exists(file_path):
    return os.path.exists(file_path)

# 下載影片
def download_video():
    global downloading, video_title
    if downloading:
        status_label.config(text="正在下載中，請稍候...", fg="red")
        return

    url = url_entry.get()
    if not url:
        status_label.config(text="請輸入YouTube影片網址", fg="red")
        return

    def run_download():
        global downloaded_file, downloading, video_title
        downloading = True
        try:
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(url, download=False)
                file_name = ydl.prepare_filename(info)
                video_title = info.get('title', '未知影片')  # 獲取影片標題

                if check_file_exists(file_name):
                    status_label.config(text=f"檔案已存在: {video_title}", fg="blue")
                    downloaded_file = file_name
                    open_button.pack(pady=10)
                    if messagebox.askyesno("檔案已存在", "檔案已存在，是否重新下載？"):
                        os.remove(file_name)
                        status_label.config(text=f"重新下載: {video_title}", fg="green")
                        ydl.download([url])
                    return

                progress_bar['value'] = 0
                percent_label.config(text="0.00%")
                status_label.config(text=f"正在下載: {video_title}", fg="green")
                root.update_idletasks()
                ydl.download([url])
        except yt_dlp.utils.DownloadError as e:
            status_label.config(text=f"下載失敗: {str(e)}", fg="red")
        except Exception as e:
            status_label.config(text=f"發生未知錯誤: {str(e)}", fg="red")
        finally:
            downloading = False
            progress_bar['value'] = 0
            percent_label.config(text="0.00%")

    threading.Thread(target=run_download, daemon=True).start()

# 打開檔案位置
def open_file_location():
    if not downloaded_file:
        status_label.config(text="沒有檔案可以打開", fg="red")
        return

    directory = os.path.dirname(downloaded_file)
    if not os.path.exists(directory):
        status_label.config(text="檔案目錄不存在", fg="red")
        return

    if platform.system() == "Windows":
        subprocess.run(f'explorer "{directory}"')
    elif platform.system() == "Darwin":  # macOS
        subprocess.run(["open", directory])
    else:  # Linux
        subprocess.run(["xdg-open", directory])

# 設置 yt-dlp 下載選項
ydl_opts = {
    'format': 'bestvideo[height>=720]+bestaudio/best[height>=720]',
    'outtmpl': 'downloads/%(title)s.%(ext)s',
    'socket_timeout': 60,
    'retries': 10,
    'progress_hooks': [progress_hook],
    'quiet': True,
    'no_warnings': True
}

# 建立 tkinter 介面
def close_window():
    if downloading:
        if not messagebox.askyesno("下載中", "下載仍在進行中，確定要關閉視窗嗎？"):
            return
    root.quit()     # 停止 mainloop
    root.destroy()  # 銷毀視窗

root = tk.Tk()
root.title("YouTube影片下載器")
root.geometry("800x400")  # 設置視窗大小
root.resizable(False, False)  # 禁止調整視窗大小

# 綁定視窗的「X」按鈕到 close_window 函數
root.protocol("WM_DELETE_WINDOW", close_window)

# 設置字體
font_large = ('Helvetica', 14)
font_small = ('Helvetica', 12)

# 主框架
main_frame = tk.Frame(root, padx=20, pady=20)
main_frame.pack(fill=tk.BOTH, expand=True)

# URL 輸入框
url_label = tk.Label(main_frame, text="請輸入YouTube影片網址：", font=font_large)
url_label.pack(pady=(0, 10))

url_entry = tk.Entry(main_frame, width=80, font=font_large)
url_entry.pack(pady=(0, 20))

# 下載按鈕
button_frame = tk.Frame(main_frame)
button_frame.pack(pady=(0, 20))

download_button = tk.Button(button_frame, text="下載", command=download_video, font=font_large, bg="#4CAF50", fg="white")
download_button.pack(side=tk.LEFT, padx=10)

open_button = tk.Button(button_frame, text="打開檔案位置", command=open_file_location, font=font_large, bg="#2196F3", fg="white")
open_button.pack(side=tk.LEFT, padx=10)
open_button.pack_forget()  # 初始隱藏

# 進度條框架
progress_frame = tk.Frame(main_frame)
progress_frame.pack(fill=tk.X, pady=(0, 10))

progress_bar = ttk.Progressbar(progress_frame, length=700, mode='determinate')
progress_bar.pack()

percent_label = tk.Label(progress_frame, text="0.00%", font=font_small)
percent_label.pack()

# 狀態標籤（增加自動換行）
status_label = tk.Label(main_frame, text="", font=font_small, wraplength=700, justify=tk.LEFT)
status_label.pack()

# 啟動 tkinter 介面
root.mainloop()