from fastapi.responses import HTMLResponse
from fastapi import FastAPI, Depends
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


@app.get("/")
def home():
    return {"message": "SmartLocator funcionando"}


@app.get("/enderecos", response_model=list[schema.EnderecoResposta])
def listar_enderecos(db: Session = Depends(get_db)):
    return crud.listar_enderecos(db)


@app.get("/caixas", response_model=list[schema.CaixaResposta])
def listar_caixas(db: Session = Depends(get_db)):
    return crud.listar_caixas(db)


@app.post("/paletes/auto", response_model=schema.PaleteResposta)
def criar_palete_auto(palete: schema.PaleteCriar, db: Session = Depends(get_db)):
    return crud.criar_palete_auto(db, palete)


@app.get("/paletes", response_model=list[schema.PaleteResposta])
def listar_paletes(db: Session = Depends(get_db)):
    return crud.listar_paletes(db)


@app.post("/pedidos-volume", response_model=schema.PedidoVolumeResposta)
def criar_pedido_volume(pedido: schema.PedidoVolumeCriar, db: Session = Depends(get_db)):
    return crud.criar_pedido_volume(db, pedido)


@app.get("/enderecos/{codigo_endereco}/detalhes")
def detalhes_endereco(codigo_endereco: str, db: Session = Depends(get_db)):
    return crud.detalhes_endereco(db, codigo_endereco)


@app.get("/pedidos/{numero_pedido}")
def buscar_pedido(numero_pedido: str, db: Session = Depends(get_db)):
    return crud.buscar_pedido(db, numero_pedido)


@app.delete("/pedidos-volume/duplicados")
def limpar_pedidos_duplicados(db: Session = Depends(get_db)):
    return crud.limpar_pedidos_duplicados(db)


