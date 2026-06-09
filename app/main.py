import base64 as _b64, json as _json, os as _os
from fastapi import FastAPI, Depends, HTTPException, Header
from fastapi.responses import HTMLResponse, JSONResponse, Response
from sqlalchemy.orm import Session

from app.database import engine, Base, get_db, ping_db
from app import models, schema, crud
from app.auth import (criar_usuario, fazer_login,
                      get_usuario_atual, hash_senha)

Base.metadata.create_all(bind=engine)
app = FastAPI(title="WMS — TCruzLoc", version="3.0")

# ── ícones PWA ──
def _load_icon(name):
    try:
        p = _os.path.join(_os.path.dirname(__file__), '..', 'pwa', name)
        if _os.path.exists(p):
            return open(p,'rb').read()
    except: pass
    return _b64.b64decode("iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNkYPhfDwAChwGA60e6kgAAAABJRU5ErkJggg==")

_ICON_192 = _load_icon('icon-192.png')
_ICON_512 = _load_icon('icon-512.png')

_MANIFEST = {"name":"WMS TCruzLoc","short_name":"TCruzLoc","description":"Sistema WMS","start_url":"/app","display":"standalone","background_color":"#0a0a0a","theme_color":"#00e676","orientation":"portrait-primary","scope":"/","lang":"pt-BR","icons":[{"src":"/icon-192.png","sizes":"192x192","type":"image/png","purpose":"any maskable"},{"src":"/icon-512.png","sizes":"512x512","type":"image/png","purpose":"any maskable"}],"shortcuts":[{"name":"Conferente","url":"/conferente-v2"},{"name":"Operação","url":"/operacao"},{"name":"Volumes","url":"/gerenciar-volumes"},{"name":"Histórico","url":"/historico"}]}

_SW = "const CACHE='wms-v2';const PAGES=['/app','/login','/operacao','/conferente-v2','/gerenciar-volumes','/historico','/manifest.json'];self.addEventListener('install',e=>{e.waitUntil(caches.open(CACHE).then(c=>c.addAll(PAGES)).then(()=>self.skipWaiting()));});self.addEventListener('activate',e=>{e.waitUntil(caches.keys().then(ks=>Promise.all(ks.filter(k=>k!==CACHE).map(k=>caches.delete(k)))).then(()=>self.clients.claim()));});self.addEventListener('fetch',e=>{const isApi=['/pedidos','/paletes','/enderecos','/pedidos-volume','/auth','/historico-api'].some(p=>e.request.url.includes(p));if(isApi){e.respondWith(fetch(e.request).catch(()=>new Response(JSON.stringify({detail:'Sem conexão.'}),{status:503,headers:{'Content-Type':'application/json'}})));return;}e.respondWith(fetch(e.request).then(r=>{if(r.ok){const c=r.clone();caches.open(CACHE).then(ch=>ch.put(e.request,c));}return r;}).catch(()=>caches.match(e.request)));});"

