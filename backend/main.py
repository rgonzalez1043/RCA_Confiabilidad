"""
Punto de entrada del backend RCA.

Funciona tanto en desarrollo (python main.py) como en producción como servicio
de Windows con NSSM (uvicorn + app:app).
"""
import logging
import sys
from pathlib import Path

from fastapi import FastAPI, Depends, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles
from sqlalchemy import text
from sqlalchemy.orm import Session

# Configuración de logging ANTES de importar módulos que usen logger
from config import config, BASE_DIR

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    handlers=[
        logging.StreamHandler(sys.stdout),
    ],
)
logger = logging.getLogger("rca.main")

# Asegurar carpeta de logs en disco (si se configura un FileHandler externo)
try:
    Path(config.LOGS_PATH).mkdir(parents=True, exist_ok=True)
except OSError:
    pass

# Imports de la base de datos y modelos
from database import SessionLocal, engine, Base, get_db  # noqa: E402
import models  # noqa: E402
import schemas  # noqa: E402

# Imports de routers
from routers import auth, rca, archivos, reportes  # noqa: E402


# ---------------------------------------------------------------------------
# Crear tablas si no existen
# ---------------------------------------------------------------------------
Base.metadata.create_all(bind=engine)


# ---------------------------------------------------------------------------
# App FastAPI
# ---------------------------------------------------------------------------
app = FastAPI(
    title="RCA API - Sistema de Análisis de Causa Raíz",
    version="1.1.0",
    description="API para gestión de RCA en operaciones industriales",
    docs_url="/docs",
    redoc_url="/redoc",
)


# ---------------------------------------------------------------------------
# CORS
# ---------------------------------------------------------------------------
# allow_credentials=True NO es compatible con origins=["*"]; se ajusta aquí.
if config.cors_is_wildcard:
    logger.warning("CORS configurado con '*' (desarrollo). Credenciales deshabilitadas.")
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=False,
        allow_methods=["*"],
        allow_headers=["*"],
    )
else:
    logger.info("CORS orígenes permitidos: %s", config.CORS_ORIGINS)
    app.add_middleware(
        CORSMiddleware,
        allow_origins=config.CORS_ORIGINS,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )


# ---------------------------------------------------------------------------
# Handlers globales de excepciones
# ---------------------------------------------------------------------------
@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    return JSONResponse(
        status_code=exc.status_code,
        content={"detail": exc.detail},
        headers=getattr(exc, "headers", None),
    )


@app.exception_handler(Exception)
async def unhandled_exception_handler(request: Request, exc: Exception):
    logger.exception("Error no controlado en %s %s", request.method, request.url.path)
    return JSONResponse(
        status_code=500,
        content={"detail": "Error interno del servidor"},
    )


# ---------------------------------------------------------------------------
# Routers
# ---------------------------------------------------------------------------
app.include_router(auth.router)
app.include_router(rca.router)
app.include_router(archivos.router)
app.include_router(reportes.router)


# ---------------------------------------------------------------------------
# Endpoints raíz y de salud
# ---------------------------------------------------------------------------
@app.get("/")
def root():
    return {
        "api": "RCA Sistema",
        "version": "1.1.0",
        "status": "online",
        "servidor": f"{config.SERVER_HOST}:{config.SERVER_PORT}",
    }


@app.get("/health")
def health_check(db: Session = Depends(get_db)):
    """Health-check usado por NSSM / balanceadores para saber si la API vive."""
    try:
        db.execute(text("SELECT 1"))
        return {"status": "healthy", "database": "connected"}
    except Exception as e:
        logger.error("Health-check falló: %s", e)
        raise HTTPException(status_code=503, detail=f"Database error: {str(e)}")


# ---------------------------------------------------------------------------
# Archivos estáticos (subidas)
# ---------------------------------------------------------------------------
ARCHIVOS_DIR = Path(config.ARCHIVOS_PATH)
logger.info("ARCHIVOS_DIR = %s (existe=%s)", ARCHIVOS_DIR, ARCHIVOS_DIR.exists())

# Crear todas las subcarpetas necesarias antes de montar StaticFiles
ARCHIVOS_DIR.mkdir(parents=True, exist_ok=True)
for sub in ("fotos", "pdfs", "evidencias"):
    (ARCHIVOS_DIR / sub).mkdir(parents=True, exist_ok=True)

app.mount("/archivos", StaticFiles(directory=str(ARCHIVOS_DIR)), name="archivos")
logger.info("Endpoint /archivos configurado")


# ---------------------------------------------------------------------------
# Inicio en modo desarrollo
# ---------------------------------------------------------------------------
if __name__ == "__main__":
    import uvicorn

    logger.info("Iniciando servidor (desarrollo) en http://%s:%s", config.SERVER_HOST, config.SERVER_PORT)
    uvicorn.run(
        "main:app",
        host=config.SERVER_HOST,
        port=config.SERVER_PORT,
        log_level="info",
        reload=False,
    )