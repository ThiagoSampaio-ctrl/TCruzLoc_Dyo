import hashlib
import secrets
from datetime import datetime, timedelta, timezone
from fastapi import HTTPException
from sqlalchemy.orm import Session
from app import models


def hash_senha(senha: str) -> str:
    return hashlib.sha256(senha.encode()).hexdigest()


def mascarar_cpf(cpf: str | None) -> str:
    if not cpf:
        return ""
    digitos = "".join(c for c in cpf if c.isdigit())
    if len(digitos) != 11:
        return cpf
    return f"{digitos[:3]}.***.**-{digitos[9:]}"


def criar_usuario(db: Session, nome: str, login: str, senha: str,
                  papel: str = "OPERADOR", email: str | None = None,
                  telefone: str | None = None, cpf: str | None = None,
                  foto_url: str | None = None) -> models.Usuario:
    login = login.strip().lower()
    if db.query(models.Usuario).filter(models.Usuario.login == login).first():
        raise HTTPException(status_code=400, detail="Login já existe")
    u = models.Usuario(
        nome=nome, login=login, senha_hash=hash_senha(senha),
        papel=papel.strip().upper() if papel else "OPERADOR",
        email=email, telefone=telefone, cpf=cpf, foto_url=foto_url,
    )
    db.add(u)
    db.commit()
    db.refresh(u)
    return u


def fazer_login(db: Session, login: str, senha: str) -> dict:
    u = db.query(models.Usuario).filter(
        models.Usuario.login == login.strip().lower(),
        models.Usuario.ativo == 1
    ).first()
    if not u or u.senha_hash != hash_senha(senha):
        raise HTTPException(status_code=401, detail="Login ou senha incorretos")
    token = secrets.token_hex(32)
    expira = datetime.now(timezone.utc) + timedelta(hours=12)
    db.add(models.Sessao(token=token, usuario_id=u.id, expira_em=expira))
    db.commit()
    return {"token": token, "nome": u.nome, "login": u.login, "papel": u.papel or "OPERADOR"}


def get_usuario_atual(db: Session, authorization: str = "") -> models.Usuario:
    token = authorization.replace("Bearer ", "").strip()
    if not token:
        raise HTTPException(status_code=401, detail="Token ausente")
    sess = db.query(models.Sessao).filter(models.Sessao.token == token).first()
    if not sess:
        raise HTTPException(status_code=401, detail="Sessão inválida")
    if sess.expira_em.replace(tzinfo=timezone.utc) < datetime.now(timezone.utc):
        db.delete(sess)
        db.commit()
        raise HTTPException(status_code=401, detail="Sessão expirada — faça login novamente")
    u = db.query(models.Usuario).filter(models.Usuario.id == sess.usuario_id).first()
    if not u or not u.ativo:
        raise HTTPException(status_code=401, detail="Usuário inativo")
    return u


def exigir_admin(usuario: models.Usuario):
    if (usuario.papel or "OPERADOR").upper() != "ADMIN":
        raise HTTPException(status_code=403, detail="Apenas administradores podem fazer isso")


def registrar(db: Session, acao: str, usuario: models.Usuario, **kwargs):
    db.add(models.Historico(acao=acao, usuario_id=usuario.id,
                            usuario_nome=usuario.nome, **kwargs))