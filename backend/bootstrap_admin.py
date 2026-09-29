"""Alta inicial local: nunca se habilita un registro anónimo en HTTP."""
from getpass import getpass
from database import Base, engine, SessionLocal
from models import Usuario
from schemas import UsuarioCreate
from routers.auth import get_password_hash


def main():
    Base.metadata.create_all(engine)
    with SessionLocal() as db:
        if db.query(Usuario).count():
            raise SystemExit('Ya existen usuarios. Usa un administrador activo para crear cuentas.')
        data = UsuarioCreate(email=input('Email: ').strip(),
            nombre_usuario=input('Usuario: ').strip(), nombre_completo=input('Nombre completo: ').strip(),
            rol='Gerente', password=getpass('Contraseña (mínimo 8 caracteres): '))
        if getpass('Repite la contraseña: ') != data.password:
            raise SystemExit('Las contraseñas no coinciden.')
        db.add(Usuario(email=str(data.email), nombre_usuario=data.nombre_usuario,
            nombre_completo=data.nombre_completo, rol='Gerente', activo=True,
            password_hash=get_password_hash(data.password)))
        db.commit()
        print('Administrador inicial creado.')


if __name__ == '__main__':
    main()
