@echo off
chcp 65001 >nul
title RCA - Instalación y Configuración
color 0A
cls

echo.
echo ========================================================
echo   RCA - INSTALACION AUTOMATICA
echo ========================================================
echo.

REM Obtener la carpeta donde está este .bat
set "PROJECT_DIR=%~dp0"
cd /d "%PROJECT_DIR%"

echo [1/5] Verificando Python...
python --version >nul 2>&1
if %ERRORLEVEL% neq 0 (
    echo.
    echo ERROR: Python no esta instalado o no esta en el PATH.
    echo Descarga Python desde: https://www.python.org/downloads/
    echo IMPORTANTE: Marca "Add Python to PATH" durante la instalacion.
    echo.
    pause
    exit /b 1
)
echo       OK - Python encontrado
echo.

echo [2/5] Creando entorno virtual...
if not exist "venv" (
    python -m venv venv
    echo       OK - Entorno virtual creado
) else (
    echo       OK - Entorno virtual ya existe
)
echo.

echo [3/5] Instalando dependencias...
call venv\Scripts\activate.bat
pip install -r requirements.txt --quiet
if %ERRORLEVEL% neq 0 (
    echo ERROR: Fallo la instalacion de dependencias.
    pause
    exit /b 1
)
echo       OK - Dependencias instaladas
echo.

echo [4/5] Configurando archivo .env...
if not exist "backend\.env" (
    copy "backend\.env.example" "backend\.env" >nul
    echo       OK - Archivo .env creado desde .env.example
    echo.
    echo ========================================================
    echo   IMPORTANTE: Edita backend\.env con tus datos reales:
    echo   - DB_PASSWORD = tu password de MySQL (XAMPP)
    echo   - SECRET_KEY  = una clave secreta larga
    echo ========================================================
    echo.
) else (
    echo       OK - Archivo .env ya existe
)
echo.

echo [5/5] Creando base de datos en MySQL (XAMPP)...
set "MYSQL_PATH=C:\xampp\mysql\bin\mysql.exe"
if exist "%MYSQL_PATH%" (
    "%MYSQL_PATH%" -u root -e "CREATE DATABASE IF NOT EXISTS rca_database CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;" 2>nul
    if %ERRORLEVEL% equ 0 (
        echo       OK - Base de datos rca_database lista
    ) else (
        echo       AVISO: No se pudo crear la BD automaticamente.
        echo       Crea manualmente: CREATE DATABASE rca_database CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
    )
) else (
    echo       AVISO: XAMPP MySQL no encontrado en ruta por defecto.
    echo       Asegurate de crear la BD manualmente.
)
echo.

echo ========================================================
echo   INSTALACION COMPLETADA
echo ========================================================
echo.
echo   Ahora edita backend\.env si es necesario y luego
echo   ejecuta: start_server.bat
echo.
pause
