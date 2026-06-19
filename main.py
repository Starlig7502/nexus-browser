# -*- coding: utf-8 -*-
import sys
import os
import json
import secrets
import string
import math
import time
import re
import threading
import concurrent.futures
import requests
import gc
from datetime import datetime

# ── HiDPI & Chromium flags - OPTIMIZED FOR LOW RAM ───────────────────
os.environ.setdefault("QT_ENABLE_HIGHDPI_SCALING", "1")
os.environ.setdefault("QT_FONT_DPI", "96")
os.environ.setdefault("QT_SCALE_FACTOR_ROUNDING_POLICY", "PassThrough")
os.environ.setdefault(
    "QTWEBENGINE_CHROMIUM_FLAGS",
    "--disable-gpu-shader-disk-cache "
    "--disk-cache-size=33554432 "  # 32MB instead of 64MB
    "--media-cache-size=5242880 "   # 5MB instead of 10MB
    "--disable-reading-from-canvas "
    "--process-per-site "           # Share processes
    "--ignore-gpu-blocklist "
    "--enable-gpu-rasterization "
    "--enable-features=NetworkService "
    "--disable-features=CalculateNativeWinOcclusion,PaintHolding "
    "--js-flags=--max-old-space-size=128 "  # Limit JS heap
)

from PyQt6.QtCore import (
    QUrl, QTimer, Qt, QSize, QThread, pyqtSignal, QObject, QPoint,
)
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QTabWidget, QToolBar, QLineEdit, QPushButton,
    QVBoxLayout, QHBoxLayout, QWidget, QSplitter, QTextEdit, QMessageBox,
    QLabel, QMenu, QDialog, QListWidget, QListWidgetItem, QProgressBar,
    QFileDialog, QSizePolicy, QFrame, QCheckBox, QComboBox, QSlider,
    QSpinBox, QGroupBox, QTabWidget as QTabW, QScrollArea, QGridLayout,
    QFormLayout, QDialogButtonBox, QStatusBar, QToolButton, QStackedWidget,
)
from PyQt6.QtWebEngineWidgets import QWebEngineView
from PyQt6.QtWebEngineCore import (
    QWebEngineProfile, QWebEngineUrlRequestInterceptor,
    QWebEnginePage, QWebEngineFindTextResult,
)
from PyQt6.QtNetwork import QNetworkProxy
from PyQt6.QtGui import (
    QFont, QPalette, QColor, QShortcut, QKeySequence, QClipboard, QIcon,
)

try:
    import pyperclip
    _CLIP = True
except ImportError:
    _CLIP = False

# ════════════════════════════════════════════════════════════════════════════
# CONSTANTS
# ════════════════════════════════════════════════════════════════════════════
APP_NAME    = "Nexus Browser"
APP_VERSION = "4.1-Lite"
ACCENT      = "#0078D4"

GEMINI_URL = (
    "https://generativelanguage.googleapis.com/v1beta/models/"
    "gemini-2.0-flash:generateContent"
)

# ════════════════════════════════════════════════════════════════════════════
# TRANSLATIONS
# ════════════════════════════════════════════════════════════════════════════
TRANSLATIONS = {
    "vi": {
        "search_placeholder": "Tìm kiếm hoặc nhập địa chỉ...",
        "home": "Trang chủ",
        "new_tab": "Tab mới",
        "history": "🕐 Lịch sử",
        "bookmarks": "★ Dấu trang",
        "passwords": "🔑 Mật khẩu",
        "adblock": "🛡 AdBlock",
        "vpn": "🌐 WARP VPN",
        "tor": "🧅 Tor Proxy",
        "disable_proxy": "❌ Tắt Proxy",
        "find_page": "🔍 Tìm trong trang",
        "devtools": "🔍 DevTools (F12)",
        "theme": "🌗 Dark/Light Mode",
        "language": "🌐 Ngôn ngữ",
        "clear_data": "🗑 Xóa dữ liệu",
        "about": "ℹ Về Nexus",
        "extensions": "📦 Tiện ích",
        "translate": "🌐 Dịch trang này",
        "pdf": "📄 Lưu PDF",
        "zoom_in": "🔍 Phóng to",
        "zoom_out": "🔍 Thu nhỏ",
        "zoom_reset": "🔍 Reset zoom",
    },
    "en": {
        "search_placeholder": "Search or enter address...",
        "home": "Home",
        "new_tab": "New Tab",
        "history": "🕐 History",
        "bookmarks": "★ Bookmarks",
        "passwords": "🔑 Passwords",
        "adblock": "🛡 AdBlock",
        "vpn": "🌐 WARP VPN",
        "tor": "🧅 Tor Proxy",
        "disable_proxy": "❌ Disable Proxy",
        "find_page": "🔍 Find in Page",
        "devtools": "🔍 DevTools (F12)",
        "theme": "🌗 Dark/Light Mode",
        "language": "🌐 Language",
        "clear_data": "🗑 Clear Data",
        "about": "ℹ About Nexus",
        "extensions": "📦 Extensions",
        "translate": "🌐 Translate Page",
        "pdf": "📄 Save as PDF",
        "zoom_in": "🔍 Zoom In",
        "zoom_out": "🔍 Zoom Out",
        "zoom_reset": "🔍 Reset Zoom",
    }
}

# ════════════════════════════════════════════════════════════════════════════
# START PAGE WITH SEARCH BAR
# ════════════════════════════════════════════════════════════════════════════
def build_start_page(dark: bool, lang: str = "vi") -> str:
    bg       = "#141417" if dark else "#F5F5F7"
    card_bg  = "#1C1C20" if dark else "#FFFFFF"
    text     = "#F5F5F7" if dark else "#141417"
    subtext  = "#8E8E93" if dark else "#6E6E73"
    inp_bg   = card_bg
    inp_brd  = "#2C2C30" if dark else "#D1D1D6"
    
    search_text = TRANSLATIONS[lang]["search_placeholder"]
    
    return f"""<!DOCTYPE html>
<html>
<head>
<meta charset="utf-8">
<style>
    * {{ margin: 0; padding: 0; box-sizing: border-box; }}
    body {{
        background-color: {bg}; 
        color: {text}; 
        font-family: 'Segoe UI', system-ui, sans-serif;
        display: flex; 
        flex-direction: column; 
        align-items: center; 
        justify-content: center;
        height: 100vh; 
        overflow: hidden;
    }}
    .logo {{ 
        font-size: 48px; 
        margin-bottom: 10px; 
        font-weight: 700; 
        letter-spacing: 4px;
        background: linear-gradient(135deg, #0078D4, #00BCF2);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
    }}
    .tagline {{ color: {subtext}; margin-bottom: 40px; font-size: 14px; }}
    .search-box {{
        width: 600px;
        max-width: 90%;
        margin-bottom: 40px;
    }}
    .search-box input {{
        width: 100%;
        padding: 16px 24px;
        font-size: 16px;
        border: 2px solid {inp_brd};
        border-radius: 30px;
        background: {inp_bg};
        color: {text};
        outline: none;
        transition: all 0.3s ease;
    }}
    .search-box input:focus {{
        border-color: #0078D4;
        box-shadow: 0 0 0 4px rgba(0,120,212,0.1);
    }}
    .grid {{ 
        display: grid; 
        grid-template-columns: repeat(4, 1fr); 
        gap: 16px; 
        max-width: 800px;
        padding: 0 20px;
    }}
    .card {{
        background: {card_bg}; 
        padding: 20px; 
        border-radius: 12px; 
        text-align: center;
        text-decoration: none; 
        color: {text}; 
        transition: all 0.2s ease;
        display: flex; 
        flex-direction: column; 
        align-items: center; 
        gap: 8px;
        cursor: pointer;
    }}
    .card:hover {{ 
        transform: translateY(-4px); 
        box-shadow: 0 8px 24px rgba(0,0,0,0.15); 
    }}
    .icon {{ font-size: 28px; }}
    .title {{ font-size: 13px; font-weight: 500; }}
</style>
</head>
<body>
    <div class="logo">NEXUS</div>
    <div class="tagline">TRÌNH DUYỆT THẾ HỆ MỚI - TỐI ƯU RAM</div>
    
    <div class="search-box">
        <input type="text" id="searchInput" placeholder="{search_text}" 
               onkeypress="if(event.key==='Enter')doSearch()">
    </div>
    
    <div class="grid">
        <a href="https://google.com" class="card"><div class="icon">🔍</div><div class="title">Google</div></a>
        <a href="https://youtube.com" class="card"><div class="icon">▶️</div><div class="title">YouTube</div></a>
        <a href="https://github.com" class="card"><div class="icon">🐙</div><div class="title">GitHub</div></a>
        <a href="https://facebook.com" class="card"><div class="icon">📘</div><div class="title">Facebook</div></a>
        <a href="https://mail.google.com" class="card"><div class="icon">✉️</div><div class="title">Gmail</div></a>
        <a href="https://chat.openai.com" class="card"><div class="icon">🤖</div><div class="title">ChatGPT</div></a>
        <a href="https://translate.google.com" class="card"><div class="icon">🌐</div><div class="title">Dịch</div></a>
        <a href="https://news.ycombinator.com" class="card"><div class="icon">📰</div><div class="title">HN</div></a>
    </div>
    
    <script>
        function doSearch() {{
            var q = document.getElementById('searchInput').value;
            if(q) {{
                window.location = 'https://www.google.com/search?q=' + encodeURIComponent(q);
            }}
        }}
    </script>
</body>
</html>"""

