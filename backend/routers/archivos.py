"""Evidencias autenticadas, con cuotas, validación de imagen y nombres únicos."""
import logging
import mimetypes
import warnings
from pathlib import Path
from uuid import uuid4
from PIL import Image, UnidentifiedImageError
from fastapi import APIRouter, Depends, UploadFile, File, Form, HTTPException, Response
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session
from config import config
from database import get_db
from routers.auth import get_current_active_user
from routers.rca import locked_rca
from workflow import require_writable
import crud
import models

logger = logging.getLogger('rca.archivos')
router = APIRouter(prefix='/archivo', tags=['Archivos'], dependencies=[Depends(get_current_active_user)])
legacy_router = APIRouter(prefix='/archivos', tags=['Archivos'], dependencies=[Depends(get_current_active_user)])
ARCHIVOS_ROOT = Path(config.ARCHIVOS_PATH).resolve()
IMAGE_EXTENSIONS = {'jpg', 'jpeg', 'png', 'gif', 'bmp', 'webp'}


def safe_path(relative):
    path = (ARCHIVOS_ROOT / relative).resolve()
    if not path.is_relative_to(ARCHIVOS_ROOT) or path == ARCHIVOS_ROOT:
        raise HTTPException(400, 'Ruta de archivo no válida')
    return path


def serialize(archivo):
    return dict(id=archivo.id, rca_id=archivo.rca_id, nombre_archivo=archivo.nombre_archivo,
        ruta_archivo=archivo.ruta_archivo, ruta=archivo.ruta_archivo,
        url=f'/archivo/{archivo.id}/contenido', tipo_archivo=archivo.tipo_archivo,
        tipo_contenido=archivo.tipo_contenido, tamanio_kb=archivo.tamanio_kb,
        fecha_subida=archivo.fecha_subida, subido_por=archivo.subido_por)


@router.post('/upload', status_code=201)
def subir_archivo(rca_id: int = Form(...), tipo_contenido: str = Form('Evidencia'),
    file: UploadFile = File(...), db: Session = Depends(get_db),
    user: models.Usuario = Depends(get_current_active_user)):
    rca = locked_rca(db, rca_id)
    require_writable(rca, user)
    name = Path((file.filename or 'archivo').replace('\\', '/')).name
    if len(name) > 255 or len(tipo_contenido) > 100:
        raise HTTPException(422, 'Nombre o clasificación del archivo demasiado largo')
    ext = Path(name).suffix.lstrip('.').lower()
    if ext not in config.ALLOWED_EXTENSIONS:
        raise HTTPException(415, 'Tipo de archivo no permitido')
    if ext in IMAGE_EXTENSIONS:
        count = db.query(models.Archivo).filter(models.Archivo.rca_id == rca_id,
            models.Archivo.tipo_archivo.in_(IMAGE_EXTENSIONS | {'imagen'})).count()
        if count >= config.MAX_PHOTOS_PER_RCA:
            raise HTTPException(409, f'Se permiten hasta {config.MAX_PHOTOS_PER_RCA} fotos por RCA')
    folder = 'fotos' if ext in IMAGE_EXTENSIONS else 'pdfs' if ext == 'pdf' else 'evidencias'
    relative = f'{folder}/{uuid4().hex}.{ext}'
    destination = safe_path(relative)
    destination.parent.mkdir(parents=True, exist_ok=True)
    received = 0
    try:
        with destination.open('xb') as target:
            while True:
                chunk = file.file.read(1024 * 1024)
                if not chunk:
                    break
                received += len(chunk)
                if received > config.MAX_UPLOAD_MB * 1024 * 1024:
                    raise HTTPException(413, f'El archivo supera {config.MAX_UPLOAD_MB} MB')
                target.write(chunk)
        if not received:
            raise HTTPException(422, 'El archivo está vacío')
        if ext in IMAGE_EXTENSIONS:
            try:
                with warnings.catch_warnings():
                    warnings.simplefilter('error', Image.DecompressionBombWarning)
                    with Image.open(destination) as image:
                        expected = 'JPEG' if ext in ('jpg', 'jpeg') else ext.upper()
                        if image.format != expected:
                            raise ValueError('Formato distinto de la extensión')
                        image.verify()
            except (UnidentifiedImageError, OSError, ValueError, Image.DecompressionBombError, Image.DecompressionBombWarning):
                raise HTTPException(415, 'El contenido no es una imagen válida del tipo indicado')
        archivo = models.Archivo(rca_id=rca_id, nombre_archivo=name,
            ruta_archivo=relative, tipo_archivo=ext, tipo_contenido=tipo_contenido,
            tamanio_kb=max(1, (received + 1023) // 1024),
            subido_por=user.nombre_completo or user.nombre_usuario)
        db.add(archivo)
        db.commit()
        db.refresh(archivo)
        return serialize(archivo)
    except Exception:
        db.rollback()
        destination.unlink(missing_ok=True)
        raise
    finally:
        file.file.close()


@router.get('/{rca_id}')
def listar_archivos(rca_id: int, db: Session = Depends(get_db)):
    if not crud.get_rca(db, rca_id):
        raise HTTPException(404, 'RCA no encontrado')
    return [serialize(item) for item in crud.get_archivos_rca(db, rca_id)]


def download(archivo):
    path = safe_path(archivo.ruta_archivo)
    if not path.is_file():
        raise HTTPException(404, 'Archivo no encontrado')
    return FileResponse(str(path), filename=archivo.nombre_archivo,
        media_type=mimetypes.guess_type(archivo.nombre_archivo)[0] or 'application/octet-stream',
        headers={'Cache-Control': 'private, no-store', 'X-Content-Type-Options': 'nosniff'})


@router.get('/{archivo_id}/contenido')
def descargar_archivo(archivo_id: int, db: Session = Depends(get_db)):
    archivo = db.query(models.Archivo).filter_by(id=archivo_id).first()
    if not archivo:
        raise HTTPException(404, 'Archivo no encontrado')
    return download(archivo)


@legacy_router.get('/{relative:path}')
def descargar_ruta_legacy(relative: str, db: Session = Depends(get_db)):
    safe_path(relative)
    archivo = db.query(models.Archivo).filter_by(ruta_archivo=relative).first()
    if not archivo:
        raise HTTPException(404, 'Archivo no encontrado')
    return download(archivo)


@router.delete('/{archivo_id}', status_code=204)
def eliminar_archivo(archivo_id: int, db: Session = Depends(get_db),
    user: models.Usuario = Depends(get_current_active_user)):
    archivo = db.query(models.Archivo).filter_by(id=archivo_id).first()
    if not archivo:
        raise HTTPException(404, 'Archivo no encontrado')
    rca = locked_rca(db, archivo.rca_id)
    require_writable(rca, user)
    # Revalidar después de adquirir el bloqueo compartido por todas las escrituras.
    archivo = db.query(models.Archivo).filter_by(id=archivo_id).populate_existing().first()
    if not archivo:
        raise HTTPException(404, 'Archivo no encontrado')
    path = safe_path(archivo.ruta_archivo)
    db.delete(archivo)
    db.commit()
    try:
        path.unlink(missing_ok=True)
    except OSError:
        # Sin registro, la ruta tampoco es accesible mediante la API.
        logger.exception('Pendiente de limpieza física archivo_id=%s', archivo_id)
    return Response(status_code=204)