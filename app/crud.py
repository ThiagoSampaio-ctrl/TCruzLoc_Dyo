import re
from fastapi import HTTPException
from sqlalchemy.orm import Session
from app import models, schema
from app.auth import registrar


# ═══════════════════════════════════════════════
#  NORMALIZAÇÃO
# ═══════════════════════════════════════════════

def normalizar_endereco(codigo: str) -> str:
    s = re.sub(r'[\s\-]+', '', codigo.strip().upper())
    m = re.match(r'^R(\d{2})(\d{3})(\d{1,2}[A-Z]?)$', s)
    if m: return f"R{m.group(1)} {m.group(2)} {m.group(3)}"
    m = re.match(r'^R(\d{3})(\d{3})(\d{1,2}[A-Z]?)$', s)
    if m: return f"R{m.group(1)} {m.group(2)} {m.group(3)}"
    return ' '.join(codigo.strip().upper().split())


# ═══════════════════════════════════════════════
#  ENDEREÇOS
# ═══════════════════════════════════════════════

def listar_enderecos(db: Session):
    return db.query(models.Endereco).order_by(models.Endereco.codigo).all()


def atualizar_status_endereco(db: Session, codigo: str, status: str, usuario=None):
    e = db.query(models.Endereco).filter(models.Endereco.codigo == codigo).first()
    if not e:
        raise HTTPException(status_code=404, detail=f"Endereço '{codigo}' não encontrado")
    status_ant = e.status_ocupacao or "LIVRE"
    e.status_ocupacao = status
    if usuario:
        registrar(db, "STATUS_END", usuario,
                  endereco_de=status_ant, endereco_para=status,
                  detalhe_extra=f"Endereço {codigo}: {status_ant} → {status}")
    db.commit(); db.refresh(e)
    return e


def detalhes_endereco(db: Session, codigo: str):
    codigo = normalizar_endereco(codigo)
    paletes = (db.query(models.Palete)
               .filter(models.Palete.endereco_codigo == codigo)
               .order_by(models.Palete.codigo).all())
    volumes = (db.query(models.PedidoVolume)
               .filter(models.PedidoVolume.endereco_codigo == codigo)
               .order_by(models.PedidoVolume.palete_codigo,
                         models.PedidoVolume.numero_pedido,
                         models.PedidoVolume.volume_atual).all())
    resultado = {"endereco": codigo, "paletes": []}
    for p in paletes:
        ag: dict[str, list[str]] = {}
        for v in volumes:
            if v.palete_codigo != p.codigo: continue
            ag.setdefault(v.numero_pedido, []).append(
                f"{v.volume_atual:03d}/{v.volume_total:03d}")
        resultado["paletes"].append({
            "palete":  p.codigo,
            "pedidos": [{"pedido": n, "volumes": vs} for n, vs in ag.items()],
        })
    return resultado


# ═══════════════════════════════════════════════
#  CAIXAS
# ═══════════════════════════════════════════════

def listar_caixas(db: Session):
    return db.query(models.TipoCaixa).order_by(models.TipoCaixa.nome).all()


# ═══════════════════════════════════════════════
#  PALETES
# ═══════════════════════════════════════════════

def listar_paletes(db: Session):
    return db.query(models.Palete).order_by(models.Palete.codigo).all()


