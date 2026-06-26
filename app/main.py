from sqlalchemy import text
import base64 as _b64, json as _json, os as _os
from fastapi import FastAPI, Depends, HTTPException, Header
from fastapi.responses import HTMLResponse, JSONResponse, Response
from sqlalchemy.orm import Session

from app.database import engine, Base, get_db, ping_db
from app import models, schema, crud
from app.auth import criar_usuario, fazer_login, get_usuario_atual, exigir_admin

Base.metadata.create_all(bind=engine)
app = FastAPI(title="WMS — WALZE WMS", version="4.0")


def _load_icon(name):
    try:
        p = _os.path.join(_os.path.dirname(__file__), '..', 'pwa', name)
        if _os.path.exists(p):
            return open(p, 'rb').read()
    except Exception:
        pass
    return _b64.b64decode(
        "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNk"
        "YPhfDwAChwGA60e6kgAAAABJRU5ErkJggg==")

_ICON_192 = _load_icon('icon-192.png')
_ICON_512 = _load_icon('icon-512.png')

_MANIFEST = {
    "name": "WMS WALZE", "short_name": "WALZE WMS",
    "description": "Sistema WMS", "start_url": "/app",
    "display": "standalone", "background_color": "#0a0e14",
    "theme_color": "#22c55e", "orientation": "portrait-primary",
    "scope": "/", "lang": "pt-BR",
    "icons": [
        {"src": "/icon-192.png", "sizes": "192x192", "type": "image/png", "purpose": "any maskable"},
        {"src": "/icon-512.png", "sizes": "512x512", "type": "image/png", "purpose": "any maskable"}
    ],
    "shortcuts": [
        {"name": "Conferente",  "url": "/conferente-v2"},
        {"name": "Operação",    "url": "/operacao"},
        {"name": "Volumes",     "url": "/gerenciar-volumes"},
        {"name": "Histórico",   "url": "/historico"},
        {"name": "Endereços",   "url": "/enderecos-page"},
    ]
}

_SW = ("const CACHE='wms-v4';"
       "const PAGES=['/app','/login','/operacao','/conferente-v2',"
       "'/gerenciar-volumes','/historico','/enderecos-page','/perfil','/manifest.json'];"
       "self.addEventListener('install',e=>{e.waitUntil(caches.open(CACHE)"
       ".then(c=>c.addAll(PAGES)).then(()=>self.skipWaiting()));});"
       "self.addEventListener('activate',e=>{e.waitUntil(caches.keys()"
       ".then(ks=>Promise.all(ks.filter(k=>k!==CACHE).map(k=>caches.delete(k))))"
       ".then(()=>self.clients.claim()));});"
       "self.addEventListener('fetch',e=>{"
       "const isApi=['/pedidos','/paletes','/enderecos','/pedidos-volume','/auth','/historico-api','/usuarios','/dashboard-api']"
       ".some(p=>e.request.url.includes(p));"
       "if(isApi){e.respondWith(fetch(e.request).catch(()=>new Response("
       "JSON.stringify({detail:'Sem conexão.'}),{status:503,"
       "headers:{'Content-Type':'application/json'}})));return;}"
       "e.respondWith(fetch(e.request).then(r=>{if(r.ok){"
       "const c=r.clone();caches.open(CACHE).then(ch=>ch.put(e.request,c));}return r;})"
       ".catch(()=>caches.match(e.request)));});")

# ── Design System: Sidebar dark, cards de status, mapa de armazém ──
_SHARED = """
<meta charset="UTF-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<link rel="manifest" href="/manifest.json">
<meta name="theme-color" content="#22c55e">
<meta name="apple-mobile-web-app-capable" content="yes">
<meta name="apple-mobile-web-app-status-bar-style" content="black-translucent">
<meta name="apple-mobile-web-app-title" content="WALZE WMS">
<link rel="apple-touch-icon" href="/icon-192.png">
<link rel="preconnect" href="https://fonts.googleapis.com">
<link href="https://fonts.googleapis.com/css2?family=IBM+Plex+Mono:wght@400;500;600&family=Inter:wght@400;500;600;700&display=swap" rel="stylesheet">
<script>
if("serviceWorker"in navigator)window.addEventListener("load",()=>navigator.serviceWorker.register("/service-worker.js"));
function getToken(){return localStorage.getItem('wms_token')||'';}
function getUser(){return localStorage.getItem('wms_user')||'';}
function getPapel(){return localStorage.getItem('wms_papel')||'OPERADOR';}
function isAdmin(){return getPapel()==='ADMIN';}
function authHeaders(){return{'Content-Type':'application/json','Authorization':'Bearer '+getToken()};}
</script>
<style>
:root{
  --bg:#0a0e14;--s1:#0f1420;--s2:#161b28;--s3:#1d2333;
  --br:#222838;--br2:#323a4f;
  --green:#22c55e;--gdim:#22c55e1c;--gtxt:#4ade80;
  --blue:#3b82f6;--bdim:#3b82f61c;--btxt:#60a5fa;
  --red:#ef4444;--rdim:#ef44441c;--rtxt:#f87171;
  --amber:#f59e0b;--adim:#f59e0b1c;--atxt:#fbbf24;
  --purple:#a855f7;--pdim:#a855f71c;--ptxt:#c084fc;
  --txt:#f4f6fb;--txt2:#9aa3b8;--txt3:#5b6478;
  --font:'Inter',sans-serif;--mono:'IBM Plex Mono',monospace;
  --r:8px;--rl:12px;--sbw:230px;
}
*{box-sizing:border-box;margin:0;padding:0;}
html,body{background:var(--bg);color:var(--txt);font-family:var(--font);min-height:100vh;}
a{color:inherit;text-decoration:none;}
::-webkit-scrollbar{width:8px;height:8px;}
::-webkit-scrollbar-thumb{background:var(--br2);border-radius:4px;}

/* ── SIDEBAR ── */
.shell{display:flex;min-height:100vh;}
.sidebar{width:var(--sbw);background:var(--s1);border-right:1px solid var(--br);
  display:flex;flex-direction:column;flex-shrink:0;position:sticky;top:0;height:100vh;
  overflow-y:auto;z-index:50;}
.sb-brand{display:flex;align-items:center;gap:10px;padding:18px 18px 16px;}
.sb-logo{width:30px;height:30px;border-radius:8px;background:var(--green);
  display:flex;align-items:center;justify-content:center;font-weight:700;
  font-size:15px;color:#04130a;flex-shrink:0;font-family:var(--mono);}
.sb-name{font-size:14px;font-weight:600;color:var(--txt);}
.sb-nav{flex:1;padding:6px 12px;display:flex;flex-direction:column;gap:2px;}
.sb-link{display:flex;align-items:center;gap:11px;padding:9px 12px;border-radius:8px;
  font-size:13px;color:var(--txt2);cursor:pointer;transition:.12s;font-weight:500;}
.sb-link .ic{width:17px;text-align:center;font-size:14px;flex-shrink:0;}
.sb-link:hover{color:var(--txt);background:var(--s2);}
.sb-link.on{color:var(--gtxt);background:var(--gdim);}
.sb-foot{padding:14px 16px;border-top:1px solid var(--br);}
.sb-logout{display:flex;align-items:center;gap:8px;font-size:12px;color:var(--txt3);
  cursor:pointer;padding:7px 4px;transition:.12s;}
.sb-logout:hover{color:var(--rtxt);}

/* ── TOP BAR ── */
.main{flex:1;min-width:0;display:flex;flex-direction:column;}
.topbar{display:flex;align-items:center;justify-content:space-between;
  padding:16px 24px;border-bottom:1px solid var(--br);background:var(--bg);
  position:sticky;top:0;z-index:40;}
.tb-title{display:flex;align-items:center;gap:11px;}
.tb-icon{width:34px;height:34px;border-radius:9px;display:flex;align-items:center;
  justify-content:center;font-size:16px;flex-shrink:0;}
.tb-h1{font-size:16px;font-weight:600;color:var(--txt);}
.tb-sub{font-size:11.5px;color:var(--txt3);margin-top:1px;}
.tb-right{display:flex;align-items:center;gap:14px;}
.tb-user{display:flex;align-items:center;gap:9px;cursor:pointer;}
.tb-av{width:30px;height:30px;border-radius:50%;background:var(--bdim);
  border:1px solid var(--blue);display:flex;align-items:center;justify-content:center;
  font-size:10px;font-weight:600;color:var(--btxt);flex-shrink:0;overflow:hidden;}
.tb-av img{width:100%;height:100%;object-fit:cover;}
.tb-uname{font-size:12.5px;font-weight:600;color:var(--txt);}
.tb-urole{font-size:10px;color:var(--txt3);}

.content{padding:22px 24px;flex:1;}

/* ── CARD ── */
.card{background:var(--s1);border:1px solid var(--br);border-radius:var(--rl);
  padding:20px;margin-bottom:14px;}
.ct{font-size:10px;letter-spacing:.08em;text-transform:uppercase;
  color:var(--txt3);margin-bottom:12px;font-weight:600;}

/* ── FORM ── */
.f{margin-bottom:12px;}
.f label{display:block;font-size:10.5px;letter-spacing:.04em;text-transform:uppercase;
  color:var(--txt3);margin-bottom:6px;font-weight:600;}
.fi{width:100%;padding:11px 13px;background:var(--bg);color:var(--txt);
  border:1px solid var(--br);border-radius:var(--r);
  font-family:var(--mono);font-size:14px;transition:.12s;outline:none;}
.fi:focus{border-color:var(--green);box-shadow:0 0 0 3px var(--gdim);}
.fi::placeholder{color:var(--txt3);}
.fi:disabled{opacity:.5;cursor:not-allowed;}
.fi.ok{border-color:var(--green);}
.fi.err{border-color:var(--red);}
.g2{display:grid;grid-template-columns:1fr 1fr;gap:12px;}
.g3{display:grid;grid-template-columns:repeat(3,1fr);gap:10px;}

/* ── BOTÕES ── */
.btn{display:inline-flex;align-items:center;justify-content:center;gap:6px;
  padding:9px 16px;border:none;border-radius:var(--r);
  font-family:var(--font);font-size:13px;font-weight:600;
  cursor:pointer;transition:.12s;white-space:nowrap;}
.btn:disabled{opacity:.35;cursor:not-allowed;}
.btn:active:not(:disabled){transform:scale(.97);}
.bg{background:var(--green);color:#04130a;}
.bg:hover:not(:disabled){filter:brightness(1.1);}
.bb{background:var(--blue);color:#fff;}
.bb:hover:not(:disabled){filter:brightness(1.1);}
.ba{background:var(--amber);color:#1a1200;}
.ba:hover:not(:disabled){filter:brightness(1.1);}
.bgh{background:var(--s2);color:var(--txt);border:1px solid var(--br);}
.bgh:hover:not(:disabled){border-color:var(--br2);}
.bd{background:var(--rdim);color:var(--rtxt);border:1px solid var(--rdim);}
.bd:hover:not(:disabled){background:var(--red);color:#fff;}
.brow{display:flex;gap:8px;flex-wrap:wrap;}
.bfull{width:100%;}

/* ── OUTPUT ── */
.term{background:var(--bg);border:1px solid var(--br);border-radius:var(--rl);
  padding:16px;font-family:var(--mono);font-size:13px;color:var(--gtxt);
  white-space:pre-wrap;min-height:90px;line-height:1.7;position:relative;}
.term::before{content:'OUTPUT';position:absolute;top:7px;right:10px;
  font-size:9px;color:var(--txt3);letter-spacing:.1em;}

.sb-status{min-height:24px;display:flex;align-items:center;gap:6px;
  font-size:12px;padding:3px 0;}
.sb-status.ok{color:var(--gtxt);}.sb-status.err{color:var(--rtxt);}
.sb-status.warn{color:var(--atxt);}.sb-status.info{color:var(--txt3);}
.dot{width:5px;height:5px;border-radius:50%;background:currentColor;flex-shrink:0;}

.chips{display:flex;flex-wrap:wrap;gap:6px;margin-top:8px;}
.chip{padding:3px 10px;background:var(--s2);border:1px solid var(--br);
  border-radius:20px;font-family:var(--mono);font-size:11px;color:var(--txt3);
  cursor:pointer;transition:.12s;}
.chip:hover{border-color:var(--green);color:var(--gtxt);}

.sw{position:relative;}
.sw input{width:100%;padding:14px 14px 14px 40px;font-size:16px;
  font-family:var(--mono);background:var(--s1);color:var(--txt);
  border:1px solid var(--br);border-radius:var(--rl);outline:none;transition:.12s;}
.sw input:focus{border-color:var(--green);box-shadow:0 0 0 3px var(--gdim);}
.sw .si{position:absolute;left:14px;top:50%;transform:translateY(-50%);
  font-size:15px;color:var(--txt3);pointer-events:none;}

.tw{overflow-x:auto;}
table{width:100%;border-collapse:collapse;font-size:12px;}
th{text-align:left;padding:9px 10px;font-size:9.5px;letter-spacing:.06em;
  text-transform:uppercase;color:var(--txt3);border-bottom:1px solid var(--br);font-weight:600;}
td{padding:9px 10px;border-bottom:1px solid var(--br);color:var(--txt);}
tr:last-child td{border-bottom:none;}
tr:hover td{background:var(--s2);}

.bk{display:inline-block;padding:3px 8px;border-radius:5px;
  font-family:var(--mono);font-size:10px;font-weight:600;}
.bk-blue{background:var(--bdim);color:var(--btxt);}
.bk-green{background:var(--gdim);color:var(--gtxt);}
.bk-red{background:var(--rdim);color:var(--rtxt);}
.bk-amber{background:var(--adim);color:var(--atxt);}
.bk-purple{background:var(--pdim);color:var(--ptxt);}

.end-livre{background:var(--gdim);color:var(--gtxt);border:1px solid var(--green);}
.end-parcial{background:var(--adim);color:var(--atxt);border:1px solid var(--amber);}
.end-ocupado{background:var(--rdim);color:var(--rtxt);border:1px solid var(--red);}
.end-bloqueado{background:var(--s2);color:var(--txt3);border:1px solid var(--br2);}

input[type=checkbox]{width:14px;height:14px;accent-color:var(--green);cursor:pointer;}

.stats{display:flex;flex-wrap:wrap;gap:10px;margin-bottom:18px;}
.stat{flex:1;min-width:88px;background:var(--s1);border:1px solid var(--br);
  border-radius:var(--r);padding:11px 13px;}
.sl{font-size:9.5px;text-transform:uppercase;letter-spacing:.06em;color:var(--txt3);margin-bottom:4px;}
.sv{font-family:var(--mono);font-size:19px;font-weight:600;color:var(--gtxt);}
.sv.red{color:var(--rtxt);}

.divider{height:1px;background:var(--br);margin:18px 0;}

#toast{position:fixed;bottom:18px;right:18px;background:var(--s1);
  border:1px solid var(--br);border-radius:var(--rl);padding:10px 14px;
  font-size:12px;z-index:999;transform:translateY(60px);opacity:0;
  transition:.2s cubic-bezier(.4,0,.2,1);pointer-events:none;max-width:280px;}
#toast.show{transform:translateY(0);opacity:1;}
#toast.ok{border-color:var(--green);color:var(--gtxt);}
#toast.err{border-color:var(--red);color:var(--rtxt);}

.modal-bg{display:none;position:fixed;inset:0;background:#000c;z-index:200;
  align-items:center;justify-content:center;}
.modal-bg.open{display:flex;}
.modal{background:var(--s1);border:1px solid var(--br);border-radius:var(--rl);
  padding:24px;width:100%;max-width:440px;margin:16px;}
.modal h3{font-size:15px;font-weight:600;color:var(--txt);margin-bottom:16px;}

/* ── DASHBOARD: cards de métrica com ícone de tendência ── */
.metric-card{background:var(--s1);border:1px solid var(--br);border-radius:var(--rl);
  padding:16px 18px;display:flex;align-items:center;justify-content:space-between;}
.metric-card .num{font-family:var(--mono);font-size:26px;font-weight:700;line-height:1;}
.metric-card .lbl{font-size:11.5px;color:var(--txt2);margin-top:4px;font-weight:500;}
.metric-card .trend{font-size:17px;}

/* ── MAPA DE ARMAZÉM ── */
.map-toolbar{display:flex;gap:10px;align-items:center;margin-bottom:16px;flex-wrap:wrap;}
.map-select{padding:9px 13px;background:var(--s1);color:var(--txt);
  border:1px solid var(--br);border-radius:var(--r);font-size:13px;outline:none;
  font-family:var(--font);cursor:pointer;}
.map-grid-label{font-family:var(--mono);font-size:12px;color:var(--txt2);
  font-weight:600;margin-bottom:12px;letter-spacing:.04em;}
.map-wrap{overflow-x:auto;padding-bottom:6px;}
.map-grid{display:inline-block;}
.map-row{display:flex;gap:6px;margin-bottom:6px;align-items:center;}
.map-rowlabel{width:24px;height:46px;display:flex;align-items:center;justify-content:center;
  background:var(--s2);border-radius:6px;font-size:11px;font-weight:700;color:var(--txt2);
  flex-shrink:0;}
.map-cell{width:70px;height:46px;border-radius:6px;display:flex;align-items:center;
  justify-content:center;font-family:var(--mono);font-size:10.5px;font-weight:600;
  cursor:pointer;transition:.12s;flex-shrink:0;border:1.5px solid transparent;}
.map-cell:hover{transform:scale(1.05);}
.map-cell.empty{background:var(--s2);border:1px dashed var(--br);color:transparent;cursor:default;}
.map-cell.empty:hover{transform:none;}
.map-cell.livre{background:#16331f;color:var(--gtxt);border-color:var(--green);}
.map-cell.parcial{background:#332a10;color:var(--atxt);border-color:var(--amber);}
.map-cell.ocupado{background:#3a1414;color:var(--rtxt);border-color:var(--red);}
.map-cell.bloqueado{background:var(--s2);color:var(--txt3);border-color:var(--br2);}
.map-cell.selected{outline:2px solid var(--txt);outline-offset:1px;}
.map-colheader{width:70px;text-align:center;font-size:11px;color:var(--txt3);
  font-family:var(--mono);flex-shrink:0;}
.map-legend{display:flex;gap:20px;flex-wrap:wrap;margin-top:18px;padding-top:16px;
  border-top:1px solid var(--br);}
.map-legend-item{display:flex;align-items:center;gap:8px;}
.map-legend-dot{width:13px;height:13px;border-radius:3px;flex-shrink:0;}
.map-legend-txt{font-size:11.5px;}
.map-legend-txt b{display:block;font-size:12px;color:var(--txt);}
.map-legend-txt span{color:var(--txt3);font-size:10.5px;}

/* ── PAINEL DE DETALHES (lateral direita) ── */
.detail-panel{background:var(--s1);border:1px solid var(--br);border-radius:var(--rl);
  padding:18px;position:sticky;top:80px;}
.detail-head{display:flex;align-items:center;justify-content:space-between;margin-bottom:14px;}
.detail-close{cursor:pointer;color:var(--txt3);font-size:16px;background:none;border:none;}
.detail-close:hover{color:var(--txt);}
.detail-code{font-family:var(--mono);font-size:19px;font-weight:700;color:var(--txt);margin:8px 0 14px;}
.detail-row{display:flex;justify-content:space-between;padding:8px 0;
  border-bottom:1px solid var(--br);font-size:12.5px;}
.detail-row:last-child{border-bottom:none;}
.detail-row span:first-child{color:var(--txt3);}
.detail-row span:last-child{color:var(--txt);font-weight:600;font-family:var(--mono);}

/* ── PERFIL ── */
.profile-photo{width:88px;height:88px;border-radius:50%;background:var(--s2);
  border:2px solid var(--br2);display:flex;align-items:center;justify-content:center;
  font-size:30px;font-weight:700;color:var(--btxt);overflow:hidden;flex-shrink:0;}
.profile-photo img{width:100%;height:100%;object-fit:cover;}
.cpf-toggle{display:inline-flex;align-items:center;gap:6px;cursor:pointer;
  font-size:11px;color:var(--btxt);}

/* ── LOGIN ── */
.login-wrap{display:flex;align-items:center;justify-content:center;min-height:100vh;padding:20px;
  background:radial-gradient(circle at 20% 20%, #122218 0%, var(--bg) 55%);}
.login-box{background:var(--s1);border:1px solid var(--br);border-radius:var(--rl);
  padding:36px;width:100%;max-width:380px;}
.login-logo{display:flex;align-items:center;gap:10px;margin-bottom:6px;}
.login-logo .sb-logo{width:34px;height:34px;font-size:17px;}
.login-logo span{font-size:18px;font-weight:700;color:var(--txt);}
.login-sub{color:var(--txt3);font-size:12px;margin-bottom:26px;}
.err-msg{color:var(--rtxt);font-size:12px;margin-top:8px;min-height:18px;}

@media (max-width: 900px){

  .sidebar{
    position:fixed;
    left:-100%;
    top:0;
    height:100vh;
    transition:.2s;
    box-shadow:0 0 40px #000a;
    z-index:9999;
  }

  .sidebar.open{
    left:0;
  }

  #menuBtn{
    display:block !important;
  }

  .content{
    padding:16px;
  }

  .topbar{
    padding:12px 16px;
    display:flex;
    align-items:center;
    gap:10px;
  }
}
</style>
"""