ERROR_PAGE_HTML = """<!DOCTYPE html>
<html><head><meta charset="utf-8">
<style>
    body { background: #141417; color: #F5F5F7; font-family: 'Segoe UI', sans-serif; 
           display: flex; flex-direction: column; align-items: center; justify-content: center; 
           height: 100vh; margin: 0; }
    h1 { font-size: 64px; margin: 0; } 
    p { color: #8E8E93; font-size: 18px; }
    .btn { margin-top: 20px; padding: 10px 24px; background: #0078D4; color: white; 
           border-radius: 8px; text-decoration: none; font-weight: 600; }
</style></head>
<body>
    <h1>🌐</h1>
    <p>Không thể kết nối. Trang web không phản hồi hoặc mạng bị gián đoạn.</p>
    <a href="javascript:history.back()" class="btn">◀ Quay lại</a>
</body></html>"""

# ════════════════════════════════════════════════════════════════════════════
# QSS - OPTIMIZED
# ════════════════════════════════════════════════════════════════════════════
def _qss(dark: bool) -> str:
    if dark:
        bg, card, text, brd, sub = "#141417", "#1C1C20", "#F5F5F7", "#2C2C30", "#8E8E93"
        hover, pressed = "#2C2C30", "#3A3A40"
    else:
        bg, card, text, brd, sub = "#F5F5F7", "#FFFFFF", "#141417", "#D1D1D6", "#6E6E73"
        hover, pressed = "#E5E5EA", "#D1D1D6"
        
    return f"""
    QMainWindow, QWidget#central {{ background: {bg}; color: {text}; }}
    QToolBar {{ background: {bg}; border: none; padding: 6px 8px; spacing: 5px; 
               border-bottom: 1px solid {brd}; }}
    QToolBar::separator {{ background: {brd}; width: 1px; margin: 4px 2px; }}
    
    QPushButton {{ background: {card}; color: {text}; border: none; 
                   padding: 7px 14px; border-radius: 7px; font-weight: 500; }}
    QPushButton:hover {{ background: {hover}; }}
    QPushButton:pressed {{ background: {pressed}; }}
    QPushButton:disabled {{ color: {sub}; }}
    
    QPushButton#ai_btn {{ background: transparent; color: {ACCENT}; 
                         border: 1.5px solid {ACCENT}; border-radius: 7px; 
                         padding: 6px 13px; font-weight: 700; }}
    QPushButton#ai_btn:hover {{ background: {ACCENT}22; }}
    QPushButton#ai_btn:checked {{ background: {ACCENT}; color: #fff; }}
    
    QPushButton#new_tab_btn {{ background: {ACCENT}; color: white; 
                              padding: 6px 16px; border-radius: 6px; 
                              font-weight: 700; font-size: 16px; }}
    QPushButton#new_tab_btn:hover {{ background: #106EBE; }}
    
    QPushButton.danger {{ background: #FF453A22; color: #FF453A; 
                         border: 1px solid #FF453A44; }}
    QPushButton.danger:hover {{ background: #FF453A44; }}
    
    QLineEdit {{ background: {card}; color: {text}; padding: 8px 12px; 
                border-radius: 7px; border: 1.5px solid {brd}; font-size: 14px; }}
    QLineEdit:focus {{ border: 1.5px solid {ACCENT}; }}
    
    QTabWidget::pane {{ border: none; background: {bg}; }}
    QTabBar {{ background: {bg}; }}
    QTabBar::tab {{ background: {bg}; color: {sub}; padding: 9px 18px; 
                   min-width: 90px; border-top-left-radius: 8px; 
                   border-top-right-radius: 8px; margin-right: 2px; }}
    QTabBar::tab:selected {{ background: {card}; color: {text}; font-weight: 700; }}
    QTabBar::tab:hover:!selected {{ background: {card}; }}
    
    QTextEdit {{ background: {card}; color: {text}; border: none; 
                border-radius: 7px; padding: 10px; font-size: 14px; line-height: 1.5; }}
    
    QMenu {{ background: {card}; border: 1px solid {brd}; 
            border-radius: 10px; padding: 4px; }}
    QMenu::item {{ padding: 9px 24px; border-radius: 6px; color: {text}; }}
    QMenu::item:selected {{ background: {hover}; }}
    QMenu::separator {{ height: 1px; background: {brd}; margin: 4px 0; }}
    
    QProgressBar {{ border: none; border-radius: 3px; background: {brd}; 
                   text-align: center; color: transparent; }}
    QProgressBar::chunk {{ background: {ACCENT}; border-radius: 3px; }}
    
    QDialog {{ background: {bg}; border-radius: 12px; color: {text}; }}
    
    QListWidget {{ background: {card}; border: 1px solid {brd}; 
                   border-radius: 8px; padding: 4px; color: {text}; }}
    QListWidget::item {{ padding: 10px 8px; border-radius: 6px; }}
    QListWidget::item:selected {{ background: {hover}; color: {text}; }}
    
    QLabel {{ color: {text}; }}
    
    QGroupBox {{ border: 1px solid {brd}; border-radius: 8px; 
                margin-top: 12px; padding: 8px; color: {text}; font-weight: 600; }}
    QGroupBox::title {{ subcontrol-origin: margin; left: 10px; padding: 0 4px; }}
    
    QScrollBar:vertical {{ background: {bg}; width: 8px; border-radius: 4px; }}
    QScrollBar::handle:vertical {{ background: {brd}; border-radius: 4px; min-height: 24px; }}
    QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{ height: 0; }}
    
    QSplitter::handle {{ background: {brd}; width: 1px; }}
    QStatusBar {{ background: {card}; color: {sub}; 
                 border-top: 1px solid {brd}; font-size: 12px; }}
    
    QComboBox {{ background: {card}; color: {text}; border: 1.5px solid {brd}; 
                border-radius: 7px; padding: 6px 10px; }}
    QSpinBox {{ background: {card}; color: {text}; border: 1.5px solid {brd}; 
               border-radius: 7px; padding: 6px 8px; }}
    QCheckBox {{ color: {text}; }}
    QCheckBox::indicator {{ width: 16px; height: 16px; border-radius: 4px; 
                           border: 2px solid {brd}; }}
    QCheckBox::indicator:checked {{ background: {ACCENT}; border-color: {ACCENT}; }}
    """

