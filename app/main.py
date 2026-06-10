from sqlalchemy import text
import base64 as _b64, json as _json, os as _os
from fastapi import FastAPI, Depends, HTTPException, Header
from fastapi.responses import HTMLResponse, JSONResponse, Response
from sqlalchemy.orm import Session

from app.database import engine, Base, get_db, ping_db
from app import models, schema, crud
from app.auth import criar_usuario, fazer_login, get_usuario_atual

Base.metadata.create_all(bind=engine)
app = FastAPI(title="WMS — TCruzLoc", version="3.0")


# ── Ícones PWA ──────────────────────────────────────────────────────
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
    "name": "WMS TCruzLoc", "short_name": "TCruzLoc",
    "description": "Sistema WMS", "start_url": "/app",
    "display": "standalone", "background_color": "#09090b",
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

_SW = ("const CACHE='wms-v3';"
       "const PAGES=['/app','/login','/operacao','/conferente-v2',"
       "'/gerenciar-volumes','/historico','/enderecos-page','/manifest.json'];"
       "self.addEventListener('install',e=>{e.waitUntil(caches.open(CACHE)"
       ".then(c=>c.addAll(PAGES)).then(()=>self.skipWaiting()));});"
       "self.addEventListener('activate',e=>{e.waitUntil(caches.keys()"
       ".then(ks=>Promise.all(ks.filter(k=>k!==CACHE).map(k=>caches.delete(k))))"
       ".then(()=>self.clients.claim()));});"
       "self.addEventListener('fetch',e=>{"
       "const isApi=['/pedidos','/paletes','/enderecos','/pedidos-volume','/auth','/historico-api']"
       ".some(p=>e.request.url.includes(p));"
       "if(isApi){e.respondWith(fetch(e.request).catch(()=>new Response("
       "JSON.stringify({detail:'Sem conexão.'}),{status:503,"
       "headers:{'Content-Type':'application/json'}})));return;}"
       "e.respondWith(fetch(e.request).then(r=>{if(r.ok){"
       "const c=r.clone();caches.open(CACHE).then(ch=>ch.put(e.request,c));}return r;})"
       ".catch(()=>caches.match(e.request)));});")

