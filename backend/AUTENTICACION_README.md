# Sistema de Autenticación JWT - RCA

## 📋 Resumen de Implementación

Se ha implementado un sistema completo de autenticación JWT para la aplicación RCA con los siguientes componentes:

### ✅ Archivos Creados/Modificados

1. **`models.py`** - Modelo Usuario actualizado
2. **`schemas.py`** - Schemas de autenticación agregados
3. **`routers/auth.py`** - Router de autenticación (NUEVO)
4. **`main.py`** - Router incluido en la aplicación
5. **`requirements.txt`** - Dependencias agregadas (NUEVO)
6. **`scripts/crear_usuarios.py`** - Script para usuarios iniciales (NUEVO)

---

## 🚀 Instalación

### 1. Instalar dependencias

```bash
pip install -r requirements.txt
```

### 2. Configurar variable de entorno (Importante para producción)

En tu archivo `.env`, agrega:

```env
SECRET_KEY=tu-clave-secreta-muy-segura-y-larga-para-jwt-tokens
```

### 3. Actualizar la base de datos

El modelo Usuario ha cambiado, ejecuta las migraciones o recrea las tablas:

```bash
# Si usas Alembic
alembic revision --autogenerate -m "Update usuario model"
alembic upgrade head

# O simplemente reinicia el servidor para que cree las tablas
python main.py
```

### 4. Crear usuarios iniciales

```bash
cd backend
python scripts/crear_usuarios.py
```

---

## 👥 Usuarios Iniciales

El script crea 3 usuarios de prueba:

| Rol | Email | Contraseña | Nombre |
|-----|-------|------------|--------|
| Mantenedor | mantenedor@puerto.cl | mantenedor123 | Juan Pérez |
| Supervisor | supervisor@puerto.cl | supervisor123 | María González |
| Gerente | gerente@puerto.cl | gerente123 | Carlos Rodríguez |

---

## 🔐 Endpoints de Autenticación

### 1. Login (POST /auth/login)

**Request:**
```bash
curl -X POST "http://192.168.38.14:8000/auth/login" \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "username=mantenedor@puerto.cl&password=mantenedor123"
```

**Response:**
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer",
  "usuario": {
    "id": 1,
    "nombre": "Juan Pérez",
    "email": "mantenedor@puerto.cl",
    "rol": "Mantenedor",
    "area": "Mantenimiento Mecánico"
  }
}
```

### 2. Obtener Usuario Actual (GET /auth/me)

**Request:**
```bash
curl -X GET "http://192.168.38.14:8000/auth/me" \
  -H "Authorization: Bearer TU_TOKEN_AQUI"
```

**Response:**
```json
{
  "id": 1,
  "email": "mantenedor@puerto.cl",
  "nombre_completo": "Juan Pérez",
  "rol": "Mantenedor",
  "area": "Mantenimiento Mecánico",
  "nombre_usuario": "mantenedor1",
  "activo": true,
  "fecha_creacion": "2024-10-27T15:30:00"
}
```

### 3. Logout (POST /auth/logout)

```bash
curl -X POST "http://192.168.38.14:8000/auth/logout" \
  -H "Authorization: Bearer TU_TOKEN_AQUI"
```

---

## 💻 Uso desde el Frontend

### Login desde React/Next.js

```javascript
// Login
const login = async (email, password) => {
  const formData = new FormData();
  formData.append('username', email);  // OAuth2 usa 'username'
  formData.append('password', password);
  
  const response = await fetch('http://192.168.38.14:8000/auth/login', {
    method: 'POST',
    body: formData
  });
  
  const data = await response.json();
  
  if (response.ok) {
    // Guardar token
    localStorage.setItem('token', data.access_token);
    localStorage.setItem('usuario', JSON.stringify(data.usuario));
    return data;
  } else {
    throw new Error(data.detail);
  }
};

// Obtener usuario actual
const getCurrentUser = async () => {
  const token = localStorage.getItem('token');
  
  const response = await fetch('http://192.168.38.14:8000/auth/me', {
    headers: {
      'Authorization': `Bearer ${token}`
    }
  });
  
  return await response.json();
};

