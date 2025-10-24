@echo off
title RCA Server - Sistema de Confiabilidad
color 0A
cls
echo.
echo ========================================
echo   RCA SERVER - INICIANDO...
echo ========================================
echo.
echo Servidor: 192.168.38.14:8000
echo Documentacion: http://192.168.38.14:8000/docs
echo.
echo Presione Ctrl+C para detener el servidor
echo.
echo ========================================
echo.

cd /d C:\Users\NUC_GRUAS\Desktop\Proyecto_RCA\backend
python main.py

echo.
echo ========================================
echo   SERVIDOR DETENIDO
echo ========================================
echo.
pause
```

**Guardar el archivo.**

### **12.2 Probar el BAT manualmente**

1. **Detener el servidor actual** (Ctrl+C en el CMD donde corre)
2. **Doble click** en `start_server.bat`
3. **Verificar que el servidor arranca correctamente**
4. **Cerrar la ventana** (Ctrl+C)

---

### **12.3 Configurar Task Scheduler (Programador de Tareas)**

**Paso a paso DETALLADO:**

#### **1. Abrir Task Scheduler:**
- Windows ? Buscar: **"Programador de tareas"** o **"Task Scheduler"**

#### **2. Crear nueva tarea:**
- Panel derecho ? Click en: **"Crear tarea..."** (NO "Crear tarea básica")

#### **3. Pestaña "General":**
- **Nombre:** `RCA Server`
- **Descripción:** `Servidor API para Sistema RCA - Inicia automáticamente con Windows`
- **Opciones de seguridad:**
  - ? **IMPORTANTE:** Marcar "Ejecutar con los privilegios más altos"
  - Seleccionar: "Ejecutar tanto si el usuario inició sesión como si no"
- **Configurar para:** Windows 10

#### **4. Pestaña "Desencadenadores":**
- Click botón **"Nuevo..."**
- **Iniciar la tarea:** Seleccionar "Al iniciar"
- **Configuración avanzada:**
  - ? Habilitado
  - Retrasar la tarea: 1 minuto (opcional, para dar tiempo a que arranque Windows)
- Click **"Aceptar"**

#### **5. Pestaña "Acciones":**
- Click botón **"Nuevo..."**
- **Acción:** Iniciar un programa
- **Programa o script:** 
```
  C:\Users\NUC_GRUAS\Desktop\Proyecto_RCA\start_server.bat
```
- **Iniciar en (opcional):**
```
  C:\Users\NUC_GRUAS\Desktop\Proyecto_RCA\backend