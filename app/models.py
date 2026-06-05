from sqlalchemy import Column, Integer, String, ForeignKey, DateTime, func
from app.database import Base


class Endereco(Base):
    __tablename__ = "enderecos"

    id               = Column(Integer, primary_key=True, index=True)
    codigo           = Column(String, unique=True, index=True, nullable=False)
    rua              = Column(String, nullable=False)
    predio           = Column(String, nullable=False)
    andar            = Column(String, nullable=False)
    frente           = Column(String, default="N")
    comprimento_cm   = Column(Integer, default=100)
    largura_cm       = Column(Integer, default=100)
    altura_cm        = Column(Integer, default=100)
    capacidade_total = Column(Integer, default=1)
    capacidade_usada = Column(Integer, default=0)


class TipoCaixa(Base):
    __tablename__ = "tipos_caixa"

    id             = Column(Integer, primary_key=True, index=True)
    nome           = Column(String, unique=True, index=True, nullable=False)
    comprimento_cm = Column(Integer)
    largura_cm     = Column(Integer)
    altura_cm      = Column(Integer)
    volume_cm3     = Column(Integer)


class Palete(Base):
    __tablename__ = "paletes"

    id              = Column(Integer, primary_key=True, index=True)
    codigo          = Column(String, unique=True, index=True, nullable=False)
    volume_total    = Column(Integer, default=0)
    endereco_codigo = Column(String, ForeignKey("enderecos.codigo"), nullable=False)
    status          = Column(String, default="EM USO")
    criado_em       = Column(DateTime(timezone=True), server_default=func.now())


class PedidoVolume(Base):
    __tablename__ = "pedidos_volumes"

    id              = Column(Integer, primary_key=True, index=True)
    numero_pedido   = Column(String, index=True, nullable=False)
    volume_atual    = Column(Integer, nullable=False)
    volume_total    = Column(Integer, nullable=False)
    palete_codigo   = Column(String, ForeignKey("paletes.codigo"), nullable=False)
    endereco_codigo = Column(String, ForeignKey("enderecos.codigo"), nullable=True)
    criado_em       = Column(DateTime(timezone=True), server_default=func.now())