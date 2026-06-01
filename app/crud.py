from fastapi import HTTPException
from sqlalchemy.orm import Session
from app import models, schema


# ─────────────────────────────────────────────
#  ENDEREÇOS
# ─────────────────────────────────────────────

def listar_enderecos(db: Session):
    return db.query(models.Endereco).order_by(models.Endereco.codigo).all()


def detalhes_endereco(db: Session, codigo_endereco: str):
    """
    Retorna um endereço com todos os seus paletes e, dentro de cada
    palete, os pedidos agrupados com seus volumes.
    """
    paletes = db.query(models.Palete).filter(
        models.Palete.endereco_codigo == codigo_endereco
    ).order_by(models.Palete.codigo).all()

    # Busca todos os volumes desse endereço de uma só vez (evita N+1 queries)
    pedidos = db.query(models.PedidoVolume).filter(
        models.PedidoVolume.endereco_codigo == codigo_endereco
    ).order_by(
        models.PedidoVolume.palete_codigo,
        models.PedidoVolume.numero_pedido,
        models.PedidoVolume.volume_atual
    ).all()

    resposta = {
        "endereco": codigo_endereco,
        "paletes": []
    }

    for palete in paletes:
        pedidos_agrupados: dict[str, list[str]] = {}

        for pedido in pedidos:
            if pedido.palete_codigo != palete.codigo:
                continue
            numero = pedido.numero_pedido
            if numero not in pedidos_agrupados:
                pedidos_agrupados[numero] = []
            pedidos_agrupados[numero].append(
                f"{pedido.volume_atual:03d}/{pedido.volume_total:03d}"
            )

        lista_final = [
            {"pedido": numero, "volumes": volumes}
            for numero, volumes in pedidos_agrupados.items()
        ]

        resposta["paletes"].append({
            "palete": palete.codigo,
            "pedidos": lista_final
        })

    return resposta


# ─────────────────────────────────────────────
#  CAIXAS
# ─────────────────────────────────────────────

def listar_caixas(db: Session):
    return db.query(models.TipoCaixa).order_by(models.TipoCaixa.nome).all()


# ─────────────────────────────────────────────
#  PALETES
# ─────────────────────────────────────────────

def listar_paletes(db: Session):
    return db.query(models.Palete).order_by(models.Palete.codigo).all()


def criar_palete_auto(db: Session, palete: schema.PaleteCriar):
    """
    Cria um palete com endereço atribuído automaticamente
    (primeiro endereço sem palete vinculado).
    Se o palete já existir, retorna o existente sem erro.
    """
    existente = db.query(models.Palete).filter(
        models.Palete.codigo == palete.codigo
    ).first()
    if existente:
        return existente

    # Busca o primeiro endereço sem palete vinculado
    enderecos = db.query(models.Endereco).order_by(models.Endereco.id).all()
    endereco = None
    for e in enderecos:
        palete_no_endereco = db.query(models.Palete).filter(
            models.Palete.endereco_codigo == e.codigo
        ).first()
        if not palete_no_endereco:
            endereco = e
            break

    if not endereco:
        raise HTTPException(status_code=400, detail="Nenhum endereço disponível")

    novo = models.Palete(
        codigo=palete.codigo,
        volume_total=0,
        endereco_codigo=endereco.codigo,
        status="EM USO"
    )
    endereco.capacidade_usada = 1
    db.add(novo)
    db.commit()
    db.refresh(novo)
    return novo


def criar_ou_usar_palete_manual(db: Session, codigo_palete: str, codigo_endereco: str):
    """
    Cria um palete no endereço informado.
    Se o palete já existir (mesmo código), retorna o existente — permitindo
    adicionar mais pedidos ao mesmo palete sem erro.
    O endereço deve existir no banco.
    """
    endereco = db.query(models.Endereco).filter(
        models.Endereco.codigo == codigo_endereco
    ).first()
    if not endereco:
        raise HTTPException(status_code=404, detail="Endereço não encontrado")

    palete = db.query(models.Palete).filter(
        models.Palete.codigo == codigo_palete
    ).first()
    if palete:
        # Palete já existe — apenas retorna sem criar duplicata
        return palete

    novo = models.Palete(
        codigo=codigo_palete,
        volume_total=0,
        endereco_codigo=codigo_endereco,
        status="EM USO"
    )
    endereco.capacidade_usada = 1
    db.add(novo)
    db.commit()
    db.refresh(novo)
    return novo


