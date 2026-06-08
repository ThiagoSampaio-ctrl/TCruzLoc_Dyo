import base64 as _b64
import json as _json
from fastapi import FastAPI, Depends, HTTPException
from fastapi.responses import HTMLResponse, JSONResponse, Response
from sqlalchemy.orm import Session

from app.database import engine, Base, get_db, ping_db
from app import models, schema, crud

Base.metadata.create_all(bind=engine)

app = FastAPI(title="WMS — TCruzLoc", version="2.0")

# PWA
_ICON_192 = _b64.b64decode("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")
_ICON_512 = _b64.b64decode("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")
_MANIFEST = {'name': 'WMS TCruzLoc', 'short_name': 'TCruzLoc', 'description': 'Sistema de gerenciamento de armazém — TCruzLoc_Dyo', 'start_url': '/app', 'display': 'standalone', 'background_color': '#0a0a0a', 'theme_color': '#00e676', 'orientation': 'portrait-primary', 'scope': '/', 'lang': 'pt-BR', 'icons': [{'src': '/icon-192.png', 'sizes': '192x192', 'type': 'image/png', 'purpose': 'any maskable'}, {'src': '/icon-512.png', 'sizes': '512x512', 'type': 'image/png', 'purpose': 'any maskable'}], 'shortcuts': [{'name': 'Conferente', 'short_name': 'Conferente', 'url': '/conferente-v2', 'description': 'Montar paletes e endereçar pedidos'}, {'name': 'Operação', 'short_name': 'Operação', 'url': '/operacao', 'description': 'Consultar pedidos e endereços'}, {'name': 'Volumes', 'short_name': 'Volumes', 'url': '/gerenciar-volumes', 'description': 'Gerenciar volumes cadastrados'}], 'categories': ['business', 'productivity', 'utilities']}
_SW = "const CACHE = 'wms-tcruzloc-v1';\n\n// Recursos que ficam em cache para funcionar offline\nconst PRECACHE = [\n  '/app',\n  '/operacao',\n  '/conferente-v2',\n  '/gerenciar-volumes',\n  '/manifest.json',\n];\n\n// ── Instalação: faz cache dos recursos principais ──\nself.addEventListener('install', e => {\n  e.waitUntil(\n    caches.open(CACHE)\n      .then(c => c.addAll(PRECACHE))\n      .then(() => self.skipWaiting())\n  );\n});\n\n// ── Ativação: limpa caches antigos ──\nself.addEventListener('activate', e => {\n  e.waitUntil(\n    caches.keys().then(keys =>\n      Promise.all(\n        keys.filter(k => k !== CACHE).map(k => caches.delete(k))\n      )\n    ).then(() => self.clients.claim())\n  );\n});\n\n// ── Fetch: network-first para APIs, cache-first para páginas ──\nself.addEventListener('fetch', e => {\n  const url = new URL(e.request.url);\n\n  // Requisições de API sempre vão para a rede (dados precisam ser frescos)\n  const isApi = [\n    '/pedidos', '/paletes', '/enderecos', '/pedidos-volume'\n  ].some(p => url.pathname.startsWith(p));\n\n  if (isApi) {\n    // Network first — se falhar, retorna erro limpo\n    e.respondWith(\n      fetch(e.request).catch(() =>\n        new Response(\n          JSON.stringify({ detail: 'Sem conexão. Verifique a internet.' }),\n          { status: 503, headers: { 'Content-Type': 'application/json' } }\n        )\n      )\n    );\n    return;\n  }\n\n  // Páginas HTML: network first, fallback para cache\n  e.respondWith(\n    fetch(e.request)\n      .then(res => {\n        // Atualiza cache com versão nova\n        if (res.ok) {\n          const clone = res.clone();\n          caches.open(CACHE).then(c => c.put(e.request, clone));\n        }\n        return res;\n      })\n      .catch(() => caches.match(e.request))\n  );\n});\n"

