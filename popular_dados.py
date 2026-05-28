from app.database import SessionLocal, Base, engine
from app.models import Endereco, TipoCaixa

Base.metadata.create_all(bind=engine)

db = SessionLocal()

enderecos = [
    "R07 028 1", "R07 026 1", "R07 024 1", "R07 022 1",
    "R07 020 1", "R07 018 1", "R07 016 1", "R07 014 1",
    "R07 028 1F", "R07 026 1F", "R07 024 1F", "R07 022 1F",
    "R07 020 1F", "R07 018 1F", "R07 016 1F", "R07 014 1F"
]

caixas = [
    {"nome": "K0", "comprimento": 26, "largura": 21, "altura": 12},
    {"nome": "K1", "comprimento": 41, "largura": 32, "altura": 27},
    {"nome": "K2", "comprimento": 33, "largura": 27, "altura": 23},
    {"nome": "K3", "comprimento": 52, "largura": 41, "altura": 43},
]

for codigo in enderecos:
    existe = db.query(Endereco).filter(Endereco.codigo == codigo).first()

    if not existe:
        partes = codigo.split()
        rua = partes[0]
        predio = partes[1]
        andar = partes[2]

        frente = "S" if andar.endswith("F") else "N"

        comprimento = 230
        largura = 100
        altura = 200
        capacidade = comprimento * largura * altura

        novo = Endereco(
            codigo=codigo,
            rua=rua,
            predio=predio,
            andar=andar,
            frente=frente,
            comprimento_cm=comprimento,
            largura_cm=largura,
            altura_cm=altura,
            capacidade_total=capacidade,
            capacidade_usada=0
        )

        db.add(novo)

for caixa in caixas:
    existe = db.query(TipoCaixa).filter(TipoCaixa.nome == caixa["nome"]).first()

    if not existe:
        volume = caixa["comprimento"] * caixa["largura"] * caixa["altura"]

        nova = TipoCaixa(
            nome=caixa["nome"],
            comprimento_cm=caixa["comprimento"],
            largura_cm=caixa["largura"],
            altura_cm=caixa["altura"],
            volume_cm3=volume
        )

        db.add(nova)

db.commit()
db.close()

print("Endereços e caixas cadastrados com sucesso!")