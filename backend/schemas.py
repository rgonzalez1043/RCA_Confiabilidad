from pydantic import BaseModel, Field, EmailStr
from datetime import datetime, date
from typing import Optional, List, Dict
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
    
    # Análisis de causa raíz
    cinco_porques: Optional[List[str]] = None
    ishikawa: Optional[Dict[str, List[str]]] = None

class RCAUpdate(BaseModel):
    # Campos principales
    titulo: Optional[str] = None
    descripcion: Optional[str] = None
    
    # Ubicación y contexto
    area: Optional[str] = None
    planta: Optional[str] = None
    equipo: Optional[str] = None
    sistema: Optional[str] = None
    
    # Descripción del problema
    descripcion_falla: Optional[str] = None
    impacto: Optional[str] = None
    metodo_analisis: Optional[str] = None
    
    # Análisis de causas
    causa_inmediata: Optional[str] = None
    causa_raiz: Optional[str] = None
    causas_contribuyentes: Optional[str] = None
    
    # Acciones
    acciones_correctivas: Optional[str] = None
    acciones_preventivas: Optional[str] = None
    
    # Responsables y seguimiento
    responsable: Optional[str] = None
    area_responsable: Optional[str] = None
    fecha_compromiso: Optional[date] = None  # ✅ AGREGADO
    fecha_cierre: Optional[date] = None
    
    # Estado y criticidad
    estado: Optional[EstadoRCA] = None
    criticidad: Optional[CriticidadRCA] = None
    
    # Clasificación
    tipo_falla: Optional[str] = None
    categoria: Optional[str] = None
    
    # Impacto económico
    tiempo_parada_horas: Optional[float] = None
    costo_estimado: Optional[float] = None
    
    # Verificación de efectividad
    verificacion_efectividad: Optional[str] = None
    fecha_verificacion: Optional[date] = None
    efectivo: Optional[bool] = None
    
    # Auditoría
    modificado_por: Optional[str] = None
    
    # Análisis de causa raíz
    cinco_porques: Optional[List[str]] = None
    ishikawa: Optional[Dict[str, List[str]]] = None

class RCAResponse(BaseModel):
    # Campos principales
    id: int
    codigo: str
    titulo: str
    descripcion: Optional[str] = None
    
    # Fechas
    fecha_evento: datetime
    fecha_creacion: datetime
    fecha_actualizacion: Optional[datetime] = None
    
    # Ubicación y contexto
    area: Optional[str] = None
    planta: Optional[str] = None
    equipo: Optional[str] = None
    sistema: Optional[str] = None
    
    # Descripción del problema
    descripcion_falla: Optional[str] = None
    impacto: Optional[str] = None
    metodo_analisis: Optional[str] = None
    
    # Análisis de causas
    causa_inmediata: Optional[str] = None
    causa_raiz: Optional[str] = None
    causas_contribuyentes: Optional[str] = None
    
    # Acciones
    acciones_correctivas: Optional[str] = None
    acciones_preventivas: Optional[str] = None
    
    # Responsables y seguimiento
    responsable: Optional[str] = None
    area_responsable: Optional[str] = None
    fecha_compromiso: Optional[date] = None
    fecha_cierre: Optional[date] = None
    
    # Estado y criticidad
    estado: str
    criticidad: str
    
    # Clasificación
    tipo_falla: Optional[str] = None
    categoria: Optional[str] = None
    
    # Impacto económico
    tiempo_parada_horas: Optional[float] = None
    costo_estimado: Optional[float] = None
    
    # Verificación de efectividad
    verificacion_efectividad: Optional[str] = None
    fecha_verificacion: Optional[date] = None
    efectivo: Optional[bool] = None
    
    # Auditoría
    creado_por: Optional[str] = None
    modificado_por: Optional[str] = None
    
    # Análisis de causa raíz (poblado desde relaciones)
    cinco_porques: Optional[List[str]] = None
    ishikawa: Optional[Dict[str, List[str]]] = None
    
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

class RolUsuario(str, Enum):
    MANTENEDOR = "Mantenedor"
    SUPERVISOR = "Supervisor"
    GERENTE = "Gerente"

class UsuarioBase(BaseModel):
    email: EmailStr
    nombre_completo: str = Field(..., min_length=3, description="Nombre completo del usuario")
    rol: RolUsuario = Field(..., description="Rol del usuario en el sistema")
    area: Optional[str] = Field(None, description="Área de trabajo del usuario")

class UsuarioCreate(UsuarioBase):
    password: str = Field(..., min_length=6, description="Contraseña (mínimo 6 caracteres)")
    nombre_usuario: str = Field(..., min_length=3, description="Nombre de usuario único")

class UsuarioLogin(BaseModel):
    email: EmailStr
    password: str

class UsuarioResponse(BaseModel):
    id: int
    nombre_usuario: str
    email: EmailStr
    nombre_completo: str
    rol: str  # String simple en la respuesta
    area: Optional[str] = None
    activo: bool
    fecha_creacion: datetime
    
    class Config:
        from_attributes = True

class Token(BaseModel):
    access_token: str
    token_type: str
    usuario: dict