@app.get("/manifest.json")
def pwa_manifest():
    return Response(content=_json.dumps(_MANIFEST, ensure_ascii=False), media_type="application/manifest+json")

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
#  CSS / JS compartilhados injetados em todas as páginas
# ══════════════════════════════════════════════════════════════════
_SHARED = """
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<link rel="manifest" href="/manifest.json">
<meta name="theme-color" content="#00e676">
<meta name="mobile-web-app-capable" content="yes">
<meta name="apple-mobile-web-app-capable" content="yes">
<meta name="apple-mobile-web-app-status-bar-style" content="black-translucent">
<meta name="apple-mobile-web-app-title" content="TCruzLoc">
<link rel="apple-touch-icon" href="/icon-192.png">
<script>
if("serviceWorker" in navigator){
  window.addEventListener("load",()=>{
    navigator.serviceWorker.register("/service-worker.js")
      .then(()=>console.log("PWA pronto"))
      .catch(e=>console.warn("SW:",e));
  });
}
</script>
<link rel="preconnect" href="https://fonts.googleapis.com">
<link href="https://fonts.googleapis.com/css2?family=IBM+Plex+Mono:wght@400;600&family=IBM+Plex+Sans:wght@400;500;600&display=swap" rel="stylesheet">
<style>
:root{
  --bg:#0a0a0a;--surface:#111;--surface2:#181818;--border:#222;
  --green:#00e676;--green-dim:#00e67620;--green-text:#00ff88;
  --blue:#2979ff;--blue-dim:#2979ff18;
  --red:#ff1744;--red-dim:#ff174420;
  --amber:#ffab00;--amber-dim:#ffab0018;
  --text:#e8e8e8;--muted:#666;--muted2:#444;
  --font:'IBM Plex Sans',sans-serif;
  --mono:'IBM Plex Mono',monospace;
  --r:10px;--r-sm:6px;
}
*{box-sizing:border-box;margin:0;padding:0;}
html,body{background:var(--bg);color:var(--text);font-family:var(--font);min-height:100vh;}
a{color:inherit;text-decoration:none;}

/* ── NAV ── */
nav{
  display:flex;align-items:center;gap:0;
  background:var(--surface);border-bottom:1px solid var(--border);
  padding:0 24px;height:56px;position:sticky;top:0;z-index:100;
}
.nav-brand{
  font-family:var(--mono);font-size:15px;font-weight:600;
  color:var(--green-text);letter-spacing:-.3px;margin-right:32px;
  display:flex;align-items:center;gap:8px;
}
.nav-brand::before{
  content:'';display:block;width:8px;height:8px;
  background:var(--green);border-radius:50%;
  box-shadow:0 0 8px var(--green);
}
.nav-links{display:flex;gap:2px;flex:1;}
.nav-link{
  padding:6px 14px;border-radius:var(--r-sm);font-size:13px;
  color:var(--muted);transition:.15s;cursor:pointer;
  border:1px solid transparent;
}
.nav-link:hover{color:var(--text);background:var(--surface2);}
.nav-link.active{color:var(--green-text);background:var(--green-dim);border-color:var(--green-dim);}
.nav-clock{font-family:var(--mono);font-size:12px;color:var(--muted);margin-left:auto;}

/* ── LAYOUT ── */
.page{max-width:900px;margin:0 auto;padding:32px 20px;}
.page-wide{max-width:1200px;margin:0 auto;padding:32px 20px;}

/* ── CARD ── */
.card{
  background:var(--surface);border:1px solid var(--border);
  border-radius:var(--r);padding:28px;margin-bottom:20px;
}
.card-title{
  font-size:11px;letter-spacing:.08em;text-transform:uppercase;
  color:var(--muted);margin-bottom:16px;font-weight:500;
}

/* ── FORM ── */
.field{margin-bottom:16px;}
.field label{
  display:block;font-size:11px;letter-spacing:.06em;text-transform:uppercase;
  color:var(--muted);margin-bottom:8px;font-weight:500;
}
.field input{
  width:100%;padding:14px 16px;
  background:var(--bg);color:var(--green-text);
  border:1px solid var(--border);border-radius:var(--r-sm);
  font-family:var(--mono);font-size:16px;
  transition:.15s;outline:none;
}
.field input:focus{border-color:var(--green);box-shadow:0 0 0 3px var(--green-dim);}
.field input::placeholder{color:var(--muted2);}
.field input.ok{border-color:var(--green);}
.field input.err{border-color:var(--red);box-shadow:0 0 0 3px var(--red-dim);}
.grid-3{display:grid;grid-template-columns:repeat(3,1fr);gap:12px;}

/* ── BOTÕES ── */
.btn{
  display:inline-flex;align-items:center;justify-content:center;gap:8px;
  padding:13px 22px;border:none;border-radius:var(--r-sm);
  font-family:var(--font);font-size:14px;font-weight:600;
  cursor:pointer;transition:.15s;white-space:nowrap;
}
.btn:disabled{opacity:.4;cursor:not-allowed;}
.btn:active:not(:disabled){transform:scale(.97);}
.btn-green{background:var(--green);color:#000;}
.btn-green:hover:not(:disabled){background:#00ff9a;}
.btn-blue{background:var(--blue);color:#fff;}
.btn-blue:hover:not(:disabled){background:#448aff;}
.btn-ghost{background:var(--surface2);color:var(--text);border:1px solid var(--border);}
.btn-ghost:hover:not(:disabled){border-color:var(--muted);}
.btn-danger{background:var(--red-dim);color:var(--red);border:1px solid var(--red-dim);}
.btn-danger:hover:not(:disabled){background:var(--red);color:#fff;}
.btn-row{display:flex;gap:10px;flex-wrap:wrap;}
.btn-full{width:100%;}

/* ── OUTPUT TERMINAL ── */
.terminal{
  background:var(--bg);border:1px solid var(--border);
  border-radius:var(--r);padding:20px;
  font-family:var(--mono);font-size:14px;color:var(--green-text);
  white-space:pre-wrap;min-height:120px;line-height:1.7;
  position:relative;overflow:hidden;
}
.terminal::before{
  content:'OUTPUT';position:absolute;top:8px;right:12px;
  font-size:10px;color:var(--muted2);letter-spacing:.1em;
}

/* ── STATUS BAR ── */
.status-bar{
  min-height:28px;display:flex;align-items:center;gap:8px;
  font-size:13px;padding:4px 0;
}
.status-bar.ok{color:var(--green-text);}
.status-bar.err{color:var(--red);}
.status-bar.warn{color:var(--amber);}
.status-bar.info{color:var(--muted);}
.dot{
  width:6px;height:6px;border-radius:50%;
  background:currentColor;flex-shrink:0;
}

/* ── CHIPS / HISTÓRICO ── */
.chips{display:flex;flex-wrap:wrap;gap:8px;margin-top:12px;}
.chip{
  padding:5px 12px;background:var(--surface2);
  border:1px solid var(--border);border-radius:20px;
  font-family:var(--mono);font-size:12px;color:var(--muted);
  cursor:pointer;transition:.15s;
}
.chip:hover{border-color:var(--green);color:var(--green-text);}

/* ── BUSCA GRANDE ── */
.search-wrap{position:relative;}
.search-wrap input{
  width:100%;padding:20px 20px 20px 52px;
  font-size:22px;font-family:var(--mono);
  background:var(--surface);color:var(--green-text);
  border:1px solid var(--border);border-radius:var(--r);
  outline:none;transition:.15s;
}
.search-wrap input:focus{border-color:var(--green);box-shadow:0 0 0 3px var(--green-dim);}
.search-wrap .search-icon{
  position:absolute;left:18px;top:50%;transform:translateY(-50%);
  font-size:20px;color:var(--muted);pointer-events:none;
}
.search-wrap input.ok{border-color:var(--green);}
.search-wrap input.err{border-color:var(--red);}

/* ── TABLE ── */
.tbl-wrap{overflow-x:auto;}
table{width:100%;border-collapse:collapse;font-size:13px;}
th{
  text-align:left;padding:10px 12px;
  font-size:10px;letter-spacing:.08em;text-transform:uppercase;
  color:var(--muted);border-bottom:1px solid var(--border);
  font-weight:500;
}
td{padding:10px 12px;border-bottom:1px solid var(--border);color:var(--text);}
tr:last-child td{border-bottom:none;}
tr:hover td{background:var(--surface2);}
.badge{
  display:inline-block;padding:2px 8px;border-radius:4px;
  font-family:var(--mono);font-size:11px;font-weight:600;
  background:var(--blue-dim);color:#82b1ff;
}
input[type=checkbox]{
  width:15px;height:15px;accent-color:var(--green);cursor:pointer;
}

/* ── DASH STATS ── */
.stats{display:flex;flex-wrap:wrap;gap:12px;margin-bottom:24px;}
.stat{
  flex:1;min-width:110px;
  background:var(--surface);border:1px solid var(--border);
  border-radius:var(--r);padding:14px 16px;
}
.stat-label{font-size:10px;text-transform:uppercase;letter-spacing:.08em;color:var(--muted);margin-bottom:6px;}
.stat-value{font-family:var(--mono);font-size:22px;font-weight:600;color:var(--green-text);}
.stat-value.red{color:var(--red);}

/* ── DIVIDER ── */
.divider{height:1px;background:var(--border);margin:24px 0;}

/* ── TOAST ── */
#toast{
  position:fixed;bottom:24px;right:24px;
  background:var(--surface);border:1px solid var(--border);
  border-radius:var(--r);padding:12px 18px;
  font-size:13px;z-index:999;
  transform:translateY(80px);opacity:0;
  transition:.25s cubic-bezier(.4,0,.2,1);
  pointer-events:none;max-width:320px;
}
#toast.show{transform:translateY(0);opacity:1;}
#toast.ok{border-color:var(--green);color:var(--green-text);}
#toast.err{border-color:var(--red);color:var(--red);}
</style>
"""

