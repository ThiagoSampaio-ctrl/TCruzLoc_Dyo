from fastapi import APIRouter
from fastapi.responses import HTMLResponse
from app.pages._shared import SHARED, shell_open, shell_close

router = APIRouter()

@router.get("/conferente-v2", response_class=HTMLResponse)
def pg_conferente():
    return ("""<!DOCTYPE html><html lang="pt-BR"><head>""" + SHARED +
            """<title>WMS · Conferente</title></head><body>""" +
            shell_open('conf','📦','var(--gdim)','Montagem de Palete','Informe palete e endereço, depois adicione os pedidos') +
            r"""
<div class="card">
  <div class="ct">Identificação do Palete</div>
  <div class="g2">
    <div class="f"><label>Palete</label>
      <input class="fi" id="palete" placeholder="Ex: PAL001" autofocus></div>
    <div class="f"><label>Endereço</label>
      <div style="position:relative;">
        <input class="fi" id="endereco" placeholder="Ex: R07 014 1" autocomplete="off"
          oninput="filtrarDropdown();verificarEndereco()"
          onfocus="abrirDropdown()" onblur="fecharDropdown();verificarEndereco()">
        <span id="end-badge" style="position:absolute;right:10px;top:50%;transform:translateY(-50%);
          font-size:10px;padding:2px 7px;border-radius:4px;font-family:var(--mono);font-weight:600;display:none;"></span>
        <div id="end-dropdown" style="display:none;position:absolute;top:calc(100% + 4px);left:0;right:0;
          max-height:260px;overflow-y:auto;background:var(--s1);border:1px solid var(--br2);
          border-radius:var(--r);z-index:50;box-shadow:0 8px 24px rgba(0,0,0,.4);"></div>
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
    <div class="f"><label>Vol. Inicial</label><input class="fi" id="vol_ini" type="number" min="1" placeholder="1"></div>
    <div class="f"><label>Vol. Final</label><input class="fi" id="vol_fin" type="number" min="1" placeholder="6"></div>
    <div class="f"><label>Total do Pedido</label><input class="fi" id="vol_tot" type="number" min="1" placeholder="10"></div>
  </div>
  <div class="brow" style="margin-top:4px;">
    <button class="btn bg" id="btnAdd" onclick="adicionar()">＋ Adicionar</button>
    <button class="btn bb" id="btnFin" onclick="finalizar()">✓ Finalizar Palete</button>
    <button class="btn bgh" onclick="resetar()">↺ Novo</button>
  </div>
</div>
<div class="sb-status info" id="stbar"><div class="dot"></div>Aguardando dados...</div>
<div class="term" id="out">Pedidos adicionados aparecerão aqui...</div>
<div style="margin-top:10px;display:flex;gap:8px;flex-wrap:wrap;">
  <div class="stat" style="flex:0 0 auto;min-width:110px;"><div class="sl">Palete</div><div class="sv" id="s-pal" style="font-size:13px;">—</div></div>
  <div class="stat" style="flex:0 0 auto;min-width:110px;"><div class="sl">Endereço</div><div class="sv" id="s-end" style="font-size:13px;">—</div></div>
  <div class="stat" style="flex:0 0 auto;min-width:78px;"><div class="sl">Pedidos</div><div class="sv" id="s-nped">0</div></div>
  <div class="stat" style="flex:0 0 auto;min-width:78px;"><div class="sl">Volumes</div><div class="sv" id="s-nvol">0</div></div>
</div>
<script>
var resumo=[],totalVols=0,endStatus={},endLista=[];
async function carregarStatusEnderecos(){
  try{var r=await fetch('/enderecos-status');var d=await r.json();endLista=[];
    d.forEach(function(e){endStatus[e.codigo]=e.status;endLista.push(e.codigo);});}catch(e){}
}
carregarStatusEnderecos();
function corDot(st){if(st==='LIVRE')return'var(--green)';if(st==='PARCIAL')return'var(--amber)';if(st==='OCUPADO')return'var(--red)';return'var(--txt3)';}
function labelStatus(st){if(st==='LIVRE')return'Livre';if(st==='PARCIAL')return'Parcial';if(st==='OCUPADO')return'Ocupado';if(st==='BLOQUEADO')return'Bloqueado';return'—';}
function renderDropdown(filtro){
  var dd=document.getElementById('end-dropdown');
  var f=(filtro||'').trim().toUpperCase();
  var itens=endLista.filter(function(cod){return !f||cod.toUpperCase().indexOf(f)!==-1;});
  dd.innerHTML='';
  if(!itens.length){var v=document.createElement('div');v.style.padding='10px 12px';v.style.fontSize='12px';v.style.color='var(--txt3)';v.textContent='Nenhum endereço encontrado.';dd.appendChild(v);dd.style.display='block';return;}
  itens.forEach(function(cod){
    var st=endStatus[cod]||'LIVRE';
    var item=document.createElement('div');
    item.style.cssText='display:flex;align-items:center;gap:8px;padding:9px 12px;cursor:pointer;font-family:var(--mono);font-size:13px;color:var(--txt);border-bottom:1px solid var(--br);transition:.1s;';
    var dot=document.createElement('span');dot.style.cssText='width:8px;height:8px;border-radius:50%;background:'+corDot(st)+';flex-shrink:0;';
    var nome=document.createElement('span');nome.style.flex='1';nome.textContent=cod;
    var lbl=document.createElement('span');lbl.style.cssText='font-size:10px;color:'+corDot(st)+';';lbl.textContent=labelStatus(st);
    item.appendChild(dot);item.appendChild(nome);item.appendChild(lbl);
    item.addEventListener('mouseover',function(){item.style.background='var(--s2)';});
    item.addEventListener('mouseout',function(){item.style.background='transparent';});
    item.addEventListener('mousedown',function(e){e.preventDefault();selecionarEndereco(cod);});
    dd.appendChild(item);
  });
  dd.style.display='block';
}
function abrirDropdown(){renderDropdown(document.getElementById('endereco').value);}
function filtrarDropdown(){renderDropdown(document.getElementById('endereco').value);}
function fecharDropdown(){document.getElementById('end-dropdown').style.display='none';}
function selecionarEndereco(cod){document.getElementById('endereco').value=cod;fecharDropdown();verificarEndereco();upd();}
function verificarEndereco(){
  var val=document.getElementById('endereco').value.trim().toUpperCase();
  var badge=document.getElementById('end-badge');var info=document.getElementById('end-info');
  if(!val){badge.style.display='none';info.textContent='';return;}
  var norm=val.replace(/[\s\-]+/g,'');var m=norm.match(/^R(\d{2})(\d{3})(\d{1,2}[A-Z]?)$/);
  if(m)norm='R'+m[1]+' '+m[2]+' '+m[3];else norm=val;
  var st=endStatus[norm];
  if(!st){badge.style.display='none';info.textContent='';return;}
  badge.style.display='inline-block';
  if(st==='LIVRE'){badge.className='end-livre';badge.textContent='LIVRE';info.style.color='var(--gtxt)';info.textContent='✓ Endereço disponível';}
  else if(st==='PARCIAL'){badge.className='end-parcial';badge.textContent='PARCIAL';info.style.color='var(--atxt)';info.textContent='⚠ Parcialmente ocupado';}
  else if(st==='OCUPADO'){badge.className='end-ocupado';badge.textContent='OCUPADO';info.style.color='var(--rtxt)';info.textContent='✕ Endereço ocupado';}
  else if(st==='BLOQUEADO'){badge.className='end-bloqueado';badge.textContent='BLOQUEADO';info.style.color='var(--txt3)';info.textContent='⛔ Endereço bloqueado';}
}
function ss(msg,t){var el=document.getElementById('stbar');el.className='sb-status '+(t||'info');el.innerHTML='<div class="dot"></div>'+msg;}
function fmt(n,t){return String(n).padStart(3,'0')+'/'+String(t).padStart(3,'0');}
function upd(){
  document.getElementById('s-pal').textContent=document.getElementById('palete').value.trim()||'—';
  document.getElementById('s-end').textContent=document.getElementById('endereco').value.trim()||'—';
  document.getElementById('s-nped').textContent=new Set(resumo.map(function(r){return r.pedido;})).size;
  document.getElementById('s-nvol').textContent=totalVols;
}
function renderOut(){
  if(!resumo.length){document.getElementById('out').textContent='Pedidos adicionados aparecerão aqui...';return;}
  var ag={};
  resumo.forEach(function(r){if(!ag[r.pedido])ag[r.pedido]={ini:r.ini,fin:r.fin,tot:r.tot};
    else{ag[r.pedido].ini=Math.min(ag[r.pedido].ini,r.ini);ag[r.pedido].fin=Math.max(ag[r.pedido].fin,r.fin);}});
  var txt='PALETE:   '+resumo[0].palete+'\nENDEREÇO: '+resumo[0].endereco+'\n\n';
  for(var p in ag){var a=ag[p];txt+=p+'\n  '+fmt(a.ini,a.tot)+' → '+fmt(a.fin,a.tot)+'\n\n';}
  document.getElementById('out').textContent=txt;
}
['palete','endereco','pedido','vol_ini','vol_fin'].forEach(function(id,i){
  var nx=['endereco','pedido','vol_ini','vol_fin','vol_tot'];
  document.getElementById(id).addEventListener('keydown',function(e){if(e.key==='Enter'){e.preventDefault();fecharDropdown();document.getElementById(nx[i]).focus();}});
});
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
    document.getElementById('pedido').value='';document.getElementById('vol_ini').value='';
    document.getElementById('vol_fin').value='';document.getElementById('vol_tot').value='';
    document.getElementById('pedido').focus();
  }catch(e){ss('✕ Erro de conexão.','err');toast('Erro de conexão','err');}
  document.getElementById('btnAdd').disabled=false;document.getElementById('btnFin').disabled=false;
}
function finalizar(){
  var pal=document.getElementById('palete').value.trim();var end=document.getElementById('endereco').value.trim();
  if(!pal||!end){ss('⚠ Informe palete e endereço.','warn');return;}
  if(!resumo.length){ss('⚠ Nenhum pedido adicionado.','warn');return;}
  var ag={};
  resumo.forEach(function(r){if(!ag[r.pedido])ag[r.pedido]={ini:r.ini,fin:r.fin,tot:r.tot};
    else{ag[r.pedido].ini=Math.min(ag[r.pedido].ini,r.ini);ag[r.pedido].fin=Math.max(ag[r.pedido].fin,r.fin);}});
  var txt='✓ PALETE FINALIZADO\n\nPALETE:   '+pal+'\nENDEREÇO: '+end+'\n\nRESUMO:\n\n';
  for(var p in ag){var a=ag[p];txt+=p+'\n  '+fmt(a.ini,a.tot)+' → '+fmt(a.fin,a.tot)+'\n\n';}
  document.getElementById('out').textContent=txt;
  ss('Palete finalizado. Clique em "Novo" para recomeçar.','ok');toast('Palete finalizado!');
  document.getElementById('btnAdd').disabled=true;document.getElementById('btnFin').disabled=true;
}
function resetar(){
  resumo=[];totalVols=0;
  ['palete','endereco','pedido','vol_ini','vol_fin','vol_tot'].forEach(function(id){document.getElementById(id).value='';});
  document.getElementById('out').textContent='Pedidos adicionados aparecerão aqui...';
  document.getElementById('end-badge').style.display='none';
  document.getElementById('end-info').textContent='';
  fecharDropdown();document.getElementById('btnAdd').disabled=false;document.getElementById('btnFin').disabled=false;
  ss('Pronto para novo palete.','info');upd();document.getElementById('palete').focus();
}
upd();
</script>
""" + shell_close() + "</body></html>")