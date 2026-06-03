from sqlalchemy import Column, Integer, String, ForeignKey
from app.database import Base

class Endereco(Base):
    __tablename__ = "enderecos"

    id = Column(Integer, primary_key=True, index=True)
    codigo = Column(String, unique=True, index=True)
    rua = Column(String)
    predio = Column(String)
    andar = Column(String)
    frente = Column(String, default="N")
    comprimento_cm = Column(Integer)
    largura_cm = Column(Integer)
    altura_cm = Column(Integer)
    capacidade_total = Column(Integer)
    capacidade_usada = Column(Integer, default=0)


class TipoCaixa(Base):
    __tablename__ = "tipos_caixa"

    id = Column(Integer, primary_key=True, index=True)
    nome = Column(String, unique=True, index=True)
    comprimento_cm = Column(Integer)
    largura_cm = Column(Integer)
    altura_cm = Column(Integer)
    volume_cm3 = Column(Integer)


class Palete(Base):
    __tablename__ = "paletes"

    id = Column(Integer, primary_key=True, index=True)
    codigo = Column(String, unique=True, index=True)
    qtd_k0 = Column(Integer, default=0)
    qtd_k1 = Column(Integer, default=0)
    qtd_k2 = Column(Integer, default=0)
    qtd_k3 = Column(Integer, default=0)
    volume_total = Column(Integer)
    endereco_id = Column(Integer, ForeignKey("enderecos.id"))
    endereco_codigo = Column(String)
    status = Column(String, default="ENDERECADO")


class PedidoVolume(Base):
    __tablename__ = "pedidos_volumes"

    id = Column(Integer, primary_key=True, index=True)
    numero_pedido = Column(String, index=True)
    volume_atual = Column(Integer)
    volume_total = Column(Integer)
    palete_codigo = Column(String, index=True)
    endereco_codigo = Column(String, index=True)