// Llamadas protegidas
const fetchProtected = async (url, options = {}) => {
  const token = localStorage.getItem('token');
  
  return fetch(url, {
    ...options,
    headers: {
      ...options.headers,
      'Authorization': `Bearer ${token}`
    }
  });
};
```

### Ejemplo de Componente de Login

```javascript
import { useState } from 'react';

export default function LoginForm() {
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState('');

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError('');
    
    try {
      const formData = new FormData();
      formData.append('username', email);
      formData.append('password', password);
      
      const response = await fetch('http://192.168.38.14:8000/auth/login', {
        method: 'POST',
        body: formData
      });
      
      const data = await response.json();
      
      if (response.ok) {
        localStorage.setItem('token', data.access_token);
        localStorage.setItem('usuario', JSON.stringify(data.usuario));
        window.location.href = '/dashboard';
      } else {
        setError(data.detail);
      }
    } catch (err) {
      setError('Error de conexión');
    }
  };

  return (
    <form onSubmit={handleSubmit}>
      <input 
        type="email" 
        value={email}
        onChange={(e) => setEmail(e.target.value)}
        placeholder="Email"
        required
      />
      <input 
        type="password" 
        value={password}
        onChange={(e) => setPassword(e.target.value)}
        placeholder="Contraseña"
        required
      />
      {error && <p className="error">{error}</p>}
      <button type="submit">Iniciar Sesión</button>
    </form>
  );
}
```

---

## 🔒 Proteger Endpoints

Para proteger endpoints existentes, agrega la dependencia de autenticación:

```python
from routers.auth import oauth2_scheme
from jose import JWTError, jwt
from fastapi import Depends, HTTPException, status

async def get_current_user(
    token: str = Depends(oauth2_scheme),
    db: Session = Depends(get_db)
):
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
    
    return usuario

# Usar en endpoints
@app.post("/rca")
async def crear_rca(
    rca: RCACreate, 
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user)  # PROTEGIDO
):
    # Solo usuarios autenticados pueden acceder
    rca.creado_por = current_user.nombre_completo
    # ... resto del código
```

---

## 📝 Notas Importantes

1. **Token expira en 24 horas** - Configurable en `ACCESS_TOKEN_EXPIRE_MINUTES`
2. **SECRET_KEY** - Cambiar en producción en el archivo `.env`
3. **HTTPS** - En producción usar HTTPS para enviar tokens de forma segura
4. **Refresh tokens** - Actualmente no implementados, agregar si es necesario

---

## 🧪 Probar con Swagger

1. Inicia el servidor: `python main.py`
2. Abre: http://192.168.38.14:8000/docs
3. Ve a `/auth/login` y haz click en "Try it out"
4. Ingresa credenciales de prueba
5. Copia el `access_token` de la respuesta
6. Click en "Authorize" (candado) arriba a la derecha
7. Pega el token
8. Ahora puedes probar endpoints protegidos

---

## ✅ Checklist de Implementación

- [x] Modelo Usuario actualizado
- [x] Schemas de autenticación
- [x] Router de autenticación
- [x] JWT tokens implementados
- [x] Passwords hasheados con bcrypt
- [x] Endpoints de login y me
- [x] Script de usuarios iniciales
- [x] Sistema de roles y permisos implementado
- [x] Protección de endpoints por rol (Supervisor/Gerente)
- [x] Endpoint de registro protegido
- [ ] Implementar en frontend
- [ ] Proteger endpoints existentes de RCA
- [ ] Configurar SECRET_KEY en producción

---

## 🆘 Troubleshooting

### Error: "No module named 'jose'"
```bash
pip install python-jose[cryptography]
```

### Error: "No module named 'passlib'"
```bash
pip install passlib[bcrypt]
```

### Error: "No module named 'email_validator'"
```bash
pip install email-validator
```

### Token inválido
- Verifica que el SECRET_KEY sea el mismo
- Verifica que el token no haya expirado
- Verifica el formato: `Bearer TOKEN`

---

¡Sistema de autenticación listo para usar! 🎉