@app.get("/operacao", response_class=HTMLResponse)
def tela_operacao():
    return """

    
<!DOCTYPE html>
<html lang="pt-BR">
<head>
<meta charset="UTF-8">
<title>TCruzLoc_Dyo</title>



<style>

#contador{
    color:#00ff88;
    font-size:18px;
    font-weight:bold;
    margin-top:18px;
    margin-bottom:12px;
}

#historico{
    margin-top:20px;
    display:flex;
    flex-wrap:wrap;
    gap:10px;
}

.item-historico{
    background:#222;
    color:#00ff88;
    border:1px solid #00ff88;
    padding:10px 18px;
    border-radius:8px;
    cursor:pointer;
    font-size:18px;
}

body{
    font-family:Arial,sans-serif;
    background:#111;
    color:white;
    margin:0;
    padding:25px;
}

.box{
    background:#1b1b1b;
    max-width:950px;
    margin:auto;
    padding:35px;
    border-radius:14px;
    box-shadow:0 0 20px #000;
}

h1{
    font-size:42px;
    color:#00ff88;
    margin-top:0;
}

h2{
    font-size:28px;
}

input{
    width:100%;
    padding:22px;
    font-size:34px;

    background:#000;
    color:#00ff88;

    border:3px solid #00ff88;
    border-radius:10px;

    margin-bottom:20px;

    caret-color:#00ff88;

    box-sizing:border-box;
}

input::placeholder{
    color:#777;
}

button{
    width:49%;
    padding:20px;
    font-size:24px;

    border:none;
    border-radius:10px;

    cursor:pointer;
}

button:hover{
    transform:scale(1.02);
    transition:.15s;
}

.btn-pedido{
    background:#198754;
}

pre{
    background:#000;
    color:#00ff88;

    padding:30px;
    font-size:30px;

    white-space:pre-wrap;

    margin-top:25px;

    border-radius:12px;

    min-height:300px;

    border:2px solid #00ff88;
}
.sucesso{
    border:2px solid #00ff88 !important;
    box-shadow:0 0 18px #00ff88;
}

.erro{
    border:2px solid #ff3333 !important;
    box-shadow:0 0 18px #ff3333;
}

#relogio{
    color:#00ff88;
    font-size:18px;
    font-weight:bold;
    margin-bottom:15px;
}
#dashboard{

    display:flex;
    flex-wrap:wrap;

    gap:18px;

    margin-top:15px;
    margin-bottom:18px;

    color:#00ff88;

    font-weight:bold;
    font-size:18px;
}

#contadorErros{
    color:#ff4444;
}

</style>

</head>

<body>

<div class="box">

<h1>TCruzLoc_Dyo</h1>

<div id="relogio"></div>

<h2>Bipar / Digitar endereço ou pedido</h2>

<input
id="codigo"
placeholder="Ex: R07 014 1 ou 349596"
autofocus
onkeypress="if(event.key==='Enter'){buscarAutomatico()}"
>

<button onclick="buscarEndereco()">Buscar Endereço</button>
<button class="btn-pedido" onclick="buscarPedido()">Buscar Pedido</button>

<pre id="resultado">Aguardando leitura...</pre> 

<div id="dashboard">

    <span id="contador">
        Consultas: 0
    </span>

    <span id="contadorPedidos">
        Pedidos: 0
    </span>

    <span id="contadorEnderecos">
        Endereços: 0
    </span>

    <span id="contadorErros">
        Erros: 0
    </span>

</div>

<h3>Últimas consultas</h3>
<div id="historico"></div>

</div>

<script>

window.onload=function(){
    document.getElementById("codigo").focus()
}
function atualizarRelogio(){

    const agora = new Date()

    const dataHora =
        agora.toLocaleDateString("pt-BR") +
        " " +
        agora.toLocaleTimeString("pt-BR")

    document.getElementById("relogio").textContent = dataHora
}

setInterval(atualizarRelogio, 1000)
atualizarRelogio()

let tempoBusca = null
let historico = []
let contadorConsultas = 0
let contadorPedidos = 0
let contadorEnderecos = 0
let contadorErros = 0

document.addEventListener("DOMContentLoaded", function(){

    const campo = document.getElementById("codigo")

    campo.addEventListener("input", function(){

        clearTimeout(tempoBusca)

        tempoBusca = setTimeout(function(){

            const valor = campo.value.trim()

            if(!valor.trim().toUpperCase().startsWith("R") && valor.length >= 5) {
    buscarAutomatico()
}

        }, 500)
    })
    })
function efeitoSucesso(){

    const campo = document.getElementById("codigo")

    campo.classList.remove("erro")

    campo.classList.add("sucesso")

    setTimeout(()=>{
        campo.classList.remove("sucesso")
    },800)
}

function efeitoErro(){

    const campo = document.getElementById("codigo")

    campo.classList.remove("sucesso")

    campo.classList.add("erro")

    setTimeout(()=>{
        campo.classList.remove("erro")
    },800)
}

function beepSucesso(){

    const audio =
        new Audio(
        "https://actions.google.com/sounds/v1/alarms/beep_short.ogg"    
        )

    audio.play()

}

function beepErro(){

    const audio =
        new Audio(
        "https://actions.google.com/sounds/v1/cartoon/pop.ogg"          
        )

    audio.play()

}

function atualizarDashboard(){

    document.getElementById("contador").textContent =
        "Consultas: " + contadorConsultas

    document.getElementById("contadorPedidos").textContent =
        "Pedidos: " + contadorPedidos

    document.getElementById("contadorEnderecos").textContent =
        "Endereços: " + contadorEnderecos

    document.getElementById("contadorErros").textContent =
        "Erros: " + contadorErros
}

function salvarHistorico(valor){

    if(!valor) return

    historico.unshift(valor)

    historico = [...new Set(historico)]

    historico = historico.slice(0,10)

    renderHistorico()

    contadorConsultas++

    atualizarDashboard()
}

function renderHistorico(){

    const area = document.getElementById("historico")

    area.innerHTML = ""

    historico.forEach(item=>{

        area.innerHTML +=
        `<div class="item-historico" onclick="rebuscar('${item}')">
            ${item}
        </div>`
    })
}

function rebuscar(valor){

    document.getElementById("codigo").value = valor

    buscarAutomatico()
}

function iniciarLoading(){

    document.getElementById("resultado").textContent =
        "⏳ Buscando..."

    document.querySelectorAll("button").forEach(botao=>{
        botao.disabled = true
    })
}

function finalizarLoading(){

    document.querySelectorAll("button").forEach(botao=>{
        botao.disabled = false
    })

    document.getElementById("codigo").focus()
}

function limparCampo(){
    document.getElementById("codigo").value=""
    document.getElementById("codigo").focus()
}
function buscarAutomatico(){

    let codigo =
        document.getElementById("codigo")
        .value
        .trim()

    codigo =
        codigo.toUpperCase()

    // endereço bipado sem espaços
if(/^R\\d+$/.test(codigo)){

        if(codigo.length === 7){

            codigo =
                codigo.substring(0,3) + " " +
                codigo.substring(3,6) + " " +
                codigo.substring(6)

            document.getElementById("codigo")
                .value = codigo
        }
    }

    if(codigo.startsWith("R")){

        buscarEndereco()

    }else{

        buscarPedido()

    }
}
async function buscarEndereco(){

    const codigo = document.getElementById("codigo").value.trim()
    const resultado = document.getElementById("resultado")
    iniciarLoading()
    
    if(!codigo){
        resultado.textContent = "Digite ou bipe um endereço."
        finalizarLoading()
        return
    }

    try{
        const resposta = await fetch(
            "/enderecos/" + encodeURIComponent(codigo) + "/detalhes"
        )

        const dados = await resposta.json()

        if(!dados.paletes || dados.paletes.length === 0){
            resultado.textContent = "Endereço não encontrado ou sem palete."
            efeitoErro()
            beepErro()
            limparCampo()
            contadorErros++
            atualizarDashboard()
            finalizarLoading()
            return
        }

        let texto = ""

        texto += "ENDEREÇO: " + dados.endereco + "\\n\\n"

        dados.paletes.forEach(palete=>{

            texto += "PALETE: " + palete.palete + "\\n\\n"
            texto += "PEDIDOS:\\n\\n"

            palete.pedidos.forEach(pedido=>{

                texto += pedido.pedido + "\\n"

                pedido.volumes.forEach(volume=>{
                    texto += volume + "\\n"
                })

                texto += "\\n"
            })
        })

        resultado.textContent = texto
        efeitoSucesso()
        beepSucesso()
        salvarHistorico(codigo)
        contadorEnderecos++
        atualizarDashboard()
    }
    catch{
        resultado.textContent = "Erro ao buscar endereço."
        efeitoErro()
        beepErro()
        contadorErros++
        atualizarDashboard()
    }
    finalizarLoading()
    limparCampo()
}


async function buscarPedido(){

    const codigo = document.getElementById("codigo").value.trim()
    const resultado = document.getElementById("resultado")
    iniciarLoading()

    if(!codigo){
        resultado.textContent = "Digite ou bipe um pedido."
        finalizarLoading()
        return
    }

    try{
        const resposta = await fetch(
            "/pedidos/" + encodeURIComponent(codigo)
        )

        const dados = await resposta.json()

        if(dados.detail){
            resultado.textContent = dados.detail
            efeitoErro()
            beepErro()
            limparCampo()
            contadorErros++
            atualizarDashboard()
            finalizarLoading()
            return
        }

        let texto = ""

        texto += "PEDIDO: " + dados.pedido + "\\n\\n"

        dados.enderecos.forEach(item=>{

            texto += "ENDEREÇO: " + item.endereco + "\\n"
            texto += "PALETE: " + item.palete + "\\n\\n"
            texto += "VOLUMES:\\n"

            item.volumes.forEach(volume=>{
                texto += volume + "\\n"
            })

            texto += "\\n"
        })

        resultado.textContent = texto
        salvarHistorico(codigo)
        efeitoSucesso()
        beepSucesso()
        contadorPedidos++
        atualizarDashboard()
    }
    catch{
        resultado.textContent = "Erro ao buscar pedido."
        efeitoErro()
        beepErro()
        contadorErros++
        atualizarDashboard()
    }
    finalizarLoading()
    limparCampo()
}

</script>

</body>
</html>
"""



