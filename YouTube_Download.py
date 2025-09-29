import tkinter as tk
from tkinter import ttk, messagebox
import yt_dlp
import os
import subprocess
import platform
import threading

# ✅ 啟動時自動嘗試更新 yt-dlp（避免因 YouTube 改格式而下載失敗）
try:
    subprocess.run(["python", "-m", "pip", "install", "-U", "yt-dlp"], check=False)
except Exception:
    pass

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
        status_label.config(text=f"正在下載: {video_title} - {percent:.2f}%")
        root.update_idletasks()

    elif d['status'] == 'finished':
        downloading = False
        progress_bar['value'] = 100
        percent_label.config(text="100.00%")
        status_label.config(text=f"下載完成: {video_title}")
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
                video_title = info.get('title', '未知影片')

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
    elif platform.system() == "Darwin":
        subprocess.run(["open", directory])
    else:
        subprocess.run(["xdg-open", directory])

# ✅ yt-dlp 下載設定（自動選擇最佳畫質）
ydl_opts = {
    'format': 'bestvideo+bestaudio/best',  # ✅ 兼容所有畫質
    'outtmpl': 'downloads/%(title)s.%(ext)s',
    'socket_timeout': 60,
    'retries': 10,
    'progress_hooks': [progress_hook],
    'quiet': True,
    'no_warnings': True
}

# 關閉視窗
def close_window():
    if downloading:
        if not messagebox.askyesno("下載中", "下載仍在進行中，確定要關閉視窗嗎？"):
            return
    root.quit()
    root.destroy()

root = tk.Tk()
root.title("YouTube影片下載器")
root.geometry("800x400")
root.resizable(False, False)
root.protocol("WM_DELETE_WINDOW", close_window)

# 字體
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

# ✅ 新增 Enter 鍵啟動下載
url_entry.bind("<Return>", lambda event: download_video())

# === 新增右鍵選單功能 ===
context_menu = tk.Menu(root, tearoff=0)
context_menu.add_command(label="剪下", command=lambda: url_entry.event_generate("<<Cut>>"))
context_menu.add_command(label="複製", command=lambda: url_entry.event_generate("<<Copy>>"))
context_menu.add_command(label="貼上", command=lambda: url_entry.event_generate("<<Paste>>"))
context_menu.add_command(label="全選", command=lambda: url_entry.select_range(0, tk.END))

def show_context_menu(event):
    context_menu.tk_popup(event.x_root, event.y_root)

url_entry.bind("<Button-3>", show_context_menu)  # Windows/Linux
url_entry.bind("<Button-2>", show_context_menu)  # macOS

# 下載按鈕
button_frame = tk.Frame(main_frame)
button_frame.pack(pady=(0, 20))

download_button = tk.Button(button_frame, text="下載", command=download_video, font=font_large, bg="#4CAF50", fg="white")
download_button.pack(side=tk.LEFT, padx=10)

open_button = tk.Button(button_frame, text="打開檔案位置", command=open_file_location, font=font_large, bg="#2196F3", fg="white")
open_button.pack(side=tk.LEFT, padx=10)
open_button.pack_forget()

# 進度條框架
progress_frame = tk.Frame(main_frame)
progress_frame.pack(fill=tk.X, pady=(0, 10))

progress_bar = ttk.Progressbar(progress_frame, length=700, mode='determinate')
progress_bar.pack()

percent_label = tk.Label(progress_frame, text="0.00%", font=font_small)
percent_label.pack()

# 狀態標籤
status_label = tk.Label(main_frame, text="", font=font_small, wraplength=700, justify=tk.LEFT)
status_label.pack()

root.mainloop()