# ── CSS/JS compartilhados ──
_SHARED = """
<meta charset="UTF-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<link rel="manifest" href="/manifest.json">
<meta name="theme-color" content="#00e676">
<meta name="apple-mobile-web-app-capable" content="yes">
<meta name="apple-mobile-web-app-status-bar-style" content="black-translucent">
<meta name="apple-mobile-web-app-title" content="TCruzLoc">
<link rel="apple-touch-icon" href="/icon-192.png">
<link rel="preconnect" href="https://fonts.googleapis.com">
<link href="https://fonts.googleapis.com/css2?family=IBM+Plex+Mono:wght@400;600&family=IBM+Plex+Sans:wght@400;500;600&display=swap" rel="stylesheet">
<script>
if("serviceWorker"in navigator)window.addEventListener("load",()=>navigator.serviceWorker.register("/service-worker.js"));
function getToken(){return localStorage.getItem('wms_token')||'';}
function getUser(){return localStorage.getItem('wms_user')||'';}
function authHeaders(){return{'Content-Type':'application/json','Authorization':'Bearer '+getToken()};}
function checkAuth(){if(!getToken()){window.location.href='/login';return false;}return true;}
</script>
<style>
:root{--bg:#0a0a0a;--surface:#111;--surface2:#181818;--border:#222;--green:#00e676;--green-dim:#00e67620;--green-text:#00ff88;--blue:#2979ff;--blue-dim:#2979ff18;--red:#ff1744;--red-dim:#ff174420;--amber:#ffab00;--amber-dim:#ffab0018;--text:#e8e8e8;--muted:#666;--muted2:#444;--font:'IBM Plex Sans',sans-serif;--mono:'IBM Plex Mono',monospace;--r:10px;--r-sm:6px;}
*{box-sizing:border-box;margin:0;padding:0;}html,body{background:var(--bg);color:var(--text);font-family:var(--font);min-height:100vh;}a{color:inherit;text-decoration:none;}
nav{display:flex;align-items:center;background:var(--surface);border-bottom:1px solid var(--border);padding:0 20px;height:56px;position:sticky;top:0;z-index:100;}
.nav-brand{font-family:var(--mono);font-size:14px;font-weight:600;color:var(--green-text);margin-right:24px;display:flex;align-items:center;gap:8px;}
.nav-brand::before{content:'';display:block;width:7px;height:7px;background:var(--green);border-radius:50%;box-shadow:0 0 8px var(--green);}
.nav-links{display:flex;gap:2px;flex:1;overflow-x:auto;}
.nav-link{padding:5px 12px;border-radius:var(--r-sm);font-size:13px;color:var(--muted);transition:.15s;cursor:pointer;border:1px solid transparent;white-space:nowrap;}
.nav-link:hover{color:var(--text);background:var(--surface2);}
.nav-link.active{color:var(--green-text);background:var(--green-dim);border-color:var(--green-dim);}
.nav-right{display:flex;align-items:center;gap:10px;margin-left:auto;flex-shrink:0;}
.nav-user{font-size:12px;color:var(--muted);font-family:var(--mono);}
.nav-clock{font-family:var(--mono);font-size:12px;color:var(--muted2);}
.page{max-width:900px;margin:0 auto;padding:28px 16px;}
.page-wide{max-width:1200px;margin:0 auto;padding:28px 16px;}
.card{background:var(--surface);border:1px solid var(--border);border-radius:var(--r);padding:24px;margin-bottom:18px;}
.card-title{font-size:11px;letter-spacing:.08em;text-transform:uppercase;color:var(--muted);margin-bottom:14px;font-weight:500;}
.field{margin-bottom:14px;}
.field label{display:block;font-size:11px;letter-spacing:.06em;text-transform:uppercase;color:var(--muted);margin-bottom:7px;font-weight:500;}
.field input{width:100%;padding:12px 14px;background:var(--bg);color:var(--green-text);border:1px solid var(--border);border-radius:var(--r-sm);font-family:var(--mono);font-size:16px;transition:.15s;outline:none;}
.field input:focus{border-color:var(--green);box-shadow:0 0 0 3px var(--green-dim);}
.field input::placeholder{color:var(--muted2);}
.grid-2{display:grid;grid-template-columns:1fr 1fr;gap:14px;}
.grid-3{display:grid;grid-template-columns:repeat(3,1fr);gap:12px;}
.btn{display:inline-flex;align-items:center;justify-content:center;gap:7px;padding:11px 20px;border:none;border-radius:var(--r-sm);font-family:var(--font);font-size:14px;font-weight:600;cursor:pointer;transition:.15s;white-space:nowrap;}
.btn:disabled{opacity:.4;cursor:not-allowed;}
.btn:active:not(:disabled){transform:scale(.97);}
.btn-green{background:var(--green);color:#000;}
.btn-green:hover:not(:disabled){background:#00ff9a;}
.btn-blue{background:var(--blue);color:#fff;}
.btn-blue:hover:not(:disabled){background:#448aff;}
.btn-amber{background:var(--amber);color:#000;}
.btn-amber:hover:not(:disabled){background:#ffc107;}
.btn-ghost{background:var(--surface2);color:var(--text);border:1px solid var(--border);}
.btn-ghost:hover:not(:disabled){border-color:var(--muted);}
.btn-danger{background:var(--red-dim);color:var(--red);border:1px solid var(--red-dim);}
.btn-danger:hover:not(:disabled){background:var(--red);color:#fff;}
.btn-row{display:flex;gap:8px;flex-wrap:wrap;}
.btn-full{width:100%;}
.terminal{background:var(--bg);border:1px solid var(--border);border-radius:var(--r);padding:18px;font-family:var(--mono);font-size:14px;color:var(--green-text);white-space:pre-wrap;min-height:100px;line-height:1.7;position:relative;}
.terminal::before{content:'OUTPUT';position:absolute;top:7px;right:10px;font-size:10px;color:var(--muted2);letter-spacing:.1em;}
.status-bar{min-height:26px;display:flex;align-items:center;gap:7px;font-size:13px;padding:3px 0;}
.status-bar.ok{color:var(--green-text);}.status-bar.err{color:var(--red);}.status-bar.warn{color:var(--amber);}.status-bar.info{color:var(--muted);}
.dot{width:6px;height:6px;border-radius:50%;background:currentColor;flex-shrink:0;}
.chips{display:flex;flex-wrap:wrap;gap:7px;margin-top:10px;}
.chip{padding:4px 11px;background:var(--surface2);border:1px solid var(--border);border-radius:20px;font-family:var(--mono);font-size:12px;color:var(--muted);cursor:pointer;transition:.15s;}
.chip:hover{border-color:var(--green);color:var(--green-text);}
.search-wrap{position:relative;}
.search-wrap input{width:100%;padding:18px 18px 18px 48px;font-size:20px;font-family:var(--mono);background:var(--surface);color:var(--green-text);border:1px solid var(--border);border-radius:var(--r);outline:none;transition:.15s;}
.search-wrap input:focus{border-color:var(--green);box-shadow:0 0 0 3px var(--green-dim);}
.search-wrap .si{position:absolute;left:16px;top:50%;transform:translateY(-50%);font-size:18px;color:var(--muted);pointer-events:none;}
.search-wrap input.ok{border-color:var(--green);}
.search-wrap input.err{border-color:var(--red);}
.tbl-wrap{overflow-x:auto;}
table{width:100%;border-collapse:collapse;font-size:13px;}
th{text-align:left;padding:9px 11px;font-size:10px;letter-spacing:.08em;text-transform:uppercase;color:var(--muted);border-bottom:1px solid var(--border);font-weight:500;}
td{padding:9px 11px;border-bottom:1px solid var(--border);color:var(--text);}
tr:last-child td{border-bottom:none;}tr:hover td{background:var(--surface2);}
.badge{display:inline-block;padding:2px 7px;border-radius:4px;font-family:var(--mono);font-size:11px;font-weight:600;background:var(--blue-dim);color:#82b1ff;}
.badge-green{background:var(--green-dim);color:var(--green-text);}
.badge-red{background:var(--red-dim);color:#ff8a80;}
.badge-amber{background:var(--amber-dim);color:#ffd740;}
input[type=checkbox]{width:15px;height:15px;accent-color:var(--green);cursor:pointer;}
.stats{display:flex;flex-wrap:wrap;gap:10px;margin-bottom:20px;}
.stat{flex:1;min-width:100px;background:var(--surface);border:1px solid var(--border);border-radius:var(--r);padding:12px 14px;}
.stat-label{font-size:10px;text-transform:uppercase;letter-spacing:.08em;color:var(--muted);margin-bottom:5px;}
.stat-value{font-family:var(--mono);font-size:20px;font-weight:600;color:var(--green-text);}
.stat-value.red{color:var(--red);}
.divider{height:1px;background:var(--border);margin:20px 0;}
#toast{position:fixed;bottom:20px;right:20px;background:var(--surface);border:1px solid var(--border);border-radius:var(--r);padding:11px 16px;font-size:13px;z-index:999;transform:translateY(70px);opacity:0;transition:.25s cubic-bezier(.4,0,.2,1);pointer-events:none;max-width:300px;}
#toast.show{transform:translateY(0);opacity:1;}#toast.ok{border-color:var(--green);color:var(--green-text);}#toast.err{border-color:var(--red);color:var(--red);}
.modal-bg{display:none;position:fixed;inset:0;background:#000a;z-index:200;align-items:center;justify-content:center;}
.modal-bg.open{display:flex;}
.modal{background:var(--surface);border:1px solid var(--border);border-radius:var(--r);padding:28px;width:100%;max-width:460px;margin:16px;}
.modal h3{font-size:16px;font-weight:600;color:var(--text);margin-bottom:18px;}
</style>
"""

_NAV_TPL = """<nav>
  <div class="nav-brand">WMS · TCruzLoc</div>
  <div class="nav-links">
    <a class="nav-link{a}" href="/app">Início</a>
    <a class="nav-link{b}" href="/conferente-v2">Conferente</a>
    <a class="nav-link{c}" href="/operacao">Operação</a>
    <a class="nav-link{d}" href="/gerenciar-volumes">Volumes</a>
    <a class="nav-link{e}" href="/historico">Histórico</a>
  </div>
  <div class="nav-right">
    <span class="nav-user" id="navUser"></span>
    <span class="nav-clock" id="clk"></span>
    <button class="btn btn-ghost" style="padding:5px 10px;font-size:12px;" onclick="sair()">Sair</button>
  </div>
</nav>
<div id="toast"></div>
<script>
(function(){
  if(!localStorage.getItem('wms_token')&&window.location.pathname!=='/login'){window.location.href='/login';return;}
  document.addEventListener('DOMContentLoaded',function(){
    var el=document.getElementById('navUser');
    if(el)el.textContent=localStorage.getItem('wms_user')||'';
  });
  function tick(){var d=new Date();var el=document.getElementById('clk');if(el)el.textContent=d.toLocaleDateString('pt-BR')+' '+d.toLocaleTimeString('pt-BR');}
  setInterval(tick,1000);tick();
  window.toast=function(msg,type){var t=document.getElementById('toast');t.textContent=msg;t.className='show '+(type||'ok');clearTimeout(t._t);t._t=setTimeout(()=>t.className='',3000);};
  window.sair=function(){localStorage.removeItem('wms_token');localStorage.removeItem('wms_user');window.location.href='/login';};
})();
</script>"""

def nav(active):
    m = {'home':'a','conf':'b','oper':'c','vol':'d','hist':'e'}
    t = _NAV_TPL
    for k,v in m.items():
        t = t.replace('{'+v+'}', ' active' if active==k else '')
    return t