# ── Design System compartilhado ─────────────────────────────────────
_SHARED = """
<meta charset="UTF-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<link rel="manifest" href="/manifest.json">
<meta name="theme-color" content="#22c55e">
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
</script>
<style>
:root{
  --bg:#09090b;--s1:#111113;--s2:#18181b;--s3:#27272a;
  --br:#27272a;--br2:#3f3f46;
  --green:#22c55e;--gdim:#22c55e18;--gtxt:#4ade80;
  --blue:#3b82f6;--bdim:#3b82f618;--btxt:#60a5fa;
  --red:#ef4444;--rdim:#ef444418;--rtxt:#f87171;
  --amber:#f59e0b;--adim:#f59e0b18;--atxt:#fbbf24;
  --purple:#a855f7;--pdim:#a855f718;--ptxt:#c084fc;
  --txt:#fafafa;--txt2:#a1a1aa;--txt3:#71717a;
  --font:'IBM Plex Sans',sans-serif;--mono:'IBM Plex Mono',monospace;
  --r:8px;--rl:12px;
}
*{box-sizing:border-box;margin:0;padding:0;}
html,body{background:var(--bg);color:var(--txt);font-family:var(--font);min-height:100vh;}
a{color:inherit;text-decoration:none;}

/* NAV */
nav{display:flex;align-items:center;background:var(--s1);border-bottom:1px solid var(--br);
  padding:0 18px;height:52px;position:sticky;top:0;z-index:100;}
.nb{font-family:var(--mono);font-size:13px;font-weight:600;color:var(--gtxt);
  margin-right:24px;display:flex;align-items:center;gap:7px;flex-shrink:0;}
.nb::before{content:'';width:7px;height:7px;background:var(--green);border-radius:50%;}
.nl{display:flex;gap:1px;flex:1;overflow-x:auto;scrollbar-width:none;}
.nl::-webkit-scrollbar{display:none;}
.na{padding:5px 11px;border-radius:6px;font-size:12px;color:var(--txt3);
  transition:.12s;cursor:pointer;border:1px solid transparent;white-space:nowrap;}
.na:hover{color:var(--txt);background:var(--s2);}
.na.on{color:var(--gtxt);background:var(--gdim);border-color:var(--gdim);}
.nr{display:flex;align-items:center;gap:10px;margin-left:auto;flex-shrink:0;}
.av{width:28px;height:28px;border-radius:50%;background:var(--bdim);
  border:1px solid var(--blue);display:flex;align-items:center;justify-content:center;
  font-size:10px;font-weight:600;color:var(--btxt);flex-shrink:0;}
.nu{font-size:12px;color:var(--txt3);font-family:var(--mono);
  max-width:110px;overflow:hidden;text-overflow:ellipsis;white-space:nowrap;}
.nc{font-family:var(--mono);font-size:11px;color:var(--txt3);}

/* LAYOUT */
.page{max-width:920px;margin:0 auto;padding:26px 16px;}
.pw{max-width:1200px;margin:0 auto;padding:26px 16px;}

/* CARD */
.card{background:var(--s1);border:1px solid var(--br);border-radius:var(--rl);
  padding:20px;margin-bottom:14px;}
.ct{font-size:10px;letter-spacing:.08em;text-transform:uppercase;
  color:var(--txt3);margin-bottom:12px;font-weight:500;}

/* FORM */
.f{margin-bottom:12px;}
.f label{display:block;font-size:10px;letter-spacing:.06em;text-transform:uppercase;
  color:var(--txt3);margin-bottom:6px;font-weight:500;}
.fi{width:100%;padding:11px 13px;background:var(--bg);color:var(--gtxt);
  border:1px solid var(--br);border-radius:var(--r);
  font-family:var(--mono);font-size:15px;transition:.12s;outline:none;}
.fi:focus{border-color:var(--green);box-shadow:0 0 0 3px var(--gdim);}
.fi::placeholder{color:var(--txt3);}
.fi.ok{border-color:var(--green);}
.fi.err{border-color:var(--red);}
.g2{display:grid;grid-template-columns:1fr 1fr;gap:12px;}
.g3{display:grid;grid-template-columns:repeat(3,1fr);gap:10px;}

/* BOTÕES */
.btn{display:inline-flex;align-items:center;justify-content:center;gap:6px;
  padding:9px 17px;border:none;border-radius:var(--r);
  font-family:var(--font);font-size:13px;font-weight:500;
  cursor:pointer;transition:.12s;white-space:nowrap;}
.btn:disabled{opacity:.35;cursor:not-allowed;}
.btn:active:not(:disabled){transform:scale(.97);}
.bg{background:var(--green);color:#000;}
.bg:hover:not(:disabled){filter:brightness(1.1);}
.bb{background:var(--blue);color:#fff;}
.bb:hover:not(:disabled){filter:brightness(1.1);}
.ba{background:var(--amber);color:#000;}
.ba:hover:not(:disabled){filter:brightness(1.1);}
.bgh{background:var(--s2);color:var(--txt);border:1px solid var(--br);}
.bgh:hover:not(:disabled){border-color:var(--br2);}
.bd{background:var(--rdim);color:var(--rtxt);border:1px solid var(--rdim);}
.bd:hover:not(:disabled){background:var(--red);color:#fff;}
.brow{display:flex;gap:8px;flex-wrap:wrap;}
.bfull{width:100%;}

/* OUTPUT */
.term{background:var(--bg);border:1px solid var(--br);border-radius:var(--rl);
  padding:16px;font-family:var(--mono);font-size:13px;color:var(--gtxt);
  white-space:pre-wrap;min-height:90px;line-height:1.7;position:relative;}
.term::before{content:'OUTPUT';position:absolute;top:7px;right:10px;
  font-size:9px;color:var(--txt3);letter-spacing:.1em;}

/* STATUS BAR */
.sb{min-height:24px;display:flex;align-items:center;gap:6px;
  font-size:12px;padding:3px 0;}
.sb.ok{color:var(--gtxt);}.sb.err{color:var(--rtxt);}
.sb.warn{color:var(--atxt);}.sb.info{color:var(--txt3);}
.dot{width:5px;height:5px;border-radius:50%;background:currentColor;flex-shrink:0;}

/* CHIPS */
.chips{display:flex;flex-wrap:wrap;gap:6px;margin-top:8px;}
.chip{padding:3px 10px;background:var(--s2);border:1px solid var(--br);
  border-radius:20px;font-family:var(--mono);font-size:11px;color:var(--txt3);
  cursor:pointer;transition:.12s;}
.chip:hover{border-color:var(--green);color:var(--gtxt);}

/* SEARCH */
.sw{position:relative;}
.sw input{width:100%;padding:15px 15px 15px 42px;font-size:18px;
  font-family:var(--mono);background:var(--s1);color:var(--gtxt);
  border:1px solid var(--br);border-radius:var(--rl);outline:none;transition:.12s;}
.sw input:focus{border-color:var(--green);box-shadow:0 0 0 3px var(--gdim);}
.sw .si{position:absolute;left:14px;top:50%;transform:translateY(-50%);
  font-size:16px;color:var(--txt3);pointer-events:none;}
.sw input.ok{border-color:var(--green);}
.sw input.err{border-color:var(--red);}

/* TABLE */
.tw{overflow-x:auto;}
table{width:100%;border-collapse:collapse;font-size:12px;}
th{text-align:left;padding:8px 10px;font-size:9px;letter-spacing:.08em;
  text-transform:uppercase;color:var(--txt3);border-bottom:1px solid var(--br);font-weight:500;}
td{padding:8px 10px;border-bottom:1px solid var(--br);color:var(--txt);}
tr:last-child td{border-bottom:none;}
tr:hover td{background:var(--s2);}

/* BADGES */
.bk{display:inline-block;padding:2px 7px;border-radius:4px;
  font-family:var(--mono);font-size:10px;font-weight:600;}
.bk-blue{background:var(--bdim);color:var(--btxt);}
.bk-green{background:var(--gdim);color:var(--gtxt);}
.bk-red{background:var(--rdim);color:var(--rtxt);}
.bk-amber{background:var(--adim);color:var(--atxt);}

/* STATUS DE ENDEREÇO */
.end-livre{background:var(--gdim);color:var(--gtxt);border:1px solid var(--green);}
.end-parcial{background:var(--adim);color:var(--atxt);border:1px solid var(--amber);}
.end-ocupado{background:var(--rdim);color:var(--rtxt);border:1px solid var(--red);}

input[type=checkbox]{width:14px;height:14px;accent-color:var(--green);cursor:pointer;}

/* STATS */
.stats{display:flex;flex-wrap:wrap;gap:10px;margin-bottom:18px;}
.stat{flex:1;min-width:88px;background:var(--s1);border:1px solid var(--br);
  border-radius:var(--r);padding:11px 13px;}
.sl{font-size:9px;text-transform:uppercase;letter-spacing:.08em;color:var(--txt3);margin-bottom:4px;}
.sv{font-family:var(--mono);font-size:19px;font-weight:600;color:var(--gtxt);}
.sv.red{color:var(--rtxt);}

/* DIVIDER */
.divider{height:1px;background:var(--br);margin:18px 0;}

/* TOAST */
#toast{position:fixed;bottom:18px;right:18px;background:var(--s1);
  border:1px solid var(--br);border-radius:var(--rl);padding:10px 14px;
  font-size:12px;z-index:999;transform:translateY(60px);opacity:0;
  transition:.2s cubic-bezier(.4,0,.2,1);pointer-events:none;max-width:280px;}
#toast.show{transform:translateY(0);opacity:1;}
#toast.ok{border-color:var(--green);color:var(--gtxt);}
#toast.err{border-color:var(--red);color:var(--rtxt);}

/* MODAL */
.modal-bg{display:none;position:fixed;inset:0;background:#000c;z-index:200;
  align-items:center;justify-content:center;}
.modal-bg.open{display:flex;}
.modal{background:var(--s1);border:1px solid var(--br);border-radius:var(--rl);
  padding:24px;width:100%;max-width:440px;margin:16px;}
.modal h3{font-size:15px;font-weight:600;color:var(--txt);margin-bottom:16px;}

/* MÓDULOS (HOME) */
.mod-card{background:var(--s1);border:1px solid var(--br);border-radius:var(--rl);
  padding:18px;cursor:pointer;transition:.15s;}
.mod-card:hover{border-color:var(--br2);background:var(--s2);}
.mod-icon{width:34px;height:34px;border-radius:8px;display:flex;
  align-items:center;justify-content:center;margin-bottom:11px;font-size:17px;}
.mod-title{font-size:13px;font-weight:600;margin-bottom:4px;}
.mod-desc{font-size:11px;color:var(--txt3);margin-bottom:12px;line-height:1.5;}
.mod-cta{font-size:10px;font-family:var(--mono);}

/* METRIC */
.metric{background:var(--s1);border:1px solid var(--br);border-radius:var(--r);padding:12px 14px;}
.ml{font-size:9px;text-transform:uppercase;letter-spacing:.06em;color:var(--txt3);margin-bottom:5px;}
.mv{font-family:var(--mono);font-size:20px;font-weight:600;}

/* LOGIN */
.login-wrap{display:flex;align-items:center;justify-content:center;min-height:100vh;padding:20px;}
.login-box{background:var(--s1);border:1px solid var(--br);border-radius:var(--rl);
  padding:36px;width:100%;max-width:380px;}
.login-logo{font-family:var(--mono);font-size:20px;font-weight:600;color:var(--gtxt);
  margin-bottom:5px;display:flex;align-items:center;gap:9px;}
.login-logo::before{content:'';width:9px;height:9px;background:var(--green);
  border-radius:50%;box-shadow:0 0 10px var(--green);}
.login-sub{color:var(--txt3);font-size:12px;margin-bottom:24px;}
.err-msg{color:var(--rtxt);font-size:12px;margin-top:8px;min-height:18px;}
</style>
"""