def criar_ou_usar_palete_manual(db: Session, codigo_palete: str,
                                 codigo_endereco: str, usuario=None):
    codigo_palete   = codigo_palete.strip().upper()
    codigo_endereco = normalizar_endereco(codigo_endereco)

    endereco = db.query(models.Endereco).filter(
        models.Endereco.codigo == codigo_endereco).first()
    if not endereco:
        raise HTTPException(status_code=404,
            detail=f"Endereço '{codigo_endereco}' não encontrado. "
                   f"Rode /seed para criar os endereços.")

    palete = db.query(models.Palete).filter(
        models.Palete.codigo == codigo_palete).first()

    if palete:
        if palete.endereco_codigo != codigo_endereco:
            end_ant = db.query(models.Endereco).filter(
                models.Endereco.codigo == palete.endereco_codigo).first()
            if end_ant and end_ant.capacidade_usada > 0:
                end_ant.capacidade_usada -= 1
            palete.endereco_codigo = codigo_endereco
            endereco.capacidade_usada = (endereco.capacidade_usada or 0) + 1
            db.query(models.PedidoVolume).filter(
                models.PedidoVolume.palete_codigo == codigo_palete
            ).update({"endereco_codigo": codigo_endereco})
            db.commit()
        db.refresh(palete)
        return palete

    novo = models.Palete(codigo=codigo_palete, volume_total=0,
                         endereco_codigo=codigo_endereco, status="EM USO")
    endereco.capacidade_usada = (endereco.capacidade_usada or 0) + 1
    db.add(novo); db.commit(); db.refresh(novo)
    return novo


def criar_palete_auto(db: Session, palete: schema.PaleteCriar):
    existente = db.query(models.Palete).filter(
        models.Palete.codigo == palete.codigo).first()
    if existente: return existente
    for e in db.query(models.Endereco).order_by(models.Endereco.id).all():
        if not db.query(models.Palete).filter(
                models.Palete.endereco_codigo == e.codigo).first():
            novo = models.Palete(codigo=palete.codigo, volume_total=0,
                                 endereco_codigo=e.codigo, status="EM USO")
            e.capacidade_usada = 1
            db.add(novo); db.commit(); db.refresh(novo)
            return novo
    raise HTTPException(status_code=400, detail="Nenhum endereço disponível")


# ═══════════════════════════════════════════════
#  PEDIDOS / VOLUMES
# ═══════════════════════════════════════════════

def criar_pedido_volume(db: Session, pedido: schema.PedidoVolumeCriar, usuario=None):
    palete = db.query(models.Palete).filter(
        models.Palete.codigo == pedido.palete_codigo).first()
    if not palete:
        raise HTTPException(status_code=404,
            detail=f"Palete '{pedido.palete_codigo}' não encontrado.")

    dup = db.query(models.PedidoVolume).filter(
        models.PedidoVolume.numero_pedido == pedido.numero_pedido,
        models.PedidoVolume.volume_atual  == pedido.volume_atual,
        models.PedidoVolume.volume_total  == pedido.volume_total,
        models.PedidoVolume.palete_codigo == pedido.palete_codigo,
    ).first()
    if dup:
        raise HTTPException(status_code=400,
            detail=f"Volume {pedido.volume_atual:03d}/{pedido.volume_total:03d} "
                   f"do pedido {pedido.numero_pedido} já está neste palete.")

    novo = models.PedidoVolume(
        numero_pedido=pedido.numero_pedido,
        volume_atual=pedido.volume_atual,
        volume_total=pedido.volume_total,
        palete_codigo=pedido.palete_codigo,
        endereco_codigo=palete.endereco_codigo,
    )
    db.add(novo)
    if usuario:
        registrar(db, "CADASTRO", usuario,
                  numero_pedido=pedido.numero_pedido,
                  volume_atual=pedido.volume_atual,
                  volume_total=pedido.volume_total,
                  palete_codigo=pedido.palete_codigo,
                  endereco_para=palete.endereco_codigo)
    db.commit(); db.refresh(novo)
    return novo


def buscar_pedido(db: Session, numero_pedido: str):
    numero_pedido = numero_pedido.strip().upper()
    registros = (db.query(models.PedidoVolume)
                 .filter(models.PedidoVolume.numero_pedido == numero_pedido)
                 .order_by(models.PedidoVolume.palete_codigo,
                           models.PedidoVolume.volume_atual).all())
    if not registros:
        raise HTTPException(status_code=404, detail="Pedido não encontrado")
    ag: dict[tuple, list[str]] = {}
    for r in registros:
        ag.setdefault((r.endereco_codigo, r.palete_codigo), []).append(
            f"{r.volume_atual:03d}/{r.volume_total:03d}")
    return {"pedido": numero_pedido,
            "enderecos": [{"endereco": e, "palete": p, "volumes": v}
                          for (e, p), v in ag.items()]}


