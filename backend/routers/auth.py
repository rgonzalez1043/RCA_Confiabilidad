from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from passlib.context import CryptContext
from datetime import datetime, timedelta
from jose import JWTError, jwt
from typing import Optional
import os

from database import get_db
from models import Usuario
from schemas import UsuarioLogin, UsuarioResponse, Token, UsuarioCreate

router = APIRouter(prefix="/auth", tags=["Autenticación"])

# Configuración
SECRET_KEY = os.getenv("SECRET_KEY", "tu-clave-secreta-super-segura-cambiar-en-produccion")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60 * 24  # 24 horas

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="auth/login", auto_error=False)

# ==================== FUNCIONES AUXILIARES ====================

def verify_password(plain_password, hashed_password):
    """Verificar contraseña contra hash"""
    return pwd_context.verify(plain_password, hashed_password)

def get_password_hash(password):
    """Generar hash de contraseña"""
    return pwd_context.hash(password)

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    """Crear token JWT"""
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=15)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

def authenticate_user(db: Session, email: str, password: str):
    """Autenticar usuario con email y contraseña"""
    usuario = db.query(Usuario).filter(Usuario.email == email).first()
    if not usuario:
        return False
    if not verify_password(password, usuario.password_hash):
        return False
    return usuario

async def get_current_active_user(
    token: str = Depends(oauth2_scheme),
    db: Session = Depends(get_db)
) -> Usuario:
    """Obtener usuario actual autenticado"""
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="No se pudo validar las credenciales",
        headers={"WWW-Authenticate": "Bearer"},
    )
    
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        email: str = payload.get("sub")
        if email is None:
            raise credentials_exception
    except JWTError:
        raise credentials_exception
    
    usuario = db.query(Usuario).filter(Usuario.email == email).first()
    if usuario is None:
        raise credentials_exception
    
    if not usuario.activo:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Usuario inactivo"
        )
    
    return usuario

async def verificar_permiso_admin(
    current_user: Usuario = Depends(get_current_active_user)
) -> Usuario:
    """Verificar que el usuario tiene permisos de administrador (Supervisor o Gerente)"""
    roles_permitidos = ["Supervisor", "Gerente"]
    if current_user.rol not in roles_permitidos:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"No tienes permisos. Solo {' y '.join(roles_permitidos)} pueden realizar esta acción."
        )
    return current_user

# ==================== ENDPOINTS ====================

@router.post("/login", response_model=Token)
async def login(
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: Session = Depends(get_db)
):
    """
    Login de usuario con OAuth2
    - username: email del usuario
    - password: contraseña
    """
    usuario = authenticate_user(db, form_data.username, form_data.password)
    
    if not usuario:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Email o contraseña incorrectos",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    if not usuario.activo:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Usuario inactivo"
        )
    
    # Actualizar último acceso
    usuario.ultimo_acceso = datetime.now()
    db.commit()
    
    # Crear token
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": usuario.email, "rol": usuario.rol},
        expires_delta=access_token_expires
    )
    
    return {
        "access_token": access_token,
        "token_type": "bearer",
        "usuario": {
            "id": usuario.id,
            "nombre": usuario.nombre_completo,
            "email": usuario.email,
            "rol": usuario.rol,
            "area": usuario.area
        }
    }

@router.post("/registro", response_model=UsuarioResponse, status_code=status.HTTP_201_CREATED)
async def registrar_usuario(
    usuario_data: UsuarioCreate,
    db: Session = Depends(get_db),
    token: Optional[str] = Depends(oauth2_scheme)
):
    """
    Registrar un nuevo usuario
    
    🔓 PRIMER USUARIO: Si NO hay usuarios en la BD, permite crear sin autenticación
    🔒 SIGUIENTES USUARIOS: Requiere autenticación y permisos de Supervisor/Gerente
    
    - nombre_usuario: nombre de usuario único
    - nombre_completo: nombre completo del usuario
    - email: email único del usuario
    - password: contraseña (se guardará hasheada)
    - rol: Mantenedor, Supervisor o Gerente (se recomienda Gerente para el primer usuario)
    - area: área de trabajo (opcional)
    """
    # Verificar cuántos usuarios hay
    total_usuarios = db.query(Usuario).count()
    
    # Si ya hay usuarios, REQUIERE autenticación
    if total_usuarios > 0:
        if not token:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Debes estar autenticado para crear usuarios. Usa el candado 'Authorize' en Swagger.",
                headers={"WWW-Authenticate": "Bearer"},
            )
        
        # Verificar el token
        try:
            payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
            email: str = payload.get("sub")
            if email is None:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Token inválido"
                )
        except JWTError:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Token inválido o expirado"
            )
        
        # Obtener usuario actual
        current_user = db.query(Usuario).filter(Usuario.email == email).first()
        if not current_user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Usuario no encontrado"
            )
        
        # Verificar permisos (solo Supervisor o Gerente)
        if current_user.rol not in ["Supervisor", "Gerente"]:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"No tienes permisos. Solo Supervisor y Gerente pueden crear usuarios. Tu rol: {current_user.rol}"
            )
    else:
        # Es el PRIMER usuario - se permite sin autenticación
        print(f"\n🔓 Creando PRIMER usuario del sistema (sin autenticación requerida)")
    
    # Verificar si el email ya existe
    if db.query(Usuario).filter(Usuario.email == usuario_data.email).first():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="El email ya está registrado"
        )
    
    # Verificar si el nombre de usuario ya existe
    if db.query(Usuario).filter(Usuario.nombre_usuario == usuario_data.nombre_usuario).first():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="El nombre de usuario ya está en uso"
        )
    
    # Validar rol (ya validado por Pydantic, pero por si acaso)
    roles_validos = ["Mantenedor", "Supervisor", "Gerente"]
    if usuario_data.rol.value not in roles_validos:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Rol inválido. Debe ser uno de: {', '.join(roles_validos)}"
        )
    
    # Crear nuevo usuario
    nuevo_usuario = Usuario(
        nombre_usuario=usuario_data.nombre_usuario,
        nombre_completo=usuario_data.nombre_completo,
        email=usuario_data.email,
        password_hash=get_password_hash(usuario_data.password),
        rol=usuario_data.rol.value,  # Usar .value para obtener el string del Enum
        area=usuario_data.area,
        activo=True
    )
    
    db.add(nuevo_usuario)
    db.commit()
    db.refresh(nuevo_usuario)
    
    # Mensaje informativo
    if total_usuarios == 0:
        print(f"✅ PRIMER USUARIO CREADO: {nuevo_usuario.nombre_completo} ({nuevo_usuario.email}) - Rol: {nuevo_usuario.rol}")
        print(f"🔒 A partir de ahora se requerirá autenticación para crear más usuarios\n")
    
    return nuevo_usuario

@router.get("/me", response_model=UsuarioResponse)
async def get_current_user(
    current_user: Usuario = Depends(get_current_active_user)
):
    """
    Obtener información del usuario actual autenticado
    
    Requiere token de autenticación (usar el candado Authorize en Swagger)
    """
    return current_user

@router.get("/usuarios", response_model=list[UsuarioResponse])
async def listar_usuarios(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(verificar_permiso_admin)
):
    """
    Listar todos los usuarios del sistema (REQUIERE PERMISOS DE SUPERVISOR/GERENTE)
    
    Solo Supervisores y Gerentes pueden ver la lista de usuarios.
    """
    usuarios = db.query(Usuario).offset(skip).limit(limit).all()
    return usuarios

@router.post("/logout")
async def logout():
    """
    Logout - el cliente debe eliminar el token localmente
    """
    return {"message": "Sesión cerrada correctamente"}
