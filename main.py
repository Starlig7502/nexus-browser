import sys
import os
import json
import secrets
import string
import math
import time
import threading
import concurrent.futures
import requests
from datetime import datetime

# ── HiDPI & CHROMIUM FLAGS ── phải đặt TRƯỚC khi tạo QApplication ──────────
os.environ["QT_ENABLE_HIGHDPI_SCALING"] = "1"
os.environ["QT_FONT_DPI"] = "96"
os.environ["QT_SCALE_FACTOR_ROUNDING_POLICY"] = "PassThrough"
os.environ["QTWEBENGINE_CHROMIUM_FLAGS"] = (
    "--disable-gpu-shader-disk-cache "
    "--disk-cache-size=52428800 "
    "--media-cache-size=10485760 "
    "--disable-reading-from-canvas "
    "--process-per-site "
    "--ignore-gpu-blocklist "
    "--enable-gpu-rasterization "
    "--enable-features=NetworkService "
    "--disable-features=CalculateNativeWinOcclusion"
)

from PyQt6.QtCore import (
    QUrl, QTimer, Qt, QSize, QThread, pyqtSignal, QObject
)
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QTabWidget, QToolBar, QLineEdit, QPushButton,
    QVBoxLayout, QHBoxLayout, QWidget, QSplitter, QTextEdit, QTextBrowser, QMessageBox,
    QLabel, QMenu, QDialog, QListWidget, QListWidgetItem, QProgressBar,
    QFileDialog, QSizePolicy, QScrollArea, QFrame
)
from PyQt6.QtWebEngineWidgets import QWebEngineView
from PyQt6.QtWebEngineCore import (
    QWebEngineProfile, QWebEngineUrlRequestInterceptor, QWebEnginePage
)
from PyQt6.QtNetwork import QNetworkProxy
from PyQt6.QtGui import QFont, QPalette, QColor, QShortcut, QKeySequence

# ════════════════════════════════════════════════════════════════════════════
# START PAGE HTML
# ════════════════════════════════════════════════════════════════════════════
def build_start_page(dark: bool) -> str:
    bg        = "#141417" if dark else "#F5F5F7"
    card_bg   = "#1C1C20" if dark else "#FFFFFF"
    text      = "#F5F5F7" if dark else "#141417"
    sub_text  = "#8E8E93" if dark else "#6E6E73"
    input_bg  = "#1C1C20" if dark else "#FFFFFF"
    input_brd = "#2C2C30" if dark else "#D1D1D6"
    accent    = "#0078D4"
    return f"""<!DOCTYPE html>
<html lang="vi">
<head>
<meta charset="UTF-8">
<style>
  * {{ box-sizing: border-box; margin: 0; padding: 0; }}
  body {{
    background: {bg};
    color: {text};
    font-family: 'Segoe UI', Arial, sans-serif;
    display: flex;
    flex-direction: column;
    align-items: center;
    justify-content: center;
    min-height: 100vh;
    gap: 24px;
  }}
  .logo {{
    font-size: 72px;
    font-weight: 900;
    letter-spacing: 12px;
    color: {accent};
    text-shadow: 0 0 20px {accent}99, 0 0 60px {accent}44;
    user-select: none;
  }}
  .subtitle {{
    font-size: 16px;
    color: {sub_text};
    letter-spacing: 2px;
  }}
  .search-box {{
    display: flex;
    width: min(600px, 90vw);
    border-radius: 28px;
    overflow: hidden;
    border: 2px solid {accent};
    background: {input_bg};
    box-shadow: 0 0 24px {accent}33;
  }}
  .search-box input {{
    flex: 1;
    padding: 14px 20px;
    border: none;
    outline: none;
    background: transparent;
    color: {text};
    font-size: 16px;
    font-family: 'Segoe UI', Arial, sans-serif;
  }}
  .search-box button {{
    padding: 14px 24px;
    border: none;
    background: {accent};
    color: #fff;
    font-size: 18px;
    cursor: pointer;
    transition: opacity .2s;
  }}
  .search-box button:hover {{ opacity: .85; }}
  .shortcuts {{
    display: flex;
    gap: 16px;
    flex-wrap: wrap;
    justify-content: center;
    max-width: 620px;
  }}
  .shortcut {{
    background: {card_bg};
    border: 1px solid {input_brd};
    border-radius: 12px;
    padding: 14px 22px;
    font-size: 14px;
    font-weight: 600;
    cursor: pointer;
    color: {text};
    transition: transform .15s, box-shadow .15s;
    text-decoration: none;
    display: block;
  }}
  .shortcut:hover {{
    transform: scale(1.06);
    box-shadow: 0 4px 24px {accent}44;
  }}
</style>
</head>
<body>
<div class="logo">NEXUS</div>
<div class="subtitle">Trình duyệt tương lai thế hệ mới</div>
<div class="search-box">
  <input id="q" type="text" placeholder="Tìm kiếm với Google..."
         onkeydown="if(event.key==='Enter')go()">
  <button onclick="go()">&#x1F50D;</button>
</div>
<div class="shortcuts">
  <a class="shortcut" href="https://google.com">🔍 Google</a>
  <a class="shortcut" href="https://youtube.com">▶ YouTube</a>
  <a class="shortcut" href="https://github.com">🐙 GitHub</a>
  <a class="shortcut" href="https://facebook.com">📘 Facebook</a>
  <a class="shortcut" href="https://mail.google.com">✉ Gmail</a>
  <a class="shortcut" href="https://translate.google.com">🌐 Dịch</a>
</div>
<script>
  function go() {{
    var q = document.getElementById('q').value.trim();
    if (q) location.href = 'https://www.google.com/search?q=' + encodeURIComponent(q);
  }}
  document.querySelectorAll('.shortcut').forEach(function(a) {{
    a.addEventListener('click', function(e) {{
      e.preventDefault();
      window.location.href = this.href;
    }});
  }});
</script>
</body>
</html>"""


ERROR_PAGE_HTML = """<!DOCTYPE html>
<html lang="vi">
<head><meta charset="UTF-8">
<style>
  body { background:#141417; color:#F5F5F7; font-family:'Segoe UI',sans-serif;
          display:flex; flex-direction:column; align-items:center;
          justify-content:center; height:100vh; gap:18px; }
  .icon { font-size:72px; }
  h1 { font-size:28px; color:#FF453A; }
  p { color:#8E8E93; font-size:15px; max-width:420px; text-align:center; }
  button { background:#0078D4; color:#fff; border:none; padding:12px 32px;
            border-radius:24px; font-size:15px; cursor:pointer; }
  button:hover { opacity:.85; }
</style></head>
<body>
<div class="icon">🌐</div>
<h1>Không thể kết nối</h1>
<p>Trang web không phản hồi hoặc bạn không có kết nối Internet.<br>
Kiểm tra lại đường truyền mạng rồi thử lại.</p>
<button onclick="location.reload()">↺ Thử lại</button>
</body></html>"""