# ══════════════════════════════════════════════════════════════════
#  ROTAS PWA
# ══════════════════════════════════════════════════════════════════
@app.get("/manifest.json")
def pwa_manifest():
    return Response(content=_json.dumps(_MANIFEST,ensure_ascii=False),media_type="application/manifest+json")

@app.get("/service-worker.js")
def pwa_sw():
    return Response(content=_SW,media_type="application/javascript")

@app.get("/icon-192.png")
def pwa_icon_192():
    return Response(content=_ICON_192,media_type="image/png")

@app.get("/icon-512.png")
def pwa_icon_512():
    return Response(content=_ICON_512,media_type="image/png")

# ══════════════════════════════════════════════════════════════════
#  AUTH API
# ══════════════════════════════════════════════════════════════════
@app.post("/auth/login", response_model=schema.LoginResposta)
def api_login(dados: schema.LoginInput, db: Session=Depends(get_db)):
    return fazer_login(db, dados.login, dados.senha)

@app.post("/auth/criar-usuario", response_model=schema.UsuarioResposta)
def api_criar_usuario(dados: schema.UsuarioCriar, db: Session=Depends(get_db),
                      authorization: str=Header(default="")):
    get_usuario_atual(db, authorization)   # só usuário logado pode criar
    return criar_usuario(db, dados.nome, dados.login, dados.senha)

@app.get("/auth/me")
def api_me(db: Session=Depends(get_db), authorization: str=Header(default="")):
    u = get_usuario_atual(db, authorization)
    return {"id": u.id, "nome": u.nome, "login": u.login}

# ══════════════════════════════════════════════════════════════════
#  ROTAS API
# ══════════════════════════════════════════════════════════════════
@app.get("/")
def root(): return {"status":"ok","app":"WMS TCruzLoc v3"}

@app.get("/health")
def health():
    ok = ping_db()
    return JSONResponse(status_code=200 if ok else 503,content={"status":"ok" if ok else "db_error","db":ok})

@app.get("/enderecos",response_model=list[schema.EnderecoResposta])
def listar_enderecos(db:Session=Depends(get_db)): return crud.listar_enderecos(db)

@app.get("/caixas",response_model=list[schema.CaixaResposta])
def listar_caixas(db:Session=Depends(get_db)): return crud.listar_caixas(db)

@app.post("/paletes/manual",response_model=schema.PaleteResposta)
def criar_palete_manual(dados:schema.PaleteManualCriar,db:Session=Depends(get_db),
                        authorization:str=Header(default="")):
    u = get_usuario_atual(db, authorization)
    return crud.criar_ou_usar_palete_manual(db,dados.codigo_palete,dados.codigo_endereco,u)

@app.post("/paletes/auto",response_model=schema.PaleteResposta)
def criar_palete_auto(palete:schema.PaleteCriar,db:Session=Depends(get_db)):
    return crud.criar_palete_auto(db,palete)

@app.get("/paletes",response_model=list[schema.PaleteResposta])
def listar_paletes(db:Session=Depends(get_db)): return crud.listar_paletes(db)

@app.delete("/pedidos-volume/duplicados")
def limpar_dup(db:Session=Depends(get_db)): return crud.limpar_pedidos_duplicados(db)

@app.post("/pedidos-volume/deletar-varios")
def deletar_varios(dados:schema.DeletarVolumes,db:Session=Depends(get_db),
                   authorization:str=Header(default="")):
    u = get_usuario_atual(db, authorization)
    return crud.deletar_varios_pedidos_volume(db,dados.ids,u)

@app.post("/pedidos-volume/transferir")
def transferir(dados:schema.TransferirVolumes,db:Session=Depends(get_db),
               authorization:str=Header(default="")):
    u = get_usuario_atual(db, authorization)
    return crud.transferir_volumes(db,dados,u)

@app.get("/pedidos-volume")
def listar_volumes(db:Session=Depends(get_db)): return crud.listar_pedidos_volume(db)

@app.post("/pedidos-volume",response_model=schema.PedidoVolumeResposta)
def criar_volume(pedido:schema.PedidoVolumeCriar,db:Session=Depends(get_db),
                 authorization:str=Header(default="")):
    u = get_usuario_atual(db, authorization)
    return crud.criar_pedido_volume(db,pedido,u)

@app.delete("/pedidos-volume/{volume_id}")
def deletar_volume(volume_id:int,db:Session=Depends(get_db),
                   authorization:str=Header(default="")):
    u = get_usuario_atual(db, authorization)
    return crud.deletar_pedido_volume(db,volume_id,u)

@app.get("/enderecos/{codigo}/detalhes")
def detalhes_endereco(codigo:str,db:Session=Depends(get_db)):
    return crud.detalhes_endereco(db,codigo)

@app.get("/pedidos/{numero_pedido}")
def buscar_pedido(numero_pedido:str,db:Session=Depends(get_db)):
    return crud.buscar_pedido(db,numero_pedido)

@app.get("/historico-api")
def historico_api(db:Session=Depends(get_db),
                  authorization:str=Header(default="")):
    get_usuario_atual(db, authorization)
    items = crud.listar_historico(db)
    result = []
    for h in items:
        result.append({
            "id": h.id,
            "usuario_nome": h.usuario_nome or "—",
            "acao": h.acao,
            "numero_pedido": h.numero_pedido or "—",
            "volume_atual": h.volume_atual,
            "volume_total": h.volume_total,
            "palete_codigo": h.palete_codigo or "—",
            "endereco_de": h.endereco_de or "—",
            "endereco_para": h.endereco_para or "—",
            "detalhe_extra": h.detalhe_extra or "",
            "criado_em": h.criado_em.strftime("%d/%m/%Y %H:%M:%S") if h.criado_em else "—",
        })
    return result

# ══════════════════════════════════════════════════════════════════
#  PÁGINA: LOGIN
# ══════════════════════════════════════════════════════════════════
@app.get("/login",response_class=HTMLResponse)
def pg_login():
    return f"""<!DOCTYPE html><html lang="pt-BR"><head>{_SHARED}<title>WMS · Login</title>
<style>
.login-wrap{{display:flex;align-items:center;justify-content:center;min-height:100vh;padding:20px;}}
.login-box{{background:var(--surface);border:1px solid var(--border);border-radius:var(--r);padding:40px 36px;width:100%;max-width:400px;}}
.login-logo{{font-family:var(--mono);font-size:22px;font-weight:600;color:var(--green-text);margin-bottom:6px;display:flex;align-items:center;gap:10px;}}
.login-logo::before{{content:'';display:block;width:10px;height:10px;background:var(--green);border-radius:50%;box-shadow:0 0 10px var(--green);}}
.login-sub{{color:var(--muted);font-size:13px;margin-bottom:28px;}}
.err-msg{{color:var(--red);font-size:13px;margin-top:10px;min-height:20px;}}
</style></head><body>
<div class="login-wrap">
<div class="login-box">
  <div class="login-logo">WMS · TCruzLoc</div>
  <div class="login-sub">Sistema de Gerenciamento de Armazém</div>
  <div class="field"><label>Usuário</label><input id="login" placeholder="seu.login" autofocus onkeydown="if(event.key==='Enter')document.getElementById('senha').focus()"></div>
  <div class="field"><label>Senha</label><input id="senha" type="password" placeholder="••••••••" onkeydown="if(event.key==='Enter')entrar()"></div>
  <button class="btn btn-green btn-full" style="margin-top:8px;" onclick="entrar()">Entrar</button>
  <div class="err-msg" id="err"></div>
</div></div>
<script>
async function entrar(){{
  var l=document.getElementById('login').value.trim();
  var s=document.getElementById('senha').value;
  var e=document.getElementById('err');
  if(!l||!s){{e.textContent='Preencha usuário e senha.';return;}}
  e.textContent='';
  try{{
    var r=await fetch('/auth/login',{{method:'POST',headers:{{'Content-Type':'application/json'}},body:JSON.stringify({{login:l,senha:s}})}});
    var d=await r.json();
    if(d.detail){{e.textContent=d.detail;return;}}
    localStorage.setItem('wms_token',d.token);
    localStorage.setItem('wms_user',d.nome);
    window.location.href='/app';
  }}catch(ex){{e.textContent='Erro de conexão.';}}
}}
// Se já estiver logado, vai direto
if(localStorage.getItem('wms_token'))window.location.href='/app';
</script></body></html>"""

