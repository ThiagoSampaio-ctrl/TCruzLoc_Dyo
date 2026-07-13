from fastapi import APIRouter
from fastapi.responses import HTMLResponse
from app.pages._shared import SHARED, shell_open, shell_close

router = APIRouter()

@router.get("/perfil", response_class=HTMLResponse)
def pg_perfil():
    return ("""<!DOCTYPE html><html lang="pt-BR"><head>""" + SHARED +
            """<title>WMS · Perfil</title></head><body>""" +
            shell_open('perfil','👤','var(--bdim)','Meu Perfil','Seus dados pessoais e configurações de conta') +
            r"""
<div style="display:grid;grid-template-columns:1fr 1fr;gap:16px;">
  <div class="card">
    <div class="ct">Dados pessoais</div>
    <div style="display:flex;align-items:center;gap:16px;margin-bottom:20px;">
      <div class="profile-photo" id="fotoPreview">?</div>
      <div>
        <div style="font-size:17px;font-weight:700;color:var(--txt);" id="pNomeDisplay">—</div>
        <div style="font-size:12px;color:var(--txt3);margin-top:3px;" id="pPapelDisplay">—</div>
        <div style="font-size:11px;color:var(--txt3);">@<span id="pLoginDisplay">—</span></div>
      </div>
    </div>
    <div class="f"><label>Nome completo</label><input class="fi" id="pNome" placeholder="Seu nome completo"></div>
    <div class="f"><label>E-mail</label><input class="fi" id="pEmail" type="email" placeholder="seu@email.com"></div>
    <div class="f"><label>Telefone</label><input class="fi" id="pTelefone" placeholder="(XX) 9 XXXX-XXXX"></div>
    <div class="f">
      <label>CPF <span id="cpfToggle" class="cpf-toggle" onclick="toggleCPF()" style="margin-left:8px;font-size:10px;">👁 Ver completo</span></label>
      <input class="fi" id="pCPF" placeholder="Somente números (11 dígitos)">
    </div>
    <div class="f"><label>URL da foto de perfil</label><input class="fi" id="pFoto" placeholder="https://... ou data:image/..."></div>
    <button class="btn bg bfull" style="margin-top:4px;" onclick="salvarPerfil()">💾 Salvar alterações</button>
    <div id="pMsg" style="font-size:12px;margin-top:10px;min-height:18px;"></div>
  </div>
  <div class="card">
    <div class="ct">Resumo da conta</div>
    <div style="display:flex;flex-direction:column;gap:0;">
      <div class="detail-row"><span>Login</span><span id="rLogin">—</span></div>
      <div class="detail-row"><span>Papel</span><span id="rPapel">—</span></div>
      <div class="detail-row"><span>Status</span><span id="rAtivo">—</span></div>
      <div class="detail-row"><span>E-mail</span><span id="rEmail">—</span></div>
      <div class="detail-row"><span>Telefone</span><span id="rTelefone">—</span></div>
      <div class="detail-row"><span>CPF</span><span id="rCPF">—</span></div>
    </div>
  </div>
</div>
<script>
var cpfVisivel=false;
async function carregarPerfil(){
  try{
    var r=await fetch('/perfil-api',{headers:authHeaders()});
    if(r.status===401){window.location.href='/login';return;}
    var d=await r.json();
    document.getElementById('pNome').value=d.nome||'';
    document.getElementById('pEmail').value=d.email||'';
    document.getElementById('pTelefone').value=d.telefone||'';
    document.getElementById('pCPF').value=d.cpf_mascarado||'';
    document.getElementById('pFoto').value=d.foto_url||'';
    document.getElementById('pNomeDisplay').textContent=d.nome||'—';
    document.getElementById('pPapelDisplay').textContent=d.papel==='ADMIN'?'Administrador':'Operador';
    document.getElementById('pLoginDisplay').textContent=d.login||'—';
    var fp=document.getElementById('fotoPreview');
    if(d.foto_url){fp.innerHTML='<img src="'+d.foto_url+'">';}
    else{var p=(d.nome||'').trim().split(' ');fp.textContent=p.length>=2?(p[0][0]+p[p.length-1][0]).toUpperCase():(d.nome||'?').substring(0,2).toUpperCase();}
    document.getElementById('rLogin').textContent=d.login||'—';
    document.getElementById('rPapel').textContent=d.papel==='ADMIN'?'Administrador':'Operador';
    document.getElementById('rAtivo').textContent=d.ativo?'Ativo':'Inativo';
    document.getElementById('rEmail').textContent=d.email||'—';
    document.getElementById('rTelefone').textContent=d.telefone||'—';
    document.getElementById('rCPF').textContent=d.cpf_mascarado||'—';
  }catch(e){}
}
async function toggleCPF(){
  if(cpfVisivel){cpfVisivel=false;carregarPerfil();document.getElementById('cpfToggle').textContent='👁 Ver completo';return;}
  try{
    var r=await fetch('/perfil-api/cpf-completo',{headers:authHeaders()});
    var d=await r.json();
    document.getElementById('pCPF').value=d.cpf||'';
    document.getElementById('cpfToggle').textContent='🙈 Ocultar';
    cpfVisivel=true;
  }catch(e){}
}
async function salvarPerfil(){
  var msg=document.getElementById('pMsg');
  var payload={};
  var nome=document.getElementById('pNome').value.trim();if(nome)payload.nome=nome;
  var email=document.getElementById('pEmail').value.trim();if(email)payload.email=email;
  var tel=document.getElementById('pTelefone').value.trim();if(tel)payload.telefone=tel;
  var foto=document.getElementById('pFoto').value.trim();if(foto)payload.foto_url=foto;
  var cpf=document.getElementById('pCPF').value.replace(/\D/g,'');if(cpf.length===11)payload.cpf=cpf;
  try{
    var r=await fetch('/perfil-api',{method:'PATCH',headers:authHeaders(),body:JSON.stringify(payload)});
    var d=await r.json();
    if(d.detail){msg.style.color='var(--rtxt)';msg.textContent=d.detail;return;}
    localStorage.setItem('wms_user',d.nome);
    if(d.foto_url)localStorage.setItem('wms_foto',d.foto_url);
    msg.style.color='var(--gtxt)';msg.textContent='✓ Perfil atualizado!';
    toast('Perfil salvo com sucesso!');carregarPerfil();cpfVisivel=false;
  }catch(e){msg.style.color='var(--rtxt)';msg.textContent='Erro de conexão.';}
}
carregarPerfil();
</script>
""" + shell_close() + "</body></html>")