# ════════════════════════════════════════════════════════════════════════════
# QSS STYLESHEETS
# ════════════════════════════════════════════════════════════════════════════
DARK_QSS = """
QMainWindow, QWidget#central { background:#141417; color:#F5F5F7; }
QToolBar {
    background:#141417; border:none;
    padding:6px 8px; spacing:6px;
}
QToolBar::separator { background:#2C2C30; width:1px; margin:4px 2px; }
QPushButton {
    background:#1C1C20; color:#F5F5F7; border:none;
    padding:7px 14px; border-radius:6px; font-weight:500;
}
QPushButton:hover  { background:#2C2C30; }
QPushButton:pressed { background:#3A3A40; }
QPushButton#ai_btn {
    background:transparent; color:#0078D4;
    border:1.5px solid #0078D4; border-radius:6px;
    padding:6px 14px; font-weight:600;
}
QPushButton#ai_btn:hover    { background:#0078D422; }
QPushButton#ai_btn:checked  { background:#0078D4; color:#fff; }
QLineEdit {
    background:#1C1C20; color:#F5F5F7; padding:8px 12px;
    border-radius:6px; border:1.5px solid #2C2C30; font-size:14px;
}
QLineEdit:focus { border:1.5px solid #0078D4; }
QTabWidget::pane { border:none; background:#141417; }
QTabBar { background:#141417; }
QTabBar::tab {
    background:#141417; color:#8E8E93;
    padding:9px 20px; min-width:100px;
    border-top-left-radius:8px; border-top-right-radius:8px;
    margin-right:2px;
}
QTabBar::tab:selected { background:#1C1C20; color:#F5F5F7; font-weight:600; }
QTabBar::tab:hover:!selected { background:#1C1C20; }
QTextEdit {
    background:#1C1C20; color:#F5F5F7; border:none;
    border-radius:6px; padding:10px; font-size:14px;
}
QMenu { background:#1C1C20; border:1px solid #2C2C30; border-radius:8px; padding:4px; }
QMenu::item { padding:8px 24px; border-radius:5px; color:#F5F5F7; }
QMenu::item:selected { background:#2C2C30; }
QMenu::separator { height:1px; background:#2C2C30; margin:4px 0; }
QProgressBar {
    border:none; border-radius:2px; background:#2C2C30;
    text-align:center; color:transparent;
}
QProgressBar::chunk { background:#0078D4; border-radius:2px; }
QDialog { background:#141417; border-radius:12px; color:#F5F5F7; }
QListWidget {
    background:#1C1C20; border:1px solid #2C2C30;
    border-radius:8px; padding:4px; color:#F5F5F7;
}
QListWidget::item { padding:10px 8px; border-radius:5px; }
QListWidget::item:selected { background:#2C2C30; }
QLabel { color:#F5F5F7; }
QScrollBar:vertical { background:#141417; width:8px; border-radius:4px; }
QScrollBar::handle:vertical { background:#2C2C30; border-radius:4px; }
QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical { height:0; }
QSplitter::handle { background:#2C2C30; width:1px; }
"""

LIGHT_QSS = """
QMainWindow, QWidget#central { background:#F5F5F7; color:#141417; }
QToolBar {
    background:#F5F5F7; border:none;
    padding:6px 8px; spacing:6px;
    border-bottom:1px solid #D1D1D6;
}
QPushButton {
    background:#E5E5EA; color:#141417; border:none;
    padding:7px 14px; border-radius:6px; font-weight:500;
}
QPushButton:hover  { background:#D1D1D6; }
QPushButton:pressed { background:#C7C7CC; }
QPushButton#ai_btn {
    background:transparent; color:#0078D4;
    border:1.5px solid #0078D4; border-radius:6px;
    padding:6px 14px; font-weight:600;
}
QPushButton#ai_btn:hover   { background:#0078D411; }
QPushButton#ai_btn:checked { background:#0078D4; color:#fff; }
QLineEdit {
    background:#FFFFFF; color:#141417; padding:8px 12px;
    border-radius:6px; border:1.5px solid #D1D1D6; font-size:14px;
}
QLineEdit:focus { border:1.5px solid #0078D4; }
QTabWidget::pane { border:none; background:#F5F5F7; }
QTabBar { background:#F5F5F7; }
QTabBar::tab {
    background:#F5F5F7; color:#6E6E73;
    padding:9px 20px; min-width:100px;
    border-top-left-radius:8px; border-top-right-radius:8px;
    margin-right:2px;
}
QTabBar::tab:selected { background:#FFFFFF; color:#141417; font-weight:600; }
QTabBar::tab:hover:!selected { background:#E5E5EA; }
QTextEdit {
    background:#FFFFFF; color:#141417; border:1px solid #D1D1D6;
    border-radius:6px; padding:10px; font-size:14px;
}
QMenu { background:#FFFFFF; border:1px solid #D1D1D6; border-radius:8px; padding:4px; }
QMenu::item { padding:8px 24px; border-radius:5px; color:#141417; }
QMenu::item:selected { background:#E5E5EA; }
QMenu::separator { height:1px; background:#D1D1D6; margin:4px 0; }
QProgressBar {
    border:none; border-radius:2px; background:#D1D1D6;
    text-align:center; color:transparent;
}
QProgressBar::chunk { background:#0078D4; border-radius:2px; }
QDialog { background:#F5F5F7; border-radius:12px; color:#141417; }
QListWidget {
    background:#FFFFFF; border:1px solid #D1D1D6;
    border-radius:8px; padding:4px; color:#141417;
}
QListWidget::item { padding:10px 8px; border-radius:5px; }
QListWidget::item:selected { background:#E5E5EA; }
QLabel { color:#141417; }
QScrollBar:vertical { background:#F5F5F7; width:8px; border-radius:4px; }
QScrollBar::handle:vertical { background:#D1D1D6; border-radius:4px; }
QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical { height:0; }
QSplitter::handle { background:#D1D1D6; width:1px; }
"""

# ════════════════════════════════════════════════════════════════════════════
# AD BLOCKER
# ════════════════════════════════════════════════════════════════════════════
class NexusAdBlocker(QWebEngineUrlRequestInterceptor):
    BLOCK_LIST = [
        "googlesyndication", "doubleclick", "adservice", "popads",
        "analytics.google", "facebook.net/tr", "scorecardresearch",
        "ads.yahoo", "taboola", "outbrain", "adnxs", "criteo",
        "amazon-adsystem", "pubmatic", "rubiconproject", "tracking",
        "mc.yandex", "hotjar", "mouseflow", "fullstory",
    ]

    def __init__(self, parent=None):
        super().__init__(parent)

    def interceptRequest(self, info):
        url = info.requestUrl().toString().lower()
        for pattern in self.BLOCK_LIST:
            if pattern in url:
                info.block(True)
                return


# ════════════════════════════════════════════════════════════════════════════
# DATA MANAGER — debounced disk I/O
# ════════════════════════════════════════════════════════════════════════════
class DataManager(QObject):
    def __init__(self):
        super().__init__()
        self.file   = "nexus_config.json"
        self.data   = self._load()
        self._dirty = False
        self._timer = QTimer(self)
        self._timer.timeout.connect(self._flush)
        self._timer.start(2000)

    def _load(self):
        if os.path.exists(self.file):
            try:
                with open(self.file, "r", encoding="utf-8") as f:
                    return json.load(f)
            except Exception:
                pass
        return {"history": [], "bookmarks": [], "passwords": {}}

    def _save(self):
        try:
            with open(self.file, "w", encoding="utf-8") as f:
                json.dump(self.data, f, indent=2, ensure_ascii=False)
        except Exception:
            pass

    def _flush(self):
        if self._dirty:
            self._save()
            self._dirty = False

    # ── API KEY ───────────────────────────────────────────────────────────
    def get_api_key(self) -> str:
        return self.data.get("gemini_api_key", "")

    def set_api_key(self, key: str):
        self.data["gemini_api_key"] = key.strip()
        self._dirty = True

    # ── HISTORY ───────────────────────────────────────────────────────────
    def add_history(self, url, title):
        if not url.startswith("http"):
            return
        self.data["history"].insert(0, {
            "url":  url,
            "title": title or url,
            "time": datetime.now().strftime("%Y-%m-%d %H:%M"),
        })
        self.data["history"] = self.data["history"][:500]
        self._dirty = True

    # ── BOOKMARKS ─────────────────────────────────────────────────────────
    def add_bookmark(self, url, title) -> bool:
        bms = self.data["bookmarks"]
        if not any(b["url"] == url for b in bms):
            bms.append({"url": url, "title": title or url})
            self._dirty = True
            return True
        return False

    def remove_bookmark(self, url):
        before = len(self.data["bookmarks"])
        self.data["bookmarks"] = [b for b in self.data["bookmarks"] if b["url"] != url]
        if len(self.data["bookmarks"]) != before:
            self._dirty = True

    def is_bookmarked(self, url) -> bool:
        return any(b["url"] == url for b in self.data["bookmarks"])

    # ── CLEAR ALL ─────────────────────────────────────────────────────────
    def clear_all(self):
        key = self.data.get("gemini_api_key", "")
        self.data = {"history": [], "bookmarks": [], "passwords": {}}
        if key:
            self.data["gemini_api_key"] = key  # API key is preserved
        self._dirty = True


