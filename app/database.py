import os
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker, declarative_base

# ── Lê a variável de ambiente ──────────────────────────────────────────────
# No Render: Environment → Add Environment Variable → DATABASE_URL = <postgres url>
# Localmente: cria um arquivo .env com DATABASE_URL=sqlite:///./wms.db
_url = os.getenv("DATABASE_URL", "sqlite:///./wms.db")

# O Render às vezes entrega "postgres://" — SQLAlchemy 1.4+ exige "postgresql://"
if _url.startswith("postgres://"):
    _url = _url.replace("postgres://", "postgresql://", 1)

_is_sqlite = _url.startswith("sqlite")

# ── Engine ─────────────────────────────────────────────────────────────────
engine = create_engine(
    _url,
    # SQLite precisa deste argumento; PostgreSQL NÃO aceita — separamos:
    connect_args={"check_same_thread": False} if _is_sqlite else {},
    # PostgreSQL: pool saudável com reconexão automática
    **({} if _is_sqlite else {
        "pool_pre_ping": True,   # testa conexão antes de usar
        "pool_size": 5,
        "max_overflow": 10,
    })
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


def get_db():
    """Dependency para FastAPI — garante fechamento mesmo em exceções."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def ping_db() -> bool:
    """Verifica se o banco está respondendo. Usado na rota /health."""
    try:
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        return True
    except Exception:
        return False

