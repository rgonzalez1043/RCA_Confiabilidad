"""
Capa de acceso a la base de datos (SQLAlchemy + MySQL).
"""
import logging
import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base
from sqlalchemy.pool import StaticPool
from config import config

logger = logging.getLogger("rca.database")

if os.getenv("RCA_TESTING") == "1":
    engine = create_engine("sqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool)
else:
    engine = create_engine(config.database_url, pool_pre_ping=True,
        pool_recycle=3600, pool_size=10, max_overflow=20, pool_timeout=30,
        isolation_level="READ COMMITTED", echo=False)

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