# ════════════════════════════════════════════════════════════════════════════
# GEMINI AI THREAD  — non-blocking REST call in background QThread
# ════════════════════════════════════════════════════════════════════════════
GEMINI_URL = (
    "https://generativelanguage.googleapis.com/v1beta/models/"
    "gemini-2.0-flash:generateContent"
)

SYSTEM_PROMPT = (
    "Bạn là Nexus AI — trợ lý thông minh tích hợp trong Nexus Browser. "
    "Hãy trả lời ngắn gọn, hữu ích bằng tiếng Việt trừ khi người dùng hỏi "
    "bằng tiếng Anh. Bạn có thể hỗ trợ duyệt web, giải thích nội dung trang, "
    "tóm tắt, dịch thuật, lập trình và bất kỳ câu hỏi nào."
)


class GeminiThread(QThread):
    reply = pyqtSignal(str)
    err   = pyqtSignal(str)

    def __init__(self, api_key: str, history: list, user_msg: str, parent=None):
        super().__init__(parent)
        self.api_key  = api_key
        self.history  = list(history)
        self.user_msg = user_msg

    def run(self):
        if not self.api_key:
            self.err.emit("no_key")
            return

        contents = self.history + [
            {"role": "user", "parts": [{"text": self.user_msg}]}
        ]
        payload = {
            "system_instruction": {
                "parts": [{"text": SYSTEM_PROMPT}]
            },
            "contents": contents,
            "generationConfig": {
                "temperature": 0.7,
                "maxOutputTokens": 1024,
            },
        }
        try:
            resp = requests.post(
                GEMINI_URL,
                params={"key": self.api_key},
                json=payload,
                timeout=30,
            )
            if resp.status_code == 400:
                self.err.emit("bad_key")
                return
            if resp.status_code == 429:
                self.err.emit("rate_limit")
                return
            resp.raise_for_status()
            data = resp.json()
            text = (
                data.get("candidates", [{}])[0]
                    .get("content", {})
                    .get("parts", [{}])[0]
                    .get("text", "")
                    .strip()
            )
            if not text:
                self.err.emit("empty")
                return
            self.reply.emit(text)
        except requests.exceptions.ConnectionError:
            self.err.emit("no_network")
        except requests.exceptions.Timeout:
            self.err.emit("timeout")
        except Exception as exc:
            self.err.emit(f"unknown:{exc}")


# ════════════════════════════════════════════════════════════════════════════
# EXTENSION SCANNER
# ════════════════════════════════════════════════════════════════════════════
NEXUS_EXTENSIONS = {
    "Dark Mode Pro": "document.body.style.filter='invert(100%) hue-rotate(180deg)';",
}

MALICIOUS_KEYWORDS = ["eval", "XMLHttpRequest", "fetch", "cookie", "localStorage"]


def scan_extension_code(js_code: str):
    for kw in MALICIOUS_KEYWORDS:
        if kw in js_code:
            return False, f"Blocked: '{kw}' detected"
    return True, "Safe"


