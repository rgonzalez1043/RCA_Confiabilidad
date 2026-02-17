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

def convert_rca_to_response(db_rca):
    """Convertir RCA con relaciones a formato JSON"""
    # Convertir cinco_porques a lista
    cinco_porques_list = None
    if hasattr(db_rca, 'cinco_porques_rel') and db_rca.cinco_porques_rel:
        cinco_porques_list = [cp.respuesta for cp in sorted(db_rca.cinco_porques_rel, key=lambda x: x.nivel)]
    
    # Convertir ishikawa a diccionario
    ishikawa_dict = None
    if hasattr(db_rca, 'ishikawa_rel') and db_rca.ishikawa_rel:
        ishikawa_dict = {}
        for ish in db_rca.ishikawa_rel:
            if ish.categoria not in ishikawa_dict:
                ishikawa_dict[ish.categoria] = []
            ishikawa_dict[ish.categoria].append(ish.causa)
    
    # Crear respuesta
    response = schemas.RCAResponse.from_orm(db_rca)
    response.cinco_porques = cinco_porques_list
    response.ishikawa = ishikawa_dict
    return response

@router.post("", response_model=schemas.RCAResponse, status_code=201)
def crear_rca(rca: schemas.RCACreate, db: Session = Depends(get_db)):
    """Crear nuevo RCA"""
    # Verificar si código ya existe
    existe = crud.get_rca_by_codigo(db, rca.codigo)
    if existe:
        raise HTTPException(status_code=400, detail="Código RCA ya existe")
    
    db_rca = crud.create_rca(db, rca.dict())
    return convert_rca_to_response(db_rca)

@router.get("", response_model=List[schemas.RCAResponse])
def listar_rcas(
    skip: int = 0,
    limit: int = 100,
    estado: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """Listar RCAs con filtros opcionales"""
    rcas = crud.get_rcas(db, skip, limit, estado)
    return [convert_rca_to_response(rca) for rca in rcas]

@router.get("/{rca_id}", response_model=schemas.RCAResponse)
def obtener_rca(rca_id: int, db: Session = Depends(get_db)):
    """Obtener RCA por ID"""
    rca = crud.get_rca(db, rca_id)
    if not rca:
        raise HTTPException(status_code=404, detail="RCA no encontrado")
    return convert_rca_to_response(rca)

@router.put("/{rca_id}", response_model=schemas.RCAResponse)
def actualizar_rca(
    rca_id: int,
    rca_update: schemas.RCAUpdate,
    db: Session = Depends(get_db)
):
    """Actualizar RCA"""
    update_dict = rca_update.dict(exclude_unset=True)
    
    # Debug: Ver qué campos se están actualizando
    print(f"\n🔧 UPDATE RCA {rca_id}")
    print(f"📋 Campos recibidos: {list(update_dict.keys())}")
    if 'fecha_compromiso' in update_dict:
        print(f"📅 fecha_compromiso: {update_dict['fecha_compromiso']}")
    else:
        print(f"⚠️ fecha_compromiso NO está en el request")
    
    rca = crud.update_rca(db, rca_id, update_dict)
    if not rca:
        raise HTTPException(status_code=404, detail="RCA no encontrado")
    return convert_rca_to_response(rca)

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