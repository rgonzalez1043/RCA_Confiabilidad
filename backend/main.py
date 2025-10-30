from fastapi import FastAPI, HTTPException, Depends, UploadFile, File, Form
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from datetime import datetime
from typing import List, Optional
import shutil
import os
from pathlib import Path

# Imports de la base de datos
from database import SessionLocal, engine, Base, get_db
import models
import schemas
from config import config

# Crear tablas si no existen
Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="RCA API - Sistema de Análisis de Causa Raíz",
    version="1.0.0",
    description="API para gestión de RCA en operaciones industriales"
)

# CORS - permitir conexiones desde tablets
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
# Incluir routers
from routers import auth, rca

app.include_router(auth.router)
app.include_router(rca.router)
#app.include_router(archivos.router)
#app.include_router(reportes.router)

# ==================== ROOT ====================
@app.get("/")
def root():
    return {
        "api": "RCA Sistema",
        "version": "1.0.0",
        "status": "online",
        "servidor": f"{config.SERVER_HOST}:{config.SERVER_PORT}"
    }

@app.get("/health")
def health_check(db: Session = Depends(get_db)):
    try:
        db.execute("SELECT 1")
        return {"status": "healthy", "database": "connected"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")

# ==================== RCAs ====================
@app.post("/rca", response_model=schemas.RCAResponse, status_code=201)
def crear_rca(rca: schemas.RCACreate, db: Session = Depends(get_db)):
    """Crear nuevo RCA"""
    # Verificar si el código ya existe
    existe = db.query(models.RCA).filter(models.RCA.codigo == rca.codigo).first()
    if existe:
        raise HTTPException(status_code=400, detail="Código RCA ya existe")
    
    db_rca = models.RCA(**rca.dict())
    db.add(db_rca)
    db.commit()
    db.refresh(db_rca)
    return db_rca

@app.get("/rca", response_model=List[schemas.RCAResponse])
def listar_rcas(
    skip: int = 0,
    limit: int = 100,
    estado: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """Listar RCAs con filtros opcionales"""
    query = db.query(models.RCA)
    
    if estado:
        query = query.filter(models.RCA.estado == estado)
    
    rcas = query.offset(skip).limit(limit).all()
    return rcas

@app.get("/rca/{rca_id}")
def obtener_rca(rca_id: int, db: Session = Depends(get_db)):
    """Obtener RCA por ID con todos sus detalles"""
    rca = db.query(models.RCA).filter(models.RCA.id == rca_id).first()
    if not rca:
        raise HTTPException(status_code=404, detail="RCA no encontrado")
    return rca

@app.put("/rca/{rca_id}")
def actualizar_rca(rca_id: int, rca_update: schemas.RCAUpdate, db: Session = Depends(get_db)):
    """Actualizar RCA existente"""
    rca = db.query(models.RCA).filter(models.RCA.id == rca_id).first()
    if not rca:
        raise HTTPException(status_code=404, detail="RCA no encontrado")
    
    update_data = rca_update.dict(exclude_unset=True)
    for key, value in update_data.items():
        setattr(rca, key, value)
    
    db.commit()
    db.refresh(rca)
    return rca

@app.delete("/rca/{rca_id}", status_code=204)
def eliminar_rca(rca_id: int, db: Session = Depends(get_db)):
    """Eliminar RCA"""
    rca = db.query(models.RCA).filter(models.RCA.id == rca_id).first()
    if not rca:
        raise HTTPException(status_code=404, detail="RCA no encontrado")
    
    db.delete(rca)
    db.commit()
    return None

# ==================== 5 PORQUÉS ====================
@app.post("/cinco-porques")
def crear_cinco_porques(porques: schemas.CincoPorquesCreate, db: Session = Depends(get_db)):
    """Agregar análisis de 5 porqués"""
    db_porques = models.CincoPorques(**porques.dict())
    db.add(db_porques)
    db.commit()
    db.refresh(db_porques)
    return db_porques

@app.get("/cinco-porques/{rca_id}")
def obtener_cinco_porques(rca_id: int, db: Session = Depends(get_db)):
    """Obtener 5 porqués de un RCA"""
    porques = db.query(models.CincoPorques).filter(models.CincoPorques.rca_id == rca_id).all()
    return porques

# ==================== ISHIKAWA ====================
@app.post("/ishikawa")
def crear_ishikawa(ishikawa: schemas.IshikawaCreate, db: Session = Depends(get_db)):
    """Agregar causa al diagrama Ishikawa"""
    db_ishikawa = models.Ishikawa(**ishikawa.dict())
    db.add(db_ishikawa)
    db.commit()
    db.refresh(db_ishikawa)
    return db_ishikawa

@app.get("/ishikawa/{rca_id}")
def obtener_ishikawa(rca_id: int, db: Session = Depends(get_db)):
    """Obtener diagrama Ishikawa de un RCA"""
    ishikawa = db.query(models.Ishikawa).filter(models.Ishikawa.rca_id == rca_id).all()
    return ishikawa

# ==================== ARCHIVOS ====================
@app.post("/archivo/upload")
async def subir_archivo(
    rca_id: int = Form(...),
    tipo_contenido: str = Form(None),
    subido_por: str = Form(None),
    file: UploadFile = File(...),
    db: Session = Depends(get_db)
):
    """Subir archivo (foto, PDF, etc.)"""
    # Determinar carpeta según tipo de archivo
    ext = file.filename.split('.')[-1].lower()
    if ext in ['jpg', 'jpeg', 'png']:
        carpeta = 'fotos'
    elif ext == 'pdf':
        carpeta = 'pdfs'
    else:
        carpeta = 'evidencias'
    
    # Crear nombre único
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    nombre_archivo = f"{rca_id}_{timestamp}_{file.filename}"
    ruta_completa = os.path.join(config.ARCHIVOS_PATH, carpeta, nombre_archivo)
    
    # Guardar archivo
    os.makedirs(os.path.dirname(ruta_completa), exist_ok=True)
    with open(ruta_completa, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)
    
    # Registrar en base de datos
    tamanio_kb = os.path.getsize(ruta_completa) // 1024
    db_archivo = models.Archivo(
        rca_id=rca_id,
        nombre_archivo=file.filename,
        ruta_archivo=ruta_completa,
        tipo_archivo=ext,
        tipo_contenido=tipo_contenido,
        tamanio_kb=tamanio_kb,
        subido_por=subido_por
    )
    db.add(db_archivo)
    db.commit()
    
    # Generar URL relativa para acceder al archivo
    ruta_relativa = ruta_completa.replace(config.ARCHIVOS_PATH, "").replace("\\", "/")
    if ruta_relativa.startswith("/"):
        ruta_relativa = ruta_relativa[1:]
    
    return {
        "id": db_archivo.id,
        "nombre": file.filename,
        "ruta": ruta_completa,
        "url": f"/archivos/{ruta_relativa}",  # URL para mostrar en frontend
        "tamanio_kb": tamanio_kb,
        "tipo": ext
    }

@app.get("/archivo")
def listar_archivos_query(rca_id: int, db: Session = Depends(get_db)):
    """Listar archivos de un RCA usando query parameter"""
    archivos = db.query(models.Archivo).filter(models.Archivo.rca_id == rca_id).all()
    
    # Convertir a lista con URLs para el frontend
    resultado = []
    for archivo in archivos:
        # Generar URL relativa desde la ruta completa
        ruta_relativa = archivo.ruta_archivo.replace(config.ARCHIVOS_PATH, "").replace("\\", "/")
        if ruta_relativa.startswith("/"):
            ruta_relativa = ruta_relativa[1:]
        
        resultado.append({
            "id": archivo.id,
            "rca_id": archivo.rca_id,
            "nombre_archivo": archivo.nombre_archivo,
            "ruta_archivo": archivo.ruta_archivo,
            "url": f"/archivos/{ruta_relativa}",  # URL para mostrar imagen
            "tipo_archivo": archivo.tipo_archivo,
            "tipo_contenido": archivo.tipo_contenido,
            "tamanio_kb": archivo.tamanio_kb,
            "fecha_subida": archivo.fecha_subida,
            "subido_por": archivo.subido_por
        })
    
    return resultado

@app.get("/archivo/{rca_id}")
def listar_archivos_path(rca_id: int, db: Session = Depends(get_db)):
    """Listar archivos de un RCA usando path parameter"""
    archivos = db.query(models.Archivo).filter(models.Archivo.rca_id == rca_id).all()
    
    # Convertir a lista con URLs para el frontend
    resultado = []
    for archivo in archivos:
        # Generar URL relativa desde la ruta completa
        ruta_relativa = archivo.ruta_archivo.replace(config.ARCHIVOS_PATH, "").replace("\\", "/")
        if ruta_relativa.startswith("/"):
            ruta_relativa = ruta_relativa[1:]
        
        resultado.append({
            "id": archivo.id,
            "rca_id": archivo.rca_id,
            "nombre_archivo": archivo.nombre_archivo,
            "ruta_archivo": archivo.ruta_archivo,
            "url": f"/archivos/{ruta_relativa}",  # URL para mostrar imagen
            "tipo_archivo": archivo.tipo_archivo,
            "tipo_contenido": archivo.tipo_contenido,
            "tamanio_kb": archivo.tamanio_kb,
            "fecha_subida": archivo.fecha_subida,
            "subido_por": archivo.subido_por
        })
    
    return resultado

@app.delete("/archivo/{archivo_id}", status_code=204)
def eliminar_archivo(archivo_id: int, db: Session = Depends(get_db)):
    """Eliminar archivo y su registro de la base de datos"""
    # Buscar el archivo en la base de datos
    archivo = db.query(models.Archivo).filter(models.Archivo.id == archivo_id).first()
    
    if not archivo:
        raise HTTPException(status_code=404, detail="Archivo no encontrado")
    
    # Eliminar archivo físico del disco
    try:
        if os.path.exists(archivo.ruta_archivo):
            os.remove(archivo.ruta_archivo)
            print(f" Archivo físico eliminado: {archivo.ruta_archivo}")
        else:
            print(f" Archivo físico no existe: {archivo.ruta_archivo}")
    except Exception as e:
        print(f" Error al eliminar archivo físico: {e}")
        # Continuar para eliminar el registro de la BD de todas formas
    
    # Eliminar registro de la base de datos
    db.delete(archivo)
    db.commit()
    
    print(f" Registro eliminado de BD: ID {archivo_id}")
    return None

# ==================== ESTADÍSTICAS ====================
@app.get("/estadisticas/resumen")
def obtener_estadisticas(db: Session = Depends(get_db)):
    """Obtener resumen estadístico"""
    total_rcas = db.query(models.RCA).count()
    abiertos = db.query(models.RCA).filter(models.RCA.estado == "Abierto").count()
    cerrados = db.query(models.RCA).filter(models.RCA.estado == "Cerrado").count()
    criticos = db.query(models.RCA).filter(models.RCA.criticidad == "Crítica").count()
    
    return {
        "total_rcas": total_rcas,
        "abiertos": abiertos,
        "en_analisis": db.query(models.RCA).filter(models.RCA.estado == "En Análisis").count(),
        "cerrados": cerrados,
        "criticos": criticos,
        "tasa_cierre": round(cerrados / total_rcas * 100, 2) if total_rcas > 0 else 0
    }

# ==================== SERVIR ARCHIVOS ESTÁTICOS ====================
# ESTE BLOQUE DEBE ESTAR AQUÍ - DESPUÉS DE LOS ROUTERS
from fastapi.staticfiles import StaticFiles
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
ARCHIVOS_DIR = BASE_DIR / "archivos"

print(f"\n{'='*50}")
print(f"?? ARCHIVOS_DIR: {ARCHIVOS_DIR}")
print(f"?? Existe: {ARCHIVOS_DIR.exists()}")
print(f"{'='*50}\n")

ARCHIVOS_DIR.mkdir(exist_ok=True)
(ARCHIVOS_DIR / "fotos").mkdir(exist_ok=True)

# CRÍTICO: Esto debe ser lo ÚLTIMO antes de if __name__
app.mount("/archivos", StaticFiles(directory=str(ARCHIVOS_DIR)), name="archivos")
print("? Endpoint /archivos configurado\n")

# ==================== INICIO DEL SERVIDOR ====================
if __name__ == "__main__":
    import uvicorn
    print(f"?? Iniciando servidor en http://{config.SERVER_HOST}:{config.SERVER_PORT}")
    print(f"?? Las tablets deben conectarse a: http://192.168.38.14:{config.SERVER_PORT}")
    print(f"?? Documentación: http://192.168.38.14:{config.SERVER_PORT}/docs")
    
    uvicorn.run(
        app,
        host=config.SERVER_HOST,
        port=config.SERVER_PORT,
        log_level="info"
    )