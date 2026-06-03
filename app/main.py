from fastapi.responses import HTMLResponse
from fastapi import FastAPI, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import engine, Base, SessionLocal
from app import models, schema, crud

Base.metadata.create_all(bind=engine)

app = FastAPI(title="SmartLocator")


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


# ─────────────────────────────────────────────
#  ROTAS BÁSICAS
# ─────────────────────────────────────────────

@app.get("/")
def home():
    return {"message": "SmartLocator funcionando"}


@app.get("/enderecos", response_model=list[schema.EnderecoResposta])
def listar_enderecos(db: Session = Depends(get_db)):
    return crud.listar_enderecos(db)


@app.get("/caixas", response_model=list[schema.CaixaResposta])
def listar_caixas(db: Session = Depends(get_db)):
    return crud.listar_caixas(db)


# ─────────────────────────────────────────────
#  PALETES  — rotas estáticas ANTES das dinâmicas
# ─────────────────────────────────────────────

@app.post("/paletes/manual", response_model=schema.PaleteResposta)
def criar_palete_manual(
    dados: schema.PaleteManualCriar,
    db: Session = Depends(get_db)
):
    return crud.criar_ou_usar_palete_manual(
        db,
        dados.codigo_palete,
        dados.codigo_endereco
    )


@app.post("/paletes/auto", response_model=schema.PaleteResposta)
def criar_palete_auto(palete: schema.PaleteCriar, db: Session = Depends(get_db)):
    return crud.criar_palete_auto(db, palete)


@app.get("/paletes", response_model=list[schema.PaleteResposta])
def listar_paletes(db: Session = Depends(get_db)):
    return crud.listar_paletes(db)


# ─────────────────────────────────────────────
#  PEDIDOS-VOLUME — rotas estáticas ANTES das dinâmicas
#  ORDEM IMPORTA no FastAPI: /duplicados e /deletar-varios
#  devem vir ANTES de /{volume_id}
# ─────────────────────────────────────────────

@app.delete("/pedidos-volume/duplicados")
def limpar_pedidos_duplicados(db: Session = Depends(get_db)):
    return crud.limpar_pedidos_duplicados(db)


@app.post("/pedidos-volume/deletar-varios")
def deletar_varios_pedidos_volume(
    dados: schema.DeletarVolumes,
    db: Session = Depends(get_db)
):
    return crud.deletar_varios_pedidos_volume(db, dados.ids)


@app.get("/pedidos-volume")
def listar_pedidos_volume(db: Session = Depends(get_db)):
    return crud.listar_pedidos_volume(db)


@app.post("/pedidos-volume", response_model=schema.PedidoVolumeResposta)
def criar_pedido_volume(pedido: schema.PedidoVolumeCriar, db: Session = Depends(get_db)):
    return crud.criar_pedido_volume(db, pedido)


@app.delete("/pedidos-volume/{volume_id}")
def deletar_pedido_volume(volume_id: int, db: Session = Depends(get_db)):
    return crud.deletar_pedido_volume(db, volume_id)


# ─────────────────────────────────────────────
#  ENDEREÇOS — rotas estáticas ANTES das dinâmicas
# ─────────────────────────────────────────────

@app.get("/enderecos/{codigo_endereco}/detalhes")
def detalhes_endereco(codigo_endereco: str, db: Session = Depends(get_db)):
    return crud.detalhes_endereco(db, codigo_endereco)


# ─────────────────────────────────────────────
#  PEDIDOS
# ─────────────────────────────────────────────

@app.get("/pedidos/{numero_pedido}")
def buscar_pedido(numero_pedido: str, db: Session = Depends(get_db)):
    return crud.buscar_pedido(db, numero_pedido)


# ─────────────────────────────────────────────
#  TELA DE OPERAÇÃO  (consulta por endereço ou pedido)
# ─────────────────────────────────────────────