_SIDEBAR_TPL = """<div class="sidebar" id="sidebar">
  <div class="sb-brand">
    <div class="sb-logo">W</div>
    <div class="sb-name">WALZE WMS</div>
  </div>
  <div class="sb-nav">
    <a class="sb-link{a}" href="/app"><span class="ic">⬜</span>Dashboard</a>
    <a class="sb-link{b}" href="/conferente-v2"><span class="ic">📦</span>Conferente</a>
    <a class="sb-link{c}" href="/operacao"><span class="ic">🔍</span>Operação</a>
    <a class="sb-link{d}" href="/gerenciar-volumes"><span class="ic">🗂️</span>Volumes</a>
    <a class="sb-link{e}" href="/enderecos-page"><span class="ic">🏷️</span>Endereços</a>
    <a class="sb-link{f}" href="/historico"><span class="ic">📋</span>Histórico</a>
    <a class="sb-link{g}" href="/perfil"><span class="ic">👤</span>Perfil</a>
    <a class="sb-link{h} admin-only" href="/usuarios" style="display:none;"><span class="ic">👥</span>Usuários</a>
  </div>
  <div class="sb-foot">
    <div class="sb-logout" onclick="sair()"><span class="ic">↩</span>Sair</div>
  </div>
</div>"""

_TOPBAR_TPL = """<div class="topbar">

<button id="menuBtn" onclick="toggleMenu()" style="
display:none;
background:none;
border:none;
font-size:24px;
color:white;
cursor:pointer;
margin-right:10px;
">
☰
</button>

  <button class="menu-btn" onclick="toggleSidebar()">☰</button>

  <div class="tb-title">
    <div class="tb-icon" style="background:{iconbg};">{icon}</div>
    <div>
      <div class="tb-h1">{title}</div>
      <div class="tb-sub">{subtitle}</div>
    </div>
  </div>
  <div class="tb-right">
    <span style="font-family:var(--mono);font-size:11px;color:var(--txt3);" id="clk"></span>
    <a href="/perfil" class="tb-user">
      <div class="tb-av" id="navAv"></div>
      <div>
        <div class="tb-uname" id="navUser"></div>
        <div class="tb-urole" id="navRole"></div>
      </div>
    </a>
  </div>
</div>
<div id="toast"></div>
<script>
(function(){
  if(!localStorage.getItem('wms_token')&&window.location.pathname!=='/login'){
    window.location.href='/login';return;
  }
  document.addEventListener('DOMContentLoaded',function(){
    var u=localStorage.getItem('wms_user')||'';
    var papel=localStorage.getItem('wms_papel')||'OPERADOR';
    var foto=localStorage.getItem('wms_foto')||'';
    var elU=document.getElementById('navUser');if(elU)elU.textContent=u;
    var elR=document.getElementById('navRole');if(elR)elR.textContent=papel==='ADMIN'?'Administrador':'Operador';
    var av=document.getElementById('navAv');
    if(av){
      if(foto){av.innerHTML='<img src="'+foto+'">';}
      else{var p=u.trim().split(' ');
        av.textContent=p.length>=2?(p[0][0]+p[p.length-1][0]).toUpperCase():u.substring(0,2).toUpperCase();}
    }
    if(papel==='ADMIN'){
      document.querySelectorAll('.admin-only').forEach(function(el){el.style.display='flex';});
    }
  });
  function tick(){var d=new Date();var el=document.getElementById('clk');
    if(el)el.textContent=d.toLocaleDateString('pt-BR')+' '+d.toLocaleTimeString('pt-BR');}
  setInterval(tick,1000);tick();
  window.toast=function(msg,t){var el=document.getElementById('toast');
    el.textContent=msg;el.className='show '+(t||'ok');
    clearTimeout(el._t);el._t=setTimeout(()=>el.className='',3000);};
 window.toggleMenu=function(){
  const sb=document.getElementById('sidebar');

  if(sb){
    sb.classList.toggle('open');
  }
};
   window.sair=function(){localStorage.removeItem('wms_token');
    localStorage.removeItem('wms_user');localStorage.removeItem('wms_papel');
    localStorage.removeItem('wms_foto');window.location.href='/login';};
})();
</script>"""


def sidebar(active: str) -> str:
    m = {'home':'a','conf':'b','oper':'c','vol':'d','end':'e','hist':'f','perfil':'g','users':'h'}
    t = _SIDEBAR_TPL
    for k, v in m.items():
        t = t.replace('{'+v+'}', ' on' if active == k else '')
    return t


def topbar(icon: str, iconbg: str, title: str, subtitle: str) -> str:
    return (_TOPBAR_TPL
            .replace('{icon}', icon)
            .replace('{iconbg}', iconbg)
            .replace('{title}', title)
            .replace('{subtitle}', subtitle))


def shell_open(active: str, icon: str, iconbg: str, title: str, subtitle: str) -> str:
    """Abre a estrutura: sidebar + main + topbar + content. Lembrar de fechar com shell_close()."""
    return (f'<div class="shell">{sidebar(active)}<div class="main">'
            f'{topbar(icon, iconbg, title, subtitle)}<div class="content">')


def shell_close() -> str:
    return '</div></div></div>'

# ══════════════════════════════════════════════════════════════════
#  PWA
# ══════════════════════════════════════════════════════════════════
@app.get("/manifest.json")
def pwa_manifest():
    return Response(content=_json.dumps(_MANIFEST, ensure_ascii=False),
                    media_type="application/manifest+json")

@app.get("/service-worker.js")
def pwa_sw():
    return Response(content=_SW, media_type="application/javascript")

@app.get("/icon-192.png")
def pwa_icon_192():
    return Response(content=_ICON_192, media_type="image/png")

@app.get("/icon-512.png")
def pwa_icon_512():
    return Response(content=_ICON_512, media_type="image/png")


# ══════════════════════════════════════════════════════════════════
#  AUTH API
# ══════════════════════════════════════════════════════════════════
@app.post("/auth/login", response_model=schema.LoginResposta)
def api_login(dados: schema.LoginInput, db: Session = Depends(get_db)):
    return fazer_login(db, dados.login, dados.senha)

@app.post("/auth/criar-usuario", response_model=schema.UsuarioResposta)
def api_criar_usuario(dados: schema.UsuarioCriar, db: Session = Depends(get_db),
                      authorization: str = Header(default="")):
    """Primeira conta pode ser criada livremente; depois disso exige admin."""
    tem_usuarios = db.query(models.Usuario).first() is not None
    if tem_usuarios:
        u = get_usuario_atual(db, authorization)
        exigir_admin(u)
    return criar_usuario(db, dados.nome, dados.login, dados.senha, dados.papel,
                         dados.email, dados.telefone, dados.cpf)

