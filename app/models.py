from sqlalchemy import Column, Integer, String
from app.database import Base


class Endereco(Base):
    __tablename__ = "enderecos"

    id = Column(Integer, primary_key=True, index=True)
    codigo = Column(String, unique=True, index=True)
    rua = Column(String)
    predio = Column(String)
    andar = Column(String)
    frente = Column(String)
    comprimento_cm = Column(Integer)
    largura_cm = Column(Integer)
    altura_cm = Column(Integer)
    capacidade_total = Column(Integer, default=1)
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
    volume_total = Column(Integer, default=0)
    endereco_codigo = Column(String, index=True)
    status = Column(String, default="EM USO")


class PedidoVolume(Base):
    __tablename__ = "pedidos_volume"

    id = Column(Integer, primary_key=True, index=True)
    numero_pedido = Column(String, index=True)
    volume_atual = Column(Integer)
    volume_total = Column(Integer)
    palete_codigo = Column(String, index=True)
    endereco_codigo = Column(String, index=True)