@app.get("/operacao", response_class=HTMLResponse)
def tela_operacao():
    return """<!DOCTYPE html>
<html lang="pt-BR">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>TCruzLoc_Dyo – Operação</title>
<style>
*{box-sizing:border-box;margin:0;padding:0;}
body{font-family:Arial,sans-serif;background:#111;color:white;padding:20px;}
.box{background:#1b1b1b;max-width:950px;margin:auto;padding:30px;border-radius:14px;box-shadow:0 0 20px #000;}
h1{font-size:38px;color:#00ff88;margin-bottom:4px;}
#relogio{color:#00ff88;font-size:16px;font-weight:bold;margin-bottom:18px;}
h2{font-size:22px;margin-bottom:12px;}
input{
    width:100%;padding:20px;font-size:32px;
    background:#000;color:#00ff88;
    border:3px solid #00ff88;border-radius:10px;
    margin-bottom:16px;caret-color:#00ff88;
}
input::placeholder{color:#555;}
input.sucesso{border-color:#00ff88!important;box-shadow:0 0 16px #00ff88;}
input.erro{border-color:#ff3333!important;box-shadow:0 0 16px #ff3333;}
.btns{display:flex;gap:12px;margin-bottom:0;}
button{
    flex:1;padding:18px;font-size:22px;
    border:none;border-radius:10px;cursor:pointer;
    background:#333;color:white;transition:transform .12s;
}
button:hover{transform:scale(1.02);}
button:disabled{opacity:.5;cursor:not-allowed;transform:none;}
.btn-endereco{background:#0d6efd;}
.btn-pedido{background:#198754;}
pre{
    background:#000;color:#00ff88;
    padding:26px;font-size:26px;
    white-space:pre-wrap;margin-top:20px;
    border-radius:12px;min-height:260px;
    border:2px solid #333;
}
#dashboard{display:flex;flex-wrap:wrap;gap:14px;margin-top:16px;font-weight:bold;font-size:16px;}
#dashboard span{color:#00ff88;}
#contadorErros{color:#ff4444!important;}
#historico{margin-top:18px;display:flex;flex-wrap:wrap;gap:8px;}
.item-hist{
    background:#222;color:#00ff88;
    border:1px solid #00ff88;
    padding:8px 16px;border-radius:8px;
    cursor:pointer;font-size:16px;
}
.item-hist:hover{background:#00ff8820;}
h3{margin-top:20px;margin-bottom:8px;font-size:18px;color:#aaa;}
</style>
</head>
<body>
<div class="box">
  <h1>TCruzLoc_Dyo</h1>
  <div id="relogio"></div>

  <h2>Bipar / Digitar endereço ou pedido</h2>
  <input id="codigo" placeholder="Ex: R07 014 1 ou 349596" autofocus
         onkeypress="if(event.key==='Enter') buscarAutomatico()">

  <div class="btns">
    <button class="btn-endereco" onclick="buscarEndereco()">🔍 Buscar Endereço</button>
    <button class="btn-pedido"   onclick="buscarPedido()">📦 Buscar Pedido</button>
  </div>

  <pre id="resultado">Aguardando leitura...</pre>

  <div id="dashboard">
    <span id="cConsultas">Consultas: 0</span>
    <span id="cPedidos">Pedidos: 0</span>
    <span id="cEnderecos">Endereços: 0</span>
    <span id="contadorErros">Erros: 0</span>
  </div>

  <h3>Últimas consultas</h3>
  <div id="historico"></div>
</div>

<script>
// ── relógio ──
function tick(){
    const d = new Date()
    document.getElementById("relogio").textContent =
        d.toLocaleDateString("pt-BR") + "  " + d.toLocaleTimeString("pt-BR")
}
setInterval(tick, 1000); tick()

// ── estado ──
let historico = [], nConsultas=0, nPedidos=0, nEnderecos=0, nErros=0
let timerAuto = null

// ── auto-busca ao digitar ──
document.getElementById("codigo").addEventListener("input", function(){
    clearTimeout(timerAuto)
    const v = this.value.trim()
    // só dispara auto se não começar com R (endereço) e tiver >= 5 chars
    if(!v.toUpperCase().startsWith("R") && v.length >= 5){
        timerAuto = setTimeout(buscarAutomatico, 600)
    }
})

function buscarAutomatico(){
    let codigo = document.getElementById("codigo").value.trim().toUpperCase()

    // formatar endereço bipado sem espaços: R070141 -> R07 014 1
    if(/^R\d{6,}$/.test(codigo) && codigo.length === 7){
        codigo = codigo.substring(0,3)+" "+codigo.substring(3,6)+" "+codigo.substring(6)
        document.getElementById("codigo").value = codigo
    }

    if(codigo.startsWith("R")) buscarEndereco()
    else buscarPedido()
}

// ── feedback visual ──
function flash(cls){
    const el = document.getElementById("codigo")
    el.classList.add(cls)
    setTimeout(()=>el.classList.remove(cls), 800)
}

// ── sons ──
function beep(url){ try{ new Audio(url).play() }catch(e){} }
const SOM_OK  = "https://actions.google.com/sounds/v1/alarms/beep_short.ogg"
const SOM_ERR = "https://actions.google.com/sounds/v1/cartoon/pop.ogg"

// ── loading ──
function loading(sim){
    document.querySelectorAll("button").forEach(b => b.disabled = sim)
    if(sim) document.getElementById("resultado").textContent = "⏳ Buscando..."
}

function limpar(){ document.getElementById("codigo").value=""; document.getElementById("codigo").focus() }

// ── dashboard ──
function dash(){
    document.getElementById("cConsultas").textContent  = "Consultas: "+nConsultas
    document.getElementById("cPedidos").textContent    = "Pedidos: "+nPedidos
    document.getElementById("cEnderecos").textContent  = "Endereços: "+nEnderecos
    document.getElementById("contadorErros").textContent = "Erros: "+nErros
}

function addHist(v){
    if(!v) return
    historico = [...new Set([v,...historico])].slice(0,10)
    document.getElementById("historico").innerHTML =
        historico.map(h=>`<div class="item-hist" onclick="rebuscar('${h}')">${h}</div>`).join("")
    nConsultas++; dash()
}

function rebuscar(v){ document.getElementById("codigo").value=v; buscarAutomatico() }

// ── buscar endereço ──
async function buscarEndereco(){
    const codigo = document.getElementById("codigo").value.trim()
    if(!codigo) return
    loading(true)
    try{
        const r = await fetch("/enderecos/"+encodeURIComponent(codigo)+"/detalhes")
        const d = await r.json()

        if(!d.paletes || d.paletes.length===0){
            document.getElementById("resultado").textContent = "❌ Endereço não encontrado ou sem palete."
            flash("erro"); beep(SOM_ERR); nErros++; dash(); limpar()
            loading(false); return
        }

        let txt = "ENDEREÇO: "+d.endereco+"\n\n"
        d.paletes.forEach(p=>{
            txt += "PALETE: "+p.palete+"\n\nPEDIDOS:\n\n"
            p.pedidos.forEach(ped=>{
                txt += ped.pedido+"\n"
                ped.volumes.forEach(v=> txt += "  "+v+"\n")
                txt += "\n"
            })
        })

        document.getElementById("resultado").textContent = txt
        flash("sucesso"); beep(SOM_OK); addHist(codigo); nEnderecos++; dash()
    }catch(e){
        document.getElementById("resultado").textContent = "❌ Erro ao buscar endereço."
        flash("erro"); beep(SOM_ERR); nErros++; dash()
    }
    loading(false); limpar()
}

// ── buscar pedido ──
async function buscarPedido(){
    const codigo = document.getElementById("codigo").value.trim()
    if(!codigo) return
    loading(true)
    try{
        const r = await fetch("/pedidos/"+encodeURIComponent(codigo))
        const d = await r.json()

        if(d.detail){
            document.getElementById("resultado").textContent = "❌ "+d.detail
            flash("erro"); beep(SOM_ERR); nErros++; dash(); limpar()
            loading(false); return
        }

        let txt = "PEDIDO: "+d.pedido+"\n\n"
        d.enderecos.forEach(item=>{
            txt += "ENDEREÇO: "+item.endereco+"\n"
            txt += "PALETE:   "+item.palete+"\n\n"
            txt += "VOLUMES:\n"
            item.volumes.forEach(v=> txt += "  "+v+"\n")
            txt += "\n"
        })

        document.getElementById("resultado").textContent = txt
        flash("sucesso"); beep(SOM_OK); addHist(codigo); nPedidos++; dash()
    }catch(e){
        document.getElementById("resultado").textContent = "❌ Erro ao buscar pedido."
        flash("erro"); beep(SOM_ERR); nErros++; dash()
    }
    loading(false); limpar()
}
</script>
</body>
</html>"""


