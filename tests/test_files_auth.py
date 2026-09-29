from io import BytesIO
from pathlib import Path
from PIL import Image
from conftest import headers, create, update
from database import SessionLocal
from config import config
import models


def photo():
    buffer = BytesIO()
    Image.new('RGB', (10, 10), 'blue').save(buffer, format='PNG')
    return buffer.getvalue()


def upload(client, rca, data=None, name='evidencia.png'):
    return client.post('/archivo/upload', headers=headers('mantenedor'),
        data={'rca_id': rca['id'], 'subido_por': 'Impostor'},
        files={'file': (name, photo() if data is None else data, 'image/png')})


def test_file_contract_auth_download_delete(client):
    rca = create(client)
    response = upload(client, rca)
    assert response.status_code == 201, response.text
    evidence = response.json()
    assert evidence['rca_id'] == rca['id']
    assert evidence['nombre_archivo'] == 'evidencia.png'
    assert evidence['subido_por'] == 'Mantenedor'
    assert client.get(evidence['url']).status_code == 401
    assert client.get(evidence['url'], headers=headers()).content == photo()
    assert client.get('/archivos/' + evidence['ruta_archivo']).status_code == 401
    assert client.get('/archivos/' + evidence['ruta_archivo'], headers=headers()).status_code == 200
    assert client.get(f'/archivo/{rca["id"]}', headers=headers()).json() == [evidence]
    assert client.delete(f'/archivo/{evidence["id"]}', headers=headers()).status_code == 204
    assert client.get(evidence['url'], headers=headers()).status_code == 404
    assert not (Path(config.ARCHIVOS_PATH) / evidence['ruta_archivo']).exists()


def test_same_name_does_not_overwrite_and_photo_quota(client):
    rca = create(client)
    a, b = upload(client, rca).json(), upload(client, rca).json()
    assert a['ruta_archivo'] != b['ruta_archivo']
    for _ in range(8):
        assert upload(client, rca).status_code == 201
    assert upload(client, rca).status_code == 409


def test_invalid_empty_large_photos_leave_no_metadata_or_file(client):
    rca = create(client)
    root = Path(config.ARCHIVOS_PATH)
    before = set(root.rglob('*'))
    for data, status in [(b'<script>fake image</script>', 415), (b'', 422), (b'x' * (10 * 1024 * 1024 + 1), 413)]:
        response = upload(client, rca, data)
        assert response.status_code == status, response.text
    assert client.get(f'/archivo/{rca["id"]}', headers=headers()).json() == []
    assert {p for p in root.rglob('*') if p.is_file()} == {p for p in before if p.is_file()}


def test_closed_file_writes_are_rejected(client):
    rca = create(client)
    evidence = upload(client, rca).json()
    with SessionLocal() as db:
        db.get(models.RCA, rca['id']).estado = 'Cerrado'
        db.commit()
    assert upload(client, rca).status_code == 409
    assert client.delete(f'/archivo/{evidence["id"]}', headers=headers()).status_code == 409
    assert client.get(evidence['url'], headers=headers()).status_code == 200


def test_registration_requires_active_admin_and_blocks_role_escalation(client):
    data = dict(email='new@example.com', nombre_usuario='newuser', nombre_completo='Nuevo Usuario',
        rol='Gerente', password='ValidPassword123')
    assert client.post('/auth/registro', json=data).status_code == 401
    assert client.post('/auth/registro', json=data, headers=headers('inactivo')).status_code == 403
    assert client.post('/auth/registro', json=data, headers=headers('supervisor')).status_code == 403
    assert client.post('/auth/registro', json=data, headers=headers('gerente')).status_code == 201


def test_login_and_inactive_user(client):
    response = client.post('/auth/login', data={'username': 'supervisor@example.com', 'password': 'TestPass123'})
    assert response.status_code == 200
    assert response.json()['usuario']['activo'] is True
    assert client.post('/auth/login', data={'username': 'supervisor@example.com', 'password': 'Incorrecta'}).status_code == 401
    assert client.post('/auth/login', data={'username': 'inactivo@example.com', 'password': 'TestPass123'}).status_code == 403


def test_pdf_is_authenticated_and_temporary(client):
    rca = create(client)
    route = f'/reportes/rca/{rca["id"]}/pdf'
    assert client.get(route).status_code == 401
    response = client.get(route, headers=headers())
    assert response.status_code == 200
    assert response.content.startswith(b'%PDF')
    assert not list((Path(config.ARCHIVOS_PATH) / 'pdfs').glob('reporte_*.pdf'))


def test_pdf_handles_long_special_text_and_preserves_full_fields(client, monkeypatch):
    import routers.reportes as reports
    original = reports.generar_reporte_rca
    captured = {}
    def capture(data, path):
        captured.update(data)
        return original(data, path)
    monkeypatch.setattr(reports, 'generar_reporte_rca', capture)
    rca = create(client)
    rca = update(client, rca, dict(descripcion_falla=('Presión < 5 & temperatura > 90 °C\n' * 160),
        cinco_porques=['Primero', '', 'Tercero'], ishikawa={'Equipo': ['Válvula dañada']},
        verificacion_efectividad='Prueba < 10 bar & sin pérdidas', efectivo=True))
    response = client.get(f'/reportes/rca/{rca["id"]}/pdf', headers=headers())
    assert response.status_code == 200, response.text
    assert response.content.startswith(b'%PDF')
    assert captured['cinco_porques'][:3] == ['Primero', '', 'Tercero']
    assert captured['ishikawa'] == {'Equipo': ['Válvula dañada']}
    assert captured['verificacion_efectividad'] == 'Prueba < 10 bar & sin pérdidas'
    assert captured['efectivo'] is True