def listar_pedidos_volume(db: Session):
    return (db.query(models.PedidoVolume)
            .order_by(models.PedidoVolume.palete_codigo,
                      models.PedidoVolume.numero_pedido,
                      models.PedidoVolume.volume_atual).all())


def deletar_pedido_volume(db: Session, volume_id: int, usuario=None):
    v = db.query(models.PedidoVolume).filter(
        models.PedidoVolume.id == volume_id).first()
    if not v:
        raise HTTPException(status_code=404, detail="Volume não encontrado")
    if usuario:
        registrar(db, "EXCLUSAO", usuario,
                  numero_pedido=v.numero_pedido,
                  volume_atual=v.volume_atual, volume_total=v.volume_total,
                  palete_codigo=v.palete_codigo, endereco_de=v.endereco_codigo)
    db.delete(v); db.commit()
    return {"ok": True}


def deletar_varios_pedidos_volume(db: Session, ids: list[int], usuario=None):
    volumes = db.query(models.PedidoVolume).filter(
        models.PedidoVolume.id.in_(ids)).all()
    for v in volumes:
        if usuario:
            registrar(db, "EXCLUSAO", usuario,
                      numero_pedido=v.numero_pedido,
                      volume_atual=v.volume_atual, volume_total=v.volume_total,
                      palete_codigo=v.palete_codigo, endereco_de=v.endereco_codigo)
        db.delete(v)
    db.commit()
    return {"ok": True, "removidos": len(volumes)}


def transferir_volumes(db: Session, dados: schema.TransferirVolumes, usuario=None):
    novo_end = normalizar_endereco(dados.novo_endereco)
    novo_pal = dados.novo_palete.strip().upper()
    endereco = db.query(models.Endereco).filter(
        models.Endereco.codigo == novo_end).first()
    if not endereco:
        raise HTTPException(status_code=404, detail=f"Endereço '{novo_end}' não encontrado.")
    palete_dest = db.query(models.Palete).filter(
        models.Palete.codigo == novo_pal).first()
    if not palete_dest:
        palete_dest = models.Palete(codigo=novo_pal, volume_total=0,
                                    endereco_codigo=novo_end, status="EM USO")
        endereco.capacidade_usada = (endereco.capacidade_usada or 0) + 1
        db.add(palete_dest); db.flush()
    volumes = db.query(models.PedidoVolume).filter(
        models.PedidoVolume.id.in_(dados.ids)).all()
    movidos = 0
    for v in volumes:
        end_ant, pal_ant = v.endereco_codigo, v.palete_codigo
        v.palete_codigo = novo_pal; v.endereco_codigo = novo_end
        if usuario:
            registrar(db, "TRANSFERENCIA", usuario,
                      numero_pedido=v.numero_pedido,
                      volume_atual=v.volume_atual, volume_total=v.volume_total,
                      palete_codigo=novo_pal, endereco_de=end_ant,
                      endereco_para=novo_end,
                      detalhe_extra=f"De {pal_ant} → {novo_pal}")
        movidos += 1
    db.commit()
    return {"ok": True, "movidos": movidos,
            "novo_palete": novo_pal, "novo_endereco": novo_end}


def limpar_pedidos_duplicados(db: Session):
    todos = db.query(models.PedidoVolume).order_by(models.PedidoVolume.id).all()
    vistos: set[tuple] = set()
    removidos = 0
    for p in todos:
        chave = (p.numero_pedido, p.volume_atual, p.volume_total, p.palete_codigo)
        if chave in vistos:
            db.delete(p); removidos += 1
        else:
            vistos.add(chave)
    db.commit()
    return {"ok": True, "removidos": removidos}


def listar_historico(db: Session, limit: int = 500):
    return (db.query(models.Historico)
            .order_by(models.Historico.id.desc())
            .limit(limit).all())