# ══════════════════════════════════════════════════════════════════
#  PÁGINA: HOME
# ══════════════════════════════════════════════════════════════════
@app.get("/app",response_class=HTMLResponse)
def pg_home():
    return f"""<!DOCTYPE html><html lang="pt-BR"><head>{_SHARED}<title>WMS · Início</title></head><body>
{nav('home')}
<div class="page">
  <div style="margin-bottom:28px;">
    <h1 style="font-family:var(--mono);font-size:26px;font-weight:600;color:var(--green-text);margin-bottom:6px;">WMS · TCruzLoc_Dyo</h1>
    <p style="color:var(--muted);font-size:13px;">Sistema de gerenciamento de armazém</p>
  </div>
  <div style="display:grid;grid-template-columns:repeat(auto-fit,minmax(220px,1fr));gap:14px;">
    <a href="/conferente-v2"><div class="card" style="border-color:#1a2a1a;cursor:pointer;transition:.2s;" onmouseover="this.style.borderColor='var(--green)'" onmouseout="this.style.borderColor='#1a2a1a'">
      <div style="font-size:26px;margin-bottom:10px;">📦</div>
      <div style="font-size:15px;font-weight:600;color:var(--green-text);margin-bottom:5px;">Conferente</div>
      <div style="font-size:12px;color:var(--muted);">Montar paletes e endereçar pedidos.</div>
      <div style="margin-top:14px;font-size:12px;color:var(--green);font-family:var(--mono);">ACESSAR →</div>
    </div></a>
    <a href="/operacao"><div class="card" style="border-color:#1a1a2a;cursor:pointer;transition:.2s;" onmouseover="this.style.borderColor='var(--blue)'" onmouseout="this.style.borderColor='#1a1a2a'">
      <div style="font-size:26px;margin-bottom:10px;">🔍</div>
      <div style="font-size:15px;font-weight:600;color:#82b1ff;margin-bottom:5px;">Operação</div>
      <div style="font-size:12px;color:var(--muted);">Consultar pedidos e endereços.</div>
      <div style="margin-top:14px;font-size:12px;color:var(--blue);font-family:var(--mono);">ACESSAR →</div>
    </div></a>
    <a href="/gerenciar-volumes"><div class="card" style="border-color:#2a1a1a;cursor:pointer;transition:.2s;" onmouseover="this.style.borderColor='var(--amber)'" onmouseout="this.style.borderColor='#2a1a1a'">
      <div style="font-size:26px;margin-bottom:10px;">🗂️</div>
      <div style="font-size:15px;font-weight:600;color:var(--amber);margin-bottom:5px;">Volumes</div>
      <div style="font-size:12px;color:var(--muted);">Gerenciar, transferir e apagar volumes.</div>
      <div style="margin-top:14px;font-size:12px;color:var(--amber);font-family:var(--mono);">ACESSAR →</div>
    </div></a>
    <a href="/historico"><div class="card" style="border-color:#1a1a2a;cursor:pointer;transition:.2s;" onmouseover="this.style.borderColor='#ce93d8'" onmouseout="this.style.borderColor='#1a1a2a'">
      <div style="font-size:26px;margin-bottom:10px;">📋</div>
      <div style="font-size:15px;font-weight:600;color:#ce93d8;margin-bottom:5px;">Histórico</div>
      <div style="font-size:12px;color:var(--muted);">Auditoria completa de todas as ações.</div>
      <div style="margin-top:14px;font-size:12px;color:#ce93d8;font-family:var(--mono);">ACESSAR →</div>
    </div></a>
  </div>
  <div class="divider"></div>
  <div style="display:flex;gap:10px;flex-wrap:wrap;">
    <a href="/seed"><button class="btn btn-ghost" style="font-size:12px;">⚙️ Inicializar Endereços</button></a>
    <a href="/criar-admin"><button class="btn btn-ghost" style="font-size:12px;">👤 Criar Usuário</button></a>
    <a href="/health"><button class="btn btn-ghost" style="font-size:12px;">💚 Status</button></a>
    <a href="/docs"><button class="btn btn-ghost" style="font-size:12px;">📄 API</button></a>
  </div>
  <div style="margin-top:14px;padding:12px 14px;background:var(--surface2);border-radius:var(--r);border:1px solid var(--border);">
    <p style="font-size:12px;color:var(--muted);">📱 <strong style="color:var(--text);">Instalar:</strong> Chrome → ⋮ → Adicionar à tela inicial &nbsp;|&nbsp; Safari → ⬆️ → Adicionar à Tela de Início</p>
  </div>
</div></body></html>"""

# ══════════════════════════════════════════════════════════════════
#  PÁGINA: CRIAR USUÁRIO (formulário simples)
# ══════════════════════════════════════════════════════════════════
@app.get("/criar-admin",response_class=HTMLResponse)
def pg_criar_usuario():
    return f"""<!DOCTYPE html><html lang="pt-BR"><head>{_SHARED}<title>WMS · Criar Usuário</title></head><body>
{nav('home')}
<div class="page">
  <div style="margin-bottom:24px;">
    <h1 style="font-family:var(--mono);font-size:20px;font-weight:600;color:var(--green-text);">Criar Usuário</h1>
  </div>
  <div class="card" style="max-width:420px;">
    <div class="field"><label>Nome completo</label><input id="nome" placeholder="Ex: João Silva" autofocus></div>
    <div class="field"><label>Login</label><input id="login" placeholder="Ex: joao.silva"></div>
    <div class="field"><label>Senha</label><input id="senha" type="password" placeholder="Mínimo 4 caracteres"></div>
    <button class="btn btn-green btn-full" style="margin-top:4px;" onclick="criar()">Criar Usuário</button>
    <div id="msg" style="margin-top:12px;font-size:13px;min-height:20px;"></div>
  </div>
</div>
<script>
async function criar(){{
  var n=document.getElementById('nome').value.trim();
  var l=document.getElementById('login').value.trim();
  var s=document.getElementById('senha').value;
  var m=document.getElementById('msg');
  if(!n||!l||!s){{m.style.color='var(--red)';m.textContent='Preencha todos os campos.';return;}}
  try{{
    var r=await fetch('/auth/criar-usuario',{{method:'POST',headers:authHeaders(),body:JSON.stringify({{nome:n,login:l,senha:s}})}});
    var d=await r.json();
    if(d.detail){{m.style.color='var(--red)';m.textContent=d.detail;}}
    else{{m.style.color='var(--green-text)';m.textContent='✓ Usuário "'+d.login+'" criado!';document.getElementById('nome').value='';document.getElementById('login').value='';document.getElementById('senha').value='';}}
  }}catch(e){{m.style.color='var(--red)';m.textContent='Erro de conexão.';}}
}}
</script></body></html>"""