@app.get("/auth/me")
def api_me(db: Session = Depends(get_db), authorization: str = Header(default="")):
    u = get_usuario_atual(db, authorization)
    return crud.perfil_para_resposta(u, revelar_cpf=False)


# ══════════════════════════════════════════════════════════════════
#  PERFIL
# ══════════════════════════════════════════════════════════════════
@app.get("/perfil-api", response_model=schema.PerfilResposta)
def perfil_proprio(db: Session = Depends(get_db), authorization: str = Header(default="")):
    u = get_usuario_atual(db, authorization)
    return crud.perfil_para_resposta(u, revelar_cpf=False)

@app.get("/perfil-api/cpf-completo")
def perfil_cpf_completo(db: Session = Depends(get_db), authorization: str = Header(default="")):
    """Só o próprio usuário pode revelar o próprio CPF completo."""
    u = get_usuario_atual(db, authorization)
    return {"cpf": u.cpf or ""}

@app.patch("/perfil-api", response_model=schema.PerfilResposta)
def atualizar_perfil_proprio(dados: schema.PerfilAtualizar, db: Session = Depends(get_db),
                             authorization: str = Header(default="")):
    u = get_usuario_atual(db, authorization)
    u = crud.atualizar_perfil(db, u, dados)
    return crud.perfil_para_resposta(u, revelar_cpf=False)


# ══════════════════════════════════════════════════════════════════
#  USUÁRIOS (admin)
# ══════════════════════════════════════════════════════════════════
@app.get("/usuarios-api")
def listar_usuarios_admin(db: Session = Depends(get_db), authorization: str = Header(default="")):
    u = get_usuario_atual(db, authorization)
    exigir_admin(u)
    return [crud.perfil_para_resposta(x, revelar_cpf=False) for x in crud.listar_usuarios(db)]

@app.patch("/usuarios-api/{usuario_id}/ativo")
def alternar_ativo(usuario_id: int, ativo: bool, db: Session = Depends(get_db),
                   authorization: str = Header(default="")):
    u = get_usuario_atual(db, authorization)
    exigir_admin(u)
    alvo = crud.alternar_ativo_usuario(db, usuario_id, ativo)
    return crud.perfil_para_resposta(alvo, revelar_cpf=False)


# ══════════════════════════════════════════════════════════════════
#  DASHBOARD
# ══════════════════════════════════════════════════════════════════
@app.get("/dashboard-api")
def dashboard_api(db: Session = Depends(get_db)):
    return crud.metricas_dashboard(db)


# ══════════════════════════════════════════════════════════════════
#  API ROTAS — armazém, paletes, pedidos
# ══════════════════════════════════════════════════════════════════
@app.get("/")
def root(): return {"status": "ok", "app": "WMS WALZE WMS v4"}

@app.get("/health")
def health():
    ok = ping_db()
    return JSONResponse(status_code=200 if ok else 503,
                        content={"status": "ok" if ok else "db_error", "db": ok})

@app.get("/enderecos", response_model=list[schema.EnderecoResposta])
def listar_enderecos(db: Session = Depends(get_db)):
    return crud.listar_enderecos(db)

@app.get("/enderecos-status")
def listar_enderecos_status(db: Session = Depends(get_db)):
    return [{"codigo": e.codigo, "status": e.status_ocupacao or "LIVRE"}
            for e in crud.listar_enderecos(db)]

@app.patch("/enderecos/{codigo}/status", response_model=schema.EnderecoResposta)
def atualizar_status(codigo: str, dados: schema.EnderecoStatusUpdate,
                     db: Session = Depends(get_db),
                     authorization: str = Header(default="")):
    u = get_usuario_atual(db, authorization)
    return crud.atualizar_status_endereco(db, codigo, dados.status_ocupacao, u)

@app.get("/enderecos/{codigo}/pedidos")
def pedidos_endereco_api(codigo: str, db: Session = Depends(get_db)):
    return crud.pedidos_no_endereco(db, codigo)

@app.get("/caixas", response_model=list[schema.CaixaResposta])
def listar_caixas(db: Session = Depends(get_db)):
    return crud.listar_caixas(db)

@app.post("/paletes/manual", response_model=schema.PaleteResposta)
def criar_palete_manual(dados: schema.PaleteManualCriar, db: Session = Depends(get_db),
                        authorization: str = Header(default="")):
    u = get_usuario_atual(db, authorization)
    return crud.criar_ou_usar_palete_manual(db, dados.codigo_palete, dados.codigo_endereco, u)

@app.post("/paletes/auto", response_model=schema.PaleteResposta)
def criar_palete_auto(palete: schema.PaleteCriar, db: Session = Depends(get_db)):
    return crud.criar_palete_auto(db, palete)

@app.get("/paletes", response_model=list[schema.PaleteResposta])
def listar_paletes(db: Session = Depends(get_db)):
    return crud.listar_paletes(db)

@app.delete("/pedidos-volume/duplicados")
def limpar_dup(db: Session = Depends(get_db)):
    return crud.limpar_pedidos_duplicados(db)

@app.post("/pedidos-volume/deletar-varios")
def deletar_varios(dados: schema.DeletarVolumes, db: Session = Depends(get_db),
                   authorization: str = Header(default="")):
    u = get_usuario_atual(db, authorization)
    return crud.deletar_varios_pedidos_volume(db, dados.ids, u)

@app.post("/pedidos-volume/transferir")
def transferir(dados: schema.TransferirVolumes, db: Session = Depends(get_db),
               authorization: str = Header(default="")):
    u = get_usuario_atual(db, authorization)
    return crud.transferir_volumes(db, dados, u)

@app.get("/pedidos-volume")
def listar_volumes(db: Session = Depends(get_db)):
    return crud.listar_pedidos_volume(db)

@app.post("/pedidos-volume", response_model=schema.PedidoVolumeResposta)
def criar_volume(pedido: schema.PedidoVolumeCriar, db: Session = Depends(get_db),
                 authorization: str = Header(default="")):
    u = get_usuario_atual(db, authorization)
    return crud.criar_pedido_volume(db, pedido, u)

@app.delete("/pedidos-volume/{volume_id}")
def deletar_volume(volume_id: int, db: Session = Depends(get_db),
                   authorization: str = Header(default="")):
    u = get_usuario_atual(db, authorization)
    return crud.deletar_pedido_volume(db, volume_id, u)

@app.get("/enderecos/{codigo}/detalhes")
def detalhes_endereco(codigo: str, db: Session = Depends(get_db)):
    return crud.detalhes_endereco(db, codigo)

@app.get("/pedidos/{numero_pedido}")
def buscar_pedido(numero_pedido: str, db: Session = Depends(get_db)):
    return crud.buscar_pedido(db, numero_pedido)

@app.get("/historico-api")
def historico_api(db: Session = Depends(get_db), authorization: str = Header(default="")):
    get_usuario_atual(db, authorization)
    return [{
        "id": h.id, "usuario_nome": h.usuario_nome or "—", "acao": h.acao,
        "numero_pedido": h.numero_pedido or "—", "volume_atual": h.volume_atual,
        "volume_total": h.volume_total, "palete_codigo": h.palete_codigo or "—",
        "endereco_de": h.endereco_de or "—", "endereco_para": h.endereco_para or "—",
        "detalhe_extra": h.detalhe_extra or "",
        "criado_em": h.criado_em.strftime("%d/%m/%Y %H:%M:%S") if h.criado_em else "—",
    } for h in crud.listar_historico(db)]

# ══════════════════════════════════════════════════════════════════
#  PÁGINA: LOGIN
# ══════════════════════════════════════════════════════════════════
@app.get("/login", response_class=HTMLResponse)
def pg_login():
    return f"""<!DOCTYPE html><html lang="pt-BR"><head>{_SHARED}<title>WMS · Login</title>
</head><body>
<div class="login-wrap">
<div class="login-box">
  <div class="login-logo"><div class="sb-logo">W</div><span>WALZE WMS</span></div>
  <div class="login-sub">Sistema de Gerenciamento de Armazém</div>
  <div class="f"><label>Usuário</label>
    <input class="fi" id="lg" placeholder="seu.login" autofocus
      onkeydown="if(event.key==='Enter')document.getElementById('pw').focus()">
  </div>
  <div class="f"><label>Senha</label>
    <input class="fi" id="pw" type="password" placeholder="••••••••"
      onkeydown="if(event.key==='Enter')entrar()">
  </div>
  <button class="btn bg bfull" style="margin-top:6px;" onclick="entrar()">Entrar</button>
  <div class="err-msg" id="err"></div>
</div></div>
<script>
async function entrar(){{
  var l=document.getElementById('lg').value.trim();
  var s=document.getElementById('pw').value;
  var e=document.getElementById('err');
  if(!l||!s){{e.textContent='Preencha usuário e senha.';return;}}
  e.textContent='';
  try{{
    var r=await fetch('/auth/login',{{method:'POST',
      headers:{{'Content-Type':'application/json'}},
      body:JSON.stringify({{login:l,senha:s}})}});
    var d=await r.json();
    if(d.detail){{e.textContent=d.detail;return;}}
    localStorage.setItem('wms_token',d.token);
    localStorage.setItem('wms_user',d.nome);
    localStorage.setItem('wms_papel',d.papel||'OPERADOR');
    window.location.href='/app';
  }}catch(ex){{e.textContent='Erro de conexão.';}}
}}
if(localStorage.getItem('wms_token'))window.location.href='/app';
</script></body></html>"""