# ════════════════════════════════════════════════════════════════════════════
# AD BLOCKER - OPTIMIZED
# ════════════════════════════════════════════════════════════════════════════
AD_URL_PATTERNS = [
    "googlesyndication.com", "doubleclick.net", "adservice.google",
    "adnxs.com", "criteo.com", "pubmatic.com", "rubiconproject.com",
    "openx.net", "appnexus.com", "taboola.com", "outbrain.com",
    "amazon-adsystem.com", "ads.yahoo.com",
    "analytics.google.com", "google-analytics.com", "googletagmanager.com",
    "facebook.net/tr", "connect.facebook.net",
]

AD_HIDE_JS = r"""
(function(){
var style=document.createElement('style');
style.textContent=`
  [class*="google_ad"],[id*="google_ad"],[class*="adsbygoogle"],
  [class*="advertisement"],[class*="sponsored"],iframe[src*="ad"],
  ins.adsbygoogle { display:none!important; }
`;
document.head.appendChild(style);
})();
"""

class NexusAdBlocker(QWebEngineUrlRequestInterceptor):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.enabled = True
        self.blocked = 0

    def interceptRequest(self, info):
        if not self.enabled:
            return
        url = info.requestUrl().toString().lower()
        for pat in AD_URL_PATTERNS:
            if pat in url:
                info.block(True)
                self.blocked += 1
                return

# ════════════════════════════════════════════════════════════════════════════
# DATA MANAGER - OPTIMIZED
# ════════════════════════════════════════════════════════════════════════════
class DataManager(QObject):
    def __init__(self):
        super().__init__()
        self.file = "nexus_config.json"
        self.data = self._load()
        self._dirty = False
        t = QTimer(self)
        t.timeout.connect(self._flush)
        t.start(5000)  # 5 seconds instead of 2

    def _load(self) -> dict:
        if os.path.exists(self.file):
            try:
                with open(self.file, "r", encoding="utf-8") as f:
                    d = json.load(f)
                    d.setdefault("history", [])
                    d.setdefault("bookmarks", [])
                    d.setdefault("passwords", [])
                    d.setdefault("language", "vi")
                    return d
            except Exception:
                pass
        return {"history": [], "bookmarks": [], "passwords": [], "language": "vi"}

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

    def save_now(self):
        self._save()
        self._dirty = False

    def get_api_key(self) -> str:
        return self.data.get("gemini_api_key", "")

    def set_api_key(self, key: str):
        self.data["gemini_api_key"] = key.strip()
        self._dirty = True

    def get_language(self) -> str:
        return self.data.get("language", "vi")

    def set_language(self, lang: str):
        self.data["language"] = lang
        self._dirty = True

    def add_history(self, url: str, title: str):
        if not url.startswith("http"):
            return
        if self.data["history"] and self.data["history"][0].get("url") == url:
            return
        self.data["history"].insert(0, {
            "url": url,
            "title": (title or url)[:80],
            "time": datetime.now().strftime("%Y-%m-%d %H:%M"),
        })
        self.data["history"] = self.data["history"][:500]  # Limit to 500
        self._dirty = True

    def clear_history(self):
        self.data["history"] = []
        self._dirty = True

    def add_bookmark(self, url: str, title: str) -> bool:
        if any(b["url"] == url for b in self.data["bookmarks"]):
            return False
        self.data["bookmarks"].append({"url": url, "title": (title or url)[:60]})
        self._dirty = True
        return True

    def remove_bookmark(self, url: str):
        before = len(self.data["bookmarks"])
        self.data["bookmarks"] = [b for b in self.data["bookmarks"] if b["url"] != url]
        if len(self.data["bookmarks"]) != before:
            self._dirty = True

    def is_bookmarked(self, url: str) -> bool:
        return any(b["url"] == url for b in self.data["bookmarks"])

    def get_passwords(self) -> list:
        return self.data.get("passwords", [])

    def add_password(self, site: str, username: str, password: str):
        self.data["passwords"].append({
            "site": site.strip(),
            "username": username.strip(),
            "password": password,
            "added": datetime.now().strftime("%Y-%m-%d"),
        })
        self._dirty = True

    def delete_password(self, index: int):
        try:
            self.data["passwords"].pop(index)
            self._dirty = True
        except IndexError:
            pass

    def update_password(self, index: int, site: str, username: str, password: str):
        try:
            self.data["passwords"][index] = {
                "site": site.strip(),
                "username": username.strip(),
                "password": password,
                "added": self.data["passwords"][index].get("added", ""),
            }
            self._dirty = True
        except IndexError:
            pass

    def clear_all(self):
        key = self.data.get("gemini_api_key", "")
        lang = self.data.get("language", "vi")
        self.data = {"history": [], "bookmarks": [], "passwords": [], 
                     "gemini_api_key": key, "language": lang}
        self._dirty = True

# ════════════════════════════════════════════════════════════════════════════
# GEMINI AI THREAD
# ════════════════════════════════════════════════════════════════════════════
class GeminiThread(QThread):
    reply = pyqtSignal(str)
    err = pyqtSignal(str)

    def __init__(self, api_key: str, history: list, user_msg: str, parent=None):
        super().__init__(parent)
        self.api_key = api_key
        self.history = list(history)
        self.user_msg = user_msg

    def run(self):
        if not self.api_key:
            self.err.emit("no_key")
            return
        contents = self.history + [{"role": "user", "parts": [{"text": self.user_msg}]}]
        payload = {
            "system_instruction": {"parts": [{"text": "Bạn là Nexus AI."}]},
            "contents": contents,
            "generationConfig": {"temperature": 0.7, "maxOutputTokens": 512},
        }
        try:
            r = requests.post(GEMINI_URL, params={"key": self.api_key}, 
                            json=payload, timeout=20)
            if r.status_code == 400:
                self.err.emit("bad_key")
                return
            if r.status_code == 429:
                self.err.emit("rate_limit")
                return
            r.raise_for_status()
            text = (r.json().get("candidates", [{}])[0]
                    .get("content", {}).get("parts", [{}])[0]
                    .get("text", " ").strip())
            self.reply.emit(text) if text else self.err.emit("empty")
        except requests.exceptions.ConnectionError:
            self.err.emit("no_network")
        except requests.exceptions.Timeout:
            self.err.emit("timeout")
        except Exception as e:
            self.err.emit(f"unknown:{e}")

