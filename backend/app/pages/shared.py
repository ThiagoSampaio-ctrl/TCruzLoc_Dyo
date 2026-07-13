import base64 as _b64, os as _os

def _load_icon(name):
    try:
        p = _os.path.join(_os.path.dirname(__file__), '..', '..', 'pwa', name)
        if _os.path.exists(p):
            return open(p, 'rb').read()
    except Exception:
        pass
    return _b64.b64decode(
        "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNk"
        "YPhfDwAChwGA60e6kgAAAABJRU5ErkJggg==")

ICON_192 = _load_icon('icon-192.png')
ICON_512 = _load_icon('icon-512.png')

SHARED = """
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
.tb-av{width:30px;height:30px;border-radius:50%;background:var(--bdim);
  border:1px solid var(--blue);display:flex;align-items:center;justify-content:center;
  font-size:10px;font-weight:600;color:var(--btxt);flex-shrink:0;overflow:hidden;}
.tb-av img{width:100%;height:100%;object-fit:cover;}
.tb-uname{font-size:12.5px;font-weight:600;color:var(--txt);}
.tb-urole{font-size:10px;color:var(--txt3);}
.content{padding:22px 24px;flex:1;}
.card{background:var(--s1);border:1px solid var(--br);border-radius:var(--rl);padding:20px;margin-bottom:14px;}
.ct{font-size:10px;letter-spacing:.08em;text-transform:uppercase;color:var(--txt3);margin-bottom:12px;font-weight:600;}
.f{margin-bottom:12px;}
.f label{display:block;font-size:10.5px;letter-spacing:.04em;text-transform:uppercase;color:var(--txt3);margin-bottom:6px;font-weight:600;}
.fi{width:100%;padding:11px 13px;background:var(--bg);color:var(--txt);border:1px solid var(--br);border-radius:var(--r);font-family:var(--mono);font-size:14px;transition:.12s;outline:none;}
.fi:focus{border-color:var(--green);box-shadow:0 0 0 3px var(--gdim);}
.fi::placeholder{color:var(--txt3);}
.g2{display:grid;grid-template-columns:1fr 1fr;gap:12px;}
.g3{display:grid;grid-template-columns:repeat(3,1fr);gap:10px;}
.btn{display:inline-flex;align-items:center;justify-content:center;gap:6px;padding:9px 16px;border:none;border-radius:var(--r);font-family:var(--font);font-size:13px;font-weight:600;cursor:pointer;transition:.12s;white-space:nowrap;}
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
.term{background:var(--bg);border:1px solid var(--br);border-radius:var(--rl);padding:16px;font-family:var(--mono);font-size:13px;color:var(--gtxt);white-space:pre-wrap;min-height:90px;line-height:1.7;position:relative;}
.term::before{content:'OUTPUT';position:absolute;top:7px;right:10px;font-size:9px;color:var(--txt3);letter-spacing:.1em;}
.sb-status{min-height:24px;display:flex;align-items:center;gap:6px;font-size:12px;padding:3px 0;}
.sb-status.ok{color:var(--gtxt);}.sb-status.err{color:var(--rtxt);}
.sb-status.warn{color:var(--atxt);}.sb-status.info{color:var(--txt3);}
.dot{width:5px;height:5px;border-radius:50%;background:currentColor;flex-shrink:0;}
.chips{display:flex;flex-wrap:wrap;gap:6px;margin-top:8px;}
.chip{padding:3px 10px;background:var(--s2);border:1px solid var(--br);border-radius:20px;font-family:var(--mono);font-size:11px;color:var(--txt3);cursor:pointer;transition:.12s;}
.chip:hover{border-color:var(--green);color:var(--gtxt);}
.sw{position:relative;}
.sw input{width:100%;padding:14px 14px 14px 40px;font-size:16px;font-family:var(--mono);background:var(--s1);color:var(--txt);border:1px solid var(--br);border-radius:var(--rl);outline:none;transition:.12s;}
.sw input:focus{border-color:var(--green);box-shadow:0 0 0 3px var(--gdim);}
.sw .si{position:absolute;left:14px;top:50%;transform:translateY(-50%);font-size:15px;color:var(--txt3);pointer-events:none;}
.tw{overflow-x:auto;}
table{width:100%;border-collapse:collapse;font-size:12px;}
th{text-align:left;padding:9px 10px;font-size:9.5px;letter-spacing:.06em;text-transform:uppercase;color:var(--txt3);border-bottom:1px solid var(--br);font-weight:600;}
td{padding:9px 10px;border-bottom:1px solid var(--br);color:var(--txt);}
tr:last-child td{border-bottom:none;}
tr:hover td{background:var(--s2);}
.bk{display:inline-block;padding:3px 8px;border-radius:5px;font-family:var(--mono);font-size:10px;font-weight:600;}
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
.stat{flex:1;min-width:88px;background:var(--s1);border:1px solid var(--br);border-radius:var(--r);padding:11px 13px;}
.sl{font-size:9.5px;text-transform:uppercase;letter-spacing:.06em;color:var(--txt3);margin-bottom:4px;}
.sv{font-family:var(--mono);font-size:19px;font-weight:600;color:var(--gtxt);}
.sv.red{color:var(--rtxt);}
.divider{height:1px;background:var(--br);margin:18px 0;}
#toast{position:fixed;bottom:18px;right:18px;background:var(--s1);border:1px solid var(--br);border-radius:var(--rl);padding:10px 14px;font-size:12px;z-index:999;transform:translateY(60px);opacity:0;transition:.2s cubic-bezier(.4,0,.2,1);pointer-events:none;max-width:280px;}
#toast.show{transform:translateY(0);opacity:1;}
#toast.ok{border-color:var(--green);color:var(--gtxt);}
#toast.err{border-color:var(--red);color:var(--rtxt);}
.modal-bg{display:none;position:fixed;inset:0;background:#000c;z-index:200;align-items:center;justify-content:center;}
.modal-bg.open{display:flex;}
.modal{background:var(--s1);border:1px solid var(--br);border-radius:var(--rl);padding:24px;width:100%;max-width:440px;margin:16px;}
.modal h3{font-size:15px;font-weight:600;color:var(--txt);margin-bottom:16px;}
.metric-card{background:var(--s1);border:1px solid var(--br);border-radius:var(--rl);padding:16px 18px;display:flex;align-items:center;justify-content:space-between;}
.metric-card .num{font-family:var(--mono);font-size:26px;font-weight:700;line-height:1;}
.metric-card .lbl{font-size:11.5px;color:var(--txt2);margin-top:4px;font-weight:500;}
.metric-card .trend{font-size:17px;}
.map-toolbar{display:flex;gap:10px;align-items:center;margin-bottom:16px;flex-wrap:wrap;}
.map-select{padding:9px 13px;background:var(--s1);color:var(--txt);border:1px solid var(--br);border-radius:var(--r);font-size:13px;outline:none;font-family:var(--font);cursor:pointer;}
.map-grid-label{font-family:var(--mono);font-size:12px;color:var(--txt2);font-weight:600;margin-bottom:12px;letter-spacing:.04em;}
.map-wrap{overflow-x:auto;padding-bottom:6px;}
.map-grid{display:inline-block;}
.map-row{display:flex;gap:6px;margin-bottom:6px;align-items:center;}
.map-rowlabel{width:24px;height:46px;display:flex;align-items:center;justify-content:center;background:var(--s2);border-radius:6px;font-size:11px;font-weight:700;color:var(--txt2);flex-shrink:0;}
.map-cell{width:70px;height:46px;border-radius:6px;display:flex;align-items:center;justify-content:center;font-family:var(--mono);font-size:10.5px;font-weight:600;cursor:pointer;transition:.12s;flex-shrink:0;border:1.5px solid transparent;}
.map-cell:hover{transform:scale(1.05);}
.map-cell.empty{background:var(--s2);border:1px dashed var(--br);color:transparent;cursor:default;}
.map-cell.empty:hover{transform:none;}
.map-cell.livre{background:#16331f;color:var(--gtxt);border-color:var(--green);}
.map-cell.parcial{background:#332a10;color:var(--atxt);border-color:var(--amber);}
.map-cell.ocupado{background:#3a1414;color:var(--rtxt);border-color:var(--red);}
.map-cell.bloqueado{background:var(--s2);color:var(--txt3);border-color:var(--br2);}
.map-cell.selected{outline:2px solid var(--txt);outline-offset:1px;}
.map-colheader{width:70px;text-align:center;font-size:11px;color:var(--txt3);font-family:var(--mono);flex-shrink:0;}
.map-legend{display:flex;gap:20px;flex-wrap:wrap;margin-top:18px;padding-top:16px;border-top:1px solid var(--br);}
.map-legend-item{display:flex;align-items:center;gap:8px;}
.map-legend-dot{width:13px;height:13px;border-radius:3px;flex-shrink:0;}
.map-legend-txt{font-size:11.5px;}
.map-legend-txt b{display:block;font-size:12px;color:var(--txt);}
.map-legend-txt span{color:var(--txt3);font-size:10.5px;}
.detail-panel{background:var(--s1);border:1px solid var(--br);border-radius:var(--rl);padding:18px;position:sticky;top:80px;}
.detail-head{display:flex;align-items:center;justify-content:space-between;margin-bottom:14px;}
.detail-close{cursor:pointer;color:var(--txt3);font-size:16px;background:none;border:none;}
.detail-close:hover{color:var(--txt);}
.detail-code{font-family:var(--mono);font-size:19px;font-weight:700;color:var(--txt);margin:8px 0 14px;}
.detail-row{display:flex;justify-content:space-between;padding:8px 0;border-bottom:1px solid var(--br);font-size:12.5px;}
.detail-row:last-child{border-bottom:none;}
.detail-row span:first-child{color:var(--txt3);}
.detail-row span:last-child{color:var(--txt);font-weight:600;font-family:var(--mono);}
.profile-photo{width:88px;height:88px;border-radius:50%;background:var(--s2);border:2px solid var(--br2);display:flex;align-items:center;justify-content:center;font-size:30px;font-weight:700;color:var(--btxt);overflow:hidden;flex-shrink:0;}
.profile-photo img{width:100%;height:100%;object-fit:cover;}
.login-wrap{display:flex;align-items:center;justify-content:center;min-height:100vh;padding:20px;background:radial-gradient(circle at 20% 20%, #122218 0%, var(--bg) 55%);}
.login-box{background:var(--s1);border:1px solid var(--br);border-radius:var(--rl);padding:36px;width:100%;max-width:380px;}
.login-logo{display:flex;align-items:center;gap:10px;margin-bottom:6px;}
.login-logo .sb-logo{width:34px;height:34px;font-size:17px;}
.login-logo span{font-size:18px;font-weight:700;color:var(--txt);}
.login-sub{color:var(--txt3);font-size:12px;margin-bottom:26px;}
.err-msg{color:var(--rtxt);font-size:12px;margin-top:8px;min-height:18px;}
@media (max-width:900px){
  .sidebar{position:fixed;left:-100%;top:0;height:100vh;transition:.2s;box-shadow:0 0 40px #000a;z-index:9999;}
  .sidebar.open{left:0;}
  #menuBtn{display:block !important;}
  .content{padding:16px;}
  .topbar{padding:12px 16px;}
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
    <div class="sb-logout" onclick="sair()"><span>↩</span> Sair</div>
  </div>
</div>"""