# ══════════════════════════════════════════════════════════════════
#  PÁGINA: DASHBOARD — mapa do armazém em tempo real
# ══════════════════════════════════════════════════════════════════
@app.get("/app", response_class=HTMLResponse)
def pg_dashboard():
    return ("""<!DOCTYPE html><html lang="pt-BR"><head>""" + _SHARED +
            """<title>WMS · Dashboard</title></head><body>""" +
            shell_open('home', '🗺️', 'var(--gdim)', 'Mapa do Armazém', 'Visão geral dos endereços e sua ocupação') +
            r"""
  <div class="map-toolbar">
    <select class="map-select" id="selRua" onchange="renderMapa()"></select>
    <select class="map-select" id="selNivel" onchange="renderMapa()"></select>
    <div class="sw" style="flex:1;min-width:200px;">
      <span class="si">⌕</span>
      <input id="buscaEnd" placeholder="Buscar endereço..." style="padding:9px 13px 9px 38px;font-size:13px;"
        oninput="renderMapa()">
    </div>
    <select class="map-select" id="selStatus" onchange="renderMapa()">
      <option value="">Todos os status</option>
      <option value="LIVRE">Livre</option>
      <option value="PARCIAL">Parcial</option>
      <option value="OCUPADO">Ocupado</option>
      <option value="BLOQUEADO">Bloqueado</option>
    </select>
    <button class="btn bg" onclick="carregarTudo()">↺ Atualizar</button>
  </div>

  <div style="display:grid;grid-template-columns:repeat(4,1fr);gap:12px;margin-bottom:18px;">
    <div class="metric-card"><div><div class="num" id="m-ocupados" style="color:var(--rtxt);">—</div>
      <div class="lbl">Ocupados</div></div><div class="trend">🔴</div></div>
    <div class="metric-card"><div><div class="num" id="m-parciais" style="color:var(--atxt);">—</div>
      <div class="lbl">Parciais</div></div><div class="trend">🟡</div></div>
    <div class="metric-card"><div><div class="num" id="m-livres" style="color:var(--gtxt);">—</div>
      <div class="lbl">Livres</div></div><div class="trend">🟢</div></div>
    <div class="metric-card"><div><div class="num" id="m-total" style="color:var(--txt);">—</div>
      <div class="lbl">Total Endereços</div></div><div class="trend">📋</div></div>
  </div>

  <div style="display:grid;grid-template-columns:1fr 320px;gap:14px;align-items:start;">
    <div class="card" style="margin-bottom:0;">
      <div class="map-grid-label" id="mapaLabel">RUA — NÍVEL</div>
      <div class="map-wrap">
        <div class="map-grid" id="mapaGrid"></div>
      </div>
      <div class="map-legend">
        <div class="map-legend-item"><div class="map-legend-dot" style="background:var(--green);"></div>
          <div class="map-legend-txt"><b>Livre</b><span>Disponível para uso</span></div></div>
        <div class="map-legend-item"><div class="map-legend-dot" style="background:var(--amber);"></div>
          <div class="map-legend-txt"><b>Parcial</b><span>Parcialmente ocupado</span></div></div>
        <div class="map-legend-item"><div class="map-legend-dot" style="background:var(--red);"></div>
          <div class="map-legend-txt"><b>Ocupado</b><span>Totalmente ocupado</span></div></div>
        <div class="map-legend-item"><div class="map-legend-dot" style="background:var(--br2);"></div>
          <div class="map-legend-txt"><b>Bloqueado</b><span>Não disponível</span></div></div>
      </div>
    </div>

    <div id="painelVazio" class="card" style="text-align:center;color:var(--txt3);font-size:13px;padding:40px 18px;">
      Clique em um endereço<br>para ver os detalhes
    </div>
    <div class="detail-panel" id="painelDetalhe" style="display:none;">
      <div class="detail-head">
        <span class="bk" id="dStatusBadge">—</span>
        <button class="detail-close" onclick="fecharPainel()">✕</button>
      </div>
      <div class="detail-code" id="dCodigo">—</div>
      <div class="detail-row"><span>Rua</span><span id="dRua">—</span></div>
      <div class="detail-row"><span>Nível</span><span id="dNivel">—</span></div>
      <div class="detail-row"><span>Posição</span><span id="dPosicao">—</span></div>
      <div class="detail-row"><span>Status</span><span id="dStatus">—</span></div>
      <div class="detail-row"><span>Capacidade</span><span id="dCapacidade">—</span></div>
      <div class="detail-row"><span>Operador</span><span id="dOperador">—</span></div>

      <div class="divider"></div>
      <div class="ct" style="display:flex;align-items:center;justify-content:space-between;">
        <span>Pedidos no endereço</span>
        <span id="dQtdPedidos" style="color:var(--gtxt);">—</span>
      </div>
      <div id="dPedidosLista" style="display:flex;flex-direction:column;gap:8px;margin-top:6px;"></div>

      <div class="divider"></div>
      <div class="brow" style="flex-direction:column;">
        <button class="btn bgh bfull" onclick="window.location.href='/historico'">📋 Ver histórico deste endereço</button>
      </div>
    </div>
  </div>

<script>
var TODOS_ENDERECOS=[];
var enderecoSelecionado=null;
var pollTimer=null;

function corClasse(s){
  if(s==='LIVRE')return'livre';
  if(s==='PARCIAL')return'parcial';
  if(s==='OCUPADO')return'ocupado';
  if(s==='BLOQUEADO')return'bloqueado';
  return'livre';
}
function corBadge(s){
  if(s==='LIVRE')return'bk-green';
  if(s==='PARCIAL')return'bk-amber';
  if(s==='OCUPADO')return'bk-red';
  if(s==='BLOQUEADO')return'bk-blue';
  return'bk-green';
}

async function carregarTudo(){
  try{
    var resE=await fetch('/enderecos');
    var resD=await fetch('/dashboard-api');
    TODOS_ENDERECOS=await resE.json();
    var dash=await resD.json();
    document.getElementById('m-ocupados').textContent=dash.ocupados;
    document.getElementById('m-parciais').textContent=dash.parciais;
    document.getElementById('m-livres').textContent=dash.livres;
    document.getElementById('m-total').textContent=dash.total;
    montarFiltros();
    renderMapa();
  }catch(e){}
}

function montarFiltros(){
  var ruas=[...new Set(TODOS_ENDERECOS.map(function(e){return e.rua;}))].sort();
  var selRua=document.getElementById('selRua');
  var ruaAtual=selRua.value;
  selRua.innerHTML=ruas.map(function(r){return '<option value="'+r+'">Rua '+r+'</option>';}).join('');
  if(ruas.indexOf(ruaAtual)!==-1)selRua.value=ruaAtual;

  var niveis=[...new Set(TODOS_ENDERECOS.filter(function(e){return e.rua===selRua.value;}).map(function(e){return e.predio;}))].sort();
  var selNivel=document.getElementById('selNivel');
  var nivelAtual=selNivel.value;
  selNivel.innerHTML=niveis.map(function(n){return '<option value="'+n+'">Nível '+n+'</option>';}).join('');
  if(niveis.indexOf(nivelAtual)!==-1)selNivel.value=nivelAtual;
}

function renderMapa(){
  var rua=document.getElementById('selRua').value;
  var nivel=document.getElementById('selNivel').value;
  var busca=document.getElementById('buscaEnd').value.trim().toUpperCase();
  var statusFiltro=document.getElementById('selStatus').value;

  document.getElementById('mapaLabel').textContent='RUA '+rua+' — NÍVEL '+nivel;

  var doNivel=TODOS_ENDERECOS.filter(function(e){return e.rua===rua&&e.predio===nivel;});
  doNivel.sort(function(a,b){
    var na=parseInt(a.andar)||0, nb=parseInt(b.andar)||0;
    return na-nb;
  });

  var frentes=[...new Set(doNivel.map(function(e){return e.frente||'A';}))].sort();
  var posicoes=[...new Set(doNivel.map(function(e){return parseInt(e.andar)||0;}))].sort(function(a,b){return a-b;});
  if(!posicoes.length){
    document.getElementById('mapaGrid').innerHTML='<p style="color:var(--txt3);padding:20px;">Nenhum endereço nesta seleção.</p>';
    return;
  }
  var minPos=posicoes[0], maxPos=posicoes[posicoes.length-1];
  var todasPos=[];
  for(var p=minPos;p<=maxPos;p++)todasPos.push(p);

  var html='<div class="map-row" style="margin-left:30px;">';
  todasPos.forEach(function(p){html+='<div class="map-colheader">'+p+'</div>';});
  html+='</div>';

  frentes.forEach(function(fr){
    html+='<div class="map-row"><div class="map-rowlabel">'+fr+'</div>';
    todasPos.forEach(function(p){
      var end=doNivel.find(function(e){return (e.frente||'A')===fr&&(parseInt(e.andar)||0)===p;});
      if(!end){html+='<div class="map-cell empty">.</div>';return;}
      var st=end.status_ocupacao||'LIVRE';
      var visivel=true;
      if(busca&&end.codigo.toUpperCase().indexOf(busca)===-1)visivel=false;
      if(statusFiltro&&st!==statusFiltro)visivel=false;
      var cls='map-cell '+corClasse(st)+(visivel?'':' empty')+
        (enderecoSelecionado===end.codigo?' selected':'');
      html+="<div class='"+cls+"' onclick='selecionarEndereco(&quot;"+end.codigo+"&quot;)' title='"+end.codigo+"'>"+
        (visivel?end.codigo.replace('R',''):'')+'</div>';
    });
    html+='</div>';
  });
  document.getElementById('mapaGrid').innerHTML=html;
}

async function selecionarEndereco(codigo){
  enderecoSelecionado=codigo;
  renderMapa();
  var end=TODOS_ENDERECOS.find(function(e){return e.codigo===codigo;});
  if(!end)return;

  document.getElementById('painelVazio').style.display='none';
  document.getElementById('painelDetalhe').style.display='block';

  var st=end.status_ocupacao||'LIVRE';
  var badge=document.getElementById('dStatusBadge');
  badge.className='bk '+corBadge(st);
  badge.textContent=st;

  document.getElementById('dCodigo').textContent=end.codigo;
  document.getElementById('dRua').textContent=end.rua;
  document.getElementById('dNivel').textContent=end.predio;
  document.getElementById('dPosicao').textContent=end.andar+(end.frente?(' '+end.frente):'');
  document.getElementById('dStatus').textContent=st;
  var pct=end.capacidade_total?Math.round((end.capacidade_usada/end.capacidade_total)*100):0;
  document.getElementById('dCapacidade').textContent=pct+'% ('+end.capacidade_usada+'/'+end.capacidade_total+' Palete)';
  document.getElementById('dOperador').textContent=getUser()||'—';

  try{
    var r=await fetch('/enderecos/'+encodeURIComponent(codigo)+'/pedidos');
    var pedidos=await r.json();
    document.getElementById('dQtdPedidos').textContent=pedidos.length+' pedido(s)';
    var lista=document.getElementById('dPedidosLista');
    if(!pedidos.length){
      lista.innerHTML='<div style="font-size:11.5px;color:var(--txt3);">Nenhum pedido neste endereço.</div>';
    }else{
      lista.innerHTML=pedidos.map(function(p){
        return '<div style="background:var(--s2);border-radius:8px;padding:10px 12px;'+
          'display:flex;justify-content:space-between;align-items:center;">'+
          '<div><div style="font-family:var(--mono);font-weight:600;font-size:13px;">'+p.pedido+'</div>'+
          '<div style="font-size:10.5px;color:var(--txt3);">Volume: '+p.qtd+'/'+p.total+'</div></div>'+
          '<span class="bk bk-blue">'+(p.qtd===p.total?'COMPLETO':'PARCIAL')+'</span></div>';
      }).join('');
    }
  }catch(e){}
}

function fecharPainel(){
  enderecoSelecionado=null;
  document.getElementById('painelDetalhe').style.display='none';
  document.getElementById('painelVazio').style.display='block';
  renderMapa();
}

carregarTudo();
pollTimer=setInterval(carregarTudo,15000);
</script>
""" + shell_close() + """
</body></html>""")

# ══════════════════════════════════════════════════════════════════
#  PÁGINA: PERFIL — dados pessoais com CPF mascarado
# ══════════════════════════════════════════════════════════════════
@app.get("/perfil", response_class=HTMLResponse)
def pg_perfil():
    return ("""<!DOCTYPE html><html lang="pt-BR"><head>""" + _SHARED +
            """<title>WMS · Perfil</title></head><body>""" +
            shell_open('perfil', '👤', 'var(--bdim)', 'Meu Perfil', 'Seus dados pessoais e de acesso') +
            r"""
  <div style="display:grid;grid-template-columns:280px 1fr;gap:16px;align-items:start;">
    <div class="card" style="text-align:center;">
      <div class="profile-photo" id="pFotoWrap" style="margin:0 auto 14px;">
        <span id="pFotoIniciais">--</span>
      </div>
      <div style="font-weight:600;font-size:15px;" id="pNomeCard">—</div>
      <div style="font-size:11.5px;color:var(--txt3);margin-top:2px;" id="pPapelCard">—</div>
      <input type="file" id="inputFoto" accept="image/*" style="display:none;" onchange="onFotoSelecionada(event)">
      <button class="btn bgh bfull" style="margin-top:14px;" onclick="document.getElementById('inputFoto').click()">
        📷 Alterar foto
      </button>
    </div>

    <div class="card">
      <div class="ct">Dados Pessoais</div>
      <div class="g2">
        <div class="f"><label>Nome completo</label>
          <input class="fi" id="pNome" placeholder="Seu nome"></div>
        <div class="f"><label>Login (não editável)</label>
          <input class="fi" id="pLogin" disabled></div>
      </div>
      <div class="g2">
        <div class="f"><label>E-mail</label>
          <input class="fi" id="pEmail" type="email" placeholder="seu@email.com"></div>
        <div class="f"><label>Telefone</label>
          <input class="fi" id="pTelefone" placeholder="(11) 99999-9999"></div>
      </div>
      <div class="f">
        <label>CPF</label>
        <div style="display:flex;gap:8px;align-items:center;">
          <input class="fi" id="pCpf" placeholder="000.000.000-00" style="flex:1;">
          <span class="cpf-toggle" onclick="alternarCpf()" id="cpfToggleBtn">👁 Mostrar completo</span>
        </div>
      </div>
      <div class="brow" style="margin-top:8px;">
        <button class="btn bg" onclick="salvarPerfil()">✓ Salvar Alterações</button>
      </div>
      <div id="pMsg" style="font-size:12px;margin-top:10px;min-height:18px;"></div>
    </div>
  </div>

<script>
var cpfRevelado=false;
var cpfCompletoCache='';

function iniciaisDe(nome){
  var p=(nome||'').trim().split(' ');
  return p.length>=2?(p[0][0]+p[p.length-1][0]).toUpperCase():(nome||'?').substring(0,2).toUpperCase();
}

async function carregarPerfil(){
  try{
    var r=await fetch('/perfil-api',{headers:authHeaders()});
    if(r.status===401){window.location.href='/login';return;}
    var d=await r.json();
    document.getElementById('pNome').value=d.nome||'';
    document.getElementById('pLogin').value=d.login||'';
    document.getElementById('pEmail').value=d.email||'';
    document.getElementById('pTelefone').value=d.telefone||'';
    document.getElementById('pCpf').value=d.cpf_mascarado||'';
    document.getElementById('pNomeCard').textContent=d.nome||'—';
    document.getElementById('pPapelCard').textContent=d.papel==='ADMIN'?'Administrador':'Operador';
    var fotoWrap=document.getElementById('pFotoWrap');
    if(d.foto_url){
      fotoWrap.innerHTML='<img src="'+d.foto_url+'">';
    }else{
      fotoWrap.innerHTML='<span>'+iniciaisDe(d.nome)+'</span>';
    }
  }catch(e){}
}

async function alternarCpf(){
  var campo=document.getElementById('pCpf');
  var btn=document.getElementById('cpfToggleBtn');
  if(!cpfRevelado){
    try{
      var r=await fetch('/perfil-api/cpf-completo',{headers:authHeaders()});
      var d=await r.json();
      cpfCompletoCache=d.cpf||'';
      campo.value=cpfCompletoCache;
      btn.textContent='🙈 Ocultar';
      cpfRevelado=true;
    }catch(e){toast('Erro ao revelar CPF','err');}
  }else{
    await carregarPerfil();
    btn.textContent='👁 Mostrar completo';
    cpfRevelado=false;
  }
}

function onFotoSelecionada(ev){
  var file=ev.target.files[0];
  if(!file)return;
  if(file.size>1500000){toast('Imagem muito grande (máx 1.5MB)','err');return;}
  var reader=new FileReader();
  reader.onload=function(e){
    document.getElementById('pFotoWrap').innerHTML='<img src="'+e.target.result+'">';
    window._novaFoto=e.target.result;
  };
  reader.readAsDataURL(file);
}

async function salvarPerfil(){
  var msg=document.getElementById('pMsg');
  var payload={
    nome: document.getElementById('pNome').value.trim(),
    email: document.getElementById('pEmail').value.trim(),
    telefone: document.getElementById('pTelefone').value.trim(),
  };
  var cpfVal=document.getElementById('pCpf').value.trim();
  if(cpfRevelado && cpfVal && cpfVal.indexOf('*')===-1){
    payload.cpf=cpfVal;
  }
  if(window._novaFoto)payload.foto_url=window._novaFoto;

  try{
    var r=await fetch('/perfil-api',{method:'PATCH',headers:authHeaders(),body:JSON.stringify(payload)});
    var d=await r.json();
    if(d.detail){msg.style.color='var(--rtxt)';msg.textContent=d.detail;return;}
    localStorage.setItem('wms_user',d.nome);
    if(d.foto_url)localStorage.setItem('wms_foto',d.foto_url);
    msg.style.color='var(--gtxt)';msg.textContent='✓ Perfil atualizado com sucesso!';
    toast('Perfil atualizado!');
    cpfRevelado=false;
    carregarPerfil();
  }catch(e){msg.style.color='var(--rtxt)';msg.textContent='Erro de conexão.';}
}

carregarPerfil();
</script>
""" + shell_close() + """
</body></html>""")

