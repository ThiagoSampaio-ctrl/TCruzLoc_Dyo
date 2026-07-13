import json as _json
import os as _os
import base64 as _b64
from fastapi import FastAPI, Depends
from fastapi.responses import HTMLResponse, JSONResponse, Response
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.database import engine, Base, get_db, ping_db

# ── Routers de API ──────────────────────────────────────────────────
from app.api.auth     import router as router_auth
from app.api.usuarios import router as router_usuarios
from app.api.paletes  import router as router_paletes
from app.api.pedidos  import router as router_pedidos

# ── Routers de Páginas ──────────────────────────────────────────────
from app.pages.dashboard  import router as page_dashboard
from app.pages.conferente import router as page_conferente
from app.pages.operacao   import router as page_operacao
from app.pages.historico  import router as page_historico
from app.pages.perfil     import router as page_perfil
from app.pages.usuarios   import router as page_usuarios

# ── Inicialização ───────────────────────────────────────────────────
Base.metadata.create_all(bind=engine)

app = FastAPI(title="WMS — WALZE WMS", version="4.0")

# ── Registro de routers ─────────────────────────────────────────────
app.include_router(router_auth)
app.include_router(router_usuarios)
app.include_router(router_paletes)
app.include_router(router_pedidos)

app.include_router(page_dashboard)
app.include_router(page_conferente)
app.include_router(page_operacao)
app.include_router(page_historico)
app.include_router(page_perfil)
app.include_router(page_usuarios)


# ── PWA ─────────────────────────────────────────────────────────────
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
       "'/gerenciar-volumes','/historico','/enderecos-page','/perfil','/usuarios','/manifest.json'];"
       "self.addEventListener('install',e=>{e.waitUntil(caches.open(CACHE)"
       ".then(c=>c.addAll(PAGES)).then(()=>self.skipWaiting()));});"
       "self.addEventListener('activate',e=>{e.waitUntil(caches.keys()"
       ".then(ks=>Promise.all(ks.filter(k=>k!==CACHE).map(k=>caches.delete(k))))"
       ".then(()=>self.clients.claim()));});"
       "self.addEventListener('fetch',e=>{"
       "const isApi=['/pedidos','/paletes','/enderecos','/pedidos-volume',"
       "'/auth','/historico-api','/usuarios-api','/dashboard-api','/perfil-api']"
       ".some(p=>e.request.url.includes(p));"
       "if(isApi){e.respondWith(fetch(e.request).catch(()=>new Response("
       "JSON.stringify({detail:'Sem conexão.'}),{status:503,"
       "headers:{'Content-Type':'application/json'}})));return;}"
       "e.respondWith(fetch(e.request).then(r=>{if(r.ok){"
       "const c=r.clone();caches.open(CACHE).then(ch=>ch.put(e.request,c));}return r;})"
       ".catch(()=>caches.match(e.request)));});")


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


# ── Rotas utilitárias ───────────────────────────────────────────────
@app.get("/")
def root():
    return {"status": "ok", "app": "WMS WALZE v4"}

@app.get("/health")
def health():
    ok = ping_db()
    return JSONResponse(status_code=200 if ok else 503,
                        content={"status": "ok" if ok else "db_error", "db": ok})

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
    return {"status": "ok", "erros": erros}


# ── Página de Login (única página que fica no main.py) ──────────────
from app.pages._shared import SHARED

@app.get("/login", response_class=HTMLResponse)
def pg_login():
    return f"""<!DOCTYPE html><html lang="pt-BR"><head>{SHARED}<title>WMS · Login</title>
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

# ── Página: Gerenciar Volumes ────────────────────────────────────────
from app.pages._shared import shell_open, shell_close

@app.get("/gerenciar-volumes", response_class=HTMLResponse)
def pg_gerenciar():
    return ("""<!DOCTYPE html><html lang="pt-BR"><head>""" + SHARED +
            """<title>WMS · Volumes</title></head><body>""" +
            shell_open('vol','🗂️','var(--adim)','Gerenciar Volumes','Visualize, transfira e apague volumes') +
            r"""