_NAV = """
<nav>
  <div class="nav-brand">WMS · TCruzLoc</div>
  <div class="nav-links">
    <a class="nav-link{a}" href="/app">Início</a>
    <a class="nav-link{b}" href="/conferente-v2">Conferente</a>
    <a class="nav-link{c}" href="/operacao">Operação</a>
    <a class="nav-link{d}" href="/gerenciar-volumes">Volumes</a>
  </div>
  <div class="nav-clock" id="clk"></div>
</nav>
<div id="toast"></div>
<script>
(function(){
  function tick(){var d=new Date();document.getElementById('clk').textContent=d.toLocaleDateString('pt-BR')+' '+d.toLocaleTimeString('pt-BR');}
  setInterval(tick,1000);tick();
  window.toast=function(msg,type){var t=document.getElementById('toast');t.textContent=msg;t.className='show '+(type||'ok');clearTimeout(t._t);t._t=setTimeout(()=>t.className='',3000);};
})();
</script>
"""


def nav(active: str) -> str:
    return _NAV.replace("{a}", " active" if active == "home" else "") \
               .replace("{b}", " active" if active == "conf" else "") \
               .replace("{c}", " active" if active == "oper" else "") \
               .replace("{d}", " active" if active == "vol"  else "")


# ══════════════════════════════════════════════════════════════════
#  ROTAS API
# ══════════════════════════════════════════════════════════════════

@app.get("/")
def root():
    return {"status": "ok", "app": "WMS TCruzLoc v2"}


@app.get("/health")
def health():
    db_ok = ping_db()
    return JSONResponse(
        status_code=200 if db_ok else 503,
        content={"status": "ok" if db_ok else "db_error", "db": db_ok}
    )


@app.get("/enderecos", response_model=list[schema.EnderecoResposta])
def listar_enderecos(db: Session = Depends(get_db)):
    return crud.listar_enderecos(db)


@app.get("/caixas", response_model=list[schema.CaixaResposta])
def listar_caixas(db: Session = Depends(get_db)):
    return crud.listar_caixas(db)


# ── Paletes — estáticas ANTES de dinâmicas ──
@app.post("/paletes/manual", response_model=schema.PaleteResposta)
def criar_palete_manual(dados: schema.PaleteManualCriar, db: Session = Depends(get_db)):
    return crud.criar_ou_usar_palete_manual(db, dados.codigo_palete, dados.codigo_endereco)


@app.post("/paletes/auto", response_model=schema.PaleteResposta)
def criar_palete_auto(palete: schema.PaleteCriar, db: Session = Depends(get_db)):
    return crud.criar_palete_auto(db, palete)