# ══════════════════════════════════════════════════════════════════
#  PÁGINA: CONFERENTE — dropdown de endereços com status colorido
# ══════════════════════════════════════════════════════════════════
@app.get("/conferente-v2", response_class=HTMLResponse)
def pg_conferente():
    return ("""<!DOCTYPE html><html lang="pt-BR"><head>""" + _SHARED +
            """<title>WMS · Conferente</title></head><body>""" +
            shell_open('conf', '📦', 'var(--gdim)', 'Montagem de Palete', 'Informe palete e endereço, depois adicione os pedidos') +
            r"""
  <div class="card">
    <div class="ct">Identificação do Palete</div>
    <div class="g2">
      <div class="f"><label>Palete</label>
        <input class="fi" id="palete" placeholder="Ex: PAL001" autofocus></div>
      <div class="f"><label>Endereço</label>
        <div style="position:relative;">
          <input class="fi" id="endereco" placeholder="Ex: R07 014 1 ou R070141"
            autocomplete="off"
            oninput="filtrarDropdown();verificarEndereco()"
            onfocus="abrirDropdown()"
            onblur="fecharDropdown();verificarEndereco()">
          <span id="end-badge" style="position:absolute;right:10px;top:50%;
            transform:translateY(-50%);font-size:10px;padding:2px 7px;
            border-radius:4px;font-family:var(--mono);font-weight:600;display:none;"></span>
          <div id="end-dropdown" style="display:none;position:absolute;top:calc(100% + 4px);
            left:0;right:0;max-height:260px;overflow-y:auto;background:var(--s1);
            border:1px solid var(--br2);border-radius:var(--r);z-index:50;
            box-shadow:0 8px 24px rgba(0,0,0,.4);"></div>
        </div>
      </div>
    </div>
    <div id="end-info" style="font-size:11px;color:var(--txt3);margin-top:-6px;margin-bottom:4px;"></div>
  </div>

  <div class="card">
    <div class="ct">Adicionar Pedido</div>
    <div class="f"><label>Número do Pedido</label>
      <input class="fi" id="pedido" placeholder="Ex: 349596"></div>
    <div class="g3">
      <div class="f"><label>Vol. Inicial</label>
        <input class="fi" id="vol_ini" type="number" min="1" placeholder="1"></div>
      <div class="f"><label>Vol. Final</label>
        <input class="fi" id="vol_fin" type="number" min="1" placeholder="6"></div>
      <div class="f"><label>Total do Pedido</label>
        <input class="fi" id="vol_tot" type="number" min="1" placeholder="10"></div>
    </div>
    <div class="brow" style="margin-top:4px;">
      <button class="btn bg" id="btnAdd" onclick="adicionar()">＋ Adicionar</button>
      <button class="btn bb" id="btnFin" onclick="finalizar()">✓ Finalizar Palete</button>
      <button class="btn bgh" onclick="resetar()">↺ Novo</button>
    </div>
  </div>

  <div class="sb-status info" id="stbar"><div class="dot"></div>Aguardando dados...</div>
  <div class="term" id="out">Pedidos adicionados aparecerão aqui...</div>

  <div style="margin-top:10px;display:flex;gap:8px;flex-wrap:wrap;">
    <div class="stat" style="flex:0 0 auto;min-width:110px;"><div class="sl">Palete</div>
      <div class="sv" id="s-pal" style="font-size:13px;">—</div></div>
    <div class="stat" style="flex:0 0 auto;min-width:110px;"><div class="sl">Endereço</div>
      <div class="sv" id="s-end" style="font-size:13px;">—</div></div>
    <div class="stat" style="flex:0 0 auto;min-width:78px;"><div class="sl">Pedidos</div>
      <div class="sv" id="s-nped">0</div></div>
    <div class="stat" style="flex:0 0 auto;min-width:78px;"><div class="sl">Volumes</div>
      <div class="sv" id="s-nvol">0</div></div>
  </div>

<script>
var resumo=[],totalVols=0;
var endStatus={};
var endLista=[];

async function carregarStatusEnderecos(){
  try{
    var r=await fetch('/enderecos-status');
    var d=await r.json();
    endLista=[];
    d.forEach(function(e){endStatus[e.codigo]=e.status;endLista.push(e.codigo);});
  }catch(e){}
}
carregarStatusEnderecos();

function corDot(st){
  if(st==='LIVRE')return'var(--green)';
  if(st==='PARCIAL')return'var(--amber)';
  if(st==='OCUPADO')return'var(--red)';
  if(st==='BLOQUEADO')return'var(--txt3)';
  return'var(--txt3)';
}
function labelStatus(st){
  if(st==='LIVRE')return'Livre';
  if(st==='PARCIAL')return'Parcial';
  if(st==='OCUPADO')return'Ocupado';
  if(st==='BLOQUEADO')return'Bloqueado';
  return'—';
}

function renderDropdown(filtro){
  var dd=document.getElementById('end-dropdown');
  var f=(filtro||'').trim().toUpperCase();
  var itens=endLista.filter(function(cod){
    return !f || cod.toUpperCase().indexOf(f)!==-1;
  });
  dd.innerHTML='';
  if(!itens.length){
    var vazio=document.createElement('div');
    vazio.style.padding='10px 12px';
    vazio.style.fontSize='12px';
    vazio.style.color='var(--txt3)';
    vazio.textContent='Nenhum endereço encontrado.';
    dd.appendChild(vazio);
    dd.style.display='block';
    return;
  }
  itens.forEach(function(cod){
    var st=endStatus[cod]||'LIVRE';
    var item=document.createElement('div');
    item.style.display='flex';
    item.style.alignItems='center';
    item.style.gap='8px';
    item.style.padding='9px 12px';
    item.style.cursor='pointer';
    item.style.fontFamily='var(--mono)';
    item.style.fontSize='13px';
    item.style.color='var(--txt)';
    item.style.borderBottom='1px solid var(--br)';
    item.style.transition='.1s';

    var dot=document.createElement('span');
    dot.style.width='8px';dot.style.height='8px';dot.style.borderRadius='50%';
    dot.style.background=corDot(st);dot.style.flexShrink='0';

    var nome=document.createElement('span');
    nome.style.flex='1';nome.textContent=cod;

    var label=document.createElement('span');
    label.style.fontSize='10px';label.style.color=corDot(st);
    label.textContent=labelStatus(st);

    item.appendChild(dot);item.appendChild(nome);item.appendChild(label);

    item.addEventListener('mouseover',function(){item.style.background='var(--s2)';});
    item.addEventListener('mouseout',function(){item.style.background='transparent';});
    item.addEventListener('mousedown',function(e){
      e.preventDefault();
      selecionarEndereco(cod);
    });

    dd.appendChild(item);
  });
  dd.style.display='block';
}
function abrirDropdown(){ renderDropdown(document.getElementById('endereco').value); }
function filtrarDropdown(){ renderDropdown(document.getElementById('endereco').value); }
function fecharDropdown(){ document.getElementById('end-dropdown').style.display='none'; }
function selecionarEndereco(cod){
  document.getElementById('endereco').value=cod;
  fecharDropdown();
  verificarEndereco();
  upd();
}

function verificarEndereco(){
  var val=document.getElementById('endereco').value.trim().toUpperCase();
  var badge=document.getElementById('end-badge');
  var info=document.getElementById('end-info');
  if(!val){badge.style.display='none';info.textContent='';return;}
  var norm=val.replace(/[\s\-]+/g,'');
  var m=norm.match(/^R(\d{2})(\d{3})(\d{1,2}[A-Z]?)$/);
  if(m)norm='R'+m[1]+' '+m[2]+' '+m[3];
  else norm=val;
  var st=endStatus[norm];
  if(!st){badge.style.display='none';info.textContent='';return;}
  badge.style.display='inline-block';
  if(st==='LIVRE'){
    badge.className='end-livre';badge.textContent='LIVRE';
    info.style.color='var(--gtxt)';info.textContent='✓ Endereço disponível';
  }else if(st==='PARCIAL'){
    badge.className='end-parcial';badge.textContent='PARCIAL';
    info.style.color='var(--atxt)';info.textContent='⚠ Endereço parcialmente ocupado';
  }else if(st==='OCUPADO'){
    badge.className='end-ocupado';badge.textContent='OCUPADO';
    info.style.color='var(--rtxt)';info.textContent='✕ Endereço ocupado — verifique antes de usar';
  }else if(st==='BLOQUEADO'){
    badge.className='end-bloqueado';badge.textContent='BLOQUEADO';
    info.style.color='var(--txt3)';info.textContent='⛔ Endereço bloqueado para uso';
  }
}

function ss(msg,t){var el=document.getElementById('stbar');
  el.className='sb-status '+(t||'info');el.innerHTML='<div class="dot"></div>'+msg;}
function fmt(n,t){return String(n).padStart(3,'0')+'/'+String(t).padStart(3,'0');}
function upd(){
  document.getElementById('s-pal').textContent=document.getElementById('palete').value.trim()||'—';
  document.getElementById('s-end').textContent=document.getElementById('endereco').value.trim()||'—';
  document.getElementById('s-nped').textContent=new Set(resumo.map(function(r){return r.pedido;})).size;
  document.getElementById('s-nvol').textContent=totalVols;
}
function renderOut(){
  if(!resumo.length){document.getElementById('out').textContent='Pedidos adicionados aparecerão aqui...';return;}
  var ag={};
  resumo.forEach(function(r){
    if(!ag[r.pedido])ag[r.pedido]={ini:r.ini,fin:r.fin,tot:r.tot};
    else{ag[r.pedido].ini=Math.min(ag[r.pedido].ini,r.ini);
         ag[r.pedido].fin=Math.max(ag[r.pedido].fin,r.fin);}
  });
  var txt='PALETE:   '+resumo[0].palete+'\nENDEREÇO: '+resumo[0].endereco+'\n\n';
  for(var p in ag){var a=ag[p];txt+=p+'\n  '+fmt(a.ini,a.tot)+' → '+fmt(a.fin,a.tot)+'\n\n';}
  document.getElementById('out').textContent=txt;
}
['palete','endereco','pedido','vol_ini','vol_fin'].forEach(function(id,i){
  var nx=['endereco','pedido','vol_ini','vol_fin','vol_tot'];
  document.getElementById(id).addEventListener('keydown',function(e){
    if(e.key==='Enter'){e.preventDefault();fecharDropdown();document.getElementById(nx[i]).focus();}
  });
});
document.getElementById('vol_tot').addEventListener('keydown',function(e){
  if(e.key==='Enter'){e.preventDefault();adicionar();}
});
async function adicionar(){
  var pal=document.getElementById('palete').value.trim().toUpperCase();
  var end=document.getElementById('endereco').value.trim().toUpperCase();
  var ped=document.getElementById('pedido').value.trim().toUpperCase();
  var ini=parseInt(document.getElementById('vol_ini').value)||0;
  var fin=parseInt(document.getElementById('vol_fin').value)||0;
  var tot=parseInt(document.getElementById('vol_tot').value)||0;
  if(!pal||!end||!ped||!ini||!fin||!tot){ss('⚠ Preencha todos os campos.','warn');return;}
  if(fin<ini){ss('⚠ Vol. final menor que inicial.','warn');return;}
  if(fin>tot){ss('⚠ Vol. final maior que total.','warn');return;}
  document.getElementById('btnAdd').disabled=true;document.getElementById('btnFin').disabled=true;
  ss('Criando palete...','info');
  try{
    var rP=await fetch('/paletes/manual',{method:'POST',headers:authHeaders(),
      body:JSON.stringify({codigo_palete:pal,codigo_endereco:end})});
    var dP=await rP.json();
    if(dP.detail){ss('✕ '+dP.detail,'err');toast(dP.detail,'err');
      document.getElementById('btnAdd').disabled=false;document.getElementById('btnFin').disabled=false;return;}
    ss('Gravando '+(fin-ini+1)+' volume(s)...','info');
    var erros=[];
    for(var i=ini;i<=fin;i++){
      var rV=await fetch('/pedidos-volume',{method:'POST',headers:authHeaders(),
        body:JSON.stringify({numero_pedido:ped,volume_atual:i,volume_total:tot,palete_codigo:pal})});
      var dV=await rV.json();if(dV.detail)erros.push('Vol '+i+': '+dV.detail);
    }
    if(erros.length)ss('⚠ '+(fin-ini+1-erros.length)+' ok, '+erros.length+' já existiam.','warn');
    else{ss('✓ '+(fin-ini+1)+' volume(s) de '+ped+' adicionados!','ok');toast('Volumes adicionados!');}
    resumo.push({palete:pal,endereco:end,pedido:ped,ini:ini,fin:fin,tot:tot});
    totalVols+=(fin-ini+1-erros.length);renderOut();upd();
    document.getElementById('pedido').value='';document.getElementById('vol_ini').value='';
    document.getElementById('vol_fin').value='';document.getElementById('vol_tot').value='';
    document.getElementById('pedido').focus();
  }catch(e){ss('✕ Erro de conexão.','err');toast('Erro de conexão','err');}
  document.getElementById('btnAdd').disabled=false;document.getElementById('btnFin').disabled=false;
}
function finalizar(){
  var pal=document.getElementById('palete').value.trim();
  var end=document.getElementById('endereco').value.trim();
  if(!pal||!end){ss('⚠ Informe palete e endereço.','warn');return;}
  if(!resumo.length){ss('⚠ Nenhum pedido adicionado.','warn');return;}
  var ag={};
  resumo.forEach(function(r){
    if(!ag[r.pedido])ag[r.pedido]={ini:r.ini,fin:r.fin,tot:r.tot};
    else{ag[r.pedido].ini=Math.min(ag[r.pedido].ini,r.ini);ag[r.pedido].fin=Math.max(ag[r.pedido].fin,r.fin);}
  });
  var txt='✓ PALETE FINALIZADO\n\nPALETE:   '+pal+'\nENDEREÇO: '+end+'\nSTATUS:   EM USO\n\nRESUMO:\n\n';
  for(var p in ag){var a=ag[p];txt+=p+'\n  '+fmt(a.ini,a.tot)+' → '+fmt(a.fin,a.tot)+'\n\n';}
  document.getElementById('out').textContent=txt;
  ss('Palete finalizado. Clique em "Novo" para recomeçar.','ok');toast('Palete finalizado!');
  document.getElementById('btnAdd').disabled=true;document.getElementById('btnFin').disabled=true;
}
function resetar(){
  resumo=[];totalVols=0;
  ['palete','endereco','pedido','vol_ini','vol_fin','vol_tot'].forEach(function(id){document.getElementById(id).value='';});
  document.getElementById('out').textContent='Pedidos adicionados aparecerão aqui...';
  document.getElementById('end-badge').style.display='none';
  document.getElementById('end-info').textContent='';
  fecharDropdown();
  document.getElementById('btnAdd').disabled=false;document.getElementById('btnFin').disabled=false;
  ss('Pronto para novo palete.','info');upd();document.getElementById('palete').focus();
}
upd();
</script>
""" + shell_close() + """
</body></html>""")

