# RCA - Sistema de Análisis de Causa Raíz

Sistema de gestión de RCA (Root Cause Analysis) para operaciones industriales con análisis 5 Porqués y Diagrama de Ishikawa.

## 🚀 Características

- ✅ Gestión completa de RCAs
- 📊 Análisis 5 Porqués
- 🐟 Diagrama de Ishikawa
- 📸 Gestión de archivos y evidencias fotográficas
- 📈 Estadísticas y reportes
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
cd Proyecto_RCA
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
Editar el archivo `backend/.env` con tus datos:
```env
DB_HOST=localhost
DB_PORT=3306
DB_USER=root
DB_PASSWORD=tu_password
DB_NAME=rca_database

SERVER_HOST=0.0.0.0
SERVER_PORT=8000

ARCHIVOS_PATH=C:/ruta/completa/al/proyecto/archivos
RESPALDOS_PATH=C:/ruta/completa/al/proyecto/respaldos
```

5. **Crear base de datos:**
```sql
CREATE DATABASE rca_database CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
```

## ▶️ Ejecución

### Opción 1: Usando start_server.bat (Windows)
```bash
start_server.bat
```

### Opción 2: Manual
```bash
cd backend
python main.py
```

El servidor estará disponible en:
- API: http://192.168.38.14:8000
- Documentación: http://192.168.38.14:8000/docs

## 📁 Estructura del Proyecto

```
Proyecto_RCA/
├── backend/
│   ├── main.py              # Punto de entrada principal
│   ├── models.py            # Modelos de base de datos
│   ├── schemas.py           # Esquemas Pydantic
│   ├── crud.py              # Operaciones CRUD
│   ├── database.py          # Configuración BD
│   ├── config.py            # Configuración
│   ├── routers/             # Endpoints organizados
│   │   ├── rca.py
│   │   ├── archivos.py
│   │   └── reportes.py
│   └── utils/               # Utilidades
├── archivos/                # Archivos subidos
│   ├── fotos/
│   ├── pdfs/
│   └── evidencias/
└── requirements.txt
```

## 🔌 API Endpoints

### RCA
- `POST /rca` - Crear RCA
- `GET /rca` - Listar RCAs
- `GET /rca/{id}` - Obtener RCA
- `PUT /rca/{id}` - Actualizar RCA
- `DELETE /rca/{id}` - Eliminar RCA

### Archivos
- `POST /archivo/upload` - Subir archivo
- `GET /archivo?rca_id={id}` - Listar archivos
- `GET /archivos/fotos/{filename}` - Descargar archivo

### Análisis
- `POST /cinco-porques` - Agregar 5 porqués
- `GET /cinco-porques/{rca_id}` - Obtener 5 porqués
- `POST /ishikawa` - Agregar causa Ishikawa
- `GET /ishikawa/{rca_id}` - Obtener Ishikawa

### Reportes
- `GET /estadisticas/resumen` - Estadísticas generales
- `GET /reportes/por-area` - Estadísticas por área
- `GET /reportes/rca/{id}/pdf` - Generar PDF

## 🛠️ Tecnologías

- **Backend:** FastAPI
- **Base de datos:** MySQL + SQLAlchemy
- **PDF:** ReportLab
- **Validación:** Pydantic

## 📝 Notas

- Las imágenes se sirven a través de `/archivos/`
- Los archivos se almacenan con timestamp único
- CORS habilitado para conexiones desde tablets
- El servidor escucha en todas las interfaces (0.0.0.0)

## 🤝 Contribuciones

Proyecto desarrollado para gestión industrial de análisis de causa raíz.

## 📄 Licencia

Uso interno - Todos los derechos reservados