# ════════════════════════════════════════════════════════════════════════════
# IDM 64-THREAD DOWNLOAD ENGINE
# ════════════════════════════════════════════════════════════════════════════
class NexusIDMEngine(QThread):
    progress = pyqtSignal(int, float)
    done     = pyqtSignal(str)
    error    = pyqtSignal(str)

    def __init__(self, url: str, save_path: str, parent=None):
        super().__init__(parent)
        self.url        = url
        self.save_path  = save_path
        self.is_running = True

    def run(self):
        ua = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) NexusIDM/3.0"}
        try:
            head         = requests.head(self.url, headers=ua, allow_redirects=True, timeout=15)
            file_size    = int(head.headers.get("Content-Length", 0))
            accept_range = head.headers.get("Accept-Ranges", "").lower()

            if file_size == 0 or accept_range != "bytes":
                self._single_thread(ua)
                return

            num_threads = min(64, max(1, file_size // (1024 * 1024)))
            chunk_size  = math.ceil(file_size / num_threads)
            self.total  = 0
            self.lock   = threading.Lock()
            t0          = time.time()
            self.last_t = 0.0

            def fetch_chunk(idx, start, end):
                if not self.is_running:
                    return
                h2 = ua.copy()
                h2["Range"] = f"bytes={start}-{end}"
                tmp = f"{self.save_path}.part{idx}"
                try:
                    with requests.get(self.url, headers=h2, stream=True, timeout=30) as r:
                        r.raise_for_status()
                        with open(tmp, "wb") as fp:
                            for chunk in r.iter_content(65536):
                                if not self.is_running:
                                    break
                                if chunk:
                                    fp.write(chunk)
                                    with self.lock:
                                        self.total += len(chunk)
                                        now = time.time()
                                        if now - self.last_t > 0.2:
                                            self.last_t = now
                                            elapsed = now - t0 or 0.001
                                            speed   = (self.total / 1_048_576) / elapsed
                                            pct     = int(self.total * 100 / file_size)
                                            self.progress.emit(pct, speed)
                except Exception as ex:
                    self.error.emit(f"Part {idx}: {ex}")

            with concurrent.futures.ThreadPoolExecutor(num_threads) as pool:
                futs = []
                for i in range(num_threads):
                    s = i * chunk_size
                    e = (s + chunk_size - 1) if i < num_threads - 1 else (file_size - 1)
                    futs.append(pool.submit(fetch_chunk, i, s, e))
                concurrent.futures.wait(futs)

            if not self.is_running:
                return

            with open(self.save_path, "wb") as out:
                for i in range(num_threads):
                    tmp = f"{self.save_path}.part{i}"
                    if os.path.exists(tmp):
                        with open(tmp, "rb") as fp:
                            out.write(fp.read())
                        os.remove(tmp)

            self.progress.emit(100, 0.0)
            self.done.emit(self.save_path)

        except Exception as exc:
            self.error.emit(str(exc))

    def _single_thread(self, headers):
        try:
            with requests.get(self.url, headers=headers, stream=True, timeout=30) as r:
                r.raise_for_status()
                total = int(r.headers.get("Content-Length", 0))
                dl    = 0
                t0    = time.time()
                last  = 0.0
                with open(self.save_path, "wb") as fp:
                    for chunk in r.iter_content(65536):
                        if not self.is_running:
                            break
                        if chunk:
                            fp.write(chunk)
                            dl += len(chunk)
                            if total:
                                now = time.time()
                                if now - last > 0.2:
                                    last  = now
                                    speed = (dl / 1_048_576) / (now - t0 or 0.001)
                                    self.progress.emit(int(dl * 100 / total), speed)
            self.done.emit(self.save_path)
        except Exception as exc:
            self.error.emit(str(exc))

    def stop(self):
        self.is_running = False


class DownloadWidget(QWidget):
    def __init__(self, filename: str, parent=None):
        super().__init__(parent)
        lay = QHBoxLayout(self)
        lay.setContentsMargins(10, 4, 10, 4)
        self.setStyleSheet("background:#1C1C20; border-radius:6px; margin:2px;")

        self.lbl   = QLabel(filename)
        self.bar   = QProgressBar()
        self.bar.setFixedHeight(14)
        self.bar.setValue(0)
        self.speed = QLabel("0.00 MB/s")
        self.speed.setFixedWidth(84)

        lay.addWidget(self.lbl,   2)
        lay.addWidget(self.bar,   2)
        lay.addWidget(self.speed)

    def on_progress(self, pct: int, spd: float):
        self.bar.setValue(pct)
        self.speed.setText(f"{spd:.2f} MB/s")

    def on_done(self, _):
        self.lbl.setText(self.lbl.text() + "  ✓")
        self.bar.setValue(100)
        self.speed.setText("Done")

    def on_error(self, _):
        self.speed.setText("Error")


# ════════════════════════════════════════════════════════════════════════════
# LIST MANAGER DIALOG
# ════════════════════════════════════════════════════════════════════════════
class ListDialog(QDialog):
    def __init__(self, title: str, items: list, on_click=None, parent=None):
        super().__init__(parent)
        self.setWindowTitle(title)
        self.resize(680, 460)
        lay = QVBoxLayout(self)
        lay.setContentsMargins(12, 12, 12, 12)
        lay.setSpacing(8)

        search = QLineEdit()
        search.setPlaceholderText("Tìm kiếm...")
        lay.addWidget(search)

        self.lst    = QListWidget()
        self._items = items
        self._populate(items)
        lay.addWidget(self.lst)

        search.textChanged.connect(lambda t: self._populate(
            [x for x in items
             if t.lower() in (x.get("url", "") + x.get("title", "")).lower()]
        ))

        if on_click:
            self.lst.itemDoubleClicked.connect(
                lambda item: on_click(item.data(Qt.ItemDataRole.UserRole))
            )

    def _populate(self, items: list):
        self.lst.clear()
        for it in items:
            label = (
                f"{it.get('time', ''):<16}  "
                f"{it.get('title', '')[:40]}  —  "
                f"{it.get('url', '')}"
            )
            wi = QListWidgetItem(label)
            wi.setData(Qt.ItemDataRole.UserRole, it.get("url", ""))
            self.lst.addItem(wi)


# ════════════════════════════════════════════════════════════════════════════
# DEVTOOLS WINDOW
# ════════════════════════════════════════════════════════════════════════════
class DevToolsWindow(QDialog):
    def __init__(self, page, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Nexus DevTools")
        self.resize(1020, 660)
        lay = QVBoxLayout(self)
        lay.setContentsMargins(0, 0, 0, 0)
        self.view = QWebEngineView()
        page.setDevToolsPage(self.view.page())
        lay.addWidget(self.view)


# ════════════════════════════════════════════════════════════════════════════
# MAIN BROWSER WINDOW
# ════════════════════════════════════════════════════════════════════════════
class NexusBrowser(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Nexus Browser")
        self.resize(1400, 900)

        self.dark_mode       = True
        self.data_mgr        = DataManager()
        self.idm_engine      = None
        self._sidebar_open   = False
        self._devtools_wins  = []
        self._ai_history     = []   # Gemini conversation history (keeps context)
        self._ai_thread      = None # active GeminiThread

        # ── WebEngine profile ────────────────────────────────────────────
        self.profile = QWebEngineProfile.defaultProfile()
        self.profile.setHttpCacheType(QWebEngineProfile.HttpCacheType.MemoryHttpCache)
        self.profile.setHttpUserAgent(
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/124.0.0.0 Safari/537.36 NexusBrowser/3.0"
        )
        self.ad_blocker = NexusAdBlocker(self)
        self.profile.setUrlRequestInterceptor(self.ad_blocker)
        self.profile.downloadRequested.connect(self._on_download_requested)

        self._apply_theme()
        self._build_ui()

        # ── Tab hibernation timer (5 min) ────────────────────────────────
        self._hibernate_timer = QTimer(self)
        self._hibernate_timer.timeout.connect(self._hibernate_bg_tabs)
        self._hibernate_timer.start(300_000)

        # ── DevTools shortcut ────────────────────────────────────────────
        sc = QShortcut(QKeySequence("F12"), self)
        sc.activated.connect(self._open_devtools)

        self._open_start_page()

    # ══════════════════════════════════════════════════════════════════════
    # THEME
    # ══════════════════════════════════════════════════════════════════════
    def _apply_theme(self):
        self.setStyleSheet(DARK_QSS if self.dark_mode else LIGHT_QSS)
        self._apply_palette()

    def _apply_palette(self):
        p = QPalette()
        if self.dark_mode:
            p.setColor(QPalette.ColorRole.Window,          QColor("#141417"))
            p.setColor(QPalette.ColorRole.WindowText,      QColor("#F5F5F7"))
            p.setColor(QPalette.ColorRole.Base,            QColor("#1C1C20"))
            p.setColor(QPalette.ColorRole.AlternateBase,   QColor("#141417"))
            p.setColor(QPalette.ColorRole.Text,            QColor("#F5F5F7"))
            p.setColor(QPalette.ColorRole.Button,          QColor("#1C1C20"))
            p.setColor(QPalette.ColorRole.ButtonText,      QColor("#F5F5F7"))
            p.setColor(QPalette.ColorRole.Highlight,       QColor("#0078D4"))
            p.setColor(QPalette.ColorRole.HighlightedText, QColor("#FFFFFF"))
            p.setColor(QPalette.ColorRole.Link,            QColor("#0078D4"))
        else:
            p.setColor(QPalette.ColorRole.Window,          QColor("#F5F5F7"))
            p.setColor(QPalette.ColorRole.WindowText,      QColor("#141417"))
            p.setColor(QPalette.ColorRole.Base,            QColor("#FFFFFF"))
            p.setColor(QPalette.ColorRole.AlternateBase,   QColor("#F5F5F7"))
            p.setColor(QPalette.ColorRole.Text,            QColor("#141417"))
            p.setColor(QPalette.ColorRole.Button,          QColor("#E5E5EA"))
            p.setColor(QPalette.ColorRole.ButtonText,      QColor("#141417"))
            p.setColor(QPalette.ColorRole.Highlight,       QColor("#0078D4"))
            p.setColor(QPalette.ColorRole.HighlightedText, QColor("#FFFFFF"))
            p.setColor(QPalette.ColorRole.Link,            QColor("#0078D4"))
        QApplication.instance().setPalette(p)

    def _set_theme(self, dark: bool):
        self.dark_mode = dark
        self._apply_theme()

    # ══════════════════════════════════════════════════════════════════════
    # UI BUILD
    # ══════════════════════════════════════════════════════════════════════
    def _build_ui(self):
        central = QWidget()
        central.setObjectName("central")
        self.setCentralWidget(central)
        root = QVBoxLayout(central)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)

        self._build_toolbar()

        # Page load progress bar (3 px ribbon)
        self.page_progress = QProgressBar()
        self.page_progress.setMaximumHeight(3)
        self.page_progress.setTextVisible(False)
        self.page_progress.setRange(0, 100)
        self.page_progress.hide()
        root.addWidget(self.page_progress)

        self._build_bookmark_bar(root)

        self.splitter = QSplitter(Qt.Orientation.Horizontal)
        root.addWidget(self.splitter)

        self._build_tabs()
        self._build_sidebar()
        self._build_download_bar(root)

    def _build_toolbar(self):
        tb = QToolBar()
        tb.setMovable(False)
        tb.setIconSize(QSize(18, 18))
        self.addToolBar(tb)

        def _btn(text, tip="", w=38):
            b = QPushButton(text)
            b.setFixedWidth(w)
            b.setToolTip(tip)
            return b

        self.btn_back    = _btn("◀", "Quay lại")
        self.btn_forward = _btn("▶", "Tiếp theo")
        self.btn_reload  = _btn("↻", "Tải lại / Dừng (F5)")
        self.btn_home    = _btn("🏠", "Trang chủ")
        for b in [self.btn_back, self.btn_forward, self.btn_reload, self.btn_home]:
            tb.addWidget(b)
        tb.addSeparator()

        self.lock_lbl = QLabel(" 🔒 ")
        self.lock_lbl.setToolTip("Kết nối bảo mật HTTPS")
        tb.addWidget(self.lock_lbl)

        self.url_bar = QLineEdit()
        self.url_bar.setPlaceholderText("Nhập địa chỉ web hoặc từ khóa tìm kiếm...")
        self.url_bar.returnPressed.connect(self._navigate)
        self.url_bar.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        tb.addWidget(self.url_bar)
        tb.addSeparator()

        self.btn_ai = QPushButton("🤖 Nexus AI")
        self.btn_ai.setObjectName("ai_btn")
        self.btn_ai.setFixedWidth(108)
        self.btn_ai.setCheckable(True)
        self.btn_ai.setToolTip("Bật/Tắt Nexus AI Sidebar (Gemini 2.0 Flash)")
        self.btn_ai.clicked.connect(self._toggle_sidebar)
        tb.addWidget(self.btn_ai)

        self.btn_menu = QPushButton("⋮")
        self.btn_menu.setFixedWidth(36)
        self._menu = QMenu(self)
        self._build_menu()
        self.btn_menu.setMenu(self._menu)
        tb.addWidget(self.btn_menu)

        self.btn_back.clicked.connect(self._go_back)
        self.btn_forward.clicked.connect(self._go_forward)
        self.btn_reload.clicked.connect(self._reload_or_stop)
        self.btn_home.clicked.connect(self._open_start_page)

    def _build_menu(self):
        m = self._menu
        m.addAction("＋  Tab mới",        self._open_start_page)
        m.addSeparator()
        tm = m.addMenu("🎨  Giao diện")
        tm.addAction("🌙  Tối (Dark)",    lambda: self._set_theme(True))
        tm.addAction("☀️  Sáng (Light)",  lambda: self._set_theme(False))
        m.addSeparator()
        m.addAction("🕐  Lịch sử",        self._show_history)
        m.addAction("★  Dấu trang",       self._show_bookmarks)
        m.addAction("☆  Thêm dấu trang",  self._bookmark_current)
        m.addSeparator()
        m.addAction("🔍  Thu phóng +",    self._zoom_in)
        m.addAction("🔍  Thu phóng −",    self._zoom_out)
        m.addAction("🔍  Chuẩn (100%)",   self._zoom_reset)
        m.addSeparator()
        m.addAction("🌐  VPN WARP",       self._warp)
        m.addAction("🧅  Tor Proxy",       self._tor)
        m.addAction("🔑  Mật khẩu",       self._gen_password)
        m.addAction("🧩  Tiện ích",        self._show_extensions)
        m.addAction("🌏  Dịch trang",      self._translate)
        m.addSeparator()
        m.addAction("🗑️  Xóa dữ liệu",   self._clear_data)
        m.addAction("ℹ️  Về Nexus",        self._about)

    def _build_bookmark_bar(self, parent_layout):
        self.bm_bar = QWidget()
        bm_lay = QHBoxLayout(self.bm_bar)
        bm_lay.setContentsMargins(8, 3, 8, 3)
        bm_lay.setSpacing(4)

        defaults = [
            ("Google",   "https://google.com"),
            ("YouTube",  "https://youtube.com"),
            ("GitHub",   "https://github.com"),
            ("Facebook", "https://facebook.com"),
        ]
        for label, url in defaults:
            b = QPushButton(label)
            b.setFixedHeight(24)
            b.clicked.connect(lambda _, u=url: self._load_url(u))
            bm_lay.addWidget(b)

        bm_lay.addStretch()
        add_btn = QPushButton("＋ Dấu trang")
        add_btn.setFixedHeight(24)
        add_btn.clicked.connect(self._bookmark_current)
        bm_lay.addWidget(add_btn)
        parent_layout.addWidget(self.bm_bar)

    def _build_tabs(self):
        self.tabs = QTabWidget()
        self.tabs.setDocumentMode(True)
        self.tabs.setTabsClosable(True)
        self.tabs.setMovable(True)
        self.tabs.tabCloseRequested.connect(self._close_tab)
        self.tabs.currentChanged.connect(self._on_tab_changed)

        new_tab_btn = QPushButton(" ＋ ")
        new_tab_btn.setFixedSize(32, 28)
        new_tab_btn.setToolTip("Tab mới")
        new_tab_btn.clicked.connect(self._open_start_page)
        self.tabs.setCornerWidget(new_tab_btn, Qt.Corner.TopRightCorner)

        self.splitter.addWidget(self.tabs)

    def _build_sidebar(self):
        self.sidebar = QWidget()
        self.sidebar.setFixedWidth(320)
        sl = QVBoxLayout(self.sidebar)
        sl.setContentsMargins(8, 6, 8, 6)
        sl.setSpacing(6)

        # ── Header ────────────────────────────────────────────────────────
        hdr = QHBoxLayout()
        title = QLabel("🤖  <b>Nexus AI</b>")
        title.setTextFormat(Qt.TextFormat.RichText)
        self._ai_status_dot = QLabel("●")
        self._ai_status_dot.setStyleSheet("color:#8E8E93; font-size:10px;")
        self._ai_status_dot.setToolTip("Trạng thái: chưa cấu hình API key")
        close_btn = QPushButton("✕")
        close_btn.setFixedSize(26, 26)
        close_btn.clicked.connect(self._toggle_sidebar)
        hdr.addWidget(title)
        hdr.addWidget(self._ai_status_dot)
        hdr.addStretch()
        hdr.addWidget(close_btn)
        sl.addLayout(hdr)

        # ── API Key section ───────────────────────────────────────────────
        key_frame = QFrame()
        key_frame.setStyleSheet("QFrame { background:#1C1C20; border-radius:8px; }")
        kf = QVBoxLayout(key_frame)
        kf.setContentsMargins(8, 8, 8, 8)
        kf.setSpacing(4)

        key_lbl = QLabel("🔑  Gemini API Key")
        key_lbl.setStyleSheet("font-size:11px; font-weight:600; color:#8E8E93;")
        kf.addWidget(key_lbl)

        key_row = QHBoxLayout()
        self.api_key_input = QLineEdit()
        self.api_key_input.setPlaceholderText("Dán API key vào đây...")
        self.api_key_input.setEchoMode(QLineEdit.EchoMode.Password)
        saved_key = self.data_mgr.get_api_key()
        if saved_key:
            self.api_key_input.setText(saved_key)
        self._save_key_btn = QPushButton("Lưu")
        self._save_key_btn.setFixedWidth(48)
        self._save_key_btn.clicked.connect(self._save_api_key)
        key_row.addWidget(self.api_key_input)
        key_row.addWidget(self._save_key_btn)
        kf.addLayout(key_row)

        hint = QLabel(
            '<a href="https://aistudio.google.com/app/apikey" '
            'style="color:#0078D4;">Lấy key miễn phí tại Google AI Studio →</a>'
        )
        hint.setOpenExternalLinks(True)
        hint.setStyleSheet("font-size:10px;")
        kf.addWidget(hint)
        sl.addWidget(key_frame)

        if saved_key:
            self._set_ai_dot_ready()

        # ── Divider ───────────────────────────────────────────────────────
        line = QFrame()
        line.setFrameShape(QFrame.Shape.HLine)
        sl.addWidget(line)

        # ── Chat display ──────────────────────────────────────────────────
        self.ai_chat = QTextBrowser()
        self.ai_chat.setReadOnly(True)
        self.ai_chat.setOpenLinks(True)
        self.ai_chat.setHtml(
            "<p style='color:#8E8E93; margin:6px 2px;'>"
            "<b style='color:#0078D4;'>Nexus AI:</b>&nbsp;"
            "Xin chào! Tôi là <b>Nexus AI</b> — vận hành bởi "
            "<b>Google Gemini 2.0 Flash</b>.<br>"
            "Nhập API key ở trên rồi bắt đầu hỏi nhé! 🚀"
            "</p>"
        )
        sl.addWidget(self.ai_chat, 1)

        # ── Status row + clear ────────────────────────────────────────────
        ctrl = QHBoxLayout()
        self._ai_thinking_lbl = QLabel("")
        self._ai_thinking_lbl.setStyleSheet("color:#8E8E93; font-size:11px;")
        clear_btn = QPushButton("🗑 Xóa chat")
        clear_btn.setFixedHeight(24)
        clear_btn.clicked.connect(self._clear_ai_chat)
        ctrl.addWidget(self._ai_thinking_lbl)
        ctrl.addStretch()
        ctrl.addWidget(clear_btn)
        sl.addLayout(ctrl)

        # ── Input row ─────────────────────────────────────────────────────
        row = QHBoxLayout()
        self.ai_input = QLineEdit()
        self.ai_input.setPlaceholderText("Hỏi Nexus AI...")
        self.ai_input.returnPressed.connect(self._send_ai)
        self._send_btn = QPushButton("Gửi")
        self._send_btn.setFixedWidth(56)
        self._send_btn.clicked.connect(self._send_ai)
        row.addWidget(self.ai_input)
        row.addWidget(self._send_btn)
        sl.addLayout(row)

        self.splitter.addWidget(self.sidebar)
        self.sidebar.setVisible(False)
        self.splitter.setSizes([1400, 0])

    def _build_download_bar(self, parent_layout):
        self.dl_bar = QWidget()
        self.dl_bar.setStyleSheet("border-top:1px solid #2C2C30;")
        self.dl_layout = QVBoxLayout(self.dl_bar)
        self.dl_layout.setContentsMargins(10, 4, 10, 4)
        self.dl_layout.setSpacing(4)
        self.dl_bar.hide()
        parent_layout.addWidget(self.dl_bar)

    # ══════════════════════════════════════════════════════════════════════
    # TAB MANAGEMENT
    # ══════════════════════════════════════════════════════════════════════
    def _open_start_page(self):
        view = QWebEngineView()
        view.setHtml(build_start_page(self.dark_mode))
        view.titleChanged.connect(lambda t, v=view: self._update_tab_title(v, t))
        view.loadProgress.connect(self._on_load_progress)
        view.loadFinished.connect(self._on_load_finished)
        view.urlChanged.connect(lambda u, v=view: self._on_url_changed(u, v))
        view.page().renderProcessTerminated.connect(
            lambda _s, _ec, v=view: QTimer.singleShot(500, lambda: self._crash_reload(v))
        )
        idx = self.tabs.addTab(view, "Trang chủ")
        self.tabs.setCurrentIndex(idx)

    def _add_tab(self, url: str, title: str = "Đang tải..."):
        qurl = QUrl(url)
        if not qurl.isValid() or not qurl.scheme():
            qurl = QUrl("https://" + url)

        if any(bad in url for bad in ["malware", "phishing", "virus", "trojan"]):
            self._warn_av(url)
            return

        view = QWebEngineView()
        view.setUrl(qurl)
        view.titleChanged.connect(lambda t, v=view: self._update_tab_title(v, t))
        view.loadProgress.connect(self._on_load_progress)
        view.loadFinished.connect(self._on_load_finished)
        view.urlChanged.connect(lambda u, v=view: self._on_url_changed(u, v))
        view.iconChanged.connect(lambda ico, v=view: self._update_tab_icon(v, ico))
        view.page().renderProcessTerminated.connect(
            lambda _s, _ec, v=view: QTimer.singleShot(500, lambda: self._crash_reload(v))
        )
        idx = self.tabs.addTab(view, title)
        self.tabs.setCurrentIndex(idx)
        self._inject_ext(view)

    def _current_view(self):
        w = self.tabs.currentWidget()
        return w if isinstance(w, QWebEngineView) else None

    def _close_tab(self, idx: int):
        if self.tabs.count() <= 1:
            self.close()
            return
        w = self.tabs.widget(idx)
        self.tabs.removeTab(idx)
        if isinstance(w, QWebEngineView):
            w.setUrl(QUrl("about:blank"))
            w.deleteLater()
        elif isinstance(w, QLabel):
            w.deleteLater()

    def _on_tab_changed(self, idx: int):
        if idx < 0:
            return
        w = self.tabs.widget(idx)
        if isinstance(w, QLabel) and w.property("url"):
            QTimer.singleShot(0, lambda: self._restore_tab(w))
        elif isinstance(w, QWebEngineView):
            self.url_bar.setText(w.url().toString())
            self.setWindowTitle(f"Nexus Browser — {w.title()}")
            self._update_lock_icon(w.url())

    def _update_tab_title(self, view, title: str):
        idx = self.tabs.indexOf(view)
        if idx >= 0:
            self.tabs.setTabText(idx, title[:18] if title else "…")
            if self.tabs.currentIndex() == idx:
                self.setWindowTitle(f"Nexus Browser — {title}")

    def _update_tab_icon(self, view, icon):
        idx = self.tabs.indexOf(view)
        if idx >= 0 and not icon.isNull():
            self.tabs.setTabIcon(idx, icon)

    def _inject_ext(self, view):
        for name, code in NEXUS_EXTENSIONS.items():
            ok, _ = scan_extension_code(code)
            if ok:
                view.page().runJavaScript(code)

    def _crash_reload(self, view):
        idx = self.tabs.indexOf(view)
        if idx >= 0:
            url = view.url().toString()
            if url and url != "about:blank":
                view.reload()

    # ══════════════════════════════════════════════════════════════════════
    # NAVIGATION
    # ══════════════════════════════════════════════════════════════════════
    def _navigate(self):
        text = self.url_bar.text().strip()
        if not text:
            return
        if " " in text or "." not in text:
            url = "https://www.google.com/search?q=" + requests.utils.quote(text)
        elif not text.startswith("http"):
            url = "https://" + text
        else:
            url = text

        if any(bad in url for bad in ["malware", "phishing", "virus", "trojan"]):
            self._warn_av(url)
            return

        v = self._current_view()
        if v:
            v.setUrl(QUrl(url))
        else:
            self._add_tab(url)

    def _load_url(self, url: str):
        v = self._current_view()
        if v:
            v.setUrl(QUrl(url))
        else:
            self._add_tab(url)

    def _go_back(self):
        v = self._current_view()
        if v:
            v.back()

    def _go_forward(self):
        v = self._current_view()
        if v:
            v.forward()

    def _reload_or_stop(self):
        v = self._current_view()
        if not v:
            return
        if v.page().isLoading():
            v.stop()
            self.btn_reload.setText("↻")
        else:
            v.reload()

    def _on_url_changed(self, qurl, view):
        if self.tabs.currentWidget() is view:
            self.url_bar.setText(qurl.toString())
            self._update_lock_icon(qurl)
        self.data_mgr.add_history(qurl.toString(), view.title())

    def _update_lock_icon(self, qurl):
        if qurl.scheme() == "https":
            self.lock_lbl.setText(" 🔒 ")
            self.lock_lbl.setToolTip("Kết nối bảo mật HTTPS")
        else:
            self.lock_lbl.setText(" 🔓 ")
            self.lock_lbl.setToolTip("Kết nối không bảo mật HTTP")

    def _on_load_progress(self, pct: int):
        if pct < 100:
            self.page_progress.show()
            self.page_progress.setValue(pct)
            self.btn_reload.setText("✕")
        else:
            self.page_progress.setValue(100)
            QTimer.singleShot(300, self.page_progress.hide)
            self.btn_reload.setText("↻")

    def _on_load_finished(self, ok: bool):
        self.btn_reload.setText("↻")
        if not ok:
            v = self._current_view()
            if v:
                v.setHtml(ERROR_PAGE_HTML)

    def _warn_av(self, url: str):
        QMessageBox.critical(
            self, "Nexus AV — URL nguy hiểm",
            f"⚠  Phát hiện mẫu độc hại:\n{url}\n\nTruy cập bị chặn."
        )

    # ══════════════════════════════════════════════════════════════════════
    # DEVTOOLS
    # ══════════════════════════════════════════════════════════════════════
    def _open_devtools(self):
        v = self._current_view()
        if not v:
            return
        dw = DevToolsWindow(v.page(), self)
        self._devtools_wins.append(dw)
        dw.finished.connect(
            lambda: self._devtools_wins.remove(dw) if dw in self._devtools_wins else None
        )
        dw.show()

    # ══════════════════════════════════════════════════════════════════════
    # AI SIDEBAR
    # ══════════════════════════════════════════════════════════════════════
    def _toggle_sidebar(self):
        self._sidebar_open = not self._sidebar_open
        self.sidebar.setVisible(self._sidebar_open)
        self.btn_ai.setChecked(self._sidebar_open)
        if self._sidebar_open:
            self.splitter.setSizes([1080, 320])
        else:
            self.splitter.setSizes([1400, 0])

    def _save_api_key(self):
        key = self.api_key_input.text().strip()
        if not key:
            QMessageBox.warning(self, "Nexus AI", "Vui lòng nhập API key trước.")
            return
        self.data_mgr.set_api_key(key)
        self._set_ai_dot_ready()
        self.ai_chat.append(
            "<p style='color:#30D158; margin:4px 0;'>"
            "✔  API key đã được lưu. Bạn có thể bắt đầu hỏi Nexus AI!"
            "</p>"
        )

    def _set_ai_dot_ready(self):
        self._ai_status_dot.setStyleSheet("color:#30D158; font-size:10px;")
        self._ai_status_dot.setToolTip("Nexus AI: Sẵn sàng (Gemini 2.0 Flash)")

    def _set_ai_dot_busy(self):
        self._ai_status_dot.setStyleSheet("color:#FFD60A; font-size:10px;")
        self._ai_status_dot.setToolTip("Nexus AI: Đang xử lý...")

    def _set_ai_dot_error(self):
        self._ai_status_dot.setStyleSheet("color:#FF453A; font-size:10px;")
        self._ai_status_dot.setToolTip("Nexus AI: Lỗi kết nối")

    def _clear_ai_chat(self):
        self._ai_history.clear()
        self.ai_chat.setHtml(
            "<p style='color:#8E8E93; margin:6px 2px;'>"
            "<b style='color:#0078D4;'>Nexus AI:</b>&nbsp;"
            "Lịch sử trò chuyện đã được xóa. Tôi có thể giúp gì cho bạn?"
            "</p>"
        )

    def _send_ai(self):
        text = self.ai_input.text().strip()
        if not text:
            return

        api_key = self.data_mgr.get_api_key()
        if not api_key:
            self.ai_chat.append(
                "<p style='color:#FF453A; margin:4px 0;'>"
                "⚠  Chưa có API key. Vui lòng nhập và nhấn Lưu ở trên.<br>"
                '<a href="https://aistudio.google.com/app/apikey" '
                'style="color:#0078D4;">Lấy key miễn phí →</a>'
                "</p>"
            )
            return

        if self._ai_thread and self._ai_thread.isRunning():
            return

        self.ai_chat.append(
            f"<p style='margin:6px 2px;'>"
            f"<b style='color:#A78BFA;'>Bạn:</b>&nbsp;"
            f"{self._escape_html(text)}</p>"
        )
        self.ai_input.clear()
        self.ai_input.setEnabled(False)
        self._send_btn.setEnabled(False)
        self._ai_thinking_lbl.setText("● Nexus AI đang suy nghĩ...")
        self._set_ai_dot_busy()

        self._ai_thread = GeminiThread(api_key, self._ai_history, text, self)
        self._ai_thread.reply.connect(lambda r, t=text: self._on_ai_reply(t, r))
        self._ai_thread.err.connect(self._on_ai_error)
        self._ai_thread.start()

    def _on_ai_reply(self, user_text: str, reply_text: str):
        self._ai_history.append({"role": "user",  "parts": [{"text": user_text}]})
        self._ai_history.append({"role": "model", "parts": [{"text": reply_text}]})
        if len(self._ai_history) > 40:
            self._ai_history = self._ai_history[-40:]

        html_reply = self._escape_html(reply_text).replace("\n", "<br>")
        self.ai_chat.append(
            f"<p style='margin:6px 2px; line-height:1.5;'>"
            f"<b style='color:#0078D4;'>Nexus AI:</b>&nbsp;"
            f"{html_reply}</p>"
        )
        self._reset_ai_ui()
        self._set_ai_dot_ready()

    def _on_ai_error(self, code: str):
        messages = {
            "no_key":     "⚠  Chưa có API key.",
            "bad_key":    "❌  API key không hợp lệ. Kiểm tra tại Google AI Studio.",
            "rate_limit": "⏳  Vượt giới hạn tốc độ. Đợi 1 phút rồi thử lại.",
            "no_network": "🌐  Không có kết nối Internet.",
            "timeout":    "⏱  Gemini phản hồi quá chậm. Thử lại sau.",
            "empty":      "⚠  Gemini trả về phản hồi rỗng. Thử lại.",
        }
        msg = messages.get(code, f"⚠  Lỗi: {code}")
        self.ai_chat.append(
            f"<p style='color:#FF453A; margin:4px 2px;'>{msg}</p>"
        )
        self._reset_ai_ui()
        self._set_ai_dot_error()

    def _reset_ai_ui(self):
        self.ai_input.setEnabled(True)
        self._send_btn.setEnabled(True)
        self._ai_thinking_lbl.setText("")
        self.ai_input.setFocus()

    @staticmethod
    def _escape_html(text: str) -> str:
        return (text.replace("&", "&amp;")
                    .replace("<", "&lt;")
                    .replace(">", "&gt;")
                    .replace('"', "&quot;"))

    # ══════════════════════════════════════════════════════════════════════
    # TAB HIBERNATION
    # ══════════════════════════════════════════════════════════════════════
    def _hibernate_bg_tabs(self):
        cur = self.tabs.currentIndex()
        to_sleep = [
            i for i in range(self.tabs.count())
            if i != cur and isinstance(self.tabs.widget(i), QWebEngineView)
        ]
        for i in reversed(to_sleep):
            w     = self.tabs.widget(i)
            url   = w.url().toString()
            title = w.title() or url
            self.tabs.removeTab(i)
            w.setUrl(QUrl("about:blank"))
            w.deleteLater()

            ph = QLabel(f"❄  {title}\nTab đóng băng — click để hồi phục")
            ph.setAlignment(Qt.AlignmentFlag.AlignCenter)
            ph.setStyleSheet(
                "font-size:16px; color:#8E8E93; background:#141417; border-radius:8px;"
            )
            ph.setProperty("url",   url)
            ph.setProperty("title", title)
            self.tabs.insertTab(i, ph, f"❄ {title[:12]}")

    def _restore_tab(self, ph):
        idx = self.tabs.indexOf(ph)
        if idx < 0:
            return
        url   = ph.property("url")
        title = ph.property("title")
        self.tabs.removeTab(idx)
        ph.deleteLater()
        self._add_tab(url, title)

    # ══════════════════════════════════════════════════════════════════════
    # DOWNLOADS
    # ══════════════════════════════════════════════════════════════════════
    def _on_download_requested(self, item):
        url  = item.url().toString()
        name = item.suggestedFileName()
        item.cancel()

        path, _ = QFileDialog.getSaveFileName(self, "Lưu file", name)
        if not path:
            return

        self.dl_bar.show()
        while self.dl_layout.count():
            old = self.dl_layout.takeAt(0)
            if old.widget():
                old.widget().deleteLater()

        dw = DownloadWidget(name, self)
        self.dl_layout.addWidget(dw)

        if self.idm_engine and self.idm_engine.isRunning():
            self.idm_engine.stop()
            self.idm_engine.wait()

        self.idm_engine = NexusIDMEngine(url, path, self)
        self.idm_engine.progress.connect(dw.on_progress)
        self.idm_engine.done.connect(dw.on_done)
        self.idm_engine.error.connect(dw.on_error)
        self.idm_engine.start()

    # ══════════════════════════════════════════════════════════════════════
    # ZOOM
    # ══════════════════════════════════════════════════════════════════════
    def _zoom_in(self):
        v = self._current_view()
        if v:
            v.setZoomFactor(min(5.0, v.zoomFactor() + 0.1))

    def _zoom_out(self):
        v = self._current_view()
        if v:
            v.setZoomFactor(max(0.25, v.zoomFactor() - 0.1))

    def _zoom_reset(self):
        v = self._current_view()
        if v:
            v.setZoomFactor(1.0)

    # ══════════════════════════════════════════════════════════════════════
    # MENU ACTIONS
    # ══════════════════════════════════════════════════════════════════════
    def _show_history(self):
        ListDialog(
            "Lịch Sử Duyệt Web",
            self.data_mgr.data["history"],
            on_click=self._load_url,
            parent=self,
        ).exec()

    def _show_bookmarks(self):
        ListDialog(
            "Dấu Trang",
            self.data_mgr.data["bookmarks"],
            on_click=self._load_url,
            parent=self,
        ).exec()

    def _bookmark_current(self):
        v = self._current_view()
        if not v:
            return
        url   = v.url().toString()
        title = v.title()
        if self.data_mgr.add_bookmark(url, title):
            QMessageBox.information(self, "Đã lưu", f"★ Đã thêm dấu trang:\n{title}")
        else:
            self.data_mgr.remove_bookmark(url)
            QMessageBox.information(self, "Đã xóa", f"Đã xóa dấu trang:\n{title}")

    def _gen_password(self):
        chars = string.ascii_letters + string.digits + "!@#$%^&*()-_=+"
        pwd   = "".join(secrets.choice(chars) for _ in range(18))
        QMessageBox.information(
            self, "Password Manager",
            f"Mật khẩu mạnh (18 ký tự):\n\n{pwd}\n\nHãy sao chép và lưu lại!"
        )

    def _show_extensions(self):
        QMessageBox.information(
            self, "Extensions Manager",
            f"Đã tải: {len(NEXUS_EXTENSIONS)} tiện ích.\n"
            "Tất cả đã được quét & xác minh an toàn bởi Nexus Scanner."
        )

    def _warp(self):
        proxy = QNetworkProxy(QNetworkProxy.ProxyType.Socks5Proxy, "127.0.0.1", 40001)
        QNetworkProxy.setApplicationProxy(proxy)
        QMessageBox.information(self, "WARP VPN", "✔ Cloudflare WARP đã bật (SOCKS5 :40001)")

    def _tor(self):
        proxy = QNetworkProxy(QNetworkProxy.ProxyType.Socks5Proxy, "127.0.0.1", 9050)
        QNetworkProxy.setApplicationProxy(proxy)
        QMessageBox.information(self, "Tor Proxy", "✔ Tor Proxy đã bật (:9050)")

    def _translate(self):
        v = self._current_view()
        if v:
            url = v.url().toString()
            v.setUrl(QUrl(f"https://translate.google.com/translate?sl=auto&tl=vi&u={url}"))

    def _clear_data(self):
        ret = QMessageBox.question(
            self, "Xóa dữ liệu",
            "Xóa toàn bộ lịch sử, dấu trang và cache?\n(API key sẽ được giữ lại)",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
        )
        if ret == QMessageBox.StandardButton.Yes:
            self.data_mgr.clear_all()
            self.profile.clearHttpCache()
            QMessageBox.information(self, "Hoàn tất", "✔ Đã xóa toàn bộ dữ liệu duyệt web.")

    def _about(self):
        QMessageBox.about(
            self, "Về Nexus Browser",
            "Nexus Browser  v3.0\n"
            "──────────────────────────────\n"
            "Developed by Loc Shadow\n\n"
            "✔ Fluent Design UI (Dark / Light)\n"
            "✔ Tab Hibernation — tiết kiệm RAM\n"
            "✔ IDM 64-Thread Download Engine\n"
            "✔ Network-Level Ad Blocker\n"
            "✔ F12 DevTools (Chromium)\n"
            "✔ Custom Error Page\n"
            "✔ WARP VPN + Tor Proxy\n"
            "✔ Nexus AI (Google Gemini 2.0 Flash)\n"
            "✔ HiDPI + Segoe UI Antialiasing\n"
            "──────────────────────────────\n"
            "Built with PyQt6 + WebEngine"
        )


# ════════════════════════════════════════════════════════════════════════════
# ENTRY POINT
# ════════════════════════════════════════════════════════════════════════════
def _set_dark_palette(app):
    p = QPalette()
    p.setColor(QPalette.ColorRole.Window,          QColor("#141417"))
    p.setColor(QPalette.ColorRole.WindowText,      QColor("#F5F5F7"))
    p.setColor(QPalette.ColorRole.Base,            QColor("#1C1C20"))
    p.setColor(QPalette.ColorRole.AlternateBase,   QColor("#141417"))
    p.setColor(QPalette.ColorRole.ToolTipBase,     QColor("#1C1C20"))
    p.setColor(QPalette.ColorRole.ToolTipText,     QColor("#F5F5F7"))
    p.setColor(QPalette.ColorRole.Text,            QColor("#F5F5F7"))
    p.setColor(QPalette.ColorRole.Button,          QColor("#1C1C20"))
    p.setColor(QPalette.ColorRole.ButtonText,      QColor("#F5F5F7"))
    p.setColor(QPalette.ColorRole.BrightText,      QColor("#FF453A"))
    p.setColor(QPalette.ColorRole.Link,            QColor("#0078D4"))
    p.setColor(QPalette.ColorRole.Highlight,       QColor("#0078D4"))
    p.setColor(QPalette.ColorRole.HighlightedText, QColor("#FFFFFF"))
    app.setPalette(p)


if __name__ == "__main__":
    QApplication.setHighDpiScaleFactorRoundingPolicy(
        Qt.HighDpiScaleFactorRoundingPolicy.PassThrough
    )

    app = QApplication(sys.argv)
    app.setApplicationName("Nexus Browser")
    app.setApplicationVersion("3.0")

    font = QFont("Segoe UI", 10)
    font.setStyleStrategy(QFont.StyleStrategy.PreferAntialias)
    app.setFont(font)

    _set_dark_palette(app)

    browser = NexusBrowser()
    browser.show()
    sys.exit(app.exec())