# ─────────────────────────────────────────────
#  TELA CONFERENTE v1  (cadastro simples)
# ─────────────────────────────────────────────

@app.get("/conferente", response_class=HTMLResponse)
def tela_conferente():
    return r"""<!DOCTYPE html>
<html lang="pt-BR">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>TCruzLoc_Dyo – Conferente</title>
<style>
*{box-sizing:border-box;margin:0;padding:0;}
body{font-family:Arial,sans-serif;background:#111;color:white;padding:20px;}
.box{
    background:#1b1b1b;max-width:750px;margin:auto;
    padding:30px;border-radius:14px;box-shadow:0 0 20px #000;
    transition:box-shadow .3s,border .3s;border:2px solid transparent;
}
.box.sucesso{border-color:#00ff88;box-shadow:0 0 24px #00ff88;}
.box.erro{border-color:#ff3333;box-shadow:0 0 24px #ff3333;}
h1{color:#00ff88;font-size:36px;margin-bottom:4px;}
h2{font-size:22px;margin-bottom:20px;color:#aaa;}
label{display:block;margin-top:14px;margin-bottom:6px;font-size:16px;color:#00ff88;}
input{
    width:100%;padding:16px;font-size:24px;
    background:#000;color:#00ff88;
    border:2px solid #00ff88;border-radius:10px;
}
input::placeholder{color:#555;}
button{
    width:100%;margin-top:22px;padding:18px;font-size:22px;
    background:#198754;color:white;border:none;border-radius:10px;cursor:pointer;
    transition:transform .12s;
}
button:hover{transform:scale(1.01);}
button:disabled{opacity:.5;cursor:not-allowed;transform:none;}
pre{
    background:#000;color:#00ff88;padding:22px;font-size:20px;
    white-space:pre-wrap;margin-top:20px;border-radius:12px;
    border:2px solid #333;min-height:120px;
}
</style>
</head>
<body>
<div class="box" id="box">
  <h1>TCruzLoc_Dyo</h1>
  <h2>Conferente — Cadastro de Volumes</h2>

  <label>Pedido</label>
  <input id="pedido" placeholder="Ex: 349596" autofocus>

  <label>Quantidade de volumes</label>
  <input id="volume_total" type="number" min="1" placeholder="Ex: 3">

  <label>Palete</label>
  <input id="palete" placeholder="Ex: PAL001">

  <button id="btnCadastrar" onclick="cadastrarVolume()">Cadastrar Volumes</button>

  <pre id="resultado">Aguardando cadastro...</pre>
</div>

<script>
// permitir Enter nos campos para avançar / cadastrar
document.getElementById("pedido").addEventListener("keypress", e=>{
    if(e.key==="Enter") document.getElementById("volume_total").focus()
})
document.getElementById("volume_total").addEventListener("keypress", e=>{
    if(e.key==="Enter") document.getElementById("palete").focus()
})
document.getElementById("palete").addEventListener("keypress", e=>{
    if(e.key==="Enter") cadastrarVolume()
})

function flash(cls){
    const box = document.getElementById("box")
    box.classList.add(cls)
    setTimeout(()=>box.classList.remove(cls), 900)
}

async function cadastrarVolume(){
    const pedido      = document.getElementById("pedido").value.trim()
    const volumeTotal = parseInt(document.getElementById("volume_total").value.trim())
    const palete      = document.getElementById("palete").value.trim()   // ← CORRIGIDO: ler do input
    const resultado   = document.getElementById("resultado")
    const btn         = document.getElementById("btnCadastrar")

    if(!pedido || !volumeTotal || volumeTotal < 1 || !palete){
        resultado.textContent = "⚠️ Preencha todos os campos corretamente."
        flash("erro"); return
    }

    btn.disabled = true
    resultado.textContent = "⏳ Cadastrando volumes..."

    try{
        let cadastrados = ""
        let erros = []

        for(let i=1; i<=volumeTotal; i++){
            const resp = await fetch("/pedidos-volume",{
                method:"POST",
                headers:{"Content-Type":"application/json"},
                body:JSON.stringify({
                    numero_pedido: pedido,
                    volume_atual: i,
                    volume_total: volumeTotal,
                    palete_codigo: palete
                })
            })
            const dados = await resp.json()

            if(dados.detail){
                erros.push("Vol "+i+": "+dados.detail)
            } else {
                cadastrados += pedido+" "+
                    String(i).padStart(3,"0")+"/"+
                    String(volumeTotal).padStart(3,"0")+"\n"
            }
        }

        if(erros.length > 0){
            resultado.textContent = "⚠️ Alguns erros:\n\n"+erros.join("\n")
            flash("erro")
        } else {
            resultado.textContent =
                "✅ VOLUMES CADASTRADOS!\n\n"+
                cadastrados+
                "\nPalete: "+palete
            flash("sucesso")
            document.getElementById("pedido").value=""
            document.getElementById("volume_total").value=""
            document.getElementById("pedido").focus()
        }
    }catch(e){
        resultado.textContent = "❌ Erro de conexão ao cadastrar."
        flash("erro")
    }
    btn.disabled = false
}
</script>
</body>
</html>"""


