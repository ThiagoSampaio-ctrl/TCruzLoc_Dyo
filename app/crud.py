from fastapi import HTTPException
from sqlalchemy.orm import Session
from app import models, schema


def listar_enderecos(db: Session):
    return db.query(models.Endereco).order_by(models.Endereco.codigo).all()


def listar_caixas(db: Session):
    return db.query(models.TipoCaixa).order_by(models.TipoCaixa.nome).all()


def listar_paletes(db: Session):
    return db.query(models.Palete).order_by(models.Palete.codigo).all()


def criar_palete_auto(db: Session, palete: schema.PaleteCriar):

    existente = db.query(models.Palete).filter(
        models.Palete.codigo == palete.codigo
    ).first()

    if existente:
        return existente

    endereco = db.query(models.Endereco).filter(
        models.Endereco.capacidade_usada < models.Endereco.capacidade_total
    ).order_by(models.Endereco.id).first()

    if not endereco:
        raise HTTPException(
            status_code=400,
            detail="Nenhum endereço disponível"
        )

    novo = models.Palete(
        codigo=palete.codigo,
        qtd_k0=palete.qtd_k0,
        qtd_k1=palete.qtd_k1,
        qtd_k2=palete.qtd_k2,
        qtd_k3=palete.qtd_k3,
        volume_total=0,
        endereco_codigo=endereco.codigo,
        status="ENDERECADO"
    )

    db.add(novo)
    db.commit()
    db.refresh(novo)

    return novo


def detalhes_endereco(db: Session, codigo_endereco: str):

    paletes = db.query(models.Palete).filter(
        models.Palete.endereco_codigo == codigo_endereco
    ).order_by(models.Palete.codigo).all()

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

        pedidos_agrupados = {}

        for pedido in pedidos:

            if pedido.palete_codigo != palete.codigo:
                continue

            numero = pedido.numero_pedido

            if numero not in pedidos_agrupados:
                pedidos_agrupados[numero] = []

            pedidos_agrupados[numero].append(
                f"{pedido.volume_atual:03d}/{pedido.volume_total:03d}"
            )

        lista_final = []

        for numero, volumes in pedidos_agrupados.items():
            lista_final.append({
                "pedido": numero,
                "volumes": volumes
            })

        resposta["paletes"].append({
            "palete": palete.codigo,
            "pedidos": lista_final
        })

    return resposta


def criar_pedido_volume(db: Session, pedido: schema.PedidoVolumeCriar):

    palete = db.query(models.Palete).filter(
        models.Palete.codigo == pedido.palete_codigo
    ).first()

    if not palete:
        raise HTTPException(
            status_code=404,
            detail="Palete não encontrado"
        )

    duplicado = db.query(models.PedidoVolume).filter(
        models.PedidoVolume.numero_pedido == pedido.numero_pedido,
        models.PedidoVolume.volume_atual == pedido.volume_atual,
        models.PedidoVolume.volume_total == pedido.volume_total,
        models.PedidoVolume.palete_codigo == pedido.palete_codigo
    ).first()

    if duplicado:
        raise HTTPException(
            status_code=400,
            detail="Este volume já foi cadastrado neste palete"
        )

    novo = models.PedidoVolume(
        numero_pedido=pedido.numero_pedido,
        volume_atual=pedido.volume_atual,
        volume_total=pedido.volume_total,
        palete_codigo=pedido.palete_codigo,
        endereco_codigo=palete.endereco_codigo
    )

    db.add(novo)
    db.commit()
    db.refresh(novo)

    return novo


def limpar_pedidos_duplicados(db: Session):

    pedidos = db.query(models.PedidoVolume).all()

    vistos = {}
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

    return {
        "status": "ok",
        "duplicados_removidos": removidos
    }


def buscar_pedido(db: Session, numero_pedido: str):

    registros = db.query(models.PedidoVolume).filter(
        models.PedidoVolume.numero_pedido == numero_pedido
    ).order_by(
        models.PedidoVolume.palete_codigo,
        models.PedidoVolume.volume_atual
    ).all()

    if not registros:
        raise HTTPException(
            status_code=404,
            detail="Pedido não encontrado"
        )

    resultado = {
        "pedido": numero_pedido,
        "enderecos": []
    }

    agrupado = {}

    for item in registros:
        chave = (
            item.endereco_codigo,
            item.palete_codigo
        )

        if chave not in agrupado:
            agrupado[chave] = []

        agrupado[chave].append(
            f"{item.volume_atual:03d}/{item.volume_total:03d}"
        )

    for (endereco, palete), volumes in agrupado.items():
        resultado["enderecos"].append({
            "endereco": endereco,
            "palete": palete,
            "volumes": volumes
        })

    return resultado
# -------------------------
# GERENCIAR VOLUMES
# -------------------------

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
        raise HTTPException(
            status_code=404,
            detail="Volume não encontrado"
        )

    db.delete(volume)
    db.commit()

    return {
        "status":"apagado"
    }


def deletar_varios_pedidos_volume(
    db: Session,
    ids: list[int]
):

    removidos = 0

    for volume_id in ids:

        volume = db.query(
            models.PedidoVolume
        ).filter(
            models.PedidoVolume.id == volume_id
        ).first()

        if volume:

            db.delete(volume)
            removidos += 1

    db.commit()

    return {
        "status":"ok",
        "removidos": removidos
    }