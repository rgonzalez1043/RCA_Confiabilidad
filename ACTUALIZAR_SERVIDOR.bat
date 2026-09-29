@echo off
REM Actualiza el backend RCA instalado como servicio. Ejecutar como Administrador.
powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0actualizar_servidor.ps1" %*
echo.
pause
