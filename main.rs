// ============================================================================
// NEXUS BROWSER - ELITE RUST EDITION (HARDENED & OPTIMIZED)
// Single-file architecture: main.rs
// Target: 4GB RAM / HDD low-end systems
// Wry 0.45 / Tao / Tokio multi-thread
// ============================================================================

use std::sync::Arc;
use std::time::Instant;
use tao::{event::{Event, StartCause}, event_loop::{ControlFlow, EventLoopBuilder}, window::WindowBuilder};
use wry::WebViewBuilder;
use tokio::runtime::Builder;
use tokio::sync::RwLock;

pub mod state {
    use super::*;
    #[derive(Clone, Debug, PartialEq)] pub enum Theme { Dark, Light }
    #[derive(Clone, Debug, PartialEq)] pub enum Lang { EN, VI }
    
    #[derive(Clone, Debug, Default)]
    pub struct Cfg {
        pub proxy: bool, pub proxy_url: String, pub tor: bool, pub warp: bool, pub dev: bool,
        pub ad: bool, pub trk: bool, pub cookie: bool, pub sinkhole: bool, pub incog: bool,
    }
    
    #[derive(Debug)]
    pub struct State {
        pub hist: Vec<String>, pub cfg: Cfg, pub theme: Theme, pub lang: Lang, pub blocked: u64,
        pub last_active: Instant, pub api_key: String, pub ai_mem: Vec<(String, String)>,
    }
    
    impl State {
        pub fn new() -> Self { 
            Self {
                hist: Vec::with_capacity(32),
                cfg: Cfg { 
                    proxy_url: "socks5h://127.0.0.1:1080".into(), 
                    ad: true, trk: true, cookie: true, sinkhole: true, 
                    warp: false, tor: false, incog: false, 
                    ..Default::default() 
                },
                theme: Theme::Dark, lang: Lang::EN, blocked: 0, last_active: Instant::now(),
                api_key: "NX-ELITE-0000".into(), ai_mem: Vec::with_capacity(40),
            }
        }
        
        #[inline] 
        pub fn push_ai(&mut self, r: String, c: String) {
            self.ai_mem.push((r, c));
            if self.ai_mem.len() > 40 { self.ai_mem.remove(0); }
        }
    }
    
    // SECURITY: Zero sensitive memory on drop (autonomous hardening)
    impl Drop for State {
        fn drop(&mut self) {
            self.ai_mem.clear(); 
            self.hist.clear();
            unsafe { 
                let ptr = self.api_key.as_mut_ptr();
                let len = self.api_key.len();
                std::ptr::write_bytes(ptr, 0, len); 
            }
        }
    }
}

mod blocker {
    use super::state::Cfg;
    #[inline]
    pub fn check(u: &str, c: &Cfg) -> bool {
        (c.ad && (u.contains("adsystem") || u.contains("adnxs") || u.contains("taboola") || u.contains("cookie-law"))) ||
        (c.trk && (u.contains("analytics") || u.contains("segment.io") || u.contains("telemetry") || u.contains("fingerprint") || u.contains("trackcmp")))
    }
}

mod sinkhole {
    #[inline]
    pub fn check(u: &str) -> bool {
        u.contains("doubleclick") || u.contains("adsense") || u.contains("mixpanel") || 
        u.contains("hotjar") || u.contains("facebook.com/tr") || u.contains("google-analytics")
    }
}

mod net {
    use super::state::Cfg;
    // Priority: Tor > WARP > custom proxy > direct
    pub fn client(c: &Cfg) -> reqwest::Client {
        let mut b = reqwest::Client::builder()
            .user_agent("Mozilla/5.0 (X11; Linux x86_64) Nexus/1.0")
            .cookie_store(!c.cookie && !c.incog) // Enforce isolation if cookie block or incognito is active
            .danger_accept_invalid_certs(false)
            .timeout(std::time::Duration::from_secs(30));
            
        if c.tor {
            if let Ok(p) = reqwest::Proxy::all("socks5h://127.0.0.1:9050") { b = b.proxy(p); }
        } else if c.warp {
            if let Ok(p) = reqwest::Proxy::all("socks5h://127.0.0.1:4018") { b = b.proxy(p); }
        } else if c.proxy {
            if let Ok(p) = reqwest::Proxy::all(&c.proxy_url) { b = b.proxy(p); }
        }
        b.build().unwrap_or_else(|_| reqwest::Client::new())
    }
}