# ══════════════════════════════════════════════════════════════════
#  PÁGINA: OPERAÇÃO
# ══════════════════════════════════════════════════════════════════
@app.get("/operacao", response_class=HTMLResponse)
def pg_operacao():
    return ("""<!DOCTYPE html><html lang="pt-BR"><head>""" + _SHARED +
            """<title>WMS · Operação</title></head><body>""" +
            shell_open('oper', '🔍', 'var(--bdim)', 'Consulta Rápida', 'Bipe ou digite um endereço ou número de pedido') +
            r"""
  <div class="sw" style="margin-bottom:12px;">
    <span class="si">⌕</span>
    <input id="q" placeholder="Endereço ou pedido..." autofocus
      onkeydown="if(event.key==='Enter')buscar()">
  </div>
  <div class="brow" style="margin-bottom:16px;">
    <button class="btn bb bfull" onclick="buscarEndereco()">🔍 Buscar Endereço</button>
    <button class="btn bgh bfull" style="border-color:var(--green);color:var(--gtxt);"
      onclick="buscarPedido()">📦 Buscar Pedido</button>
  </div>
  <div class="stats">
    <div class="stat"><div class="sl">Consultas</div><div class="sv" id="nc">0</div></div>
    <div class="stat"><div class="sl">Endereços</div><div class="sv" id="ne">0</div></div>
    <div class="stat"><div class="sl">Pedidos</div><div class="sv" id="np">0</div></div>
    <div class="stat"><div class="sl">Erros</div><div class="sv red" id="nr">0</div></div>
  </div>
  <div class="term" id="out">Aguardando leitura...</div>
  <div style="margin-top:12px;">
    <div style="font-size:10px;text-transform:uppercase;letter-spacing:.08em;
      color:var(--txt3);margin-bottom:6px;">Histórico</div>
    <div class="chips" id="hist"></div>
  </div>
<script>
var nc=0,ne=0,np=0,nr=0,hist=[];
var SOK='https://actions.google.com/sounds/v1/alarms/beep_short.ogg';
var SERR='https://actions.google.com/sounds/v1/cartoon/pop.ogg';
function beep(u){try{new Audio(u).play();}catch(e){}}
function flash(c){var el=document.getElementById('q');el.className=c;setTimeout(function(){el.className='';},800);}
function addHist(v){if(!v)return;hist=[...new Set([v].concat(hist))].slice(0,12);
  document.getElementById('hist').innerHTML=hist.map(function(h){return '<div class="chip" onclick="rebuscar(&quot;'+h+'&quot;)">'+h+'</div>';}).join('');
  nc++;document.getElementById('nc').textContent=nc;}
function rebuscar(v){document.getElementById('q').value=v;buscar();}
function buscar(){var v=document.getElementById('q').value.trim().toUpperCase();
  if(!v)return;
  if(v.match(/^R[0-9]/)||v.indexOf('R ')===0)buscarEndereco();else buscarPedido();}
var _t;document.getElementById('q').addEventListener('input',function(){
  clearTimeout(_t);var v=this.value.trim();
  if(v.length>=5&&v.toUpperCase().indexOf('R')!==0){_t=setTimeout(buscar,500);}
});
async function buscarEndereco(){
  var cod=document.getElementById('q').value.trim().toUpperCase();if(!cod)return;
  document.getElementById('out').textContent='Buscando...';
  document.querySelectorAll('button').forEach(function(b){b.disabled=true;});
  try{
    var r=await fetch('/enderecos/'+encodeURIComponent(cod)+'/detalhes');
    var d=await r.json();
    if(!d.paletes||!d.paletes.length){
      document.getElementById('out').textContent='Endereço não encontrado ou sem palete.';
      flash('err');beep(SERR);nr++;document.getElementById('nr').textContent=nr;
    }else{
      var txt='ENDEREÇO: '+d.endereco+'\n\n';
      d.paletes.forEach(function(p){
        txt+='PALETE: '+p.palete+'\n'+'─'.repeat(24)+'\n';
        if(!p.pedidos.length)txt+='  (sem pedidos)\n';
        p.pedidos.forEach(function(ped){txt+='\n  PEDIDO: '+ped.pedido+'\n';
          ped.volumes.forEach(function(v){txt+='    '+v+'\n';});});txt+='\n';
      });
      document.getElementById('out').textContent=txt;
      flash('ok');beep(SOK);addHist(cod);ne++;document.getElementById('ne').textContent=ne;
    }
  }catch(e){document.getElementById('out').textContent='Erro ao buscar.';
    flash('err');beep(SERR);nr++;document.getElementById('nr').textContent=nr;}
  document.querySelectorAll('button').forEach(function(b){b.disabled=false;});
  document.getElementById('q').value='';document.getElementById('q').focus();
}
async function buscarPedido(){
  var cod=document.getElementById('q').value.trim().toUpperCase();if(!cod)return;
  document.getElementById('out').textContent='Buscando...';
  document.querySelectorAll('button').forEach(function(b){b.disabled=true;});
  try{
    var r=await fetch('/pedidos/'+encodeURIComponent(cod));var d=await r.json();
    if(d.detail){document.getElementById('out').textContent=d.detail;
      flash('err');beep(SERR);nr++;document.getElementById('nr').textContent=nr;
    }else{
      var txt='PEDIDO: '+d.pedido+'\n\n';
      d.enderecos.forEach(function(i){
        txt+='ENDEREÇO: '+i.endereco+'\nPALETE:   '+i.palete+'\n'+'─'.repeat(24)+'\n';
        i.volumes.forEach(function(v){txt+='  '+v+'\n';});txt+='\n';
      });
      document.getElementById('out').textContent=txt;
      flash('ok');beep(SOK);addHist(cod);np++;document.getElementById('np').textContent=np;
    }
  }catch(e){document.getElementById('out').textContent='Erro ao buscar.';
    flash('err');beep(SERR);nr++;document.getElementById('nr').textContent=nr;}
  document.querySelectorAll('button').forEach(function(b){b.disabled=false;});
  document.getElementById('q').value='';document.getElementById('q').focus();
}
</script>
""" + shell_close() + """
</body></html>""")

# ══════════════════════════════════════════════════════════════════
#  PÁGINA: GERENCIAR VOLUMES
# ══════════════════════════════════════════════════════════════════
@app.get("/gerenciar-volumes", response_class=HTMLResponse)
def pg_gerenciar():
    return ("""<!DOCTYPE html><html lang="pt-BR"><head>""" + _SHARED +
            """<title>WMS · Volumes</title></head><body>""" +
            shell_open('vol', '🗂️', 'var(--adim)', 'Gerenciar Volumes', 'Visualize, transfira e apague volumes') +
            r"""
  <div class="modal-bg" id="modalBg">
    <div class="modal">
      <h3>↔ Transferir Volumes</h3>
      <p style="font-size:12px;color:var(--txt3);margin-bottom:16px;" id="modalInfo">— volumes</p>
      <div class="f"><label>Novo Palete</label>
        <input class="fi" id="tPal" placeholder="Ex: PAL002"></div>
      <div class="f"><label>Novo Endereço</label>
        <input class="fi" id="tEnd" placeholder="Ex: R07 016 1"></div>
      <div class="brow" style="margin-top:4px;">
        <button class="btn ba" onclick="confirmarTransf()">↔ Transferir</button>
        <button class="btn bgh" onclick="fecharModal()">Cancelar</button>
      </div>
      <div id="modalMsg" style="font-size:12px;margin-top:8px;min-height:16px;"></div>
    </div>
  </div>
  <div style="display:flex;align-items:center;justify-content:space-between;
    flex-wrap:wrap;gap:10px;margin-bottom:16px;">
    <div class="brow">
      <button class="btn bgh" onclick="carregar()">↺ Atualizar</button>
      <button class="btn bgh" onclick="selAll()">☑ Todos</button>
      <button class="btn bgh" onclick="desSel()">☐ Nenhum</button>
      <button class="btn ba" onclick="abrirTransf()">↔ Transferir</button>
      <button class="btn bd" onclick="apagarSel()">🗑 Apagar</button>
    </div>
  </div>
  <div style="display:flex;gap:10px;align-items:center;margin-bottom:12px;flex-wrap:wrap;">
    <input type="text" id="filtro" placeholder="Filtrar por pedido, palete ou endereço..."
      style="flex:1;min-width:180px;padding:9px 13px;background:var(--s1);color:var(--txt);
        border:1px solid var(--br);border-radius:var(--r);font-size:13px;outline:none;"
      oninput="filtrar()">
    <span id="info" style="font-size:12px;color:var(--txt3);white-space:nowrap;">—</span>
  </div>
  <div class="card" style="margin-bottom:0;">
    <div class="tw">
      <table>
        <thead><tr>
          <th style="width:32px"><input type="checkbox" id="chkAll" onchange="toggleAll(this)"></th>
          <th>ID</th><th>Pedido</th><th>Volume</th><th>Palete</th><th>Endereço</th><th>Ação</th>
        </tr></thead>
        <tbody id="tbody"></tbody>
      </table>
    </div>
  </div>
<script>
var dados=[];
async function carregar(){
  document.getElementById('tbody').innerHTML='<tr><td colspan="7" style="color:var(--txt3);text-align:center;padding:20px;">Carregando...</td></tr>';
  var r=await fetch('/pedidos-volume');dados=await r.json();
  document.getElementById('filtro').value='';filtrar();
}
function filtrar(){
  var q=document.getElementById('filtro').value.trim().toLowerCase();
  var fd=q?dados.filter(function(d){return String(d.numero_pedido).toLowerCase().indexOf(q)!==-1||
    d.palete_codigo.toLowerCase().indexOf(q)!==-1||(d.endereco_codigo||'').toLowerCase().indexOf(q)!==-1;}):dados;
  var tb=document.getElementById('tbody');
  if(!fd.length){tb.innerHTML='<tr><td colspan="7" style="color:var(--txt3);text-align:center;padding:20px;">Nenhum registro.</td></tr>';
    document.getElementById('info').textContent='0 registros';return;}
  tb.innerHTML=fd.map(function(d){
    var vol=String(d.volume_atual).padStart(3,'0')+'/'+String(d.volume_total).padStart(3,'0');
    return '<tr>'+
      '<td><input type="checkbox" class="chk" value="'+d.id+'"></td>'+
      '<td style="color:var(--txt3);font-family:var(--mono);font-size:11px;">'+d.id+'</td>'+
      '<td style="font-family:var(--mono);font-weight:600;">'+d.numero_pedido+'</td>'+
      '<td><span class="bk bk-blue">'+vol+'</span></td>'+
      '<td style="color:var(--gtxt);font-family:var(--mono);">'+d.palete_codigo+'</td>'+
      '<td style="color:var(--txt3);">'+(d.endereco_codigo||'—')+'</td>'+
      '<td><button class="btn bd" style="padding:4px 9px;font-size:11px;" onclick="apagarUm('+d.id+')">Apagar</button></td>'+
      '</tr>';
  }).join('');
  document.getElementById('info').textContent=fd.length+' registro(s)';
}
function getIds(){return Array.from(document.querySelectorAll('.chk:checked')).map(function(c){return parseInt(c.value);});}
function selAll(){document.querySelectorAll('.chk').forEach(function(c){c.checked=true;});}
function desSel(){document.querySelectorAll('.chk').forEach(function(c){c.checked=false;});}
function toggleAll(el){document.querySelectorAll('.chk').forEach(function(c){c.checked=el.checked;});}
async function apagarUm(id){
  if(!confirm('Apagar este volume?'))return;
  await fetch('/pedidos-volume/'+id,{method:'DELETE',headers:authHeaders()});
  toast('Volume apagado.');carregar();
}
async function apagarSel(){
  var ids=getIds();if(!ids.length){alert('Selecione ao menos um volume.');return;}
  if(!confirm('Apagar '+ids.length+' volume(s)?'))return;
  var r=await fetch('/pedidos-volume/deletar-varios',{method:'POST',
    headers:authHeaders(),body:JSON.stringify({ids:ids})});
  var d=await r.json();toast(d.removidos+' volume(s) apagados.');carregar();
}
function abrirTransf(){
  var ids=getIds();if(!ids.length){alert('Selecione os volumes a transferir.');return;}
  document.getElementById('modalInfo').textContent=ids.length+' volume(s) selecionado(s)';
  document.getElementById('tPal').value='';document.getElementById('tEnd').value='';
  document.getElementById('modalMsg').textContent='';
  document.getElementById('modalBg').classList.add('open');
  document.getElementById('tPal').focus();
}
function fecharModal(){document.getElementById('modalBg').classList.remove('open');}
document.getElementById('tPal').addEventListener('keydown',function(e){if(e.key==='Enter')document.getElementById('tEnd').focus();});
document.getElementById('tEnd').addEventListener('keydown',function(e){if(e.key==='Enter')confirmarTransf();});
async function confirmarTransf(){
  var ids=getIds();
  var pal=document.getElementById('tPal').value.trim().toUpperCase();
  var end=document.getElementById('tEnd').value.trim().toUpperCase();
  var msg=document.getElementById('modalMsg');
  if(!pal||!end){msg.style.color='var(--rtxt)';msg.textContent='Preencha palete e endereço.';return;}
  msg.style.color='var(--txt3)';msg.textContent='Transferindo...';
  try{
    var r=await fetch('/pedidos-volume/transferir',{method:'POST',headers:authHeaders(),
      body:JSON.stringify({ids:ids,novo_palete:pal,novo_endereco:end})});
    var d=await r.json();
    if(d.detail){msg.style.color='var(--rtxt)';msg.textContent=d.detail;return;}
    toast('✓ '+d.movidos+' volume(s) transferidos para '+pal+' / '+d.novo_endereco);
    fecharModal();carregar();
  }catch(e){msg.style.color='var(--rtxt)';msg.textContent='Erro de conexão.';}
}
carregar();
</script>
""" + shell_close() + """
</body></html>""")