# ─────────────────────────────────────────────
#  TELA CONFERENTE v2  (montagem inteligente de palete)
# ─────────────────────────────────────────────

@app.get("/conferente-v2", response_class=HTMLResponse)
def tela_conferente_v2():
   return r"""<!DOCTYPE html>
<html lang="pt-BR">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>TCruzLoc_Dyo – Montagem Palete</title>
<style>
*{box-sizing:border-box;margin:0;padding:0;}
body{font-family:Arial,sans-serif;background:#111;color:white;padding:20px;}
.box{background:#1b1b1b;max-width:950px;margin:auto;padding:30px;border-radius:14px;box-shadow:0 0 20px #000;}
h1{color:#00ff88;font-size:38px;margin-bottom:4px;}
h2{font-size:20px;color:#aaa;margin-bottom:18px;}
label{color:#00ff88;font-weight:bold;display:block;margin-top:14px;margin-bottom:5px;}
input{
    width:100%;padding:14px;font-size:22px;
    background:#000;color:#00ff88;
    border:2px solid #00ff88;border-radius:10px;margin-top:4px;
}
input::placeholder{color:#555;}
hr{border-color:#333;margin:22px 0;}
.grid{display:grid;grid-template-columns:repeat(3,1fr);gap:12px;}
.btns{display:flex;gap:12px;margin-top:22px;}
button{
    flex:1;padding:18px;font-size:20px;
    color:white;border:none;border-radius:10px;cursor:pointer;
    transition:transform .12s;
}
button:hover{transform:scale(1.01);}
button:disabled{opacity:.5;cursor:not-allowed;transform:none;}
.btn-add{background:#198754;}
.btn-fin{background:#0d6efd;}
.btn-reset{background:#6c757d;font-size:16px;padding:10px;}
pre{
    background:#000;color:#00ff88;padding:22px;font-size:20px;
    white-space:pre-wrap;margin-top:20px;border-radius:12px;
    border:2px solid #333;min-height:160px;
}
#status{
    margin-top:10px;font-size:14px;color:#aaa;
    min-height:20px;
}
</style>
</head>
<body>
<div class="box">
  <h1>TCruzLoc_Dyo</h1>
  <h2>Montagem Inteligente de Palete</h2>

  <label>Palete</label>
  <input id="palete" placeholder="Ex: PAL001" autofocus>

  <label>Endereço</label>
  <input id="endereco" placeholder="Ex: R07 014 1">

  <hr>

  <label>Pedido</label>
  <input id="pedido" placeholder="Ex: 349596">

  <div class="grid">
    <div>
      <label>Vol. inicial</label>
      <input id="vol_inicial" type="number" min="1" placeholder="1">
    </div>
    <div>
      <label>Vol. final</label>
      <input id="vol_final" type="number" min="1" placeholder="6">
    </div>
    <div>
      <label>Total do pedido</label>
      <input id="vol_total" type="number" min="1" placeholder="10">
    </div>
  </div>

  <div class="btns">
    <button class="btn-add" id="btnAdd" onclick="adicionarAoPalete()">➕ Adicionar ao Palete</button>
    <button class="btn-fin" id="btnFin" onclick="finalizarPalete()">✅ Finalizar Palete</button>
  </div>
  <div style="margin-top:10px;">
    <button class="btn-reset" onclick="resetarTela()">🔄 Novo palete</button>
  </div>

  <div id="status"></div>
  <pre id="resultado">Pedidos no palete aparecerão aqui...</pre>
</div>

<script>
let resumo = []

// ── navegação por Enter ──
document.getElementById("palete").addEventListener("keypress",    e=>{ if(e.key==="Enter") document.getElementById("endereco").focus() })
document.getElementById("endereco").addEventListener("keypress",  e=>{ if(e.key==="Enter") document.getElementById("pedido").focus() })
document.getElementById("pedido").addEventListener("keypress",    e=>{ if(e.key==="Enter") document.getElementById("vol_inicial").focus() })
document.getElementById("vol_inicial").addEventListener("keypress",e=>{ if(e.key==="Enter") document.getElementById("vol_final").focus() })
document.getElementById("vol_final").addEventListener("keypress", e=>{ if(e.key==="Enter") document.getElementById("vol_total").focus() })
document.getElementById("vol_total").addEventListener("keypress", e=>{ if(e.key==="Enter") adicionarAoPalete() })

function status(msg, cor="#aaa"){
    const el = document.getElementById("status")
    el.textContent = msg
    el.style.color = cor
}

function fmt(n, t){ return String(n).padStart(3,"0")+"/"+String(t).padStart(3,"0") }

function renderResumo(){
    if(resumo.length===0){
        document.getElementById("resultado").textContent = "Pedidos no palete aparecerão aqui..."
        return
    }
    const palete   = resumo[0].palete
    const endereco = resumo[0].endereco

    // agrupa pedidos (mesmo pedido pode ter sido adicionado em lotes)
    let agrupado = {}
    resumo.forEach(item=>{
        if(!agrupado[item.pedido]){
            agrupado[item.pedido] = {ini:item.ini, fin:item.fin, total:item.total}
        } else {
            agrupado[item.pedido].ini = Math.min(agrupado[item.pedido].ini, item.ini)
            agrupado[item.pedido].fin = Math.max(agrupado[item.pedido].fin, item.fin)
        }
    })

    let txt = "PALETE:   "+palete+"\nENDEREÇO: "+endereco+"\n\n"+"PEDIDOS:\n\n"
    for(const ped in agrupado){
        const a = agrupado[ped]
        txt += ped+"\n  "+fmt(a.ini,a.total)+" até "+fmt(a.fin,a.total)+"\n\n"
    }
    document.getElementById("resultado").textContent = txt
}

async function adicionarAoPalete(){
    const palete   = document.getElementById("palete").value.trim()
    const endereco = document.getElementById("endereco").value.trim()
    const pedido   = document.getElementById("pedido").value.trim()
    const ini      = parseInt(document.getElementById("vol_inicial").value)
    const fin      = parseInt(document.getElementById("vol_final").value)
    const total    = parseInt(document.getElementById("vol_total").value)

    if(!palete || !endereco || !pedido || !ini || !fin || !total){
        status("⚠️ Preencha todos os campos.", "#ffaa00"); return
    }
    if(fin < ini){
        status("⚠️ Vol. final não pode ser menor que o inicial.", "#ffaa00"); return
    }
    if(fin > total){
        status("⚠️ Vol. final não pode ser maior que o total.", "#ffaa00"); return
    }

    document.getElementById("btnAdd").disabled = true
    document.getElementById("btnFin").disabled = true
    status("⏳ Criando/verificando palete...")

    try{
        // 1. cria ou reutiliza palete
        const rPalete = await fetch("/paletes/manual",{
            method:"POST",
            headers:{"Content-Type":"application/json"},
            body:JSON.stringify({codigo_palete:palete, codigo_endereco:endereco})
        })
        const dPalete = await rPalete.json()

        if(dPalete.detail){
            status("❌ "+dPalete.detail, "#ff4444")
            document.getElementById("btnAdd").disabled = false
            document.getElementById("btnFin").disabled = false
            return
        }

        status("⏳ Cadastrando "+(fin-ini+1)+" volume(s)...")

        // 2. cadastra cada volume
        for(let i=ini; i<=fin; i++){
            const rVol = await fetch("/pedidos-volume",{
                method:"POST",
                headers:{"Content-Type":"application/json"},
                body:JSON.stringify({
                    numero_pedido: pedido,
                    volume_atual:  i,
                    volume_total:  total,
                    palete_codigo: palete
                })
            })
            const dVol = await rVol.json()
            if(dVol.detail){
                status("❌ Vol "+i+": "+dVol.detail, "#ff4444")
                document.getElementById("btnAdd").disabled = false
                document.getElementById("btnFin").disabled = false
                return
            }
        }

        resumo.push({palete, endereco, pedido, ini, fin, total})
        renderResumo()
        status("✅ "+(fin-ini+1)+" volume(s) de "+pedido+" adicionados!", "#00ff88")

        // limpa só os campos de pedido/volume
        document.getElementById("pedido").value=""
        document.getElementById("vol_inicial").value=""
        document.getElementById("vol_final").value=""
        document.getElementById("vol_total").value=""
        document.getElementById("pedido").focus()

    }catch(e){
        status("❌ Erro de conexão. Verifique o servidor.", "#ff4444")
        console.error(e)
    }

    document.getElementById("btnAdd").disabled = false
    document.getElementById("btnFin").disabled = false
}

function finalizarPalete(){
    const palete   = document.getElementById("palete").value.trim()
    const endereco = document.getElementById("endereco").value.trim()

    if(!palete || !endereco){
        status("⚠️ Informe palete e endereço.", "#ffaa00"); return
    }
    if(resumo.length===0){
        status("⚠️ Nenhum pedido adicionado ainda.", "#ffaa00"); return
    }

    let agrupado = {}
    resumo.forEach(item=>{
        if(!agrupado[item.pedido]) agrupado[item.pedido]={ini:item.ini,fin:item.fin,total:item.total}
        else{
            agrupado[item.pedido].ini = Math.min(agrupado[item.pedido].ini, item.ini)
            agrupado[item.pedido].fin = Math.max(agrupado[item.pedido].fin, item.fin)
        }
    })

    let txt = "✅ PALETE FINALIZADO\n\n"
    txt += "PALETE:   "+palete+"\nENDEREÇO: "+endereco+"\nSTATUS:   EM USO\n\n"
    txt += "RESUMO:\n\n"
    for(const ped in agrupado){
        const a = agrupado[ped]
        txt += ped+"\n  "+fmt(a.ini,a.total)+" até "+fmt(a.fin,a.total)+"\n\n"
    }
    document.getElementById("resultado").textContent = txt
    status("Palete finalizado. Clique em 'Novo palete' para recomeçar.", "#00ff88")
    document.getElementById("btnAdd").disabled = true
    document.getElementById("btnFin").disabled = true
}

function resetarTela(){
    resumo = []
    document.getElementById("palete").value=""
    document.getElementById("endereco").value=""
    document.getElementById("pedido").value=""
    document.getElementById("vol_inicial").value=""
    document.getElementById("vol_final").value=""
    document.getElementById("vol_total").value=""
    document.getElementById("resultado").textContent="Pedidos no palete aparecerão aqui..."
    document.getElementById("btnAdd").disabled=false
    document.getElementById("btnFin").disabled=false
    status("")
    document.getElementById("palete").focus()
}
</script>
</body>
</html>"""


