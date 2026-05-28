from typing import Optional
from pydantic import BaseModel

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

    class Config:
        from_attributes = True


class CaixaResposta(BaseModel):
    id: int
    nome: str
    comprimento_cm: int
    largura_cm: int
    altura_cm: int
    volume_cm3: int

    class Config:
        from_attributes = True


class PaleteCriar(BaseModel):
    codigo: str
    qtd_k0: int = 0
    qtd_k1: int = 0
    qtd_k2: int = 0
    qtd_k3: int = 0


class PaleteResposta(BaseModel):
    id: int
    codigo: str
    qtd_k0: int
    qtd_k1: int
    qtd_k2: int
    qtd_k3: int
    volume_total: int
    endereco_codigo: str
    status: str

    class Config:
        from_attributes = True


class PedidoVolumeCriar(BaseModel):
    numero_pedido: str
    volume_atual: int
    volume_total: int
    palete_codigo: str


class PedidoVolumeResposta(BaseModel):
    id: int
    numero_pedido: str
    volume_atual: int
    volume_total: int
    palete_codigo: str
    endereco_codigo: Optional[str] = None

    class Config:
        from_attributes = True


class DeletarVolumes(BaseModel):
    ids: list[int]