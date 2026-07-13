from fastapi import APIRouter, Depends, Header
from sqlalchemy.orm import Session
from app.database import get_db
from app import models, schema, crud
from app.auth import get_usuario_atual

router = APIRouter(prefix="/paletes", tags=["paletes"])

@router.post("/manual", response_model=schema.PaleteResposta)
def criar_palete_manual(dados: schema.PaleteManualCriar, db: Session = Depends(get_db),
                        authorization: str = Header(default="")):
    u = get_usuario_atual(db, authorization)
    return crud.criar_ou_usar_palete_manual(db, dados.codigo_palete, dados.codigo_endereco, u)

@router.post("/auto", response_model=schema.PaleteResposta)
def criar_palete_auto(palete: schema.PaleteCriar, db: Session = Depends(get_db)):
    return crud.criar_palete_auto(db, palete)

@router.get("", response_model=list[schema.PaleteResposta])
def listar_paletes(db: Session = Depends(get_db)):
    return crud.listar_paletes(db)

@router.post("/finalizar/{codigo_palete}")
def finalizar_palete(codigo_palete: str, db: Session = Depends(get_db)):
    from fastapi import HTTPException
    palete = db.query(models.Palete).filter(models.Palete.codigo == codigo_palete).first()
    if not palete:
        raise HTTPException(status_code=404, detail="Palete não encontrado")
    palete.status = "FINALIZADO"
    db.query(models.PedidoVolume).filter(
        models.PedidoVolume.palete_codigo == codigo_palete
    ).update({"status": "FINALIZADO"}, synchronize_session=False)
    db.commit()
    return {"ok": True, "palete": codigo_palete, "status": "FINALIZADO"}