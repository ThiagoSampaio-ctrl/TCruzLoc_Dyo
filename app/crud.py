from fastapi import HTTPException
from sqlalchemy.orm import Session
from app import models, schema


# ═══════════════════════════════════════════════
#  ENDEREÇOS
# ═══════════════════════════════════════════════

def listar_enderecos(db: Session):
    return db.query(models.Endereco).order_by(models.Endereco.codigo).all()


def detalhes_endereco(db: Session, codigo_endereco: str):
    paletes = db.query(models.Palete).filter(
        models.Palete.endereco_codigo == codigo_endereco
    ).order_by(models.Palete.codigo).all()

    pedidos = db.query(models.PedidoVolume).filter(
        models.PedidoVolume.endereco_codigo == codigo_endereco
    ).order_by(
        models.PedidoVolume.palete_codigo,
        models.PedidoVolume.numero_pedido,
        models.PedidoVolume.volume_atual,
    ).all()

    resposta = {"endereco": codigo_endereco, "paletes": []}

    for palete in paletes:
        agrupado: dict[str, list[str]] = {}
        for p in pedidos:
            if p.palete_codigo != palete.codigo:
                continue
            agrupado.setdefault(p.numero_pedido, []).append(
                f"{p.volume_atual:03d}/{p.volume_total:03d}"
            )
        resposta["paletes"].append({
            "palete":  palete.codigo,
            "pedidos": [{"pedido": num, "volumes": vols} for num, vols in agrupado.items()],
        })

    return resposta


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


def criar_palete_auto(db: Session, palete: schema.PaleteCriar):
    existente = db.query(models.Palete).filter(
        models.Palete.codigo == palete.codigo
    ).first()
    if existente:
        return existente

    enderecos = db.query(models.Endereco).order_by(models.Endereco.id).all()
    endereco = None
    for e in enderecos:
        tem_palete = db.query(models.Palete).filter(
            models.Palete.endereco_codigo == e.codigo
        ).first()
        if not tem_palete:
            endereco = e
            break

    if not endereco:
        raise HTTPException(status_code=400, detail="Nenhum endereço disponível")

    novo = models.Palete(
        codigo=palete.codigo,
        volume_total=0,
        endereco_codigo=endereco.codigo,
        status="EM USO",
    )
    endereco.capacidade_usada = 1
    db.add(novo)
    db.commit()
    db.refresh(novo)
    return novo


def criar_ou_usar_palete_manual(db: Session, codigo_palete: str, codigo_endereco: str):
    endereco = db.query(models.Endereco).filter(
        models.Endereco.codigo == codigo_endereco
    ).first()
    if not endereco:
        raise HTTPException(status_code=404, detail=f"Endereço '{codigo_endereco}' não encontrado")

    palete = db.query(models.Palete).filter(
        models.Palete.codigo == codigo_palete
    ).first()
    if palete:
        return palete  # já existe — reutiliza sem erro

    novo = models.Palete(
        codigo=codigo_palete,
        volume_total=0,
        endereco_codigo=codigo_endereco,
        status="EM USO",
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
            detail=f"Palete '{pedido.palete_codigo}' não encontrado. Crie o palete primeiro."
        )

    duplicado = db.query(models.PedidoVolume).filter(
        models.PedidoVolume.numero_pedido == pedido.numero_pedido,
        models.PedidoVolume.volume_atual  == pedido.volume_atual,
        models.PedidoVolume.volume_total  == pedido.volume_total,
        models.PedidoVolume.palete_codigo == pedido.palete_codigo,
    ).first()
    if duplicado:
        raise HTTPException(
            status_code=400,
            detail=f"Volume {pedido.volume_atual:03d}/{pedido.volume_total:03d} "
                   f"do pedido {pedido.numero_pedido} já está cadastrado neste palete",
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
    registros = db.query(models.PedidoVolume).filter(
        models.PedidoVolume.numero_pedido == numero_pedido
    ).order_by(
        models.PedidoVolume.palete_codigo,
        models.PedidoVolume.volume_atual,
    ).all()

    if not registros:
        raise HTTPException(status_code=404, detail="Pedido não encontrado")

    agrupado: dict[tuple, list[str]] = {}
    for item in registros:
        chave = (item.endereco_codigo, item.palete_codigo)
        agrupado.setdefault(chave, []).append(
            f"{item.volume_atual:03d}/{item.volume_total:03d}"
        )

    return {
        "pedido":    numero_pedido,
        "enderecos": [
            {"endereco": end, "palete": pal, "volumes": vols}
            for (end, pal), vols in agrupado.items()
        ],
    }


def listar_pedidos_volume(db: Session):
    return db.query(models.PedidoVolume).order_by(
        models.PedidoVolume.palete_codigo,
        models.PedidoVolume.numero_pedido,
        models.PedidoVolume.volume_atual,
    ).all()


def deletar_pedido_volume(db: Session, volume_id: int):
    volume = db.query(models.PedidoVolume).filter(
        models.PedidoVolume.id == volume_id
    ).first()
    if not volume:
        raise HTTPException(status_code=404, detail="Volume não encontrado")
    db.delete(volume)
    db.commit()
    return {"status": "apagado"}


def deletar_varios_pedidos_volume(db: Session, ids: list[int]):
    removidos = db.query(models.PedidoVolume).filter(
        models.PedidoVolume.id.in_(ids)
    ).delete(synchronize_session=False)
    db.commit()
    return {"status": "ok", "removidos": removidos}


def limpar_pedidos_duplicados(db: Session):
    pedidos = db.query(models.PedidoVolume).order_by(models.PedidoVolume.id).all()
    vistos: dict[tuple, int] = {}
    removidos = 0
    for p in pedidos:
        chave = (p.numero_pedido, p.volume_atual, p.volume_total, p.palete_codigo)
        if chave not in vistos:
            vistos[chave] = p.id
        else:
            db.delete(p)
            removidos += 1
    db.commit()
    return {"status": "ok", "duplicados_removidos": removidos}