"""
Script para crear usuarios iniciales del sistema RCA
Ejecutar con: python scripts/crear_usuarios.py
"""
import sys
from pathlib import Path

# Agregar el directorio padre al path para importar módulos
sys.path.append(str(Path(__file__).parent.parent))

from passlib.context import CryptContext
from database import SessionLocal
from models import Usuario

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def crear_usuarios_iniciales():
    """Crear usuarios iniciales para el sistema"""
    db = SessionLocal()
    
    usuarios = [
        {
            "nombre_usuario": "mantenedor1",
            "nombre_completo": "Juan Pérez",
            "email": "mantenedor@puerto.cl",
            "password": "mantenedor123",
            "rol": "Mantenedor",
            "area": "Mantenimiento Mecánico"
        },
        {
            "nombre_usuario": "supervisor1",
            "nombre_completo": "María González",
            "email": "supervisor@puerto.cl",
            "password": "supervisor123",
            "rol": "Supervisor",
            "area": "Confiabilidad"
        },
        {
            "nombre_usuario": "gerente1",
            "nombre_completo": "Carlos Rodríguez",
            "email": "gerente@puerto.cl",
            "password": "gerente123",
            "rol": "Gerente",
            "area": "Gerencia de Mantenimiento"
        }
    ]
    
    print("\n" + "="*60)
    print("CREACIÓN DE USUARIOS INICIALES - SISTEMA RCA")
    print("="*60 + "\n")
    
    for user_data in usuarios:
        # Verificar si ya existe
        existe = db.query(Usuario).filter(Usuario.email == user_data["email"]).first()
        if existe:
            print(f"⚠️  Usuario {user_data['email']} ya existe - OMITIDO")
            continue
        
        # Crear usuario
        usuario = Usuario(
            nombre_usuario=user_data["nombre_usuario"],
            nombre_completo=user_data["nombre_completo"],
            email=user_data["email"],
            password_hash=pwd_context.hash(user_data["password"]),
            rol=user_data["rol"],
            area=user_data["area"],
            activo=True
        )
        
        db.add(usuario)
        print(f"✅ Usuario {user_data['email']} creado")
        print(f"   - Nombre: {user_data['nombre_completo']}")
        print(f"   - Rol: {user_data['rol']}")
        print(f"   - Área: {user_data['area']}")
        print(f"   - Usuario: {user_data['nombre_usuario']}")
        print(f"   - Contraseña: {user_data['password']}")
        print()
    
    try:
        db.commit()
        print("="*60)
        print("✅ Usuarios iniciales creados correctamente")
        print("="*60 + "\n")
    except Exception as e:
        db.rollback()
        print(f"\n❌ Error al crear usuarios: {e}")
    finally:
        db.close()

if __name__ == "__main__":
    crear_usuarios_iniciales()
