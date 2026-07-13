from fastapi import APIRouter, Depends, Header
from sqlalchemy.orm import Session
from app.database import get_db
from app import schema, crud
from app.auth import get_usuario_atual

router = APIRouter(tags=["pedidos"])

# ── Volumes ────────────────────────────────────────────────────────
@router.delete("/pedidos-volume/duplicados")
def limpar_dup(db: Session = Depends(get_db)):
    return crud.limpar_pedidos_duplicados(db)

@router.post("/pedidos-volume/deletar-varios")
def deletar_varios(dados: schema.DeletarVolumes, db: Session = Depends(get_db),
                   authorization: str = Header(default="")):
    u = get_usuario_atual(db, authorization)
    return crud.deletar_varios_pedidos_volume(db, dados.ids, u)

@router.post("/pedidos-volume/transferir")
def transferir(dados: schema.TransferirVolumes, db: Session = Depends(get_db),
               authorization: str = Header(default="")):
    u = get_usuario_atual(db, authorization)
    return crud.transferir_volumes(db, dados, u)

@router.get("/pedidos-volume")
def listar_volumes(db: Session = Depends(get_db)):
    return crud.listar_pedidos_volume(db)

@router.post("/pedidos-volume", response_model=schema.PedidoVolumeResposta)
def criar_volume(pedido: schema.PedidoVolumeCriar, db: Session = Depends(get_db),
                 authorization: str = Header(default="")):
    u = get_usuario_atual(db, authorization)
    return crud.criar_pedido_volume(db, pedido, u)

@router.delete("/pedidos-volume/{volume_id}")
def deletar_volume(volume_id: int, db: Session = Depends(get_db),
                   authorization: str = Header(default="")):
    u = get_usuario_atual(db, authorization)
    return crud.deletar_pedido_volume(db, volume_id, u)

# ── Endereços ──────────────────────────────────────────────────────
@router.get("/enderecos-status")
def listar_enderecos_status(db: Session = Depends(get_db)):
    return [{"codigo": e.codigo, "status": e.status_ocupacao or "LIVRE"}
            for e in crud.listar_enderecos(db)]

@router.get("/enderecos/{codigo}/pedidos")
def pedidos_endereco_api(codigo: str, db: Session = Depends(get_db)):
    return crud.pedidos_no_endereco(db, codigo)

@router.get("/enderecos/{codigo}/detalhes")
def detalhes_endereco(codigo: str, db: Session = Depends(get_db)):
    return crud.detalhes_endereco(db, codigo)

@router.get("/enderecos", response_model=list[schema.EnderecoResposta])
def listar_enderecos(db: Session = Depends(get_db)):
    return crud.listar_enderecos(db)

@router.patch("/enderecos/{codigo}/status", response_model=schema.EnderecoResposta)
def atualizar_status(codigo: str, dados: schema.EnderecoStatusUpdate,
                     db: Session = Depends(get_db),
                     authorization: str = Header(default="")):
    u = get_usuario_atual(db, authorization)
    return crud.atualizar_status_endereco(db, codigo, dados.status_ocupacao, u)

@router.get("/pedidos/{numero_pedido}")
def buscar_pedido(numero_pedido: str, db: Session = Depends(get_db)):
    return crud.buscar_pedido(db, numero_pedido)

@router.get("/dashboard-api")
def dashboard_api(db: Session = Depends(get_db)):
    return crud.metricas_dashboard(db)

@router.get("/historico-api")
def historico_api(db: Session = Depends(get_db), authorization: str = Header(default="")):
    get_usuario_atual(db, authorization)
    return [{
        "id": h.id, "usuario_nome": h.usuario_nome or "—", "acao": h.acao,
        "numero_pedido": h.numero_pedido or "—", "volume_atual": h.volume_atual,
        "volume_total": h.volume_total, "palete_codigo": h.palete_codigo or "—",
        "endereco_de": h.endereco_de or "—", "endereco_para": h.endereco_para or "—",
        "detalhe_extra": h.detalhe_extra or "",
        "criado_em": h.criado_em.strftime("%d/%m/%Y %H:%M:%S") if h.criado_em else "—",
    } for h in crud.listar_historico(db)]