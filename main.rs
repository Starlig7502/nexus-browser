// ============================================================================
// NEXUS BROWSER - ELITE RUST EDITION (4GB DDR3 LOW-RAM OPTIMIZED)
// Single-file architecture: src/main.rs
// ============================================================================

use std::sync::{Arc, RwLock, Mutex};
use std::time::Instant;
use tao::{event::{Event, StartCause}, event_loop::{ControlFlow, EventLoopBuilder}, window::WindowBuilder};
use wry::WebViewBuilder;

pub mod state {
    use super::*;
    #[derive(Clone, Debug, PartialEq)] pub enum Theme { Dark, Light }
    #[derive(Clone, Debug, Default)] pub struct Cfg {
        pub proxy: bool, pub proxy_url: String, pub tor: bool, pub dev: bool,
        pub ad: bool, pub trk: bool, pub sinkhole: bool,
    }
    #[derive(Clone, Debug)]
    pub struct State {
        pub hist: Vec<String>, pub cfg: Cfg, pub theme: Theme, pub blocked: u64,
        pub last_active: Instant,
    }
    impl State {
        pub fn new() -> Self { Self {
            hist: vec![], cfg: Cfg { proxy_url: "socks5://127.0.0.1:1080".into(), ad: true, trk: true, sinkhole: true, ..Default::default() },
            theme: Theme::Dark, blocked: 0, last_active: Instant::now(),
        }}
    }
}

mod blocker {
    use super::state::Cfg;
    pub fn check(url: &str, c: &Cfg) -> bool {
        (c.ad && (url.contains("adsystem") || url.contains("adnxs") || url.contains("taboola"))) ||
        (c.trk && (url.contains("analytics") || url.contains("segment.io")))
    }
}

mod sinkhole {
    pub fn check(url: &str) -> bool {
        url.contains("doubleclick") || url.contains("adsense") || url.contains("mixpanel") || 
        url.contains("hotjar") || url.contains("facebook.com/tr")
    }
}

mod net {
    use super::state::Cfg;
    pub fn client(c: &Cfg) -> reqwest::Client {
        let mut b = reqwest::Client::builder().user_agent("Nexus/1.0").pool_idle_timeout(None);
        if c.tor { if let Ok(p) = reqwest::Proxy::all("socks5h://127.0.0.1:9050") { b = b.proxy(p); } }
        else if c.proxy { if let Ok(p) = reqwest::Proxy::all(&c.proxy_url) { b = b.proxy(p); } }
        b.build().unwrap_or_else(|_| reqwest::Client::new())
    }
}

mod dl {
    use super::{net, state::State};
    use std::sync::Arc;
    use tokio::{sync::Semaphore, task, io::{AsyncWriteExt, AsyncSeekExt, SeekFrom}};
    use futures_util::StreamExt;