_NAV_TPL = """<nav>
  <div class="nb">WMS · TCruzLoc</div>
  <div class="nl">
    <a class="na{a}" href="/app">Início</a>
    <a class="na{b}" href="/conferente-v2">Conferente</a>
    <a class="na{c}" href="/operacao">Operação</a>
    <a class="na{d}" href="/gerenciar-volumes">Volumes</a>
    <a class="na{e}" href="/historico">Histórico</a>
    <a class="na{f}" href="/enderecos-page">Endereços</a>
  </div>
  <div class="nr">
    <div class="av" id="navAv"></div>
    <span class="nu" id="navUser"></span>
    <span class="nc" id="clk"></span>
    <button class="btn bgh" style="padding:4px 10px;font-size:11px;" onclick="sair()">Sair</button>
  </div>
</nav>
<div id="toast"></div>
<script>
(function(){
  if(!localStorage.getItem('wms_token')&&window.location.pathname!=='/login'){
    window.location.href='/login';return;
  }
  document.addEventListener('DOMContentLoaded',function(){
    var u=localStorage.getItem('wms_user')||'';
    var el=document.getElementById('navUser');if(el)el.textContent=u;
    var av=document.getElementById('navAv');
    if(av){var p=u.trim().split(' ');
      av.textContent=p.length>=2?(p[0][0]+p[p.length-1][0]).toUpperCase():u.substring(0,2).toUpperCase();}
  });
  function tick(){var d=new Date();var el=document.getElementById('clk');
    if(el)el.textContent=d.toLocaleDateString('pt-BR')+' '+d.toLocaleTimeString('pt-BR');}
  setInterval(tick,1000);tick();
  window.toast=function(msg,t){var el=document.getElementById('toast');
    el.textContent=msg;el.className='show '+(t||'ok');
    clearTimeout(el._t);el._t=setTimeout(()=>el.className='',3000);};
  window.sair=function(){localStorage.removeItem('wms_token');
    localStorage.removeItem('wms_user');window.location.href='/login';};
})();
</script>"""


def nav(active: str) -> str:
    m = {'home':'a','conf':'b','oper':'c','vol':'d','hist':'e','end':'f'}
    t = _NAV_TPL
    for k, v in m.items():
        t = t.replace('{'+v+'}', ' on' if active == k else '')
    return t


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
def api_criar_usuario(dados: schema.UsuarioCriar, db: Session = Depends(get_db)):
    return criar_usuario(db, dados.nome, dados.login, dados.senha)

@app.get("/auth/me")
def api_me(db: Session = Depends(get_db), authorization: str = Header(default="")):
    u = get_usuario_atual(db, authorization)
    return {"id": u.id, "nome": u.nome, "login": u.login}


# ══════════════════════════════════════════════════════════════════
#  API ROTAS
# ══════════════════════════════════════════════════════════════════
@app.get("/")
def root(): return {"status": "ok", "app": "WMS TCruzLoc v3"}

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

@app.get("/caixas", response_model=list[schema.CaixaResposta])
def listar_caixas(db: Session = Depends(get_db)):
    return crud.listar_caixas(db)

# Paletes — estáticas ANTES de dinâmicas
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