_TOPBAR_TPL = """<div class="topbar">
  <button id="menuBtn" onclick="document.getElementById('sidebar').classList.toggle('open')"
    style="display:none;background:none;border:none;font-size:22px;color:var(--txt);cursor:pointer;margin-right:8px;">☰</button>
  <div class="tb-title">
    <div class="tb-icon" style="background:{iconbg};">{icon}</div>
    <div><div class="tb-h1">{title}</div><div class="tb-sub">{subtitle}</div></div>
  </div>
  <div class="tb-right">
    <span style="font-family:var(--mono);font-size:11px;color:var(--txt3);" id="clk"></span>
    <a href="/perfil" class="tb-av" id="navAv" style="text-decoration:none;"></a>
    <div><div class="tb-uname" id="navUser"></div><div class="tb-urole" id="navRole"></div></div>
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
      if(foto){av.innerHTML='<img src="'+foto+'" style="width:30px;height:30px;border-radius:50%;object-fit:cover;">';}
      else{
        av.style.cssText='width:30px;height:30px;border-radius:50%;background:var(--bdim);border:1px solid var(--blue);display:flex;align-items:center;justify-content:center;font-size:10px;font-weight:600;color:var(--btxt);';
        var p=u.trim().split(' ');
        av.textContent=p.length>=2?(p[0][0]+p[p.length-1][0]).toUpperCase():u.substring(0,2).toUpperCase();
      }
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
    clearTimeout(el._t);el._t=setTimeout(function(){el.className='';},3000);};
  window.sair=function(){
    localStorage.removeItem('wms_token');localStorage.removeItem('wms_user');
    localStorage.removeItem('wms_papel');localStorage.removeItem('wms_foto');
    window.location.href='/login';};
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
            .replace('{icon}', icon).replace('{iconbg}', iconbg)
            .replace('{title}', title).replace('{subtitle}', subtitle))


def shell_open(active: str, icon: str, iconbg: str, title: str, subtitle: str) -> str:
    return (f'<div class="shell">{sidebar(active)}<div class="main">'
            f'{topbar(icon, iconbg, title, subtitle)}<div class="content">')


def shell_close() -> str:
    return '</div></div></div>'