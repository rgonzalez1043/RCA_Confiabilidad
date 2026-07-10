"""
Endpoints para gestión de RCAs.
"""
import logging
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from database import get_db
from routers.auth import get_current_active_user
import schemas
import crud
import models

logger = logging.getLogger("rca.router")

router = APIRouter(
    prefix="/rca",
    tags=["RCA"],
    dependencies=[Depends(get_current_active_user)],  # 🔒 Todo el router requiere auth
)


def convert_rca_to_response(db_rca: models.RCA) -> schemas.RCAResponse:
    """Convertir un modelo RCA (con relaciones) al schema de respuesta."""
    # 5 porqués -> lista ordenada por nivel
    cinco_porques_list: Optional[List[str]] = None
    if db_rca.cinco_porques_rel:
        cinco_porques_list = [
            cp.respuesta
            for cp in sorted(db_rca.cinco_porques_rel, key=lambda x: x.nivel)
        ]

    # Ishikawa -> dict categoria -> [causas]
    ishikawa_dict: Optional[dict] = None
    if db_rca.ishikawa_rel:
        ishikawa_dict = {}
        for ish in db_rca.ishikawa_rel:
            ishikawa_dict.setdefault(ish.categoria, []).append(ish.causa)

    # Pydantic v2: model_validate en vez de from_orm
    response = schemas.RCAResponse.model_validate(db_rca)
    response.cinco_porques = cinco_porques_list
    response.ishikawa = ishikawa_dict
    return response


@router.post("", response_model=schemas.RCAResponse, status_code=201)
def crear_rca(rca: schemas.RCACreate, db: Session = Depends(get_db)):
    """Crear nuevo RCA."""
    if crud.get_rca_by_codigo(db, rca.codigo):
        raise HTTPException(status_code=400, detail="Código RCA ya existe")

    db_rca = crud.create_rca(db, rca.model_dump())
    return convert_rca_to_response(db_rca)


@router.get("", response_model=List[schemas.RCAResponse])
def listar_rcas(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=500),
    estado: Optional[str] = None,
    area: Optional[str] = None,
    criticidad: Optional[str] = None,
    q: Optional[str] = Query(None, description="Búsqueda libre en código/título/falla"),
    db: Session = Depends(get_db),
):
    """Listar RCAs con filtros opcionales."""
    rcas = crud.get_rcas(db, skip=skip, limit=limit, estado=estado, area=area, criticidad=criticidad, q=q)
    return [convert_rca_to_response(rca) for rca in rcas]


@router.get("/{rca_id}", response_model=schemas.RCAResponse)
def obtener_rca(rca_id: int, db: Session = Depends(get_db)):
    """Obtener RCA por ID."""
    rca = crud.get_rca(db, rca_id)
    if not rca:
        raise HTTPException(status_code=404, detail="RCA no encontrado")
    return convert_rca_to_response(rca)


@router.put("/{rca_id}", response_model=schemas.RCAResponse)
def actualizar_rca(rca_id: int, rca_update: schemas.RCAUpdate, db: Session = Depends(get_db)):
    """Actualizar RCA."""
    update_dict = rca_update.model_dump(exclude_unset=True)
    rca = crud.update_rca(db, rca_id, update_dict)
    if not rca:
        raise HTTPException(status_code=404, detail="RCA no encontrado")
    return convert_rca_to_response(rca)


@router.delete("/{rca_id}", status_code=204)
def eliminar_rca(rca_id: int, db: Session = Depends(get_db)):
    """Eliminar RCA."""
    if not crud.delete_rca(db, rca_id):
        raise HTTPException(status_code=404, detail="RCA no encontrado")
    return None


@router.post("/{rca_id}/cinco-porques")
def agregar_cinco_porques(
    rca_id: int,
    porques: schemas.CincoPorquesCreate,
    db: Session = Depends(get_db),
):
    """Agregar análisis de 5 porqués (registro individual)."""
    if not crud.get_rca(db, rca_id):
        raise HTTPException(status_code=404, detail="RCA no encontrado")
    data = porques.model_dump()
    data["rca_id"] = rca_id
    return crud.create_cinco_porque(db, data)


@router.get("/{rca_id}/cinco-porques")
def obtener_cinco_porques(rca_id: int, db: Session = Depends(get_db)):
    """Obtener 5 porqués de un RCA."""
    if not crud.get_rca(db, rca_id):
        raise HTTPException(status_code=404, detail="RCA no encontrado")
    return crud.get_cinco_porques(db, rca_id)


@router.post("/{rca_id}/ishikawa")
def agregar_ishikawa(
    rca_id: int,
    ishikawa: schemas.IshikawaCreate,
    db: Session = Depends(get_db),
):
    """Agregar causa al diagrama Ishikawa."""
    if not crud.get_rca(db, rca_id):
        raise HTTPException(status_code=404, detail="RCA no encontrado")
    data = ishikawa.model_dump()
    data["rca_id"] = rca_id
    return crud.create_ishikawa(db, data)


@router.get("/{rca_id}/ishikawa")
def obtener_ishikawa(rca_id: int, db: Session = Depends(get_db)):
    """Obtener diagrama Ishikawa."""
    if not crud.get_rca(db, rca_id):
        raise HTTPException(status_code=404, detail="RCA no encontrado")
    return crud.get_ishikawa(db, rca_id)