# Volumes — estáticas ANTES de dinâmicas
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
def historico_api(db: Session = Depends(get_db),
                  authorization: str = Header(default="")):
    get_usuario_atual(db, authorization)
    return [{
        "id": h.id,
        "usuario_nome":  h.usuario_nome  or "—",
        "acao":          h.acao,
        "numero_pedido": h.numero_pedido or "—",
        "volume_atual":  h.volume_atual,
        "volume_total":  h.volume_total,
        "palete_codigo": h.palete_codigo or "—",
        "endereco_de":   h.endereco_de   or "—",
        "endereco_para": h.endereco_para or "—",
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
  <div class="login-logo">WMS · TCruzLoc</div>
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
    window.location.href='/app';
  }}catch(ex){{e.textContent='Erro de conexão.';}}
}}
if(localStorage.getItem('wms_token'))window.location.href='/app';
</script></body></html>"""


# ══════════════════════════════════════════════════════════════════
#  PÁGINA: HOME
# ══════════════════════════════════════════════════════════════════
@app.get("/app", response_class=HTMLResponse)
def pg_home():
    return f"""<!DOCTYPE html><html lang="pt-BR"><head>{_SHARED}<title>WMS · Início</title></head><body>
{nav('home')}
<div class="page">
  <div style="margin-bottom:22px;">
    <div style="display:flex;align-items:center;gap:10px;margin-bottom:4px;">
      <h1 style="font-family:var(--mono);font-size:21px;font-weight:600;color:var(--gtxt);">WMS · TCruzLoc_Dyo</h1>
      <span style="font-size:10px;padding:2px 8px;border-radius:20px;background:var(--gdim);
        color:var(--gtxt);border:1px solid var(--green);font-family:var(--mono);">v3.0 online</span>
    </div>
    <p style="color:var(--txt3);font-size:12px;">Sistema de gerenciamento de armazém</p>
  </div>

  <div style="display:grid;grid-template-columns:repeat(4,1fr);gap:10px;margin-bottom:20px;">
    <div class="metric"><div class="ml">Volumes ativos</div>
      <div class="mv" id="mv" style="color:var(--gtxt);">—</div></div>
    <div class="metric"><div class="ml">Endereços livres</div>
      <div class="mv" id="me-l" style="color:var(--gtxt);">—</div></div>
    <div class="metric"><div class="ml">Endereços parciais</div>
      <div class="mv" id="me-p" style="color:var(--atxt);">—</div></div>
    <div class="metric"><div class="ml">Endereços ocupados</div>
      <div class="mv" id="me-o" style="color:var(--rtxt);">—</div></div>
  </div>

  <div style="display:grid;grid-template-columns:repeat(2,1fr);gap:12px;margin-bottom:20px;">
    <a href="/conferente-v2"><div class="mod-card">
      <div class="mod-icon" style="background:var(--gdim);">📦</div>
      <div class="mod-title" style="color:var(--gtxt);">Conferente</div>
      <div class="mod-desc">Montar paletes, endereçar pedidos e registrar volumes.</div>
      <div class="mod-cta" style="color:var(--gtxt);">ACESSAR →</div>
    </div></a>
    <a href="/operacao"><div class="mod-card">
      <div class="mod-icon" style="background:var(--bdim);">🔍</div>
      <div class="mod-title" style="color:var(--btxt);">Operação</div>
      <div class="mod-desc">Consultar onde está um pedido ou listar pedidos de um endereço.</div>
      <div class="mod-cta" style="color:var(--btxt);">ACESSAR →</div>
    </div></a>
    <a href="/gerenciar-volumes"><div class="mod-card">
      <div class="mod-icon" style="background:var(--adim);">🗂️</div>
      <div class="mod-title" style="color:var(--atxt);">Volumes</div>
      <div class="mod-desc">Visualizar, filtrar, transferir e apagar volumes cadastrados.</div>
      <div class="mod-cta" style="color:var(--atxt);">ACESSAR →</div>
    </div></a>
    <a href="/historico"><div class="mod-card">
      <div class="mod-icon" style="background:var(--pdim);">📋</div>
      <div class="mod-title" style="color:var(--ptxt);">Histórico</div>
      <div class="mod-desc">Auditoria completa — cadastros, exclusões e transferências.</div>
      <div class="mod-cta" style="color:var(--ptxt);">ACESSAR →</div>
    </div></a>
  </div>

  <div class="divider"></div>
  <div style="display:flex;gap:8px;flex-wrap:wrap;align-items:center;">
    <a href="/seed"><button class="btn bgh" style="font-size:11px;">⚙️ Inicializar endereços</button></a>
    <a href="/criar-admin"><button class="btn bgh" style="font-size:11px;">👤 Criar usuário</button></a>
    <a href="/health"><button class="btn bgh" style="font-size:11px;">💚 Status</button></a>
    <a href="/docs"><button class="btn bgh" style="font-size:11px;">📄 API</button></a>
    <span style="margin-left:auto;font-size:11px;color:var(--txt3);">
      📱 Chrome → ⋮ → Adicionar à tela inicial
    </span>
  </div>
</div>
<script>
async function loadMetrics(){{
  try{{
    var dv=await(await fetch('/pedidos-volume')).json();
    document.getElementById('mv').textContent=Array.isArray(dv)?dv.length:'—';
    var de=await(await fetch('/enderecos-status')).json();
    if(Array.isArray(de)){{
      document.getElementById('me-l').textContent=de.filter(e=>e.status==='LIVRE').length;
      document.getElementById('me-p').textContent=de.filter(e=>e.status==='PARCIAL').length;
      document.getElementById('me-o').textContent=de.filter(e=>e.status==='OCUPADO').length;
    }}
  }}catch(e){{}}
}}
loadMetrics();
</script>
</body></html>"""


# ══════════════════════════════════════════════════════════════════
#  PÁGINA: CRIAR USUÁRIO
# ══════════════════════════════════════════════════════════════════
@app.get("/criar-admin", response_class=HTMLResponse)
def pg_criar_usuario():
    return f"""<!DOCTYPE html><html lang="pt-BR"><head>{_SHARED}<title>WMS · Criar Usuário</title></head><body>
{nav('home')}
<div class="page">
  <div style="margin-bottom:22px;">
    <h1 style="font-family:var(--mono);font-size:19px;font-weight:600;color:var(--gtxt);">Criar Usuário</h1>
  </div>
  <div class="card" style="max-width:400px;">
    <div class="f"><label>Nome completo</label>
      <input class="fi" id="nome" placeholder="Ex: João Silva" autofocus
        onkeydown="if(event.key==='Enter')document.getElementById('login').focus()"></div>
    <div class="f"><label>Login</label>
      <input class="fi" id="login" placeholder="Ex: joao.silva"
        onkeydown="if(event.key==='Enter')document.getElementById('senha').focus()"></div>
    <div class="f"><label>Senha</label>
      <input class="fi" id="senha" type="password" placeholder="Mínimo 4 caracteres"
        onkeydown="if(event.key==='Enter')criar()"></div>
    <button class="btn bg bfull" style="margin-top:4px;" onclick="criar()">Criar Usuário</button>
    <div id="msg" style="margin-top:10px;font-size:12px;min-height:18px;"></div>
  </div>
</div>
<script>
async function criar(){{
  var n=document.getElementById('nome').value.trim();
  var l=document.getElementById('login').value.trim();
  var s=document.getElementById('senha').value;
  var m=document.getElementById('msg');
  if(!n||!l||!s){{m.style.color='var(--rtxt)';m.textContent='Preencha todos os campos.';return;}}
  try{{
    var r=await fetch('/auth/criar-usuario',{{method:'POST',
      headers:authHeaders(),body:JSON.stringify({{nome:n,login:l,senha:s}})}});
    var d=await r.json();
    if(d.detail){{m.style.color='var(--rtxt)';m.textContent=d.detail;}}
    else{{m.style.color='var(--gtxt)';m.textContent='✓ Usuário "'+d.login+'" criado!';
      document.getElementById('nome').value='';document.getElementById('login').value='';
      document.getElementById('senha').value='';}}
  }}catch(e){{m.style.color='var(--rtxt)';m.textContent='Erro de conexão.';}}
}}
</script></body></html>"""


# ══════════════════════════════════════════════════════════════════
#  PÁGINA: CONFERENTE v2 — com indicador de status do endereço
# ══════════════════════════════════════════════════════════════════
@app.get("/conferente-v2", response_class=HTMLResponse)
def pg_conferente():
    return r"""<!DOCTYPE html><html lang="pt-BR"><head>""" + _SHARED + r"""
