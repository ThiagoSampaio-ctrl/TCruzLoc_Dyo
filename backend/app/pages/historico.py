from fastapi import APIRouter
from fastapi.responses import HTMLResponse
from app.pages.shared import SHARED, shell_open, shell_close

router = APIRouter()

@router.get("/historico", response_class=HTMLResponse)
def pg_historico():
    return ("""<!DOCTYPE html><html lang="pt-BR"><head>""" + SHARED +
            """<title>WMS · Histórico</title>
<script src="https://cdnjs.cloudflare.com/ajax/libs/SheetJS/0.18.5/xlsx.full.min.js"></script>
</head><body>""" +
            shell_open('hist','📋','var(--pdim)','Histórico de Ações','Auditoria — cadastros, exclusões, transferências e status') +
            r"""
<div class="modal-bg" id="filtroModalBg">
  <div class="modal" style="max-width:480px;">
    <h3>🔧 Filtros do Histórico</h3>
    <div class="f"><label>Ação</label>
      <select id="m-filtroAcao" style="width:100%;padding:11px 13px;background:var(--bg);color:var(--txt);border:1px solid var(--br);border-radius:var(--r);font-family:var(--mono);font-size:14px;outline:none;">
        <option value="">Todas as ações</option>
        <option value="CADASTRO">Cadastros</option>
        <option value="EXCLUSAO">Exclusões</option>
        <option value="TRANSFERENCIA">Transferências</option>
        <option value="STATUS_END">Status endereço</option>
      </select>
    </div>
    <div class="f"><label>Buscar (pedido, usuário, endereço...)</label>
      <input class="fi" id="m-filtroTxt" placeholder="Digite para filtrar...">
    </div>
    <div class="brow" style="margin-top:6px;">
      <button class="btn bg" onclick="aplicarFiltrosModal()">✓ Aplicar Filtros</button>
      <button class="btn bgh" onclick="limparFiltrosModal()">↺ Limpar</button>
    </div>
    <div class="divider"></div>
    <button class="btn bb bfull" onclick="exportarExcel()">⬇ Baixar Relatório (Excel)</button>
    <div style="font-size:11px;color:var(--txt3);margin-top:8px;text-align:center;">O relatório respeita os filtros aplicados acima.</div>
    <div class="brow" style="margin-top:14px;">
      <button class="btn bgh bfull" onclick="fecharFiltroModal()">Fechar</button>
    </div>
  </div>
</div>
<div style="display:flex;align-items:center;justify-content:flex-end;flex-wrap:wrap;gap:10px;margin-bottom:16px;">
  <button class="btn bgh" onclick="carregar()">↺ Atualizar</button>
  <button class="btn ba" onclick="abrirFiltroModal()">🔧 Filtros / Exportar</button>
  <span id="info" style="font-size:12px;color:var(--txt3);white-space:nowrap;align-self:center;">—</span>
</div>
<div id="filtroAtivoTag" style="display:none;margin-bottom:12px;font-size:11px;color:var(--atxt);background:var(--adim);border:1px solid var(--amber);border-radius:var(--r);padding:6px 12px;"></div>
<div class="card" style="margin-bottom:0;">
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
var dados=[],filtroAcao='',filtroTxt='';
async function carregar(){
  document.getElementById('tbody').innerHTML='<tr><td colspan="9" style="color:var(--txt3);text-align:center;padding:20px;">Carregando...</td></tr>';
  try{
    var r=await fetch('/historico-api',{headers:authHeaders()});
    if(r.status===401){window.location.href='/login';return;}
    dados=await r.json();filtrar();
  }catch(e){document.getElementById('tbody').innerHTML='<tr><td colspan="9" style="color:var(--rtxt);text-align:center;padding:20px;">Erro ao carregar.</td></tr>';}
}
function getFiltrados(){
  return dados.filter(function(d){
    if(filtroAcao&&d.acao!==filtroAcao)return false;
    if(filtroTxt){var s=(d.numero_pedido+d.usuario_nome+d.palete_codigo+d.endereco_de+d.endereco_para+d.detalhe_extra).toLowerCase();if(s.indexOf(filtroTxt.toLowerCase())===-1)return false;}
    return true;
  });
}
function filtrar(){
  var fd=getFiltrados();var tb=document.getElementById('tbody');
  if(!fd.length){tb.innerHTML='<tr><td colspan="9" style="color:var(--txt3);text-align:center;padding:20px;">Nenhum registro.</td></tr>';document.getElementById('info').textContent='0 registros';return;}
  var cor={'CADASTRO':'bk-green','EXCLUSAO':'bk-red','TRANSFERENCIA':'bk-amber','STATUS_END':'bk-blue'};
  tb.innerHTML=fd.map(function(d){
    var vol=d.volume_atual!=null?String(d.volume_atual).padStart(3,'0')+'/'+String(d.volume_total).padStart(3,'0'):'—';
    return '<tr>'+
      '<td style="font-family:var(--mono);font-size:11px;color:var(--txt3);white-space:nowrap;">'+d.criado_em+'</td>'+
      '<td style="font-weight:500;font-size:12px;">'+d.usuario_nome+'</td>'+
      '<td><span class="bk '+(cor[d.acao]||'bk-blue')+'">'+d.acao+'</span></td>'+
      '<td style="font-family:var(--mono);">'+d.numero_pedido+'</td>'+
      '<td><span class="bk bk-blue">'+vol+'</span></td>'+
      '<td style="color:var(--gtxt);font-family:var(--mono);">'+d.palete_codigo+'</td>'+
      '<td style="color:var(--txt3);font-family:var(--mono);font-size:11px;">'+d.endereco_de+'</td>'+
      '<td style="color:var(--gtxt);font-family:var(--mono);font-size:11px;">'+d.endereco_para+'</td>'+
      '<td style="color:var(--txt3);font-size:11px;">'+d.detalhe_extra+'</td></tr>';
  }).join('');
  document.getElementById('info').textContent=fd.length+' registro(s)';
}
function abrirFiltroModal(){document.getElementById('m-filtroAcao').value=filtroAcao;document.getElementById('m-filtroTxt').value=filtroTxt;document.getElementById('filtroModalBg').classList.add('open');}
function fecharFiltroModal(){document.getElementById('filtroModalBg').classList.remove('open');}
function aplicarFiltrosModal(){filtroAcao=document.getElementById('m-filtroAcao').value;filtroTxt=document.getElementById('m-filtroTxt').value.trim();filtrar();atualizarTagFiltro();fecharFiltroModal();toast('Filtros aplicados.');}
function limparFiltrosModal(){document.getElementById('m-filtroAcao').value='';document.getElementById('m-filtroTxt').value='';filtroAcao='';filtroTxt='';filtrar();atualizarTagFiltro();toast('Filtros limpos.');}
function atualizarTagFiltro(){var tag=document.getElementById('filtroAtivoTag');var partes=[];if(filtroAcao)partes.push('Ação: '+filtroAcao);if(filtroTxt)partes.push('Busca: "'+filtroTxt+'"');if(partes.length){tag.style.display='block';tag.textContent='🔧 Filtro ativo — '+partes.join('  ·  ');}else{tag.style.display='none';}}
function exportarExcel(){
  filtroAcao=document.getElementById('m-filtroAcao').value;filtroTxt=document.getElementById('m-filtroTxt').value.trim();
  var fd=getFiltrados();if(!fd.length){toast('Nenhum registro para exportar.','err');return;}
  var linhas=fd.map(function(d){var vol=d.volume_atual!=null?String(d.volume_atual).padStart(3,'0')+'/'+String(d.volume_total).padStart(3,'0'):'—';
    return{'Data/Hora':d.criado_em,'Usuário':d.usuario_nome,'Ação':d.acao,'Pedido':d.numero_pedido,'Volume':vol,'Palete':d.palete_codigo,'Endereço De':d.endereco_de,'Endereço Para':d.endereco_para,'Detalhe':d.detalhe_extra};});
  var agora=new Date();var ds=agora.toLocaleDateString('pt-BR').replace(/\//g,'-');var hs=agora.toLocaleTimeString('pt-BR').replace(/:/g,'-');
  if(typeof XLSX==='undefined'){exportarCSVFallback(linhas,ds,hs);return;}
  try{
    var ws=XLSX.utils.json_to_sheet(linhas);ws['!cols']=[{wch:18},{wch:18},{wch:14},{wch:12},{wch:10},{wch:10},{wch:14},{wch:14},{wch:30}];
    var wb=XLSX.utils.book_new();XLSX.utils.book_append_sheet(wb,ws,'Historico');
    XLSX.writeFile(wb,'historico_walze_'+ds+'_'+hs+'.xlsx');filtrar();atualizarTagFiltro();toast('✓ Relatório baixado: '+fd.length+' registro(s)');
  }catch(e){exportarCSVFallback(linhas,ds,hs);}
}
function exportarCSVFallback(linhas,ds,hs){
  var cab=Object.keys(linhas[0]);var rows=[cab.join(';')];
  linhas.forEach(function(l){rows.push(cab.map(function(c){return(l[c]==null?'':String(l[c])).replace(/;/g,',');}).join(';'));});
  var csv='\ufeff'+rows.join('\n');var blob=new Blob([csv],{type:'text/csv;charset=utf-8;'});
  var url=URL.createObjectURL(blob);var a=document.createElement('a');a.href=url;a.download='historico_walze_'+ds+'_'+hs+'.csv';
  document.body.appendChild(a);a.click();document.body.removeChild(a);URL.revokeObjectURL(url);
  filtrar();atualizarTagFiltro();toast('✓ Relatório CSV baixado: '+linhas.length+' registro(s)');
}
carregar();
</script>
""" + shell_close() + "</body></html>")