# ══════════════════════════════════════════════════════════════════
#  PÁGINA: CONFERENTE v2
# ══════════════════════════════════════════════════════════════════
@app.get("/conferente-v2",response_class=HTMLResponse)
def pg_conferente():
    return r"""<!DOCTYPE html><html lang="pt-BR"><head>"""+_SHARED+r"""<title>WMS · Conferente</title></head><body>
"""+nav("conf")+r"""
<div class="page">
  <div style="margin-bottom:20px;">
    <h1 style="font-family:var(--mono);font-size:20px;font-weight:600;color:var(--green-text);">Montagem de Palete</h1>
    <p style="color:var(--muted);font-size:13px;margin-top:3px;">Informe palete e endereço, depois adicione os pedidos.</p>
  </div>
  <div class="card">
    <div class="card-title">Identificação do Palete</div>
    <div class="grid-2">
      <div class="field"><label>Palete</label><input id="palete" placeholder="Ex: PAL001" autofocus></div>
      <div class="field"><label>Endereço</label><input id="endereco" placeholder="Ex: R07 014 1 ou R070141"></div>
    </div>
  </div>
  <div class="card">
    <div class="card-title">Adicionar Pedido</div>
    <div class="field"><label>Número do Pedido</label><input id="pedido" placeholder="Ex: 349596"></div>
    <div class="grid-3">
      <div class="field"><label>Vol. Inicial</label><input id="vol_ini" type="number" min="1" placeholder="1"></div>
      <div class="field"><label>Vol. Final</label><input id="vol_fin" type="number" min="1" placeholder="6"></div>
      <div class="field"><label>Total do Pedido</label><input id="vol_tot" type="number" min="1" placeholder="10"></div>
    </div>
    <div class="btn-row" style="margin-top:6px;">
      <button class="btn btn-green" id="btnAdd" onclick="adicionar()">＋ Adicionar</button>
      <button class="btn btn-blue" id="btnFin" onclick="finalizar()">✓ Finalizar Palete</button>
      <button class="btn btn-ghost" onclick="resetar()">↺ Novo</button>
    </div>
  </div>
  <div class="status-bar info" id="stbar"><div class="dot"></div>Aguardando dados...</div>
  <div class="terminal" id="out">Pedidos adicionados aparecerão aqui...</div>
  <div style="margin-top:10px;display:flex;gap:8px;flex-wrap:wrap;">
    <div class="stat" style="flex:0 0 auto;min-width:110px;"><div class="stat-label">Palete</div><div class="stat-value" id="s-pal" style="font-size:14px;">—</div></div>
    <div class="stat" style="flex:0 0 auto;min-width:110px;"><div class="stat-label">Endereço</div><div class="stat-value" id="s-end" style="font-size:14px;">—</div></div>
    <div class="stat" style="flex:0 0 auto;min-width:80px;"><div class="stat-label">Pedidos</div><div class="stat-value" id="s-nped">0</div></div>
    <div class="stat" style="flex:0 0 auto;min-width:80px;"><div class="stat-label">Volumes</div><div class="stat-value" id="s-nvol">0</div></div>
  </div>
</div>
<script>
var resumo=[],totalVols=0;
function ss(msg,t){var el=document.getElementById('stbar');el.className='status-bar '+(t||'info');el.innerHTML='<div class="dot"></div>'+msg;}
function fmt(n,t){return String(n).padStart(3,'0')+'/'+String(t).padStart(3,'0');}
function upd(){document.getElementById('s-pal').textContent=document.getElementById('palete').value.trim()||'—';document.getElementById('s-end').textContent=document.getElementById('endereco').value.trim()||'—';document.getElementById('s-nped').textContent=new Set(resumo.map(r=>r.pedido)).size;document.getElementById('s-nvol').textContent=totalVols;}
function renderOut(){
  if(!resumo.length){document.getElementById('out').textContent='Pedidos adicionados aparecerão aqui...';return;}
  var ag={};resumo.forEach(r=>{if(!ag[r.pedido])ag[r.pedido]={ini:r.ini,fin:r.fin,tot:r.tot};else{ag[r.pedido].ini=Math.min(ag[r.pedido].ini,r.ini);ag[r.pedido].fin=Math.max(ag[r.pedido].fin,r.fin);}});
  var txt='PALETE:   '+resumo[0].palete+'\nENDEREÇO: '+resumo[0].endereco+'\n\n';
  for(var p in ag){var a=ag[p];txt+=p+'\n  '+fmt(a.ini,a.tot)+' → '+fmt(a.fin,a.tot)+'\n\n';}
  document.getElementById('out').textContent=txt;
}
['palete','endereco','pedido','vol_ini','vol_fin'].forEach(function(id,i){var nx=['endereco','pedido','vol_ini','vol_fin','vol_tot'];document.getElementById(id).addEventListener('keydown',function(e){if(e.key==='Enter'){e.preventDefault();document.getElementById(nx[i]).focus();}});});
document.getElementById('vol_tot').addEventListener('keydown',function(e){if(e.key==='Enter'){e.preventDefault();adicionar();}});
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
    var rP=await fetch('/paletes/manual',{method:'POST',headers:authHeaders(),body:JSON.stringify({codigo_palete:pal,codigo_endereco:end})});
    var dP=await rP.json();
    if(dP.detail){ss('✕ '+dP.detail,'err');toast(dP.detail,'err');document.getElementById('btnAdd').disabled=false;document.getElementById('btnFin').disabled=false;return;}
    ss('Gravando '+(fin-ini+1)+' volume(s)...','info');
    var erros=[];
    for(var i=ini;i<=fin;i++){
      var rV=await fetch('/pedidos-volume',{method:'POST',headers:authHeaders(),body:JSON.stringify({numero_pedido:ped,volume_atual:i,volume_total:tot,palete_codigo:pal})});
      var dV=await rV.json();if(dV.detail)erros.push('Vol '+i+': '+dV.detail);
    }
    if(erros.length)ss('⚠ '+(fin-ini+1-erros.length)+' ok, '+erros.length+' já existiam.','warn');
    else{ss('✓ '+(fin-ini+1)+' volume(s) de '+ped+' adicionados!','ok');toast('Volumes adicionados!');}
    resumo.push({palete:pal,endereco:end,pedido:ped,ini:ini,fin:fin,tot:tot});
    totalVols+=(fin-ini+1-erros.length);renderOut();upd();
    document.getElementById('pedido').value='';document.getElementById('vol_ini').value='';document.getElementById('vol_fin').value='';document.getElementById('vol_tot').value='';document.getElementById('pedido').focus();
  }catch(e){ss('✕ Erro de conexão.','err');toast('Erro de conexão','err');}
  document.getElementById('btnAdd').disabled=false;document.getElementById('btnFin').disabled=false;
}
function finalizar(){
  var pal=document.getElementById('palete').value.trim(),end=document.getElementById('endereco').value.trim();
  if(!pal||!end){ss('⚠ Informe palete e endereço.','warn');return;}
  if(!resumo.length){ss('⚠ Nenhum pedido adicionado.','warn');return;}
  var ag={};resumo.forEach(r=>{if(!ag[r.pedido])ag[r.pedido]={ini:r.ini,fin:r.fin,tot:r.tot};else{ag[r.pedido].ini=Math.min(ag[r.pedido].ini,r.ini);ag[r.pedido].fin=Math.max(ag[r.pedido].fin,r.fin);}});
  var txt='✓ PALETE FINALIZADO\n\nPALETE:   '+pal+'\nENDEREÇO: '+end+'\nSTATUS:   EM USO\n\nRESUMO:\n\n';
  for(var p in ag){var a=ag[p];txt+=p+'\n  '+fmt(a.ini,a.tot)+' → '+fmt(a.fin,a.tot)+'\n\n';}
  document.getElementById('out').textContent=txt;
  ss('Palete finalizado. Clique em "Novo" para recomeçar.','ok');toast('Palete finalizado!');
  document.getElementById('btnAdd').disabled=true;document.getElementById('btnFin').disabled=true;
}
function resetar(){
  resumo=[];totalVols=0;
  ['palete','endereco','pedido','vol_ini','vol_fin','vol_tot'].forEach(id=>document.getElementById(id).value='');
  document.getElementById('out').textContent='Pedidos adicionados aparecerão aqui...';
  document.getElementById('btnAdd').disabled=false;document.getElementById('btnFin').disabled=false;
  ss('Pronto para novo palete.','info');upd();document.getElementById('palete').focus();
}
upd();
</script></body></html>"""