<title>WMS · Conferente</title></head><body>
""" + nav("conf") + r"""
<div class="page">
  <div style="margin-bottom:18px;">
    <h1 style="font-family:var(--mono);font-size:19px;font-weight:600;color:var(--gtxt);">Montagem de Palete</h1>
    <p style="color:var(--txt3);font-size:12px;margin-top:3px;">Informe palete e endereço, depois adicione os pedidos.</p>
  </div>

  <div class="card">
    <div class="ct">Identificação do Palete</div>
    <div class="g2">
      <div class="f"><label>Palete</label>
        <input class="fi" id="palete" placeholder="Ex: PAL001" autofocus></div>
      <div class="f"><label>Endereço</label>
        <div style="position:relative;">
          <input class="fi" id="endereco" placeholder="Ex: R07 014 1 ou R070141"
            oninput="verificarEndereco()" onblur="verificarEndereco()">
          <span id="end-badge" style="position:absolute;right:10px;top:50%;
            transform:translateY(-50%);font-size:10px;padding:2px 7px;
            border-radius:4px;font-family:var(--mono);font-weight:600;display:none;"></span>
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

  <div class="sb info" id="stbar"><div class="dot"></div>Aguardando dados...</div>
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
</div>

<script>
var resumo=[],totalVols=0;
var endStatus={};  // cache: codigo -> status

// Carrega status de todos os endereços ao iniciar
async function carregarStatusEnderecos(){
  try{
    var r=await fetch('/enderecos-status');
    var d=await r.json();
    d.forEach(function(e){endStatus[e.codigo]=e.status;});
  }catch(e){}
}
carregarStatusEnderecos();

function verificarEndereco(){
  var val=document.getElementById('endereco').value.trim().toUpperCase();
  var badge=document.getElementById('end-badge');
  var info=document.getElementById('end-info');
  if(!val){badge.style.display='none';info.textContent='';return;}

  // Normaliza para tentar achar no cache
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
  }
}

function ss(msg,t){var el=document.getElementById('stbar');
  el.className='sb '+(t||'info');el.innerHTML='<div class="dot"></div>'+msg;}
