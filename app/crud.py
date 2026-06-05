import re
from fastapi import HTTPException
from sqlalchemy.orm import Session
from app import models, schema


# ═══════════════════════════════════════════════
#  NORMALIZAÇÃO DE ENDEREÇO
#  Aceita qualquer formato:
#    r070141 | R070141 | R07 014 1 | r07 014 1 | R07-014-1 | r07014 1f
#  → sempre retorna "R07 014 1" ou "R07 014 1F"
# ═══════════════════════════════════════════════

def normalizar_endereco(codigo: str) -> str:
    # limpa e coloca maiúsculo
    s = re.sub(r'[\s\-]+', '', codigo.strip().upper())

    # R + 2 dígitos + 3 dígitos + sufixo (1, 2, 1F, 2F, 1f …)
    # ex: R070141 -> R07 014 1   |  R0701 41F -> R07 014 1F
    m = re.match(r'^R(\d{2})(\d{3})(\d{1,2}[A-Z]?)$', s)
    if m:
        return f"R{m.group(1)} {m.group(2)} {m.group(3)}"

    # R + 3 dígitos + 3 dígitos + sufixo
    m = re.match(r'^R(\d{3})(\d{3})(\d{1,2}[A-Z]?)$', s)
    if m:
        return f"R{m.group(1)} {m.group(2)} {m.group(3)}"

    # fallback: só maiúsculo com espaços simples
    return ' '.join(codigo.strip().upper().split())


# ═══════════════════════════════════════════════
#  ENDEREÇOS
# ═══════════════════════════════════════════════

