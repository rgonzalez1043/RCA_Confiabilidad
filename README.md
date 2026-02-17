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

```bash
cd backend
python main.py
```

- **API:** http://localhost:8000
- **Documentación Swagger:** http://localhost:8000/docs

> 📖 Ver [Guía del Backend](backend/GUIA_BACKEND.md) para instrucciones detalladas de autenticación, roles, endpoints y troubleshooting.

## 📁 Estructura del Proyecto

```
RCA_Confiabilidad/
├── backend/
│   ├── main.py              # Punto de entrada principal
│   ├── models.py            # Modelos de base de datos
│   ├── schemas.py           # Esquemas Pydantic
│   ├── crud.py              # Operaciones CRUD
│   ├── database.py          # Configuración BD
│   ├── config.py            # Configuración
│   ├── GUIA_BACKEND.md      # Documentación del backend
│   ├── routers/
│   │   ├── auth.py          # Autenticación JWT
│   │   ├── rca.py           # CRUD de RCAs
│   │   ├── archivos.py      # Gestión de archivos
│   │   └── reportes.py      # Reportes y estadísticas
│   ├── scripts/
│   │   └── crear_usuarios.py
│   └── utils/
│       ├── pdf_generator.py
│       └── backup.py
├── archivos/                # Archivos subidos
│   ├── fotos/
│   ├── pdfs/
│   └── evidencias/
├── requirements.txt
└── start_server.bat
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
