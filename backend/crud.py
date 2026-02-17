"""
Operaciones CRUD reutilizables para todas las tablas
"""
from sqlalchemy.orm import Session
from typing import List, Optional
import models
from datetime import datetime

# ==================== RCAs ====================
def get_rca(db: Session, rca_id: int):
    """Obtener RCA por ID con cinco_porques e ishikawa"""
    rca = db.query(models.RCA).filter(models.RCA.id == rca_id).first()
    return rca

def get_rca_by_codigo(db: Session, codigo: str):
    """Obtener RCA por código"""
    return db.query(models.RCA).filter(models.RCA.codigo == codigo).first()

def get_rcas(db: Session, skip: int = 0, limit: int = 100, estado: Optional[str] = None):
    """Listar RCAs con filtros"""
    query = db.query(models.RCA)
    if estado:
        query = query.filter(models.RCA.estado == estado)
    return query.offset(skip).limit(limit).all()

def create_rca(db: Session, rca_data: dict):
    """Crear nuevo RCA con cinco_porques e ishikawa"""
    # Extraer datos relacionados
    cinco_porques_data = rca_data.pop('cinco_porques', None)
    ishikawa_data = rca_data.pop('ishikawa', None)
    
    # Crear RCA principal (sin cinco_porques e ishikawa)
    db_rca = models.RCA(**rca_data)
    db.add(db_rca)
    db.commit()
    db.refresh(db_rca)
    
    # Guardar cinco_porques
    if cinco_porques_data:
        for nivel, respuesta in enumerate(cinco_porques_data, start=1):
            if respuesta and respuesta.strip():
                cp = models.CincoPorques(
                    rca_id=db_rca.id,
                    nivel=nivel,
                    porque=f"¿Por qué {nivel}?",
                    respuesta=respuesta
                )
                db.add(cp)
    
    # Guardar ishikawa
    if ishikawa_data:
        for categoria, causas in ishikawa_data.items():
            for causa in causas:
                if causa and causa.strip():
                    ish = models.Ishikawa(
                        rca_id=db_rca.id,
                        categoria=categoria,
                        causa=causa
                    )
                    db.add(ish)
    
    db.commit()
    db.refresh(db_rca)
    return db_rca

def update_rca(db: Session, rca_id: int, update_data: dict):
    """Actualizar RCA con cinco_porques e ishikawa"""
    rca = get_rca(db, rca_id)
    if not rca:
        return None
    
    # Extraer datos relacionados
    cinco_porques_data = update_data.pop('cinco_porques', None)
    ishikawa_data = update_data.pop('ishikawa', None)
    
    # Actualizar campos principales del RCA
    for key, value in update_data.items():
        if key == 'fecha_compromiso':
            print(f"🔄 Actualizando fecha_compromiso: {value}")
        setattr(rca, key, value)
    
    # Si se enviaron cinco_porques, reemplazar completamente
    if cinco_porques_data is not None:
        # Eliminar registros anteriores
        db.query(models.CincoPorques).filter(models.CincoPorques.rca_id == rca_id).delete()
        
        # Crear nuevos registros
        for nivel, respuesta in enumerate(cinco_porques_data, start=1):
            if respuesta and respuesta.strip():
                cp = models.CincoPorques(
                    rca_id=rca_id,
                    nivel=nivel,
                    porque=f"¿Por qué {nivel}?",
                    respuesta=respuesta
                )
                db.add(cp)
    
    # Si se enviaron ishikawa, reemplazar completamente
    if ishikawa_data is not None:
        # Eliminar registros anteriores
        db.query(models.Ishikawa).filter(models.Ishikawa.rca_id == rca_id).delete()
        
        # Crear nuevos registros
        for categoria, causas in ishikawa_data.items():
            for causa in causas:
                if causa and causa.strip():
                    ish = models.Ishikawa(
                        rca_id=rca_id,
                        categoria=categoria,
                        causa=causa
                    )
                    db.add(ish)
    
    db.commit()
    db.refresh(rca)
    return rca

def delete_rca(db: Session, rca_id: int):
    """Eliminar RCA"""
    rca = get_rca(db, rca_id)
    if rca:
        db.delete(rca)
        db.commit()
        return True
    return False

# ==================== 5 PORQUÉS ====================
def get_cinco_porques(db: Session, rca_id: int):
    """Obtener 5 porqués de un RCA"""
    return db.query(models.CincoPorques).filter(models.CincoPorques.rca_id == rca_id).all()

def create_cinco_porque(db: Session, porque_data: dict):
    """Crear registro de 5 porqués"""
    db_porque = models.CincoPorques(**porque_data)
    db.add(db_porque)
    db.commit()
    db.refresh(db_porque)
    return db_porque

# ==================== ISHIKAWA ====================
def get_ishikawa(db: Session, rca_id: int):
    """Obtener diagrama Ishikawa de un RCA"""
    return db.query(models.Ishikawa).filter(models.Ishikawa.rca_id == rca_id).all()

def create_ishikawa(db: Session, ishikawa_data: dict):
    """Crear causa en Ishikawa"""
    db_ishikawa = models.Ishikawa(**ishikawa_data)
    db.add(db_ishikawa)
    db.commit()
    db.refresh(db_ishikawa)
    return db_ishikawa

# ==================== ARCHIVOS ====================
def get_archivos_rca(db: Session, rca_id: int):
    """Obtener archivos de un RCA"""
    return db.query(models.Archivo).filter(models.Archivo.rca_id == rca_id).all()

def create_archivo(db: Session, archivo_data: dict):
    """Registrar archivo"""
    db_archivo = models.Archivo(**archivo_data)
    db.add(db_archivo)
    db.commit()
    db.refresh(db_archivo)
    return db_archivo

# ==================== ESTADÍSTICAS ====================
def get_estadisticas(db: Session):
    """Obtener estadísticas generales"""
    total = db.query(models.RCA).count()
    abiertos = db.query(models.RCA).filter(models.RCA.estado == "Abierto").count()
    cerrados = db.query(models.RCA).filter(models.RCA.estado == "Cerrado").count()
    criticos = db.query(models.RCA).filter(models.RCA.criticidad == "Crítica").count()
    
    return {
        "total_rcas": total,
        "abiertos": abiertos,
        "cerrados": cerrados,
        "en_analisis": db.query(models.RCA).filter(models.RCA.estado == "En Análisis").count(),
        "criticos": criticos,
        "tasa_cierre": round(cerrados / total * 100, 2) if total > 0 else 0
    }