function fmt(n,t){return String(n).padStart(3,'0')+'/'+String(t).padStart(3,'0');}
function upd(){
  document.getElementById('s-pal').textContent=document.getElementById('palete').value.trim()||'—';
  document.getElementById('s-end').textContent=document.getElementById('endereco').value.trim()||'—';
  document.getElementById('s-nped').textContent=new Set(resumo.map(r=>r.pedido)).size;
  document.getElementById('s-nvol').textContent=totalVols;
}
function renderOut(){
  if(!resumo.length){document.getElementById('out').textContent='Pedidos adicionados aparecerão aqui...';return;}
  var ag={};
  resumo.forEach(r=>{
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
    if(e.key==='Enter'){e.preventDefault();document.getElementById(nx[i]).focus();}
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
  resumo.forEach(r=>{
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
  ['palete','endereco','pedido','vol_ini','vol_fin','vol_tot'].forEach(id=>document.getElementById(id).value='');
  document.getElementById('out').textContent='Pedidos adicionados aparecerão aqui...';
  document.getElementById('end-badge').style.display='none';
  document.getElementById('end-info').textContent='';
  document.getElementById('btnAdd').disabled=false;document.getElementById('btnFin').disabled=false;
  ss('Pronto para novo palete.','info');upd();document.getElementById('palete').focus();
}
upd();
</script></body></html>"""


# ══════════════════════════════════════════════════════════════════
#  PÁGINA: OPERAÇÃO
# ══════════════════════════════════════════════════════════════════
@app.get("/operacao", response_class=HTMLResponse)
def pg_operacao():
    return r"""<!DOCTYPE html><html lang="pt-BR"><head>""" + _SHARED + r"""
<title>WMS · Operação</title></head><body>
""" + nav("oper") + r"""
<div class="page">
  <div style="margin-bottom:18px;">
    <h1 style="font-family:var(--mono);font-size:19px;font-weight:600;color:var(--btxt);">Consulta Rápida</h1>
    <p style="color:var(--txt3);font-size:12px;margin-top:3px;">Bipe ou digite um endereço ou número de pedido.</p>
  </div>
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
</div>
<script>
var nc=0,ne=0,np=0,nr=0,hist=[];
var SOK='https://actions.google.com/sounds/v1/alarms/beep_short.ogg';
var SERR='https://actions.google.com/sounds/v1/cartoon/pop.ogg';
function beep(u){try{new Audio(u).play();}catch(e){}}
function flash(c){var el=document.getElementById('q');el.className=c;setTimeout(()=>el.className='',800);}
function addHist(v){if(!v)return;hist=[...new Set([v,...hist])].slice(0,12);
  document.getElementById('hist').innerHTML=hist.map(h=>`<div class="chip" onclick="rebuscar('${h}')">${h}</div>`).join('');
  nc++;document.getElementById('nc').textContent=nc;}
function rebuscar(v){document.getElementById('q').value=v;buscar();}
function buscar(){var v=document.getElementById('q').value.trim().toUpperCase();
  if(!v)return;
  if(v.match(/^R[0-9]/)||v.startsWith('R '))buscarEndereco();else buscarPedido();}
var _t;document.getElementById('q').addEventListener('input',function(){
  clearTimeout(_t);var v=this.value.trim();
  if(v.length>=5&&!v.toUpperCase().startsWith('R')){_t=setTimeout(buscar,500);}
});
async function buscarEndereco(){
  var cod=document.getElementById('q').value.trim().toUpperCase();if(!cod)return;
  document.getElementById('out').textContent='Buscando...';
  document.querySelectorAll('button').forEach(b=>b.disabled=true);
  try{
    var r=await fetch('/enderecos/'+encodeURIComponent(cod)+'/detalhes');
    var d=await r.json();
    if(!d.paletes||!d.paletes.length){
      document.getElementById('out').textContent='Endereço não encontrado ou sem palete.';
      flash('err');beep(SERR);nr++;document.getElementById('nr').textContent=nr;
    }else{
      var txt='ENDEREÇO: '+d.endereco+'\n\n';
      d.paletes.forEach(p=>{
        txt+='PALETE: '+p.palete+'\n'+'─'.repeat(24)+'\n';
        if(!p.pedidos.length)txt+='  (sem pedidos)\n';
        p.pedidos.forEach(ped=>{txt+='\n  PEDIDO: '+ped.pedido+'\n';
          ped.volumes.forEach(v=>txt+='    '+v+'\n');});txt+='\n';
      });
      document.getElementById('out').textContent=txt;
      flash('ok');beep(SOK);addHist(cod);ne++;document.getElementById('ne').textContent=ne;
    }
  }catch(e){document.getElementById('out').textContent='Erro ao buscar.';
    flash('err');beep(SERR);nr++;document.getElementById('nr').textContent=nr;}
  document.querySelectorAll('button').forEach(b=>b.disabled=false);
  document.getElementById('q').value='';document.getElementById('q').focus();
}
async function buscarPedido(){
  var cod=document.getElementById('q').value.trim().toUpperCase();if(!cod)return;
  document.getElementById('out').textContent='Buscando...';
  document.querySelectorAll('button').forEach(b=>b.disabled=true);
  try{
    var r=await fetch('/pedidos/'+encodeURIComponent(cod));var d=await r.json();
    if(d.detail){document.getElementById('out').textContent=d.detail;
      flash('err');beep(SERR);nr++;document.getElementById('nr').textContent=nr;
    }else{
      var txt='PEDIDO: '+d.pedido+'\n\n';
      d.enderecos.forEach(i=>{
        txt+='ENDEREÇO: '+i.endereco+'\nPALETE:   '+i.palete+'\n'+'─'.repeat(24)+'\n';
        i.volumes.forEach(v=>txt+='  '+v+'\n');txt+='\n';
      });
      document.getElementById('out').textContent=txt;
      flash('ok');beep(SOK);addHist(cod);np++;document.getElementById('np').textContent=np;
    }
  }catch(e){document.getElementById('out').textContent='Erro ao buscar.';
    flash('err');beep(SERR);nr++;document.getElementById('nr').textContent=nr;}
  document.querySelectorAll('button').forEach(b=>b.disabled=false);
  document.getElementById('q').value='';document.getElementById('q').focus();
}
</script></body></html>"""


# ══════════════════════════════════════════════════════════════════
#  PÁGINA: GERENCIAR VOLUMES (com transferência)
# ══════════════════════════════════════════════════════════════════
@app.get("/gerenciar-volumes", response_class=HTMLResponse)
def pg_gerenciar():
    return """<!DOCTYPE html><html lang="pt-BR"><head>""" + _SHARED + """
<title>WMS · Volumes</title></head><body>
""" + nav("vol") + """
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
<div class="pw">
  <div style="display:flex;align-items:center;justify-content:space-between;
    flex-wrap:wrap;gap:10px;margin-bottom:18px;">
    <div>
      <h1 style="font-family:var(--mono);font-size:19px;font-weight:600;color:var(--atxt);">Gerenciar Volumes</h1>
      <p style="color:var(--txt3);font-size:12px;margin-top:3px;">Visualize, transfira e apague volumes.</p>
    </div>
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
      style="flex:1;min-width:180px;padding:8px 12px;background:var(--s1);color:var(--txt);
        border:1px solid var(--br);border-radius:var(--r);font-size:13px;outline:none;"
      oninput="filtrar()">
    <span id="info" style="font-size:12px;color:var(--txt3);white-space:nowrap;">—</span>
  </div>
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
  var fd=q?dados.filter(d=>String(d.numero_pedido).toLowerCase().includes(q)||
    d.palete_codigo.toLowerCase().includes(q)||(d.endereco_codigo||'').toLowerCase().includes(q)):dados;
  var tb=document.getElementById('tbody');
  if(!fd.length){tb.innerHTML='<tr><td colspan="7" style="color:var(--txt3);text-align:center;padding:20px;">Nenhum registro.</td></tr>';
    document.getElementById('info').textContent='0 registros';return;}
  tb.innerHTML=fd.map(d=>{
    var vol=String(d.volume_atual).padStart(3,'0')+'/'+String(d.volume_total).padStart(3,'0');
    return `<tr>
      <td><input type="checkbox" class="chk" value="${d.id}"></td>
      <td style="color:var(--txt3);font-family:var(--mono);font-size:11px;">${d.id}</td>
      <td style="font-family:var(--mono);font-weight:600;">${d.numero_pedido}</td>
      <td><span class="bk bk-blue">${vol}</span></td>
      <td style="color:var(--gtxt);font-family:var(--mono);">${d.palete_codigo}</td>
      <td style="color:var(--txt3);">${d.endereco_codigo||'—'}</td>
      <td><button class="btn bd" style="padding:4px 9px;font-size:11px;" onclick="apagarUm(${d.id})">Apagar</button></td>
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
  await fetch('/pedidos-volume/'+id,{method:'DELETE',headers:authHeaders()});
  toast('Volume apagado.');carregar();
}
async function apagarSel(){
  var ids=getIds();if(!ids.length){alert('Selecione ao menos um volume.');return;}
  if(!confirm('Apagar '+ids.length+' volume(s)?'))return;
  var r=await fetch('/pedidos-volume/deletar-varios',{method:'POST',
    headers:authHeaders(),body:JSON.stringify({ids})});
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
</script></body></html>"""


# ══════════════════════════════════════════════════════════════════
#  PÁGINA: HISTÓRICO
# ══════════════════════════════════════════════════════════════════
@app.get("/historico", response_class=HTMLResponse)
def pg_historico():
    return """<!DOCTYPE html><html lang="pt-BR"><head>""" + _SHARED + """
<title>WMS · Histórico</title></head><body>
""" + nav("hist") + """
<div class="pw">
  <div style="display:flex;align-items:center;justify-content:space-between;
    flex-wrap:wrap;gap:10px;margin-bottom:18px;">
    <div>
      <h1 style="font-family:var(--mono);font-size:19px;font-weight:600;color:var(--ptxt);">Histórico de Ações</h1>
      <p style="color:var(--txt3);font-size:12px;margin-top:3px;">Auditoria — cadastros, exclusões, transferências e status.</p>
    </div>
    <div class="brow" style="flex-wrap:wrap;gap:8px;">
      <button class="btn bgh" onclick="carregar()">↺ Atualizar</button>
      <select id="filtroAcao" onchange="filtrar()"
        style="padding:7px 11px;background:var(--s1);color:var(--txt);
          border:1px solid var(--br);border-radius:var(--r);font-size:12px;outline:none;">
        <option value="">Todas as ações</option>
        <option value="CADASTRO">Cadastros</option>
        <option value="EXCLUSAO">Exclusões</option>
        <option value="TRANSFERENCIA">Transferências</option>
        <option value="STATUS_END">Status endereço</option>
      </select>
      <input type="text" id="filtroTxt" placeholder="Pedido, usuário, endereço..."
        style="padding:7px 11px;background:var(--s1);color:var(--txt);
          border:1px solid var(--br);border-radius:var(--r);font-size:12px;
          outline:none;min-width:200px;" oninput="filtrar()">
      <span id="info" style="font-size:12px;color:var(--txt3);white-space:nowrap;">—</span>
    </div>
  </div>
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
async function carregar(){
  document.getElementById('tbody').innerHTML='<tr><td colspan="9" style="color:var(--txt3);text-align:center;padding:20px;">Carregando...</td></tr>';
  try{
    var r=await fetch('/historico-api',{headers:authHeaders()});
    if(r.status===401){window.location.href='/login';return;}
    dados=await r.json();filtrar();
  }catch(e){document.getElementById('tbody').innerHTML='<tr><td colspan="9" style="color:var(--rtxt);text-align:center;padding:20px;">Erro ao carregar.</td></tr>';}
}
function filtrar(){
  var ac=document.getElementById('filtroAcao').value;
  var q=document.getElementById('filtroTxt').value.trim().toLowerCase();
  var fd=dados.filter(d=>{
    if(ac&&d.acao!==ac)return false;
    if(q){var s=(d.numero_pedido+d.usuario_nome+d.palete_codigo+d.endereco_de+d.endereco_para+d.detalhe_extra).toLowerCase();if(!s.includes(q))return false;}
    return true;
  });
  var tb=document.getElementById('tbody');
  if(!fd.length){tb.innerHTML='<tr><td colspan="9" style="color:var(--txt3);text-align:center;padding:20px;">Nenhum registro.</td></tr>';
    document.getElementById('info').textContent='0 registros';return;}
  var cor={'CADASTRO':'bk-green','EXCLUSAO':'bk-red','TRANSFERENCIA':'bk-amber','STATUS_END':'bk-blue'};
  tb.innerHTML=fd.map(d=>{
    var vol=d.volume_atual!=null?String(d.volume_atual).padStart(3,'0')+'/'+String(d.volume_total).padStart(3,'0'):'—';
    return `<tr>
      <td style="font-family:var(--mono);font-size:11px;color:var(--txt3);white-space:nowrap;">${d.criado_em}</td>
      <td style="font-weight:500;font-size:12px;">${d.usuario_nome}</td>
      <td><span class="bk ${cor[d.acao]||'bk-blue'}">${d.acao}</span></td>
      <td style="font-family:var(--mono);">${d.numero_pedido}</td>
      <td><span class="bk bk-blue">${vol}</span></td>
      <td style="color:var(--gtxt);font-family:var(--mono);">${d.palete_codigo}</td>
      <td style="color:var(--txt3);font-family:var(--mono);font-size:11px;">${d.endereco_de}</td>
      <td style="color:var(--gtxt);font-family:var(--mono);font-size:11px;">${d.endereco_para}</td>
      <td style="color:var(--txt3);font-size:11px;">${d.detalhe_extra}</td>
    </tr>`;
  }).join('');
  document.getElementById('info').textContent=fd.length+' registro(s)';
}
carregar();
</script></body></html>"""


# ══════════════════════════════════════════════════════════════════
#  PÁGINA: ENDEREÇOS — gerenciar status manualmente
# ══════════════════════════════════════════════════════════════════
@app.get("/enderecos-page", response_class=HTMLResponse)
def pg_enderecos():
    return """<!DOCTYPE html><html lang="pt-BR"><head>""" + _SHARED + """
<title>WMS · Endereços</title></head><body>
""" + nav("end") + """
<div class="pw">
  <div style="display:flex;align-items:center;justify-content:space-between;
    flex-wrap:wrap;gap:10px;margin-bottom:18px;">
    <div>
      <h1 style="font-family:var(--mono);font-size:19px;font-weight:600;color:var(--btxt);">Endereços</h1>
      <p style="color:var(--txt3);font-size:12px;margin-top:3px;">
        Gerencie o status de ocupação de cada endereço do armazém.</p>
    </div>
    <button class="btn bgh" onclick="carregar()">↺ Atualizar</button>
  </div>

 <div style="display:flex;gap:8px;margin-bottom:18px;flex-wrap:wrap;">
  <button class="btn bgh" onclick="setFiltro('TODOS')">Todos</button>
  <button class="btn bgh" onclick="setFiltro('LIVRE')">Livres</button>
  <button class="btn bgh" onclick="setFiltro('PARCIAL')">Parciais</button>
  <button class="btn bgh" onclick="setFiltro('OCUPADO')">Ocupados</button>
</div>

<div style="display:flex;gap:10px;margin-bottom:18px;flex-wrap:wrap;">
    <div class="metric" style="flex:1;min-width:110px;">
      <div class="ml">Livres</div>
      <div class="mv" id="cnt-l" style="color:var(--gtxt);">—</div>
    </div>
    <div class="metric" style="flex:1;min-width:110px;">
      <div class="ml">Parciais</div>
      <div class="mv" id="cnt-p" style="color:var(--atxt);">—</div>
    </div>
    <div class="metric" style="flex:1;min-width:110px;">
      <div class="ml">Ocupados</div>
      <div class="mv" id="cnt-o" style="color:var(--rtxt);">—</div>
    </div>
    <div class="metric" style="flex:1;min-width:110px;">
      <div class="ml">Total</div>
      <div class="mv" id="cnt-t" style="color:var(--txt);">—</div>
    </div>
  </div>

  <div style="display:grid;grid-template-columns:repeat(auto-fill,minmax(200px,1fr));gap:10px;"
    id="grid"></div>
</div>

<script>
var enderecos=[];
var filtroAtual='TODOS';

function setFiltro(status){
  filtroAtual=status;
  renderGrid();
}

async function carregar(){
  document.getElementById('grid').innerHTML='<p style="color:var(--txt3);padding:10px;">Carregando...</p>';
  try{
    var r=await fetch('/enderecos');
    enderecos=await r.json();
    renderGrid();
    atualizarContadores();
  }catch(e){document.getElementById('grid').innerHTML='<p style="color:var(--rtxt);">Erro ao carregar.</p>';}
}

function corStatus(s){
  if(s==='LIVRE')   return {bg:'var(--gdim)',border:'var(--green)',txt:'var(--gtxt)',cls:'end-livre'};
  if(s==='PARCIAL') return {bg:'var(--adim)',border:'var(--amber)',txt:'var(--atxt)',cls:'end-parcial'};
  if(s==='OCUPADO') return {bg:'var(--rdim)',border:'var(--red)',  txt:'var(--rtxt)',cls:'end-ocupado'};
  return {bg:'var(--s2)',border:'var(--br)',txt:'var(--txt3)',cls:''};
}

function renderGrid(){
  var g=document.getElementById('grid');
  g.innerHTML='';
  var lista = enderecos;

if(filtroAtual !== 'TODOS'){
  lista = enderecos.filter(e => (e.status_ocupacao || 'LIVRE') === filtroAtual);
}

if(!lista.length){
  g.innerHTML='<p style="color:var(--txt3);padding:10px;">Nenhum endereço encontrado nesse filtro.</p>';
  return;
}

lista.forEach(function(e){
    var st=e.status_ocupacao||'LIVRE';
    var c=corStatus(st);
    var div=document.createElement('div');
    div.style.cssText='background:var(--s1);border:1px solid '+c.border+';border-radius:var(--rl);padding:16px;';
    div.innerHTML=`
      <div style="font-family:var(--mono);font-size:14px;font-weight:600;
        color:var(--txt);margin-bottom:8px;">${e.codigo}</div>
      <span class="bk ${c.cls}" style="margin-bottom:12px;display:inline-block;">${st}</span>
      <div style="display:flex;flex-direction:column;gap:5px;margin-top:10px;">
        <button onclick="setStatus('${e.codigo}','LIVRE')"
          class="btn" style="padding:6px;font-size:11px;
          background:${st==='LIVRE'?'var(--green)':'var(--gdim)'};
          color:${st==='LIVRE'?'#000':'var(--gtxt)'};border:1px solid var(--green);">
          ● Livre</button>
        <button onclick="setStatus('${e.codigo}','PARCIAL')"
          class="btn" style="padding:6px;font-size:11px;
          background:${st==='PARCIAL'?'var(--amber)':'var(--adim)'};
          color:${st==='PARCIAL'?'#000':'var(--atxt)'};border:1px solid var(--amber);">
          ● Parcial</button>
        <button onclick="setStatus('${e.codigo}','OCUPADO')"
          class="btn" style="padding:6px;font-size:11px;
          background:${st==='OCUPADO'?'var(--red)':'var(--rdim)'};
          color:${st==='OCUPADO'?'#fff':'var(--rtxt)'};border:1px solid var(--red);">
          ● Ocupado</button>
      </div>`;
    g.appendChild(div);
  });
}

function atualizarContadores(){
  var l=enderecos.filter(e=>(e.status_ocupacao||'LIVRE')==='LIVRE').length;
  var p=enderecos.filter(e=>e.status_ocupacao==='PARCIAL').length;
  var o=enderecos.filter(e=>e.status_ocupacao==='OCUPADO').length;
  document.getElementById('cnt-l').textContent=l;
  document.getElementById('cnt-p').textContent=p;
  document.getElementById('cnt-o').textContent=o;
  document.getElementById('cnt-t').textContent=enderecos.length;
}

async function setStatus(codigo, status){
  try{
    var r=await fetch('/enderecos/'+encodeURIComponent(codigo)+'/status',{
      method:'PATCH',headers:authHeaders(),
      body:JSON.stringify({status_ocupacao:status})});
    var d=await r.json();
    if(d.detail){toast(d.detail,'err');return;}
    // Atualiza localmente sem recarregar tudo
    var idx=enderecos.findIndex(e=>e.codigo===codigo);
    if(idx>=0)enderecos[idx].status_ocupacao=status;
    renderGrid();atualizarContadores();
    toast('✓ '+codigo+' marcado como '+status);
  }catch(e){toast('Erro de conexão','err');}
}
carregar();
</script></body></html>"""


# ══════════════════════════════════════════════════════════════════
#  UTILITÁRIOS
# ══════════════════════════════════════════════════════════════════
@app.get("/seed")
def seed(db: Session = Depends(get_db)):
    enderecos = [
        ("R07 014 1","R07","014","1"), ("R07 016 1","R07","016","1"),
        ("R07 018 1","R07","018","1"), ("R07 020 1","R07","020","1"),
        ("R07 022 1","R07","022","1"), ("R07 024 1","R07","024","1"),
        ("R07 026 1","R07","026","1"), ("R07 028 1","R07","028","1"),
        ("R07 014 1F","R07","014","1F"), ("R07 016 1F","R07","016","1F"),
        ("R07 018 1F","R07","018","1F"), ("R07 020 1F","R07","020","1F"),
        ("R07 022 1F","R07","022","1F"), ("R07 024 1F","R07","024","1F"),
        ("R07 026 1F","R07","026","1F"), ("R07 028 1F","R07","028","1F"),
    ]
    criados = 0
    for cod, rua, pred, and_ in enderecos:
        e = db.query(models.Endereco).filter(models.Endereco.codigo == cod).first()
        if e:
            e.rua = rua; e.predio = pred; e.andar = and_
            if not hasattr(e, 'status_ocupacao') or e.status_ocupacao is None:
                e.status_ocupacao = "LIVRE"
        else:
            db.add(models.Endereco(
                codigo=cod, rua=rua, predio=pred, andar=and_,
                frente="A", comprimento_cm=120, largura_cm=100,
                altura_cm=200, capacidade_total=1, capacidade_usada=0,
                status_ocupacao="LIVRE"
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
    db.execute(
        text(
            "ALTER TABLE enderecos "
            "ADD COLUMN IF NOT EXISTS status_ocupacao VARCHAR DEFAULT 'LIVRE'"
        )
    )
    db.commit()

    return {
        "status": "ok",
        "mensagem": "Banco atualizado com status_ocupacao"
    }