"""
Endpoints para reportes y estadísticas.
"""
import logging
import os
import re
from uuid import uuid4
from pathlib import Path

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import FileResponse
from starlette.background import BackgroundTask
from sqlalchemy import func, case
from sqlalchemy.orm import Session

from config import config
from database import get_db
from routers.auth import get_current_active_user
import crud
import models
from utils.pdf_generator import generar_reporte_rca
from serialization import convert_rca_to_response

logger = logging.getLogger("rca.reportes")

router = APIRouter(
    prefix="/reportes",
    tags=["Reportes"],
    dependencies=[Depends(get_current_active_user)],  # 🔒 Todo el router requiere auth
)

_SAFE_RE = re.compile(r"[^A-Za-z0-9._-]+")


def _safe_slug(valor: str) -> str:
    """Convertir un código/título en un nombre de archivo seguro."""
    valor = _SAFE_RE.sub("_", valor or "").strip("._")
    return valor or "RCA"


@router.get("/estadisticas")
def obtener_estadisticas(db: Session = Depends(get_db)):
    """Resumen estadístico general."""
    return crud.get_estadisticas(db)


@router.get("/por-area")
def estadisticas_por_area(db: Session = Depends(get_db)):
    """Estadísticas agrupadas por área."""
    resultado = (
        db.query(
            models.RCA.area,
            func.count(models.RCA.id).label("total"),
            func.sum(case((models.RCA.estado == "Cerrado", 1), else_=0)).label("cerrados"),
        )
        .group_by(models.RCA.area)
        .all()
    )
    return [
        {
            "area": r.area or "Sin área",
            "total": r.total,
            "cerrados": r.cerrados,
            "abiertos": r.total - r.cerrados,
        }
        for r in resultado
    ]


@router.get("/por-criticidad")
def estadisticas_por_criticidad(db: Session = Depends(get_db)):
    """Estadísticas por nivel de criticidad."""
    resultado = (
        db.query(
            models.RCA.criticidad,
            func.count(models.RCA.id).label("total"),
        )
        .group_by(models.RCA.criticidad)
        .all()
    )
    return [{"criticidad": r.criticidad or "Sin clasificar", "total": r.total} for r in resultado]


@router.get("/rca/{rca_id}/pdf")
def generar_pdf_rca(rca_id: int, db: Session = Depends(get_db)):
    """Generar (y devolver) el PDF de un RCA."""
    rca = crud.get_rca(db, rca_id)
    if not rca:
        raise HTTPException(status_code=404, detail="RCA no encontrado")

    rca_dict = convert_rca_to_response(rca).model_dump(mode='json')

    # Nombre de archivo sanitizado (sin path traversal)
    nombre_seguro = f"RCA_{_safe_slug(rca.codigo)}.pdf"
    pdf_dir = Path(config.ARCHIVOS_PATH) / "pdfs"
    pdf_dir.mkdir(parents=True, exist_ok=True)
    pdf_path = pdf_dir / f"reporte_{uuid4().hex}.pdf"

    try:
        generar_reporte_rca(rca_dict, str(pdf_path))
    except Exception as e:
        logger.exception("Error generando PDF para RCA %s", rca_id)
        pdf_path.unlink(missing_ok=True)
        raise HTTPException(status_code=500, detail="No se pudo generar el PDF")

    return FileResponse(
        path=str(pdf_path),
        media_type="application/pdf",
        filename=nombre_seguro,
        background=BackgroundTask(pdf_path.unlink, missing_ok=True),
        headers={'Cache-Control': 'private, no-store'},
    )
