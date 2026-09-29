"""Toda la suite utiliza SQLite en memoria y archivos temporales, nunca .env."""
import os
import sys
import tempfile
from pathlib import Path

os.environ['RCA_TESTING'] = '1'
os.environ['SECRET_KEY'] = 'test-only-secret-never-use-in-production-000000000'
_files = tempfile.TemporaryDirectory(prefix='rca_tests_')
os.environ['ARCHIVOS_PATH'] = _files.name
os.environ['LOGS_PATH'] = _files.name
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'backend'))

import pytest
from fastapi.testclient import TestClient
from database import Base, engine, SessionLocal
import models
from main import app
from routers.auth import create_access_token, get_password_hash


@pytest.fixture
def client():
    assert engine.url.drivername == 'sqlite' and engine.url.database is None
    Base.metadata.drop_all(engine)
    Base.metadata.create_all(engine)
    with SessionLocal() as db:
        for name, role, active in [('mantenedor', 'Mantenedor', True),
                ('supervisor', 'Supervisor', True), ('gerente', 'Gerente', True),
                ('inactivo', 'Supervisor', False)]:
            db.add(models.Usuario(nombre_usuario=name, nombre_completo=name.title(),
                email=f'{name}@example.com', password_hash=get_password_hash('TestPass123'),
                rol=role, activo=active))
        db.commit()
    with TestClient(app) as test_client:
        yield test_client


def headers(role='supervisor', revision=None):
    token = create_access_token({'sub': f'{role}@example.com'})
    result = {'Authorization': f'Bearer {token}'}
    if revision:
        result['If-Match'] = '"' + revision + '"'
    return result


def payload(**changes):
    return dict(codigo='RCA-TEST-001', titulo='Falla en grúa', fecha_evento='2026-09-01T09:00:00',
        descripcion_falla='Detención del motor', criticidad='Media', planta='Terminal',
        equipo='Grúa 1', responsable='Mantenimiento', **changes)


def create(client, **changes):
    response = client.post('/rca', json=payload(**changes), headers=headers('mantenedor'))
    assert response.status_code == 201, response.text
    return response.json()


def update(client, rca, changes, role='supervisor', expected=200):
    response = client.put(f'/rca/{rca["id"]}', json=changes, headers=headers(role, rca['revision']))
    assert response.status_code == expected, response.text
    return response.json()
