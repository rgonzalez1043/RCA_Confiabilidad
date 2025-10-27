# 🔐 Guía de Autorización y Permisos - Sistema RCA

## 📋 Sistema Implementado

Se ha implementado un **sistema de autenticación y autorización por roles** con los siguientes niveles:

### 👥 Roles y Permisos

| Rol | Permisos | Acciones |
|-----|----------|----------|
| **Gerente** | ✅ Admin completo | Crear usuarios, modificar RCAs, ver todo |
| **Supervisor** | ✅ Admin completo | Crear usuarios, modificar RCAs, ver todo |
| **Mantenedor** | ⚠️ Limitado | Crear y editar sus propios RCAs, ver RCAs |

---

## 🔒 Endpoints Protegidos

### ✅ Endpoints que REQUIEREN AUTENTICACIÓN:

1. **GET `/auth/me`** - Ver mi perfil
   - Requiere: Token válido
   - Cualquier usuario autenticado

2. **POST `/auth/registro`** - Crear nuevos usuarios
   - Requiere: Token válido + Rol Supervisor/Gerente
   - ❌ Mantenedores NO pueden crear usuarios

3. **GET `/auth/usuarios`** - Listar usuarios
   - Requiere: Token válido + Rol Supervisor/Gerente
   - ❌ Mantenedores NO pueden ver lista de usuarios

### 🌐 Endpoints PÚBLICOS (sin autenticación):

1. **POST `/auth/login`** - Login
   - No requiere autenticación previa

---

## 🔐 Cómo Usar el Candado "Authorize" en Swagger

### Paso 1: Login

1. Ve a http://192.168.38.14:8000/docs
2. Busca el endpoint **POST `/auth/login`**
3. Click en **"Try it out"**
4. Ingresa tus credenciales:
   ```
   username: tu-email@puerto.cl
   password: tu-contraseña
   ```
5. Click en **"Execute"**
6. **Copia el `access_token`** de la respuesta (sin las comillas)

### Paso 2: Autorizar

1. **Click en el candado 🔒 "Authorize"** (arriba a la derecha)
2. En el campo que aparece, pega SOLO el token (sin "Bearer")
   ```
   eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiJ...
   ```
3. Click en **"Authorize"**
4. Click en **"Close"**

### Paso 3: Usar Endpoints Protegidos

Ahora puedes usar cualquier endpoint protegido:
- **GET `/auth/me`** - Ver tu perfil
- **POST `/auth/registro`** - Crear usuarios (si eres Supervisor/Gerente)
- **GET `/auth/usuarios`** - Ver lista de usuarios (si eres Supervisor/Gerente)

---

## ⚠️ Mensajes de Error Comunes

### 🔴 Error 401 - Unauthorized
```json
{
  "detail": "Not authenticated"
}
```
**Solución**: No estás autenticado. Usa el candado "Authorize" con tu token.

### 🔴 Error 403 - Forbidden
```json
{
  "detail": "No tienes permisos. Solo Supervisor y Gerente pueden realizar esta acción."
}
```
**Solución**: Tu rol no tiene permisos. Solo Supervisores y Gerentes pueden crear usuarios.

### 🔴 Error 401 - Invalid credentials
```json
{
  "detail": "Email o contraseña incorrectos"
}
```
**Solución**: Verifica tu email y contraseña.

---

## 💡 Flujo Completo de Uso

### Para CREAR el Primer Usuario (Solo la primera vez):

Como ya creaste tu usuario Supervisor, ahora puedes:

1. **Login con tu usuario**:
   ```bash
   POST /auth/login
   username: tu-email@puerto.cl
   password: tu-contraseña
   ```

2. **Autorizar en Swagger** (candado 🔒)

3. **Crear nuevos usuarios**:
   ```bash
   POST /auth/registro
   {
     "email": "nuevo-usuario@puerto.cl",
     "nombre_completo": "Nuevo Usuario",
     "rol": "Mantenedor",
     "area": "Mantenimiento",
     "password": "password123",
     "nombre_usuario": "nusuario"
   }
   ```

---

## 🛡️ Proteger Otros Endpoints

Para proteger endpoints existentes (RCAs, archivos, etc.):

```python
from routers.auth import get_current_active_user, verificar_permiso_admin
from models import Usuario

# Endpoint que requiere autenticación
@app.post("/rca")
async def crear_rca(
    rca: RCACreate,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_active_user)  # ✅ Protegido
):
    # Solo usuarios autenticados
    rca.creado_por = current_user.nombre_completo
    # ... resto del código

# Endpoint que requiere permisos de admin
@app.delete("/rca/{rca_id}")
async def eliminar_rca(
    rca_id: int,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(verificar_permiso_admin)  # ✅ Solo Supervisor/Gerente
):
    # Solo supervisores y gerentes pueden eliminar
    # ... resto del código
```

---

## 📱 Uso desde Frontend (React/JavaScript)

### Login y Guardar Token

```javascript
// 1. Login
const login = async (email, password) => {
  const formData = new FormData();
  formData.append('username', email);
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
  }
};

// 2. Hacer llamadas autenticadas
const crearUsuario = async (nuevoUsuario) => {
  const token = localStorage.getItem('token');
  
  const response = await fetch('http://192.168.38.14:8000/auth/registro', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      'Authorization': `Bearer ${token}`  // ✅ Incluir token
    },
    body: JSON.stringify(nuevoUsuario)
  });
  
  if (response.status === 403) {
    alert('No tienes permisos para crear usuarios');
  }
  
  return await response.json();
};

// 3. Verificar rol del usuario
const puedeCrearUsuarios = () => {
  const usuario = JSON.parse(localStorage.getItem('usuario'));
  return ['Supervisor', 'Gerente'].includes(usuario.rol);
};
```

---

## 🎯 Recomendaciones de Seguridad

1. ✅ **Token expira en 24 horas** - El usuario debe hacer login nuevamente
2. ✅ **Contraseñas hasheadas** - No se guardan en texto plano
3. ✅ **Roles verificados en backend** - No se puede falsificar desde frontend
4. ⚠️ **Cambiar SECRET_KEY en producción** - Usar una clave segura única
5. ⚠️ **Usar HTTPS en producción** - Nunca HTTP para tokens

---

## ✅ Resumen Rápido

| Acción | ¿Quién puede? | ¿Requiere Auth? |
|--------|---------------|-----------------|
| Login | Todos | ❌ No |
| Ver mi perfil | Usuarios autenticados | ✅ Sí |
| Crear usuarios | Supervisor/Gerente | ✅ Sí + Rol |
| Listar usuarios | Supervisor/Gerente | ✅ Sí + Rol |
| Ver RCAs | Usuarios autenticados | ✅ Sí |
| Crear RCAs | Usuarios autenticados | ✅ Sí |
| Eliminar RCAs | Supervisor/Gerente | ✅ Sí + Rol |

---

¡Sistema de autorización implementado correctamente! 🎉

Como Supervisor, ahora puedes:
- ✅ Crear nuevos usuarios
- ✅ Ver lista de usuarios
- ✅ Modificar RCAs
- ✅ Tener control total del sistema