@app.get("/paletes", response_model=list[schema.PaleteResposta])
def listar_paletes(db: Session = Depends(get_db)):
    return crud.listar_paletes(db)


# ── Pedidos-volume — estáticas ANTES de dinâmicas ──
@app.delete("/pedidos-volume/duplicados")
def limpar_duplicados(db: Session = Depends(get_db)):
    return crud.limpar_pedidos_duplicados(db)


@app.post("/pedidos-volume/deletar-varios")
def deletar_varios(dados: schema.DeletarVolumes, db: Session = Depends(get_db)):
    return crud.deletar_varios_pedidos_volume(db, dados.ids)


@app.get("/pedidos-volume")
def listar_volumes(db: Session = Depends(get_db)):
    return crud.listar_pedidos_volume(db)


@app.post("/pedidos-volume", response_model=schema.PedidoVolumeResposta)
def criar_volume(pedido: schema.PedidoVolumeCriar, db: Session = Depends(get_db)):
    return crud.criar_pedido_volume(db, pedido)


@app.delete("/pedidos-volume/{volume_id}")
def deletar_volume(volume_id: int, db: Session = Depends(get_db)):
    return crud.deletar_pedido_volume(db, volume_id)


@app.get("/enderecos/{codigo}/detalhes")
def detalhes_endereco(codigo: str, db: Session = Depends(get_db)):
    return crud.detalhes_endereco(db, codigo)


@app.get("/pedidos/{numero_pedido}")
def buscar_pedido(numero_pedido: str, db: Session = Depends(get_db)):
    return crud.buscar_pedido(db, numero_pedido)


# ══════════════════════════════════════════════════════════════════
#  PÁGINA: HOME / HUB
# ══════════════════════════════════════════════════════════════════

@app.get("/app", response_class=HTMLResponse)
def pg_home():
    return f"""<!DOCTYPE html><html lang="pt-BR"><head>{_SHARED}<title>WMS · TCruzLoc</title></head><body>
{nav('home')}
<div class="page">
  <div style="margin-bottom:32px;">
    <h1 style="font-family:var(--mono);font-size:28px;font-weight:600;color:var(--green-text);margin-bottom:6px;">
      WMS · TCruzLoc_Dyo
    </h1>
    <p style="color:var(--muted);font-size:14px;">Sistema de gerenciamento de armazém — selecione o módulo</p>
  </div>

  <div style="display:grid;grid-template-columns:repeat(auto-fit,minmax(240px,1fr));gap:16px;">
    <a href="/conferente-v2" style="display:block;">
      <div class="card" style="border-color:#1a2a1a;cursor:pointer;transition:.2s;" onmouseover="this.style.borderColor='var(--green)'" onmouseout="this.style.borderColor='#1a2a1a'">
        <div style="font-size:28px;margin-bottom:12px;">📦</div>
        <div style="font-size:16px;font-weight:600;color:var(--green-text);margin-bottom:6px;">Conferente</div>
        <div style="font-size:13px;color:var(--muted);">Montar paletes, endereçar pedidos e registrar volumes no sistema.</div>
        <div style="margin-top:16px;font-size:12px;color:var(--green);font-family:var(--mono);">ACESSAR →</div>
      </div>
    </a>

    <a href="/operacao" style="display:block;">
      <div class="card" style="border-color:#1a1a2a;cursor:pointer;transition:.2s;" onmouseover="this.style.borderColor='var(--blue)'" onmouseout="this.style.borderColor='#1a1a2a'">
        <div style="font-size:28px;margin-bottom:12px;">🔍</div>
        <div style="font-size:16px;font-weight:600;color:#82b1ff;margin-bottom:6px;">Operação</div>
        <div style="font-size:13px;color:var(--muted);">Consultar onde está um pedido ou quais pedidos estão em um endereço.</div>
        <div style="margin-top:16px;font-size:12px;color:var(--blue);font-family:var(--mono);">ACESSAR →</div>
      </div>
    </a>

    <a href="/gerenciar-volumes" style="display:block;">
      <div class="card" style="border-color:#2a1a1a;cursor:pointer;transition:.2s;" onmouseover="this.style.borderColor='var(--amber)'" onmouseout="this.style.borderColor='#2a1a1a'">
        <div style="font-size:28px;margin-bottom:12px;">🗂️</div>
        <div style="font-size:16px;font-weight:600;color:var(--amber);margin-bottom:6px;">Gerenciar Volumes</div>
        <div style="font-size:13px;color:var(--muted);">Visualizar, filtrar e apagar volumes cadastrados no sistema.</div>
        <div style="margin-top:16px;font-size:12px;color:var(--amber);font-family:var(--mono);">ACESSAR →</div>
      </div>
    </a>
  </div>

  <div class="divider"></div>

  <div style="display:flex;gap:12px;flex-wrap:wrap;">
    <a href="/seed"><button class="btn btn-ghost" style="font-size:13px;">⚙️ Inicializar Endereços (/seed)</button></a>
    <a href="/health"><button class="btn btn-ghost" style="font-size:13px;">💚 Status do Banco</button></a>
    <a href="/docs"><button class="btn btn-ghost" style="font-size:13px;">📄 API Docs</button></a>
  </div>
  <p style="font-size:12px;color:var(--muted);margin-top:12px;">
    ⚠️ Se for o primeiro acesso após o deploy, clique em <strong style="color:var(--text)">Inicializar Endereços</strong> para criar os endereços no banco.
  </p>
</div>
</body></html>"""


