from sqlalchemy import Column, Integer, String, Text, DateTime, Date, Boolean, DECIMAL, Enum, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from database import Base

class RCA(Base):
    __tablename__ = "rcas"
    
    id = Column(Integer, primary_key=True, index=True)
    codigo = Column(String(50), unique=True, nullable=False)
    titulo = Column(String(200), nullable=False)
    descripcion = Column(Text)
    
    fecha_evento = Column(DateTime, nullable=False)
    fecha_creacion = Column(DateTime, default=func.now())
    fecha_actualizacion = Column(DateTime, default=func.now(), onupdate=func.now())
    
    area = Column(String(100))
    planta = Column(String(100))
    equipo = Column(String(150))
    sistema = Column(String(100))
    
    descripcion_falla = Column(Text)
    impacto = Column(Text)
    metodo_analisis = Column(String(50))
    
    causa_inmediata = Column(Text)
    causa_raiz = Column(Text)
    causas_contribuyentes = Column(Text)
    
    acciones_correctivas = Column(Text)
    acciones_preventivas = Column(Text)
    
    responsable = Column(String(100))
    area_responsable = Column(String(100))
    fecha_compromiso = Column(Date)
    fecha_cierre = Column(Date)
    
    estado = Column(Enum('Abierto', 'En Análisis', 'En Implementación', 'Cerrado', 'Cancelado'), default='Abierto')
    criticidad = Column(Enum('Crítica', 'Alta', 'Media', 'Baja'), default='Media')
    
    tipo_falla = Column(String(100))
    categoria = Column(String(100))
    
    tiempo_parada_horas = Column(DECIMAL(10, 2))
    costo_estimado = Column(DECIMAL(15, 2))
    
    verificacion_efectividad = Column(Text)
    fecha_verificacion = Column(Date)
    efectivo = Column(Boolean)
    
    creado_por = Column(String(100))
    modificado_por = Column(String(100))
    
    # Relaciones
    cinco_porques_rel = relationship("CincoPorques", back_populates="rca", cascade="all, delete-orphan")
    ishikawa_rel = relationship("Ishikawa", back_populates="rca", cascade="all, delete-orphan")


class CincoPorques(Base):
    __tablename__ = "cinco_porques"
    
    id = Column(Integer, primary_key=True)
    rca_id = Column(Integer, ForeignKey('rcas.id', ondelete='CASCADE'), nullable=False)
    nivel = Column(Integer, nullable=False)
    porque = Column(Text, nullable=False)
    respuesta = Column(Text)
    
    # Relación
    rca = relationship("RCA", back_populates="cinco_porques_rel")


class Ishikawa(Base):
    __tablename__ = "ishikawa"
    
    id = Column(Integer, primary_key=True)
    rca_id = Column(Integer, ForeignKey('rcas.id', ondelete='CASCADE'), nullable=False)
    categoria = Column(String(50), nullable=False)
    causa = Column(Text, nullable=False)
    sub_causa = Column(Text)
    
    # Relación
    rca = relationship("RCA", back_populates="ishikawa_rel")


class Archivo(Base):
    __tablename__ = "archivos"
    
    id = Column(Integer, primary_key=True)
    rca_id = Column(Integer, ForeignKey('rcas.id', ondelete='CASCADE'), nullable=False)
    nombre_archivo = Column(String(255), nullable=False)
    ruta_archivo = Column(String(500), nullable=False)
    tipo_archivo = Column(String(50))
    tipo_contenido = Column(String(100))
    tamanio_kb = Column(Integer)
    fecha_subida = Column(DateTime, default=func.now())
    subido_por = Column(String(100))


class Accion(Base):
    __tablename__ = "acciones"
    
    id = Column(Integer, primary_key=True)
    rca_id = Column(Integer, ForeignKey('rcas.id', ondelete='CASCADE'), nullable=False)
    tipo = Column(Enum('Correctiva', 'Preventiva'), nullable=False)
    descripcion = Column(Text, nullable=False)
    responsable = Column(String(100))
    fecha_compromiso = Column(Date)
    fecha_completada = Column(Date)
    estado = Column(Enum('Pendiente', 'En Progreso', 'Completada', 'Vencida', 'Cancelada'), default='Pendiente')
    observaciones = Column(Text)


class Comentario(Base):
    __tablename__ = "comentarios"
    
    id = Column(Integer, primary_key=True)
    rca_id = Column(Integer, ForeignKey('rcas.id', ondelete='CASCADE'), nullable=False)
    usuario = Column(String(100))
    comentario = Column(Text, nullable=False)
    fecha = Column(DateTime, default=func.now())


class Usuario(Base):
    __tablename__ = "usuarios"
    
    id = Column(Integer, primary_key=True, index=True)
    nombre_usuario = Column(String(50), unique=True, nullable=False, index=True)
    nombre_completo = Column(String(100))
    email = Column(String(100), unique=True, nullable=False, index=True)
    password_hash = Column(String(255), nullable=False)
    rol = Column(String(50), nullable=False)  # 'Mantenedor', 'Supervisor', 'Gerente'
    area = Column(String(100))
    activo = Column(Boolean, default=True)
    fecha_creacion = Column(DateTime, default=func.now())
    ultimo_acceso = Column(DateTime)


class Equipo(Base):
    __tablename__ = "equipos"
    
    id = Column(Integer, primary_key=True)
    codigo_equipo = Column(String(50), unique=True, nullable=False)
    nombre = Column(String(200), nullable=False)
    descripcion = Column(Text)
    area = Column(String(100))
    planta = Column(String(100))
    sistema = Column(String(100))
    fabricante = Column(String(100))
    modelo = Column(String(100))
    criticidad = Column(Enum('A', 'B', 'C'))
    activo = Column(Boolean, default=True)