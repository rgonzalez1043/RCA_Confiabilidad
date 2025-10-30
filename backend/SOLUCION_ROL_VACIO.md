# ✅ Solución: Rol Vacío en Swagger

## 🔍 Problema Identificado

Cuando creabas usuarios desde Swagger, el campo `rol` llegaba vacío (`""`) a la base de datos, aunque el campo existía en la tabla.

**Causa:** El schema `UsuarioCreate` permitía strings vacíos en el campo `rol`.

---

## ✅ Solución Implementada

### 1. **Enum de Roles** (schemas.py)

Se creó un Enum para los roles válidos:

```python
class RolUsuario(str, Enum):
    MANTENEDOR = "Mantenedor"
    SUPERVISOR = "Supervisor"
    GERENTE = "Gerente"
```

### 2. **Validación en el Schema**

Se agregó validación con `Field` y el Enum:

```python
class UsuarioBase(BaseModel):
    email: EmailStr
    nombre_completo: str = Field(..., min_length=3, description="Nombre completo del usuario")
    rol: RolUsuario = Field(..., description="Rol del usuario en el sistema")  # ✅ Ahora es Enum
    area: Optional[str] = Field(None, description="Área de trabajo del usuario")

class UsuarioCreate(UsuarioBase):
    password: str = Field(..., min_length=6, description="Contraseña (mínimo 6 caracteres)")
    nombre_usuario: str = Field(..., min_length=3, description="Nombre de usuario único")
```

### 3. **Actualización del Endpoint**

El endpoint ahora usa `.value` del Enum:

```python
nuevo_usuario = Usuario(
    nombre_usuario=usuario_data.nombre_usuario,
    nombre_completo=usuario_data.nombre_completo,
    email=usuario_data.email,
    password_hash=get_password_hash(usuario_data.password),
    rol=usuario_data.rol.value,  # ✅ Obtiene el string del Enum
    area=usuario_data.area,
    activo=True
)
```

---

## 🎯 Beneficios de la Solución

### ✅ En Swagger:

1. **Dropdown con opciones** - El campo `rol` ahora muestra un select con 3 opciones:
   - Mantenedor
   - Supervisor
   - Gerente

2. **Campo obligatorio** - No se puede dejar vacío

3. **Validación automática** - Solo acepta los valores permitidos

4. **Mejor documentación** - Cada campo tiene descripción

### ✅ En el Código:

1. **Validación estricta** - Pydantic valida automáticamente
2. **No más strings vacíos** - El Enum no permite valores vacíos
3. **Type safety** - El IDE detecta errores
4. **Mejor mantenibilidad** - Roles definidos en un solo lugar

---

## 🧪 Cómo Probarlo

### 1. **Reiniciar el servidor**

```bash
python main.py
```

### 2. **Ir a Swagger**

http://192.168.38.14:8000/docs

### 3. **Ir a POST /auth/registro**

Ahora verás que el campo `rol` es un **dropdown** con 3 opciones:

```
rol *  [Select]
  ▼ Mantenedor
    Supervisor
    Gerente
```

### 4. **Crear un usuario**

Completa todos los campos:

```json
{
  "email": "test@puerto.cl",
  "nombre_completo": "Usuario Prueba",
  "rol": "Mantenedor",  ← Seleccionar del dropdown
  "area": "Área de Prueba",
  "password": "prueba123",
  "nombre_usuario": "uprueba"
}
```

### 5. **Verificar en la base de datos**

Ahora el campo `rol` tendrá el valor correcto: `"Mantenedor"`, `"Supervisor"` o `"Gerente"`.

---

## 🔧 Para Usuarios Existentes con Rol Vacío

Los usuarios que ya tienen el rol vacío en la base de datos necesitan ser actualizados manualmente en phpMyAdmin:

```sql
-- Ver usuarios con rol vacío
SELECT id, nombre_completo, email, rol 
FROM usuarios 
WHERE rol = '' OR rol IS NULL;

-- Actualizar tu usuario
UPDATE usuarios 
SET rol = 'Supervisor' 
WHERE email = 'rgonzalez@stiport.com';

-- Actualizar otros usuarios según corresponda
UPDATE usuarios 
SET rol = 'Mantenedor' 
WHERE email = 'otro@usuario.com';
```

O usar el endpoint PUT /usuarios/{id} (si lo tienes habilitado):

```json
PUT /usuarios/2
{
  "rol": "Supervisor"
}
```

---

## 📋 Validaciones Agregadas

| Campo | Validación | Descripción |
|-------|------------|-------------|
| email | EmailStr | Debe ser email válido |
| nombre_completo | min_length=3 | Mínimo 3 caracteres |
| rol | Enum (obligatorio) | Solo: Mantenedor, Supervisor, Gerente |
| area | Opcional | Puede estar vacío |
| password | min_length=6 | Mínimo 6 caracteres |
| nombre_usuario | min_length=3 | Mínimo 3 caracteres |

---

## ✅ Resultado Final

**ANTES (Problema):**
```json
{
  "usuario": {
    "rol": ""  ❌ VACÍO
  }
}
```

**DESPUÉS (Solucionado):**
```json
{
  "usuario": {
    "rol": "Supervisor"  ✅ CORRECTO
  }
}
```

---

¡Problema resuelto directamente en el código del backend! 🎉
