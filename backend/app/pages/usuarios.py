from fastapi import APIRouter
from fastapi.responses import HTMLResponse
from app.pages.shared import SHARED, shell_open, shell_close

router = APIRouter()

@router.get("/usuarios", response_class=HTMLResponse)
def pg_usuarios():
    return ("""<!DOCTYPE html><html lang="pt-BR"><head>""" + SHARED +
            """<title>WMS · Usuários</title></head><body>""" +
            shell_open('users','👥','var(--bdim)','Usuários','Gerencie quem tem acesso ao sistema') +
            r"""
<div class="card">
  <div class="ct">Criar Novo Usuário</div>
  <div class="g2">
    <div class="f"><label>Nome completo</label><input class="fi" id="nNome" placeholder="Ex: João Silva"></div>
    <div class="f"><label>Login</label><input class="fi" id="nLogin" placeholder="Ex: joao.silva"></div>
  </div>
  <div class="g2">
    <div class="f"><label>Senha</label><input class="fi" id="nSenha" type="password" placeholder="Mínimo 4 caracteres"></div>
    <div class="f"><label>Papel</label>
      <select id="nPapel" style="width:100%;padding:11px 13px;background:var(--bg);color:var(--txt);border:1px solid var(--br);border-radius:var(--r);font-size:14px;outline:none;">
        <option value="OPERADOR">Operador</option>
        <option value="ADMIN">Administrador</option>
      </select>
    </div>
  </div>
  <button class="btn bg" onclick="criarUsuario()">✓ Criar Usuário</button>
  <div id="nMsg" style="font-size:12px;margin-top:10px;min-height:18px;"></div>
</div>
<div class="card" style="margin-bottom:0;">
  <div class="ct">Usuários do Sistema</div>
  <div class="tw">
    <table>
      <thead><tr><th>Nome</th><th>Login</th><th>Papel</th><th>E-mail</th><th>Status</th><th>Ação</th></tr></thead>
      <tbody id="tbody"></tbody>
    </table>
  </div>
</div>
<script>
async function carregar(){
  document.getElementById('tbody').innerHTML='<tr><td colspan="6" style="color:var(--txt3);text-align:center;padding:20px;">Carregando...</td></tr>';
  try{
    var r=await fetch('/usuarios-api',{headers:authHeaders()});
    if(r.status===401){window.location.href='/login';return;}
    if(r.status===403){document.getElementById('tbody').innerHTML='<tr><td colspan="6" style="color:var(--rtxt);text-align:center;padding:20px;">Acesso restrito a administradores.</td></tr>';return;}
    var d=await r.json();
    document.getElementById('tbody').innerHTML=d.map(function(u){
      return '<tr>'+
        '<td style="font-weight:600;">'+u.nome+'</td>'+
        '<td style="font-family:var(--mono);color:var(--txt3);">'+u.login+'</td>'+
        '<td><span class="bk '+(u.papel==='ADMIN'?'bk-purple':'bk-blue')+'">'+u.papel+'</span></td>'+
        '<td style="color:var(--txt3);font-size:11.5px;">'+(u.email||'—')+'</td>'+
        '<td><span class="bk '+(u.ativo?'bk-green':'bk-red')+'">'+(u.ativo?'ATIVO':'INATIVO')+'</span></td>'+
        '<td><button class="btn '+(u.ativo?'bd':'bg')+'" style="padding:5px 10px;font-size:11px;" onclick="alternar('+u.id+','+(!u.ativo)+')">'+
          (u.ativo?'Desativar':'Ativar')+'</button></td>'+
        '</tr>';
    }).join('');
  }catch(e){}
}
async function alternar(id,novoAtivo){
  try{
    var r=await fetch('/usuarios-api/'+id+'/ativo?ativo='+novoAtivo,{method:'PATCH',headers:authHeaders()});
    var d=await r.json();
    if(d.detail){toast(d.detail,'err');return;}
    toast('Status atualizado.');carregar();
  }catch(e){toast('Erro de conexão','err');}
}
async function criarUsuario(){
  var nome=document.getElementById('nNome').value.trim();
  var login=document.getElementById('nLogin').value.trim();
  var senha=document.getElementById('nSenha').value;
  var papel=document.getElementById('nPapel').value;
  var msg=document.getElementById('nMsg');
  if(!nome||!login||!senha){msg.style.color='var(--rtxt)';msg.textContent='Preencha todos os campos.';return;}
  try{
    var r=await fetch('/auth/criar-usuario',{method:'POST',headers:authHeaders(),
      body:JSON.stringify({nome:nome,login:login,senha:senha,papel:papel})});
    var d=await r.json();
    if(d.detail){msg.style.color='var(--rtxt)';msg.textContent=d.detail;return;}
    msg.style.color='var(--gtxt)';msg.textContent='✓ Usuário "'+d.login+'" criado com sucesso!';
    document.getElementById('nNome').value='';document.getElementById('nLogin').value='';document.getElementById('nSenha').value='';
    toast('Usuário criado!');carregar();
  }catch(e){msg.style.color='var(--rtxt)';msg.textContent='Erro de conexão.';}
}

// Proteção: redireciona se não for admin
document.addEventListener('DOMContentLoaded',function(){
  if(!isAdmin()){window.location.href='/app';}
  else{carregar();}
});
</script>
""" + shell_close() + "</body></html>")

@router.get("/criar-admin", response_class=HTMLResponse)
def pg_criar_admin():
    return ("""<!DOCTYPE html><html lang="pt-BR"><head>""" + SHARED +
            """<title>WMS · Criar Administrador</title></head><body>
<div class="login-wrap">
<div class="login-box" style="max-width:420px;">
  <div class="login-logo"><div class="sb-logo">W</div><span>WALZE WMS</span></div>
  <div class="login-sub">Criação do primeiro administrador do sistema</div>
  <div class="f"><label>Nome completo</label><input class="fi" id="nome" placeholder="Ex: João Silva" autofocus></div>
  <div class="f"><label>Login</label><input class="fi" id="login" placeholder="Ex: joao.silva"></div>
  <div class="f"><label>Senha</label><input class="fi" id="senha" type="password" placeholder="Mínimo 4 caracteres"></div>
  <button class="btn bg bfull" onclick="criar()">Criar Administrador</button>
  <div class="err-msg" id="msg"></div>
</div></div>
<script>
async function criar(){
  var n=document.getElementById('nome').value.trim();
  var l=document.getElementById('login').value.trim();
  var s=document.getElementById('senha').value;
  var m=document.getElementById('msg');
  if(!n||!l||!s){m.textContent='Preencha todos os campos.';return;}
  try{
    var r=await fetch('/auth/criar-usuario',{method:'POST',
      headers:{'Content-Type':'application/json'},
      body:JSON.stringify({nome:n,login:l,senha:s,papel:'ADMIN'})});
    var d=await r.json();
    if(d.detail){m.textContent=d.detail;return;}
    m.style.color='var(--gtxt)';m.textContent='✓ Administrador criado! Redirecionando...';
    setTimeout(function(){window.location.href='/login';},1200);
  }catch(e){m.textContent='Erro de conexão.';}
}
</script></body></html>""")
