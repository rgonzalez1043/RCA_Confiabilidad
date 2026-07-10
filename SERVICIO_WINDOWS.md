# 🚀 Desplegar RCA como Servicio de Windows con NSSM

Esta guía explica cómo dejar el backend RCA corriendo **permanentemente** como un servicio de Windows, de modo que arranque solo con el servidor y se reinicie ante caídas.

---

## 1. Requisitos previos

1. **Python 3.10+** instalado (marcado en el PATH).
2. **MySQL / MariaDB** corriendo (XAMPP o servicio propio).
3. La base de datos `rca_database` creada:
   ```sql
   CREATE DATABASE IF NOT EXISTS rca_database CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
   ```
4. Haber ejecutado una vez `instalar.bat` (crea `venv`, instala dependencias y genera `backend/.env`).

> 💡 Comprueba que el `.env` tenga la contraseña correcta de MySQL en `DB_PASSWORD`.

---

## 2. Descargar NSSM

NSSM = **Non-Sucking Service Manager**.

1. Descargar desde <https://nssm.cc/download> (usa la versión **win64**).
2. Descomprimir y copiar `nssm.exe` a una carpeta del PATH, por ejemplo:
   ```
   C:\Windows\System32\nssm.exe
   ```
   o junto al proyecto en `C:\Python Projects\RCA_Confiabilidad\nssm\nssm.exe`.

Verificar:
```cmd
nssm version
```

---

## 3. Instalación asistida (recomendado)

Ejecuta (como **Administrador**):

```cmd
instalar_servicio.bat
```

El script:
- Lee `backend\.env` para usar el mismo puerto configurado.
- Registra el servicio **`RCAService`** con NSSM.
- Aplica configuración de reinicio automático.
- Inicia el servicio.

---

## 4. Instalación manual con NSSM

Si prefieres hacerlo paso a paso:

```cmd
:: Variables (ajusta si tu proyecto está en otra ruta)
set PROJECT_DIR=C:\Python Projects\RCA_Confiabilidad
set VENV_PY=%PROJECT_DIR%\venv\Scripts\python.exe

:: Crear el servicio
nssm install RCAService "%VENV_PY%" "-m uvicorn main:app --host 0.0.0.0 --port 8007"

:: Directorio de trabajo (MUY IMPORTANTE: tiene que ser backend)
nssm set RCAService AppDirectory "%PROJECT_DIR%\backend"

:: Descripción
nssm set RCAService DisplayName "RCA - Sistema de Análisis de Causa Raíz"
nssm set RCAService Description "API FastAPI del sistema RCA"
nssm set RCAService Start SERVICE_AUTO_START

:: Reinicio automático si cae
nssm set RCAService AppStdout "%PROJECT_DIR%\logs\stdout.log"
nssm set RCAService AppStderr "%PROJECT_DIR%\logs\stderr.log"
nssm set RCAService AppRotateFiles 1
nssm set RCAService AppRotateBytes 10485760

nssm set RCAService AppExit Default Restart
nssm set RCAService AppRestartDelay 5000

:: Iniciar
nssm start RCAService
```

---

## 5. Verificar que está corriendo

```cmd
nssm status RCAService
```
Debe responder `SERVICE_RUNNING`.

Probar health-check:
```cmd
curl http://localhost:8007/health
```
Respuesta esperada:
```json
{"status":"healthy","database":"connected"}
```

Swagger UI: <http://localhost:8007/docs>

---

## 6. Comandos útiles

| Acción | Comando |
|---|---|
| Ver estado | `nssm status RCAService` |
| Iniciar | `nssm start RCAService` |
| Detener | `nssm stop RCAService` |
| Reiniciar | `nssm restart RCAService` |
| Editar config | `nssm edit RCAService` |
| Ver logs | `type logs\stdout.log` / `type logs\stderr.log` |
| Desinstalar | `nssm remove RCAService confirm` |

Desde PowerShell también sirve `Start-Service`, `Stop-Service`, `Restart-Service RCAService`.

---

## 7. Configuración de la red / Firewall

Para que las tablets puedan llegar al servidor:

1. **IP fija** del servidor (ej. `192.168.38.14`).
2. Abrir el puerto `8007` (TCP) en el Firewall de Windows:
   ```cmd
   netsh advfirewall firewall add rule name="RCA API 8007" dir=in action=allow protocol=TCP localport=8007
   ```
3. Desde la tablet, navegar a `http://192.168.38.14:8007/docs`.

---

## 8. Actualizar el código

1. Copiar los nuevos archivos del proyecto.
2. Reiniciar el servicio:
   ```cmd
   nssm restart RCAService
   ```

> No hace falta reinstalar dependencias salvo que cambie `requirements.txt`.

---

## 9. Troubleshooting

| Síntoma | Revisión |
|---|---|
| `SERVICE_STOPPED` inmediatamente | Revisar `logs\stderr.log` |
| `503 Database error` en `/health` | MySQL caído o `DB_PASSWORD` incorrecta en `.env` |
| El servicio arranca pero no responde | Conflicto de puerto (ver `netstat -ano \| findstr :8007`) |
| Tokens dejan de funcionar tras reinicio | Se borró/renovó `SECRET_KEY` del `.env` |
| `nssm` no se reconoce | `nssm.exe` no está en el PATH |

---

## 10. Migración a un Gestor de Procesos (opcional)

Si en el futuro prefieres no usar NSSM, alternativas válidas:
- **Windows Task Scheduler** al inicio.
- **pm2** (con `pm2 start "uvicorn main:app ..."`) + `pm2-windows-service`.
- **IIS + HttpPlatformHandler**.
- Contenedor Docker + `--restart unless-stopped`.

NSSM sigue siendo la opción más simple y liviana.