# ══════════════════════════════════════════════════════════════════
#  PÁGINA: CONFERENTE v2
# ══════════════════════════════════════════════════════════════════

@app.get("/conferente-v2", response_class=HTMLResponse)
def pg_conferente():
    return r"""<!DOCTYPE html><html lang="pt-BR"><head>""" + _SHARED + r"""
<title>WMS · Conferente</title></head><body>
""" + nav("conf") + r"""
<div class="page">
  <div style="margin-bottom:24px;">
    <h1 style="font-family:var(--mono);font-size:22px;font-weight:600;color:var(--green-text);">Montagem de Palete</h1>
    <p style="color:var(--muted);font-size:13px;margin-top:4px;">Informe o palete e endereço, depois adicione os pedidos.</p>
  </div>

  <div class="card">
    <div class="card-title">Identificação do Palete</div>
    <div style="display:grid;grid-template-columns:1fr 1fr;gap:16px;">
      <div class="field">
        <label>Palete</label>
        <input id="palete" placeholder="Ex: PAL001" autofocus>
      </div>
      <div class="field">
        <label>Endereço</label>
        <input id="endereco" placeholder="Ex: R07 014 1">
      </div>
    </div>
  </div>

  <div class="card">
    <div class="card-title">Adicionar Pedido</div>
    <div class="field">
      <label>Número do Pedido</label>
      <input id="pedido" placeholder="Ex: 349596">
    </div>
    <div class="grid-3">
      <div class="field">
        <label>Vol. Inicial</label>
        <input id="vol_ini" type="number" min="1" placeholder="1">
      </div>
      <div class="field">
        <label>Vol. Final</label>
        <input id="vol_fin" type="number" min="1" placeholder="6">
      </div>
      <div class="field">
        <label>Total do Pedido</label>
        <input id="vol_tot" type="number" min="1" placeholder="10">
      </div>
    </div>
    <div class="btn-row" style="margin-top:8px;">
      <button class="btn btn-green" id="btnAdd" onclick="adicionar()">＋ Adicionar ao Palete</button>
      <button class="btn btn-blue"  id="btnFin" onclick="finalizar()">✓ Finalizar Palete</button>
      <button class="btn btn-ghost" onclick="resetar()">↺ Novo Palete</button>
    </div>
  </div>

  <div class="status-bar info" id="stbar"><div class="dot"></div>Aguardando dados...</div>

  <div class="terminal" id="out">Pedidos adicionados aparecerão aqui...</div>

  <div style="margin-top:12px;display:flex;gap:8px;flex-wrap:wrap;" id="statrow">
    <div class="stat" style="flex:0 0 auto;min-width:120px;"><div class="stat-label">Palete</div><div class="stat-value" id="s-pal" style="font-size:15px;">—</div></div>
    <div class="stat" style="flex:0 0 auto;min-width:120px;"><div class="stat-label">Endereço</div><div class="stat-value" id="s-end" style="font-size:15px;">—</div></div>
    <div class="stat" style="flex:0 0 auto;min-width:90px;"><div class="stat-label">Pedidos</div><div class="stat-value" id="s-nped">0</div></div>
    <div class="stat" style="flex:0 0 auto;min-width:90px;"><div class="stat-label">Volumes</div><div class="stat-value" id="s-nvol">0</div></div>
  </div>
</div>

<script>
let resumo = [], totalVols = 0;

function setStatus(msg, type) {
  var el = document.getElementById('stbar');
  el.className = 'status-bar ' + (type||'info');
  el.innerHTML = '<div class="dot"></div>' + msg;
}

function fmt(n,t){ return String(n).padStart(3,'0')+'/'+String(t).padStart(3,'0'); }

function updateStats(){
  var pal = document.getElementById('palete').value.trim()||'—';
  var end = document.getElementById('endereco').value.trim()||'—';
  document.getElementById('s-pal').textContent = pal;
  document.getElementById('s-end').textContent = end;
  var pedSet = new Set(resumo.map(r=>r.pedido));
  document.getElementById('s-nped').textContent = pedSet.size;
  document.getElementById('s-nvol').textContent = totalVols;
}

function renderOut(){
  if(!resumo.length){ document.getElementById('out').textContent='Pedidos adicionados aparecerão aqui...'; return; }
  var pal = resumo[0].palete, end = resumo[0].endereco;
  var ag = {};
  resumo.forEach(r=>{
    if(!ag[r.pedido]) ag[r.pedido]={ini:r.ini,fin:r.fin,tot:r.tot};
    else{ ag[r.pedido].ini=Math.min(ag[r.pedido].ini,r.ini); ag[r.pedido].fin=Math.max(ag[r.pedido].fin,r.fin); }
  });
  var txt='PALETE:   '+pal+'\nENDEREÇO: '+end+'\n\n';
  for(var p in ag){ var a=ag[p]; txt+=p+'\n  '+fmt(a.ini,a.tot)+' → '+fmt(a.fin,a.tot)+'\n\n'; }
  document.getElementById('out').textContent = txt;
}

// navegação por Enter
['palete','endereco','pedido','vol_ini','vol_fin'].forEach(function(id,i){
  var nexts=['endereco','pedido','vol_ini','vol_fin','vol_tot'];
  document.getElementById(id).addEventListener('keydown',function(e){
    if(e.key==='Enter'){ e.preventDefault(); document.getElementById(nexts[i]).focus(); }
  });
});
document.getElementById('vol_tot').addEventListener('keydown',function(e){
  if(e.key==='Enter'){ e.preventDefault(); adicionar(); }
});

async function adicionar(){
  var pal = document.getElementById('palete').value.trim().toUpperCase();
  var end = document.getElementById('endereco').value.trim().toUpperCase();
  var ped = document.getElementById('pedido').value.trim().toUpperCase();
  var ini = parseInt(document.getElementById('vol_ini').value)||0;
  var fin = parseInt(document.getElementById('vol_fin').value)||0;
  var tot = parseInt(document.getElementById('vol_tot').value)||0;

  if(!pal||!end||!ped||!ini||!fin||!tot){ setStatus('⚠ Preencha todos os campos.','warn'); return; }
  if(fin<ini){ setStatus('⚠ Vol. final menor que inicial.','warn'); return; }
  if(fin>tot){ setStatus('⚠ Vol. final maior que total do pedido.','warn'); return; }

  document.getElementById('btnAdd').disabled=true;
  document.getElementById('btnFin').disabled=true;
  setStatus('Criando palete no banco...','info');

  try{
    var rP=await fetch('/paletes/manual',{method:'POST',headers:{'Content-Type':'application/json'},
      body:JSON.stringify({codigo_palete:pal,codigo_endereco:end})});
    var dP=await rP.json();
    if(dP.detail){ setStatus('✕ '+dP.detail,'err'); toast(dP.detail,'err'); return; }

    setStatus('Gravando '+(fin-ini+1)+' volume(s)...','info');
    var erros=[];
    for(var i=ini;i<=fin;i++){
      var rV=await fetch('/pedidos-volume',{method:'POST',headers:{'Content-Type':'application/json'},
        body:JSON.stringify({numero_pedido:ped,volume_atual:i,volume_total:tot,palete_codigo:pal})});
      var dV=await rV.json();
      if(dV.detail) erros.push('Vol '+i+': '+dV.detail);
    }
    if(erros.length){ setStatus('⚠ '+(fin-ini+1-erros.length)+' ok, '+erros.length+' já existiam.','warn'); }
    else{ setStatus('✓ '+(fin-ini+1)+' volume(s) de '+ped+' adicionados!','ok'); toast('Volumes adicionados!'); }

    resumo.push({palete:pal,endereco:end,pedido:ped,ini:ini,fin:fin,tot:tot});
    totalVols+=(fin-ini+1-erros.length);
    renderOut(); updateStats();

    document.getElementById('pedido').value='';
    document.getElementById('vol_ini').value='';
    document.getElementById('vol_fin').value='';
    document.getElementById('vol_tot').value='';
    document.getElementById('pedido').focus();
  }catch(e){
    setStatus('✕ Erro de conexão — verifique o servidor.','err');
    toast('Erro de conexão','err');
    console.error(e);
  }
  document.getElementById('btnAdd').disabled=false;
  document.getElementById('btnFin').disabled=false;
}

function finalizar(){
  var pal=document.getElementById('palete').value.trim();
  var end=document.getElementById('endereco').value.trim();
  if(!pal||!end){ setStatus('⚠ Informe palete e endereço.','warn'); return; }
  if(!resumo.length){ setStatus('⚠ Nenhum pedido adicionado.','warn'); return; }
  var ag={};
  resumo.forEach(r=>{
    if(!ag[r.pedido]) ag[r.pedido]={ini:r.ini,fin:r.fin,tot:r.tot};
    else{ ag[r.pedido].ini=Math.min(ag[r.pedido].ini,r.ini); ag[r.pedido].fin=Math.max(ag[r.pedido].fin,r.fin); }
  });
  var txt='✓ PALETE FINALIZADO\n\nPALETE:   '+pal+'\nENDEREÇO: '+end+'\nSTATUS:   EM USO\n\nRESUMO:\n\n';
  for(var p in ag){ var a=ag[p]; txt+=p+'\n  '+fmt(a.ini,a.tot)+' → '+fmt(a.fin,a.tot)+'\n\n'; }
  document.getElementById('out').textContent=txt;
  setStatus('Palete finalizado. Clique em "Novo Palete" para recomeçar.','ok');
  toast('Palete finalizado!');
  document.getElementById('btnAdd').disabled=true;
  document.getElementById('btnFin').disabled=true;
}

function resetar(){
  resumo=[]; totalVols=0;
  ['palete','endereco','pedido','vol_ini','vol_fin','vol_tot'].forEach(id=>document.getElementById(id).value='');
  document.getElementById('out').textContent='Pedidos adicionados aparecerão aqui...';
  document.getElementById('btnAdd').disabled=false;
  document.getElementById('btnFin').disabled=false;
  setStatus('Pronto para novo palete.','info');
  updateStats();
  document.getElementById('palete').focus();
}
updateStats();
</script>
</body></html>"""


