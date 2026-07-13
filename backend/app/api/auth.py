from fastapi import APIRouter, Depends, Header
from sqlalchemy.orm import Session
from app.database import get_db
from app import models, schema, crud
from app.auth import criar_usuario, fazer_login, get_usuario_atual, exigir_admin

router = APIRouter(prefix="/auth", tags=["auth"])

@router.post("/login", response_model=schema.LoginResposta)
def api_login(dados: schema.LoginInput, db: Session = Depends(get_db)):
    return fazer_login(db, dados.login, dados.senha)

@router.post("/criar-usuario", response_model=schema.UsuarioResposta)
def api_criar_usuario(dados: schema.UsuarioCriar, db: Session = Depends(get_db),
                      authorization: str = Header(default="")):
    tem_usuarios = db.query(models.Usuario).first() is not None
    if tem_usuarios:
        u = get_usuario_atual(db, authorization)
        exigir_admin(u)
    return criar_usuario(db, dados.nome, dados.login, dados.senha, dados.papel,
                         dados.email, dados.telefone, dados.cpf)

@router.get("/me")
def api_me(db: Session = Depends(get_db), authorization: str = Header(default="")):
    u = get_usuario_atual(db, authorization)
    return crud.perfil_para_resposta(u, revelar_cpf=False)