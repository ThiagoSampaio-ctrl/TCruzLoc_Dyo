from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, func
from app.database import Base


class Endereco(Base):
    __tablename__ = "enderecos"
    id               = Column(Integer, primary_key=True, index=True)
    codigo           = Column(String(30), unique=True, index=True, nullable=False)
    rua              = Column(String(20), nullable=False)
    predio           = Column(String(20), nullable=False)   # nível
    andar            = Column(String(10), nullable=False)   # posição
    frente           = Column(String(5),  default="A")
    comprimento_cm   = Column(Integer, default=120)
    largura_cm       = Column(Integer, default=100)
    altura_cm        = Column(Integer, default=200)
    capacidade_total = Column(Integer, default=1)
    capacidade_usada = Column(Integer, default=0)
    # LIVRE | PARCIAL | OCUPADO | BLOQUEADO — definido manualmente pelo operador
    status_ocupacao  = Column(String(12), default="LIVRE")


class TipoCaixa(Base):
    __tablename__ = "tipos_caixa"
    id             = Column(Integer, primary_key=True, index=True)
    nome           = Column(String(50), unique=True, index=True, nullable=False)
    comprimento_cm = Column(Integer)
    largura_cm     = Column(Integer)
    altura_cm      = Column(Integer)
    volume_cm3     = Column(Integer)


class Palete(Base):
    __tablename__ = "paletes"
    id              = Column(Integer, primary_key=True, index=True)
    codigo          = Column(String(30), unique=True, index=True, nullable=False)
    volume_total    = Column(Integer, default=0)
    endereco_codigo = Column(String(30), ForeignKey("enderecos.codigo"), nullable=False)
    status          = Column(String(20), default="EM USO")


class PedidoVolume(Base):
    __tablename__ = "pedidos_volumes"
    id              = Column(Integer, primary_key=True, index=True)
    numero_pedido   = Column(String(50), index=True, nullable=False)
    volume_atual    = Column(Integer, nullable=False)
    volume_total    = Column(Integer, nullable=False)
    palete_codigo   = Column(String(30), ForeignKey("paletes.codigo"), nullable=False)
    endereco_codigo = Column(String(30), ForeignKey("enderecos.codigo"), nullable=True)


class Usuario(Base):
    __tablename__ = "usuarios"
    id          = Column(Integer, primary_key=True, index=True)
    nome        = Column(String(60), nullable=False)
    login       = Column(String(40), unique=True, index=True, nullable=False)
    senha_hash  = Column(String(128), nullable=False)
    ativo       = Column(Integer, default=1)
    # papel: ADMIN | OPERADOR — controla quem vê/edita o perfil de outros
    papel       = Column(String(20), default="OPERADOR")
    # ── dados de perfil (sensíveis) ──
    email       = Column(String(120), nullable=True)
    telefone    = Column(String(20),  nullable=True)
    cpf         = Column(String(14),  nullable=True)   # armazenado mascarável; ver schema p/ exibição
    foto_url    = Column(String(500), nullable=True)   # data URL (base64) ou link
    criado_em   = Column(DateTime(timezone=True), server_default=func.now())


class Sessao(Base):
    __tablename__ = "sessoes"
    id         = Column(Integer, primary_key=True, index=True)
    token      = Column(String(64), unique=True, index=True, nullable=False)
    usuario_id = Column(Integer, ForeignKey("usuarios.id"), nullable=False)
    criado_em  = Column(DateTime(timezone=True), server_default=func.now())
    expira_em  = Column(DateTime(timezone=True), nullable=False)


class Historico(Base):
    __tablename__ = "historico"
    id            = Column(Integer, primary_key=True, index=True)
    usuario_id    = Column(Integer, ForeignKey("usuarios.id"), nullable=True)
    usuario_nome  = Column(String(60), nullable=True)
    acao          = Column(String(30), nullable=False)
    numero_pedido = Column(String(50), nullable=True)
    volume_atual  = Column(Integer, nullable=True)
    volume_total  = Column(Integer, nullable=True)
    palete_codigo = Column(String(30), nullable=True)
    endereco_de   = Column(String(30), nullable=True)
    endereco_para = Column(String(30), nullable=True)
    detalhe_extra = Column(String(200), nullable=True)
    criado_em     = Column(DateTime(timezone=True), server_default=func.now())