<div class="modal-bg" id="modalBg">
  <div class="modal">
    <h3>↔ Transferir Volumes</h3>
    <p style="font-size:12px;color:var(--txt3);margin-bottom:16px;" id="modalInfo">— volumes</p>
    <div class="f"><label>Novo Palete</label><input class="fi" id="tPal" placeholder="Ex: PAL002"></div>
    <div class="f"><label>Novo Endereço</label><input class="fi" id="tEnd" placeholder="Ex: R07 016 1"></div>
    <div class="brow" style="margin-top:4px;">
      <button class="btn ba" onclick="confirmarTransf()">↔ Transferir</button>
      <button class="btn bgh" onclick="fecharModal()">Cancelar</button>
    </div>
    <div id="modalMsg" style="font-size:12px;margin-top:8px;min-height:16px;"></div>
  </div>
</div>
<div style="display:flex;align-items:center;justify-content:space-between;flex-wrap:wrap;gap:10px;margin-bottom:16px;">
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
      border:1px solid var(--br);border-radius:var(--r);font-size:13px;outline:none;" oninput="filtrar()">
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
  var r=await fetch('/pedidos-volume/deletar-varios',{method:'POST',headers:authHeaders(),body:JSON.stringify({ids:ids})});
  var d=await r.json();toast(d.removidos+' volume(s) apagados.');carregar();
}
function abrirTransf(){
  var ids=getIds();if(!ids.length){alert('Selecione os volumes a transferir.');return;}
  document.getElementById('modalInfo').textContent=ids.length+' volume(s) selecionado(s)';
  document.getElementById('tPal').value='';document.getElementById('tEnd').value='';
  document.getElementById('modalMsg').textContent='';
  document.getElementById('modalBg').classList.add('open');document.getElementById('tPal').focus();
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
""" + shell_close() + "</body></html>")

# ── Página: Endereços ────────────────────────────────────────────────
@app.get("/enderecos-page", response_class=HTMLResponse)
def pg_enderecos():
    return ("""<!DOCTYPE html><html lang="pt-BR"><head>""" + SHARED +
            """<title>WMS · Endereços</title></head><body>""" +
            shell_open('end','🏷️','var(--bdim)','Endereços','Gerencie o status de ocupação de cada endereço') +
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
var enderecos=[],filtroAtual='TODOS';
function setFiltro(s){filtroAtual=s;renderGrid();}
async function carregar(){
  document.getElementById('grid').innerHTML='<p style="color:var(--txt3);padding:10px;">Carregando...</p>';
  try{var r=await fetch('/enderecos');enderecos=await r.json();renderGrid();atualizarContadores();}
  catch(e){document.getElementById('grid').innerHTML='<p style="color:var(--rtxt);">Erro ao carregar.</p>';}
}
function corStatus(s){
  if(s==='LIVRE')return{border:'var(--green)',cls:'end-livre'};
  if(s==='PARCIAL')return{border:'var(--amber)',cls:'end-parcial'};
  if(s==='OCUPADO')return{border:'var(--red)',cls:'end-ocupado'};
  return{border:'var(--br2)',cls:'end-bloqueado'};
}
function renderGrid(){
  var g=document.getElementById('grid');g.innerHTML='';
  var lista=filtroAtual==='TODOS'?enderecos:enderecos.filter(function(e){return (e.status_ocupacao||'LIVRE')===filtroAtual;});
  if(!lista.length){g.innerHTML='<p style="color:var(--txt3);padding:10px;">Nenhum endereço encontrado.</p>';return;}
  lista.forEach(function(e){
    var st=e.status_ocupacao||'LIVRE';var c=corStatus(st);
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
    renderGrid();atualizarContadores();toast('✓ '+codigo+' → '+status);
  }catch(e){toast('Erro de conexão','err');}
}
carregar();
</script>
""" + shell_close() + "</body></html>")