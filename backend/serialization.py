"""Respuesta canónica con revisión de contenido para actualizaciones condicionales."""
import hashlib
import json
from datetime import timezone
import schemas


def utc_to_local(value):
    """Historial (UTC sin zona) a la hora local sin zona del resto de fechas del RCA."""
    if value is None:
        return None
    return value.replace(tzinfo=timezone.utc).astimezone().replace(tzinfo=None)


def convert_rca_to_response(rca):
    response = schemas.RCAResponse.model_validate(rca)
    whys = [''] * 5
    for why in sorted(rca.cinco_porques_rel, key=lambda item: item.id or 0):
        if 1 <= why.nivel <= 5:
            whys[why.nivel - 1] = why.respuesta or ''
    response.cinco_porques = whys
    causes = {}
    for cause in sorted(rca.ishikawa_rel, key=lambda item: item.id or 0):
        causes.setdefault(cause.categoria, []).append(cause.causa)
    response.ishikawa = causes
    response.tiempo_parada = response.tiempo_parada_horas
    # Una reapertura hacia análisis invalida la aprobación vigente.
    for event in reversed(rca.historial_rel):
        if event.estado_nuevo in ('Abierto', 'En Análisis'):
            break
        if event.estado_anterior == 'En Análisis' and event.estado_nuevo == 'En Implementación':
            response.aprobado_por = event.usuario_nombre
            response.fecha_aprobacion = utc_to_local(event.fecha)
            response.comentario_aprobacion = event.comentario
            break
    payload = response.model_dump(mode='json', exclude={'revision'})
    # Incluye el último evento para que cerrar/reabrir no reutilice una revisión.
    payload['last_event'] = max((event.id or 0 for event in rca.historial_rel), default=0)
    response.revision = hashlib.sha256(json.dumps(payload, sort_keys=True, ensure_ascii=False).encode()).hexdigest()
    return response