# ─────────────────────────────────────────────
#  GERENCIAR VOLUMES
# ─────────────────────────────────────────────

@app.get("/gerenciar-volumes", response_class=HTMLResponse)
def gerenciar_volumes():
    return """<!DOCTYPE html>
<html lang="pt-BR">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Gerenciar Volumes</title>
<style>
*{box-sizing:border-box;margin:0;padding:0;}
body{font-family:Arial;background:#111;color:white;padding:20px;}
.box{background:#1b1b1b;max-width:1100px;margin:auto;padding:28px;border-radius:14px;}
h1{color:#00ff88;margin-bottom:16px;}
.toolbar{display:flex;flex-wrap:wrap;gap:10px;margin-bottom:16px;align-items:center;}
input[type=text]{
    padding:10px 14px;font-size:16px;background:#000;color:#00ff88;
    border:2px solid #00ff88;border-radius:8px;width:260px;
}
input::placeholder{color:#555;}
button{padding:10px 18px;background:#198754;color:white;border:none;border-radius:8px;cursor:pointer;font-size:15px;}
button:hover{opacity:.85;}
button.danger{background:#dc3545;}
button.secondary{background:#444;}
#info{font-size:14px;color:#aaa;margin-left:auto;}
table{width:100%;border-collapse:collapse;margin-top:8px;}
th,td{border:1px solid #333;padding:10px;text-align:left;font-size:14px;}
th{color:#00ff88;background:#1a1a1a;position:sticky;top:0;}
tr:hover{background:#1f1f1f;}
input[type=checkbox]{width:16px;height:16px;cursor:pointer;}
.tag{
    display:inline-block;padding:2px 8px;border-radius:4px;
    font-size:12px;background:#0d6efd33;color:#6ea8fe;border:1px solid #0d6efd55;
}
</style>
</head>
<body>
<div class="box">
  <h1>Gerenciar Volumes</h1>

  <div class="toolbar">
    <button onclick="carregar()">🔄 Atualizar</button>
    <button onclick="selecionarTodos()" class="secondary">☑ Selecionar todos</button>
    <button onclick="desselecionarTodos()" class="secondary">☐ Desmarcar todos</button>
    <button onclick="apagarSelecionados()" class="danger">🗑 Apagar selecionados</button>
    <input type="text" id="filtro" placeholder="Filtrar pedido / palete / endereço..." oninput="filtrar()">
    <span id="info">–</span>
  </div>

  <table>
    <thead>
      <tr>
        <th style="width:36px"><input type="checkbox" id="chkAll" onchange="toggleAll(this)"></th>
        <th>ID</th>
        <th>Pedido</th>
        <th>Volume</th>
        <th>Palete</th>
        <th>Endereço</th>
        <th style="width:90px">Ação</th>
      </tr>
    </thead>
    <tbody id="tabela"></tbody>
  </table>
</div>

<script>
let dados = []

async function carregar(){
    document.getElementById("tabela").innerHTML = "<tr><td colspan='7' style='color:#aaa'>Carregando...</td></tr>"
    const r = await fetch("/pedidos-volume")
    dados = await r.json()
    filtrar()
}

function filtrar(){
    const q = document.getElementById("filtro").value.trim().toLowerCase()
    const filtrados = q
        ? dados.filter(d=>
            String(d.numero_pedido).toLowerCase().includes(q) ||
            d.palete_codigo.toLowerCase().includes(q) ||
            (d.endereco_codigo||"").toLowerCase().includes(q)
          )
        : dados

    const tabela = document.getElementById("tabela")
    tabela.innerHTML = ""

    if(filtrados.length===0){
        tabela.innerHTML="<tr><td colspan='7' style='color:#aaa'>Nenhum registro encontrado.</td></tr>"
        document.getElementById("info").textContent="0 registros"
        return
    }

    filtrados.forEach(item=>{
        const vol = String(item.volume_atual).padStart(3,"0")+"/"+String(item.volume_total).padStart(3,"0")
        tabela.innerHTML += `
        <tr>
          <td><input type="checkbox" class="check" value="${item.id}"></td>
          <td>${item.id}</td>
          <td>${item.numero_pedido}</td>
          <td><span class="tag">${vol}</span></td>
          <td>${item.palete_codigo}</td>
          <td>${item.endereco_codigo||"—"}</td>
          <td><button class="danger" onclick="apagarUm(${item.id})">Apagar</button></td>
        </tr>`
    })
    document.getElementById("info").textContent = filtrados.length+" registro(s)"
}

function selecionarTodos(){ document.querySelectorAll(".check").forEach(c=>c.checked=true) }
function desselecionarTodos(){ document.querySelectorAll(".check").forEach(c=>c.checked=false) }
function toggleAll(el){ document.querySelectorAll(".check").forEach(c=>c.checked=el.checked) }

async function apagarUm(id){
    if(!confirm("Deseja apagar este volume?")) return
    await fetch("/pedidos-volume/"+id, {method:"DELETE"})
    carregar()
}

async function apagarSelecionados(){
    const ids = Array.from(document.querySelectorAll(".check:checked")).map(c=>parseInt(c.value))
    if(ids.length===0){ alert("Selecione pelo menos um volume."); return }
    if(!confirm("Deseja apagar "+ids.length+" volume(s)?")) return
    await fetch("/pedidos-volume/deletar-varios",{
        method:"POST",
        headers:{"Content-Type":"application/json"},
        body:JSON.stringify({ids})
    })
    carregar()
}

carregar()
</script>
</body>
</html>"""


