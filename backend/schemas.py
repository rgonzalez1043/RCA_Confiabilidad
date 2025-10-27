from pydantic import BaseModel, Field, EmailStr
from datetime import datetime, date
from typing import Optional, List
from enum import Enum

class EstadoRCA(str, Enum):
    ABIERTO = "Abierto"
    EN_ANALISIS = "En Análisis"
    EN_IMPLEMENTACION = "En Implementación"
    CERRADO = "Cerrado"
    CANCELADO = "Cancelado"

class CriticidadRCA(str, Enum):
    CRITICA = "Crítica"
    ALTA = "Alta"
    MEDIA = "Media"
    BAJA = "Baja"

class RCACreate(BaseModel):
    codigo: str = Field(..., max_length=50)
    titulo: str = Field(..., max_length=200)
    descripcion: Optional[str] = None
    fecha_evento: datetime
    area: Optional[str] = None
    equipo: Optional[str] = None
    descripcion_falla: Optional[str] = None
    criticidad: CriticidadRCA = CriticidadRCA.MEDIA
    creado_por: Optional[str] = None

class RCAUpdate(BaseModel):
    titulo: Optional[str] = None
    descripcion: Optional[str] = None
    causa_raiz: Optional[str] = None
    acciones_correctivas: Optional[str] = None
    estado: Optional[EstadoRCA] = None
    responsable: Optional[str] = None

class RCAResponse(BaseModel):
    id: int
    codigo: str
    titulo: str
    estado: str
    criticidad: str
    fecha_evento: datetime
    fecha_creacion: datetime
    
    class Config:
        from_attributes = True

class CincoPorquesCreate(BaseModel):
    rca_id: int
    nivel: int = Field(..., ge=1, le=5)
    porque: str
    respuesta: Optional[str] = None

class IshikawaCreate(BaseModel):
    rca_id: int
    categoria: str
    causa: str
    sub_causa: Optional[str] = None

class ArchivoUpload(BaseModel):
    rca_id: int
    tipo_contenido: Optional[str] = None
    subido_por: Optional[str] = None

# ==================== SCHEMAS DE USUARIO Y AUTENTICACIÓN ====================

class UsuarioBase(BaseModel):
    email: EmailStr
    nombre_completo: str
    rol: str
    area: Optional[str] = None

class UsuarioCreate(UsuarioBase):
    password: str
    nombre_usuario: str

class UsuarioLogin(BaseModel):
    email: EmailStr
    password: str

class UsuarioResponse(UsuarioBase):
    id: int
    nombre_usuario: str
    activo: bool
    fecha_creacion: datetime
    
    class Config:
        from_attributes = True

class Token(BaseModel):
    access_token: str
    token_type: str
    usuario: dict