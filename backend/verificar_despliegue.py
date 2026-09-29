"""Comprobaciones de solo lectura para actualizar un servidor RCA existente.

Modos:
  python verificar_despliegue.py importar
      Importa esta versión con el Python del servicio, sin abrir MySQL.
  python verificar_despliegue.py bd --env <ruta al .env instalado>
      Compara el esquema real de MySQL con los modelos de esta versión.

No escribe en la base de datos ni en disco. Código de salida 0 = sin bloqueos.
"""
import argparse
import os
import sys
import tempfile
from pathlib import Path

BACKEND_DIR = Path(__file__).resolve().parent
VERSION = '1.2.0'
ROUTES = {'/rca/{rca_id}/historial', '/archivo/{archivo_id}/contenido'}


def importar():
    temp = tempfile.mkdtemp(prefix='rca_verificacion_')
    os.environ.update(RCA_TESTING='1', ARCHIVOS_PATH=temp, LOGS_PATH=temp,
                      SECRET_KEY='verificacion-local-sin-uso-en-produccion-000000')
    sys.path.insert(0, str(BACKEND_DIR))
    import pydantic
    import fastapi
    import sqlalchemy
    print(f'Python {sys.version.split()[0]} | FastAPI {fastapi.__version__} | '
          f'Pydantic {pydantic.VERSION} | SQLAlchemy {sqlalchemy.__version__}')
    if sys.version_info < (3, 9):
        print('ERROR: se requiere Python 3.9 o superior')
        return 1
    if int(pydantic.VERSION.split('.')[0]) < 2:
        print('ERROR: se requiere Pydantic 2; instala requirements.txt')
        return 1
    import main
    paths = {route.path for route in main.app.routes}
    if main.app.version != VERSION or not ROUTES <= paths:
        print(f'ERROR: la versión importada es {main.app.version}')
        return 1
    print(f'OK: la versión {VERSION} se importa con este entorno de Python')
    return 0


def bd(env_path):
    from dotenv import load_dotenv
    if not Path(env_path).is_file():
        print(f'ERROR: no existe {env_path}')
        return 1
    load_dotenv(env_path)
    os.environ.pop('RCA_TESTING', None)
    # Esta verificación no usa JWT; evita que config genere una clave en disco.
    os.environ.setdefault('SECRET_KEY', 'verificacion-local-sin-uso-en-produccion-000000')
    sys.path.insert(0, str(BACKEND_DIR))
    from sqlalchemy import inspect, text
    from database import Base, engine
    import models  # noqa: F401  (registra las tablas)

    errors, warnings = [], []
    with engine.connect() as conn:
        name, version, default_engine = conn.execute(
            text('SELECT DATABASE(), VERSION(), @@default_storage_engine')).one()
        print(f'Conexión OK: base {name}, servidor {version}, motor por defecto {default_engine}')
        engines = dict(conn.execute(text(
            'SELECT TABLE_NAME, ENGINE FROM information_schema.TABLES WHERE TABLE_SCHEMA = DATABASE()')).all())
        counts = {}
        for table in ('rcas', 'usuarios', 'archivos'):
            if table in engines:
                counts[table] = conn.execute(text(f'SELECT COUNT(*) FROM `{table}`')).scalar()
        grants = set()
        if 'rca_historial' not in engines:
            user, host = conn.execute(text('SELECT CURRENT_USER()')).scalar().rsplit('@', 1)
            grantee = f"'{user}'@'{host}'"
            grants = {row[0] for row in conn.execute(text(
                'SELECT PRIVILEGE_TYPE FROM information_schema.USER_PRIVILEGES WHERE GRANTEE = :g '
                'UNION SELECT PRIVILEGE_TYPE FROM information_schema.SCHEMA_PRIVILEGES '
                'WHERE GRANTEE = :g AND TABLE_SCHEMA = DATABASE()'), {'g': grantee})}
    print('Registros: ' + ', '.join(f'{t}={n}' for t, n in counts.items()))
    if 'rca_historial' not in engines:
        # Al iniciar, create_all crea rca_historial con su clave foránea hacia rcas.
        # MySQL 8 exige REFERENCES para la clave foránea; MariaDB no lo utiliza.
        required = {'CREATE'} if 'mariadb' in version.lower() else {'CREATE', 'REFERENCES'}
        missing_grants = required - grants
        if missing_grants:
            errors.append('El usuario de la base no tiene permiso ' + ', '.join(sorted(missing_grants))
                          + ' para crear rca_historial (revisar con SHOW GRANTS)')

    inspector = inspect(engine)
    for table in Base.metadata.sorted_tables:
        if table.name not in engines:
            (warnings if table.name == 'rca_historial' else errors).append(
                f'La tabla {table.name} no existe' + (' (se creará al iniciar)' if table.name == 'rca_historial' else ''))
            continue
        existing = {column['name'] for column in inspector.get_columns(table.name)}
        missing = [column.name for column in table.columns if column.name not in existing]
        if missing:
            errors.append(f'A la tabla {table.name} le faltan columnas: {", ".join(missing)}')
        if (engines[table.name] or '').lower() != 'innodb':
            message = f'La tabla {table.name} usa {engines[table.name]}, no InnoDB'
            (errors if table.name in ('rcas', 'rca_historial') else warnings).append(message)

    for message in warnings:
        print('AVISO: ' + message)
    for message in errors:
        print('ERROR: ' + message)
    if 'rca_historial' in engines:
        print('La tabla rca_historial ya existe')
    print('OK: el esquema es compatible' if not errors else 'Hay bloqueos: no actualizar hasta resolverlos')
    return 1 if errors else 0


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument('modo', choices=['importar', 'bd'])
    parser.add_argument('--env', help='Ruta del .env del servidor (modo bd)')
    args = parser.parse_args()
    try:
        sys.exit(importar() if args.modo == 'importar' else bd(args.env or str(BACKEND_DIR / '.env')))
    except Exception as exc:  # El script que lo invoca muestra el motivo y se detiene.
        print(f'ERROR: {type(exc).__name__}: {exc}')
        sys.exit(1)