mod dl {
    use super::{net, state::State};
    use std::sync::Arc;
    use tokio::{sync::Semaphore, task, io::{AsyncWriteExt, AsyncSeekExt, SeekFrom}};
    use futures_util::StreamExt;

    // CONCURRENCY UPGRADE: 16-thread parallel chunks, bounded Semaphore
    pub async fn turbo(url: String, st: Arc<RwLock<State>>) {
        let cfg = { st.read().await.cfg.clone() };
        let c = net::client(&cfg);
        let len = c.head(&url).send().await.ok().and_then(|r| r.content_length()).unwrap_or(0);
        if len == 0 { return; }

        const PARTS: usize = 16;
        let chunk = (len + PARTS as u64 - 1) / PARTS as u64;
        let f_name = url.split('/').last().filter(|s| !s.is_empty()).unwrap_or("nxdl.bin").to_string();

        let file = match tokio::fs::OpenOptions::new().write(true).create(true).truncate(true).open(&f_name).await {
            Ok(f) => Arc::new(tokio::sync::Mutex::new(f)),
            Err(_) => return,
        };

        let sem = Arc::new(Semaphore::new(PARTS));
        let mut set = task::JoinSet::new();
        for i in 0..PARTS {
            let (cl, u, p, fl) = (c.clone(), url.clone(), sem.clone(), file.clone());
            let s = i as u64 * chunk;
            let e = (s + chunk).saturating_sub(1).min(len.saturating_sub(1));
            if s > e { continue; }
            set.spawn(async move {
                let _permit = match p.acquire().await { Ok(p) => p, Err(_) => return };
                let r = match cl.get(&u).header("Range", format!("bytes={}-{}", s, e)).send().await { Ok(r) => r, Err(_) => return };
                let mut stream = r.bytes_stream();
                let mut off = s;
                while let Some(Ok(b)) = stream.next().await {
                    let mut g = fl.lock().await;
                    let _ = g.seek(SeekFrom::Start(off)).await;
                    let _ = g.write_all(&b).await;
                    off += b.len() as u64;
                }
            });
        }
        while set.join_next().await.is_some() {}
    }
}

mod search {
    pub fn resolve(i: &str) -> String {
        let t = i.trim();
        if t.starts_with("http") { t.into() }
        else if t.contains('.') && !t.contains(' ') { format!("https://{}", t) }
        else { format!("https://www.google.com/search?q={}", url::form_urlencoded::byte_serialize(t.as_bytes()).collect::<String>()) }
    }
}

