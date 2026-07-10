"""
Autenticación JWT, registro y gestión de usuarios.
"""
import logging
from datetime import datetime, timedelta, timezone
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from jose import JWTError, jwt
from passlib.context import CryptContext
from sqlalchemy.orm import Session

from config import config
from database import get_db
from models import Usuario
from schemas import UsuarioLogin, UsuarioResponse, Token, UsuarioCreate

logger = logging.getLogger("rca.auth")

router = APIRouter(prefix="/auth", tags=["Autenticación"])

# Configuración tomada de config.py (SECRET_KEY se autogenera si faltaba)
SECRET_KEY = config.SECRET_KEY
ALGORITHM = config.ALGORITHM
ACCESS_TOKEN_EXPIRE_MINUTES = config.ACCESS_TOKEN_EXPIRE_MINUTES

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="auth/login", auto_error=False)


# ==================== FUNCIONES AUXILIARES ====================
def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)


def get_password_hash(password: str) -> str:
    return pwd_context.hash(password)


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + (
        expires_delta or timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    )
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)


def authenticate_user(db: Session, email: str, password: str):
    usuario = db.query(Usuario).filter(Usuario.email == email).first()
    if not usuario or not verify_password(password, usuario.password_hash):
        return False
    return usuario


async def get_current_active_user(
    token: str = Depends(oauth2_scheme),
    db: Session = Depends(get_db),
) -> Usuario:
    """Dependency: devuelve el usuario autenticado o lanza 401."""
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="No se pudo validar las credenciales",
        headers={"WWW-Authenticate": "Bearer"},
    )

    if not token:
        raise credentials_exception

    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        email: Optional[str] = payload.get("sub")
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
            detail="Usuario inactivo",
        )

    return usuario


async def verificar_permiso_admin(
    current_user: Usuario = Depends(get_current_active_user),
) -> Usuario:
    """Solo Supervisor o Gerente."""
    roles_permitidos = ["Supervisor", "Gerente"]
    if current_user.rol not in roles_permitidos:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"No tienes permisos. Solo {' y '.join(roles_permitidos)} pueden realizar esta acción.",
        )
    return current_user


# ==================== ENDPOINTS ====================
@router.post("/login", response_model=Token)
async def login(
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: Session = Depends(get_db),
):
    """
    Login OAuth2.
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
            detail="Usuario inactivo",
        )

    usuario.ultimo_acceso = datetime.now(timezone.utc)
    db.commit()

    access_token = create_access_token(
        data={"sub": usuario.email, "rol": usuario.rol},
        expires_delta=timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES),
    )

    logger.info("Login OK usuario=%s rol=%s", usuario.email, usuario.rol)

    return {
        "access_token": access_token,
        "token_type": "bearer",
        "usuario": {
            "id": usuario.id,
            "nombre": usuario.nombre_completo,
            "email": usuario.email,
            "rol": usuario.rol,
            "area": usuario.area,
        },
    }


@router.post("/registro", response_model=UsuarioResponse, status_code=status.HTTP_201_CREATED)
async def registrar_usuario(
    usuario_data: UsuarioCreate,
    db: Session = Depends(get_db),
    token: Optional[str] = Depends(oauth2_scheme),
):
    """
    Registrar un nuevo usuario.

    - Si NO hay usuarios en la BD → permite crear el primero SIN autenticación.
    - Si ya hay usuarios → requiere token válido y rol Supervisor/Gerente.
    """
    total_usuarios = db.query(Usuario).count()

    if total_usuarios > 0:
        if not token:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Debes estar autenticado para crear usuarios.",
                headers={"WWW-Authenticate": "Bearer"},
            )
        try:
            payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
            email = payload.get("sub")
            if email is None:
                raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Token inválido")
        except JWTError:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Token inválido o expirado")

        current_user = db.query(Usuario).filter(Usuario.email == email).first()
        if not current_user:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Usuario no encontrado")

        if current_user.rol not in ["Supervisor", "Gerente"]:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"No tienes permisos. Solo Supervisor y Gerente pueden crear usuarios. Tu rol: {current_user.rol}",
            )
    else:
        logger.warning("Creando PRIMER usuario del sistema (sin autenticación requerida)")

    # Validar duplicados
    if db.query(Usuario).filter(Usuario.email == usuario_data.email).first():
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="El email ya está registrado")
    if db.query(Usuario).filter(Usuario.nombre_usuario == usuario_data.nombre_usuario).first():
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="El nombre de usuario ya está en uso")

    nuevo_usuario = Usuario(
        nombre_usuario=usuario_data.nombre_usuario,
        nombre_completo=usuario_data.nombre_completo,
        email=usuario_data.email,
        password_hash=get_password_hash(usuario_data.password),
        rol=usuario_data.rol.value,
        area=usuario_data.area,
        activo=True,
    )
    db.add(nuevo_usuario)
    db.commit()
    db.refresh(nuevo_usuario)

    logger.info("Usuario creado email=%s rol=%s", nuevo_usuario.email, nuevo_usuario.rol)
    return nuevo_usuario


@router.get("/me", response_model=UsuarioResponse)
async def get_current_user(current_user: Usuario = Depends(get_current_active_user)):
    """Perfil del usuario autenticado."""
    return current_user


@router.get("/usuarios", response_model=list[UsuarioResponse])
async def listar_usuarios(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(verificar_permiso_admin),
):
    """Listar usuarios (Solo Supervisor/Gerente)."""
    usuarios = db.query(Usuario).offset(skip).limit(limit).all()
    return usuarios


@router.post("/logout")
async def logout():
    """Logout: el cliente debe eliminar el token localmente."""
    return {"message": "Sesión cerrada correctamente"}