# ══════════════════════════════════════════════════════════════════
#  PÁGINA: HISTÓRICO — com filtros e exportação Excel/CSV
# ══════════════════════════════════════════════════════════════════
@app.get("/historico", response_class=HTMLResponse)
def pg_historico():
    return ("""<!DOCTYPE html><html lang="pt-BR"><head>""" + _SHARED +
            """<title>WMS · Histórico</title>
<script src="https://cdnjs.cloudflare.com/ajax/libs/SheetJS/0.18.5/xlsx.full.min.js"></script>
</head><body>""" +
            shell_open('hist', '📋', 'var(--pdim)', 'Histórico de Ações', 'Auditoria — cadastros, exclusões, transferências e status') +
            r"""
  <div class="modal-bg" id="filtroModalBg">
    <div class="modal" style="max-width:480px;">
      <h3>🔧 Filtros do Histórico</h3>
      <div class="f"><label>Ação</label>
        <select id="m-filtroAcao" style="width:100%;padding:11px 13px;background:var(--bg);
          color:var(--txt);border:1px solid var(--br);border-radius:var(--r);
          font-family:var(--mono);font-size:14px;outline:none;">
          <option value="">Todas as ações</option>
          <option value="CADASTRO">Cadastros</option>
          <option value="EXCLUSAO">Exclusões</option>
          <option value="TRANSFERENCIA">Transferências</option>
          <option value="STATUS_END">Status endereço</option>
        </select>
      </div>
      <div class="f"><label>Buscar (pedido, usuário, endereço...)</label>
        <input class="fi" id="m-filtroTxt" placeholder="Digite para filtrar...">
      </div>
      <div class="brow" style="margin-top:6px;">
        <button class="btn bg" onclick="aplicarFiltrosModal()">✓ Aplicar Filtros</button>
        <button class="btn bgh" onclick="limparFiltrosModal()">↺ Limpar</button>
      </div>
      <div class="divider"></div>
      <button class="btn bb bfull" onclick="exportarExcel()">⬇ Baixar Relatório (Excel)</button>
      <div style="font-size:11px;color:var(--txt3);margin-top:8px;text-align:center;">
        O relatório respeita os filtros aplicados acima.
      </div>
      <div class="brow" style="margin-top:14px;">
        <button class="btn bgh bfull" onclick="fecharFiltroModal()">Fechar</button>
      </div>
    </div>
  </div>

  <div style="display:flex;align-items:center;justify-content:flex-end;
    flex-wrap:wrap;gap:10px;margin-bottom:16px;">
    <button class="btn bgh" onclick="carregar()">↺ Atualizar</button>
    <button class="btn ba" onclick="abrirFiltroModal()">🔧 Filtros / Exportar</button>
    <span id="info" style="font-size:12px;color:var(--txt3);white-space:nowrap;align-self:center;">—</span>
  </div>
  <div id="filtroAtivoTag" style="display:none;margin-bottom:12px;font-size:11px;
    color:var(--atxt);background:var(--adim);border:1px solid var(--amber);
    border-radius:var(--r);padding:6px 12px;"></div>
  <div class="card" style="margin-bottom:0;">
    <div class="tw">
      <table>
        <thead><tr>
          <th>Data/Hora</th><th>Usuário</th><th>Ação</th><th>Pedido</th>
          <th>Volume</th><th>Palete</th><th>De</th><th>Para</th><th>Detalhe</th>
        </tr></thead>
        <tbody id="tbody"></tbody>
      </table>
    </div>
  </div>
<script>
var dados=[];
var filtroAcao='';
var filtroTxt='';

async function carregar(){
  document.getElementById('tbody').innerHTML='<tr><td colspan="9" style="color:var(--txt3);text-align:center;padding:20px;">Carregando...</td></tr>';
  try{
    var r=await fetch('/historico-api',{headers:authHeaders()});
    if(r.status===401){window.location.href='/login';return;}
    dados=await r.json();filtrar();
  }catch(e){document.getElementById('tbody').innerHTML='<tr><td colspan="9" style="color:var(--rtxt);text-align:center;padding:20px;">Erro ao carregar.</td></tr>';}
}
function getFiltrados(){
  return dados.filter(function(d){
    if(filtroAcao&&d.acao!==filtroAcao)return false;
    if(filtroTxt){
      var s=(d.numero_pedido+d.usuario_nome+d.palete_codigo+d.endereco_de+d.endereco_para+d.detalhe_extra).toLowerCase();
      if(s.indexOf(filtroTxt.toLowerCase())===-1)return false;
    }
    return true;
  });
}
function filtrar(){
  var fd=getFiltrados();
  var tb=document.getElementById('tbody');
  if(!fd.length){tb.innerHTML='<tr><td colspan="9" style="color:var(--txt3);text-align:center;padding:20px;">Nenhum registro.</td></tr>';
    document.getElementById('info').textContent='0 registros';return;}
  var cor={'CADASTRO':'bk-green','EXCLUSAO':'bk-red','TRANSFERENCIA':'bk-amber','STATUS_END':'bk-blue'};
  tb.innerHTML=fd.map(function(d){
    var vol=d.volume_atual!=null?String(d.volume_atual).padStart(3,'0')+'/'+String(d.volume_total).padStart(3,'0'):'—';
    return '<tr>'+
      '<td style="font-family:var(--mono);font-size:11px;color:var(--txt3);white-space:nowrap;">'+d.criado_em+'</td>'+
      '<td style="font-weight:500;font-size:12px;">'+d.usuario_nome+'</td>'+
      '<td><span class="bk '+(cor[d.acao]||'bk-blue')+'">'+d.acao+'</span></td>'+
      '<td style="font-family:var(--mono);">'+d.numero_pedido+'</td>'+
      '<td><span class="bk bk-blue">'+vol+'</span></td>'+
      '<td style="color:var(--gtxt);font-family:var(--mono);">'+d.palete_codigo+'</td>'+
      '<td style="color:var(--txt3);font-family:var(--mono);font-size:11px;">'+d.endereco_de+'</td>'+
      '<td style="color:var(--gtxt);font-family:var(--mono);font-size:11px;">'+d.endereco_para+'</td>'+
      '<td style="color:var(--txt3);font-size:11px;">'+d.detalhe_extra+'</td>'+
      '</tr>';
  }).join('');
  document.getElementById('info').textContent=fd.length+' registro(s)';
}
function abrirFiltroModal(){
  document.getElementById('m-filtroAcao').value=filtroAcao;
  document.getElementById('m-filtroTxt').value=filtroTxt;
  document.getElementById('filtroModalBg').classList.add('open');
}
function fecharFiltroModal(){document.getElementById('filtroModalBg').classList.remove('open');}
function aplicarFiltrosModal(){
  filtroAcao=document.getElementById('m-filtroAcao').value;
  filtroTxt=document.getElementById('m-filtroTxt').value.trim();
  filtrar();atualizarTagFiltro();fecharFiltroModal();toast('Filtros aplicados.');
}
function limparFiltrosModal(){
  document.getElementById('m-filtroAcao').value='';
  document.getElementById('m-filtroTxt').value='';
  filtroAcao='';filtroTxt='';
  filtrar();atualizarTagFiltro();toast('Filtros limpos.');
}
function atualizarTagFiltro(){
  var tag=document.getElementById('filtroAtivoTag');
  var partes=[];
  if(filtroAcao)partes.push('Ação: '+filtroAcao);
  if(filtroTxt)partes.push('Busca: "'+filtroTxt+'"');
  if(partes.length){tag.style.display='block';tag.textContent='🔧 Filtro ativo — '+partes.join('  ·  ');}
  else{tag.style.display='none';}
}
function exportarExcel(){
  filtroAcao=document.getElementById('m-filtroAcao').value;
  filtroTxt=document.getElementById('m-filtroTxt').value.trim();
  var fd=getFiltrados();
  if(!fd.length){toast('Nenhum registro para exportar com esse filtro.','err');return;}
  var linhas=fd.map(function(d){
    var vol=d.volume_atual!=null?String(d.volume_atual).padStart(3,'0')+'/'+String(d.volume_total).padStart(3,'0'):'—';
    return {'Data/Hora':d.criado_em,'Usuário':d.usuario_nome,'Ação':d.acao,'Pedido':d.numero_pedido,
      'Volume':vol,'Palete':d.palete_codigo,'Endereço De':d.endereco_de,'Endereço Para':d.endereco_para,
      'Detalhe':d.detalhe_extra};
  });
  var agora=new Date();
  var dataStr=agora.toLocaleDateString('pt-BR').replace(/\//g,'-');
  var horaStr=agora.toLocaleTimeString('pt-BR').replace(/:/g,'-');
  if(typeof XLSX==='undefined'){exportarCSVFallback(linhas,dataStr,horaStr);return;}
  try{
    var ws=XLSX.utils.json_to_sheet(linhas);
    ws['!cols']=[{wch:18},{wch:18},{wch:14},{wch:12},{wch:10},{wch:10},{wch:14},{wch:14},{wch:30}];
    var wb=XLSX.utils.book_new();
    XLSX.utils.book_append_sheet(wb,ws,'Historico');
    XLSX.writeFile(wb,'historico_walze_'+dataStr+'_'+horaStr+'.xlsx');
    filtrar();atualizarTagFiltro();
    toast('✓ Relatório baixado: '+fd.length+' registro(s)');
  }catch(e){exportarCSVFallback(linhas,dataStr,horaStr);}
}
function exportarCSVFallback(linhas,dataStr,horaStr){
  var cab=Object.keys(linhas[0]);
  var rows=[cab.join(';')];
  linhas.forEach(function(l){rows.push(cab.map(function(c){return (l[c]==null?'':String(l[c])).replace(/;/g,',');}).join(';'));});
  var csv='\ufeff'+rows.join('\n');
  var blob=new Blob([csv],{type:'text/csv;charset=utf-8;'});
  var url=URL.createObjectURL(blob);
  var a=document.createElement('a');
  a.href=url;a.download='historico_walze_'+dataStr+'_'+horaStr+'.csv';
  document.body.appendChild(a);a.click();document.body.removeChild(a);URL.revokeObjectURL(url);
  filtrar();atualizarTagFiltro();
  toast('✓ Relatório baixado em CSV (Excel indisponível): '+linhas.length+' registro(s)','ok');
}
carregar();
</script>
""" + shell_close() + """
</body></html>""")

# ══════════════════════════════════════════════════════════════════
#  PÁGINA: ENDEREÇOS — gerenciar status manualmente (grid simples)
# ══════════════════════════════════════════════════════════════════
@app.get("/enderecos-page", response_class=HTMLResponse)
def pg_enderecos():
    return ("""<!DOCTYPE html><html lang="pt-BR"><head>""" + _SHARED +
            """<title>WMS · Endereços</title></head><body>""" +
            shell_open('end', '🏷️', 'var(--bdim)', 'Endereços', 'Gerencie o status de ocupação de cada endereço') +
            r"""
  <div style="display:flex;gap:8px;margin-bottom:18px;flex-wrap:wrap;">
    <button class="btn bgh" onclick="setFiltro('TODOS')">Todos</button>
    <button class="btn bgh" onclick="setFiltro('LIVRE')">Livres</button>
    <button class="btn bgh" onclick="setFiltro('PARCIAL')">Parciais</button>
    <button class="btn bgh" onclick="setFiltro('OCUPADO')">Ocupados</button>
    <button class="btn bgh" onclick="setFiltro('BLOQUEADO')">Bloqueados</button>
    <button class="btn bgh" style="margin-left:auto;" onclick="carregar()">↺ Atualizar</button>
  </div>
  <div style="display:flex;gap:10px;margin-bottom:18px;flex-wrap:wrap;">
    <div class="metric-card" style="flex:1;min-width:110px;"><div><div class="num" id="cnt-l" style="color:var(--gtxt);">—</div><div class="lbl">Livres</div></div></div>
    <div class="metric-card" style="flex:1;min-width:110px;"><div><div class="num" id="cnt-p" style="color:var(--atxt);">—</div><div class="lbl">Parciais</div></div></div>
    <div class="metric-card" style="flex:1;min-width:110px;"><div><div class="num" id="cnt-o" style="color:var(--rtxt);">—</div><div class="lbl">Ocupados</div></div></div>
    <div class="metric-card" style="flex:1;min-width:110px;"><div><div class="num" id="cnt-t" style="color:var(--txt);">—</div><div class="lbl">Total</div></div></div>
  </div>
  <div style="display:grid;grid-template-columns:repeat(auto-fill,minmax(200px,1fr));gap:10px;" id="grid"></div>
<script>
var enderecos=[];
var filtroAtual='TODOS';
function setFiltro(s){filtroAtual=s;renderGrid();}
async function carregar(){
  document.getElementById('grid').innerHTML='<p style="color:var(--txt3);padding:10px;">Carregando...</p>';
  try{
    var r=await fetch('/enderecos');
    enderecos=await r.json();
    renderGrid();atualizarContadores();
  }catch(e){document.getElementById('grid').innerHTML='<p style="color:var(--rtxt);">Erro ao carregar.</p>';}
}
function corStatus(s){
  if(s==='LIVRE')return{border:'var(--green)',cls:'end-livre'};
  if(s==='PARCIAL')return{border:'var(--amber)',cls:'end-parcial'};
  if(s==='OCUPADO')return{border:'var(--red)',cls:'end-ocupado'};
  if(s==='BLOQUEADO')return{border:'var(--br2)',cls:'end-bloqueado'};
  return{border:'var(--br)',cls:''};
}
function renderGrid(){
  var g=document.getElementById('grid');g.innerHTML='';
  var lista=enderecos;
  if(filtroAtual!=='TODOS')lista=enderecos.filter(function(e){return (e.status_ocupacao||'LIVRE')===filtroAtual;});
  if(!lista.length){g.innerHTML='<p style="color:var(--txt3);padding:10px;">Nenhum endereço encontrado nesse filtro.</p>';return;}
  lista.forEach(function(e){
    var st=e.status_ocupacao||'LIVRE';
    var c=corStatus(st);
    var div=document.createElement('div');
    div.style.cssText='background:var(--s1);border:1px solid '+c.border+';border-radius:var(--rl);padding:16px;';
    div.innerHTML='<div style="font-family:var(--mono);font-size:14px;font-weight:600;color:var(--txt);margin-bottom:8px;">'+e.codigo+'</div>'+
      '<span class="bk '+c.cls+'" style="margin-bottom:12px;display:inline-block;">'+st+'</span>'+
      '<div style="display:flex;flex-direction:column;gap:5px;margin-top:10px;">'+
      '<button onclick="setStatus(&quot;'+e.codigo+'&quot;,&quot;LIVRE&quot;)" class="btn" style="padding:6px;font-size:11px;'+
      'background:'+(st==='LIVRE'?'var(--green)':'var(--gdim)')+';color:'+(st==='LIVRE'?'#04130a':'var(--gtxt)')+';border:1px solid var(--green);">● Livre</button>'+
      '<button onclick="setStatus(&quot;'+e.codigo+'&quot;,&quot;PARCIAL&quot;)" class="btn" style="padding:6px;font-size:11px;'+
      'background:'+(st==='PARCIAL'?'var(--amber)':'var(--adim)')+';color:'+(st==='PARCIAL'?'#1a1200':'var(--atxt)')+';border:1px solid var(--amber);">● Parcial</button>'+
      '<button onclick="setStatus(&quot;'+e.codigo+'&quot;,&quot;OCUPADO&quot;)" class="btn" style="padding:6px;font-size:11px;'+
      'background:'+(st==='OCUPADO'?'var(--red)':'var(--rdim)')+';color:'+(st==='OCUPADO'?'#fff':'var(--rtxt)')+';border:1px solid var(--red);">● Ocupado</button>'+
      '<button onclick="setStatus(&quot;'+e.codigo+'&quot;,&quot;BLOQUEADO&quot;)" class="btn" style="padding:6px;font-size:11px;'+
      'background:'+(st==='BLOQUEADO'?'var(--br2)':'var(--s2)')+';color:var(--txt3);border:1px solid var(--br2);">● Bloqueado</button>'+
      '</div>';
    g.appendChild(div);
  });
}
function atualizarContadores(){
  document.getElementById('cnt-l').textContent=enderecos.filter(function(e){return (e.status_ocupacao||'LIVRE')==='LIVRE';}).length;
  document.getElementById('cnt-p').textContent=enderecos.filter(function(e){return e.status_ocupacao==='PARCIAL';}).length;
  document.getElementById('cnt-o').textContent=enderecos.filter(function(e){return e.status_ocupacao==='OCUPADO';}).length;
  document.getElementById('cnt-t').textContent=enderecos.length;
}
async function setStatus(codigo,status){
  try{
    var r=await fetch('/enderecos/'+encodeURIComponent(codigo)+'/status',{
      method:'PATCH',headers:authHeaders(),body:JSON.stringify({status_ocupacao:status})});
    var d=await r.json();
    if(d.detail){toast(d.detail,'err');return;}
    var idx=enderecos.findIndex(function(e){return e.codigo===codigo;});
    if(idx>=0)enderecos[idx].status_ocupacao=status;
    renderGrid();atualizarContadores();
    toast('✓ '+codigo+' marcado como '+status);
  }catch(e){toast('Erro de conexão','err');}
}
carregar();
</script>
""" + shell_close() + """
</body></html>""")

