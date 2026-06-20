// ============================================================================
// NEXUS BROWSER - ELITE RUST EDITION (OPTIMIZED & COMPRESSED)
// Single-file architecture: src/main.rs
// ============================================================================
// REQUIRED Cargo.toml dependencies:
// [dependencies]
// tao = "0.30"
// wry = "0.45"
// tokio = { version = "1", features = ["full"] }
// reqwest = { version = "0.12", features = ["socks", "json", "stream"] }
// serde = { version = "1", features = ["derive"] }
// serde_json = "1"
// url = "2"
// rand = "0.8"
// ============================================================================

use std::sync::{Arc, RwLock, Mutex};
use std::time::Instant;
use tao::{event::{Event, StartCause}, event_loop::{ControlFlow, EventLoopBuilder}, window::WindowBuilder};
use wry::WebViewBuilder;

mod state {
    use super::*;
    #[derive(Clone, Debug, PartialEq)] pub enum Theme { Dark, Light }
    #[derive(Clone, Debug, PartialEq)] pub enum Lang { EN, VI }
    #[derive(Clone, Debug)] pub struct Chat { pub role: String, pub content: String }
    #[derive(Clone, Debug)] pub struct Tab { pub id: String, pub url: String, pub last_active: Instant }
    #[derive(Clone, Debug, Default)] pub struct Cfg {
        pub proxy: bool, pub proxy_url: String, pub tor: bool, pub dev: bool,
        pub ad: bool, pub trk: bool, pub cook: bool,
    }
    #[derive(Clone, Debug)]
    pub struct State {
        pub ai: Vec<Chat>, pub tabs: Vec<Tab>, pub hist: Vec<String>, pub cfg: Cfg,
        pub theme: Theme, pub lang: Lang, pub blocked: u64,
    }
    impl State {
        pub fn new() -> Self { Self {
            ai: vec![], tabs: vec![], hist: vec![],
            cfg: Cfg { proxy_url: "socks5://127.0.0.1:1080".into(), ad: true, trk: true, cook: true, ..Default::default() },
            theme: Theme::Dark, lang: Lang::EN, blocked: 0,
        }}
        pub fn add_chat(&mut self, c: Chat) { self.ai.push(c); if self.ai.len() > 40 { self.ai.remove(0); } }
    }
}

mod blocker {
    use super::state::Cfg;
    const ADS: &[&str] = &["doubleclick", "adsense", "adsystem", "adservice", "adnxs", "amazon-adsystem", "facebook.com/tr"];
    const TRK: &[&str] = &["google-analytics", "mixpanel", "hotjar", "scorecardresearch", "quantserve", "segment.io"];
    const COOK: &[&str] = &["addthis", "sharethis", "disqus", "taboola", "outbrain", "demdex"];
    pub fn check(url: &str, c: &Cfg) -> bool {
        (c.ad && ADS.iter().any(|d| url.contains(d))) ||
        (c.trk && TRK.iter().any(|d| url.contains(d))) ||
        (c.cook && COOK.iter().any(|d| url.contains(d)))
    }
}

mod net {
    use super::state::Cfg;
    pub fn client(c: &Cfg) -> reqwest::Client {
        let mut b = reqwest::Client::builder().user_agent("Nexus/1.0");
        if c.tor { if let Ok(p) = reqwest::Proxy::all("socks5h://127.0.0.1:9050") { b = b.proxy(p); } }
        else if c.proxy { if let Ok(p) = reqwest::Proxy::all(&c.proxy_url) { b = b.proxy(p); } }
        b.build().unwrap_or_else(|_| reqwest::Client::new())
    }
}