def listar_enderecos(db: Session):
    return db.query(models.Endereco).order_by(models.Endereco.codigo).all()


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
        agrupado: dict[str, list[str]] = {}
        for v in volumes:
            if v.palete_codigo != p.codigo:
                continue
            agrupado.setdefault(v.numero_pedido, []).append(
                f"{v.volume_atual:03d}/{v.volume_total:03d}"
            )
        resultado["paletes"].append({
            "palete":  p.codigo,
            "pedidos": [{"pedido": num, "volumes": vols}
                        for num, vols in agrupado.items()],
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


def criar_ou_usar_palete_manual(db: Session, codigo_palete: str, codigo_endereco: str):
    codigo_palete   = codigo_palete.strip().upper()
    codigo_endereco = normalizar_endereco(codigo_endereco)

    # Verifica se endereço existe
    endereco = db.query(models.Endereco).filter(
        models.Endereco.codigo == codigo_endereco
    ).first()
    if not endereco:
        raise HTTPException(
            status_code=404,
            detail=f"Endereço '{codigo_endereco}' não encontrado. "
                   f"Verifique o código ou rode /seed para criar os endereços."
        )

    palete = db.query(models.Palete).filter(
        models.Palete.codigo == codigo_palete
    ).first()

    if palete:
        # ── PALETE JÁ EXISTE ──────────────────────────────────────────────
        # O endereço digitado pelo conferente SEMPRE prevalece.
        # Se mudou de endereço, atualiza o palete E os volumes vinculados.
        if palete.endereco_codigo != codigo_endereco:
            # libera capacidade do endereço antigo
            end_antigo = db.query(models.Endereco).filter(
                models.Endereco.codigo == palete.endereco_codigo
            ).first()
            if end_antigo and end_antigo.capacidade_usada > 0:
                end_antigo.capacidade_usada -= 1

            # atualiza o palete para o novo endereço
            palete.endereco_codigo = codigo_endereco
            endereco.capacidade_usada = (endereco.capacidade_usada or 0) + 1

            # atualiza todos os volumes deste palete para o novo endereço
            db.query(models.PedidoVolume).filter(
                models.PedidoVolume.palete_codigo == codigo_palete
            ).update({"endereco_codigo": codigo_endereco})

            db.commit()
        db.refresh(palete)
        return palete

    # ── PALETE NOVO ───────────────────────────────────────────────────────
    novo = models.Palete(
        codigo=codigo_palete,
        volume_total=0,
        endereco_codigo=codigo_endereco,
        status="EM USO",
    )
    endereco.capacidade_usada = (endereco.capacidade_usada or 0) + 1
    db.add(novo)
    db.commit()
    db.refresh(novo)
    return novo


def criar_palete_auto(db: Session, palete: schema.PaleteCriar):
    existente = db.query(models.Palete).filter(
        models.Palete.codigo == palete.codigo
    ).first()
    if existente:
        return existente

    endereco = None
    for e in db.query(models.Endereco).order_by(models.Endereco.id).all():
        tem = db.query(models.Palete).filter(
            models.Palete.endereco_codigo == e.codigo
        ).first()
        if not tem:
            endereco = e
            break

    if not endereco:
        raise HTTPException(status_code=400, detail="Nenhum endereço disponível")

    novo = models.Palete(
        codigo=palete.codigo, volume_total=0,
        endereco_codigo=endereco.codigo, status="EM USO",
    )
    endereco.capacidade_usada = 1
    db.add(novo)
    db.commit()
    db.refresh(novo)
    return novo


# ═══════════════════════════════════════════════
#  PEDIDOS / VOLUMES
# ═══════════════════════════════════════════════

def criar_pedido_volume(db: Session, pedido: schema.PedidoVolumeCriar):
    palete = db.query(models.Palete).filter(
        models.Palete.codigo == pedido.palete_codigo
    ).first()
    if not palete:
        raise HTTPException(
            status_code=404,
            detail=f"Palete '{pedido.palete_codigo}' não encontrado. Crie-o primeiro na aba Conferente."
        )

    dup = db.query(models.PedidoVolume).filter(
        models.PedidoVolume.numero_pedido == pedido.numero_pedido,
        models.PedidoVolume.volume_atual  == pedido.volume_atual,
        models.PedidoVolume.volume_total  == pedido.volume_total,
        models.PedidoVolume.palete_codigo == pedido.palete_codigo,
    ).first()
    if dup:
        raise HTTPException(
            status_code=400,
            detail=f"Volume {pedido.volume_atual:03d}/{pedido.volume_total:03d} "
                   f"do pedido {pedido.numero_pedido} já está neste palete."
        )

    novo = models.PedidoVolume(
        numero_pedido=pedido.numero_pedido,
        volume_atual=pedido.volume_atual,
        volume_total=pedido.volume_total,
        palete_codigo=pedido.palete_codigo,
        endereco_codigo=palete.endereco_codigo,
    )
    db.add(novo)
    db.commit()
    db.refresh(novo)
    return novo


def buscar_pedido(db: Session, numero_pedido: str):
    numero_pedido = numero_pedido.strip().upper()
    registros = (db.query(models.PedidoVolume)
                 .filter(models.PedidoVolume.numero_pedido == numero_pedido)
                 .order_by(models.PedidoVolume.palete_codigo,
                           models.PedidoVolume.volume_atual).all())
    if not registros:
        raise HTTPException(status_code=404, detail="Pedido não encontrado")

    agrupado: dict[tuple, list[str]] = {}
    for r in registros:
        agrupado.setdefault((r.endereco_codigo, r.palete_codigo), []).append(
            f"{r.volume_atual:03d}/{r.volume_total:03d}"
        )
    return {
        "pedido": numero_pedido,
        "enderecos": [{"endereco": e, "palete": p, "volumes": v}
                      for (e, p), v in agrupado.items()],
    }


def listar_pedidos_volume(db: Session):
    return (db.query(models.PedidoVolume)
            .order_by(models.PedidoVolume.palete_codigo,
                      models.PedidoVolume.numero_pedido,
                      models.PedidoVolume.volume_atual).all())


def deletar_pedido_volume(db: Session, volume_id: int):
    v = db.query(models.PedidoVolume).filter(
        models.PedidoVolume.id == volume_id).first()
    if not v:
        raise HTTPException(status_code=404, detail="Volume não encontrado")
    db.delete(v)
    db.commit()
    return {"ok": True}


def deletar_varios_pedidos_volume(db: Session, ids: list[int]):
    n = (db.query(models.PedidoVolume)
         .filter(models.PedidoVolume.id.in_(ids))
         .delete(synchronize_session=False))
    db.commit()
    return {"ok": True, "removidos": n}


def limpar_pedidos_duplicados(db: Session):
    todos = (db.query(models.PedidoVolume)
             .order_by(models.PedidoVolume.id).all())
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
