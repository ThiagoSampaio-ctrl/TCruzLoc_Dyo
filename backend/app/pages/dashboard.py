from fastapi import APIRouter
from fastapi.responses import HTMLResponse
from app.pages._shared import SHARED, shell_open, shell_close

router = APIRouter()

@router.get("/app", response_class=HTMLResponse)
def pg_dashboard():
    return ("""<!DOCTYPE html><html lang="pt-BR"><head>""" + SHARED +
            """<title>WMS · Dashboard</title></head><body>""" +
            shell_open('home','🗺️','var(--gdim)','Mapa do Armazém','Visão geral dos endereços e sua ocupação') +
            r"""
<div class="map-toolbar">
  <select class="map-select" id="selRua" onchange="renderMapa()"></select>
  <select class="map-select" id="selNivel" onchange="renderMapa()"></select>
  <div class="sw" style="flex:1;min-width:200px;">
    <span class="si">⌕</span>
    <input id="buscaEnd" placeholder="Buscar endereço..." style="padding:9px 13px 9px 38px;font-size:13px;" oninput="renderMapa()">
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
  <div class="metric-card"><div><div class="num" id="m-ocupados" style="color:var(--rtxt);">—</div><div class="lbl">Ocupados</div></div><div class="trend">🔴</div></div>
  <div class="metric-card"><div><div class="num" id="m-parciais" style="color:var(--atxt);">—</div><div class="lbl">Parciais</div></div><div class="trend">🟡</div></div>
  <div class="metric-card"><div><div class="num" id="m-livres" style="color:var(--gtxt);">—</div><div class="lbl">Livres</div></div><div class="trend">🟢</div></div>
  <div class="metric-card"><div><div class="num" id="m-total" style="color:var(--txt);">—</div><div class="lbl">Total Endereços</div></div><div class="trend">📋</div></div>
</div>
<div style="display:grid;grid-template-columns:1fr 320px;gap:14px;align-items:start;">
  <div class="card" style="margin-bottom:0;">
    <div class="map-grid-label" id="mapaLabel">RUA — NÍVEL</div>
    <div class="map-wrap"><div class="map-grid" id="mapaGrid"></div></div>
    <div class="map-legend">
      <div class="map-legend-item"><div class="map-legend-dot" style="background:var(--green);"></div><div class="map-legend-txt"><b>Livre</b><span>Disponível para uso</span></div></div>
      <div class="map-legend-item"><div class="map-legend-dot" style="background:var(--amber);"></div><div class="map-legend-txt"><b>Parcial</b><span>Parcialmente ocupado</span></div></div>
      <div class="map-legend-item"><div class="map-legend-dot" style="background:var(--red);"></div><div class="map-legend-txt"><b>Ocupado</b><span>Totalmente ocupado</span></div></div>
      <div class="map-legend-item"><div class="map-legend-dot" style="background:var(--br2);"></div><div class="map-legend-txt"><b>Bloqueado</b><span>Não disponível</span></div></div>
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
      <span>Pedidos no endereço</span><span id="dQtdPedidos" style="color:var(--gtxt);">—</span>
    </div>
    <div id="dPedidosLista" style="display:flex;flex-direction:column;gap:8px;margin-top:6px;"></div>
    <div class="divider"></div>
    <button class="btn bgh bfull" onclick="window.location.href='/historico'">📋 Ver histórico deste endereço</button>
  </div>
</div>
<script>
var TODOS_ENDERECOS=[];
var enderecoSelecionado=null;
function corClasse(s){if(s==='LIVRE')return'livre';if(s==='PARCIAL')return'parcial';if(s==='OCUPADO')return'ocupado';if(s==='BLOQUEADO')return'bloqueado';return'livre';}
function corBadge(s){if(s==='LIVRE')return'bk-green';if(s==='PARCIAL')return'bk-amber';if(s==='OCUPADO')return'bk-red';return'bk-blue';}
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
    montarFiltros();renderMapa();
  }catch(e){}
}
function montarFiltros(){
  var ruas=[...new Set(TODOS_ENDERECOS.map(function(e){return e.rua;}))].sort();
  var selRua=document.getElementById('selRua');var ruaAtual=selRua.value;
  selRua.innerHTML=ruas.map(function(r){return '<option value="'+r+'">Rua '+r+'</option>';}).join('');
  if(ruas.indexOf(ruaAtual)!==-1)selRua.value=ruaAtual;
  var niveis=[...new Set(TODOS_ENDERECOS.filter(function(e){return e.rua===selRua.value;}).map(function(e){return e.predio;}))].sort();
  var selNivel=document.getElementById('selNivel');var nivelAtual=selNivel.value;
  selNivel.innerHTML=niveis.map(function(n){return '<option value="'+n+'">Nível '+n+'</option>';}).join('');
  if(niveis.indexOf(nivelAtual)!==-1)selNivel.value=nivelAtual;
}
function renderMapa(){
  var rua=document.getElementById('selRua').value;
  var nivel=document.getElementById('selNivel').value;
  var busca=document.getElementById('buscaEnd').value.trim().toUpperCase();
  var sf=document.getElementById('selStatus').value;
  document.getElementById('mapaLabel').textContent='RUA '+rua+' — NÍVEL '+nivel;
  var doNivel=TODOS_ENDERECOS.filter(function(e){return e.rua===rua&&e.predio===nivel;});
  doNivel.sort(function(a,b){return (parseInt(a.andar)||0)-(parseInt(b.andar)||0);});
  var frentes=[...new Set(doNivel.map(function(e){return e.frente||'A';}))].sort();
  var posicoes=[...new Set(doNivel.map(function(e){return parseInt(e.andar)||0;}))].sort(function(a,b){return a-b;});
  if(!posicoes.length){document.getElementById('mapaGrid').innerHTML='<p style="color:var(--txt3);padding:20px;">Nenhum endereço.</p>';return;}
  var todasPos=[];for(var p=posicoes[0];p<=posicoes[posicoes.length-1];p++)todasPos.push(p);
  var html='<div class="map-row" style="margin-left:30px;">';
  todasPos.forEach(function(p){html+='<div class="map-colheader">'+p+'</div>';});html+='</div>';
  frentes.forEach(function(fr){
    html+='<div class="map-row"><div class="map-rowlabel">'+fr+'</div>';
    todasPos.forEach(function(p){
      var end=doNivel.find(function(e){return (e.frente||'A')===fr&&(parseInt(e.andar)||0)===p;});
      if(!end){html+='<div class="map-cell empty">.</div>';return;}
      var st=end.status_ocupacao||'LIVRE';
      var visivel=(!busca||end.codigo.toUpperCase().indexOf(busca)!==-1)&&(!sf||st===sf);
      var cls='map-cell '+corClasse(st)+(visivel?'':' empty')+(enderecoSelecionado===end.codigo?' selected':'');
      html+="<div class='"+cls+"' onclick='selecionarEndereco(&quot;"+end.codigo+"&quot;)' title='"+end.codigo+"'>"+(visivel?end.codigo.replace('R',''):'')+'</div>';
    });html+='</div>';
  });
  document.getElementById('mapaGrid').innerHTML=html;
}
async function selecionarEndereco(codigo){
  enderecoSelecionado=codigo;renderMapa();
  var end=TODOS_ENDERECOS.find(function(e){return e.codigo===codigo;});
  if(!end)return;
  document.getElementById('painelVazio').style.display='none';
  document.getElementById('painelDetalhe').style.display='block';
  var st=end.status_ocupacao||'LIVRE';
  var badge=document.getElementById('dStatusBadge');
  badge.className='bk '+corBadge(st);badge.textContent=st;
  document.getElementById('dCodigo').textContent=end.codigo;
  document.getElementById('dRua').textContent=end.rua;
  document.getElementById('dNivel').textContent=end.predio;
  document.getElementById('dPosicao').textContent=end.andar+(end.frente?' '+end.frente:'');
  document.getElementById('dStatus').textContent=st;
  var pct=end.capacidade_total?Math.round((end.capacidade_usada/end.capacidade_total)*100):0;
  document.getElementById('dCapacidade').textContent=pct+'% ('+end.capacidade_usada+'/'+end.capacidade_total+' Palete)';
  document.getElementById('dOperador').textContent=getUser()||'—';
  try{
    var r=await fetch('/enderecos/'+encodeURIComponent(codigo)+'/pedidos');
    var pedidos=await r.json();
    document.getElementById('dQtdPedidos').textContent=pedidos.length+' pedido(s)';
    var lista=document.getElementById('dPedidosLista');
    if(!pedidos.length){lista.innerHTML='<div style="font-size:11.5px;color:var(--txt3);">Nenhum pedido neste endereço.</div>';}
    else{lista.innerHTML=pedidos.map(function(p){
      return '<div style="background:var(--s2);border-radius:8px;padding:10px 12px;display:flex;justify-content:space-between;align-items:center;">'+
        '<div><div style="font-family:var(--mono);font-weight:600;font-size:13px;">'+p.pedido+'</div>'+
        '<div style="font-size:10.5px;color:var(--txt3);">Volume: '+p.qtd+'/'+p.total+'</div></div>'+
        '<span class="bk bk-blue">'+(p.qtd===p.total?'COMPLETO':'PARCIAL')+'</span></div>';
    }).join('');}
  }catch(e){}
}
function fecharPainel(){
  enderecoSelecionado=null;
  document.getElementById('painelDetalhe').style.display='none';
  document.getElementById('painelVazio').style.display='block';
  renderMapa();
}
carregarTudo();
setInterval(carregarTudo,15000);
</script>
""" + shell_close() + "</body></html>")