@app.get("/conferente", response_class=HTMLResponse)
def tela_conferente():
    return """
<!DOCTYPE html>
<html lang="pt-BR">
<head>
<meta charset="UTF-8">
<title>TCruzLoc_Dyo - Conferente</title>

<style>
body{
    font-family:Arial,sans-serif;
    background:#111;
    color:white;
    margin:0;
    padding:25px;
}

.box{
    background:#1b1b1b;
    max-width:750px;
    margin:auto;
    padding:35px;
    border-radius:14px;
    box-shadow:0 0 20px #000;
}

h1{
    color:#00ff88;
    font-size:40px;
    margin-top:0;
}

h2{
    font-size:26px;
}

label{
    display:block;
    margin-top:15px;
    margin-bottom:6px;
    font-size:18px;
    color:#00ff88;
}

input{
    width:100%;
    padding:18px;
    font-size:26px;
    background:#000;
    color:#00ff88;
    border:3px solid #00ff88;
    border-radius:10px;
    box-sizing:border-box;
}

button{
    width:100%;
    margin-top:25px;
    padding:20px;
    font-size:24px;
    background:#198754;
    color:white;
    border:none;
    border-radius:10px;
    cursor:pointer;
}

pre{
    background:#000;
    color:#00ff88;
    padding:25px;
    font-size:22px;
    white-space:pre-wrap;
    margin-top:25px;
    border-radius:12px;
    border:2px solid #00ff88;
}

.sucesso{
    border-color:#00ff88 !important;
    box-shadow:0 0 18px #00ff88;
}

.erro{
    border-color:#ff3333 !important;
    box-shadow:0 0 18px #ff3333;
}
</style>
</head>

<body>

<div class="box">

<h1>TCruzLoc_Dyo</h1>
<h2>Tela do Conferente</h2>

<label>Pedido</label>
<input id="pedido" placeholder="Ex: 349596" autofocus>

<label>Quantidade de volumes</label>
<input id="volume_total" placeholder="Ex: 3"> 

<label>Palete</label>
<input id="palete" placeholder="Ex: PAL001">

<button onclick="cadastrarVolume()">Cadastrar volume</button>

<pre id="resultado">Aguardando cadastro...</pre>

</div>

<script>

function efeitoSucesso(){
    const box = document.querySelector(".box")
    box.classList.remove("erro")
    box.classList.add("sucesso")

    setTimeout(()=>{
        box.classList.remove("sucesso")
    },800)
}

function efeitoErro(){
    const box = document.querySelector(".box")
    box.classList.remove("sucesso")
    box.classList.add("erro")

    setTimeout(()=>{
        box.classList.remove("erro")
    },800)
}

async function cadastrarVolume(){

    const pedido =
        document.getElementById("pedido").value.trim()

    const volumeTotal =
        parseInt(
            document.getElementById("volume_total").value.trim()
        )

    const palete =
        document.getElementById("palete").value.trim()

    const resultado =
        document.getElementById("resultado")

    if(!pedido || !volumeTotal || !palete){

        resultado.textContent =
            "Preencha todos os campos."

        efeitoErro()

        return
    }

    resultado.textContent =
        "⏳ Cadastrando volumes..."

    try{

        let cadastrados = ""

        for(let i=1;i<=volumeTotal;i++){

            const resposta =
                await fetch("/pedidos-volume",{

                    method:"POST",

                    headers:{
                        "Content-Type":"application/json"
                    },

                    body:JSON.stringify({

                        numero_pedido: pedido,

                        volume_atual: i,

                        volume_total: volumeTotal,

                        palete_codigo: palete
                    })

                })

            const dados =
                await resposta.json()

            if(dados.detail){

                resultado.textContent =
                    dados.detail

                efeitoErro()

                return
            }

            cadastrados +=
                pedido +
                " " +
                String(i).padStart(3,"0") +
                "/" +
                String(volumeTotal).padStart(3,"0") +
                "\\n"
        }

        resultado.textContent =

            "VOLUMES CADASTRADOS COM SUCESSO!\\n\\n" +

            cadastrados +

            "\\nPalete: " +
            palete

        efeitoSucesso()

        document.getElementById("pedido").value=""

        document.getElementById("volume_total").value=""

        document.getElementById("pedido").focus()

    }

    catch{

        resultado.textContent =
            "Erro ao cadastrar."

        efeitoErro()
    }
}

</script>

</body>
</html>
"""
@app.get("/conferente-v2", response_class=HTMLResponse)
def tela_conferente_v2():
    return """
<!DOCTYPE html>
<html lang="pt-BR">
<head>
<meta charset="UTF-8">
<title>TCruzLoc_Dyo - Montagem Palete</title>

<style>

body{font-family:Arial,sans-serif;background:#111;color:white;margin:0;padding:25px;}
.box{background:#1b1b1b;max-width:950px;margin:auto;padding:35px;border-radius:14px;box-shadow:0 0 20px #000;}
h1{color:#00ff88;font-size:42px;margin-top:0;}
label{color:#00ff88;font-weight:bold;display:block;margin-top:15px;}
input{width:100%;padding:16px;font-size:24px;background:#000;color:#00ff88;border:3px solid #00ff88;border-radius:10px;box-sizing:border-box;margin-top:6px;}
.grid{display:grid;grid-template-columns:repeat(4,1fr);gap:12px;}
button{width:100%;margin-top:25px;padding:20px;font-size:24px;background:#198754;color:white;border:none;border-radius:10px;cursor:pointer;}
pre{background:#000;color:#00ff88;padding:25px;font-size:22px;white-space:pre-wrap;margin-top:25px;border-radius:12px;border:2px solid #00ff88;}

</style>
</head>
<body>
<div class="box">

<h1>TCruzLoc_Dyo</h1>
<h2>Montagem Inteligente de Palete</h2>

<label>Palete</label>
<input id="palete" placeholder="Ex: PAL001" autofocus>

<hr>

<label>Pedido</label>
<input id="pedido" placeholder="Ex: 349596">

<div class="grid">
<div><label>Vol. inicial</label><input id="vol_inicial" placeholder="1"></div>
<div><label>Vol. final</label><input id="vol_final" placeholder="6"></div>
<div><label>Total pedido</label><input id="vol_total" placeholder="10"></div>
<div><label>K0</label><input id="k0" placeholder="0"></div>
</div>

<div class="grid">
<div><label>K1</label><input id="k1" placeholder="0"></div>
<div><label>K2</label><input id="k2" placeholder="0"></div>
<div><label>K3</label><input id="k3" placeholder="0"></div>
</div>

<button onclick="adicionarAoPalete()">Adicionar ao Palete</button>

<button onclick="finalizarPalete()" style= "background:#0d6efd;">
    Finalizar Palete
</button>

<pre id="resultado">Pedidos no palete aparecerão aqui...</pre>

</div>

<script>
let resumo = []
let enderecoPalete= ""

function formatarVolume(num,total){
    return String(num).padStart(3,"0") + "/" + String(total).padStart(3,"0")
}

async function adicionarAoPalete(){

    const palete = document.getElementById("palete").value.trim()
    const pedido = document.getElementById("pedido").value.trim()
    const inicial = parseInt(document.getElementById("vol_inicial").value)
    const final = parseInt(document.getElementById("vol_final").value)
    const total = parseInt(document.getElementById("vol_total").value)

    const k0 = parseInt(document.getElementById("k0").value || 0)
    const k1 = parseInt(document.getElementById("k1").value || 0)
    const k2 = parseInt(document.getElementById("k2").value || 0)
    const k3 = parseInt(document.getElementById("k3").value || 0)

    const resultado = document.getElementById("resultado")

    if(!palete || !pedido || !inicial || !final || !total){
        resultado.textContent = "Preencha palete, pedido e volumes."
        return
    }

    if(final < inicial){
        resultado.textContent = "Volume final não pode ser menor que o inicial."
        return
    }

    resultado.textContent = "⏳ Criando/verificando palete..."

    const criarPalete = await fetch("/paletes/auto", {
        method:"POST",
        headers:{"Content-Type":"application/json"},
        body:JSON.stringify({
            codigo: palete,
            qtd_k0: k0,
            qtd_k1: k1,
            qtd_k2: k2,
            qtd_k3: k3
        })
    })

    const paleteResp = await criarPalete.json()
    enderecoPalete = paleteResp.endereco_codigo

    if(paleteResp.detail){
        resultado.textContent = paleteResp.detail
        return
    }

    resultado.textContent = "⏳ Cadastrando volumes..."

    for(let i = inicial; i <= final; i++){
        const resposta = await fetch("/pedidos-volume", {
            method:"POST",
            headers:{"Content-Type":"application/json"},
            body:JSON.stringify({
                numero_pedido: pedido,
                volume_atual: i,
                volume_total: total,
                palete_codigo: palete
            })
        })

        const dados = await resposta.json()

        if(dados.detail){
            resultado.textContent = dados.detail
            return
        }
    }

    resumo.push({pedido, inicial, final, total, k0, k1, k2, k3})
    renderResumo()

    document.getElementById("pedido").value=""
    document.getElementById("vol_inicial").value=""
    document.getElementById("vol_final").value=""
    document.getElementById("vol_total").value=""
    document.getElementById("k0").value=""
    document.getElementById("k1").value=""
    document.getElementById("k2").value=""
    document.getElementById("k3").value=""
    document.getElementById("pedido").focus()
}
function renderResumo(){

    const palete =
        document.getElementById("palete").value.trim()

    let agrupado = {}

    resumo.forEach(item=>{

        if(!agrupado[item.pedido]){

            agrupado[item.pedido]={
                inicial:item.inicial,
                final:item.final,
                total:item.total,
                k0:item.k0,
                k1:item.k1,
                k2:item.k2,
                k3:item.k3
            }

        }else{

            agrupado[item.pedido].final =
                Math.max(
                    agrupado[item.pedido].final,
                    item.final
                )
        }
    })

    let texto =
        "PALETE: " + palete + "\\n\\n"

    texto += "PEDIDOS NO PALETE:\\n\\n"

    for(const pedido in agrupado){

        let item = agrupado[pedido]

        texto += pedido + "\\n"

        texto +=
            formatarVolume(
                item.inicial,
                item.total
            )

        texto += " até "

        texto +=
            formatarVolume(
                item.final,
                item.total
            ) + "\\n"

        texto +=
            "K0:"+item.k0+
            " | K1:"+item.k1+
            " | K2:"+item.k2+
            " | K3:"+item.k3+
            "\\n\\n"
    }

    document
        .getElementById("resultado")
        .textContent = texto
}
function finalizarPalete(){

    const palete =
        document.getElementById("palete").value.trim()

    if(!palete){

        document.getElementById("resultado")
            .textContent =
            "Informe o palete."

        return
    }

    if(resumo.length===0){

        document.getElementById("resultado")
            .textContent =
            "Nenhum pedido adicionado."

        return
    }

    let totalK0=0
    let totalK1=0
    let totalK2=0
    let totalK3=0

    resumo.forEach(item=>{

        totalK0 += item.k0
        totalK1 += item.k1
        totalK2 += item.k2
        totalK3 += item.k3

    })

    let texto=""

    texto+="PALETE FINALIZADO\\n\\n"

    texto+="PALETE: "+palete+"\\n"

    texto+="ENDEREÇO: "
        + enderecoPalete
        + "\\n\\n"

    texto+="TOTAL DE CAIXAS:\\n"

    texto+="K0: "+totalK0+"\\n"
    texto+="K1: "+totalK1+"\\n"
    texto+="K2: "+totalK2+"\\n"
    texto+="K3: "+totalK3+"\\n\\n"

    texto+="STATUS: ENDEREÇADO"

    document
        .getElementById("resultado")
        .textContent=texto
}



</script>
</body>
</html>
"""
@app.get("/pedidos-volume")
def listar_pedidos_volume(
    db: Session = Depends(get_db)
):
    return crud.listar_pedidos_volume(db)