# ══════════════════════════════════════════════════════════════════
#  PÁGINA: OPERAÇÃO
# ══════════════════════════════════════════════════════════════════
@app.get("/operacao",response_class=HTMLResponse)
def pg_operacao():
    return r"""<!DOCTYPE html><html lang="pt-BR"><head>"""+_SHARED+r"""<title>WMS · Operação</title></head><body>
"""+nav("oper")+r"""
<div class="page">
  <div style="margin-bottom:20px;">
    <h1 style="font-family:var(--mono);font-size:20px;font-weight:600;color:#82b1ff;">Consulta Rápida</h1>
    <p style="color:var(--muted);font-size:13px;margin-top:3px;">Bipe ou digite um endereço ou número de pedido.</p>
  </div>
  <div class="search-wrap" style="margin-bottom:14px;">
    <span class="si">⌕</span>
    <input id="q" placeholder="Endereço ou pedido..." autofocus onkeydown="if(event.key==='Enter')buscar()">
  </div>
  <div class="btn-row" style="margin-bottom:18px;">
    <button class="btn btn-blue btn-full" onclick="buscarEndereco()">🔍 Buscar Endereço</button>
    <button class="btn btn-ghost btn-full" style="border-color:var(--green);color:var(--green-text);" onclick="buscarPedido()">📦 Buscar Pedido</button>
  </div>
  <div class="stats">
    <div class="stat"><div class="stat-label">Consultas</div><div class="stat-value" id="nc">0</div></div>
    <div class="stat"><div class="stat-label">Endereços</div><div class="stat-value" id="ne">0</div></div>
    <div class="stat"><div class="stat-label">Pedidos</div><div class="stat-value" id="np">0</div></div>
    <div class="stat"><div class="stat-label">Erros</div><div class="stat-value red" id="nr">0</div></div>
  </div>
  <div class="terminal" id="out">Aguardando leitura...</div>
  <div style="margin-top:14px;">
    <div style="font-size:11px;text-transform:uppercase;letter-spacing:.08em;color:var(--muted);margin-bottom:7px;">Histórico</div>
    <div class="chips" id="hist"></div>
  </div>
</div>
<script>
var nc=0,ne=0,np=0,nr=0,hist=[];
var SOK='https://actions.google.com/sounds/v1/alarms/beep_short.ogg',SERR='https://actions.google.com/sounds/v1/cartoon/pop.ogg';
function beep(u){try{new Audio(u).play();}catch(e){}}
function flash(c){var el=document.getElementById('q');el.className=c;setTimeout(()=>el.className='',800);}
function addHist(v){if(!v)return;hist=[...new Set([v,...hist])].slice(0,12);document.getElementById('hist').innerHTML=hist.map(h=>`<div class="chip" onclick="rebuscar('${h}')">${h}</div>`).join('');nc++;document.getElementById('nc').textContent=nc;}
function rebuscar(v){document.getElementById('q').value=v;buscar();}
function buscar(){var v=document.getElementById('q').value.trim().toUpperCase();if(!v)return;if(v.match(/^R[0-9]/)||v.startsWith('R '))buscarEndereco();else buscarPedido();}
var _t;document.getElementById('q').addEventListener('input',function(){clearTimeout(_t);var v=this.value.trim();if(v.length>=5&&!v.toUpperCase().startsWith('R')){_t=setTimeout(buscar,500);}});
async function buscarEndereco(){
  var cod=document.getElementById('q').value.trim().toUpperCase();if(!cod)return;
  document.getElementById('out').textContent='Buscando...';document.querySelectorAll('button').forEach(b=>b.disabled=true);
  try{
    var r=await fetch('/enderecos/'+encodeURIComponent(cod)+'/detalhes');var d=await r.json();
    if(!d.paletes||!d.paletes.length){document.getElementById('out').textContent='Endereço não encontrado ou sem palete.';flash('err');beep(SERR);nr++;document.getElementById('nr').textContent=nr;}
    else{var txt='ENDEREÇO: '+d.endereco+'\n\n';d.paletes.forEach(p=>{txt+='PALETE: '+p.palete+'\n'+'─'.repeat(26)+'\n';if(!p.pedidos.length)txt+='  (sem pedidos)\n';p.pedidos.forEach(ped=>{txt+='\n  PEDIDO: '+ped.pedido+'\n';ped.volumes.forEach(v=>txt+='    '+v+'\n');});txt+='\n';});document.getElementById('out').textContent=txt;flash('ok');beep(SOK);addHist(cod);ne++;document.getElementById('ne').textContent=ne;}
  }catch(e){document.getElementById('out').textContent='Erro ao buscar.';flash('err');beep(SERR);nr++;document.getElementById('nr').textContent=nr;}
  document.querySelectorAll('button').forEach(b=>b.disabled=false);document.getElementById('q').value='';document.getElementById('q').focus();
}
async function buscarPedido(){
  var cod=document.getElementById('q').value.trim().toUpperCase();if(!cod)return;
  document.getElementById('out').textContent='Buscando...';document.querySelectorAll('button').forEach(b=>b.disabled=true);
  try{
    var r=await fetch('/pedidos/'+encodeURIComponent(cod));var d=await r.json();
    if(d.detail){document.getElementById('out').textContent=d.detail;flash('err');beep(SERR);nr++;document.getElementById('nr').textContent=nr;}
    else{var txt='PEDIDO: '+d.pedido+'\n\n';d.enderecos.forEach(i=>{txt+='ENDEREÇO: '+i.endereco+'\nPALETE:   '+i.palete+'\n'+'─'.repeat(26)+'\n';i.volumes.forEach(v=>txt+='  '+v+'\n');txt+='\n';});document.getElementById('out').textContent=txt;flash('ok');beep(SOK);addHist(cod);np++;document.getElementById('np').textContent=np;}
  }catch(e){document.getElementById('out').textContent='Erro ao buscar.';flash('err');beep(SERR);nr++;document.getElementById('nr').textContent=nr;}
  document.querySelectorAll('button').forEach(b=>b.disabled=false);document.getElementById('q').value='';document.getElementById('q').focus();
}
</script></body></html>"""