# ─────────────────────────────────────────────
#  PEDIDOS / VOLUMES
# ─────────────────────────────────────────────

def criar_pedido_volume(db: Session, pedido: schema.PedidoVolumeCriar):
    """
    Cadastra um volume de pedido em um palete.
    Valida: palete deve existir; volume não pode ser duplicado.
    """
    palete = db.query(models.Palete).filter(
        models.Palete.codigo == pedido.palete_codigo
    ).first()
    if not palete:
        raise HTTPException(status_code=404, detail="Palete não encontrado")

    duplicado = db.query(models.PedidoVolume).filter(
        models.PedidoVolume.numero_pedido == pedido.numero_pedido,
        models.PedidoVolume.volume_atual  == pedido.volume_atual,
        models.PedidoVolume.volume_total  == pedido.volume_total,
        models.PedidoVolume.palete_codigo == pedido.palete_codigo
    ).first()
    if duplicado:
        raise HTTPException(
            status_code=400,
            detail=f"Volume {pedido.volume_atual:03d}/{pedido.volume_total:03d} "
                   f"do pedido {pedido.numero_pedido} já está cadastrado neste palete"
        )

    novo = models.PedidoVolume(
        numero_pedido=pedido.numero_pedido,
        volume_atual=pedido.volume_atual,
        volume_total=pedido.volume_total,
        palete_codigo=pedido.palete_codigo,
        endereco_codigo=palete.endereco_codigo   # herdado do palete
    )
    db.add(novo)
    db.commit()
    db.refresh(novo)
    return novo


def buscar_pedido(db: Session, numero_pedido: str):
    """
    Retorna todos os endereços/paletes onde um pedido está alocado,
    com a lista de volumes em cada local.
    """
    registros = db.query(models.PedidoVolume).filter(
        models.PedidoVolume.numero_pedido == numero_pedido
    ).order_by(
        models.PedidoVolume.palete_codigo,
        models.PedidoVolume.volume_atual
    ).all()

    if not registros:
        raise HTTPException(status_code=404, detail="Pedido não encontrado")

    resultado = {"pedido": numero_pedido, "enderecos": []}
    agrupado: dict[tuple, list[str]] = {}

    for item in registros:
        chave = (item.endereco_codigo, item.palete_codigo)
        if chave not in agrupado:
            agrupado[chave] = []
        agrupado[chave].append(
            f"{item.volume_atual:03d}/{item.volume_total:03d}"
        )

    for (endereco, palete), volumes in agrupado.items():
        resultado["enderecos"].append({
            "endereco": endereco,
            "palete":   palete,
            "volumes":  volumes
        })

    return resultado


def listar_pedidos_volume(db: Session):
    return db.query(models.PedidoVolume).order_by(
        models.PedidoVolume.palete_codigo,
        models.PedidoVolume.numero_pedido,
        models.PedidoVolume.volume_atual
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
    """
    Apaga múltiplos volumes de uma vez.
    Usa uma única query em vez de N queries individuais.
    """
    removidos = db.query(models.PedidoVolume).filter(
        models.PedidoVolume.id.in_(ids)
    ).delete(synchronize_session=False)
    db.commit()
    return {"status": "ok", "removidos": removidos}


def limpar_pedidos_duplicados(db: Session):
    """
    Remove registros duplicados mantendo o de menor ID para cada
    combinação (pedido, volume_atual, volume_total, palete).
    """
    pedidos = db.query(models.PedidoVolume).order_by(models.PedidoVolume.id).all()
    vistos: dict[tuple, int] = {}
    removidos = 0

    for pedido in pedidos:
        chave = (
            pedido.numero_pedido,
            pedido.volume_atual,
            pedido.volume_total,
            pedido.palete_codigo
        )
        if chave not in vistos:
            vistos[chave] = pedido.id
        else:
            db.delete(pedido)
            removidos += 1

    db.commit()
    return {"status": "ok", "duplicados_removidos": removidos}
