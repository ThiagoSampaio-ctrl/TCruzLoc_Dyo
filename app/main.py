from fastapi import FastAPI, Depends, HTTPException
from fastapi.responses import HTMLResponse, JSONResponse
from sqlalchemy.orm import Session

from app.database import engine, Base, get_db, ping_db
from app import models, schema, crud

Base.metadata.create_all(bind=engine)

app = FastAPI(title="WMS — TCruzLoc", version="2.0")

# ══════════════════════════════════════════════════════════════════
#  CSS / JS compartilhados injetados em todas as páginas
# ══════════════════════════════════════════════════════════════════
_SHARED = """
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
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
