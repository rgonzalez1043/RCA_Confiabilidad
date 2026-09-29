"""API RCA: permisos, validación, revisión y bitácora en una transacción."""
from datetime import datetime, date, timezone
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, Header, Response
from sqlalchemy import func
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session, selectinload
from database import get_db
from routers.auth import get_current_active_user
from serialization import convert_rca_to_response
from workflow import require_editor, require_supervisor, require_writable, validate_transition
import schemas
import models
import crud

router = APIRouter(prefix='/rca', tags=['RCA'], dependencies=[Depends(get_current_active_user)])


def locked_rca(db, rca_id):
    rca = db.query(models.RCA).filter(models.RCA.id == rca_id).populate_existing().with_for_update().first()
    if not rca:
        raise HTTPException(404, 'RCA no encontrado')
    return rca


def require_revision(rca, if_match):
    if not if_match:
        raise HTTPException(428, 'Actualiza la aplicación y carga el RCA antes de modificarlo')
    revision = convert_rca_to_response(rca).revision
    if if_match != '"' + revision + '"':
        raise HTTPException(412, 'Otro usuario modificó este RCA. Carga su última versión antes de guardar')


def add_event(db, rca, previous, target, user, comment=None):
    # El historial se guarda en UTC sin zona; Android lo convierte a hora local.
    db.add(models.RCAHistorial(rca_id=rca.id, estado_anterior=previous,
        estado_nuevo=target, usuario_id=user.id,
        usuario_nombre=user.nombre_completo or user.nombre_usuario,
        fecha=datetime.now(timezone.utc).replace(tzinfo=None), comentario=comment))


def _comparable(key, value):
    """Forma normalizada para detectar cambios reales de contenido."""
    if key == 'cinco_porques':
        whys = [str(text or '').strip() for text in (value or [])]
        return (whys + [''] * 5)[:5]
    if key == 'ishikawa':
        causes = {str(category).strip(): [str(text).strip() for text in (texts or []) if str(text or '').strip()]
                  for category, texts in (value or {}).items()}
        return {category: texts for category, texts in causes.items() if texts}
    if isinstance(value, str):
        return value.strip() or None
    return value


def apply_fields(rca, data):
    data = dict(data)
    whys = data.pop('cinco_porques', None)
    causes = data.pop('ishikawa', None)
    data.pop('comentario_transicion', None)
    for key, value in data.items():
        setattr(rca, key, value)
    if whys is not None:
        rca.cinco_porques_rel = [models.CincoPorques(nivel=i, porque=f'¿Por qué {i}?', respuesta=text.strip())
            for i, text in enumerate(whys, 1) if text.strip()]
    if causes is not None:
        rca.ishikawa_rel = [models.Ishikawa(categoria=category.strip(), causa=text.strip())
            for category, values in causes.items() for text in values if text.strip()]


def saved_response(db, rca, response):
    db.commit()
    db.refresh(rca)
    db.expire(rca, ['cinco_porques_rel', 'ishikawa_rel', 'historial_rel'])
    result = convert_rca_to_response(rca)
    response.headers['ETag'] = '"' + result.revision + '"'
    return result


@router.post('', response_model=schemas.RCAResponse, status_code=201)
def crear_rca(rca: schemas.RCACreate, response: Response, db: Session = Depends(get_db),
              user: models.Usuario = Depends(get_current_active_user)):
    require_editor(user)
    if rca.estado != 'Abierto':
        raise HTTPException(422, 'Todo RCA nuevo debe iniciar en Abierto')
    data = rca.model_dump(exclude={'comentario_transicion'})
    entity = models.RCA()
    apply_fields(entity, data)
    entity.creado_por = user.nombre_completo or user.nombre_usuario
    entity.modificado_por = entity.creado_por
    db.add(entity)
    try:
        db.flush()
        add_event(db, entity, None, 'Abierto', user)
        return saved_response(db, entity, response)
    except IntegrityError:
        db.rollback()
        raise HTTPException(409, 'El código RCA ya existe o los datos entran en conflicto')


@router.get('', response_model=List[schemas.RCAResponse])
def listar_rcas(skip: int = Query(0, ge=0), limit: int = Query(100, ge=1, le=500),
                estado: Optional[schemas.EstadoRCA] = None, area: Optional[str] = None,
                criticidad: Optional[schemas.CriticidadRCA] = None,
                q: Optional[str] = Query(None, max_length=200), db: Session = Depends(get_db)):
    return [convert_rca_to_response(rca) for rca in crud.get_rcas(db, skip, limit, estado, area, criticidad, q)]


@router.get('/{rca_id}', response_model=schemas.RCAResponse)
def obtener_rca(rca_id: int, response: Response, db: Session = Depends(get_db)):
    rca = crud.get_rca(db, rca_id)
    if not rca:
        raise HTTPException(404, 'RCA no encontrado')
    result = convert_rca_to_response(rca)
    response.headers['ETag'] = '"' + result.revision + '"'
    return result


