@echo off
REM Comprobaciones de solo lectura antes de actualizar; no detiene ni modifica nada.
powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0actualizar_servidor.ps1" -SoloVerificar %*
echo.
pause