# ══════════════════════════════════════════════════════════════════
#  PÁGINA: OPERAÇÃO (consulta)
# ══════════════════════════════════════════════════════════════════

@app.get("/operacao", response_class=HTMLResponse)
def pg_operacao():
    return r"""<!DOCTYPE html><html lang="pt-BR"><head>""" + _SHARED + r"""
<title>WMS · Operação</title></head><body>
""" + nav("oper") + r"""
<div class="page">
  <div style="margin-bottom:24px;">
    <h1 style="font-family:var(--mono);font-size:22px;font-weight:600;color:#82b1ff;">Consulta Rápida</h1>
    <p style="color:var(--muted);font-size:13px;margin-top:4px;">Bipe ou digite um endereço (R07 014 1) ou número de pedido.</p>
  </div>

  <div class="search-wrap" style="margin-bottom:16px;">
    <span class="search-icon">⌕</span>
    <input id="q" placeholder="Endereço ou pedido..." autofocus
      onkeydown="if(event.key==='Enter')buscar()">
  </div>

  <div class="btn-row" style="margin-bottom:20px;">
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

  <div style="margin-top:16px;">
    <div style="font-size:11px;text-transform:uppercase;letter-spacing:.08em;color:var(--muted);margin-bottom:8px;">Histórico</div>
    <div class="chips" id="hist"></div>
  </div>
</div>

<script>
var nc=0,ne=0,np=0,nr=0,hist=[];
var SOM_OK='https://actions.google.com/sounds/v1/alarms/beep_short.ogg';
var SOM_ERR='https://actions.google.com/sounds/v1/cartoon/pop.ogg';

function beep(url){try{new Audio(url).play();}catch(e){}}

function setOut(txt){document.getElementById('out').textContent=txt;}

function flash(cls){
  var el=document.getElementById('q');
  el.className=cls;
  setTimeout(()=>el.className='',800);
}

function addHist(v){
  if(!v)return;
  hist=[...new Set([v,...hist])].slice(0,12);
  document.getElementById('hist').innerHTML=hist.map(h=>`<div class="chip" onclick="rebuscar('${h}')">${h}</div>`).join('');
  nc++;
  document.getElementById('nc').textContent=nc;
}

function rebuscar(v){document.getElementById('q').value=v;buscar();}

function buscar(){
  var v=document.getElementById('q').value.trim().toUpperCase();
  if(!v)return;
  // auto: começa com R = endereço, senão = pedido
  if(v.match(/^R[0-9]/)||v.match(/^R\s/)) buscarEndereco();
  else buscarPedido();
}

// auto-busca por bipar (debounce)
var _t;
document.getElementById('q').addEventListener('input',function(){
  clearTimeout(_t);
  var v=this.value.trim();
  if(v.length>=5&&!v.toUpperCase().startsWith('R')){
    _t=setTimeout(buscar,500);
  }
});

async function buscarEndereco(){
  var cod=document.getElementById('q').value.trim().toUpperCase();
  if(!cod)return;
  setOut('Buscando...');
  document.querySelectorAll('button').forEach(b=>b.disabled=true);
  try{
    var r=await fetch('/enderecos/'+encodeURIComponent(cod)+'/detalhes');
    var d=await r.json();
    if(!d.paletes||!d.paletes.length){
      setOut('Endereço não encontrado ou sem palete.');
      flash('err');beep(SOM_ERR);nr++;document.getElementById('nr').textContent=nr;
    } else {
      var txt='ENDEREÇO: '+d.endereco+'\n\n';
      d.paletes.forEach(p=>{
        txt+='PALETE: '+p.palete+'\n';
        txt+='─'.repeat(30)+'\n';
        if(!p.pedidos.length) txt+='  (sem pedidos)\n';
        p.pedidos.forEach(ped=>{
          txt+='\n  PEDIDO: '+ped.pedido+'\n';
          ped.volumes.forEach(v=>txt+='    '+v+'\n');
        });
        txt+='\n';
      });
      setOut(txt);
      flash('ok');beep(SOM_OK);addHist(cod);ne++;document.getElementById('ne').textContent=ne;
    }
  }catch(e){
    setOut('Erro ao buscar endereço.');flash('err');beep(SOM_ERR);nr++;document.getElementById('nr').textContent=nr;
  }
  document.querySelectorAll('button').forEach(b=>b.disabled=false);
  document.getElementById('q').value='';
  document.getElementById('q').focus();
}

async function buscarPedido(){
  var cod=document.getElementById('q').value.trim().toUpperCase();
  if(!cod)return;
  setOut('Buscando...');
  document.querySelectorAll('button').forEach(b=>b.disabled=true);
  try{
    var r=await fetch('/pedidos/'+encodeURIComponent(cod));
    var d=await r.json();
    if(d.detail){
      setOut(d.detail);flash('err');beep(SOM_ERR);nr++;document.getElementById('nr').textContent=nr;
    } else {
      var txt='PEDIDO: '+d.pedido+'\n\n';
      d.enderecos.forEach(item=>{
        txt+='ENDEREÇO: '+item.endereco+'\n';
        txt+='PALETE:   '+item.palete+'\n';
        txt+='─'.repeat(30)+'\n';
        item.volumes.forEach(v=>txt+='  '+v+'\n');
        txt+='\n';
      });
      setOut(txt);
      flash('ok');beep(SOM_OK);addHist(cod);np++;document.getElementById('np').textContent=np;
    }
  }catch(e){
    setOut('Erro ao buscar pedido.');flash('err');beep(SOM_ERR);nr++;document.getElementById('nr').textContent=nr;
  }
  document.querySelectorAll('button').forEach(b=>b.disabled=false);
  document.getElementById('q').value='';
  document.getElementById('q').focus();
}
</script>
</body></html>"""