# ══════════════════════════════════════════════════════════════════
#  PÁGINA: USUÁRIOS (admin) — listar, ativar/desativar
# ══════════════════════════════════════════════════════════════════
@app.get("/usuarios", response_class=HTMLResponse)
def pg_usuarios():
    return ("""<!DOCTYPE html><html lang="pt-BR"><head>""" + _SHARED +
            """<title>WMS · Usuários</title></head><body>""" +
            shell_open('users', '👥', 'var(--bdim)', 'Usuários', 'Gerencie quem tem acesso ao sistema (somente administradores)') +
            r"""
  <div class="card">
    <div class="ct">Criar Novo Usuário</div>
    <div class="g2">
      <div class="f"><label>Nome completo</label><input class="fi" id="nNome" placeholder="Ex: João Silva"></div>
      <div class="f"><label>Login</label><input class="fi" id="nLogin" placeholder="Ex: joao.silva"></div>
    </div>
    <div class="g2">
      <div class="f"><label>Senha</label><input class="fi" id="nSenha" type="password" placeholder="Mínimo 4 caracteres"></div>
      <div class="f"><label>Papel</label>
        <select id="nPapel" style="width:100%;padding:11px 13px;background:var(--bg);color:var(--txt);
          border:1px solid var(--br);border-radius:var(--r);font-size:14px;outline:none;">
          <option value="OPERADOR">Operador</option>
          <option value="ADMIN">Administrador</option>
        </select>
      </div>
    </div>
    <button class="btn bg" onclick="criarUsuario()">✓ Criar Usuário</button>
    <div id="nMsg" style="font-size:12px;margin-top:10px;min-height:18px;"></div>
  </div>

  <div class="card" style="margin-bottom:0;">
    <div class="ct">Usuários do Sistema</div>
    <div class="tw">
      <table>
        <thead><tr><th>Nome</th><th>Login</th><th>Papel</th><th>E-mail</th><th>Status</th><th>Ação</th></tr></thead>
        <tbody id="tbody"></tbody>
      </table>
    </div>
  </div>
<script>
async function carregar(){
  document.getElementById('tbody').innerHTML='<tr><td colspan="6" style="color:var(--txt3);text-align:center;padding:20px;">Carregando...</td></tr>';
  try{
    var r=await fetch('/usuarios-api',{headers:authHeaders()});
    if(r.status===403){document.getElementById('tbody').innerHTML='<tr><td colspan="6" style="color:var(--rtxt);text-align:center;padding:20px;">Acesso restrito a administradores.</td></tr>';return;}
    var d=await r.json();
    var tb=document.getElementById('tbody');
    tb.innerHTML=d.map(function(u){
      return '<tr>'+
        '<td style="font-weight:600;">'+u.nome+'</td>'+
        '<td style="font-family:var(--mono);color:var(--txt3);">'+u.login+'</td>'+
        '<td><span class="bk '+(u.papel==='ADMIN'?'bk-purple':'bk-blue')+'">'+u.papel+'</span></td>'+
        '<td style="color:var(--txt3);font-size:11.5px;">'+(u.email||'—')+'</td>'+
        '<td><span class="bk '+(u.ativo?'bk-green':'bk-red')+'">'+(u.ativo?'ATIVO':'INATIVO')+'</span></td>'+
        '<td><button class="btn '+(u.ativo?'bd':'bg')+'" style="padding:5px 10px;font-size:11px;" onclick="alternar('+u.id+','+(!u.ativo)+')">'+
          (u.ativo?'Desativar':'Ativar')+'</button></td>'+
        '</tr>';
    }).join('');
  }catch(e){}
}
async function alternar(id,novoAtivo){
  try{
    var r=await fetch('/usuarios-api/'+id+'/ativo?ativo='+novoAtivo,{method:'PATCH',headers:authHeaders()});
    var d=await r.json();
    if(d.detail){toast(d.detail,'err');return;}
    toast('Status atualizado.');carregar();
  }catch(e){toast('Erro de conexão','err');}
}
async function criarUsuario(){
  var nome=document.getElementById('nNome').value.trim();
  var login=document.getElementById('nLogin').value.trim();
  var senha=document.getElementById('nSenha').value;
  var papel=document.getElementById('nPapel').value;
  var msg=document.getElementById('nMsg');
  if(!nome||!login||!senha){msg.style.color='var(--rtxt)';msg.textContent='Preencha todos os campos.';return;}
  try{
    var r=await fetch('/auth/criar-usuario',{method:'POST',headers:authHeaders(),
      body:JSON.stringify({nome:nome,login:login,senha:senha,papel:papel})});
    var d=await r.json();
    if(d.detail){msg.style.color='var(--rtxt)';msg.textContent=d.detail;return;}
    msg.style.color='var(--gtxt)';msg.textContent='✓ Usuário "'+d.login+'" criado!';
    document.getElementById('nNome').value='';document.getElementById('nLogin').value='';document.getElementById('nSenha').value='';
    carregar();
  }catch(e){msg.style.color='var(--rtxt)';msg.textContent='Erro de conexão.';}
}
carregar();
</script>
""" + shell_close() + """
</body></html>""")

# ══════════════════════════════════════════════════════════════════
#  PÁGINA: CRIAR PRIMEIRO ADMIN (sem necessidade de login se ninguém existe)
# ══════════════════════════════════════════════════════════════════
@app.get("/criar-admin", response_class=HTMLResponse)
def pg_criar_admin():
    return ("""<!DOCTYPE html><html lang="pt-BR"><head>""" + _SHARED +
            """<title>WMS · Criar Administrador</title></head><body>
<div class="login-wrap">
<div class="login-box" style="max-width:420px;">
  <div class="login-logo"><div class="sb-logo">W</div><span>WALZE WMS</span></div>
  <div class="login-sub">Criação do primeiro administrador do sistema</div>
  <div class="f"><label>Nome completo</label><input class="fi" id="nome" placeholder="Ex: João Silva" autofocus></div>
  <div class="f"><label>Login</label><input class="fi" id="login" placeholder="Ex: joao.silva"></div>
  <div class="f"><label>Senha</label><input class="fi" id="senha" type="password" placeholder="Mínimo 4 caracteres"></div>
  <button class="btn bg bfull" onclick="criar()">Criar Administrador</button>
  <div class="err-msg" id="msg"></div>
</div></div>
<script>
async function criar(){
  var n=document.getElementById('nome').value.trim();
  var l=document.getElementById('login').value.trim();
  var s=document.getElementById('senha').value;
  var m=document.getElementById('msg');
  if(!n||!l||!s){m.textContent='Preencha todos os campos.';return;}
  try{
    var r=await fetch('/auth/criar-usuario',{method:'POST',headers:{'Content-Type':'application/json'},
      body:JSON.stringify({nome:n,login:l,senha:s,papel:'ADMIN'})});
    var d=await r.json();
    if(d.detail){m.textContent=d.detail;return;}
    m.style.color='var(--gtxt)';m.textContent='✓ Administrador criado! Redirecionando...';
    setTimeout(function(){window.location.href='/login';},1200);
  }catch(e){m.textContent='Erro de conexão.';}
}
</script></body></html>""")


# ══════════════════════════════════════════════════════════════════
#  UTILITÁRIOS
# ══════════════════════════════════════════════════════════════════
@app.get("/seed")
def seed(db: Session = Depends(get_db)):
    enderecos = []
    for nivel in ["1"]:
        for pos in range(14, 29, 2):
            for frente in ["A", "B"]:
                sufixo = "" if frente == "A" else "F"
                cod = f"R07 0{pos:02d} {nivel}{sufixo}"
                enderecos.append((cod, "R07", nivel + sufixo, str(pos), frente))
    criados = 0
    for cod, rua, pred, and_, frente in enderecos:
        e = db.query(models.Endereco).filter(models.Endereco.codigo == cod).first()
        if e:
            e.rua = rua; e.predio = pred; e.andar = and_; e.frente = frente
            if not e.status_ocupacao:
                e.status_ocupacao = "LIVRE"
        else:
            db.add(models.Endereco(
                codigo=cod, rua=rua, predio=pred, andar=and_, frente=frente,
                comprimento_cm=120, largura_cm=100, altura_cm=200,
                capacidade_total=1, capacidade_usada=0, status_ocupacao="LIVRE"
            ))
            criados += 1
    db.commit()
    return {"status": "ok", "criados": criados, "total": len(enderecos)}


@app.get("/reset-dados")
def reset_dados(db: Session = Depends(get_db)):
    db.query(models.PedidoVolume).delete()
    db.query(models.Palete).delete()
    db.query(models.Endereco).update({"capacidade_usada": 0})
    db.commit()
    return {"status": "ok", "aviso": "Paletes e volumes apagados. Endereços mantidos."}


@app.get("/migrar-banco")
def migrar_banco(db: Session = Depends(get_db)):
    comandos = [
        "ALTER TABLE enderecos ADD COLUMN IF NOT EXISTS status_ocupacao VARCHAR DEFAULT 'LIVRE'",
        "ALTER TABLE usuarios ADD COLUMN IF NOT EXISTS papel VARCHAR DEFAULT 'OPERADOR'",
        "ALTER TABLE usuarios ADD COLUMN IF NOT EXISTS email VARCHAR",
        "ALTER TABLE usuarios ADD COLUMN IF NOT EXISTS telefone VARCHAR",
        "ALTER TABLE usuarios ADD COLUMN IF NOT EXISTS cpf VARCHAR",
        "ALTER TABLE usuarios ADD COLUMN IF NOT EXISTS foto_url VARCHAR",
        "ALTER TABLE usuarios ADD COLUMN IF NOT EXISTS criado_em TIMESTAMP DEFAULT now()",
        "ALTER TABLE pedidos_volumes ADD COLUMN IF NOT EXISTS status VARCHAR DEFAULT 'EM_ANDAMENTO'",
    ]

    erros = []

    for c in comandos:
        try:
            db.execute(text(c))
        except Exception as e:
            erros.append(str(e))

    db.commit()

    return {
        "status": "ok",
        "erros": erros
    }

@app.post("/paletes/finalizar/{codigo_palete}")
def finalizar_palete(
    codigo_palete: str,
    db: Session = Depends(get_db)
):

    palete = (
        db.query(models.Palete)
        .filter(models.Palete.codigo == codigo_palete)
        .first()
    )

    if not palete:
        raise HTTPException(
            status_code=404,
            detail="Palete não encontrado"
        )

    palete.status = "FINALIZADO"

    db.query(models.PedidoVolume).filter(
        models.PedidoVolume.palete_codigo == codigo_palete
    ).update(
        {"status": "FINALIZADO"},
        synchronize_session=False
    )

    db.commit()

    return {
        "ok": True,
        "palete": codigo_palete,
        "status": "FINALIZADO"
    }