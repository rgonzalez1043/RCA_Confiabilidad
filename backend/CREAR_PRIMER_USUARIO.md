# 🎯 Guía: Crear Primer Usuario y Configurar Sistema

## 📋 Sistema Implementado

El sistema ahora detecta automáticamente si hay usuarios en la base de datos:

- **🔓 Sin usuarios (0)** → Permite crear el PRIMER usuario SIN autenticación
- **🔒 Con usuarios (1+)** → REQUIERE autenticación y permisos de Supervisor/Gerente

---

## ✅ Paso 1: Limpiar Base de Datos

### Opción A: Desde phpMyAdmin

1. Ve a phpMyAdmin
2. Selecciona la base de datos `rca_database`
3. Ejecuta:

```sql
-- Ver usuarios actuales
SELECT * FROM usuarios;

-- Eliminar TODOS los usuarios
DELETE FROM usuarios;

-- Verificar que esté vacía
SELECT COUNT(*) FROM usuarios;  -- Debe mostrar: 0
```

### Opción B: Desde Swagger (si tienes el endpoint)

```
DELETE /usuarios/{id}  -- Desactivar cada usuario
```

---

## ✅ Paso 2: Reiniciar el Servidor

```bash
cd c:\Users\NUC_GRUAS\Desktop\Proyecto_RCA\backend
python main.py
```

Deberías ver:
```
INFO:     Uvicorn running on http://0.0.0.0:8000
```

---

## ✅ Paso 3: Crear TU Usuario (Gerente)

### 🌐 Ve a Swagger

http://192.168.38.14:8000/docs

### 🔓 NO uses el candado "Authorize"

Como NO hay usuarios, puedes crear directamente sin autenticación.

### 📝 Crear tu usuario

1. Ve a **POST `/auth/registro`**
2. Click en **"Try it out"**
3. Completa los datos:

```json
{
  "email": "rgonzalez@stiport.com",
  "nombre_completo": "Roberto González",
  "rol": "Gerente",
  "area": "Confiabilidad",
  "password": "tuPasswordSegura123",
  "nombre_usuario": "rgonzalez"
}
```

4. Click en **"Execute"**

### ✅ Respuesta Exitosa

```json
{
  "id": 1,
  "nombre_usuario": "rgonzalez",
  "email": "rgonzalez@stiport.com",
  "nombre_completo": "Roberto González",
  "rol": "Gerente",
  "area": "Confiabilidad",
  "activo": true,
  "fecha_creacion": "2025-10-27T17:48:00"
}
```

En la consola del servidor verás:
```
🔓 Creando PRIMER usuario del sistema (sin autenticación requerida)
✅ PRIMER USUARIO CREADO: Roberto González (rgonzalez@stiport.com) - Rol: Gerente
🔒 A partir de ahora se requerirá autenticación para crear más usuarios
```

---

## ✅ Paso 4: Hacer Login

Ahora que tu usuario existe, haz login:

1. Ve a **POST `/auth/login`**
2. Click en **"Try it out"**
3. Ingresa credenciales:

```
username: rgonzalez@stiport.com
password: tuPasswordSegura123
```

4. Click en **"Execute"**
5. **Copia el `access_token`** de la respuesta

---

## ✅ Paso 5: Autorizar en Swagger

1. Click en el **candado 🔒 "Authorize"** (arriba a la derecha)
2. Pega el token
3. Click en **"Authorize"**
4. Click en **"Close"**

---

## ✅ Paso 6: Crear Más Usuarios

Ahora que estás autenticado como Gerente, puedes crear más usuarios:

### Usuario de Mantenimiento

```json
{
  "email": "plopez@stiport.com",
  "nombre_completo": "Pedro López",
  "rol": "Mantenedor",
  "area": "Mantenimiento Eléctrico",
  "password": "password123",
  "nombre_usuario": "plopez"
}
```

### Usuario Supervisor

```json
{
  "email": "msanchez@stiport.com",
  "nombre_completo": "María Sánchez",
  "rol": "Supervisor",
  "area": "Operaciones",
  "password": "password123",
  "nombre_usuario": "msanchez"
}
```

---

## 🔒 Seguridad Implementada

### Primera Vez (Sin Usuarios)
```
POST /auth/registro
SIN candado Authorize ✅
→ Crea el primer usuario
```

### Siguientes Veces (Con Usuarios)
```
POST /auth/registro
CON candado Authorize 🔒 (obligatorio)
→ Solo Gerente/Supervisor pueden crear usuarios
```

---

## 🧪 Verificar que Funciona

### Test 1: Intentar crear sin autenticación (debe fallar)

1. Cierra sesión en Swagger (candado → Logout)
2. Intenta crear un usuario sin Authorize
3. Deberías ver error **401 Unauthorized**:

```json
{
  "detail": "Debes estar autenticado para crear usuarios. Usa el candado 'Authorize' en Swagger."
}
```

✅ **Esto es CORRECTO** - El sistema está protegido

### Test 2: Crear con autenticación (debe funcionar)

1. Haz login
2. Usa el candado Authorize con tu token
3. Crea un usuario
4. Debe funcionar ✅

---

## 📱 Para Usar desde Flutter

Una vez que tengas tu usuario Gerente creado:

```dart
// 1. Login (obtener token)
final loginResult = await authService.login(
  'rgonzalez@stiport.com',
  'tuPasswordSegura123',
);

// 2. Crear usuarios desde Flutter
final result = await authService.registrarUsuario(
  email: 'nuevo@stiport.com',
  nombreCompleto: 'Nuevo Usuario',
  rol: 'Mantenedor',
  password: 'password123',
  nombreUsuario: 'nusuario',
  area: 'Área',
);
```

---

## ⚠️ Importante

### Roles y Permisos

| Rol | Puede crear usuarios | Puede usar la app |
|-----|---------------------|-------------------|
| **Gerente** | ✅ Sí | ✅ Sí |
| **Supervisor** | ✅ Sí | ✅ Sí |
| **Mantenedor** | ❌ No | ✅ Sí |

### Recomendación

Para el **PRIMER usuario** (tú):
- ✅ Usar rol **"Gerente"**
- ✅ Contraseña segura
- ✅ Email real

---

## 🔄 Si Necesitas Reiniciar

Si en algún momento necesitas borrar todo y empezar de nuevo:

```sql
-- Eliminar todos los usuarios
DELETE FROM usuarios;

-- Reiniciar el auto-increment (opcional)
ALTER TABLE usuarios AUTO_INCREMENT = 1;
```

Luego el sistema permitirá crear el primer usuario sin autenticación nuevamente.

---

## ✅ Checklist Completo

- [ ] 1. Limpiar base de datos (eliminar usuarios)
- [ ] 2. Reiniciar servidor FastAPI
- [ ] 3. Ir a Swagger
- [ ] 4. Crear primer usuario (Gerente) SIN Authorize
- [ ] 5. Hacer login con ese usuario
- [ ] 6. Copiar token
- [ ] 7. Usar candado Authorize
- [ ] 8. Crear más usuarios (Mantenedores, Supervisores)
- [ ] 9. Probar login desde Flutter
- [ ] 10. ¡Listo para usar la aplicación!

---

¡Sistema configurado correctamente! 🎉
