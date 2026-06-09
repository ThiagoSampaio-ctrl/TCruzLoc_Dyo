from typing import Optional
from pydantic import BaseModel, field_validator


# ─── Endereço ───────────────────────────────
class EnderecoResposta(BaseModel):
    id: int; codigo: str; rua: str; predio: str; andar: str
    frente: str; comprimento_cm: int; largura_cm: int
    altura_cm: int; capacidade_total: int; capacidade_usada: int
    class Config: from_attributes = True


# ─── Caixa ──────────────────────────────────
class CaixaResposta(BaseModel):
    id: int; nome: str; comprimento_cm: int
    largura_cm: int; altura_cm: int; volume_cm3: int
    class Config: from_attributes = True


# ─── Palete ─────────────────────────────────
class PaleteCriar(BaseModel):
    codigo: str
    @field_validator("codigo")
    @classmethod
    def norm(cls, v): return v.strip().upper()

class PaleteManualCriar(BaseModel):
    codigo_palete: str
    codigo_endereco: str
    @field_validator("codigo_palete", "codigo_endereco")
    @classmethod
    def norm(cls, v): return v.strip().upper()

class PaleteResposta(BaseModel):
    id: int; codigo: str; volume_total: int
    endereco_codigo: str; status: str
    class Config: from_attributes = True


# ─── Pedido / Volume ────────────────────────
class PedidoVolumeCriar(BaseModel):
    numero_pedido: str
    volume_atual:  int
    volume_total:  int
    palete_codigo: str
    @field_validator("numero_pedido", "palete_codigo")
    @classmethod
    def norm(cls, v): return v.strip().upper()

class PedidoVolumeResposta(BaseModel):
    id: int; numero_pedido: str; volume_atual: int
    volume_total: int; palete_codigo: str
    endereco_codigo: Optional[str] = None
    class Config: from_attributes = True

class DeletarVolumes(BaseModel):
    ids: list[int]

class TransferirVolumes(BaseModel):
    ids:             list[int]
    novo_palete:     str
    novo_endereco:   str
    @field_validator("novo_palete", "novo_endereco")
    @classmethod
    def norm(cls, v): return v.strip().upper()


# ─── Auth ────────────────────────────────────
class LoginInput(BaseModel):
    login: str
    senha: str

class LoginResposta(BaseModel):
    token:  str
    nome:   str
    login:  str

class UsuarioCriar(BaseModel):
    nome:  str
    login: str
    senha: str

class UsuarioResposta(BaseModel):
    id: int; nome: str; login: str; ativo: int
    class Config: from_attributes = True


# ─── Histórico ───────────────────────────────
class HistoricoResposta(BaseModel):
    id: int
    usuario_nome:   Optional[str] = None
    acao:           str
    numero_pedido:  Optional[str] = None
    volume_atual:   Optional[int] = None
    volume_total:   Optional[int] = None
    palete_codigo:  Optional[str] = None
    endereco_de:    Optional[str] = None
    endereco_para:  Optional[str] = None
    detalhe_extra:  Optional[str] = None
    criado_em:      Optional[str] = None
    class Config: from_attributes = True