# ══════════════════════════════════════════════════════════════════
#  PÁGINA: GERENCIAR VOLUMES (com transferência)
# ══════════════════════════════════════════════════════════════════
@app.get("/gerenciar-volumes",response_class=HTMLResponse)
def pg_gerenciar():
    return """<!DOCTYPE html><html lang="pt-BR"><head>"""+_SHARED+"""<title>WMS · Volumes</title></head><body>
"""+nav("vol")+"""
<!-- MODAL TRANSFERÊNCIA -->
<div class="modal-bg" id="modalBg">
  <div class="modal">
    <h3>↔ Transferir Volumes</h3>
    <p style="font-size:13px;color:var(--muted);margin-bottom:18px;" id="modalInfo">— volumes selecionados</p>
    <div class="field"><label>Novo Palete</label><input id="tPalete" placeholder="Ex: PAL002"></div>
    <div class="field"><label>Novo Endereço</label><input id="tEndereco" placeholder="Ex: R07 016 1"></div>
    <div class="btn-row" style="margin-top:4px;">
      <button class="btn btn-amber" onclick="confirmarTransf()">↔ Transferir</button>
      <button class="btn btn-ghost" onclick="fecharModal()">Cancelar</button>
    </div>
    <div id="modalMsg" style="font-size:13px;margin-top:10px;min-height:18px;"></div>
  </div>
</div>
<div class="page-wide">
  <div style="display:flex;align-items:center;justify-content:space-between;flex-wrap:wrap;gap:10px;margin-bottom:20px;">
    <div>
      <h1 style="font-family:var(--mono);font-size:20px;font-weight:600;color:var(--amber);">Gerenciar Volumes</h1>
      <p style="color:var(--muted);font-size:13px;margin-top:3px;">Visualize, transfira e apague volumes.</p>
    </div>
    <div class="btn-row">
      <button class="btn btn-ghost" onclick="carregar()">↺ Atualizar</button>
      <button class="btn btn-ghost" onclick="selAll()">☑ Todos</button>
      <button class="btn btn-ghost" onclick="desSel()">☐ Nenhum</button>
      <button class="btn btn-amber" onclick="abrirTransf()">↔ Transferir</button>
      <button class="btn btn-danger" onclick="apagarSel()">🗑 Apagar</button>
    </div>
  </div>
  <div style="display:flex;gap:10px;align-items:center;margin-bottom:14px;flex-wrap:wrap;">
    <input type="text" id="filtro" placeholder="Filtrar por pedido, palete ou endereço..."
      style="flex:1;min-width:180px;padding:9px 13px;background:var(--surface);color:var(--text);border:1px solid var(--border);border-radius:var(--r-sm);font-size:14px;outline:none;"
      oninput="filtrar()">
    <span id="info" style="font-size:13px;color:var(--muted);white-space:nowrap;">—</span>
  </div>
  <div class="tbl-wrap">
    <table>
      <thead><tr>
        <th style="width:34px"><input type="checkbox" id="chkAll" onchange="toggleAll(this)"></th>
        <th>ID</th><th>Pedido</th><th>Volume</th><th>Palete</th><th>Endereço</th><th>Ação</th>
      </tr></thead>
      <tbody id="tbody"></tbody>
    </table>
  </div>
</div>
<script>
var dados=[];
async function carregar(){
  document.getElementById('tbody').innerHTML='<tr><td colspan="7" style="color:var(--muted);text-align:center;padding:22px;">Carregando...</td></tr>';
  var r=await fetch('/pedidos-volume');dados=await r.json();document.getElementById('filtro').value='';filtrar();
}
function filtrar(){
  var q=document.getElementById('filtro').value.trim().toLowerCase();
  var fd=q?dados.filter(d=>String(d.numero_pedido).toLowerCase().includes(q)||d.palete_codigo.toLowerCase().includes(q)||(d.endereco_codigo||'').toLowerCase().includes(q)):dados;
  var tb=document.getElementById('tbody');
  if(!fd.length){tb.innerHTML='<tr><td colspan="7" style="color:var(--muted);text-align:center;padding:22px;">Nenhum registro.</td></tr>';document.getElementById('info').textContent='0 registros';return;}
  tb.innerHTML=fd.map(d=>{
    var vol=String(d.volume_atual).padStart(3,'0')+'/'+String(d.volume_total).padStart(3,'0');
    return `<tr>
      <td><input type="checkbox" class="chk" value="${d.id}"></td>
      <td style="color:var(--muted);font-family:var(--mono);font-size:12px;">${d.id}</td>
      <td style="font-family:var(--mono);font-weight:600;">${d.numero_pedido}</td>
      <td><span class="badge">${vol}</span></td>
      <td style="color:var(--green-text);font-family:var(--mono);">${d.palete_codigo}</td>
      <td style="color:var(--muted);">${d.endereco_codigo||'—'}</td>
      <td><button class="btn btn-danger" style="padding:4px 9px;font-size:12px;" onclick="apagarUm(${d.id})">Apagar</button></td>
    </tr>`;
  }).join('');
  document.getElementById('info').textContent=fd.length+' registro(s)';
}
function getIds(){return Array.from(document.querySelectorAll('.chk:checked')).map(c=>parseInt(c.value));}
function selAll(){document.querySelectorAll('.chk').forEach(c=>c.checked=true);}
function desSel(){document.querySelectorAll('.chk').forEach(c=>c.checked=false);}
function toggleAll(el){document.querySelectorAll('.chk').forEach(c=>c.checked=el.checked);}
async function apagarUm(id){
  if(!confirm('Apagar este volume?'))return;
  await fetch('/pedidos-volume/'+id,{method:'DELETE',headers:authHeaders()});toast('Volume apagado.');carregar();
}
async function apagarSel(){
  var ids=getIds();if(!ids.length){alert('Selecione ao menos um volume.');return;}
  if(!confirm('Apagar '+ids.length+' volume(s)?'))return;
  var r=await fetch('/pedidos-volume/deletar-varios',{method:'POST',headers:authHeaders(),body:JSON.stringify({ids})});
  var d=await r.json();toast(d.removidos+' volume(s) apagados.');carregar();
}
function abrirTransf(){
  var ids=getIds();if(!ids.length){alert('Selecione os volumes a transferir.');return;}
  document.getElementById('modalInfo').textContent=ids.length+' volume(s) selecionado(s)';
  document.getElementById('tPalete').value='';document.getElementById('tEndereco').value='';
  document.getElementById('modalMsg').textContent='';
  document.getElementById('modalBg').classList.add('open');
  document.getElementById('tPalete').focus();
}
function fecharModal(){document.getElementById('modalBg').classList.remove('open');}
document.getElementById('tPalete').addEventListener('keydown',function(e){if(e.key==='Enter')document.getElementById('tEndereco').focus();});
document.getElementById('tEndereco').addEventListener('keydown',function(e){if(e.key==='Enter')confirmarTransf();});
async function confirmarTransf(){
  var ids=getIds();
  var pal=document.getElementById('tPalete').value.trim().toUpperCase();
  var end=document.getElementById('tEndereco').value.trim().toUpperCase();
  var msg=document.getElementById('modalMsg');
  if(!pal||!end){msg.style.color='var(--red)';msg.textContent='Preencha palete e endereço.';return;}
  msg.style.color='var(--muted)';msg.textContent='Transferindo...';
  try{
    var r=await fetch('/pedidos-volume/transferir',{method:'POST',headers:authHeaders(),
      body:JSON.stringify({ids:ids,novo_palete:pal,novo_endereco:end})});
    var d=await r.json();
    if(d.detail){msg.style.color='var(--red)';msg.textContent=d.detail;return;}
    toast('✓ '+d.movidos+' volume(s) transferidos para '+pal+' / '+d.novo_endereco);
    fecharModal();carregar();
  }catch(e){msg.style.color='var(--red)';msg.textContent='Erro de conexão.';}
}
carregar();
</script></body></html>"""

