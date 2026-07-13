from fastapi import APIRouter, Depends, Header
from sqlalchemy.orm import Session
from app.database import get_db
from app import schema, crud
from app.auth import get_usuario_atual, exigir_admin

router = APIRouter(tags=["usuarios"])

# ── Perfil (próprio usuário) ──────────────────────────────────────
@router.get("/perfil-api", response_model=schema.PerfilResposta)
def perfil_proprio(db: Session = Depends(get_db), authorization: str = Header(default="")):
    u = get_usuario_atual(db, authorization)
    return crud.perfil_para_resposta(u, revelar_cpf=False)

@router.get("/perfil-api/cpf-completo")
def perfil_cpf_completo(db: Session = Depends(get_db), authorization: str = Header(default="")):
    u = get_usuario_atual(db, authorization)
    return {"cpf": u.cpf or ""}

@router.patch("/perfil-api", response_model=schema.PerfilResposta)
def atualizar_perfil_proprio(dados: schema.PerfilAtualizar, db: Session = Depends(get_db),
                             authorization: str = Header(default="")):
    u = get_usuario_atual(db, authorization)
    u = crud.atualizar_perfil(db, u, dados)
    return crud.perfil_para_resposta(u, revelar_cpf=False)

# ── Usuários (admin) ──────────────────────────────────────────────
@router.get("/usuarios-api")
def listar_usuarios_admin(db: Session = Depends(get_db), authorization: str = Header(default="")):
    u = get_usuario_atual(db, authorization)
    exigir_admin(u)
    return [crud.perfil_para_resposta(x, revelar_cpf=False) for x in crud.listar_usuarios(db)]

@router.patch("/usuarios-api/{usuario_id}/ativo")
def alternar_ativo(usuario_id: int, ativo: bool, db: Session = Depends(get_db),
                   authorization: str = Header(default="")):
    u = get_usuario_atual(db, authorization)
    exigir_admin(u)
    alvo = crud.alternar_ativo_usuario(db, usuario_id, ativo)
    return crud.perfil_para_resposta(alvo, revelar_cpf=False)