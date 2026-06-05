import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base

DATABASE_URL = os.getenv("DATABASE_URL", "")

if not DATABASE_URL:
    raise RuntimeError(
        "❌ DATABASE_URL não configurada.\n"
        "No Render: vá em Environment > Add Environment Variable\n"
        "Chave: DATABASE_URL\n"
        "Valor: (string de conexão do seu PostgreSQL no Render)"
    )

# Render fornece URLs que começam com postgres:// mas SQLAlchemy 1.4+
# exige postgresql:// — corrigindo automaticamente:
if DATABASE_URL.startswith("postgres://"):
    DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql://", 1)

engine = create_engine(
    DATABASE_URL,
    pool_pre_ping=True,       # reconecta automaticamente se a conexão cair
    pool_size=5,
    max_overflow=10,
)

SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine,
)

Base = declarative_base()