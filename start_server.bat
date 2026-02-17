@echo off
chcp 65001 >nul
title RCA Server - Puerto 8007
color 0A
cls

echo.
echo ========================================
echo   RCA SERVER - INICIANDO...
echo ========================================
echo.

REM Obtener la carpeta donde está este .bat
set "PROJECT_DIR=%~dp0"
cd /d "%PROJECT_DIR%"

REM Activar entorno virtual
if exist "venv\Scripts\activate.bat" (
    call venv\Scripts\activate.bat
    echo   Entorno virtual: activado
) else (
    echo   AVISO: No hay entorno virtual.
    echo   Ejecuta primero: instalar.bat
    echo.
    pause
    exit /b 1
)

echo   Servidor: http://192.168.38.14:8007
echo   Swagger:  http://192.168.38.14:8007/docs
echo.
echo   Presione Ctrl+C para detener
echo.
echo ========================================
echo.

cd backend
python main.py

echo.
echo ========================================
echo   SERVIDOR DETENIDO
echo ========================================
echo.
pause