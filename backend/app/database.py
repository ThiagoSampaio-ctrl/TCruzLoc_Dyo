import os
from sqlalchemy import create_engine, text, event
from sqlalchemy.orm import sessionmaker, declarative_base
from sqlalchemy.pool import StaticPool

_url = os.getenv("DATABASE_URL", "sqlite:///./wms.db")
if _url.startswith("postgres://"):
    _url = _url.replace("postgres://", "postgresql://", 1)

_sqlite = _url.startswith("sqlite")

engine = create_engine(
    _url,
    connect_args={"check_same_thread": False} if _sqlite else {},
    **({} if _sqlite else {"pool_pre_ping": True, "pool_size": 5, "max_overflow": 10})
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Base com extend_existing habilitado globalmente — evita erro de MetaData duplicada
# quando múltiplos workers/imports carregam os models
class _Base:
    """Mixin que adiciona extend_existing=True automaticamente a todas as tabelas."""
    @classmethod
    def __init_subclass__(cls, **kwargs):
        super().__init_subclass__(**kwargs)
        if hasattr(cls, '__tablename__') and not hasattr(cls, '__table_args__'):
            cls.__table_args__ = {'extend_existing': True}
        elif hasattr(cls, '__tablename__') and hasattr(cls, '__table_args__'):
            if isinstance(cls.__table_args__, dict):
                cls.__table_args__['extend_existing'] = True

Base = declarative_base(cls=_Base)


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def ping_db() -> bool:
    try:
        with engine.connect() as c:
            c.execute(text("SELECT 1"))
        return True
    except Exception:
        return False