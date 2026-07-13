from typing import Optional
from pydantic import BaseModel, field_validator


class EnderecoResposta(BaseModel):
    id: int
    codigo: str
    rua: str
    predio: str
    andar: str
    frente: str
    comprimento_cm: int
    largura_cm: int
    altura_cm: int
    capacidade_total: int
    capacidade_usada: int
    status_ocupacao: str = "LIVRE"
    class Config:
        from_attributes = True

class EnderecoStatusUpdate(BaseModel):
    status_ocupacao: str
    @field_validator("status_ocupacao")
    @classmethod
    def validar(cls, v):
        v = v.strip().upper()
        if v not in ("LIVRE","PARCIAL","OCUPADO","BLOQUEADO"):
            raise ValueError("Status inválido")
        return v

class CaixaResposta(BaseModel):
    id: int; nome: str; comprimento_cm: int; largura_cm: int; altura_cm: int; volume_cm3: int
    class Config:
        from_attributes = True

class PaleteCriar(BaseModel):
    codigo: str
    @field_validator("codigo")
    @classmethod
    def norm(cls, v): return v.strip().upper()

class PaleteManualCriar(BaseModel):
    codigo_palete: str
    codigo_endereco: str
    @field_validator("codigo_palete","codigo_endereco")
    @classmethod
    def norm(cls, v): return v.strip().upper()

class PaleteResposta(BaseModel):
    id: int; codigo: str; volume_total: int; endereco_codigo: str; status: str
    class Config:
        from_attributes = True

class PedidoVolumeCriar(BaseModel):
    numero_pedido: str; volume_atual: int; volume_total: int; palete_codigo: str
    @field_validator("numero_pedido","palete_codigo")
    @classmethod
    def norm(cls, v): return v.strip().upper()

class PedidoVolumeResposta(BaseModel):
    id: int; numero_pedido: str; volume_atual: int; volume_total: int
    palete_codigo: str; endereco_codigo: Optional[str] = None
    class Config:
        from_attributes = True

class DeletarVolumes(BaseModel):
    ids: list[int]

class TransferirVolumes(BaseModel):
    ids: list[int]; novo_palete: str; novo_endereco: str
    @field_validator("novo_palete","novo_endereco")
    @classmethod
    def norm(cls, v): return v.strip().upper()

class LoginInput(BaseModel):
    login: str; senha: str

class LoginResposta(BaseModel):
    token: str; nome: str; login: str; papel: str = "OPERADOR"

class UsuarioCriar(BaseModel):
    nome: str; login: str; senha: str; papel: str = "OPERADOR"
    email: Optional[str] = None; telefone: Optional[str] = None; cpf: Optional[str] = None
    @field_validator("papel")
    @classmethod
    def valida_papel(cls, v):
        v = (v or "OPERADOR").strip().upper()
        if v not in ("ADMIN","OPERADOR"):
            raise ValueError("Papel inválido")
        return v

class UsuarioResposta(BaseModel):
    id: int; nome: str; login: str; ativo: int; papel: str = "OPERADOR"
    class Config:
        from_attributes = True

class PerfilResposta(BaseModel):
    id: int; nome: str; login: str; papel: str
    email: Optional[str] = None; telefone: Optional[str] = None
    cpf_mascarado: Optional[str] = None; foto_url: Optional[str] = None; ativo: int

class PerfilAtualizar(BaseModel):
    nome: Optional[str] = None; email: Optional[str] = None
    telefone: Optional[str] = None; cpf: Optional[str] = None; foto_url: Optional[str] = None
    @field_validator("email")
    @classmethod
    def valida_email(cls, v):
        if v and "@" not in v: raise ValueError("E-mail inválido")
        return v
    @field_validator("cpf")
    @classmethod
    def valida_cpf(cls, v):
        if v:
            d = "".join(c for c in v if c.isdigit())
            if len(d) != 11: raise ValueError("CPF deve ter 11 dígitos")
            return d
        return v

class HistoricoResposta(BaseModel):
    id: int; usuario_nome: Optional[str] = None; acao: str
    numero_pedido: Optional[str] = None; volume_atual: Optional[int] = None
    volume_total: Optional[int] = None; palete_codigo: Optional[str] = None
    endereco_de: Optional[str] = None; endereco_para: Optional[str] = None
    detalhe_extra: Optional[str] = None; criado_em: Optional[str] = None
    class Config:
        from_attributes = True