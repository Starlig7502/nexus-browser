

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
from datetime import datetime

# ── HiDPI & Chromium flags  (MUST be before QApplication) ───────────────────
os.environ.setdefault("QT_ENABLE_HIGHDPI_SCALING", "1")
os.environ.setdefault("QT_FONT_DPI", "96")
os.environ.setdefault("QT_SCALE_FACTOR_ROUNDING_POLICY", "PassThrough")
os.environ.setdefault(
    "QTWEBENGINE_CHROMIUM_FLAGS",
    "--disable-gpu-shader-disk-cache "
    "--disk-cache-size=67108864 "
    "--media-cache-size=10485760 "
    "--disable-reading-from-canvas "
    "--process-per-site "
    "--ignore-gpu-blocklist "
    "--enable-gpu-rasterization "
    "--enable-features=NetworkService,VaapiVideoDecoder "
    "--disable-features=CalculateNativeWinOcclusion",
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
    QFormLayout, QDialogButtonBox, QStatusBar, QToolButton,
)
from PyQt6.QtWebEngineWidgets import QWebEngineView
from PyQt6.QtWebEngineCore import (
    QWebEngineProfile, QWebEngineUrlRequestInterceptor,
    QWebEnginePage, QWebEngineFindTextResult,
)
from PyQt6.QtNetwork import QNetworkProxy
from PyQt6.QtGui import (
    QFont, QPalette, QColor, QShortcut, QKeySequence, QClipboard,
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
APP_VERSION = "4.0"
ACCENT      = "#0078D4"

GEMINI_URL = (
    "https://generativelanguage.googleapis.com/v1beta/models/"
    "gemini-2.0-flash:generateContent"
)
SYSTEM_PROMPT = (
    "Bạn là Nexus AI — trợ lý thông minh tích hợp trong Nexus Browser. "
    "Hãy trả lời ngắn gọn, hữu ích bằng tiếng Việt trừ khi người dùng hỏi "
    "bằng tiếng Anh. Bạn hỗ trợ duyệt web, tóm tắt, dịch thuật, lập trình, "
    "và mọi câu hỏi khác."
)

# ════════════════════════════════════════════════════════════════════════════
# START PAGE
# ════════════════════════════════════════════════════════════════════════════
def build_start_page(dark: bool) -> str:
    bg       = "#141417" if dark else "#F5F5F7"
    card_bg  = "#1C1C20" if dark else "#FFFFFF"
    text     = "#F5F5F7" if dark else "#141417"
    subtext  = "#8E8E93" if dark else "#6E6E73"
    inp_bg   = "#1C1C20" if dark else "#FFFFFF"
    inp_brd  = "#2C2C30" if dark else "#D1D1D6"
    return f"""<!DOCTYPE html><html lang="vi"><head>
<meta charset="UTF-8">
<style>
*{{box-sizing:border-box;margin:0;padding:0}}
body{{background:{bg};color:{text};font-family:'Segoe UI',Arial,sans-serif;
     display:flex;flex-direction:column;align-items:center;justify-content:center;
     min-height:100vh;gap:28px;padding:20px}}
.logo{{font-size:76px;font-weight:900;letter-spacing:14px;color:{ACCENT};
       text-shadow:0 0 24px {ACCENT}99,0 0 64px {ACCENT}33;user-select:none}}
.sub{{font-size:15px;color:{subtext};letter-spacing:3px;margin-top:-16px}}
.search{{display:flex;width:min(620px,90vw);border-radius:30px;overflow:hidden;
         border:2px solid {ACCENT};background:{inp_bg};box-shadow:0 0 28px {ACCENT}33}}
.search input{{flex:1;padding:15px 22px;border:none;outline:none;background:transparent;
               color:{text};font-size:16px;font-family:'Segoe UI',Arial,sans-serif}}
.search button{{padding:15px 26px;border:none;background:{ACCENT};color:#fff;
                font-size:18px;cursor:pointer;transition:opacity .2s}}
.search button:hover{{opacity:.85}}
.shortcuts{{display:flex;gap:14px;flex-wrap:wrap;justify-content:center;max-width:640px}}
.sc{{background:{card_bg};border:1px solid {inp_brd};border-radius:14px;
     padding:14px 22px;font-size:14px;font-weight:600;cursor:pointer;color:{text};
     transition:transform .15s,box-shadow .15s;text-decoration:none;display:block}}
.sc:hover{{transform:scale(1.07);box-shadow:0 6px 28px {ACCENT}44}}
.time{{font-size:13px;color:{subtext}}}
</style></head><body>
<div class="logo">NEXUS</div>
<div class="sub">TRÌNH DUYỆT THẾ HỆ MỚI</div>
<div class="search">
  <input id="q" placeholder="Tìm kiếm hoặc nhập địa chỉ..."
         onkeydown="if(event.key==='Enter')go()">
  <button onclick="go()">&#x1F50D;</button>
</div>
<div class="shortcuts">
  <a class="sc" href="https://google.com">🔍 Google</a>
  <a class="sc" href="https://youtube.com">▶ YouTube</a>
  <a class="sc" href="https://github.com">🐙 GitHub</a>
  <a class="sc" href="https://facebook.com">📘 Facebook</a>
  <a class="sc" href="https://mail.google.com">✉ Gmail</a>
  <a class="sc" href="https://chat.openai.com">🤖 ChatGPT</a>
  <a class="sc" href="https://translate.google.com">🌐 Dịch</a>
  <a class="sc" href="https://news.ycombinator.com">📰 HN</a>
</div>
<div class="time" id="clk"></div>
<script>
function go(){{var q=document.getElementById('q').value.trim();
  if(q)location.href='https://www.google.com/search?q='+encodeURIComponent(q);}}
document.querySelectorAll('.sc').forEach(function(a){{
  a.addEventListener('click',function(e){{e.preventDefault();window.location.href=this.href;}});}});
function tick(){{var now=new Date();
  document.getElementById('clk').textContent=now.toLocaleString('vi-VN');}}
tick();setInterval(tick,1000);
document.getElementById('q').focus();
</script></body></html>"""


ERROR_PAGE_HTML = """<!DOCTYPE html><html lang="vi"><head><meta charset="UTF-8">
<style>
body{background:#141417;color:#F5F5F7;font-family:'Segoe UI',sans-serif;
     display:flex;flex-direction:column;align-items:center;justify-content:center;
     height:100vh;gap:20px;text-align:center;padding:20px}
.ico{font-size:80px}.title{font-size:30px;color:#FF453A;font-weight:700}
p{color:#8E8E93;font-size:15px;max-width:440px;line-height:1.6}
.btn{background:#0078D4;color:#fff;border:none;padding:13px 36px;border-radius:26px;
     font-size:15px;cursor:pointer;margin:4px}
.btn:hover{opacity:.85}.btn.sec{background:#2C2C30}
</style></head><body>
<div class="ico">🌐</div>
<div class="title">Không thể kết nối</div>
<p>Trang web không phản hồi hoặc mạng bị gián đoạn.<br>
Kiểm tra kết nối Internet rồi thử lại.</p>
<div>
  <button class="btn" onclick="location.reload()">↺ Thử lại</button>
  <button class="btn sec" onclick="history.back()">◀ Quay lại</button>
</div>
</body></html>"""


# ════════════════════════════════════════════════════════════════════════════
# QSS
# ════════════════════════════════════════════════════════════════════════════
def _qss(dark: bool) -> str:
    if dark:
        bg, card, text, brd, sub = "#141417","#1C1C20","#F5F5F7","#2C2C30","#8E8E93"
        hover, pressed = "#2C2C30","#3A3A40"
    else:
        bg, card, text, brd, sub = "#F5F5F7","#FFFFFF","#141417","#D1D1D6","#6E6E73"
        hover, pressed = "#E5E5EA","#D1D1D6"
    return f"""
QMainWindow,QWidget#central{{background:{bg};color:{text}}}
QToolBar{{background:{bg};border:none;padding:6px 8px;spacing:5px;
          border-bottom:1px solid {brd}}}
QToolBar::separator{{background:{brd};width:1px;margin:4px 2px}}
QPushButton{{background:{card};color:{text};border:none;
             padding:7px 14px;border-radius:7px;font-weight:500}}
QPushButton:hover{{background:{hover}}}
QPushButton:pressed{{background:{pressed}}}
QPushButton:disabled{{color:{sub}}}
QPushButton#ai_btn{{background:transparent;color:{ACCENT};
    border:1.5px solid {ACCENT};border-radius:7px;padding:6px 13px;font-weight:700}}
QPushButton#ai_btn:hover{{background:{ACCENT}22}}
QPushButton#ai_btn:checked{{background:{ACCENT};color:#fff}}
QPushButton.danger{{background:#FF453A22;color:#FF453A;border:1px solid #FF453A44}}
QPushButton.danger:hover{{background:#FF453A44}}
QLineEdit{{background:{card};color:{text};padding:8px 12px;
           border-radius:7px;border:1.5px solid {brd};font-size:14px}}
QLineEdit:focus{{border:1.5px solid {ACCENT}}}
QTabWidget::pane{{border:none;background:{bg}}}
QTabBar{{background:{bg}}}
QTabBar::tab{{background:{bg};color:{sub};padding:9px 18px;min-width:90px;
              border-top-left-radius:8px;border-top-right-radius:8px;margin-right:2px}}
QTabBar::tab:selected{{background:{card};color:{text};font-weight:700}}
QTabBar::tab:hover:!selected{{background:{card}}}
QTextEdit{{background:{card};color:{text};border:none;
           border-radius:7px;padding:10px;font-size:14px;line-height:1.5}}
QMenu{{background:{card};border:1px solid {brd};border-radius:10px;padding:4px}}
QMenu::item{{padding:9px 24px;border-radius:6px;color:{text}}}
QMenu::item:selected{{background:{hover}}}
QMenu::separator{{height:1px;background:{brd};margin:4px 0}}
QProgressBar{{border:none;border-radius:3px;background:{brd};
              text-align:center;color:transparent}}
QProgressBar::chunk{{background:{ACCENT};border-radius:3px}}
QDialog{{background:{bg};border-radius:12px;color:{text}}}
QListWidget{{background:{card};border:1px solid {brd};
             border-radius:8px;padding:4px;color:{text}}}
QListWidget::item{{padding:10px 8px;border-radius:6px}}
QListWidget::item:selected{{background:{hover};color:{text}}}
QLabel{{color:{text}}}
QGroupBox{{border:1px solid {brd};border-radius:8px;margin-top:12px;
           padding:8px;color:{text};font-weight:600}}
QGroupBox::title{{subcontrol-origin:margin;left:10px;padding:0 4px}}
QScrollBar:vertical{{background:{bg};width:8px;border-radius:4px}}
QScrollBar::handle:vertical{{background:{brd};border-radius:4px;min-height:24px}}
QScrollBar::add-line:vertical,QScrollBar::sub-line:vertical{{height:0}}
QSplitter::handle{{background:{brd};width:1px}}
QStatusBar{{background:{card};color:{sub};border-top:1px solid {brd};font-size:12px}}
QComboBox{{background:{card};color:{text};border:1.5px solid {brd};
           border-radius:7px;padding:6px 10px}}
QComboBox::drop-down{{border:none}}
QSpinBox{{background:{card};color:{text};border:1.5px solid {brd};
          border-radius:7px;padding:6px 8px}}
QCheckBox{{color:{text}}}
QCheckBox::indicator{{width:16px;height:16px;border-radius:4px;border:2px solid {brd}}}
QCheckBox::indicator:checked{{background:{ACCENT};border-color:{ACCENT}}}
"""


# ════════════════════════════════════════════════════════════════════════════
# AD BLOCKER  —  URL-level + CSS injection
# ════════════════════════════════════════════════════════════════════════════
AD_URL_PATTERNS = [
    # Ad networks
    "googlesyndication.com", "doubleclick.net", "adservice.google",
    "adnxs.com", "criteo.com", "criteo.net", "pubmatic.com",
    "rubiconproject.com", "openx.net", "appnexus.com", "taboola.com",
    "outbrain.com", "revcontent.com", "amazon-adsystem.com",
    "ads.yahoo.com", "ads.twitter.com", "advertising.com",
    # Trackers / analytics
    "analytics.google.com", "google-analytics.com", "googletagmanager.com",
    "facebook.net/tr", "connect.facebook.net", "scorecardresearch.com",
    "quantserve.com", "hotjar.com", "mouseflow.com", "fullstory.com",
    "mc.yandex.ru", "counter.yadro.ru", "mixpanel.com", "segment.io",
    "segment.com", "amplitude.com", "heap.io", "intercom.io",
    # Pop-up / malware
    "popads.net", "popcash.net", "propellerads.com", "trafficjunky.com",
    "exoclick.com", "juicyads.com", "trafficfactory.biz",
]

AD_HIDE_JS = r"""
(function(){
var style=document.createElement('style');
style.textContent=`
  [class*="google_ad"],[class*="GoogleAd"],[id*="google_ad"],
  [class*="adsbygoogle"],[class*="advertisement"],[class*="sponsored-"],
  [class*="sponsor-"],[id*="sponsor"],[class*="banner-ad"],[class*="ad-banner"],
  [class*="ad_banner"],[class*="adsbox"],[class*="ad-slot"],[class*="ad_slot"],
  [id*="AdArea"],[id*="adZone"],[class*="promoted-tweet"],[class*="promoted_tweet"],
  iframe[src*="ad"],[aria-label="Advertisements"],
  div[data-ad],div[data-ads],section[data-testid*="ad"],
  .widget_text > .textwidget > ins,
  ins.adsbygoogle { display:none!important; }
`;
document.head.appendChild(style);
var obs=new MutationObserver(function(ms){
  ms.forEach(function(m){
    m.addedNodes.forEach(function(n){
      if(n.nodeType===1){
        var cls=(n.className||'').toString()+' '+(n.id||'');
        if(/ad[_-]|advertisement|sponsor|promoted|adsbox/i.test(cls))
          n.style.display='none';
      }
    });
  });
});
obs.observe(document.body,{childList:true,subtree:true});
})();
"""


class NexusAdBlocker(QWebEngineUrlRequestInterceptor):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.enabled  = True
        self.blocked  = 0

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
# DATA MANAGER  —  debounced disk I/O
# ════════════════════════════════════════════════════════════════════════════
class DataManager(QObject):
    def __init__(self):
        super().__init__()
        self.file   = "nexus_config.json"
        self.data   = self._load()
        self._dirty = False
        t = QTimer(self)
        t.timeout.connect(self._flush)
        t.start(2000)

    def _load(self) -> dict:
        if os.path.exists(self.file):
            try:
                with open(self.file, "r", encoding="utf-8") as f:
                    d = json.load(f)
                    # Ensure keys exist
                    d.setdefault("history",   [])
                    d.setdefault("bookmarks", [])
                    d.setdefault("passwords", [])
                    return d
            except Exception:
                pass
        return {"history": [], "bookmarks": [], "passwords": []}

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

    # API key
    def get_api_key(self) -> str:
        return self.data.get("gemini_api_key", "")

    def set_api_key(self, key: str):
        self.data["gemini_api_key"] = key.strip()
        self._dirty = True

    # History
    def add_history(self, url: str, title: str):
        if not url.startswith("http"):
            return
        # Avoid duplicates at top
        if self.data["history"] and self.data["history"][0].get("url") == url:
            return
        self.data["history"].insert(0, {
            "url":   url,
            "title": (title or url)[:80],
            "time":  datetime.now().strftime("%Y-%m-%d %H:%M"),
        })
        self.data["history"] = self.data["history"][:1000]
        self._dirty = True

    def clear_history(self):
        self.data["history"] = []
        self._dirty = True

    # Bookmarks
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

    # Passwords
    def get_passwords(self) -> list:
        return self.data.get("passwords", [])

    def add_password(self, site: str, username: str, password: str):
        self.data["passwords"].append({
            "site":     site.strip(),
            "username": username.strip(),
            "password": password,
            "added":    datetime.now().strftime("%Y-%m-%d"),
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
                "site":     site.strip(),
                "username": username.strip(),
                "password": password,
                "added":    self.data["passwords"][index].get("added", ""),
            }
            self._dirty = True
        except IndexError:
            pass

    # Clear all (keep API key)
    def clear_all(self):
        key = self.data.get("gemini_api_key", "")
        self.data = {"history": [], "bookmarks": [], "passwords": []}
        if key:
            self.data["gemini_api_key"] = key
        self._dirty = True


# ════════════════════════════════════════════════════════════════════════════
# GEMINI AI THREAD
# ════════════════════════════════════════════════════════════════════════════
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
        contents = self.history + [{"role":"user","parts":[{"text":self.user_msg}]}]
        payload  = {
            "system_instruction": {"parts": [{"text": SYSTEM_PROMPT}]},
            "contents": contents,
            "generationConfig": {"temperature": 0.7, "maxOutputTokens": 1024},
        }
        try:
            r = requests.post(
                GEMINI_URL, params={"key": self.api_key},
                json=payload, timeout=30,
            )
            if r.status_code == 400:
                self.err.emit("bad_key"); return
            if r.status_code == 429:
                self.err.emit("rate_limit"); return
            r.raise_for_status()
            text = (
                r.json().get("candidates",[{}])[0]
                        .get("content",{})
                        .get("parts",[{}])[0]
                        .get("text","").strip()
            )
            self.reply.emit(text) if text else self.err.emit("empty")
        except requests.exceptions.ConnectionError:
            self.err.emit("no_network")
        except requests.exceptions.Timeout:
            self.err.emit("timeout")
        except Exception as e:
            self.err.emit(f"unknown:{e}")


# ════════════════════════════════════════════════════════════════════════════
# IDM 64-THREAD DOWNLOAD ENGINE
# ════════════════════════════════════════════════════════════════════════════
class NexusIDMEngine(QThread):
    progress = pyqtSignal(int, float)   # pct, MB/s
    done     = pyqtSignal(str)
    error    = pyqtSignal(str)

    def __init__(self, url: str, save_path: str, parent=None):
        super().__init__(parent)
        self.url        = url
        self.save_path  = save_path
        self.is_running = True

    def run(self):
        ua = {"User-Agent": "Mozilla/5.0 NexusBrowser/4.0"}
        try:
            head = requests.head(self.url, headers=ua, allow_redirects=True, timeout=15)
            size = int(head.headers.get("Content-Length", 0))
            ar   = head.headers.get("Accept-Ranges", "").lower()
            if size == 0 or ar != "bytes":
                return self._single(ua)

            nt   = min(64, max(1, size // (512 * 1024)))
            cs   = math.ceil(size / nt)
            self.total = 0
            self.lock  = threading.Lock()
            t0 = time.time(); self.lt = 0.0

            def chunk(idx, s, e):
                if not self.is_running: return
                h = dict(ua); h["Range"] = f"bytes={s}-{e}"
                tmp = f"{self.save_path}.p{idx}"
                try:
                    with requests.get(self.url,headers=h,stream=True,timeout=30) as resp:
                        resp.raise_for_status()
                        with open(tmp,"wb") as fp:
                            for data in resp.iter_content(65536):
                                if not self.is_running: break
                                if data:
                                    fp.write(data)
                                    with self.lock:
                                        self.total += len(data)
                                        now = time.time()
                                        if now - self.lt > 0.25:
                                            self.lt = now
                                            el = now - t0 or 1e-3
                                            self.progress.emit(
                                                int(self.total*100/size),
                                                self.total/1_048_576/el)
                except Exception as ex:
                    self.error.emit(f"Phần {idx}: {ex}")

            with concurrent.futures.ThreadPoolExecutor(nt) as pool:
                futs = [pool.submit(chunk, i, i*cs,
                        (i*cs+cs-1 if i<nt-1 else size-1)) for i in range(nt)]
                concurrent.futures.wait(futs)

            if not self.is_running: return
            with open(self.save_path,"wb") as out:
                for i in range(nt):
                    tmp = f"{self.save_path}.p{i}"
                    if os.path.exists(tmp):
                        with open(tmp,"rb") as fp: out.write(fp.read())
                        os.remove(tmp)
            self.progress.emit(100, 0.0)
            self.done.emit(self.save_path)
        except Exception as ex:
            self.error.emit(str(ex))

    def _single(self, ua):
        try:
            with requests.get(self.url,headers=ua,stream=True,timeout=30) as resp:
                resp.raise_for_status()
                total = int(resp.headers.get("Content-Length",0))
                dl = 0; t0 = time.time(); lt = 0.0
                with open(self.save_path,"wb") as fp:
                    for data in resp.iter_content(65536):
                        if not self.is_running: break
                        if data:
                            fp.write(data); dl += len(data)
                            if total:
                                now = time.time()
                                if now-lt > 0.25:
                                    lt = now
                                    el = now-t0 or 1e-3
                                    self.progress.emit(int(dl*100/total), dl/1_048_576/el)
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
        self.lbl   = QLabel(filename[:40])
        self.bar   = QProgressBar()
        self.bar.setFixedHeight(14)
        self.spd   = QLabel("—")
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
def _password_strength(pwd: str) -> tuple[int, str]:
    """Returns (score 0-100, label)."""
    score = 0
    if len(pwd) >= 8:  score += 20
    if len(pwd) >= 12: score += 10
    if len(pwd) >= 16: score += 10
    if re.search(r"[a-z]", pwd): score += 10
    if re.search(r"[A-Z]", pwd): score += 15
    if re.search(r"\d",    pwd): score += 15
    if re.search(r"[^a-zA-Z0-9]", pwd): score += 20
    label = ("Rất yếu" if score < 30 else
             "Yếu"     if score < 50 else
             "Trung bình" if score < 70 else
             "Mạnh"    if score < 90 else "Rất mạnh")
    return score, label


class PasswordManagerDialog(QDialog):
    def __init__(self, data_mgr: "DataManager", parent=None):
        super().__init__(parent)
        self.dm = data_mgr
        self.setWindowTitle("🔑 Trình Quản Lý Mật Khẩu — Nexus")
        self.setMinimumSize(800, 560)
        self._build()
        self._refresh_list()

    def _build(self):
        root = QVBoxLayout(self)
        root.setSpacing(10)

        tabs = QTabW()
        root.addWidget(tabs)

        # ── Tab 1: Vault ──────────────────────────────────────────────────
        vault_w = QWidget()
        vl = QVBoxLayout(vault_w)

        search_row = QHBoxLayout()
        self.search_box = QLineEdit()
        self.search_box.setPlaceholderText("🔍  Tìm kiếm theo tên trang / tài khoản...")
        self.search_box.textChanged.connect(self._refresh_list)
        search_row.addWidget(self.search_box)
        vl.addLayout(search_row)

        self.lst = QListWidget()
        self.lst.itemClicked.connect(self._on_select)
        vl.addWidget(self.lst, 1)

        # Detail / edit form
        form_box = QGroupBox("Chi tiết")
        fl = QFormLayout(form_box)
        self.f_site = QLineEdit(); self.f_site.setPlaceholderText("vd: google.com")
        self.f_user = QLineEdit(); self.f_user.setPlaceholderText("email / tên đăng nhập")
        self.f_pass = QLineEdit(); self.f_pass.setEchoMode(QLineEdit.EchoMode.Password)
        self.f_pass.setPlaceholderText("mật khẩu")
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
        self.btn_save  = QPushButton("💾 Lưu")
        self.btn_copy_u = QPushButton("📋 Copy tài khoản")
        self.btn_copy_p = QPushButton("📋 Copy mật khẩu")
        self.btn_del   = QPushButton("🗑 Xóa")
        self.btn_del.setProperty("class", "danger")
        self.btn_new   = QPushButton("➕ Mới")

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

        # ── Tab 2: Generator ──────────────────────────────────────────────
        gen_w  = QWidget()
        gl     = QVBoxLayout(gen_w)
        gl.setSpacing(12)

        # Options
        opt_box = QGroupBox("Tuỳ chọn tạo mật khẩu")
        ol = QFormLayout(opt_box)

        self.gen_len = QSpinBox()
        self.gen_len.setRange(8, 64)
        self.gen_len.setValue(18)
        self.chk_upper = QCheckBox("Chữ hoa (A-Z)")
        self.chk_lower = QCheckBox("Chữ thường (a-z)")
        self.chk_digit = QCheckBox("Số (0-9)")
        self.chk_sym   = QCheckBox("Ký tự đặc biệt (!@#...)")
        self.chk_ambig = QCheckBox("Loại bỏ ký tự khó đọc (0, O, l, 1)")
        for c in [self.chk_upper, self.chk_lower, self.chk_digit, self.chk_sym]:
            c.setChecked(True)
        ol.addRow("Độ dài:", self.gen_len)
        ol.addRow(self.chk_upper)
        ol.addRow(self.chk_lower)
        ol.addRow(self.chk_digit)
        ol.addRow(self.chk_sym)
        ol.addRow(self.chk_ambig)
        gl.addWidget(opt_box)

        gen_btn = QPushButton("⚡ Tạo mật khẩu mạnh")
        gen_btn.setFixedHeight(42)
        gen_btn.clicked.connect(self._generate)
        gl.addWidget(gen_btn)

        self.gen_out = QLineEdit()
        self.gen_out.setReadOnly(True)
        self.gen_out.setPlaceholderText("Mật khẩu sẽ hiện ở đây...")
        self.gen_out.setStyleSheet("font-size:16px; font-weight:600; letter-spacing:2px;")
        gl.addWidget(self.gen_out)

        self.gen_strength_bar = QProgressBar()
        self.gen_strength_bar.setMaximumHeight(8)
        self.gen_strength_bar.setTextVisible(False)
        self.gen_strength_lbl = QLabel("")
        gl.addWidget(self.gen_strength_bar)
        gl.addWidget(self.gen_strength_lbl)

        gen_copy_btn = QPushButton("📋 Sao chép")
        gen_copy_btn.clicked.connect(lambda: self._clip(self.gen_out.text()))
        gen_use_btn  = QPushButton("➕ Dùng cho mục đang chọn")
        gen_use_btn.clicked.connect(self._use_generated)

        copy_row = QHBoxLayout()
        copy_row.addWidget(gen_copy_btn)
        copy_row.addWidget(gen_use_btn)
        gl.addLayout(copy_row)
        gl.addStretch()

        tabs.addTab(gen_w, "⚡ Tạo mật khẩu")

    def _clip(self, text: str):
        if not text:
            return
        cb = QApplication.clipboard()
        cb.setText(text)
        if _CLIP:
            try: pyperclip.copy(text)
            except Exception: pass

    def _refresh_list(self):
        q   = self.search_box.text().lower()
        lst = self.dm.get_passwords()
        self.lst.clear()
        self._visible_indices = []
        for i, p in enumerate(lst):
            label = f"{p['site']}  —  {p['username']}  ({p.get('added','')})"
            if q and q not in label.lower():
                continue
            item = QListWidgetItem(f"🔐  {label}")
            item.setData(Qt.ItemDataRole.UserRole, i)
            self.lst.addItem(item)
            self._visible_indices.append(i)

    def _on_select(self, item: QListWidgetItem):
        idx  = item.data(Qt.ItemDataRole.UserRole)
        lst  = self.dm.get_passwords()
        if 0 <= idx < len(lst):
            p = lst[idx]
            self.f_site.setText(p["site"])
            self.f_user.setText(p["username"])
            self.f_pass.setText(p["password"])
            self._current_idx = idx

    def _new_entry(self):
        self.f_site.clear()
        self.f_user.clear()
        self.f_pass.clear()
        self._current_idx = -1
        self.f_site.setFocus()

    def _save_entry(self):
        site = self.f_site.text().strip()
        user = self.f_user.text().strip()
        pwd  = self.f_pass.text()
        if not site or not user or not pwd:
            QMessageBox.warning(self, "Nexus", "Vui lòng điền đầy đủ thông tin.")
            return
        if self._current_idx >= 0:
            self.dm.update_password(self._current_idx, site, user, pwd)
        else:
            self.dm.add_password(site, user, pwd)
        self.dm.save_now()
        self._refresh_list()
        QMessageBox.information(self, "Nexus", "✔ Đã lưu mật khẩu.")

    def _copy_username(self):
        self._clip(self.f_user.text())
        QMessageBox.information(self, "Nexus", "✔ Đã sao chép tên tài khoản.")

    def _copy_password(self):
        self._clip(self.f_pass.text())
        QMessageBox.information(self, "Nexus", "✔ Đã sao chép mật khẩu.")

    def _delete_entry(self):
        if self._current_idx < 0:
            return
        ret = QMessageBox.question(
            self, "Xóa mật khẩu", "Xóa mục này?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
        )
        if ret == QMessageBox.StandardButton.Yes:
            self.dm.delete_password(self._current_idx)
            self.dm.save_now()
            self._current_idx = -1
            self.f_site.clear(); self.f_user.clear(); self.f_pass.clear()
            self._refresh_list()

    def _on_pass_changed(self, text: str):
        score, label = _password_strength(text)
        self.strength_bar.setValue(score)
        color = ("#FF453A" if score < 40 else
                 "#FFD60A" if score < 70 else "#30D158")
        self.strength_bar.setStyleSheet(
            f"QProgressBar::chunk{{background:{color};border-radius:3px}}"
        )
        self.strength_lbl.setText(f"{label}  ({score}/100)")

    def _generate(self):
        chars = ""
        if self.chk_upper.isChecked(): chars += string.ascii_uppercase
        if self.chk_lower.isChecked(): chars += string.ascii_lowercase
        if self.chk_digit.isChecked(): chars += string.digits
        if self.chk_sym.isChecked():   chars += "!@#$%^&*()-_=+[]{}|;:,.<>?"
        if self.chk_ambig.isChecked():
            for ch in "0O1lI":
                chars = chars.replace(ch, "")
        if not chars:
            QMessageBox.warning(self, "Nexus", "Chọn ít nhất một nhóm ký tự!")
            return
        n   = self.gen_len.value()
        pwd = "".join(secrets.choice(chars) for _ in range(n))
        self.gen_out.setText(pwd)
        score, label = _password_strength(pwd)
        self.gen_strength_bar.setValue(score)
        color = ("#FF453A" if score < 40 else
                 "#FFD60A" if score < 70 else "#30D158")
        self.gen_strength_bar.setStyleSheet(
            f"QProgressBar::chunk{{background:{color};border-radius:3px}}"
        )
        self.gen_strength_lbl.setText(f"Độ mạnh: {label}  ({score}/100)")

    def _use_generated(self):
        pwd = self.gen_out.text()
        if pwd:
            self.f_pass.setText(pwd)


# ════════════════════════════════════════════════════════════════════════════
# LIST DIALOG  (History / Bookmarks)
# ════════════════════════════════════════════════════════════════════════════
class ListDialog(QDialog):
    def __init__(self, title: str, items: list, on_click=None, parent=None):
        super().__init__(parent)
        self.setWindowTitle(title)
        self.resize(720, 480)
        lay = QVBoxLayout(self)
        lay.setSpacing(8)

        self.search = QLineEdit()
        self.search.setPlaceholderText("🔍 Tìm kiếm...")
        lay.addWidget(self.search)

        self.lst = QListWidget()
        lay.addWidget(self.lst, 1)

        self._items    = items
        self._on_click = on_click
        self._populate(items)
        self.search.textChanged.connect(lambda t: self._populate(
            [x for x in items
             if t.lower() in (x.get("url","") + x.get("title","")).lower()]
        ))
        if on_click:
            self.lst.itemDoubleClicked.connect(
                lambda item: (on_click(item.data(Qt.ItemDataRole.UserRole)), self.close())
            )

    def _populate(self, items: list):
        self.lst.clear()
        for it in items:
            label = f"[{it.get('time','')}]  {it.get('title','')[:50]}  ⟶  {it.get('url','')}"
            wi = QListWidgetItem(label)
            wi.setData(Qt.ItemDataRole.UserRole, it.get("url",""))
            self.lst.addItem(wi)


# ════════════════════════════════════════════════════════════════════════════
# DEVTOOLS WINDOW
# ════════════════════════════════════════════════════════════════════════════
class DevToolsWindow(QDialog):
    def __init__(self, page, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Nexus DevTools")
        self.resize(1040, 680)
        lay = QVBoxLayout(self)
        lay.setContentsMargins(0, 0, 0, 0)
        self.view = QWebEngineView()
        page.setDevToolsPage(self.view.page())
        lay.addWidget(self.view)


# ════════════════════════════════════════════════════════════════════════════
# MAIN BROWSER
# ════════════════════════════════════════════════════════════════════════════
class NexusBrowser(QMainWindow):

    def __init__(self):
        super().__init__()
        self.setWindowTitle(APP_NAME)
        self.resize(1440, 900)

        self.dark_mode      = True
        self.data_mgr       = DataManager()
        self.idm_engine     = None
        self._sidebar_open  = False
        self._devtools_wins = []
        self._ai_history    = []
        self._ai_thread     = None

        # VPN / Tor state
        self._vpn_active = False
        self._tor_active = False

        # WebEngine profile
        self.profile = QWebEngineProfile.defaultProfile()
        self.profile.setHttpCacheType(QWebEngineProfile.HttpCacheType.MemoryHttpCache)
        self.profile.setHttpUserAgent(
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/124.0.0.0 Safari/537.36"
        )
        self.ad_blocker = NexusAdBlocker(self)
        self.profile.setUrlRequestInterceptor(self.ad_blocker)
        self.profile.downloadRequested.connect(self._on_download_requested)

        self._apply_theme()
        self._build_ui()

        # Hibernate timer (5 min)
        self._hib_timer = QTimer(self)
        self._hib_timer.timeout.connect(self._hibernate_bg_tabs)
        self._hib_timer.start(300_000)

        # Blocked-count status refresh
        self._stat_timer = QTimer(self)
        self._stat_timer.timeout.connect(self._update_status)
        self._stat_timer.start(3000)

        # Keyboard shortcuts
        QShortcut(QKeySequence("F12"),       self).activated.connect(self._open_devtools)
        QShortcut(QKeySequence("Ctrl+T"),    self).activated.connect(self._open_start_page)
        QShortcut(QKeySequence("Ctrl+W"),    self).activated.connect(
            lambda: self._close_tab(self.tabs.currentIndex()))
        QShortcut(QKeySequence("Ctrl+L"),    self).activated.connect(
            lambda: (self.url_bar.setFocus(), self.url_bar.selectAll()))
        QShortcut(QKeySequence("Ctrl+R"),    self).activated.connect(self._reload_or_stop)
        QShortcut(QKeySequence("Ctrl+D"),    self).activated.connect(self._bookmark_current)
        QShortcut(QKeySequence("Ctrl+F"),    self).activated.connect(self._toggle_find)
        QShortcut(QKeySequence("Alt+Left"),  self).activated.connect(self._go_back)
        QShortcut(QKeySequence("Alt+Right"), self).activated.connect(self._go_forward)
        QShortcut(QKeySequence("Escape"),    self).activated.connect(self._close_find)
        QShortcut(QKeySequence("Ctrl+Plus"), self).activated.connect(self._zoom_in)
        QShortcut(QKeySequence("Ctrl+Minus"),self).activated.connect(self._zoom_out)
        QShortcut(QKeySequence("Ctrl+0"),    self).activated.connect(self._zoom_reset)

        self._open_start_page()

    # ══════════════════════════════════════════════════════════════════════
    # THEME
    # ══════════════════════════════════════════════════════════════════════
    def _apply_theme(self):
        self.setStyleSheet(_qss(self.dark_mode))
        p = QPalette()
        if self.dark_mode:
            bg, text, base = QColor("#141417"), QColor("#F5F5F7"), QColor("#1C1C20")
        else:
            bg, text, base = QColor("#F5F5F7"), QColor("#141417"), QColor("#FFFFFF")
        p.setColor(QPalette.ColorRole.Window,          bg)
        p.setColor(QPalette.ColorRole.WindowText,      text)
        p.setColor(QPalette.ColorRole.Base,            base)
        p.setColor(QPalette.ColorRole.AlternateBase,   bg)
        p.setColor(QPalette.ColorRole.Text,            text)
        p.setColor(QPalette.ColorRole.Button,          base)
        p.setColor(QPalette.ColorRole.ButtonText,      text)
        p.setColor(QPalette.ColorRole.Highlight,       QColor(ACCENT))
        p.setColor(QPalette.ColorRole.HighlightedText, QColor("#FFFFFF"))
        p.setColor(QPalette.ColorRole.Link,            QColor(ACCENT))
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

        # Page-load ribbon
        self.page_prog = QProgressBar()
        self.page_prog.setMaximumHeight(3)
        self.page_prog.setTextVisible(False)
        self.page_prog.setRange(0, 100)
        self.page_prog.hide()
        root.addWidget(self.page_prog)

        self._build_bm_bar(root)
        self._build_find_bar(root)

        self.splitter = QSplitter(Qt.Orientation.Horizontal)
        root.addWidget(self.splitter)

        self._build_tabs()
        self._build_sidebar()
        self._build_dl_bar(root)

        # Status bar
        self.status = QStatusBar()
        self.setStatusBar(self.status)
        self.stat_lbl = QLabel("")
        self.status.addWidget(self.stat_lbl)
        self.vpn_lbl = QLabel("")
        self.status.addPermanentWidget(self.vpn_lbl)

    # ── TOOLBAR ────────────────────────────────────────────────────────────
    def _build_toolbar(self):
        tb = QToolBar()
        tb.setMovable(False)
        tb.setIconSize(QSize(18, 18))
        self.addToolBar(tb)

        def _b(txt, tip="", w=38):
            b = QPushButton(txt); b.setFixedWidth(w); b.setToolTip(tip); return b

        self.btn_back    = _b("◀", "Quay lại  (Alt+←)")
        self.btn_forward = _b("▶", "Tiếp theo  (Alt+→)")
        self.btn_reload  = _b("↻", "Tải lại / Dừng  (Ctrl+R)")
        self.btn_home    = _b("🏠", "Trang chủ")
        for b in [self.btn_back, self.btn_forward, self.btn_reload, self.btn_home]:
            tb.addWidget(b)
        tb.addSeparator()

        self.lock_lbl = QLabel(" 🔒 ")
        self.lock_lbl.setToolTip("HTTPS")
        tb.addWidget(self.lock_lbl)

        self.url_bar = QLineEdit()
        self.url_bar.setPlaceholderText("Nhập địa chỉ web hoặc từ khóa tìm kiếm…")
        self.url_bar.returnPressed.connect(self._navigate)
        self.url_bar.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        tb.addWidget(self.url_bar)
        tb.addSeparator()

        self.btn_ai = QPushButton("🤖 AI")
        self.btn_ai.setObjectName("ai_btn")
        self.btn_ai.setFixedWidth(68)
        self.btn_ai.setCheckable(True)
        self.btn_ai.setToolTip("Nexus AI Sidebar (Gemini)")
        self.btn_ai.clicked.connect(self._toggle_sidebar)
        tb.addWidget(self.btn_ai)

        self.btn_menu = QPushButton("☰")
        self.btn_menu.setFixedWidth(38)
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
        m.addAction("➕  Tab mới  (Ctrl+T)",        self._open_start_page)
        m.addSeparator()
        # Theme
        tm = m.addMenu("🎨  Giao diện")
        tm.addAction("🌙  Tối (Dark)",    lambda: self._set_theme(True))
        tm.addAction("☀️  Sáng (Light)",  lambda: self._set_theme(False))
        m.addSeparator()
        m.addAction("🕐  Lịch sử",        self._show_history)
        m.addAction("★  Dấu trang",        self._show_bookmarks)
        m.addAction("☆  Thêm/Xóa dấu trang  (Ctrl+D)", self._bookmark_current)
        m.addSeparator()
        m.addAction("🔍  Tìm trong trang  (Ctrl+F)",    self._toggle_find)
        m.addAction("🔍  Thu phóng +  (Ctrl++)",        self._zoom_in)
        m.addAction("🔍  Thu phóng −  (Ctrl+-)",        self._zoom_out)
        m.addAction("🔍  Chuẩn  (Ctrl+0)",              self._zoom_reset)
        m.addSeparator()
        # VPN / Proxy
        vpn_m = m.addMenu("🔐  Bảo mật & Proxy")
        vpn_m.addAction("🌐  Bật/Tắt WARP VPN",  self._toggle_warp)
        vpn_m.addAction("🧅  Bật/Tắt Tor Proxy",  self._toggle_tor)
        vpn_m.addAction("🚫  Tắt tất cả proxy",   self._disable_proxy)
        vpn_m.addSeparator()
        vpn_m.addAction("🛡  Bật/Tắt Ad Blocker", self._toggle_adblock)
        m.addSeparator()
        m.addAction("🔑  Quản lý mật khẩu",       self._show_passwords)
        m.addAction("🧩  Tiện ích mở rộng",        self._show_extensions)
        m.addAction("🌏  Dịch trang này",          self._translate)
        m.addAction("💾  Lưu trang dưới dạng PDF", self._save_as_pdf)
        m.addSeparator()
        m.addAction("🗑️  Xóa dữ liệu duyệt web",   self._clear_data)
        m.addAction("ℹ️  Về Nexus Browser",         self._about)

    # ── BOOKMARK BAR ───────────────────────────────────────────────────────
    def _build_bm_bar(self, parent_lay):
        self.bm_bar = QWidget()
        bm = QHBoxLayout(self.bm_bar)
        bm.setContentsMargins(8, 2, 8, 2)
        bm.setSpacing(4)

        defaults = [
            ("🔍 Google",   "https://google.com"),
            ("▶ YouTube",   "https://youtube.com"),
            ("🐙 GitHub",   "https://github.com"),
            ("📘 Facebook", "https://facebook.com"),
            ("✉ Gmail",     "https://mail.google.com"),
            ("🤖 ChatGPT",  "https://chat.openai.com"),
        ]
        for label, url in defaults:
            b = QPushButton(label)
            b.setFixedHeight(22)
            b.clicked.connect(lambda _, u=url: self._load_url(u))
            bm.addWidget(b)

        bm.addStretch()
        add_btn = QPushButton("☆ Bookmark")
        add_btn.setFixedHeight(22)
        add_btn.clicked.connect(self._bookmark_current)
        bm.addWidget(add_btn)
        parent_lay.addWidget(self.bm_bar)

    # ── FIND BAR ───────────────────────────────────────────────────────────
    def _build_find_bar(self, parent_lay):
        self.find_bar = QWidget()
        fl = QHBoxLayout(self.find_bar)
        fl.setContentsMargins(8, 2, 8, 2)
        fl.setSpacing(6)

        lbl = QLabel("Tìm:")
        self.find_input = QLineEdit()
        self.find_input.setPlaceholderText("Nhập từ cần tìm...")
        self.find_input.setMaximumWidth(300)
        self.find_input.returnPressed.connect(self._find_next)
        self.find_input.textChanged.connect(self._find_next)

        prev_btn = QPushButton("▲")
        prev_btn.setFixedWidth(30)
        prev_btn.clicked.connect(self._find_prev)
        next_btn = QPushButton("▼")
        next_btn.setFixedWidth(30)
        next_btn.clicked.connect(self._find_next)

        self.find_count_lbl = QLabel("")
        close_btn = QPushButton("✕")
        close_btn.setFixedWidth(28)
        close_btn.clicked.connect(self._close_find)

        fl.addWidget(lbl)
        fl.addWidget(self.find_input)
        fl.addWidget(prev_btn)
        fl.addWidget(next_btn)
        fl.addWidget(self.find_count_lbl)
        fl.addStretch()
        fl.addWidget(close_btn)

        self.find_bar.hide()
        parent_lay.addWidget(self.find_bar)

    # ── TABS ───────────────────────────────────────────────────────────────
    def _build_tabs(self):
        self.tabs = QTabWidget()
        self.tabs.setDocumentMode(True)
        self.tabs.setTabsClosable(True)
        self.tabs.setMovable(True)
        self.tabs.tabCloseRequested.connect(self._close_tab)
        self.tabs.currentChanged.connect(self._on_tab_changed)

        new_tab_btn = QPushButton("＋")
        new_tab_btn.setFixedSize(30, 26)
        new_tab_btn.setToolTip("Tab mới  (Ctrl+T)")
        new_tab_btn.clicked.connect(self._open_start_page)
        self.tabs.setCornerWidget(new_tab_btn, Qt.Corner.TopRightCorner)
        self.splitter.addWidget(self.tabs)

    # ── SIDEBAR ────────────────────────────────────────────────────────────
    def _build_sidebar(self):
        self.sidebar = QWidget()
        self.sidebar.setFixedWidth(330)
        sl = QVBoxLayout(self.sidebar)
        sl.setContentsMargins(8, 6, 8, 6)
        sl.setSpacing(6)

        # Header
        hdr = QHBoxLayout()
        ttl = QLabel("🤖  <b>Nexus AI</b>")
        ttl.setTextFormat(Qt.TextFormat.RichText)
        self._ai_dot = QLabel("●")
        self._ai_dot.setStyleSheet("color:#8E8E93;font-size:10px")
        self._ai_dot.setToolTip("Chưa cấu hình")
        close_btn = QPushButton("✕")
        close_btn.setFixedSize(26, 26)
        close_btn.clicked.connect(self._toggle_sidebar)
        hdr.addWidget(ttl)
        hdr.addWidget(self._ai_dot)
        hdr.addStretch()
        hdr.addWidget(close_btn)
        sl.addLayout(hdr)

        # API Key
        kf = QFrame()
        kf.setStyleSheet("QFrame{background:#1C1C20;border-radius:8px}")
        kfl = QVBoxLayout(kf)
        kfl.setContentsMargins(8, 8, 8, 8)
        kfl.setSpacing(4)

        kl = QLabel("🔑  Gemini API Key")
        kl.setStyleSheet("font-size:11px;font-weight:600;color:#8E8E93")
        kfl.addWidget(kl)

        kr = QHBoxLayout()
        self.api_key_input = QLineEdit()
        self.api_key_input.setPlaceholderText("Dán API key vào đây…")
        self.api_key_input.setEchoMode(QLineEdit.EchoMode.Password)
        saved = self.data_mgr.get_api_key()
        if saved:
            self.api_key_input.setText(saved)
        save_btn = QPushButton("Lưu")
        save_btn.setFixedWidth(48)
        save_btn.clicked.connect(self._save_api_key)
        kr.addWidget(self.api_key_input)
        kr.addWidget(save_btn)
        kfl.addLayout(kr)

        hint = QLabel('<a href="https://aistudio.google.com/app/apikey" '
                      'style="color:#0078D4;">Lấy key miễn phí →</a>')
        hint.setOpenExternalLinks(True)
        hint.setStyleSheet("font-size:10px")
        kfl.addWidget(hint)
        sl.addWidget(kf)

        if saved:
            self._dot_ready()

        # Divider
        div = QFrame(); div.setFrameShape(QFrame.Shape.HLine)
        sl.addWidget(div)

        # Chat area
        self.ai_chat = QTextEdit()
        self.ai_chat.setReadOnly(True)
        self.ai_chat.setOpenLinks(True)
        self.ai_chat.setHtml(
            "<p style='color:#8E8E93;margin:6px 2px'>"
            "<b style='color:#0078D4'>Nexus AI:</b>&nbsp;"
            "Xin chào! Nhập API key ở trên rồi bắt đầu hỏi nhé 🚀"
            "</p>"
        )
        sl.addWidget(self.ai_chat, 1)

        # Status + clear
        cr = QHBoxLayout()
        self._think_lbl = QLabel("")
        self._think_lbl.setStyleSheet("color:#8E8E93;font-size:11px")
        clr_btn = QPushButton("🗑 Xóa chat")
        clr_btn.setFixedHeight(24)
        clr_btn.clicked.connect(self._clear_ai_chat)
        cr.addWidget(self._think_lbl)
        cr.addStretch()
        cr.addWidget(clr_btn)
        sl.addLayout(cr)

        # Input
        ir = QHBoxLayout()
        self.ai_input = QLineEdit()
        self.ai_input.setPlaceholderText("Hỏi Nexus AI…")
        self.ai_input.returnPressed.connect(self._send_ai)
        self._send_btn = QPushButton("Gửi")
        self._send_btn.setFixedWidth(56)
        self._send_btn.clicked.connect(self._send_ai)
        ir.addWidget(self.ai_input)
        ir.addWidget(self._send_btn)
        sl.addLayout(ir)

        self.splitter.addWidget(self.sidebar)
        self.sidebar.setVisible(False)
        self.splitter.setSizes([1440, 0])

    # ── DOWNLOAD BAR ───────────────────────────────────────────────────────
    def _build_dl_bar(self, parent_lay):
        self.dl_bar = QWidget()
        self.dl_bar.setStyleSheet("border-top:1px solid #2C2C30")
        self.dl_lay = QVBoxLayout(self.dl_bar)
        self.dl_lay.setContentsMargins(10, 4, 10, 4)
        self.dl_lay.setSpacing(4)
        self.dl_bar.hide()
        parent_lay.addWidget(self.dl_bar)

    # ══════════════════════════════════════════════════════════════════════
    # STATUS BAR
    # ══════════════════════════════════════════════════════════════════════
    def _update_status(self):
        blocked = self.ad_blocker.blocked
        ab_on   = self.ad_blocker.enabled
        ab_txt  = f"🛡 {blocked} quảng cáo đã chặn" if ab_on else "🛡 AdBlock TẮT"
        self.stat_lbl.setText(ab_txt)

        vpn_parts = []
        if self._vpn_active: vpn_parts.append("🌐 WARP VPN")
        if self._tor_active:  vpn_parts.append("🧅 Tor")
        self.vpn_lbl.setText("  ".join(vpn_parts) if vpn_parts else "")

    # ══════════════════════════════════════════════════════════════════════
    # TAB MANAGEMENT
    # ══════════════════════════════════════════════════════════════════════
    def _make_view(self) -> QWebEngineView:
        view = QWebEngineView()
        view.titleChanged.connect(lambda t, v=view: self._update_tab_title(v, t))
        view.loadProgress.connect(self._on_load_progress)
        view.loadFinished.connect(self._on_load_finished)
        view.urlChanged.connect(lambda u, v=view: self._on_url_changed(u, v))
        view.iconChanged.connect(lambda ic, v=view: self._update_tab_icon(v, ic))
        view.page().renderProcessTerminated.connect(
            lambda _s, _ec, v=view: QTimer.singleShot(600, lambda: self._crash_reload(v))
        )
        return view

    def _open_start_page(self):
        view = self._make_view()
        view.setHtml(build_start_page(self.dark_mode), QUrl("about:blank"))
        idx = self.tabs.addTab(view, "Trang chủ")
        self.tabs.setCurrentIndex(idx)

    def _add_tab(self, url: str, title: str = "Đang tải…"):
        if self._is_dangerous(url):
            self._warn_av(url); return
        qurl = QUrl(url)
        if not qurl.scheme():
            qurl = QUrl("https://" + url)
        view = self._make_view()
        view.setUrl(qurl)
        idx = self.tabs.addTab(view, title[:20])
        self.tabs.setCurrentIndex(idx)
        # Inject ad-hide CSS after page loads
        view.loadFinished.connect(lambda ok, v=view: self._inject_ad_css(v) if ok else None)

    def _current_view(self):
        w = self.tabs.currentWidget()
        return w if isinstance(w, QWebEngineView) else None

    def _close_tab(self, idx: int):
        if self.tabs.count() <= 1:
            self.close(); return
        w = self.tabs.widget(idx)
        self.tabs.removeTab(idx)
        if isinstance(w, QWebEngineView):
            w.setUrl(QUrl("about:blank"))
            w.deleteLater()
        elif isinstance(w, QLabel):
            w.deleteLater()

    def _on_tab_changed(self, idx: int):
        if idx < 0: return
        w = self.tabs.widget(idx)
        if isinstance(w, QLabel) and w.property("url"):
            QTimer.singleShot(0, lambda: self._restore_tab(w))
        elif isinstance(w, QWebEngineView):
            url_str = w.url().toString()
            if url_str != "about:blank":
                self.url_bar.setText(url_str)
            self.setWindowTitle(f"{APP_NAME} — {w.title()}")
            self._update_lock_icon(w.url())

    def _update_tab_title(self, view, title: str):
        idx = self.tabs.indexOf(view)
        if idx >= 0:
            self.tabs.setTabText(idx, (title[:20] if title else "…"))
            if self.tabs.currentIndex() == idx:
                self.setWindowTitle(f"{APP_NAME} — {title}")

    def _update_tab_icon(self, view, icon):
        idx = self.tabs.indexOf(view)
        if idx >= 0 and not icon.isNull():
            self.tabs.setTabIcon(idx, icon)

    def _inject_ad_css(self, view):
        if self.ad_blocker.enabled:
            view.page().runJavaScript(AD_HIDE_JS)

    def _crash_reload(self, view):
        idx = self.tabs.indexOf(view)
        if idx >= 0:
            url = view.url().toString()
            if url and url not in ("about:blank", ""):
                view.reload()

    # ══════════════════════════════════════════════════════════════════════
    # NAVIGATION
    # ══════════════════════════════════════════════════════════════════════
    def _navigate(self):
        text = self.url_bar.text().strip()
        if not text: return
        # Decide: search or URL
        if re.match(r'^https?://', text):
            url = text
        elif re.match(r'^[a-zA-Z0-9\-]+(\.[a-zA-Z]{2,})(/.*)?$', text):
            url = "https://" + text
        else:
            url = "https://www.google.com/search?q=" + requests.utils.quote(text)

        if self._is_dangerous(url):
            self._warn_av(url); return
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
        if v and v.history().canGoBack(): v.back()

    def _go_forward(self):
        v = self._current_view()
        if v and v.history().canGoForward(): v.forward()

    def _reload_or_stop(self):
        v = self._current_view()
        if not v: return
        if v.page().isLoading():
            v.stop(); self.btn_reload.setText("↻")
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
            self.lock_lbl.setText(" 🔒 "); self.lock_lbl.setToolTip("HTTPS — kết nối bảo mật")
        elif qurl.scheme() == "http":
            self.lock_lbl.setText(" 🔓 "); self.lock_lbl.setToolTip("HTTP — không bảo mật")
        else:
            self.lock_lbl.setText("    ")

    def _on_load_progress(self, pct: int):
        if 0 < pct < 100:
            self.page_prog.show(); self.page_prog.setValue(pct)
            self.btn_reload.setText("✕")
        else:
            self.page_prog.setValue(100)
            QTimer.singleShot(400, self.page_prog.hide)
            self.btn_reload.setText("↻")

    def _on_load_finished(self, ok: bool):
        self.btn_reload.setText("↻")
        v = self._current_view()
        if not ok and v:
            # Only show error page if we actually tried to load an http URL
            url = v.url().toString()
            if url.startswith("http"):
                v.setHtml(ERROR_PAGE_HTML, QUrl("about:error"))

    def _is_dangerous(self, url: str) -> bool:
        danger = ["malware", "phishing", "virus", "trojan", "ransomware"]
        low = url.lower()
        return any(d in low for d in danger)

    def _warn_av(self, url: str):
        QMessageBox.critical(
            self, "⚠ Nexus Security",
            f"URL nguy hiểm bị chặn:\n{url[:120]}"
        )

    # ══════════════════════════════════════════════════════════════════════
    # FIND IN PAGE
    # ══════════════════════════════════════════════════════════════════════
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
        if v: v.findText("")

    def _find_next(self):
        v = self._current_view(); q = self.find_input.text()
        if v and q: v.findText(q)

    def _find_prev(self):
        v = self._current_view(); q = self.find_input.text()
        if v and q:
            v.findText(q, QWebEnginePage.FindFlag.FindBackward)

    # ══════════════════════════════════════════════════════════════════════
    # DEVTOOLS
    # ══════════════════════════════════════════════════════════════════════
    def _open_devtools(self):
        v = self._current_view()
        if not v: return
        dw = DevToolsWindow(v.page(), self)
        self._devtools_wins.append(dw)
        dw.finished.connect(lambda: self._devtools_wins.remove(dw)
                            if dw in self._devtools_wins else None)
        dw.show()

    # ══════════════════════════════════════════════════════════════════════
    # AI SIDEBAR
    # ══════════════════════════════════════════════════════════════════════
    def _toggle_sidebar(self):
        self._sidebar_open = not self._sidebar_open
        self.sidebar.setVisible(self._sidebar_open)
        self.btn_ai.setChecked(self._sidebar_open)
        self.splitter.setSizes([1100, 330] if self._sidebar_open else [1440, 0])

    def _save_api_key(self):
        key = self.api_key_input.text().strip()
        if not key:
            QMessageBox.warning(self, "Nexus AI", "Vui lòng nhập API key.")
            return
        self.data_mgr.set_api_key(key)
        self._dot_ready()
        self._append_ai("<span style='color:#30D158'>✔ API key đã lưu. Sẵn sàng chat!</span>")

    def _dot_ready(self):
        self._ai_dot.setStyleSheet("color:#30D158;font-size:10px")
        self._ai_dot.setToolTip("Sẵn sàng — Gemini 2.0 Flash")

    def _dot_busy(self):
        self._ai_dot.setStyleSheet("color:#FFD60A;font-size:10px")
        self._ai_dot.setToolTip("Đang xử lý…")

    def _dot_error(self):
        self._ai_dot.setStyleSheet("color:#FF453A;font-size:10px")
        self._ai_dot.setToolTip("Lỗi kết nối")

    def _append_ai(self, html: str):
        self.ai_chat.append(f"<p style='margin:6px 2px;line-height:1.5'>{html}</p>")
        self.ai_chat.verticalScrollBar().setValue(
            self.ai_chat.verticalScrollBar().maximum()
        )

    def _clear_ai_chat(self):
        self._ai_history.clear()
        self.ai_chat.setHtml(
            "<p style='color:#8E8E93;margin:6px 2px'>"
            "<b style='color:#0078D4'>Nexus AI:</b>&nbsp;"
            "Lịch sử đã xóa. Bắt đầu cuộc trò chuyện mới!"
            "</p>"
        )

    def _send_ai(self):
        text = self.ai_input.text().strip()
        if not text: return

        key = self.data_mgr.get_api_key()
        if not key:
            self._append_ai(
                "<span style='color:#FF453A'>⚠ Chưa có API key. "
                "Nhập key ở trên rồi nhấn Lưu.</span>"
            )
            return

        if self._ai_thread and self._ai_thread.isRunning():
            return

        self._append_ai(
            f"<b style='color:#A78BFA'>Bạn:</b>&nbsp;{self._esc(text)}"
        )
        self.ai_input.clear()
        self.ai_input.setEnabled(False)
        self._send_btn.setEnabled(False)
        self._think_lbl.setText("⏳ Đang suy nghĩ…")
        self._dot_busy()

        self._ai_thread = GeminiThread(key, self._ai_history, text, self)
        self._ai_thread.reply.connect(lambda r, t=text: self._ai_got_reply(t, r))
        self._ai_thread.err.connect(self._ai_got_error)
        self._ai_thread.start()

    def _ai_got_reply(self, user_txt: str, reply: str):
        self._ai_history.append({"role":"user",  "parts":[{"text":user_txt}]})
        self._ai_history.append({"role":"model", "parts":[{"text":reply}]})
        if len(self._ai_history) > 40:
            self._ai_history = self._ai_history[-40:]
        html = self._esc(reply).replace("\n", "<br>")
        self._append_ai(f"<b style='color:#0078D4'>Nexus AI:</b>&nbsp;{html}")
        self._reset_ai_ui()
        self._dot_ready()

    def _ai_got_error(self, code: str):
        msgs = {
            "no_key":     "⚠ Chưa có API key.",
            "bad_key":    "❌ API key không hợp lệ — kiểm tra tại Google AI Studio.",
            "rate_limit": "⏳ Vượt giới hạn. Đợi 1 phút rồi thử lại.",
            "no_network": "🌐 Không có kết nối Internet.",
            "timeout":    "⏱ Gemini phản hồi quá chậm. Thử lại.",
            "empty":      "⚠ Gemini trả về rỗng. Thử lại.",
        }
        self._append_ai(
            f"<span style='color:#FF453A'>"
            f"{msgs.get(code, f'⚠ Lỗi: {code}')}</span>"
        )
        self._reset_ai_ui()
        self._dot_error()

    def _reset_ai_ui(self):
        self.ai_input.setEnabled(True)
        self._send_btn.setEnabled(True)
        self._think_lbl.setText("")
        self.ai_input.setFocus()

    @staticmethod
    def _esc(t: str) -> str:
        return t.replace("&","&amp;").replace("<","&lt;").replace(">","&gt;")

    # ══════════════════════════════════════════════════════════════════════
    # TAB HIBERNATION
    # ══════════════════════════════════════════════════════════════════════
    def _hibernate_bg_tabs(self):
        cur = self.tabs.currentIndex()
        indices = [i for i in range(self.tabs.count())
                   if i != cur and isinstance(self.tabs.widget(i), QWebEngineView)]
        for i in reversed(indices):
            w     = self.tabs.widget(i)
            url   = w.url().toString()
            title = (w.title() or url)[:18]
            if not url or url == "about:blank":
                continue
            self.tabs.removeTab(i)
            w.setUrl(QUrl("about:blank"))
            QTimer.singleShot(200, w.deleteLater)
            ph = QLabel(f"❄  {title}\n\nClick để hồi phục tab")
            ph.setAlignment(Qt.AlignmentFlag.AlignCenter)
            ph.setStyleSheet(
                "font-size:15px;color:#8E8E93;"
                "background:#141417;border-radius:10px"
            )
            ph.setProperty("url",   url)
            ph.setProperty("title", title)
            self.tabs.insertTab(i, ph, f"❄ {title[:10]}")

    def _restore_tab(self, ph):
        idx = self.tabs.indexOf(ph)
        if idx < 0: return
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
        if not path: return

        self.dl_bar.show()
        while self.dl_lay.count():
            old = self.dl_lay.takeAt(0)
            if old.widget(): old.widget().deleteLater()

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

    # ══════════════════════════════════════════════════════════════════════
    # ZOOM
    # ══════════════════════════════════════════════════════════════════════
    def _zoom_in(self):
        v = self._current_view()
        if v: v.setZoomFactor(min(5.0, v.zoomFactor() + 0.1))

    def _zoom_out(self):
        v = self._current_view()
        if v: v.setZoomFactor(max(0.25, v.zoomFactor() - 0.1))

    def _zoom_reset(self):
        v = self._current_view()
        if v: v.setZoomFactor(1.0)

    # ══════════════════════════════════════════════════════════════════════
    # VPN / TOR  (nâng cấp)
    # ══════════════════════════════════════════════════════════════════════
    def _toggle_warp(self):
        if self._vpn_active:
            # Turn off
            if not self._tor_active:
                QNetworkProxy.setApplicationProxy(QNetworkProxy(QNetworkProxy.ProxyType.NoProxy))
            self._vpn_active = False
            self._update_status()
            QMessageBox.information(self, "WARP VPN", "🌐 WARP VPN đã TẮT.")
        else:
            if self._tor_active:
                QMessageBox.warning(self, "Xung đột",
                    "Tor Proxy đang bật. Tắt Tor trước rồi mới bật WARP.")
                return
            proxy = QNetworkProxy(QNetworkProxy.ProxyType.Socks5Proxy, "127.0.0.1", 40001)
            QNetworkProxy.setApplicationProxy(proxy)
            self._vpn_active = True
            self._update_status()
            QMessageBox.information(self, "WARP VPN",
                "✅ WARP VPN đã BẬT\n"
                "SOCKS5 → 127.0.0.1:40001\n\n"
                "⚠ Yêu cầu: Cloudflare WARP client đang chạy trên máy.\n"
                "Tải tại: one.one.one.one"
            )

    def _toggle_tor(self):
        if self._tor_active:
            if not self._vpn_active:
                QNetworkProxy.setApplicationProxy(QNetworkProxy(QNetworkProxy.ProxyType.NoProxy))
            self._tor_active = False
            self._update_status()
            QMessageBox.information(self, "Tor Proxy", "🧅 Tor Proxy đã TẮT.")
        else:
            if self._vpn_active:
                QMessageBox.warning(self, "Xung đột",
                    "WARP VPN đang bật. Tắt WARP trước rồi mới bật Tor.")
                return
            proxy = QNetworkProxy(QNetworkProxy.ProxyType.Socks5Proxy, "127.0.0.1", 9050)
            QNetworkProxy.setApplicationProxy(proxy)
            self._tor_active = True
            self._update_status()
            QMessageBox.information(self, "Tor Proxy",
                "✅ Tor Proxy đã BẬT\n"
                "SOCKS5 → 127.0.0.1:9050\n\n"
                "⚠ Yêu cầu: Tor Browser / Tor service đang chạy.\n"
                "Tải tại: torproject.org"
            )

    def _disable_proxy(self):
        QNetworkProxy.setApplicationProxy(QNetworkProxy(QNetworkProxy.ProxyType.NoProxy))
        self._vpn_active = False
        self._tor_active = False
        self._update_status()
        QMessageBox.information(self, "Proxy", "✔ Đã tắt tất cả proxy.")

    def _toggle_adblock(self):
        self.ad_blocker.enabled = not self.ad_blocker.enabled
        state = "BẬT" if self.ad_blocker.enabled else "TẮT"
        self._update_status()
        QMessageBox.information(self, "Ad Blocker",
            f"🛡 Ad Blocker hiện đã {state}.\n"
            "Tải lại trang để áp dụng thay đổi."
        )

    # ══════════════════════════════════════════════════════════════════════
    # MENU ACTIONS
    # ══════════════════════════════════════════════════════════════════════
    def _show_history(self):
        ListDialog(
            "🕐 Lịch Sử Duyệt Web",
            self.data_mgr.data["history"],
            on_click=self._load_url,
            parent=self,
        ).exec()

    def _show_bookmarks(self):
        ListDialog(
            "★ Dấu Trang",
            self.data_mgr.data["bookmarks"],
            on_click=self._load_url,
            parent=self,
        ).exec()

    def _bookmark_current(self):
        v = self._current_view()
        if not v: return
        url   = v.url().toString()
        title = v.title()
        if not url.startswith("http"): return
        if self.data_mgr.is_bookmarked(url):
            self.data_mgr.remove_bookmark(url)
            QMessageBox.information(self, "Dấu trang", f"Đã xóa dấu trang:\n{title}")
        else:
            self.data_mgr.add_bookmark(url, title)
            QMessageBox.information(self, "Dấu trang", f"★ Đã lưu:\n{title}")

    def _show_passwords(self):
        dlg = PasswordManagerDialog(self.data_mgr, self)
        dlg.exec()

    def _show_extensions(self):
        QMessageBox.information(
            self, "Extensions Manager",
            "Nexus Browser v4.0 — Tiện ích tích hợp:\n\n"
            "🛡  Network Ad Blocker  (luôn bật)\n"
            "💉  CSS Ad-hide Injector  (luôn bật)\n"
            "🔒  HTTPS Enforcer  (tự động)\n"
            "❄  Tab Hibernation  (5 phút)\n"
            "📥  IDM 64-Thread Downloader\n"
            "🤖  Nexus AI  (Gemini 2.0 Flash)\n\n"
            "Thêm tiện ích bên ngoài — sắp ra mắt."
        )

    def _translate(self):
        v = self._current_view()
        if v:
            url = v.url().toString()
            if url.startswith("http"):
                v.setUrl(QUrl(
                    f"https://translate.google.com/translate"
                    f"?sl=auto&tl=vi&u={requests.utils.quote(url)}"
                ))

    def _save_as_pdf(self):
        v = self._current_view()
        if not v:
            return
        path, _ = QFileDialog.getSaveFileName(
            self, "Lưu PDF", f"{v.title()}.pdf", "PDF (*.pdf)"
        )
        if path:
            v.page().printToPdf(path)
            QMessageBox.information(self, "Lưu PDF", f"✔ Đã lưu:\n{path}")

    def _clear_data(self):
        ret = QMessageBox.question(
            self, "Xóa dữ liệu",
            "Xóa toàn bộ lịch sử, dấu trang và cache HTTP?\n"
            "(API key và mật khẩu đã lưu sẽ được giữ lại)",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
        )
        if ret == QMessageBox.StandardButton.Yes:
            self.data_mgr.clear_history()
            self.data_mgr.data["bookmarks"] = []
            self.data_mgr.save_now()
            self.profile.clearHttpCache()
            QMessageBox.information(self, "Hoàn tất", "✔ Đã xóa lịch sử và cache.")

    def _about(self):
        QMessageBox.about(
            self, f"Về {APP_NAME}",
            f"{APP_NAME}  v{APP_VERSION}\n"
            "──────────────────────────────────\n"
            "Developed by Loc Shadow\n\n"
            "✔ Fluent Design UI  (Dark / Light)\n"
            "✔ Tab Hibernation — tiết kiệm RAM\n"
            "✔ IDM 64-Thread Download Engine\n"
            "✔ Network-Level + CSS Ad Blocker\n"
            "✔ F12 DevTools  (Chromium)\n"
            "✔ Find in Page  (Ctrl+F)\n"
            "✔ WARP VPN + Tor Proxy\n"
            "✔ PDF Export\n"
            "✔ Nexus AI  (Google Gemini 2.0 Flash)\n"
            "✔ Password Manager + Generator\n"
            "✔ Keyboard Shortcuts\n"
            "──────────────────────────────────\n"
            "Built with PyQt6 + WebEngine"
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

    # Bootstrap dark palette before window opens
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
    p.setColor(QPalette.ColorRole.Link,            QColor(ACCENT))
    p.setColor(QPalette.ColorRole.Highlight,       QColor(ACCENT))
    p.setColor(QPalette.ColorRole.HighlightedText, QColor("#FFFFFF"))
    app.setPalette(p)

    browser = NexusBrowser()
    browser.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