    pub async fn turbo(url: String, st: Arc<RwLock<State>>) {
        let cfg = st.read().map(|g| g.cfg.clone()).unwrap_or_default();
        let c = net::client(&cfg);
        let len = c.head(&url).send().await.ok().and_then(|r| r.content_length()).unwrap_or(0);
        if len == 0 { return; }
        
        let sem = Arc::new(Semaphore::new(32));
        let chunk = len / 32;
        let f_name = url.split('/').last().unwrap_or("nxdl.bin").to_string();
        
        // FIX: Use OpenOptions for safe async file creation without blocking set_len issues
        let file = match tokio::fs::OpenOptions::new()
            .write(true).create(true).truncate(true).open(&f_name).await {
            Ok(f) => Arc::new(tokio::sync::Mutex::new(f)),
            Err(_) => return,
        };

        let mut set = task::JoinSet::new();
        for i in 0usize..32 {
            let (c, u, p, fl) = (c.clone(), url.clone(), sem.clone(), file.clone());
            let s = i as u64 * chunk;
            let e = if i == 31 { len - 1 } else { s + chunk - 1 };
            set.spawn(async move {
                let _p = p.acquire().await;
                if let Ok(r) = c.get(&u).header("Range", format!("bytes={}-{}", s, e)).send().await {
                    let mut st = r.bytes_stream();
                    let mut off = s;
                    while let Some(Ok(b)) = st.next().await {
                        let mut g = fl.lock().await;
                        let _ = g.seek(SeekFrom::Start(off)).await;
                        let _ = g.write_all(&b).await;
                        off += b.len() as u64;
                    }
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
#u{flex:1;background:var(--in);border:1px solid var(--bd);color:var(--t);padding:8px;font-family:monospace}
#ca{flex:1;overflow:auto;position:relative;background:var(--bg)}
#st{display:flex;flex-direction:column;align-items:center;justify-content:center;height:100%}
#st h1{font-size:4rem;text-shadow:0 0 20px var(--c);color:var(--c)}
#st .s{color:var(--p);text-shadow:0 0 10px var(--p);margin-bottom:40px}
#ss{width:60%;max-width:600px;padding:15px;font-size:18px;background:color-mix(in srgb,var(--c) 10%,transparent);border:2px solid var(--c);color:var(--t);text-align:center}
#dp{position:fixed;right:-400px;top:0;width:400px;height:100vh;background:var(--pan);border-left:2px solid var(--p);z-index:99;padding:20px;overflow-y:auto;transition:.3s}
#dp.o{right:0}.le{font-size:12px;margin-bottom:5px}
#pp{position:fixed;right:0;top:60px;width:240px;background:var(--pan);border-left:2px solid var(--c);border-bottom:2px solid var(--c);border-bottom-left-radius:15px;padding:20px;z-index:9;box-shadow:-5px 5px 20px rgba(0,240,255,.15);display:flex;flex-direction:column;gap:15px}
.stg{display:flex;justify-content:space-between;align-items:center;font-size:13px;text-transform:uppercase;border-bottom:1px dashed rgba(255,255,255,.1);padding-bottom:8px}
.sw{position:relative;display:inline-block;width:40px;height:20px}.sw input{opacity:0;width:0;height:0}
.sl{position:absolute;cursor:pointer;top:0;left:0;right:0;bottom:0;background:#333;transition:.4s;border-radius:20px}
.sl:before{position:absolute;content:"";height:14px;width:14px;left:3px;bottom:3px;background:#fff;transition:.4s;border-radius:50%}
input:checked+.sl{background:var(--c);box-shadow:0 0 10px var(--c)}input:checked+.sl:before{transform:translateX(20px)}
#bc{margin-top:10px;padding:15px;background:rgba(255,0,127,.1);border:1px solid var(--p);border-radius:8px;text-align:center;transition:.3s}
#ct{font-size:2rem;color:var(--p);font-weight:700;text-shadow:0 0 10px var(--p)}
.pt{color:var(--c);border-bottom:1px solid var(--c);padding-bottom:5px;margin:0;font-size:16px}
</style></head><body>
<div id="sh"><div id="tb">
<button class="b" onclick="sr('back')">⟵</button><button class="b" onclick="sr('fwd')">⟶</button><button class="b" onclick="sr('ref')">⟳</button>
<input type="text" id="u" placeholder="Search..." onkeydown="if(event.key==='Enter')sr('nav',this.value)">
<button class="b p" onclick="sr('dl',v('u'))">⬇ TURBO</button>
<button class="b" onclick="td()">⚙ DEV</button>
<button class="b" onclick="sr('theme')">🌓</button>
</div><div id="ca"><div id="st"><h1>NEXUS</h1><div class="s">ELITE RUST // 4GB OPTIMIZED</div><input type="text" id="ss" placeholder="Query..." onkeydown="if(event.key==='Enter'){v('u',this.value);sr('nav',this.value)}"></div></div></div>
<div id="pp"><h3 class="pt">🛡 SHIELD</h3>
<div class="stg"><label>Ads</label><label class="sw"><input type="checkbox" checked onchange="ts('ad',this.checked)"><span class="sl"></span></label></div>
<div class="stg"><label>Trackers</label><label class="sw"><input type="checkbox" checked onchange="ts('trk',this.checked)"><span class="sl"></span></label></div>
<div class="stg"><label>Sinkhole</label><label class="sw"><input type="checkbox" checked onchange="ts('sink',this.checked)"><span class="sl"></span></label></div>
<div id="bc"><div style="font-size:12px;text-transform:uppercase;opacity:.8">Blocked</div><span id="ct">0</span></div></div>
<div id="dp"><h2 style="color:var(--p);border-bottom:1px solid var(--p)">DEV</h2><div id="dl"></div></div>
<script>
window.S={ad:1,trk:1,sink:1};
function ib(u){if(!u)return 0;try{if(S.sink&&/doubleclick|adsense|mixpanel|hotjar|facebook\.com\/tr/.test(u))return 1;if(S.ad&&/adsystem|adnxs|taboola/.test(u))return 1;if(S.trk&&/analytics|segment\.io/.test(u))return 1}catch(e){}return 0}
const of=window.fetch;window.fetch=function(i,n){let u='';try{u=typeof i==='string'?i:i.url}catch(e){}if(ib(u)){sr('inc');return Promise.reject(new Error('Blocked'))}return of.apply(this,arguments)};
function ts(t,v){S[t]=v?1:0;sr('shld',{s:t,v:v})}
function uc(c){let e=document.getElementById('ct');if(e){e.textContent=c;let p=document.getElementById('bc');p.style.boxShadow='0 0 25px var(--p)';setTimeout(()=>p.style.boxShadow='none',500)}}
function sr(a,p){if(window.chrome&&window.chrome.webview)window.chrome.webview.postMessage(JSON.stringify({a,p}));else if(window.ipc)window.ipc.postMessage(JSON.stringify({a,p}))}
function td(){document.getElementById('dp').classList.toggle('o')}
function lg(m,t){let l=document.getElementById('dl'),e=document.createElement('div');e.className='le '+(t||'info');e.textContent='['+new Date().toTimeString().split(' ')[0]+'] '+m;l.prepend(e)}
window.rp=function(h){document.getElementById('ca').innerHTML=h;try{localStorage.clear();sessionStorage.clear()}catch(e){}};
window.at=function(m){m==='light'?document.body.classList.add('lt'):document.body.classList.remove('lt')}
function v(id,val){let e=document.getElementById(id);if(val!==undefined)e.value=val;return e.value}
</script></body></html>"#.into()
}

#[derive(Debug, Clone)]
enum Ev { Js(String) }

async fn fetch(url: String, st: Arc<RwLock<state::State>>, px: tao::event_loop::EventLoopProxy<Ev>) {
    let cfg = st.read().map(|g| g.cfg.clone()).unwrap_or_default();
    if blocker::check(&url, &cfg) || (cfg.sinkhole && sinkhole::check(&url)) { 
        px.send_event(Ev::Js(format!("lg('SINKHOLE: {}','error')", url))).ok(); 
        if let Ok(mut g) = st.write() { g.blocked += 1; }
        px.send_event(Ev::Js(format!("uc({})", st.read().map(|g| g.blocked).unwrap_or(0)))).ok();
        return; 
    }
    
    let client = net::client(&cfg);
    if let Ok(r) = client.get(&url).send().await {
        if let Ok(h) = r.text().await {
            let base = format!("<base href=\"{}\">", url);
            let html = if h.contains("<head>") { h.replacen("<head>", &format!("<head>{}", base), 1) } else { format!("{}{}", base, h) };
            if let Ok(esc) = serde_json::to_string(&html) {
                let payload = format!("rp({})", esc);
                px.send_event(Ev::Js(payload)).ok();
                if let Ok(mut g) = st.write() { 
                    g.hist.push(url); 
                    g.last_active = Instant::now();
                }
            }
        }
    }
}

fn main() {
    std::env::set_var("WEBKIT_DISABLE_COMPOSITING_MODE", "1");
    std::env::set_var("WEBKIT_DISABLE_DMABUF_RENDERER", "1");
    
    let el = EventLoopBuilder::new().build();
    let w = match WindowBuilder::new().with_title("NEXUS").with_inner_size(tao::dpi::LogicalSize::new(1024, 768)).build(&el) {
        Ok(w) => w, Err(_) => return,
    };
    
    let st = Arc::new(RwLock::new(state::State::new()));
    let stc = st.clone();
    let px = el.create_proxy();
    let pxc = px.clone();
    
    tokio::spawn(async move {
        loop {
            tokio::time::sleep(std::time::Duration::from_secs(60)).await;
            let idle = stc.read().map(|g| g.last_active.elapsed().as_secs() > 60).unwrap_or(false);
            if idle {
                pxc.send_event(Ev::Js("if(!document.getElementById('frozen')){document.getElementById('ca').innerHTML='<div id=frozen style=\\'position:fixed;inset:0;background:#000;color:#0ff;display:flex;align-items:center;justify-content:center;font-family:monospace;z-index:9999\\'>TAB FROZEN // RAM RECLAIMED</div>';lg('DOM EVICTED','info')}".into())).ok();
            }
        }
    });

    let mut wb = WebViewBuilder::new(&w)
        .with_html(html())
        .with_incognito(true)
        .with_back_forward_navigation_gestures(false)
        .with_zoom_hotkeys(false);
        
    let ist = st.clone(); let ipx = px.clone();
    
    wb = wb.with_ipc_handler(move |req: wry::http::Request<String>| {
        if let Ok(p) = serde_json::from_str::<serde_json::Value>(req.body()) {
            let a = p["a"].as_str().unwrap_or("");
            let d = &p["p"];
            match a {
                "nav" => if let Some(u) = d.as_str() { tokio::spawn(fetch(search::resolve(u), ist.clone(), ipx.clone())); },
                "dl" => if let Some(u) = d.as_str() { tokio::spawn(dl::turbo(u.into(), ist.clone())); },
                "dev" => { if let Ok(mut g) = ist.write() { g.cfg.dev = !g.cfg.dev; } },
                "theme" => { if let Ok(mut g) = ist.write() { g.theme = if g.theme == state::Theme::Dark { state::Theme::Light } else { state::Theme::Dark }; ipx.send_event(Ev::Js(format!("at('{}')", if g.theme == state::Theme::Light {"light"} else {"dark"}))).ok(); } },
                "shld" => if let (Some(s), Some(v)) = (d["s"].as_str(), d["v"].as_bool()) { if let Ok(mut g) = ist.write() { match s { "ad" => g.cfg.ad = v, "trk" => g.cfg.trk = v, "sink" => g.cfg.sinkhole = v, _ => {} } } },
                "inc" => { if let Ok(mut g) = ist.write() { g.blocked += 1; ipx.send_event(Ev::Js(format!("uc({})", g.blocked))).ok(); } },
                _ => {}
            }
        }
    });

    let wv = match wb.build() {
        Ok(w) => Arc::new(Mutex::new(w)), Err(_) => return,
    };
    let wvc = wv.clone();

    el.run(move |ev, _, cf| {
        *cf = ControlFlow::Wait;
        match ev {
            Event::NewEvents(StartCause::Init) => { px.send_event(Ev::Js("lg('NEXUS CORE INITIALIZED','info')".into())).ok(); },
            Event::UserEvent(Ev::Js(j)) => { if let Ok(w) = wvc.lock() { w.evaluate_script(&j).ok(); } },
            Event::WindowEvent { event: tao::event::WindowEvent::CloseRequested, .. } => *cf = ControlFlow::Exit,
            _ => {}
        }
    });
}
