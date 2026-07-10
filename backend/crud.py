"""
Operaciones CRUD reutilizables para todas las tablas.
"""
import logging
from datetime import datetime
from typing import List, Optional

from sqlalchemy.orm import Session

import models

logger = logging.getLogger("rca.crud")


# ==================== RCAs ====================
def get_rca(db: Session, rca_id: int):
    """Obtener RCA por ID (incluye relaciones por lazy/eager según el schema)."""
    return db.query(models.RCA).filter(models.RCA.id == rca_id).first()


def get_rca_by_codigo(db: Session, codigo: str):
    """Obtener RCA por código único."""
    return db.query(models.RCA).filter(models.RCA.codigo == codigo).first()


def get_rcas(
    db: Session,
    skip: int = 0,
    limit: int = 100,
    estado: Optional[str] = None,
    area: Optional[str] = None,
    criticidad: Optional[str] = None,
    q: Optional[str] = None,
):
    """Listar RCAs con filtros opcionales y orden determinista."""
    query = db.query(models.RCA)
    if estado:
        query = query.filter(models.RCA.estado == estado)
    if area:
        query = query.filter(models.RCA.area == area)
    if criticidad:
        query = query.filter(models.RCA.criticidad == criticidad)
    if q:
        like = f"%{q}%"
        query = query.filter(
            (models.RCA.codigo.ilike(like))
            | (models.RCA.titulo.ilike(like))
            | (models.RCA.descripcion_falla.ilike(like))
        )
    return query.order_by(models.RCA.fecha_creacion.desc()).offset(skip).limit(limit).all()


def create_rca(db: Session, rca_data: dict):
    """Crear nuevo RCA con cinco_porques e ishikawa (transaccional)."""
    cinco_porques_data = rca_data.pop("cinco_porques", None)
    ishikawa_data = rca_data.pop("ishikawa", None)

    db_rca = models.RCA(**rca_data)
    db.add(db_rca)
    db.flush()  # necesitamos el ID sin hacer commit todavía

    _upsert_cinco_porques(db, db_rca.id, cinco_porques_data)
    _upsert_ishikawa(db, db_rca.id, ishikawa_data)

    db.commit()
    db.refresh(db_rca)
    logger.info("RCA creado id=%s codigo=%s", db_rca.id, db_rca.codigo)
    return db_rca


def update_rca(db: Session, rca_id: int, update_data: dict):
    """Actualizar RCA (campos simples + reemplazo de 5 porqués / Ishikawa)."""
    rca = get_rca(db, rca_id)
    if not rca:
        return None

    cinco_porques_data = update_data.pop("cinco_porques", None)
    ishikawa_data = update_data.pop("ishikawa", None)

    for key, value in update_data.items():
        setattr(rca, key, value)

    if cinco_porques_data is not None:
        _upsert_cinco_porques(db, rca_id, cinco_porques_data)

    if ishikawa_data is not None:
        _upsert_ishikawa(db, rca_id, ishikawa_data)

    db.commit()
    db.refresh(rca)
    logger.info("RCA actualizado id=%s campos=%s", rca_id, list(update_data.keys()))
    return rca


def delete_rca(db: Session, rca_id: int) -> bool:
    """Eliminar RCA por ID."""
    rca = get_rca(db, rca_id)
    if rca:
        db.delete(rca)
        db.commit()
        logger.info("RCA eliminado id=%s", rca_id)
        return True
    return False


# ==================== 5 PORQUÉS ====================
def get_cinco_porques(db: Session, rca_id: int):
    return (
        db.query(models.CincoPorques)
        .filter(models.CincoPorques.rca_id == rca_id)
        .order_by(models.CincoPorques.nivel.asc())
        .all()
    )


def create_cinco_porque(db: Session, porque_data: dict):
    db_porque = models.CincoPorques(**porque_data)
    db.add(db_porque)
    db.commit()
    db.refresh(db_porque)
    return db_porque


# ==================== ISHIKAWA ====================
def get_ishikawa(db: Session, rca_id: int):
    return (
        db.query(models.Ishikawa)
        .filter(models.Ishikawa.rca_id == rca_id)
        .order_by(models.Ishikawa.id.asc())
        .all()
    )


def create_ishikawa(db: Session, ishikawa_data: dict):
    db_ishikawa = models.Ishikawa(**ishikawa_data)
    db.add(db_ishikawa)
    db.commit()
    db.refresh(db_ishikawa)
    return db_ishikawa


# ==================== ARCHIVOS ====================
def get_archivos_rca(db: Session, rca_id: int):
    return (
        db.query(models.Archivo)
        .filter(models.Archivo.rca_id == rca_id)
        .order_by(models.Archivo.fecha_subida.desc())
        .all()
    )


def create_archivo(db: Session, archivo_data: dict):
    db_archivo = models.Archivo(**archivo_data)
    db.add(db_archivo)
    db.commit()
    db.refresh(db_archivo)
    return db_archivo


# ==================== ESTADÍSTICAS ====================
def get_estadisticas(db: Session):
    total = db.query(models.RCA).count()
    abiertos = db.query(models.RCA).filter(models.RCA.estado == "Abierto").count()
    cerrados = db.query(models.RCA).filter(models.RCA.estado == "Cerrado").count()
    en_analisis = db.query(models.RCA).filter(models.RCA.estado == "En Análisis").count()
    criticos = db.query(models.RCA).filter(models.RCA.criticidad == "Crítica").count()

    return {
        "total_rcas": total,
        "abiertos": abiertos,
        "cerrados": cerrados,
        "en_analisis": en_analisis,
        "criticos": criticos,
        "tasa_cierre": round(cerrados / total * 100, 2) if total > 0 else 0,
    }


# ==================== Helpers internos ====================
def _upsert_cinco_porques(db: Session, rca_id: int, cinco_porques_data: Optional[List[str]]):
    """Reemplazar completamente los 5 porqués de un RCA."""
    db.query(models.CincoPorques).filter(models.CincoPorques.rca_id == rca_id).delete()
    if cinco_porques_data:
        for nivel, respuesta in enumerate(cinco_porques_data, start=1):
            if respuesta and str(respuesta).strip():
                db.add(
                    models.CincoPorques(
                        rca_id=rca_id,
                        nivel=nivel,
                        porque=f"¿Por qué {nivel}?",
                        respuesta=str(respuesta).strip(),
                    )
                )


def _upsert_ishikawa(db: Session, rca_id: int, ishikawa_data: Optional[dict]):
    """Reemplazar completamente el Ishikawa de un RCA."""
    db.query(models.Ishikawa).filter(models.Ishikawa.rca_id == rca_id).delete()
    if ishikawa_data:
        for categoria, causas in ishikawa_data.items():
            for causa in causas or []:
                if causa and str(causa).strip():
                    db.add(
                        models.Ishikawa(
                            rca_id=rca_id,
                            categoria=str(categoria),
                            causa=str(causa).strip(),
                        )
                    )