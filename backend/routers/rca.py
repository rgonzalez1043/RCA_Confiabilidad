"""
Endpoints para gestión de RCAs
"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List, Optional

from database import get_db
import schemas
import crud

router = APIRouter(prefix="/rca", tags=["RCA"])

@router.post("", response_model=schemas.RCAResponse, status_code=201)
def crear_rca(rca: schemas.RCACreate, db: Session = Depends(get_db)):
    """Crear nuevo RCA"""
    # Verificar si código ya existe
    existe = crud.get_rca_by_codigo(db, rca.codigo)
    if existe:
        raise HTTPException(status_code=400, detail="Código RCA ya existe")
    
    return crud.create_rca(db, rca.dict())

@router.get("", response_model=List[schemas.RCAResponse])
def listar_rcas(
    skip: int = 0,
    limit: int = 100,
    estado: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """Listar RCAs con filtros opcionales"""
    return crud.get_rcas(db, skip, limit, estado)

@router.get("/{rca_id}")
def obtener_rca(rca_id: int, db: Session = Depends(get_db)):
    """Obtener RCA por ID"""
    rca = crud.get_rca(db, rca_id)
    if not rca:
        raise HTTPException(status_code=404, detail="RCA no encontrado")
    return rca

@router.put("/{rca_id}")
def actualizar_rca(
    rca_id: int,
    rca_update: schemas.RCAUpdate,
    db: Session = Depends(get_db)
):
    """Actualizar RCA"""
    rca = crud.update_rca(db, rca_id, rca_update.dict(exclude_unset=True))
    if not rca:
        raise HTTPException(status_code=404, detail="RCA no encontrado")
    return rca

@router.delete("/{rca_id}", status_code=204)
def eliminar_rca(rca_id: int, db: Session = Depends(get_db)):
    """Eliminar RCA"""
    if not crud.delete_rca(db, rca_id):
        raise HTTPException(status_code=404, detail="RCA no encontrado")
    return None

@router.post("/{rca_id}/cinco-porques")
def agregar_cinco_porques(
    rca_id: int,
    porques: schemas.CincoPorquesCreate,
    db: Session = Depends(get_db)
):
    """Agregar análisis de 5 porqués"""
    porques.rca_id = rca_id
    return crud.create_cinco_porque(db, porques.dict())

@router.get("/{rca_id}/cinco-porques")
def obtener_cinco_porques(rca_id: int, db: Session = Depends(get_db)):
    """Obtener 5 porqués de un RCA"""
    return crud.get_cinco_porques(db, rca_id)

@router.post("/{rca_id}/ishikawa")
def agregar_ishikawa(
    rca_id: int,
    ishikawa: schemas.IshikawaCreate,
    db: Session = Depends(get_db)
):
    """Agregar causa al diagrama Ishikawa"""
    ishikawa.rca_id = rca_id
    return crud.create_ishikawa(db, ishikawa.dict())

@router.get("/{rca_id}/ishikawa")
def obtener_ishikawa(rca_id: int, db: Session = Depends(get_db)):
    """Obtener diagrama Ishikawa"""
    return crud.get_ishikawa(db, rca_id)