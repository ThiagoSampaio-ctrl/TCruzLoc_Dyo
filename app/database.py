import os
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker, declarative_base

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
Base = declarative_base()

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
