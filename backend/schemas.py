"""Contratos validados; los nombres de Android y los históricos son compatibles."""
from datetime import datetime, date
from enum import Enum
from typing import Optional, List, Dict
from pydantic import BaseModel, Field, EmailStr, ConfigDict, AliasChoices, field_validator

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

class RCAUpdate(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True, allow_inf_nan=False)
    titulo: Optional[str] = Field(None, min_length=1, max_length=200)
    descripcion: Optional[str] = None
    fecha_evento: Optional[datetime] = None
    area: Optional[str] = Field(None, max_length=100)
    planta: Optional[str] = Field(None, max_length=100)
    equipo: Optional[str] = Field(None, max_length=150)
    sistema: Optional[str] = Field(None, max_length=100)
    descripcion_falla: Optional[str] = None
    impacto: Optional[str] = None
    metodo_analisis: Optional[str] = Field(None, max_length=50)
    causa_inmediata: Optional[str] = None
    causa_raiz: Optional[str] = None
    causas_contribuyentes: Optional[str] = None
    acciones_correctivas: Optional[str] = None
    acciones_preventivas: Optional[str] = None
    responsable: Optional[str] = Field(None, max_length=100)
    area_responsable: Optional[str] = Field(None, max_length=100)
    fecha_compromiso: Optional[date] = None
    estado: Optional[EstadoRCA] = None
    criticidad: Optional[CriticidadRCA] = None
    tipo_falla: Optional[str] = Field(None, max_length=100)
    categoria: Optional[str] = Field(None, max_length=100)
    tiempo_parada_horas: Optional[float] = Field(None, ge=0, le=99999999.99,
        validation_alias=AliasChoices('tiempo_parada_horas', 'tiempo_parada'))
    costo_estimado: Optional[float] = Field(None, ge=0, le=9999999999999.99)
    verificacion_efectividad: Optional[str] = None
    fecha_verificacion: Optional[date] = None
    efectivo: Optional[bool] = None
    cinco_porques: Optional[List[str]] = Field(None, max_length=5)
    ishikawa: Optional[Dict[str, List[str]]] = None
    comentario_transicion: Optional[str] = Field(None, max_length=2000)

    @field_validator('titulo', 'fecha_evento', 'estado', 'criticidad')
    @classmethod
    def no_null_required(cls, value):
        if value is None:
            raise ValueError('Este campo no admite null')
        return value

    @field_validator('ishikawa')
    @classmethod
    def bounded_ishikawa(cls, value):
        if value is not None:
            if len(value) > 30:
                raise ValueError('Demasiadas categorías')
            for key, causes in value.items():
                if not key.strip() or len(key) > 50 or len(causes) > 100:
                    raise ValueError('Categoría o cantidad de causas no válida')
        return value

class RCACreate(RCAUpdate):
    codigo: str = Field(..., min_length=1, max_length=50)
    titulo: str = Field(..., min_length=1, max_length=200)
    fecha_evento: datetime
    estado: EstadoRCA = EstadoRCA.ABIERTO
    criticidad: CriticidadRCA = CriticidadRCA.MEDIA

class RCAResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    codigo: str
    titulo: str
    descripcion: Optional[str] = None
    fecha_evento: datetime
    fecha_creacion: datetime
    fecha_actualizacion: Optional[datetime] = None
    area: Optional[str] = None
    planta: Optional[str] = None
    equipo: Optional[str] = None
    sistema: Optional[str] = None
    descripcion_falla: Optional[str] = None
    impacto: Optional[str] = None
    metodo_analisis: Optional[str] = None
    causa_inmediata: Optional[str] = None
    causa_raiz: Optional[str] = None
    causas_contribuyentes: Optional[str] = None
    acciones_correctivas: Optional[str] = None
    acciones_preventivas: Optional[str] = None
    responsable: Optional[str] = None
    area_responsable: Optional[str] = None
    fecha_compromiso: Optional[date] = None
    fecha_cierre: Optional[date] = None
    estado: str
    criticidad: str
    tipo_falla: Optional[str] = None
    categoria: Optional[str] = None
    tiempo_parada_horas: Optional[float] = None
    tiempo_parada: Optional[float] = None
    costo_estimado: Optional[float] = None
    verificacion_efectividad: Optional[str] = None
    fecha_verificacion: Optional[date] = None
    efectivo: Optional[bool] = None
    creado_por: Optional[str] = None
    modificado_por: Optional[str] = None
    aprobado_por: Optional[str] = None
    fecha_aprobacion: Optional[datetime] = None
    comentario_aprobacion: Optional[str] = None
    cinco_porques: List[str] = Field(default_factory=list)
    ishikawa: Dict[str, List[str]] = Field(default_factory=dict)
    revision: str = ''

class CincoPorquesCreate(BaseModel):
    rca_id: Optional[int] = None
    nivel: int = Field(..., ge=1, le=5)
    porque: str = Field(..., min_length=1)
    respuesta: Optional[str] = None

class IshikawaCreate(BaseModel):
    rca_id: Optional[int] = None
    categoria: str = Field(..., min_length=1, max_length=50)
    causa: str = Field(..., min_length=1)
    sub_causa: Optional[str] = None

class RolUsuario(str, Enum):
    MANTENEDOR = "Mantenedor"
    SUPERVISOR = "Supervisor"
    GERENTE = "Gerente"

class UsuarioCreate(BaseModel):
    email: EmailStr
    nombre_completo: str = Field(..., min_length=3, max_length=100)
    rol: RolUsuario
    area: Optional[str] = Field(None, max_length=100)
    password: str = Field(..., min_length=8)
    nombre_usuario: str = Field(..., min_length=3, max_length=50)

    @field_validator('email', 'nombre_completo', 'nombre_usuario', 'area', mode='before')
    @classmethod
    def strip_profile(cls, value):
        return value.strip() if isinstance(value, str) else value

    @field_validator('password')
    @classmethod
    def bcrypt_limit(cls, value):
        if len(value.encode('utf-8')) > 72:
            raise ValueError('La contraseña supera 72 bytes UTF-8')
        return value

class UsuarioResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    nombre_usuario: str
    email: EmailStr
    nombre_completo: str
    rol: str
    area: Optional[str] = None
    activo: bool
    fecha_creacion: datetime

class Token(BaseModel):
    access_token: str
    token_type: str
    usuario: dict