# ══════════════════════════════════════════════════════════════════
#  PÁGINA: HISTÓRICO
# ══════════════════════════════════════════════════════════════════
@app.get("/historico",response_class=HTMLResponse)
def pg_historico():
    return """<!DOCTYPE html><html lang="pt-BR"><head>"""+_SHARED+"""<title>WMS · Histórico</title></head><body>
"""+nav("hist")+"""
<div class="page-wide">
  <div style="display:flex;align-items:center;justify-content:space-between;flex-wrap:wrap;gap:10px;margin-bottom:20px;">
    <div>
      <h1 style="font-family:var(--mono);font-size:20px;font-weight:600;color:#ce93d8;">Histórico de Ações</h1>
      <p style="color:var(--muted);font-size:13px;margin-top:3px;">Auditoria completa — cadastros, exclusões e transferências.</p>
    </div>
    <div class="btn-row">
      <button class="btn btn-ghost" onclick="carregar()">↺ Atualizar</button>
      <select id="filtroAcao" onchange="filtrar()" style="padding:9px 12px;background:var(--surface);color:var(--text);border:1px solid var(--border);border-radius:var(--r-sm);font-size:13px;outline:none;">
        <option value="">Todas as ações</option>
        <option value="CADASTRO">Cadastros</option>
        <option value="EXCLUSAO">Exclusões</option>
        <option value="TRANSFERENCIA">Transferências</option>
      </select>
      <input type="text" id="filtroTexto" placeholder="Filtrar por pedido, usuário, endereço..."
        style="padding:9px 13px;background:var(--surface);color:var(--text);border:1px solid var(--border);border-radius:var(--r-sm);font-size:13px;outline:none;min-width:220px;"
        oninput="filtrar()">
      <span id="info" style="font-size:13px;color:var(--muted);white-space:nowrap;">—</span>
    </div>
  </div>
  <div class="tbl-wrap">
    <table>
      <thead><tr>
        <th>Data/Hora</th><th>Usuário</th><th>Ação</th><th>Pedido</th><th>Volume</th><th>Palete</th><th>De</th><th>Para</th><th>Detalhe</th>
      </tr></thead>
      <tbody id="tbody"></tbody>
    </table>
  </div>
</div>
<script>
var dados=[];
async function carregar(){
  document.getElementById('tbody').innerHTML='<tr><td colspan="9" style="color:var(--muted);text-align:center;padding:22px;">Carregando...</td></tr>';
  try{
    var r=await fetch('/historico-api',{headers:authHeaders()});
    if(r.status===401){window.location.href='/login';return;}
    dados=await r.json();filtrar();
  }catch(e){document.getElementById('tbody').innerHTML='<tr><td colspan="9" style="color:var(--red);text-align:center;padding:22px;">Erro ao carregar.</td></tr>';}
}
function filtrar(){
  var ac=document.getElementById('filtroAcao').value;
  var q=document.getElementById('filtroTexto').value.trim().toLowerCase();
  var fd=dados.filter(d=>{
    if(ac&&d.acao!==ac)return false;
    if(q){var s=(d.numero_pedido+d.usuario_nome+d.palete_codigo+d.endereco_de+d.endereco_para+d.detalhe_extra).toLowerCase();if(!s.includes(q))return false;}
    return true;
  });
  var tb=document.getElementById('tbody');
  if(!fd.length){tb.innerHTML='<tr><td colspan="9" style="color:var(--muted);text-align:center;padding:22px;">Nenhum registro.</td></tr>';document.getElementById('info').textContent='0 registros';return;}
  var corAcao={'CADASTRO':'badge-green','EXCLUSAO':'badge-red','TRANSFERENCIA':'badge-amber'};
  tb.innerHTML=fd.map(d=>{
    var vol=d.volume_atual!=null?String(d.volume_atual).padStart(3,'0')+'/'+String(d.volume_total).padStart(3,'0'):'—';
    return `<tr>
      <td style="font-family:var(--mono);font-size:12px;color:var(--muted);white-space:nowrap;">${d.criado_em}</td>
      <td style="font-weight:500;">${d.usuario_nome}</td>
      <td><span class="badge ${corAcao[d.acao]||'badge'}">${d.acao}</span></td>
      <td style="font-family:var(--mono);">${d.numero_pedido}</td>
      <td><span class="badge">${vol}</span></td>
      <td style="color:var(--green-text);font-family:var(--mono);">${d.palete_codigo}</td>
      <td style="color:var(--muted);font-family:var(--mono);font-size:12px;">${d.endereco_de}</td>
      <td style="color:var(--green-text);font-family:var(--mono);font-size:12px;">${d.endereco_para}</td>
      <td style="color:var(--muted);font-size:12px;">${d.detalhe_extra}</td>
    </tr>`;
  }).join('');
  document.getElementById('info').textContent=fd.length+' registro(s)';
}
carregar();
</script></body></html>"""

# ══════════════════════════════════════════════════════════════════
#  UTILITÁRIOS
# ══════════════════════════════════════════════════════════════════
@app.get("/seed")
def seed(db:Session=Depends(get_db)):
    enderecos=[("R07 014 1","R07","014","1"),("R07 016 1","R07","016","1"),("R07 018 1","R07","018","1"),("R07 020 1","R07","020","1"),("R07 022 1","R07","022","1"),("R07 024 1","R07","024","1"),("R07 026 1","R07","026","1"),("R07 028 1","R07","028","1"),("R07 014 1F","R07","014","1F"),("R07 016 1F","R07","016","1F"),("R07 018 1F","R07","018","1F"),("R07 020 1F","R07","020","1F"),("R07 022 1F","R07","022","1F"),("R07 024 1F","R07","024","1F"),("R07 026 1F","R07","026","1F"),("R07 028 1F","R07","028","1F")]
    criados=0
    for cod,rua,pred,and_ in enderecos:
        e=db.query(models.Endereco).filter(models.Endereco.codigo==cod).first()
        if e: e.rua=rua;e.predio=pred;e.andar=and_
        else: db.add(models.Endereco(codigo=cod,rua=rua,predio=pred,andar=and_,frente="A",comprimento_cm=120,largura_cm=100,altura_cm=200,capacidade_total=1,capacidade_usada=0));criados+=1
    db.commit()
    return {"status":"ok","criados":criados,"total":len(enderecos)}

@app.get("/reset-dados")
def reset_dados(db:Session=Depends(get_db)):
    db.query(models.PedidoVolume).delete();db.query(models.Palete).delete()
    db.query(models.Endereco).update({"capacidade_usada":0});db.commit()
    return {"status":"ok","aviso":"Paletes e volumes apagados."}