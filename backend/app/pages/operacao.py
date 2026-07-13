from fastapi import APIRouter
from fastapi.responses import HTMLResponse
from app.pages.shared import SHARED, shell_open, shell_close

router = APIRouter()

@router.get("/operacao", response_class=HTMLResponse)
def pg_operacao():
    return ("""<!DOCTYPE html><html lang="pt-BR"><head>""" + SHARED +
            """<title>WMS · Operação</title></head><body>""" +
            shell_open('oper','🔍','var(--bdim)','Consulta Rápida','Bipe ou digite um endereço ou número de pedido') +
            r"""
<div class="sw" style="margin-bottom:12px;">
  <span class="si">⌕</span>
  <input id="q" placeholder="Endereço ou pedido..." autofocus onkeydown="if(event.key==='Enter')buscar()">
</div>
<div class="brow" style="margin-bottom:16px;">
  <button class="btn bb bfull" onclick="buscarEndereco()">🔍 Buscar Endereço</button>
  <button class="btn bgh bfull" style="border-color:var(--green);color:var(--gtxt);" onclick="buscarPedido()">📦 Buscar Pedido</button>
</div>
<div class="stats">
  <div class="stat"><div class="sl">Consultas</div><div class="sv" id="nc">0</div></div>
  <div class="stat"><div class="sl">Endereços</div><div class="sv" id="ne">0</div></div>
  <div class="stat"><div class="sl">Pedidos</div><div class="sv" id="np">0</div></div>
  <div class="stat"><div class="sl">Erros</div><div class="sv red" id="nr">0</div></div>
</div>
<div class="term" id="out">Aguardando leitura...</div>
<div style="margin-top:12px;">
  <div style="font-size:10px;text-transform:uppercase;letter-spacing:.08em;color:var(--txt3);margin-bottom:6px;">Histórico</div>
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
  if(!v)return;if(v.match(/^R[0-9]/)||v.indexOf('R ')===0)buscarEndereco();else buscarPedido();}
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
""" + shell_close() + "</body></html>")
