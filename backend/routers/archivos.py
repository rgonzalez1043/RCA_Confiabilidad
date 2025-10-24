"""
Endpoints para gestión de archivos
"""
from fastapi import APIRouter, Depends, UploadFile, File, Form, HTTPException
from sqlalchemy.orm import Session
import os
import shutil
from datetime import datetime

from database import get_db
from config import config
import crud

router = APIRouter(prefix="/archivo", tags=["Archivos"])

@router.post("/upload")
async def subir_archivo(
    rca_id: int = Form(...),
    tipo_contenido: str = Form(None),
    subido_por: str = Form(None),
    file: UploadFile = File(...),
    db: Session = Depends(get_db)
):
    """Subir archivo (foto, PDF, etc.)"""
    # Verificar que el RCA existe
    if not crud.get_rca(db, rca_id):
        raise HTTPException(status_code=404, detail="RCA no encontrado")
    
    # Determinar carpeta según tipo de archivo
    ext = file.filename.split('.')[-1].lower()
    if ext in ['jpg', 'jpeg', 'png', 'gif']:
        carpeta = 'fotos'
    elif ext == 'pdf':
        carpeta = 'pdfs'
    else:
        carpeta = 'evidencias'
    
    # Crear nombre único
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    nombre_archivo = f"{rca_id}_{timestamp}_{file.filename}"
    ruta_completa = os.path.join(config.ARCHIVOS_PATH, carpeta, nombre_archivo)
    
    # Crear directorio si no existe
    os.makedirs(os.path.dirname(ruta_completa), exist_ok=True)
    
    # Guardar archivo
    with open(ruta_completa, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)
    
    # Registrar en base de datos
    tamanio_kb = os.path.getsize(ruta_completa) // 1024
    archivo_data = {
        "rca_id": rca_id,
        "nombre_archivo": file.filename,
        "ruta_archivo": ruta_completa,
        "tipo_archivo": ext,
        "tipo_contenido": tipo_contenido,
        "tamanio_kb": tamanio_kb,
        "subido_por": subido_por
    }
    
    db_archivo = crud.create_archivo(db, archivo_data)
    
    return {
        "id": db_archivo.id,
        "nombre": file.filename,
        "ruta": ruta_completa,
        "tamanio_kb": tamanio_kb,
        "tipo": ext
    }

@router.get("/{rca_id}")
def listar_archivos(rca_id: int, db: Session = Depends(get_db)):
    """Listar archivos de un RCA"""
    return crud.get_archivos_rca(db, rca_id)