# ══════════════════════════════════════════════════════════════════
#  PÁGINA: GERENCIAR VOLUMES
# ══════════════════════════════════════════════════════════════════

@app.get("/gerenciar-volumes", response_class=HTMLResponse)
def pg_gerenciar():
    return """<!DOCTYPE html><html lang="pt-BR"><head>""" + _SHARED + """
<title>WMS · Volumes</title></head><body>
""" + nav("vol") + """
<div class="page-wide">
  <div style="display:flex;align-items:center;justify-content:space-between;flex-wrap:wrap;gap:12px;margin-bottom:24px;">
    <div>
      <h1 style="font-family:var(--mono);font-size:22px;font-weight:600;color:var(--amber);">Gerenciar Volumes</h1>
      <p style="color:var(--muted);font-size:13px;margin-top:4px;">Visualize, filtre e apague volumes cadastrados.</p>
    </div>
    <div class="btn-row">
      <button class="btn btn-ghost" onclick="carregar()">↺ Atualizar</button>
      <button class="btn btn-ghost" onclick="selAll()">☑ Todos</button>
      <button class="btn btn-ghost" onclick="desSel()">☐ Nenhum</button>
      <button class="btn btn-danger" onclick="apagarSel()">🗑 Apagar Selecionados</button>
    </div>
  </div>

  <div style="display:flex;gap:12px;align-items:center;margin-bottom:16px;flex-wrap:wrap;">
    <input type="text" id="filtro" placeholder="Filtrar por pedido, palete ou endereço..."
      style="flex:1;min-width:200px;padding:10px 14px;background:var(--surface);color:var(--text);
             border:1px solid var(--border);border-radius:var(--r-sm);font-size:14px;outline:none;"
      oninput="filtrar()">
    <span id="info" style="font-size:13px;color:var(--muted);white-space:nowrap;">—</span>
  </div>

  <div class="tbl-wrap">
    <table>
      <thead>
        <tr>
          <th style="width:36px"><input type="checkbox" id="chkAll" onchange="toggleAll(this)"></th>
          <th>ID</th><th>Pedido</th><th>Volume</th><th>Palete</th><th>Endereço</th><th>Ação</th>
        </tr>
      </thead>
      <tbody id="tbody"></tbody>
    </table>
  </div>
</div>

<script>
var dados=[];

async function carregar(){
  document.getElementById('tbody').innerHTML='<tr><td colspan="7" style="color:var(--muted);text-align:center;padding:24px;">Carregando...</td></tr>';
  var r=await fetch('/pedidos-volume');
  dados=await r.json();
  document.getElementById('filtro').value='';
  filtrar();
}

function filtrar(){
  var q=document.getElementById('filtro').value.trim().toLowerCase();
  var fd=q?dados.filter(d=>String(d.numero_pedido).toLowerCase().includes(q)||d.palete_codigo.toLowerCase().includes(q)||(d.endereco_codigo||'').toLowerCase().includes(q)):dados;
  var tb=document.getElementById('tbody');
  if(!fd.length){
    tb.innerHTML='<tr><td colspan="7" style="color:var(--muted);text-align:center;padding:24px;">Nenhum registro.</td></tr>';
    document.getElementById('info').textContent='0 registros';
    return;
  }
  tb.innerHTML=fd.map(d=>{
    var vol=String(d.volume_atual).padStart(3,'0')+'/'+String(d.volume_total).padStart(3,'0');
    return `<tr>
      <td><input type="checkbox" class="chk" value="${d.id}"></td>
      <td style="color:var(--muted);font-family:var(--mono);font-size:12px;">${d.id}</td>
      <td style="font-family:var(--mono);font-weight:600;">${d.numero_pedido}</td>
      <td><span class="badge">${vol}</span></td>
      <td style="color:var(--green-text);font-family:var(--mono);">${d.palete_codigo}</td>
      <td style="color:var(--muted);">${d.endereco_codigo||'—'}</td>
      <td><button class="btn btn-danger" style="padding:5px 10px;font-size:12px;" onclick="apagarUm(${d.id})">Apagar</button></td>
    </tr>`;
  }).join('');
  document.getElementById('info').textContent=fd.length+' registro(s)';
}

function selAll(){document.querySelectorAll('.chk').forEach(c=>c.checked=true);}
function desSel(){document.querySelectorAll('.chk').forEach(c=>c.checked=false);}
function toggleAll(el){document.querySelectorAll('.chk').forEach(c=>c.checked=el.checked);}

async function apagarUm(id){
  if(!confirm('Apagar este volume?'))return;
  await fetch('/pedidos-volume/'+id,{method:'DELETE'});
  toast('Volume apagado.');
  carregar();
}

async function apagarSel(){
  var ids=Array.from(document.querySelectorAll('.chk:checked')).map(c=>parseInt(c.value));
  if(!ids.length){alert('Selecione ao menos um volume.');return;}
  if(!confirm('Apagar '+ids.length+' volume(s)?'))return;
  var r=await fetch('/pedidos-volume/deletar-varios',{method:'POST',
    headers:{'Content-Type':'application/json'},body:JSON.stringify({ids})});
  var d=await r.json();
  toast(d.removidos+' volume(s) apagados.');
  carregar();
}

carregar();
</script>
</body></html>"""


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
            e.rua=rua; e.predio=pred; e.andar=and_
        else:
            db.add(models.Endereco(
                codigo=cod, rua=rua, predio=pred, andar=and_,
                frente="A", comprimento_cm=120, largura_cm=100,
                altura_cm=200, capacidade_total=1, capacidade_usada=0
            ))
            criados += 1
    db.commit()
    return {"status": "ok", "criados": criados, "total": len(enderecos)}


@app.get("/reset-dados")
def reset_dados(db: Session = Depends(get_db)):
    """CUIDADO: apaga todos os paletes e volumes. Endereços são preservados."""
    db.query(models.PedidoVolume).delete()
    db.query(models.Palete).delete()
    db.query(models.Endereco).update({"capacidade_usada": 0})
    db.commit()
    return {"status": "ok", "aviso": "Paletes e volumes apagados. Endereços mantidos."}
