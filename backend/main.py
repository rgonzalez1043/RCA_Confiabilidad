from fastapi import FastAPI, Depends
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session

# Imports de la base de datos
from database import SessionLocal, engine, Base, get_db
import models
import schemas
from config import config

# Imports de routers
from routers import auth, rca, archivos, reportes

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
app.include_router(auth.router)
app.include_router(rca.router)
app.include_router(archivos.router)
app.include_router(reportes.router)

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
        from fastapi import HTTPException
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")

# ==================== SERVIR ARCHIVOS ESTÁTICOS ====================
from fastapi.staticfiles import StaticFiles
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
ARCHIVOS_DIR = BASE_DIR / "archivos"

print(f"\n{'='*50}")
print(f"📁 ARCHIVOS_DIR: {ARCHIVOS_DIR}")
print(f"📁 Existe: {ARCHIVOS_DIR.exists()}")
print(f"{'='*50}\n")

ARCHIVOS_DIR.mkdir(exist_ok=True)
(ARCHIVOS_DIR / "fotos").mkdir(exist_ok=True)

# CRÍTICO: Esto debe ser lo ÚLTIMO antes de if __name__
app.mount("/archivos", StaticFiles(directory=str(ARCHIVOS_DIR)), name="archivos")
print("✅ Endpoint /archivos configurado\n")

# ==================== INICIO DEL SERVIDOR ====================
if __name__ == "__main__":
    import uvicorn
    print(f"🚀 Iniciando servidor en http://{config.SERVER_HOST}:{config.SERVER_PORT}")
    print(f"📱 Las tablets deben conectarse a: http://192.168.38.14:{config.SERVER_PORT}")
    print(f"📖 Documentación: http://192.168.38.14:{config.SERVER_PORT}/docs")
    
    uvicorn.run(
        app,
        host=config.SERVER_HOST,
        port=config.SERVER_PORT,
        log_level="info"
    )