# 🔐 Cómo Usar el Candado "Authorize" en Swagger

## 📖 Guía Visual Paso a Paso

---

## ✅ PASO 1: Hacer Login

1. Abre Swagger: http://192.168.38.14:8000/docs

2. Busca el endpoint **POST `/auth/login`**

3. Click en **"Try it out"**

4. Completa los datos:
   ```
   username: tu-email@puerto.cl    (tu email real)
   password: tu-contraseña          (tu contraseña)
   ```

5. Click en **"Execute"**

6. Verás una respuesta como esta:
   ```json
   {
     "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiJ0dS1lbWFpbEBwdWVydG8uY2wiLCJyb2wiOiJTdXBlcnZpc29yIiwiZXhwIjoxNzMwMDY5MzAwfQ.abc123...",
     "token_type": "bearer",
     "usuario": {
       "id": 1,
       "nombre": "Tu Nombre",
       "email": "tu-email@puerto.cl",
       "rol": "Supervisor",
       "area": "Confiabilidad"
     }
   }
   ```

7. **COPIA EL TOKEN** (el texto largo después de "access_token", sin las comillas)

---

## ✅ PASO 2: Autorizar con el Candado 🔒

1. En Swagger, busca el botón **"Authorize" 🔒** (arriba a la derecha)

2. Click en el candado

3. Se abrirá una ventana que dice:
   ```
   Available authorizations
   
   oauth2 (OAuth2PasswordBearer)
   
   Value:
   [                                    ]
   ```

4. **PEGA EL TOKEN** que copiaste (solo el token, sin "Bearer")
   ```
   eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiJ0dS1lbWFpbEBwdWVydG8uY2wiLCJyb2wiOiJTdXBlcnZpc29yIiwiZXhwIjoxNzMwMDY5MzAwfQ.abc123...
   ```

5. Click en **"Authorize"**

6. Verás un mensaje: "Authorized ✓"

7. Click en **"Close"**

---

## ✅ PASO 3: Ahora ESTÁS AUTENTICADO ✓

Ahora el candado 🔒 aparecerá **cerrado** y podrás usar todos los endpoints protegidos.

### Endpoints que ahora puedes usar:

#### 🟢 Disponibles para TODOS los usuarios autenticados:

- **GET `/auth/me`** - Ver tu información de perfil

#### 🟡 Disponibles SOLO para Supervisores y Gerentes:

- **POST `/auth/registro`** - Crear nuevos usuarios
- **GET `/auth/usuarios`** - Ver lista de todos los usuarios

---

## 🧪 PASO 4: Probar Crear un Usuario

1. Busca **POST `/auth/registro`**

2. Click en **"Try it out"**

3. Completa los datos del nuevo usuario:
   ```json
   {
     "email": "mantenedor@puerto.cl",
     "nombre_completo": "Pedro López",
     "rol": "Mantenedor",
     "area": "Mantenimiento Eléctrico",
     "password": "mantenedor123",
     "nombre_usuario": "plopez"
   }
   ```

4. Click en **"Execute"**

5. Si todo está bien, verás:
   ```json
   {
     "id": 2,
     "email": "mantenedor@puerto.cl",
     "nombre_completo": "Pedro López",
     "rol": "Mantenedor",
     "area": "Mantenimiento Eléctrico",
     "nombre_usuario": "plopez",
     "activo": true,
     "fecha_creacion": "2024-10-27T15:45:00"
   }
   ```

   ✅ **USUARIO CREADO CORRECTAMENTE**

---

## ⚠️ Posibles Errores y Soluciones

### 🔴 Error 401: "Not authenticated"

**Mensaje:**
```json
{
  "detail": "Not authenticated"
}
```

**Causa:** No usaste el candado Authorize o el token expiró (24 horas)

**Solución:** 
1. Haz login nuevamente
2. Copia el nuevo token
3. Usa el candado Authorize

---

### 🔴 Error 403: "No tienes permisos"

**Mensaje:**
```json
{
  "detail": "No tienes permisos. Solo Supervisor y Gerente pueden realizar esta acción."
}
```

**Causa:** Tu rol es "Mantenedor" y estás intentando crear usuarios

**Solución:** Solo Supervisores y Gerentes pueden crear usuarios. Si eres Mantenedor, pide a un Supervisor que te cree la cuenta.

---

### 🔴 Error 400: "El email ya está registrado"

**Mensaje:**
```json
{
  "detail": "El email ya está registrado"
}
```

**Causa:** Ya existe un usuario con ese email

**Solución:** Usa un email diferente

---

## 📱 Flujo Completo Visual

```
┌─────────────────────────────────────────────┐
│  1. POST /auth/login                        │
│     username: tu-email@puerto.cl            │
│     password: tu-contraseña                 │
└─────────────────┬───────────────────────────┘
                  │
                  ▼
         ┌────────────────┐
         │  Obtienes TOKEN │
         └────────┬───────┘
                  │
                  ▼
┌─────────────────────────────────────────────┐
│  2. Click en Candado 🔒 Authorize           │
│     Pegar TOKEN                             │
│     Click "Authorize"                       │
└─────────────────┬───────────────────────────┘
                  │
                  ▼
         ┌─────────────────┐
         │  AUTENTICADO ✓   │
         └────────┬────────┘
                  │
                  ▼
┌─────────────────────────────────────────────┐
│  3. Ahora puedes usar endpoints protegidos  │
│     - POST /auth/registro (crear usuarios)  │
│     - GET /auth/me (ver tu perfil)          │
│     - GET /auth/usuarios (listar usuarios)  │
└─────────────────────────────────────────────┘
```

---

## 🎯 Resumen de Permisos

| Rol | Crear Usuarios | Ver Lista Usuarios | Ver Perfil Propio |
|-----|----------------|-------------------|-------------------|
| **Gerente** | ✅ Sí | ✅ Sí | ✅ Sí |
| **Supervisor** | ✅ Sí | ✅ Sí | ✅ Sí |
| **Mantenedor** | ❌ No | ❌ No | ✅ Sí |

---

## 💡 Consejos Importantes

1. ✅ **El token expira en 24 horas** - Tendrás que hacer login nuevamente cada día

2. ✅ **Guarda el token de forma segura** - No lo compartas con nadie

3. ✅ **El candado debe estar cerrado 🔒** - Cuando está abierto, no estás autenticado

4. ✅ **Puedes "Logout" en el candado** - Click en candado → "Logout" → candado se abre

5. ✅ **Si cambias de usuario** - Haz logout primero, luego login con el nuevo usuario

---

## ✅ Checklist Rápido

- [ ] 1. Hice login y copié el token
- [ ] 2. Usé el candado Authorize
- [ ] 3. Pegué el token (sin "Bearer")
- [ ] 4. Click en Authorize
- [ ] 5. El candado está cerrado 🔒
- [ ] 6. Ahora puedo crear usuarios

---

¡Listo! Ahora puedes crear usuarios de forma segura. Solo tú como Supervisor tienes acceso. 🎉
