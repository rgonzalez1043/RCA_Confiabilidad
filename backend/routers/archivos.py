"""
Endpoints para gestión de archivos (fotos, PDFs, evidencias).
"""
import logging
import os
import re
import shutil
from datetime import datetime
from pathlib import Path

from fastapi import APIRouter, Depends, UploadFile, File, Form, HTTPException
from sqlalchemy.orm import Session

from config import config
from database import get_db
from routers.auth import get_current_active_user
import crud
import models

logger = logging.getLogger("rca.archivos")

router = APIRouter(
    prefix="/archivo",
    tags=["Archivos"],
    dependencies=[Depends(get_current_active_user)],  # 🔒 Todo el router requiere auth
)

# Carpeta raíz absoluta de almacenamiento
ARCHIVOS_ROOT = Path(config.ARCHIVOS_PATH).resolve()

# Mapeo extensión -> subcarpeta
_CARPETA_POR_EXT = {
    "jpg": "fotos", "jpeg": "fotos", "png": "fotos", "gif": "fotos", "bmp": "fotos", "webp": "fotos",
    "pdf": "pdfs",
}
_MAX_BYTES = config.MAX_UPLOAD_MB * 1024 * 1024
_SAFE_NAME_RE = re.compile(r"[^A-Za-z0-9._-]+")


def _safe_filename(nombre: str) -> str:
    """Sanitizar nombre de archivo conservando la extensión."""
    nombre = os.path.basename(nombre or "")
    nombre = _SAFE_NAME_RE.sub("_", nombre).strip("._")
    return nombre or "archivo"


@router.post("/upload")
async def subir_archivo(
    rca_id: int = Form(...),
    tipo_contenido: str = Form(None),
    subido_por: str = Form(None),
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
):
    """Subir un archivo (foto, PDF, evidencia) asociado a un RCA."""
    # 1) Validar RCA
    if not crud.get_rca(db, rca_id):
        raise HTTPException(status_code=404, detail="RCA no encontrado")

    # 2) Validar extensión
    ext = (file.filename or "").rsplit(".", 1)[-1].lower() if "." in (file.filename or "") else ""
    if ext not in config.ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=400,
            detail=f"Extensión '.{ext}' no permitida. Permitidas: {', '.join(sorted(config.ALLOWED_EXTENSIONS))}",
        )

    carpeta = _CARPETA_POR_EXT.get(ext, "evidencias")
    destino_dir = ARCHIVOS_ROOT / carpeta
    destino_dir.mkdir(parents=True, exist_ok=True)

    # 3) Nombre único y seguro
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    nombre_seguro = _safe_filename(file.filename)
    nombre_archivo = f"{rca_id}_{timestamp}_{nombre_seguro}"
    ruta_absoluta = destino_dir / nombre_archivo

    # 4) Guardar con límite de tamaño (evita llenar el disco con archivos enormes)
    recibidos = 0
    with open(ruta_absoluta, "wb") as buffer:
        while True:
            chunk = await file.read(1024 * 1024)  # 1 MB por chunk
            if not chunk:
                break
            recibidos += len(chunk)
            if recibidos > _MAX_BYTES:
                buffer.close()
                ruta_absoluta.unlink(missing_ok=True)
                raise HTTPException(
                    status_code=413,
                    detail=f"El archivo supera el máximo permitido ({config.MAX_UPLOAD_MB} MB)",
                )
            buffer.write(chunk)

    # 5) Ruta relativa para la BD y para exponer al cliente (no exponer ruta absoluta)
    ruta_relativa = f"{carpeta}/{nombre_archivo}"

    tamanio_kb = max(1, ruta_absoluta.stat().st_size // 1024)
    archivo_data = {
        "rca_id": rca_id,
        "nombre_archivo": file.filename or nombre_archivo,
        "ruta_archivo": ruta_relativa,
        "tipo_archivo": ext,
        "tipo_contenido": tipo_contenido,
        "tamanio_kb": tamanio_kb,
        "subido_por": subido_por,
    }
    db_archivo = crud.create_archivo(db, archivo_data)

    logger.info("Archivo subido rca_id=%s ruta=%s (%s KB)", rca_id, ruta_relativa, tamanio_kb)

    return {
        "id": db_archivo.id,
        "nombre": file.filename,
        "ruta": ruta_relativa,                       # relativa, para usar con /archivos/...
        "url": f"/archivos/{ruta_relativa}",         # lista para el cliente
        "tamanio_kb": tamanio_kb,
        "tipo": ext,
    }


@router.get("/{rca_id}")
def listar_archivos(rca_id: int, db: Session = Depends(get_db)):
    """Listar archivos de un RCA."""
    if not crud.get_rca(db, rca_id):
        raise HTTPException(status_code=404, detail="RCA no encontrado")

    archivos = crud.get_archivos_rca(db, rca_id)
    # Enriquecer con URL pública y añadir nombre de subidor
    resultado = []
    for a in archivos:
        resultado.append(
            {
                "id": a.id,
                "nombre_archivo": a.nombre_archivo,
                "ruta": a.ruta_archivo,
                "url": f"/archivos/{a.ruta_archivo}",
                "tipo_archivo": a.tipo_archivo,
                "tipo_contenido": a.tipo_contenido,
                "tamanio_kb": a.tamanio_kb,
                "fecha_subida": a.fecha_subida.isoformat() if a.fecha_subida else None,
                "subido_por": a.subido_por,
            }
        )
    return resultado