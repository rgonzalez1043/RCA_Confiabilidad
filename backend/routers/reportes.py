"""
Endpoints para reportes y estadísticas
"""
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from fastapi.responses import FileResponse
from fastapi import HTTPException
from database import get_db
import crud

router = APIRouter(prefix="/reportes", tags=["Reportes"])

@router.get("/estadisticas")
def obtener_estadisticas(db: Session = Depends(get_db)):
    """Obtener resumen estadístico general"""
    return crud.get_estadisticas(db)

@router.get("/por-area")
def estadisticas_por_area(db: Session = Depends(get_db)):
    """Estadísticas agrupadas por área"""
    from sqlalchemy import func
    import models
    
    resultado = db.query(
        models.RCA.area,
        func.count(models.RCA.id).label('total'),
        func.count(models.RCA.id).filter(models.RCA.estado == 'Cerrado').label('cerrados')
    ).group_by(models.RCA.area).all()
    
    return [
        {
            "area": r.area or "Sin área",
            "total": r.total,
            "cerrados": r.cerrados,
            "abiertos": r.total - r.cerrados
        }
        for r in resultado
    ]

@router.get("/rca/{rca_id}/pdf")
def generar_pdf_rca(rca_id: int, db: Session = Depends(get_db)):
    """Generar PDF de un RCA"""
    from utils.pdf_generator import generar_reporte_rca
    import crud
    import os
    from config import config
    
    # Obtener RCA
    rca = crud.get_rca(db, rca_id)
    if not rca:
        raise HTTPException(status_code=404, detail="RCA no encontrado")
    
    # Convertir a dict
    rca_dict = {
        "codigo": rca.codigo or "N/A",
        "titulo": rca.titulo or "N/A",
        "fecha_evento": str(rca.fecha_evento) if rca.fecha_evento else "N/A",
        "area": rca.area or "N/A",
        "equipo": rca.equipo or "N/A",
        "criticidad": rca.criticidad or "N/A",
        "estado": rca.estado or "N/A",
        "responsable": rca.responsable or "N/A",
        "descripcion_falla": rca.descripcion_falla or "N/A",
        "causa_raiz": rca.causa_raiz or "N/A",
        "acciones_correctivas": rca.acciones_correctivas or "N/A"
    }
    
    # Generar PDF
    pdf_path = os.path.join(config.ARCHIVOS_PATH, 'pdfs', f'RCA_{rca.codigo}.pdf')
    os.makedirs(os.path.dirname(pdf_path), exist_ok=True)
    
    try:
        generar_reporte_rca(rca_dict, pdf_path)
        return FileResponse(
            pdf_path,
            media_type='application/pdf',
            filename=f'RCA_{rca.codigo}.pdf'
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error al generar PDF: {str(e)}")

@router.get("/por-criticidad")
def estadisticas_por_criticidad(db: Session = Depends(get_db)):
    """Estadísticas por nivel de criticidad"""
    from sqlalchemy import func
    import models
    
    resultado = db.query(
        models.RCA.criticidad,
        func.count(models.RCA.id).label('total')
    ).group_by(models.RCA.criticidad).all()
    
    return [{"criticidad": r.criticidad, "total": r.total} for r in resultado]