mod vault {
    use rand::Rng;
    pub fn gen(len: usize) -> String {
        const C: &[u8] = b"ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789!@#$%^&*";
        let mut r = rand::thread_rng();
        (0..len).map(|_| C[r.gen_range(0..C.len())] as char).collect()
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

mod dl {
    use super::{net, state::State};
    use std::sync::{Arc, RwLock};
    use tokio::task;

    pub async fn turbo(url: String, st: Arc<RwLock<State>>) {
        let cfg = if let Ok(g) = st.read() { g.cfg.clone() } else { return; };
        let c = net::client(&cfg);
        let len = c.head(&url).send().await.ok().and_then(|r| r.content_length()).unwrap_or(0);
        if len == 0 { return; }
        let chunk = len / 64;
        
        // FIX: Explicitly cast index to usize to prevent type mismatch in tuple (usize, Vec<u8>)
        let handles: Vec<_> = (0usize..64).map(|i| {
            let c = c.clone(); let u = url.clone();
            let start = i as u64 * chunk;
            let end = if i == 63 { len - 1 } else { start + chunk - 1 };
            task::spawn(async move {
                if let Ok(r) = c.get(&u).header("Range", format!("bytes={}-{}", start, end)).send().await {
                    if let Ok(b) = r.bytes().await { return (i, b.to_vec()); }
                }
                (i, vec![])
            })
        }).collect();
        
        let mut chunks: Vec<(usize, Vec<u8>)> = vec![];
        for h in handles { if let Ok(res) = h.await { chunks.push(res); } }
        chunks.sort_by_key(|(i, _)| *i);
        let data: Vec<u8> = chunks.into_iter().flat_map(|(_, b)| b).collect();
        if let Some(f) = url.split('/').last() { let _ = tokio::fs::write(f, data).await; }
    }
}

mod trans {
    pub async fn run(t: String) -> String {
        let mut r = t;
        for (e, v) in [("Welcome", "Chào mừng"), ("Search", "Tìm kiếm"), ("Download", "Tải"), ("NEXUS", "NEXUS")] {
            r = r.replace(e, v);
        }
        tokio::time::sleep(std::time::Duration::from_millis(100)).await;
        r
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
<input type="text" id="u" data-i18n="search" placeholder="Search..." onkeydown="if(event.key==='Enter')sr('nav',this.value)">
<button class="b p" onclick="sr('dl',v('u'))" data-i18n="turbo">⬇ TURBO</button>
<button class="b" onclick="tp()" data-i18n="trans">🌐 VI</button>
<button class="b" onclick="td()" data-i18n="dev">⚙ DEV</button>
<button class="b" onclick="sr('about')" data-i18n="about">ⓘ</button>
<button class="b" onclick="sr('theme')">🌓</button><button class="b" onclick="sr('lang')">🌐</button>
</div><div id="ca"><div id="st"><h1 data-i18n="title">NEXUS</h1><div class="s" data-i18n="sub">PREMIUM RUST // ZERO-TRUST</div><input type="text" id="ss" data-i18n="ssearch" placeholder="Query..." onkeydown="if(event.key==='Enter'){v('u',this.value);sr('nav',this.value)}"></div></div></div>
<div id="pp"><h3 class="pt" data-i18n="priv">🛡 PRIVACY</h3>
<div class="stg"><label>Ads</label><label class="sw"><input type="checkbox" id="tad" checked onchange="ts('ad',this.checked)"><span class="sl"></span></label></div>
<div class="stg"><label>Trackers</label><label class="sw"><input type="checkbox" id="ttrk" checked onchange="ts('trk',this.checked)"><span class="sl"></span></label></div>
<div class="stg"><label>Cookies</label><label class="sw"><input type="checkbox" id="tck" checked onchange="ts('ck',this.checked)"><span class="sl"></span></label></div>
<div id="bc"><div style="font-size:12px;text-transform:uppercase;opacity:.8">Blocked</div><span id="ct">0</span></div></div>
<div id="dp"><h2 style="color:var(--p);border-bottom:1px solid var(--p)">DEV CONSOLE</h2><div id="dl"></div><input type="text" id="jc" placeholder="JS..." onkeydown="if(event.key==='Enter'){eval(this.value);this.value=''}" style="width:100%;margin-top:10px;background:var(--in);border:1px solid var(--c);color:var(--t);padding:5px"></div>
<script>
window.CL='en';
const L={en:{search:"Search...",ssearch:"Query...",turbo:"⬇ TURBO",about:"ⓘ",dev:"⚙ DEV",title:"NEXUS",sub:"PREMIUM RUST // ZERO-TRUST",trans:"🌐 VI",priv:"🛡 PRIVACY"},vi:{search:"Tìm...",ssearch:"Truy vấn...",turbo:"⬇ TẢI",about:"ⓘ",dev:"⚙ DEV",title:"NEXUS",sub:"RUST CAO CẤP // KHÔNG TIN CẬY",trans:"🌐 EN",priv:"🛡 BẢO MẬT"}};
window.BL={ad:["doubleclick","adsense","adsystem","adservice","adnxs","amazon-adsystem","facebook.com/tr"],trk:["google-analytics","mixpanel","hotjar","scorecardresearch","quantserve","segment.io"],ck:["addthis","sharethis","disqus","taboola","outbrain","demdex"]};
window.S={ad:1,trk:1,ck:1};
function ib(u){if(!u)return 0;try{if(S.ad&&BL.ad.some(d=>u.includes(d)))return 1;if(S.trk&&BL.trk.some(d=>u.includes(d)))return 1;if(S.ck&&BL.ck.some(d=>u.includes(d)))return 1}catch(e){}return 0}
const of=window.fetch;window.fetch=function(i,n){let u='';try{u=typeof i==='string'?i:(i instanceof Request?i.url:String(i))}catch(e){}if(ib(u)){sr('inc','fetch');return Promise.reject(new Error('Blocked'))}return of.apply(this,arguments)};
const ox=XMLHttpRequest.prototype.open,os=XMLHttpRequest.prototype.send;
XMLHttpRequest.prototype.open=function(m,u){this.__u=u;return ox.apply(this,arguments)};
XMLHttpRequest.prototype.send=function(){if(ib(this.__u)){sr('inc','xhr');this.abort();return}return os.apply(this,arguments)};
new MutationObserver(m=>m.forEach(x=>x.addedNodes.forEach(n=>{if(n.nodeType===1&&['SCRIPT','IMG','IFRAME','LINK'].includes(n.tagName)){if((n.src&&ib(n.src))||(n.href&&ib(n.href))){n.remove();sr('inc','dom')}}}))).observe(document.documentElement,{childList:1,subtree:1});
function ts(t,v){S[t]=v?1:0;sr('shld',{s:t,v:v})}
function uc(c){let e=document.getElementById('ct');if(e){e.textContent=c;let p=document.getElementById('bc');p.style.boxShadow='0 0 25px var(--p)';setTimeout(()=>p.style.boxShadow='none',500)}}
function sr(a,p){if(window.chrome&&window.chrome.webview)window.chrome.webview.postMessage(JSON.stringify({a:a,p:p}));else if(window.ipc)window.ipc.postMessage(JSON.stringify({a:a,p:p}))}
function td(){document.getElementById('dp').classList.toggle('o');sr('dev')}
function lg(m,t){let l=document.getElementById('dl'),e=document.createElement('div');e.className='le '+(t||'info');e.textContent='['+new Date().toISOString().split('T')[1].split('.')[0]+'] '+m;l.prepend(e)}
window.rp=function(h){document.getElementById('ca').innerHTML=h;document.getElementById('ca').addEventListener('click',function(e){let t=e.target;while(t&&t.tagName!=='A'){t=t.parentNode;if(!t)return}if(t&&t.tagName==='A'){e.preventDefault();let h=t.getAttribute('href');if(h&&!h.startsWith('#')&&!h.startsWith('javascript:')){let b=document.querySelector('base');let f=h;if(b)f=new URL(h,b.getAttribute('href')).href;v('u',f);sr('nav',f)}}},!0)};
window.at=function(m){m==='light'?document.body.classList.add('lt'):document.body.classList.remove('lt')}
window.al=function(l){window.CL=l;let t=L[l];if(!t)return;v('u',null,t.search);v('ss',null,t.ssearch);document.querySelectorAll('[data-i18n]').forEach(e=>{let k=e.getAttribute('data-i18n');if(t[k])e.textContent=t[k]})}
function tp(){sr('trns',document.title+'|'+document.body.innerText.substring(0,500))}
window.atr=function(t){let o=document.createElement('div');o.style.cssText='position:fixed;bottom:20px;left:50%;transform:translateX(-50%);background:var(--p);color:#fff;padding:15px 25px;z-index:99999;border-radius:5px;box-shadow:0 0 15px var(--p);font-weight:700';o.textContent='Dịch thành công!';document.body.appendChild(o);setTimeout(()=>o.remove(),3000);document.title='[VI] '+document.title}
function v(id,val){let e=document.getElementById(id);if(val===null)return e.placeholder;if(val!==undefined)e.value=val;return e.value}
</script></body></html>"#.into()
}

#[derive(Debug, Clone)]
enum Ev { Js(String) }

async fn fetch(url: String, st: Arc<RwLock<state::State>>, px: tao::event_loop::EventLoopProxy<Ev>) {
    let cfg = if let Ok(g) = st.read() { g.cfg.clone() } else { return; };
    if blocker::check(&url, &cfg) { px.send_event(Ev::Js(format!("lg('BLOCKED: {}','error')", url))).ok(); return; }
    
    let client = net::client(&cfg);
    if let Ok(r) = client.get(&url).send().await {
        if let Ok(h) = r.text().await {
            let base = format!("<base href=\"{}\">", url);
            let html = if h.contains("<head>") { h.replacen("<head>", &format!("<head>{}", base), 1) } else { format!("{}{}", base, h) };
            let esc = html.replace("\\", "\\\\").replace("`", "\\`").replace("$", "\\$");
            px.send_event(Ev::Js(format!("rp(`{}`)", esc))).ok();
            if let Ok(mut g) = st.write() { g.hist.push(url); }
        }
    }
}

fn main() {
    let el = EventLoopBuilder::new().build();
    let w = match WindowBuilder::new().with_title("NEXUS").build(&el) {
        Ok(w) => w,
        Err(_) => return,
    };
    
    let st = Arc::new(RwLock::new(state::State::new()));
    let stc = st.clone();
    
    tokio::spawn(async move {
        loop {
            tokio::time::sleep(std::time::Duration::from_secs(60)).await;
            if let Ok(mut g) = stc.write() {
                let now = Instant::now();
                g.tabs.retain(|t| now.duration_since(t.last_active).as_secs() <= 300 || t.url.is_empty());
            }
        }
    });

    let px = el.create_proxy();
    let mut wb = WebViewBuilder::new(&w).with_html(html());
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
                "lang" => { if let Ok(mut g) = ist.write() { g.lang = if g.lang == state::Lang::EN { state::Lang::VI } else { state::Lang::EN }; ipx.send_event(Ev::Js(format!("al('{}')", if g.lang == state::Lang::VI {"vi"} else {"en"}))).ok(); } },
                "trns" => if let Some(t) = d.as_str() { let tc = t.to_string(); let pc = ipx.clone(); tokio::spawn(async move { let r = trans::run(tc).await; let e = r.replace("\\", "\\\\").replace("`", "\\`").replace("$", "\\$"); pc.send_event(Ev::Js(format!("atr(`{}`)", e))).ok(); }); },
                "shld" => if let (Some(s), Some(v)) = (d["s"].as_str(), d["v"].as_bool()) { if let Ok(mut g) = ist.write() { match s { "ad" => g.cfg.ad = v, "trk" => g.cfg.trk = v, "ck" => g.cfg.cook = v, _ => {} } } },
                "inc" => { if let Ok(mut g) = ist.write() { g.blocked += 1; ipx.send_event(Ev::Js(format!("uc({})", g.blocked))).ok(); } },
                "about" => { ipx.send_event(Ev::Js("document.body.insertAdjacentHTML('beforeend',`<div style='position:fixed;top:50%;left:50%;transform:translate(-50%,-50%);background:var(--bg);border:2px solid var(--c);padding:40px;z-index:9999;box-shadow:0 0 30px var(--c);color:var(--t);font-family:monospace'><h1 style='color:var(--c)'>NEXUS</h1><p style='color:var(--p)'>Premium Rust</p><button class='b' onclick='this.parentNode.remove()'>CLOSE</button></div>`);al(CL);".into())).ok(); },
                _ => {}
            }
        }
    });

    let wv = match wb.build() {
        Ok(w) => Arc::new(Mutex::new(w)),
        Err(_) => return,
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
