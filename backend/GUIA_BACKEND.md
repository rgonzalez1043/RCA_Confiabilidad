# Guía del Backend - Sistema RCA

## Instalación

### 1. Instalar dependencias
```bash
cd backend
pip install -r requirements.txt
```

### 2. Configurar variables de entorno
Copiar `.env.example` a `.env` y editar con tus datos:
```env
DB_HOST=localhost
DB_PORT=3306
DB_USER=root
DB_PASSWORD=tu_password
DB_NAME=rca_database
SERVER_HOST=0.0.0.0
SERVER_PORT=8000
SECRET_KEY=tu-clave-secreta-segura-minimo-32-caracteres
ARCHIVOS_PATH=C:/ruta/al/proyecto/archivos
RESPALDOS_PATH=C:/ruta/al/proyecto/respaldos
```

### 3. Crear base de datos
```sql
CREATE DATABASE rca_database CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
```

### 4. Iniciar servidor
```bash
python main.py
```
El servidor crea las tablas automáticamente al iniciar.

---

## Primer Uso — Crear Usuario Administrador

El sistema detecta automáticamente si hay usuarios:
- **Sin usuarios (0)** → Permite crear el primer usuario **sin autenticación**
- **Con usuarios (1+)** → Requiere autenticación y permisos de Supervisor/Gerente

### Pasos:

1. Ir a Swagger: `http://<IP_SERVIDOR>:8000/docs`
2. Buscar **POST `/auth/registro`** → "Try it out"
3. Crear tu usuario (recomendado rol **Gerente**):

```json
{
  "email": "tu-email@ejemplo.com",
  "nombre_completo": "Tu Nombre",
  "rol": "Gerente",
  "area": "Tu Área",
  "password": "tuPasswordSegura123",
  "nombre_usuario": "tunombre"
}
```

4. Click en "Execute" — el primer usuario se crea sin necesidad de token.

---

## Autenticación JWT

### Login

**POST `/auth/login`** con:
```
username: tu-email@ejemplo.com
password: tu-contraseña
```

Respuesta:
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIs...",
  "token_type": "bearer",
  "usuario": {
    "id": 1,
    "nombre": "Tu Nombre",
    "email": "tu-email@ejemplo.com",
    "rol": "Gerente",
    "area": "Tu Área"
  }
}
```

### Usar token en Swagger

1. Copiar el `access_token` de la respuesta
2. Click en el **candado 🔒 "Authorize"** (arriba a la derecha)
3. Pegar **solo el token** (sin "Bearer")
4. Click en "Authorize" → "Close"
5. Ahora todos los endpoints protegidos están disponibles

> **Nota:** El token expira en 24 horas. Si obtienes error 401, haz login nuevamente.

### Uso desde Flutter/Frontend

```javascript
// Login
const formData = new FormData();
formData.append('username', email);
formData.append('password', password);
const res = await fetch('http://<IP>:8000/auth/login', { method: 'POST', body: formData });
const data = await res.json();
localStorage.setItem('token', data.access_token);

// Llamadas autenticadas
const token = localStorage.getItem('token');
const res = await fetch('http://<IP>:8000/rca', {
  headers: { 'Authorization': `Bearer ${token}` }
});
```

---

## Roles y Permisos

| Acción | Mantenedor | Supervisor | Gerente |
|---|:---:|:---:|:---:|
| Login | ✅ | ✅ | ✅ |
| Ver perfil propio | ✅ | ✅ | ✅ |
| CRUD de RCAs | ✅ | ✅ | ✅ |
| Crear usuarios | ❌ | ✅ | ✅ |
| Listar usuarios | ❌ | ✅ | ✅ |

---

## Endpoints de la API

### Autenticación (`/auth`)
| Método | Ruta | Descripción | Auth |
|---|---|---|:---:|
| POST | `/auth/login` | Login (obtener token) | ❌ |
| POST | `/auth/registro` | Registrar usuario | 🔒* |
| GET | `/auth/me` | Ver perfil actual | 🔒 |
| GET | `/auth/usuarios` | Listar usuarios | 🔒 Admin |
| POST | `/auth/logout` | Cerrar sesión | 🔒 |

*El primer usuario se crea sin autenticación.

### RCA (`/rca`)
| Método | Ruta | Descripción |
|---|---|---|
| POST | `/rca` | Crear nuevo RCA |
| GET | `/rca` | Listar RCAs (filtro opcional: `?estado=Abierto`) |
| GET | `/rca/{id}` | Obtener RCA con 5 porqués e Ishikawa |
| PUT | `/rca/{id}` | Actualizar RCA |
| DELETE | `/rca/{id}` | Eliminar RCA |
| POST | `/rca/{id}/cinco-porques` | Agregar análisis 5 porqués |
| GET | `/rca/{id}/cinco-porques` | Obtener 5 porqués |
| POST | `/rca/{id}/ishikawa` | Agregar causa Ishikawa |
| GET | `/rca/{id}/ishikawa` | Obtener Ishikawa |

### Archivos (`/archivo`)
| Método | Ruta | Descripción |
|---|---|---|
| POST | `/archivo/upload` | Subir archivo (foto, PDF) |
| GET | `/archivo/{rca_id}` | Listar archivos de un RCA |

### Reportes (`/reportes`)
| Método | Ruta | Descripción |
|---|---|---|
| GET | `/reportes/estadisticas` | Resumen estadístico |
| GET | `/reportes/por-area` | Estadísticas por área |
| GET | `/reportes/por-criticidad` | Estadísticas por criticidad |
| GET | `/reportes/rca/{id}/pdf` | Generar PDF de un RCA |

---

## Formatos de Datos

### Crear/Actualizar RCA con 5 Porqués e Ishikawa

```json
{
  "codigo": "RCA-2025-001",
  "titulo": "Falla en sensor",
  "fecha_evento": "2025-10-28T10:00:00",
  "area": "Mantenimiento",
  "equipo": "Spreader 86",
  "descripcion_falla": "Sensor no responde",
  "criticidad": "Alta",
  "cinco_porques": [
    "El sensor dejó de enviar señales",
    "El cable estaba dañado",
    "Falta de mantenimiento preventivo",
    "No hay programa de inspección",
    "Presupuesto insuficiente"
  ],
  "ishikawa": {
    "Equipo": ["Desgaste de componentes", "Falta de calibración"],
    "Mantenimiento": ["Mantenimiento atrasado"],
    "Operador": ["Falta de capacitación"]
  }
}
```

### Fechas
- Formato ISO 8601: `"2025-11-15"` (date) o `"2025-10-28T10:00:00"` (datetime)
- Desde Flutter: `fecha.toIso8601String().split('T')[0]`

---

## Troubleshooting

| Error | Causa | Solución |
|---|---|---|
| 401 "Not authenticated" | No usaste Authorize o token expirado | Hacer login y usar el candado |
| 403 "No tienes permisos" | Tu rol no tiene acceso | Solo Supervisor/Gerente pueden crear usuarios |
| 400 "Email ya registrado" | Email duplicado | Usar otro email |
| `ModuleNotFoundError: jose` | Dependencia faltante | `pip install python-jose[cryptography]` |
| `ModuleNotFoundError: passlib` | Dependencia faltante | `pip install passlib[bcrypt]` |
| Rol vacío en BD | Usuarios creados antes del fix | `UPDATE usuarios SET rol = 'Mantenedor' WHERE rol = '';` |
