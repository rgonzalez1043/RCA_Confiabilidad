from datetime import date, timedelta
from sqlalchemy.dialects import mysql
from sqlalchemy import select, func, case
from conftest import headers, create, update, payload
from database import SessionLocal
import models


def test_create_preserves_android_fields_and_server_identity(client):
    rca = create(client, creado_por='Impostor', tiempo_parada=1.5,
                 costo_estimado=125.5, causa_raiz='Plan incompleto', aprobado_por='Impostor')
    assert rca['planta'] == 'Terminal'
    assert rca['responsable'] == 'Mantenimiento'
    assert rca['creado_por'] == 'Mantenedor'
    assert rca['aprobado_por'] is None
    assert rca['tiempo_parada_horas'] == rca['tiempo_parada'] == 1.5
    assert len(rca['revision']) == 64


def test_full_android_payload_preserves_data_and_changes_event_date(client):
    rca = create(client)
    data = {**rca, 'fecha_evento': '2026-09-02T09:00:00', 'titulo': 'Título editado'}
    result = update(client, rca, data, 'mantenedor')
    assert result['fecha_evento'] == '2026-09-02T09:00:00'
    assert result['titulo'] == 'Título editado'
    assert result['creado_por'] == rca['creado_por']


def test_no_null_or_negative_required_fields(client):
    rca = create(client)
    for data in [{'titulo': None}, {'titulo': '  '}, {'estado': None}, {'fecha_evento': None},
                 {'costo_estimado': -1}, {'tiempo_parada': -1}, {'cinco_porques': ['x'] * 6}]:
        update(client, rca, data, expected=422)


def test_requires_auth_and_active_role(client):
    assert client.get('/rca').status_code == 401
    assert client.get('/rca', headers=headers('inactivo')).status_code == 403
    rca = create(client)
    update(client, rca, {'estado': 'En Análisis'}, 'mantenedor', expected=403)


def test_rejects_skipping_stages_and_blank_analysis(client):
    rca = create(client)
    update(client, rca, {'estado': 'Cerrado'}, expected=422)
    rca = update(client, rca, {'estado': 'En Análisis'})
    update(client, rca, {'estado': 'En Implementación', 'cinco_porques': ['A', '', 'B', 'C'],
        'ishikawa': {'Equipo': [' '], 'Ambiente': [' ']}, 'causa_raiz': ' '}, expected=422)


def test_preserves_why_positions_and_explicit_clearing(client):
    rca = create(client, cinco_porques=['', 'Segundo', '', 'Cuarto', ''], ishikawa={'Equipo': ['Causa']})
    assert rca['cinco_porques'] == ['', 'Segundo', '', 'Cuarto', '']
    updated = update(client, rca, {'cinco_porques': ['', '', '', '', ''], 'ishikawa': {}})
    assert updated['cinco_porques'] == [''] * 5
    assert updated['ishikawa'] == {}
    read = client.get(f'/rca/{rca["id"]}', headers=headers()).json()
    assert read == updated


def test_prevents_stale_writes_including_child_endpoints(client):
    rca = create(client)
    latest = update(client, rca, {'titulo': 'Cambio de otro usuario'})
    update(client, rca, {'titulo': 'Sobrescribir'}, expected=412)
    path = f'/rca/{rca["id"]}'
    assert client.put(path, json={'titulo': 'Sin revisión'}, headers=headers()).status_code == 428
    response = client.post(path + '/cinco-porques', headers=headers(revision=rca['revision']),
        json={'nivel': 1, 'porque': 'Por qué', 'respuesta': 'Causa'})
    assert response.status_code == 412
    assert client.get(path, headers=headers()).json()['titulo'] == latest['titulo']


def test_complete_workflow_effectiveness_history_and_read_only(client):
    rca = create(client)
    rca = update(client, rca, {'estado': 'En Análisis'})
    rca = update(client, rca, {'estado': 'En Implementación', 'cinco_porques': ['A', 'B', 'C'],
        'ishikawa': {'Equipo': ['A'], 'Mantenimiento': ['B']}, 'causa_raiz': 'Plan insuficiente'})
    assert rca['aprobado_por'] == 'Supervisor'
    assert rca['fecha_aprobacion']
    update(client, rca, {'estado': 'Cerrado'}, expected=422)
    rca = update(client, rca, {'acciones_correctivas': 'Revisar plan',
        'fecha_compromiso': '2026-09-29', 'verificacion_efectividad': 'Sin recurrencia en revisión',
        'fecha_verificacion': date.today().isoformat(), 'efectivo': True})
    update(client, rca, {'estado': 'Cerrado', 'fecha_verificacion': (date.today()+timedelta(days=1)).isoformat()}, expected=422)
    rca = update(client, rca, {'estado': 'Cerrado'})
    assert rca['fecha_cierre'] == date.today().isoformat()
    update(client, rca, {'titulo': 'No editable'}, expected=409)
    response = client.post(f'/rca/{rca["id"]}/ishikawa',
        json={'categoria': 'Equipo', 'causa': 'No editable'}, headers=headers(revision=rca['revision']))
    assert response.status_code == 409
    rca = update(client, rca, {**rca, 'estado': 'En Implementación'})
    assert rca['fecha_cierre'] is None
    rca = update(client, rca, {'estado': 'En Análisis'})
    assert rca['aprobado_por'] is None
    events = client.get(f'/rca/{rca["id"]}/historial', headers=headers()).json()
    assert [e['estado_nuevo'] for e in events] == ['Abierto', 'En Análisis', 'En Implementación', 'Cerrado', 'En Implementación', 'En Análisis']


def test_duplicate_code_conflict_and_delete_draft(client):
    rca = create(client)
    assert client.post('/rca', json=payload(), headers=headers()).status_code == 409
    assert client.delete(f'/rca/{rca["id"]}', headers=headers('mantenedor', rca['revision'])).status_code == 403
    assert client.delete(f'/rca/{rca["id"]}', headers=headers(revision=rca['revision'])).status_code == 204


def test_stable_pagination_with_equal_timestamps(client):
    with SessionLocal() as db:
        from datetime import datetime
        for i in range(125):
            db.add(models.RCA(codigo=f'PAGE-{i}', titulo='Caso', fecha_evento=datetime(2026,1,1),
                fecha_creacion=datetime(2026,1,1)))
        db.commit()
    ids = []
    for skip in (0, 50, 100):
        response = client.get(f'/rca?skip={skip}&limit=50', headers=headers())
        assert response.status_code == 200
        ids.extend(rca['id'] for rca in response.json())
    assert len(ids) == len(set(ids)) == 125
    assert ids == sorted(ids, reverse=True)


def test_area_report_uses_mysql_compatible_aggregate(client):
    create(client)
    assert client.get('/reportes/por-area', headers=headers()).status_code == 200
    sql = str(select(func.sum(case((models.RCA.estado == 'Cerrado', 1), else_=0))).compile(dialect=mysql.dialect()))
    assert 'FILTER (' not in sql and 'CASE WHEN' in sql