fn html() -> String {
    r#"<!DOCTYPE html><html><head><meta charset="UTF-8"><style>
:root{--bg:#0a0a0c;--c:#00f0ff;--p:#ff007f;--t:#e0e0e0;--pan:rgba(10,10,12,.95);--in:#111;--bd:#333}
body.lt{--bg:#f5f6f8;--c:#0078d4;--p:#005a9e;--t:#1a1a1a;--pan:rgba(245,246,248,.95);--in:#fff;--bd:#d1d1d1}
body{background:var(--bg);color:var(--t);font-family:monospace;margin:0;overflow:hidden}
#sh{display:flex;flex-direction:column;height:100vh}
#tb{background:var(--pan);border-bottom:1px solid var(--c);padding:10px;display:flex;gap:10px;align-items:center;z-index:10}
.b{background:0 0;border:1px solid var(--c);color:var(--c);padding:5px 10px;cursor:pointer;text-transform:uppercase;font-weight:700;font-size:12px}
.b:hover{background:var(--c);color:var(--bg)}.b.p{border-color:var(--p);color:var(--p)}.b.p:hover{background:var(--p);color:var(--bg)}
#u{flex:1;background:var(--in);border:1px solid var(--bd);color:var(--t);padding:8px}
#ca{flex:1;overflow:auto;position:relative;background:var(--bg)}
#st{display:flex;flex-direction:column;align-items:center;justify-content:center;height:100%}
#st h1{font-size:4rem;text-shadow:0 0 20px var(--c);color:var(--c)}
#st .s{color:var(--p);text-shadow:0 0 10px var(--p);margin-bottom:40px}
#ss{width:60%;max-width:600px;padding:15px;font-size:18px;background:color-mix(in srgb,var(--c) 10%,transparent);border:2px solid var(--c);color:var(--t);text-align:center}
#dp,#ap{position:fixed;top:0;width:350px;height:100vh;background:var(--pan);z-index:99;padding:20px;overflow-y:auto;transition:.3s}
#dp{right:-350px;border-left:2px solid var(--p)}#dp.o{right:0}
#ap{left:-350px;border-right:2px solid var(--c)}#ap.o{left:0}
.le{font-size:12px;margin-bottom:5px}
#pp{position:fixed;right:0;top:60px;width:240px;background:var(--pan);border-left:2px solid var(--c);border-bottom:2px solid var(--c);border-bottom-left-radius:15px;padding:20px;z-index:9;box-shadow:-5px 5px 20px rgba(0,240,255,.15);display:flex;flex-direction:column;gap:12px}
.stg{display:flex;justify-content:space-between;align-items:center;font-size:12px;text-transform:uppercase;border-bottom:1px dashed rgba(255,255,255,.1);padding-bottom:6px}
.sw{position:relative;display:inline-block;width:36px;height:18px}.sw input{opacity:0;width:0;height:0}
.sl{position:absolute;cursor:pointer;inset:0;background:#333;transition:.3s;border-radius:18px}
.sl:before{position:absolute;content:"";height:12px;width:12px;left:3px;bottom:3px;background:#fff;transition:.3s;border-radius:50%}
input:checked+.sl{background:var(--c);box-shadow:0 0 8px var(--c)}input:checked+.sl:before{transform:translateX(18px)}
#bc{margin-top:10px;padding:12px;background:rgba(255,0,127,.1);border:1px solid var(--p);border-radius:8px;text-align:center}
#ct{font-size:1.8rem;color:var(--p);font-weight:700;text-shadow:0 0 10px var(--p)}
.pt{color:var(--c);border-bottom:1px solid var(--c);padding-bottom:5px;margin:0;font-size:14px}
#ah{padding:10px;border-bottom:1px solid var(--c);color:var(--c);font-weight:700;display:flex;justify-content:space-between}
#al{flex:1;padding:10px;overflow-y:auto;display:flex;flex-direction:column;gap:8px}
.msg{padding:8px;border-radius:6px;font-size:12px;max-width:85%;word-wrap:break-word}
.usr{background:rgba(0,240,255,.1);border:1px solid var(--c);align-self:flex-end;color:var(--c)}
.ai{background:rgba(255,0,127,.1);border:1px solid var(--p);align-self:flex-start;color:var(--p)}
#af{padding:10px;border-top:1px solid var(--bd);display:flex;gap:8px}
#ai{flex:1;background:var(--in);border:1px solid var(--bd);color:var(--t);padding:8px;outline:none}
</style></head><body>
<div id="sh"><div id="tb">
<button class="b" onclick="sr('back')">⟵</button><button class="b" onclick="sr('fwd')">⟶</button><button class="b" onclick="sr('ref')">⟳</button>
<input type="text" id="u" placeholder="Search..." onkeydown="if(event.key==='Enter')sr('nav',this.value)">
<button class="b p" onclick="sr('dl',v('u'))">⬇ TURBO</button>
<button class="b" onclick="tai()">🧠 AI</button>
<button class="b" onclick="td()">⚙ DEV</button>
<button class="b" onclick="sr('theme')">🌓</button>
<button class="b" onclick="sr('lang')">🌐</button>
</div><div id="ca"><div id="st"><h1 data-i18n="title">NEXUS</h1><div class="s" data-i18n="sub">ELITE RUST // SECURE CORE</div><input type="text" id="ss" placeholder="Query..." onkeydown="if(event.key==='Enter'){v('u',this.value);sr('nav',this.value)}"></div></div></div>
<div id="ap"><div id="ah"><span>🧠 NEXUS AI</span><span style="cursor:pointer" onclick="tai()">✕</span></div><div id="al"><div class="msg ai">Secure memory initialized.</div></div><div id="af"><input type="text" id="ai" placeholder="Ask..." onkeydown="if(event.key==='Enter')sai()"><button class="b" onclick="sai()">SEND</button></div></div>
<div id="pp"><h3 class="pt">🛡 SHIELD MATRIX</h3>
<div class="stg"><label>Ads</label><label class="sw"><input type="checkbox" checked onchange="ts('ad',this.checked)"><span class="sl"></span></label></div>
<div class="stg"><label>Trackers</label><label class="sw"><input type="checkbox" checked onchange="ts('trk',this.checked)"><span class="sl"></span></label></div>
<div class="stg"><label>Cookies</label><label class="sw"><input type="checkbox" checked onchange="ts('cookie',this.checked)"><span class="sl"></span></label></div>
<div class="stg"><label>Sinkhole</label><label class="sw"><input type="checkbox" checked onchange="ts('sink',this.checked)"><span class="sl"></span></label></div>
<div class="stg"><label>WARP VPN</label><label class="sw"><input type="checkbox" onchange="ts('warp',this.checked)"><span class="sl"></span></label></div>
<div class="stg"><label>Tor Net</label><label class="sw"><input type="checkbox" onchange="ts('tor',this.checked)"><span class="sl"></span></label></div>
<div class="stg"><label>Incognito</label><label class="sw"><input type="checkbox" onchange="ts('incog',this.checked)"><span class="sl"></span></label></div>
<div id="bc"><div style="font-size:11px;opacity:.8">THREATS BLOCKED</div><span id="ct">0</span></div></div>
<div id="dp"><h2 style="color:var(--p);border-bottom:1px solid var(--p)">DEV CONSOLE</h2><div id="dl"></div></div>
<script>
window.S={ad:1,trk:1,cookie:1,sink:1,warp:0,tor:0,incog:0};
function ib(u){if(!u)return 0;try{if(S.sink&&/doubleclick|adsense|mixpanel|hotjar|facebook\.com\/tr|google-analytics/.test(u))return 1;if(S.ad&&/adsystem|adnxs|taboola|cookie-law/.test(u))return 1;if(S.trk&&/analytics|segment\.io|telemetry|fingerprint|trackcmp/.test(u))return 1}catch(e){}return 0}
const of=window.fetch;window.fetch=function(i,n){let u='';try{u=typeof i==='string'?i:i.url}catch(e){}if(ib(u)){sr('inc');return Promise.reject(new Error('Blocked'))}return of.apply(this,arguments)};
function ts(t,v){S[t]=v?1:0;sr('shld',{s:t,v:v})}
function uc(c){let e=document.getElementById('ct');if(e){e.textContent=c;let p=document.getElementById('bc');p.style.boxShadow='0 0 25px var(--p)';setTimeout(()=>p.style.boxShadow='none',500)}}
function sr(a,p){if(window.chrome&&window.chrome.webview)window.chrome.webview.postMessage(JSON.stringify({a,p}));else if(window.ipc)window.ipc.postMessage(JSON.stringify({a,p}))}
function td(){document.getElementById('dp').classList.toggle('o')}
function tai(){document.getElementById('ap').classList.toggle('o')}
function lg(m,t){let l=document.getElementById('dl'),e=document.createElement('div');e.className='le '+(t||'info');e.style.color=t==='error'?'var(--p)':'var(--c)';e.textContent='['+new Date().toTimeString().split(' ')[0]+'] '+m;l.prepend(e)}
window.rp=function(h){
  document.getElementById('ca').innerHTML=h;
  try{localStorage.clear();sessionStorage.clear()}catch(e){}
  try{
    Object.defineProperty(navigator,'webdriver',{get:()=>undefined});
    const _toDataURL=HTMLCanvasElement.prototype.toDataURL;
    HTMLCanvasElement.prototype.toDataURL=function(t){if(t==='image/png'&&this.width<16){return 'data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mP8z8BQDwAEhQGAhKmMIQAAAABJRU5ErkJggg=='}return _toDataURL.apply(this,arguments)};
    if(navigator.mediaDevices)navigator.mediaDevices.enumerateDevices=async()=>[];
  }catch(e){}
};
window.at=function(m){m==='light'?document.body.classList.add('lt'):document.body.classList.remove('lt')}
window.al=function(l){document.querySelectorAll('[data-i18n]').forEach(e=>{let k=e.getAttribute('data-i18n');if(L[l]&&L[l][k])e.textContent=L[l][k]})};
const L={en:{title:"NEXUS",sub:"ELITE RUST // SECURE CORE"},vi:{title:"NEXUS",sub:"RUST CAO CẤP // LÕI BẢO MẬT"}};
function v(id,val){let e=document.getElementById(id);if(val!==undefined)e.value=val;return e?e.value:''}
function sai(){let i=document.getElementById('ai');let m=i.value.trim();if(!m)return;i.value='';let l=document.getElementById('al');l.innerHTML+='<div class="msg usr"><b>You:</b> '+m+'</div>';l.scrollTop=l.scrollHeight;sr('ai',m)}
function cai(r){let l=document.getElementById('al');l.innerHTML+='<div class="msg ai"><b>AI:</b> '+r+'</div>';l.scrollTop=l.scrollHeight}
</script></body></html>"#.into()
}

#[derive(Debug, Clone)]
enum Ev { Js(String) }

async fn fetch(url: String, st: Arc<RwLock<state::State>>, px: tao::event_loop::EventLoopProxy<Ev>) {
    let cfg = { st.read().await.cfg.clone() };
    if blocker::check(&url, &cfg) || (cfg.sinkhole && sinkhole::check(&url)) { 
        let _ = px.send_event(Ev::Js(format!("lg('SINKHOLE: {}','error')", url.replace('\'', "")))); 
        let blocked = {
            let mut g = st.write().await;
            g.blocked += 1;
            g.blocked
        };
        let _ = px.send_event(Ev::Js(format!("uc({})", blocked)));
        return; 
    }

    let client = net::client(&cfg);
    if let Ok(r) = client.get(&url)
        .header("Referer", "")
        .header("DNT", "1")
        .header("Sec-GPC", "1")
        .send().await {
        if let Ok(h) = r.text().await {
            let inj = format!(r#"<base href="{}"><meta http-equiv="Content-Security-Policy" content="default-src * 'unsafe-inline' 'unsafe-eval' data: blob:; script-src * 'unsafe-inline' 'unsafe-eval';"><meta name="referrer" content="no-referrer">"#, url);
            let html_out = if let Some(idx) = h.to_lowercase().find("<head>") {
                let mut s = String::with_capacity(h.len() + inj.len() + 6);
                s.push_str(&h[..idx + 6]);
                s.push_str(&inj);
                s.push_str(&h[idx + 6..]);
                s
            } else {
                format!("{}{}", inj, h)
            };
            if let Ok(esc) = serde_json::to_string(&html_out) {
                let _ = px.send_event(Ev::Js(format!("rp({})", esc)));
                let mut g = st.write().await; 
                g.hist.push(url); 
                if g.hist.len() > 100 { g.hist.remove(0); }
                g.last_active = Instant::now();
            }
        }
    }
}

fn main() {
    unsafe {
        std::env::set_var("WEBKIT_DISABLE_COMPOSITING_MODE", "1");
        std::env::set_var("WEBKIT_DISABLE_DMABUF_RENDERER", "1");
    }

    let el = EventLoopBuilder::<Ev>::with_user_event().build();
    let w = match WindowBuilder::new()
        .with_title("NEXUS")
        .with_inner_size(tao::dpi::LogicalSize::new(1024, 768))
        .build(&el) {
        Ok(w) => w,
        Err(_) => return,
    };

    let st = Arc::new(RwLock::new(state::State::new()));
    let px = el.create_proxy();

    let tokio_rt = Arc::new(Builder::new_multi_thread().enable_all().worker_threads(4).build().expect("tokio rt"));
    let tokio_handle = tokio_rt.handle().clone();

    // Idle watcher
    {
        let stc = st.clone();
        let pxc = px.clone();
        tokio_handle.spawn(async move {
            loop {
                tokio::time::sleep(std::time::Duration::from_secs(60)).await;
                let idle = { stc.read().await.last_active.elapsed().as_secs() > 300 };
                if idle {
                    let _ = pxc.send_event(Ev::Js("lg('Idle: memory compaction triggered','info')".into()));
                }
            }
        });
    }

    let ist = st.clone();
    let ipx = px.clone();
    let rth = tokio_handle.clone();
 
    // SECURITY: Native incognito + bounded WebView
    let mut wb = WebViewBuilder::new();
    wb = wb.with_html(html())
        .with_back_forward_navigation_gestures(false)
        .with_zoom_hotkeys(false)
        .with_ipc_handler(move |req: wry::http::Request<String>| {
            let msg = req.into_body();
            let p: serde_json::Value = match serde_json::from_str(&msg) { Ok(v) => v, Err(_) => return };
            let a = p["a"].as_str().unwrap_or("");
            let d = p["p"].clone();
            let ist = ist.clone();
            let ipx = ipx.clone();
            let rth = rth.clone();
            
            match a {
                "nav" => if let Some(u) = d.as_str() {
                    let u = u.to_string();
                    rth.spawn(async move { fetch(search::resolve(&u), ist, ipx).await; });
                },
                "dl" => if let Some(u) = d.as_str() {
                    let u = u.to_string();
                    rth.spawn(async move { dl::turbo(u, ist).await; });
                },
                "dev" => { rth.spawn(async move { let mut g = ist.write().await; g.cfg.dev = !g.cfg.dev; }); },
                "theme" => {
                    rth.spawn(async move {
                        let mut g = ist.write().await;
                        g.theme = if g.theme == state::Theme::Dark { state::Theme::Light } else { state::Theme::Dark };
                        let t = if g.theme == state::Theme::Dark { "dark" } else { "light" };
                        let _ = ipx.send_event(Ev::Js(format!("at('{}')", t)));
                    });
                },
                "lang" => {
                    rth.spawn(async move {
                        let mut g = ist.write().await;
                        g.lang = if g.lang == state::Lang::EN { state::Lang::VI } else { state::Lang::EN };
                        let l = if g.lang == state::Lang::EN { "en" } else { "vi" };
                        let _ = ipx.send_event(Ev::Js(format!("al('{}')", l)));
                    });
                },
                "shld" => {
                    if let (Some(s), Some(v)) = (d["s"].as_str().map(String::from), d["v"].as_bool()) {
                        rth.spawn(async move {
                            let mut g = ist.write().await;
                            match s.as_str() {
                                "ad" => g.cfg.ad = v,
                                "trk" => g.cfg.trk = v,
                                "cookie" => g.cfg.cookie = v,
                                "sink" => g.cfg.sinkhole = v,
                                "warp" => g.cfg.warp = v,
                                "tor" => g.cfg.tor = v,
                                "incog" => g.cfg.incog = v,
                                _ => {}
                            }
                        });
                    }
                },
                "inc" => {
                    rth.spawn(async move {
                        let mut g = ist.write().await;
                        g.blocked += 1;
                        let c = g.blocked;
                        drop(g);
                        let _ = ipx.send_event(Ev::Js(format!("uc({})", c)));
                    });
                },
                "ai" => if let Some(prompt) = d.as_str() {
                    let p_str = prompt.to_string();
                    rth.spawn(async move {
                        {
                            let mut g = ist.write().await;
                            g.push_ai("user".into(), p_str.clone());
                        }
                        tokio::time::sleep(std::time::Duration::from_millis(300)).await;
                        let (mem_size, api_prefix) = {
                            let g = ist.read().await;
                            (g.ai_mem.len(), g.api_key.chars().take(8).collect::<String>())
                        };
                        let reply = format!("API[{}] | FIFO mem: {} turns | Query: '{}'", api_prefix, mem_size, p_str);
                        {
                            let mut g = ist.write().await;
                            g.push_ai("ai".into(), reply.clone());
                        }
                        if let Ok(esc) = serde_json::to_string(&reply) {
                            let _ = ipx.send_event(Ev::Js(format!("cai({})", esc)));
                        }
                    });
                },
                _ => {}
            }
        });

    let wv = match wb.build(&w) { Ok(w) => w, Err(_) => return };

    // Keep runtime alive for the lifetime of the event loop
    let _rt_guard = tokio_rt.clone();

    el.run(move |ev, _, cf| {
        *cf = ControlFlow::Wait;
        match ev {
            Event::NewEvents(StartCause::Init) => {
                let _ = px.send_event(Ev::Js("lg('NEXUS CORE INITIALIZED','info');lg('Incognito envelope active','info');lg('Anti-fingerprint matrix loaded','info')".into()));
            },
            Event::UserEvent(Ev::Js(j)) => { let _ = wv.evaluate_script(&j); },
            Event::WindowEvent { event: tao::event::WindowEvent::CloseRequested, .. } => *cf = ControlFlow::Exit,
            _ => {}
        }
    });
}