# ─────────────────────────────────────────────
#  UTILITÁRIOS
# ─────────────────────────────────────────────

@app.get("/seed")
def seed(db: Session = Depends(get_db)):
    enderecos_base = [
        ("R07 014 1","R07","014","1"),
        ("R07 016 1","R07","016","1"),
        ("R07 018 1","R07","018","1"),
        ("R07 020 1","R07","020","1"),
        ("R07 022 1","R07","022","1"),
        ("R07 024 1","R07","024","1"),
        ("R07 026 1","R07","026","1"),
        ("R07 028 1","R07","028","1"),
        ("R07 014 1F","R07","014","1F"),
        ("R07 016 1F","R07","016","1F"),
        ("R07 018 1F","R07","018","1F"),
        ("R07 020 1F","R07","020","1F"),
        ("R07 022 1F","R07","022","1F"),
        ("R07 024 1F","R07","024","1F"),
        ("R07 026 1F","R07","026","1F"),
        ("R07 028 1F","R07","028","1F"),
    ]
    criados = 0
    for codigo, rua, predio, andar in enderecos_base:
        existe = db.query(models.Endereco).filter(models.Endereco.codigo == codigo).first()
        if existe:
            existe.rua = rua; existe.predio = predio; existe.andar = andar
            existe.frente = "A"; existe.comprimento_cm = 100
            existe.largura_cm = 100; existe.altura_cm = 100
            existe.capacidade_total = 1; existe.capacidade_usada = 0
        else:
            db.add(models.Endereco(
                codigo=codigo, rua=rua, predio=predio, andar=andar,
                frente="A", comprimento_cm=100, largura_cm=100, altura_cm=100,
                capacidade_total=1, capacidade_usada=0
            ))
            criados += 1
    db.commit()
    return {"status": "ok", "enderecos_criados": criados}