# ════════════════════════════════════════════════════════════════════════════
# IDM ENGINE - OPTIMIZED (16 threads instead of 64)
# ════════════════════════════════════════════════════════════════════════════
class NexusIDMEngine(QThread):
    progress = pyqtSignal(int, float)
    done = pyqtSignal(str)
    error = pyqtSignal(str)

    def __init__(self, url: str, save_path: str, parent=None):
        super().__init__(parent)
        self.url = url
        self.save_path = save_path
        self.is_running = True

    def run(self):
        ua = {"User-Agent": "Mozilla/5.0 NexusBrowser/4.1"}
        try:
            head = requests.head(self.url, headers=ua, allow_redirects=True, timeout=10)
            size = int(head.headers.get("Content-Length", 0))
            ar = head.headers.get("Accept-Ranges", "").lower()
            if size == 0 or ar != "bytes":
                return self._single(ua)

            nt = min(16, max(1, size // (1024 * 1024)))  # Max 16 threads
            cs = math.ceil(size / nt)
            self.total = 0
            self.lock = threading.Lock()
            t0 = time.time()
            self.lt = 0.0

            def chunk(idx, s, e):
                if not self.is_running:
                    return
                h = dict(ua)
                h["Range"] = f"bytes={s}-{e}"
                tmp = f"{self.save_path}.p{idx}"
                try:
                    with requests.get(self.url, headers=h, stream=True, timeout=20) as resp:
                        resp.raise_for_status()
                        with open(tmp, "wb") as fp:
                            for data in resp.iter_content(32768):
                                if not self.is_running:
                                    break
                                if data:
                                    fp.write(data)
                                    with self.lock:
                                        self.total += len(data)
                                        now = time.time()
                                        if now - self.lt > 0.5:
                                            self.lt = now
                                            el = now - t0 or 1e-3
                                            self.progress.emit(
                                                int(self.total * 100 / size),
                                                self.total / 1_048_576 / el
                                            )
                except Exception as ex:
                    self.error.emit(f"Phần {idx}: {ex}")

            with concurrent.futures.ThreadPoolExecutor(max_workers=nt) as pool:
                futs = [pool.submit(chunk, i, i * cs, 
                        (i * cs + cs - 1 if i < nt - 1 else size - 1)) 
                        for i in range(nt)]
                concurrent.futures.wait(futs)

            if not self.is_running:
                return
            with open(self.save_path, 'wb') as outfile:
                for i in range(nt):
                    tmp = f"{self.save_path}.p{i}"
                    if os.path.exists(tmp):
                        with open(tmp, 'rb') as infile:
                            outfile.write(infile.read())
                        os.remove(tmp)
            self.done.emit(self.save_path)
        except Exception as ex:
            self.error.emit(str(ex))

    def _single(self, ua):
        try:
            with requests.get(self.url, headers=ua, stream=True, timeout=20) as resp:
                resp.raise_for_status()
                total = int(resp.headers.get('content-length', 0))
                dl = 0
                t0 = time.time()
                lt = 0.0
                with open(self.save_path, 'wb') as fp:
                    for data in resp.iter_content(32768):
                        if not self.is_running:
                            break
                        if data:
                            fp.write(data)
                            dl += len(data)
                            now = time.time()
                            if now - lt > 0.5:
                                lt = now
                                el = now - t0 or 1e-3
                                if total > 0:
                                    self.progress.emit(int(dl * 100 / total), 
                                                      dl / 1_048_576 / el)
            if self.is_running:
                self.done.emit(self.save_path)
        except Exception as ex:
            self.error.emit(str(ex))

    def stop(self):
        self.is_running = False

class DownloadWidget(QWidget):
    def __init__(self, filename: str, parent=None):
        super().__init__(parent)
        lay = QHBoxLayout(self)
        lay.setContentsMargins(10, 4, 10, 4)
        self.lbl = QLabel(filename[:40])
        self.bar = QProgressBar()
        self.bar.setFixedHeight(14)
        self.spd = QLabel("—")
        self.spd.setFixedWidth(90)
        lay.addWidget(self.lbl, 2)
        lay.addWidget(self.bar, 2)
        lay.addWidget(self.spd)

    def on_progress(self, pct: int, spd: float):
        self.bar.setValue(pct)
        self.spd.setText(f"{spd:.2f} MB/s")

    def on_done(self, _):
        self.lbl.setText(self.lbl.text() + " ✓")
        self.bar.setValue(100)
        self.spd.setText("Xong")

    def on_error(self, msg: str):
        self.spd.setText("Lỗi")
        self.lbl.setStyleSheet("color:#FF453A")

# ════════════════════════════════════════════════════════════════════════════
# PASSWORD MANAGER DIALOG
# ════════════════════════════════════════════════════════════════════════════
def _password_strength(pwd: str) -> tuple:
    score = 0
    if len(pwd) >= 8:
        score += 20
    if len(pwd) >= 12:
        score += 10
    if len(pwd) >= 16:
        score += 10
    if re.search(r"[a-z]", pwd):
        score += 10
    if re.search(r"[A-Z]", pwd):
        score += 15
    if re.search(r"\d", pwd):
        score += 15
    if re.search(r"[^a-zA-Z0-9]", pwd):
        score += 20
    label = ("Rất yếu" if score < 30 else
             "Yếu" if score < 50 else
             "Trung bình" if score < 70 else
             "Mạnh" if score < 90 else "Rất mạnh")
    return score, label

class PasswordManagerDialog(QDialog):
    def __init__(self, data_mgr: "DataManager", parent=None):
        super().__init__(parent)
        self.dm = data_mgr
        self.setWindowTitle("🔑 Trình Quản Lý Mật Khẩu")
        self.setMinimumSize(800, 560)
        self._build()
        self._refresh_list()

    def _build(self):
        root = QVBoxLayout(self)
        root.setSpacing(10)
        tabs = QTabW()
        root.addWidget(tabs)

        vault_w = QWidget()
        vl = QVBoxLayout(vault_w)
        self.search_box = QLineEdit()
        self.search_box.setPlaceholderText("🔍 Tìm kiếm...")
        self.search_box.textChanged.connect(self._refresh_list)
        vl.addWidget(self.search_box)
        self.lst = QListWidget()
        self.lst.itemClicked.connect(self._on_select)
        vl.addWidget(self.lst, 1)

        form_box = QGroupBox("Chi tiết")
        fl = QFormLayout(form_box)
        self.f_site = QLineEdit()
        self.f_user = QLineEdit()
        self.f_pass = QLineEdit()
        self.f_pass.setEchoMode(QLineEdit.EchoMode.Password)
        self.f_pass.textChanged.connect(self._on_pass_changed)

        show_btn = QPushButton("👁")
        show_btn.setFixedWidth(36)
        show_btn.setCheckable(True)
        show_btn.toggled.connect(
            lambda on: self.f_pass.setEchoMode(
                QLineEdit.EchoMode.Normal if on else QLineEdit.EchoMode.Password
            )
        )
        pass_row = QHBoxLayout()
        pass_row.addWidget(self.f_pass)
        pass_row.addWidget(show_btn)

        self.strength_bar = QProgressBar()
        self.strength_bar.setMaximumHeight(6)
        self.strength_bar.setTextVisible(False)
        self.strength_lbl = QLabel("")
        self.strength_lbl.setStyleSheet("font-size:11px;")

        fl.addRow("Trang web:", self.f_site)
        fl.addRow("Tài khoản:", self.f_user)
        fl.addRow("Mật khẩu:", pass_row)
        fl.addRow("Độ mạnh:", self.strength_bar)
        fl.addRow("", self.strength_lbl)
        vl.addWidget(form_box)

        btn_row = QHBoxLayout()
        self.btn_save = QPushButton("💾 Lưu")
        self.btn_copy_u = QPushButton("📋 Copy TK")
        self.btn_copy_p = QPushButton("📋 Copy MK")
        self.btn_del = QPushButton("🗑 Xóa")
        self.btn_del.setProperty("class", "danger")
        self.btn_new = QPushButton("➕ Mới")
        for b in [self.btn_new, self.btn_save, self.btn_copy_u, self.btn_copy_p, self.btn_del]:
            btn_row.addWidget(b)
        vl.addLayout(btn_row)

        self.btn_new.clicked.connect(self._new_entry)
        self.btn_save.clicked.connect(self._save_entry)
        self.btn_copy_u.clicked.connect(self._copy_username)
        self.btn_copy_p.clicked.connect(self._copy_password)
        self.btn_del.clicked.connect(self._delete_entry)
        self._current_idx = -1
        tabs.addTab(vault_w, "🔐 Kho mật khẩu")

        gen_w = QWidget()
        gl = QVBoxLayout(gen_w)
        gl.setSpacing(12)
        opt_box = QGroupBox("Tuỳ chọn")
        ol = QFormLayout(opt_box)
        self.gen_len = QSpinBox()
        self.gen_len.setRange(8, 64)
        self.gen_len.setValue(16)
        self.chk_upper = QCheckBox("A-Z")
        self.chk_lower = QCheckBox("a-z")
        self.chk_digit = QCheckBox("0-9")
        self.chk_sym = QCheckBox("!@#...")
        self.chk_ambig = QCheckBox("Loại bỏ ký tự khó đọc")
        for c in [self.chk_upper, self.chk_lower, self.chk_digit, self.chk_sym]:
            c.setChecked(True)
        ol.addRow("Độ dài:", self.gen_len)
        ol.addRow(self.chk_upper)
        ol.addRow(self.chk_lower)
        ol.addRow(self.chk_digit)
        ol.addRow(self.chk_sym)
        ol.addRow(self.chk_ambig)
        gl.addWidget(opt_box)

        gen_btn = QPushButton("⚡ Tạo")
        gen_btn.clicked.connect(self._generate)
        gl.addWidget(gen_btn)

        self.gen_out = QLineEdit()
        self.gen_out.setReadOnly(True)
        gl.addWidget(self.gen_out)

        gen_copy_btn = QPushButton("📋 Sao chép")
        gen_copy_btn.clicked.connect(lambda: self._clip(self.gen_out.text()))
        gl.addWidget(gen_copy_btn)
        gl.addStretch()
        tabs.addTab(gen_w, "⚡ Tạo MK")

    def _clip(self, text: str):
        if not text:
            return
        QApplication.clipboard().setText(text)

    def _refresh_list(self):
        q = self.search_box.text().lower()
        lst = self.dm.get_passwords()
        self.lst.clear()
        for i, p in enumerate(lst):
            label = f"{p['site']} — {p['username']}"
            if q and q not in label.lower():
                continue
            item = QListWidgetItem(f"🔐 {label}")
            item.setData(Qt.ItemDataRole.UserRole, i)
            self.lst.addItem(item)

    def _on_select(self, item: QListWidgetItem):
        idx = item.data(Qt.ItemDataRole.UserRole)
        lst = self.dm.get_passwords()
        if 0 <= idx < len(lst):
            self._current_idx = idx
            p = lst[idx]
            self.f_site.setText(p['site'])
            self.f_user.setText(p['username'])
            self.f_pass.setText(p['password'])

    def _new_entry(self):
        self._current_idx = -1
        self.f_site.clear()
        self.f_user.clear()
        self.f_pass.clear()

    def _save_entry(self):
        site = self.f_site.text().strip()
        user = self.f_user.text().strip()
        pwd = self.f_pass.text()
        if not site or not pwd:
            return
        if self._current_idx >= 0:
            self.dm.update_password(self._current_idx, site, user, pwd)
        else:
            self.dm.add_password(site, user, pwd)
        self.dm.save_now()
        self._refresh_list()
        QMessageBox.information(self, "Nexus", "✔ Đã lưu")

    def _copy_username(self):
        self._clip(self.f_user.text())

    def _copy_password(self):
        self._clip(self.f_pass.text())

    def _delete_entry(self):
        if self._current_idx < 0:
            return
        if QMessageBox.question(self, "Xóa", "Xóa mục này?") == QMessageBox.StandardButton.Yes:
            self.dm.delete_password(self._current_idx)
            self.dm.save_now()
            self._new_entry()
            self._refresh_list()

    def _on_pass_changed(self, text: str):
        score, label = _password_strength(text)
        self.strength_bar.setValue(score)
        color = "#FF453A" if score < 40 else "#FFD60A" if score < 70 else "#30D158"
        self.strength_bar.setStyleSheet(
            f"QProgressBar::chunk{{background:{color};border-radius:3px}}"
        )
        self.strength_lbl.setText(f"{label} ({score}/100)")

    def _generate(self):
        chars = ""
        if self.chk_upper.isChecked():
            chars += string.ascii_uppercase
        if self.chk_lower.isChecked():
            chars += string.ascii_lowercase
        if self.chk_digit.isChecked():
            chars += string.digits
        if self.chk_sym.isChecked():
            chars += "!@#$%^&*()-_=+[]{}|;:,.?"
        if self.chk_ambig.isChecked():
            chars = chars.replace('0', '').replace('O', '').replace('l', '').replace('1', '')
        if not chars:
            return
        pwd = ''.join(secrets.choice(chars) for _ in range(self.gen_len.value()))
        self.gen_out.setText(pwd)

    def _use_generated(self):
        if self.gen_out.text():
            self.f_pass.setText(self.gen_out.text())

class ListDialog(QDialog):
    def __init__(self, title, items, on_click, parent=None):
        super().__init__(parent)
        self.setWindowTitle(title)
        self.setMinimumSize(600, 400)
        layout = QVBoxLayout(self)
        self.list_widget = QListWidget()
        layout.addWidget(self.list_widget)
        self.on_click = on_click
        for item in items:
            text = f"{item.get('title', '')} - {item.get('url', '')}"
            lw_item = QListWidgetItem(text)
            lw_item.setData(Qt.ItemDataRole.UserRole, item.get('url'))
            self.list_widget.addItem(lw_item)
        self.list_widget.itemDoubleClicked.connect(self._item_clicked)

    def _item_clicked(self, item):
        url = item.data(Qt.ItemDataRole.UserRole)
        if url and self.on_click:
            self.on_click(url)
            self.accept()

class DevToolsWindow(QMainWindow):
    def __init__(self, page, parent=None):
        super().__init__(parent)
        self.setWindowTitle("DevTools")
        self.resize(800, 600)
        self.view = QWebEngineView(self)
        self.setCentralWidget(self.view)
        page.setDevToolsView(self.view.page())

# ════════════════════════════════════════════════════════════════════════════
# MAIN BROWSER - OPTIMIZED
# ════════════════════════════════════════════════════════════════════════════
class NexusBrowser(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle(APP_NAME)
        self.resize(1280, 800)
        self.dark_mode = True
        self.data_mgr = DataManager()
        self.ad_blocker = NexusAdBlocker(self)
        self.lang = self.data_mgr.get_language()
        
        self.profile = QWebEngineProfile.defaultProfile()
        self.profile.setHttpUserAgent("Mozilla/5.0 NexusBrowser/4.1-Lite")
        self.profile.setUrlRequestInterceptor(self.ad_blocker)
        self.profile.downloadRequested.connect(self._on_download_requested)
        
        # RAM optimization
        self.profile.setCachePath("")  # Disable disk cache
        self.profile.clearHttpCache()
        
        self._ai_history = []
        self._ai_thread = None
        self._vpn_active = False
        self._tor_active = False
        self._sidebar_open = False
        self._devtools_wins = []
        self.idm_engine = None
        
        self._build_ui()
        self._open_start_page()
        
        # Hibernation - 10 minutes instead of 5
        self.hibernate_timer = QTimer(self)
        self.hibernate_timer.timeout.connect(self._hibernate_bg_tabs)
        self.hibernate_timer.start(10 * 60 * 1000)

    def _build_ui(self):
        self.central = QWidget()
        self.central.setObjectName("central")
        self.setCentralWidget(self.central)
        self.main_lay = QVBoxLayout(self.central)
        self.main_lay.setContentsMargins(0, 0, 0, 0)
        self.main_lay.setSpacing(0)
        
        self._build_toolbar()
        self.splitter = QSplitter(Qt.Orientation.Horizontal)
        self.main_lay.addWidget(self.splitter)
        
        self.tabs = QTabWidget()
        self.tabs.setTabsClosable(True)
        self.tabs.tabCloseRequested.connect(self._close_tab)
        self.tabs.currentChanged.connect(self._on_tab_changed)
        self.splitter.addWidget(self.tabs)
        
        self._build_ai_sidebar()
        self._build_find_bar()
        self._build_dl_bar(self.main_lay)
        self._build_status_bar()
        
        self.setStyleSheet(_qss(self.dark_mode))
        
        # Shortcuts
        QShortcut(QKeySequence("Ctrl+T"), self, self._new_tab)
        QShortcut(QKeySequence("Ctrl+W"), self, lambda: self._close_tab(self.tabs.currentIndex()))
        QShortcut(QKeySequence("Ctrl+F"), self, self._toggle_find)
        QShortcut(QKeySequence("F5"), self, self._reload_or_stop)
        QShortcut(QKeySequence("F12"), self, self._open_devtools)

    def _build_toolbar(self):
        toolbar = QToolBar()
        toolbar.setMovable(False)
        self.addToolBar(toolbar)
        
        # Navigation buttons
        self.btn_back = QPushButton("◀")
        self.btn_back.setFixedWidth(36)
        self.btn_back.clicked.connect(self._go_back)
        toolbar.addWidget(self.btn_back)
        
        self.btn_forward = QPushButton("▶")
        self.btn_forward.setFixedWidth(36)
        self.btn_forward.clicked.connect(self._go_forward)
        toolbar.addWidget(self.btn_forward)
        
        self.btn_reload = QPushButton("↻")
        self.btn_reload.setFixedWidth(36)
        self.btn_reload.clicked.connect(self._reload_or_stop)
        toolbar.addWidget(self.btn_reload)
        
        # NEW TAB BUTTON
        self.btn_new_tab = QPushButton("+")
        self.btn_new_tab.setObjectName("new_tab_btn")
        self.btn_new_tab.setFixedWidth(40)
        self.btn_new_tab.clicked.connect(self._new_tab)
        toolbar.addWidget(self.btn_new_tab)
        
        # URL bar
        self.url_bar = QLineEdit()
        self.url_bar.setPlaceholderText(TRANSLATIONS[self.lang]["search_placeholder"])
        self.url_bar.returnPressed.connect(self._navigate)
        toolbar.addWidget(self.url_bar)
        
        self.lock_lbl = QLabel("    ")
        toolbar.addWidget(self.lock_lbl)
        
        # AI button
        self.btn_ai = QPushButton("Nexus AI")
        self.btn_ai.setObjectName("ai_btn")
        self.btn_ai.setCheckable(True)
        self.btn_ai.clicked.connect(self._toggle_sidebar)
        toolbar.addWidget(self.btn_ai)
        
        # Menu button
        menu_btn = QToolButton()
        menu_btn.setText("☰")
        menu_btn.setPopupMode(QToolButton.ToolButtonPopupMode.InstantPopup)
        menu = QMenu(self)
        
        # Add menu items with translations
        t = TRANSLATIONS[self.lang]
        menu.addAction(t["history"], self._show_history)
        menu.addAction(t["bookmarks"], self._show_bookmarks)
        menu.addAction(t["passwords"], self._show_passwords)
        menu.addSeparator()
        menu.addAction(t["adblock"], self._toggle_adblock)
        menu.addAction(t["vpn"], self._toggle_warp)
        menu.addAction(t["tor"], self._toggle_tor)
        menu.addAction(t["disable_proxy"], self._disable_proxy)
        menu.addSeparator()
        menu.addAction(t["find_page"], self._toggle_find)
        menu.addAction(t["devtools"], self._open_devtools)
        menu.addSeparator()
        menu.addAction(t["theme"], self._toggle_theme)
        
        # Language submenu
        lang_menu = menu.addMenu(t["language"])
        lang_menu.addAction("🇻🇳 Tiếng Việt", lambda: self._set_language("vi"))
        lang_menu.addAction("🇬 English", lambda: self._set_language("en"))
        
        menu.addAction(t["clear_data"], self._clear_data)
        menu.addAction(t["about"], self._about)
        
        menu_btn.setMenu(menu)
        toolbar.addWidget(menu_btn)
        
        # Progress bar
        self.page_prog = QProgressBar()
        self.page_prog.setFixedHeight(3)
        self.page_prog.setMaximum(100)
        self.page_prog.hide()
        self.main_lay.addWidget(self.page_prog)

    def _build_find_bar(self):
        self.find_bar = QFrame()
        self.find_bar.setStyleSheet("background: #1C1C20; border-bottom: 1px solid #2C2C30; padding: 4px;")
        lay = QHBoxLayout(self.find_bar)
        lay.setContentsMargins(10, 5, 10, 5)
        self.find_input = QLineEdit()
        self.find_input.setPlaceholderText("Tìm kiếm...")
        self.find_input.returnPressed.connect(self._find_next)
        lay.addWidget(self.find_input)
        btn_prev = QPushButton("◀")
        btn_prev.clicked.connect(self._find_prev)
        lay.addWidget(btn_prev)
        btn_next = QPushButton("▶")
        btn_next.clicked.connect(self._find_next)
        lay.addWidget(btn_next)
        btn_close = QPushButton("✕")
        btn_close.clicked.connect(self._close_find)
        lay.addWidget(btn_close)
        self.find_bar.hide()
        self.main_lay.insertWidget(1, self.find_bar)

    def _build_ai_sidebar(self):
        self.sidebar = QFrame()
        self.sidebar.setFixedWidth(320)
        sl = QVBoxLayout(self.sidebar)
        sl.setContentsMargins(10, 10, 10, 10)
        sl.setSpacing(8)
        
        hdr = QHBoxLayout()
        ttl = QLabel("🤖 Nexus AI")
        ttl.setStyleSheet("font-size:15px;font-weight:700;")
        self._ai_dot = QLabel("●")
        self._ai_dot.setStyleSheet("color:#8E8E93;font-size:9px")
        close_btn = QPushButton("✕")
        close_btn.setFixedSize(24, 24)
        close_btn.clicked.connect(self._toggle_sidebar)
        hdr.addWidget(ttl)
        hdr.addWidget(self._ai_dot)
        hdr.addStretch()
        hdr.addWidget(close_btn)
        sl.addLayout(hdr)
        
        kf = QFrame()
        kf.setStyleSheet("QFrame{background:#1C1C20;border-radius:6px}")
        kfl = QVBoxLayout(kf)
        kfl.setContentsMargins(6, 6, 6, 6)
        kfl.setSpacing(4)
        
        kl = QLabel("🔑 API Key")
        kl.setStyleSheet("font-size:10px;color:#8E8E93")
        kfl.addWidget(kl)
        
        kr = QHBoxLayout()
        self.api_key_input = QLineEdit()
        self.api_key_input.setEchoMode(QLineEdit.EchoMode.Password)
        saved = self.data_mgr.get_api_key()
        if saved:
            self.api_key_input.setText(saved)
        save_btn = QPushButton("Lưu")
        save_btn.setFixedWidth(40)
        save_btn.clicked.connect(self._save_api_key)
        kr.addWidget(self.api_key_input)
        kr.addWidget(save_btn)
        kfl.addLayout(kr)
        sl.addWidget(kf)
        
        if saved:
            self._dot_ready()
        
        div = QFrame()
        div.setFrameShape(QFrame.Shape.HLine)
        sl.addWidget(div)
        
        self.ai_chat = QTextEdit()
        self.ai_chat.setReadOnly(True)
        self.ai_chat.setHtml("<b>Nexus AI:</b> Xin chào!")
        sl.addWidget(self.ai_chat, 1)
        
        cr = QHBoxLayout()
        self._think_lbl = QLabel("")
        clr_btn = QPushButton("🗑")
        clr_btn.setFixedWidth(30)
        clr_btn.clicked.connect(self._clear_ai_chat)
        cr.addWidget(self._think_lbl)
        cr.addStretch()
        cr.addWidget(clr_btn)
        sl.addLayout(cr)
        
        ir = QHBoxLayout()
        self.ai_input = QLineEdit()
        self.ai_input.setPlaceholderText("Hỏi AI...")
        self.ai_input.returnPressed.connect(self._send_ai)
        self._send_btn = QPushButton("Gửi")
        self._send_btn.setFixedWidth(40)
        self._send_btn.clicked.connect(self._send_ai)
        ir.addWidget(self.ai_input)
        ir.addWidget(self._send_btn)
        sl.addLayout(ir)
        
        self.splitter.addWidget(self.sidebar)
        self.sidebar.setVisible(False)
        self.splitter.setSizes([1280, 0])

    def _build_dl_bar(self, parent_lay):
        self.dl_bar = QWidget()
        self.dl_bar.setStyleSheet("border-top:1px solid #2C2C30")
        self.dl_lay = QVBoxLayout(self.dl_bar)
        self.dl_lay.setContentsMargins(10, 4, 10, 4)
        self.dl_lay.setSpacing(4)
        self.dl_bar.hide()
        parent_lay.addWidget(self.dl_bar)

    def _build_status_bar(self):
        sb = QStatusBar()
        self.setStatusBar(sb)
        self.stat_lbl = QLabel()
        sb.addWidget(self.stat_lbl)
        self.vpn_lbl = QLabel()
        sb.addPermanentWidget(self.vpn_lbl)
        self._update_status()

    def _update_status(self):
        blocked = self.ad_blocker.blocked
        ab_on = self.ad_blocker.enabled
        self.stat_lbl.setText(f"🛡 {blocked} ads" if ab_on else "🛡 Off")
        vpn_parts = []
        if self._vpn_active:
            vpn_parts.append("🌐 WARP")
        if self._tor_active:
            vpn_parts.append("🧅 Tor")
        self.vpn_lbl.setText("  ".join(vpn_parts))

    def _make_view(self) -> QWebEngineView:
        view = QWebEngineView()
        page = QWebEnginePage(self.profile, view)
        view.setPage(page)
        view.titleChanged.connect(lambda t, v=view: self._update_tab_title(v, t))
        view.loadProgress.connect(self._on_load_progress)
        view.loadFinished.connect(self._on_load_finished)
        view.urlChanged.connect(lambda u, v=view: self._on_url_changed(u, v))
        view.page().renderProcessTerminated.connect(
            lambda _s, _ec, v=view: QTimer.singleShot(600, lambda: self._crash_reload(v))
        )
        return view

    def _open_start_page(self):
        view = self._make_view()
        view.setHtml(build_start_page(self.dark_mode, self.lang), QUrl("about:blank"))
        idx = self.tabs.addTab(view, TRANSLATIONS[self.lang]["home"])
        self.tabs.setCurrentIndex(idx)

    def _add_tab(self, url: str, title: str = "..."):
        qurl = QUrl(url)
        if not qurl.scheme():
            qurl = QUrl("https://" + url)
        view = self._make_view()
        view.setUrl(qurl)
        idx = self.tabs.addTab(view, title[:15])
        self.tabs.setCurrentIndex(idx)
        view.loadFinished.connect(lambda ok, v=view: self._inject_ad_css(v) if ok else None)

    def _new_tab(self):
        self._add_tab("about:blank", TRANSLATIONS[self.lang]["new_tab"])
        self.url_bar.setFocus()

    def _current_view(self):
        w = self.tabs.currentWidget()
        return w if isinstance(w, QWebEngineView) else None

    def _close_tab(self, idx: int):
        if self.tabs.count() <= 1:
            self._open_start_page()
        self.tabs.removeTab(idx)
        gc.collect()  # Force garbage collection

    def _on_tab_changed(self, idx):
        v = self._current_view()
        if v:
            self.url_bar.setText(v.url().toString())
            self.setWindowTitle(f"{APP_NAME} — {v.title()}")
            self._update_lock_icon(v.url())

    def _update_tab_title(self, view, title):
        idx = self.tabs.indexOf(view)
        if idx >= 0:
            self.tabs.setTabText(idx, (title[:15] if title else "..."))
            if self.tabs.currentIndex() == idx:
                self.setWindowTitle(f"{APP_NAME} — {title}")

    def _inject_ad_css(self, view):
        if self.ad_blocker.enabled:
            view.page().runJavaScript(AD_HIDE_JS)

    def _crash_reload(self, view):
        idx = self.tabs.indexOf(view)
        if idx >= 0:
            url = view.url().toString()
            if url and url not in ("about:blank", ""):
                view.reload()

    def _navigate(self):
        text = self.url_bar.text().strip()
        if not text:
            return
        if re.match(r'^https?://', text):
            url = text
        elif re.match(r'^[a-zA-Z0-9\-]+(\.[a-zA-Z]{2,})(/.*)?$', text):
            url = "https://" + text
        else:
            url = "https://www.google.com/search?q=" + requests.utils.quote(text)
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
        if v and v.history().canGoBack():
            v.back()

    def _go_forward(self):
        v = self._current_view()
        if v and v.history().canGoForward():
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
            url_str = qurl.toString()
            if url_str and url_str != "about:blank":
                self.url_bar.setText(url_str)
            self._update_lock_icon(qurl)
        self.data_mgr.add_history(qurl.toString(), view.title())

    def _update_lock_icon(self, qurl):
        if qurl.scheme() == "https":
            self.lock_lbl.setText("🔒")
        elif qurl.scheme() == "http":
            self.lock_lbl.setText("🔓")
        else:
            self.lock_lbl.setText("   ")

    def _on_load_progress(self, pct: int):
        if 0 < pct < 100:
            self.page_prog.show()
            self.page_prog.setValue(pct)
            self.btn_reload.setText("✕")
        else:
            self.page_prog.setValue(100)
            QTimer.singleShot(400, self.page_prog.hide)
            self.btn_reload.setText("↻")

    def _on_load_finished(self, ok: bool):
        self.btn_reload.setText("↻")
        v = self._current_view()
        if not ok and v:
            url = v.url().toString()
            if url.startswith("http"):
                v.setHtml(ERROR_PAGE_HTML, QUrl("about:error"))

    def _toggle_find(self):
        if self.find_bar.isVisible():
            self._close_find()
        else:
            self.find_bar.show()
            self.find_input.setFocus()
            self.find_input.selectAll()

    def _close_find(self):
        self.find_bar.hide()
        self.find_input.clear()
        v = self._current_view()
        if v:
            v.findText("")

    def _find_next(self):
        v = self._current_view()
        q = self.find_input.text()
        if v and q:
            v.findText(q)

    def _find_prev(self):
        v = self._current_view()
        q = self.find_input.text()
        if v and q:
            v.findText(q, QWebEnginePage.FindFlag.FindBackward)

    def _open_devtools(self):
        v = self._current_view()
        if not v:
            return
        dw = DevToolsWindow(v.page(), self)
        self._devtools_wins.append(dw)
        dw.finished.connect(lambda: self._devtools_wins.remove(dw) if dw in self._devtools_wins else None)
        dw.show()

    def _toggle_sidebar(self):
        self._sidebar_open = not self._sidebar_open
        self.sidebar.setVisible(self._sidebar_open)
        self.btn_ai.setChecked(self._sidebar_open)
        self.splitter.setSizes([950, 320] if self._sidebar_open else [1280, 0])

    def _save_api_key(self):
        key = self.api_key_input.text().strip()
        if not key:
            QMessageBox.warning(self, "Nexus AI", "Vui lòng nhập API key.")
            return
        self.data_mgr.set_api_key(key)
        self._dot_ready()
        self._append_ai("✔ API key đã lưu.")

    def _dot_ready(self):
        self._ai_dot.setStyleSheet("color:#30D158;font-size:9px")

    def _dot_busy(self):
        self._ai_dot.setStyleSheet("color:#FFD60A;font-size:9px")

    def _dot_error(self):
        self._ai_dot.setStyleSheet("color:#FF453A;font-size:9px")

    def _append_ai(self, html: str):
        self.ai_chat.append(f"<div>{html}</div>")
        self.ai_chat.verticalScrollBar().setValue(
            self.ai_chat.verticalScrollBar().maximum()
        )

    def _clear_ai_chat(self):
        self._ai_history.clear()
        self.ai_chat.setHtml("<b>Nexus AI:</b> Lịch sử đã xóa.")

    def _send_ai(self):
        text = self.ai_input.text().strip()
        if not text:
            return
        key = self.data_mgr.get_api_key()
        if not key:
            self._append_ai("⚠ Chưa có API key.")
            return
        if self._ai_thread and self._ai_thread.isRunning():
            return
        
        self._append_ai(f"<b>Bạn:</b> {text}")
        self.ai_input.clear()
        self._think_lbl.setText("⏳ ...")
        self._dot_busy()
        self._ai_thread = GeminiThread(key, self._ai_history, text, self)
        self._ai_thread.reply.connect(lambda r, t=text: self._ai_got_reply(t, r))
        self._ai_thread.err.connect(self._ai_got_error)
        self._ai_thread.start()

    def _ai_got_reply(self, user_txt: str, reply: str):
        self._ai_history.append({"role": "user", "parts": [{"text": user_txt}]})
        self._ai_history.append({"role": "model", "parts": [{"text": reply}]})
        if len(self._ai_history) > 20:  # Limit history
            self._ai_history = self._ai_history[-20:]
        self._append_ai(f"<b>Nexus AI:</b> {reply.replace(chr(10), '<br>')}")
        self._think_lbl.setText("")
        self._dot_ready()

    def _ai_got_error(self, code: str):
        msgs = {
            "no_key": "⚠ Chưa có API key.",
            "bad_key": "❌ API key sai.",
            "rate_limit": "⏳ Vượt giới hạn.",
            "no_network": "🌐 Mất mạng.",
            "timeout": "⏱ Timeout.",
        }
        self._append_ai(msgs.get(code, f"⚠ Lỗi: {code}"))
        self._think_lbl.setText("")
        self._dot_error()

    def _hibernate_bg_tabs(self):
        cur = self.tabs.currentIndex()
        indices = [i for i in range(self.tabs.count()) 
                   if i != cur and isinstance(self.tabs.widget(i), QWebEngineView)]
        for i in reversed(indices):
            w = self.tabs.widget(i)
            url = w.url().toString()
            title = (w.title() or url)[:15]
            if not url or url == "about:blank":
                continue
            self.tabs.removeTab(i)
            w.deleteLater()
            ph = QLabel(f"❄ {title}\n\nClick để mở")
            ph.setAlignment(Qt.AlignmentFlag.AlignCenter)
            ph.setStyleSheet("font-size:13px;color:#8E8E93;background:#141417;border-radius:8px")
            ph.setProperty("url", url)
            ph.setProperty("title", title)
            self.tabs.insertTab(i, ph, f"❄ {title[:10]}")
            ph.mousePressEvent = lambda e, p=ph: self._restore_tab(p)
        gc.collect()

    def _restore_tab(self, ph):
        idx = self.tabs.indexOf(ph)
        if idx < 0:
            return
        url = ph.property("url")
        title = ph.property("title")
        self.tabs.removeTab(idx)
        ph.deleteLater()
        self._add_tab(url, title)

    def _on_download_requested(self, item):
        url = item.url().toString()
        name = item.suggestedFileName()
        item.cancel()
        path, _ = QFileDialog.getSaveFileName(self, "Lưu file", name)
        if not path:
            return
        self.dl_bar.show()
        while self.dl_lay.count():
            old = self.dl_lay.takeAt(0)
            if old.widget():
                old.widget().deleteLater()
        dw = DownloadWidget(name, self)
        self.dl_lay.addWidget(dw)
        if self.idm_engine and self.idm_engine.isRunning():
            self.idm_engine.stop()
            self.idm_engine.wait()
        self.idm_engine = NexusIDMEngine(url, path, self)
        self.idm_engine.progress.connect(dw.on_progress)
        self.idm_engine.done.connect(dw.on_done)
        self.idm_engine.error.connect(dw.on_error)
        self.idm_engine.start()

    def _toggle_warp(self):
        if self._vpn_active:
            if not self._tor_active:
                QNetworkProxy.setApplicationProxy(
                    QNetworkProxy(QNetworkProxy.ProxyType.NoProxy)
                )
            self._vpn_active = False
        else:
            if self._tor_active:
                QMessageBox.warning(self, "Xung đột", "Tắt Tor trước.")
                return
            QNetworkProxy.setApplicationProxy(
                QNetworkProxy(QNetworkProxy.ProxyType.Socks5Proxy, "127.0.0.1", 40001)
            )
            self._vpn_active = True
        self._update_status()

    def _toggle_tor(self):
        if self._tor_active:
            if not self._vpn_active:
                QNetworkProxy.setApplicationProxy(
                    QNetworkProxy(QNetworkProxy.ProxyType.NoProxy)
                )
            self._tor_active = False
        else:
            if self._vpn_active:
                QMessageBox.warning(self, "Xung đột", "Tắt WARP trước.")
                return
            QNetworkProxy.setApplicationProxy(
                QNetworkProxy(QNetworkProxy.ProxyType.Socks5Proxy, "127.0.0.1", 9050)
            )
            self._tor_active = True
        self._update_status()

    def _disable_proxy(self):
        QNetworkProxy.setApplicationProxy(
            QNetworkProxy(QNetworkProxy.ProxyType.NoProxy)
        )
        self._vpn_active = False
        self._tor_active = False
        self._update_status()

    def _toggle_adblock(self):
        self.ad_blocker.enabled = not self.ad_blocker.enabled
        self._update_status()

    def _toggle_theme(self):
        self.dark_mode = not self.dark_mode
        self.setStyleSheet(_qss(self.dark_mode))
        # Reload start page if current tab
        v = self._current_view()
        if v and v.url().toString() == "about:blank":
            v.setHtml(build_start_page(self.dark_mode, self.lang), QUrl("about:blank"))

    def _set_language(self, lang: str):
        self.lang = lang
        self.data_mgr.set_language(lang)
        self.url_bar.setPlaceholderText(TRANSLATIONS[lang]["search_placeholder"])
        # Reload start page
        v = self._current_view()
        if v and v.url().toString() == "about:blank":
            v.setHtml(build_start_page(self.dark_mode, lang), QUrl("about:blank"))
        QMessageBox.information(self, "Ngôn ngữ", f"Đã chuyển sang {lang.upper()}")

    def _show_history(self):
        ListDialog("🕐 Lịch Sử", self.data_mgr.data["history"], 
                  self._load_url, self).exec()

    def _show_bookmarks(self):
        ListDialog("★ Dấu Trang", self.data_mgr.data["bookmarks"], 
                  self._load_url, self).exec()

    def _show_passwords(self):
        PasswordManagerDialog(self.data_mgr, self).exec()

    def _clear_data(self):
        if QMessageBox.question(self, "Xóa dữ liệu", 
                               "Xóa lịch sử & cache?") == QMessageBox.StandardButton.Yes:
            self.data_mgr.clear_history()
            self.data_mgr.data["bookmarks"] = []
            self.data_mgr.save_now()
            self.profile.clearHttpCache()
            gc.collect()

    def _about(self):
        QMessageBox.about(self, f"Về {APP_NAME}",
            f"{APP_NAME} v{APP_VERSION}\n\n"
            "✔ Giao diện Fluent\n"
            "✔ Tối ưu RAM (Cache disabled)\n"
            "✔ IDM 16-Thread\n"
            "✔ AdBlock\n"
            "✔ Gemini AI\n"
            "✔ Dark/Light Mode\n"
            "✔ Đa ngôn ngữ (VI/EN)\n"
            "✔ Tab Hibernation (10 phút)"
        )

# ════════════════════════════════════════════════════════════════════════════
# ENTRY POINT
# ════════════════════════════════════════════════════════════════════════════
def main():
    QApplication.setHighDpiScaleFactorRoundingPolicy(
        Qt.HighDpiScaleFactorRoundingPolicy.PassThrough
    )
    app = QApplication(sys.argv)
    app.setApplicationName(APP_NAME)
    app.setApplicationVersion(APP_VERSION)
    
    font = QFont("Segoe UI", 10)
    font.setStyleStrategy(QFont.StyleStrategy.PreferAntialias)
    app.setFont(font)
    
    p = QPalette()
    p.setColor(QPalette.ColorRole.Window, QColor("#141417"))
    p.setColor(QPalette.ColorRole.WindowText, QColor("#F5F5F7"))
    p.setColor(QPalette.ColorRole.Base, QColor("#1C1C20"))
    p.setColor(QPalette.ColorRole.AlternateBase, QColor("#141417"))
    p.setColor(QPalette.ColorRole.ToolTipBase, QColor("#1C1C20"))
    p.setColor(QPalette.ColorRole.ToolTipText, QColor("#F5F5F7"))
    p.setColor(QPalette.ColorRole.Text, QColor("#F5F5F7"))
    p.setColor(QPalette.ColorRole.Button, QColor("#1C1C20"))
    p.setColor(QPalette.ColorRole.ButtonText, QColor("#F5F5F7"))
    p.setColor(QPalette.ColorRole.BrightText, QColor("#FF453A"))
    p.setColor(QPalette.ColorRole.Link, QColor(ACCENT))
    p.setColor(QPalette.ColorRole.Highlight, QColor(ACCENT))
    p.setColor(QPalette.ColorRole.HighlightedText, QColor("#FFFFFF"))
    app.setPalette(p)
    
    browser = NexusBrowser()
    browser.show()
    sys.exit(app.exec())

if __name__ == "__main__":
    main()
