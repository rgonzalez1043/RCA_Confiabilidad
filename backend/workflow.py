"""Reglas del proceso, compartidas por todos los endpoints de escritura."""
from datetime import date
from fastapi import HTTPException

STATES = ('Abierto', 'En Análisis', 'En Implementación', 'Cerrado')
EDIT_ROLES = ('Mantenedor', 'Supervisor', 'Gerente')
ADMIN_ROLES = ('Supervisor', 'Gerente')


def require_editor(user):
    if not user.activo or user.rol not in EDIT_ROLES:
        raise HTTPException(403, 'No tienes permiso para editar RCAs')


def require_supervisor(user):
    require_editor(user)
    if user.rol not in ADMIN_ROLES:
        raise HTTPException(403, 'Solo Supervisor o Gerente puede cambiar etapas')


def require_writable(rca, user):
    require_editor(user)
    if rca.estado in ('Cerrado', 'Cancelado'):
        raise HTTPException(409, 'El RCA está en modo de solo lectura')


def validate_transition(current, target, data, user):
    require_supervisor(user)
    if current not in STATES or target not in STATES:
        raise HTTPException(422, 'Transición no soportada')
    origin, destination = STATES.index(current), STATES.index(target)
    if abs(origin - destination) != 1:
        raise HTTPException(422, 'Debes avanzar o volver una etapa a la vez')
    if destination < origin:
        return
    missing = []
    def present(field):
        return bool(str(data.get(field) or '').strip())
    if not present('titulo'): missing.append('Título')
    if not present('descripcion_falla'): missing.append('Descripción de la falla')
    if data.get('criticidad') not in ('Baja', 'Media', 'Alta', 'Crítica'):
        missing.append('Criticidad válida')
    if destination >= 2:
        whys = data.get('cinco_porques') or []
        if len(whys) < 3 or any(not text.strip() for text in whys[:3]):
            missing.append('Primeros tres porqués sin saltos')
        categories = sum(any(cause.strip() for cause in causes)
                         for causes in (data.get('ishikawa') or {}).values())
        if categories < 2: missing.append('Dos categorías Ishikawa con causas')
        if not present('causa_raiz'): missing.append('Causa raíz')
    if destination >= 3:
        for field, label in [('acciones_correctivas', 'Acciones correctivas'),
                             ('responsable', 'Responsable'),
                             ('verificacion_efectividad', 'Verificación de efectividad')]:
            if not present(field): missing.append(label)
        if not data.get('fecha_compromiso'): missing.append('Fecha compromiso')
        verified = data.get('fecha_verificacion')
        if not verified or verified > date.today(): missing.append('Fecha de verificación no futura')
        if data.get('efectivo') is not True: missing.append('Efectividad confirmada')
    if missing:
        raise HTTPException(422, 'Para avanzar debes completar: ' + ', '.join(missing))