@app.get("/reset-teste")
def reset_teste(db: Session = Depends(get_db)):
    db.query(models.PedidoVolume).delete()
    db.query(models.Palete).delete()
    db.query(models.Endereco).update({"capacidade_usada": 0})
    db.commit()
    return {"status": "ok", "mensagem": "Paletes e volumes apagados. Endereços liberados."}

@app.get("/app", response_class=HTMLResponse)
def app_home():
    return """
<!DOCTYPE html>
<html lang="pt-BR">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>SmartLocator</title>
<style>
body{
    font-family:Arial,sans-serif;
    background:#111;
    color:white;
    margin:0;
    padding:25px;
}
.box{
    max-width:700px;
    margin:auto;
    background:#1b1b1b;
    padding:35px;
    border-radius:14px;
    box-shadow:0 0 20px #000;
}
h1{
    color:#00ff88;
    font-size:40px;
}
p{
    color:#aaa;
    font-size:18px;
}
a{
    display:block;
    text-decoration:none;
    color:white;
    background:#198754;
    padding:20px;
    margin-top:18px;
    border-radius:10px;
    font-size:22px;
    text-align:center;
}
a:hover{
    opacity:.85;
}
.sec{
    background:#0d6efd;
}
.dark{
    background:#444;
}
</style>
</head>
<body>
<div class="box">
    <h1>SmartLocator</h1>
    <p>Escolha o módulo que deseja acessar:</p>

    <a href="/conferente-v2">Conferente</a>
    <a class="sec" href="/gerenciar-volumes">Gerenciar Volumes</a>
    <a class="dark" href="/operacao">Operação / Consulta</a>
</div>
</body>
</html>
"""