def update_locked(db, rca_id, data, user, if_match, response):
    require_editor(user)
    rca = locked_rca(db, rca_id)
    require_revision(rca, if_match)
    before = convert_rca_to_response(rca).model_dump()
    # null significa "no proporcionado" solo para las herramientas; [] / {} las borran.
    data = {key: value for key, value in data.items()
            if value is not None or key not in ('cinco_porques', 'ishikawa')}
    target = data.get('estado', rca.estado)
    if target != rca.estado:
        validate_transition(rca.estado, target, {**before, **data}, user)
        if rca.estado == 'Cerrado':
            # Android reenvía el registro completo; espacios o huecos equivalentes no son cambios.
            changes = {key for key, value in data.items()
                       if key not in ('estado', 'comentario_transicion')
                       and _comparable(key, before.get(key)) != _comparable(key, value)}
            if changes:
                raise HTTPException(409, 'Reabre el RCA antes de modificar su contenido')
        add_event(db, rca, rca.estado, target, user, data.get('comentario_transicion'))
        rca.fecha_cierre = date.today() if target == 'Cerrado' else None
    else:
        require_writable(rca, user)
    apply_fields(rca, data)
    rca.modificado_por = user.nombre_completo or user.nombre_usuario
    # Mismo reloj que fecha_creacion y los registros anteriores (hora local de la BD).
    rca.fecha_actualizacion = func.now()
    try:
        return saved_response(db, rca, response)
    except IntegrityError:
        db.rollback()
        raise HTTPException(409, 'No se pudo guardar por un conflicto de datos')


@router.put('/{rca_id}', response_model=schemas.RCAResponse)
def actualizar_rca(rca_id: int, rca_update: schemas.RCAUpdate, response: Response,
                    if_match: Optional[str] = Header(None), db: Session = Depends(get_db),
                    user: models.Usuario = Depends(get_current_active_user)):
    return update_locked(db, rca_id, rca_update.model_dump(exclude_unset=True), user, if_match, response)


@router.delete('/{rca_id}', status_code=204)
def eliminar_rca(rca_id: int, if_match: Optional[str] = Header(None), db: Session = Depends(get_db),
                  user: models.Usuario = Depends(get_current_active_user)):
    require_supervisor(user)
    rca = locked_rca(db, rca_id)
    require_revision(rca, if_match)
    # Casos ya iniciados se conservan: no borrar su trazabilidad.
    if rca.estado != 'Abierto' or any(event.estado_anterior is not None for event in rca.historial_rel):
        raise HTTPException(409, 'Solo se pueden eliminar borradores sin historial de etapas')
    if db.query(models.Archivo).filter_by(rca_id=rca_id).first():
        raise HTTPException(409, 'Elimina las evidencias del borrador antes de eliminarlo')
    db.delete(rca)
    db.commit()
    return Response(status_code=204)


@router.get('/{rca_id}/historial')
def historial(rca_id: int, db: Session = Depends(get_db)):
    if not crud.get_rca(db, rca_id):
        raise HTTPException(404, 'RCA no encontrado')
    events = db.query(models.RCAHistorial).filter_by(rca_id=rca_id).order_by(models.RCAHistorial.id).all()
    return [dict(id=e.id, estado_anterior=e.estado_anterior, estado_nuevo=e.estado_nuevo,
        usuario_id=e.usuario_id, usuario_nombre=e.usuario_nombre, fecha=e.fecha,
        comentario=e.comentario) for e in events]


@router.post('/{rca_id}/cinco-porques', response_model=schemas.RCAResponse)
def agregar_cinco_porques(rca_id: int, porques: schemas.CincoPorquesCreate, response: Response,
    if_match: Optional[str] = Header(None), db: Session = Depends(get_db),
    user: models.Usuario = Depends(get_current_active_user)):
    require_editor(user)
    rca = locked_rca(db, rca_id)
    values = convert_rca_to_response(rca).cinco_porques
    values[porques.nivel - 1] = porques.respuesta or ''
    return update_locked(db, rca_id, {'cinco_porques': values}, user, if_match, response)


@router.get('/{rca_id}/cinco-porques')
def obtener_cinco_porques(rca_id: int, db: Session = Depends(get_db)):
    if not crud.get_rca(db, rca_id):
        raise HTTPException(404, 'RCA no encontrado')
    return crud.get_cinco_porques(db, rca_id)


@router.post('/{rca_id}/ishikawa', response_model=schemas.RCAResponse)
def agregar_ishikawa(rca_id: int, ishikawa: schemas.IshikawaCreate, response: Response,
    if_match: Optional[str] = Header(None), db: Session = Depends(get_db),
    user: models.Usuario = Depends(get_current_active_user)):
    require_editor(user)
    rca = locked_rca(db, rca_id)
    values = convert_rca_to_response(rca).ishikawa
    values.setdefault(ishikawa.categoria, []).append(ishikawa.causa)
    return update_locked(db, rca_id, {'ishikawa': values}, user, if_match, response)


@router.get('/{rca_id}/ishikawa')
def obtener_ishikawa(rca_id: int, db: Session = Depends(get_db)):
    if not crud.get_rca(db, rca_id):
        raise HTTPException(404, 'RCA no encontrado')
    return crud.get_ishikawa(db, rca_id)