# RCA - Sistema de Análisis de Causa Raíz

Sistema de gestión de RCA (Root Cause Analysis) para operaciones industriales con análisis 5 Porqués y Diagrama de Ishikawa.

## 🚀 Características

- ✅ Gestión completa de RCAs
- 🔐 Autenticación JWT con roles (Mantenedor, Supervisor, Gerente)
- 📊 Análisis 5 Porqués
- 🐟 Diagrama de Ishikawa
- 📸 Gestión de archivos y evidencias fotográficas
- 📈 Estadísticas y reportes PDF
- 📱 Diseñado para tablets industriales
- 🗄️ Base de datos MySQL

## 📋 Requisitos

- Python 3.8+
- MySQL 5.7+
- pip

## 🔧 Instalación

1. **Clonar el repositorio:**
```bash
git clone <url-del-repositorio>
cd RCA_Confiabilidad
```

2. **Crear entorno virtual:**
```bash
python -m venv venv
venv\Scripts\activate  # Windows
# source venv/bin/activate  # Linux/Mac
```

3. **Instalar dependencias:**
```bash
pip install -r requirements.txt
```

4. **Configurar variables de entorno:**

Copiar `backend/.env.example` a `backend/.env` y editar con tus datos.

5. **Crear base de datos:**
```sql
CREATE DATABASE rca_database CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
```

## ▶️ Ejecución

### Desarrollo
```bash
cd backend
python main.py
```

### Producción (servicio de Windows con NSSM)
```cmd
instalar.bat            :: instala dependencias y crea backend/.env
instalar_servicio.bat   :: registra y arranca el servicio RCAService (como Administrador)
```

- **API:** http://localhost:8007
- **Documentación Swagger:** http://localhost:8007/docs
- **Health-check:** http://localhost:8007/health

> 📖 Ver [Guía del Backend](backend/GUIA_BACKEND.md) para autenticación, roles y endpoints.
> 📖 Ver [Servicio de Windows](SERVICIO_WINDOWS.md) para despliegue permanente con NSSM.

## 📁 Estructura del Proyecto

```
RCA_Confiabilidad/
├── backend/
│   ├── main.py              # Punto de entrada (app FastAPI)
│   ├── config.py            # Configuración + .env (rutas absolutas)
│   ├── database.py          # Engine/pool SQLAlchemy
│   ├── models.py            # Modelos ORM
│   ├── schemas.py           # Esquemas Pydantic
│   ├── crud.py              # Operaciones CRUD
│   ├── .env.example         # Plantilla de variables de entorno
│   ├── GUIA_BACKEND.md      # Documentación del backend
│   ├── routers/
│   │   ├── auth.py          # Autenticación JWT
│   │   ├── rca.py           # CRUD de RCAs (protegido)
│   │   ├── archivos.py      # Upload/listar archivos (protegido)
│   │   └── reportes.py      # Reportes/estadísticas (protegido)
│   └── utils/
│       └── pdf_generator.py # Generación de PDF con ReportLab
├── archivos/                # Archivos subidos (servidos en /archivos)
│   ├── fotos/
│   ├── pdfs/
│   └── evidencias/
├── logs/                    # Logs del servicio NSSM (stdout/stderr)
├── requirements.txt
├── instalar.bat             # Instalación de dependencias
├── start_server.bat         # Arranque en modo desarrollo
├── instalar_servicio.bat    # Registro del servicio Windows (NSSM)
└── SERVICIO_WINDOWS.md      # Guía de despliegue con NSSM
```

## 🔌 API Endpoints

### Autenticación (`/auth`)
- `POST /auth/login` — Login (obtener token JWT)
- `POST /auth/registro` — Registrar usuario
- `GET /auth/me` — Ver perfil actual
- `GET /auth/usuarios` — Listar usuarios (admin)

### RCA (`/rca`)
- `POST /rca` — Crear RCA (incluye 5 porqués e Ishikawa)
- `GET /rca` — Listar RCAs
- `GET /rca/{id}` — Obtener RCA completo
- `PUT /rca/{id}` — Actualizar RCA
- `DELETE /rca/{id}` — Eliminar RCA

### Archivos (`/archivo`)
- `POST /archivo/upload` — Subir archivo
- `GET /archivo/{rca_id}` — Listar archivos de un RCA

### Reportes (`/reportes`)
- `GET /reportes/estadisticas` — Resumen estadístico
- `GET /reportes/por-area` — Por área
- `GET /reportes/por-criticidad` — Por criticidad
- `GET /reportes/rca/{id}/pdf` — Generar PDF

## 🛠️ Tecnologías

- **Backend:** FastAPI + Uvicorn
- **Base de datos:** MySQL + SQLAlchemy
- **Autenticación:** JWT (python-jose) + bcrypt
- **PDF:** ReportLab
- **Validación:** Pydantic

## 📄 Licencia

Uso interno — Todos los derechos reservados