@app.delete("/pedidos-volume/{volume_id}")
def deletar_pedido_volume(
    volume_id: int,
    db: Session = Depends(get_db)
):
    return crud.deletar_pedido_volume(
        db,
        volume_id
    )


@app.post("/pedidos-volume/deletar-varios")
def deletar_varios_pedidos_volume(
    dados: schema.DeletarVolumes,
    db: Session = Depends(get_db)
):
    return crud.deletar_varios_pedidos_volume(
        db,
        dados.ids
    )


@app.get("/gerenciar-volumes", response_class=HTMLResponse)
def gerenciar_volumes():
    return """

<!DOCTYPE html>
<html lang="pt-BR">
<head>
<meta charset="UTF-8">
<title>Gerenciar Volumes</title>
<style>
body{font-family:Arial;background:#111;color:white;padding:25px;}
.box{background:#1b1b1b;max-width:1100px;margin:auto;padding:30px;border-radius:14px;}
h1{color:#00ff88;}
button{padding:12px 18px;margin:8px;background:#198754;color:white;border:none;border-radius:8px;cursor:pointer;}
button.danger{background:#dc3545;}
table{width:100%;border-collapse:collapse;margin-top:20px;}
th,td{border:1px solid #00ff88;padding:10px;text-align:left;}
th{color:#00ff88;}
</style>
</head>
<body>
<div class="box">
<h1>Gerenciar Volumes</h1>

<button onclick="carregar()">Atualizar</button>
<button onclick="selecionarTodos()">Selecionar todos</button>
<button class="danger" onclick="apagarSelecionados()">Apagar selecionados</button>

<table>
<thead>
<tr>
<th></th><th>ID</th><th>Pedido</th><th>Volume</th><th>Palete</th><th>Endereço</th><th>Ação</th>
</tr>
</thead>
<tbody id="tabela"></tbody>
</table>
</div>

<script>

async function carregar(){

    const resposta = await fetch("/pedidos-volume")
    const dados = await resposta.json()

    const tabela = document.getElementById("tabela")
    tabela.innerHTML = ""

    dados.forEach(item=>{

        tabela.innerHTML += `
        <tr>
            <td><input type="checkbox" class="check" value="${item.id}"></td>
            <td>${item.id}</td>
            <td>${item.numero_pedido}</td>
            <td>${String(item.volume_atual).padStart(3,"0")}/${String(item.volume_total).padStart(3,"0")}</td>
            <td>${item.palete_codigo}</td>
            <td>${item.endereco_codigo}</td>
            <td>
                <button class="danger"
                    onclick="apagarUm(${item.id})">
                    Apagar
                </button>
            </td>
        </tr>`
    })
}

function selecionarTodos(){

    document
        .querySelectorAll(".check")
        .forEach(c=>c.checked=true)
}

async function apagarUm(id){

    if(!confirm("Deseja apagar este volume?"))
        return

    await fetch(
        "/pedidos-volume/" + id,
        {method:"DELETE"}
    )

    carregar()
}

async function apagarSelecionados(){

    const ids = Array.from(
        document.querySelectorAll(".check:checked")
    ).map(c=>parseInt(c.value))

    if(ids.length===0){

        alert("Selecione pelo menos um volume.")
        return
    }

    if(!confirm(
        "Deseja apagar os volumes selecionados?"
    )){
        return
    }

    await fetch(
        "/pedidos-volume/deletar-varios",
        {
            method:"POST",

            headers:{
                "Content-Type":"application/json"
            },

            body:JSON.stringify({
                ids: ids
            })
        }
    )

    carregar()
}

carregar()

</script>
</body>
</html>
"""

