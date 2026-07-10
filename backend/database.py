"""
Capa de acceso a la base de datos (SQLAlchemy + MySQL).
"""
import logging
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base
from config import config

logger = logging.getLogger("rca.database")

engine = create_engine(
    config.database_url,
    pool_pre_ping=True,   # Detecta conexiones caídas antes de usarlas
    pool_recycle=3600,    # Recicla conexiones cada hora (MySQL cierra wait_timeout)
    pool_size=10,
    max_overflow=20,
    pool_timeout=30,
    echo=False,
    future=True,
)

SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine,
    expire_on_commit=False,
)

Base = declarative_base()


def get_db():
    """Dependency de FastAPI: entrega una sesión y la cierra al terminar."""
    db = SessionLocal()
    try:
        yield db
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()