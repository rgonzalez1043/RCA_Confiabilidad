@echo off
chcp 65001 >nul
title RCA - Instalar Servicio de Windows (NSSM)
color 0B
cls

echo.
echo ========================================================
echo   RCA - INSTALACION DEL SERVICIO DE WINDOWS (NSSM)
echo ========================================================
echo.

REM ----------------------------------------------------------
REM Verificar privilegios de administrador
REM ----------------------------------------------------------
net session >nul 2>&1
if %ERRORLEVEL% neq 0 (
    echo  ERROR: Necesitas ejecutar este script como ADMINISTRADOR.
    echo         Click derecho ^> Ejecutar como administrador.
    echo.
    pause
    exit /b 1
)

REM ----------------------------------------------------------
REM Ubicar el proyecto
REM ----------------------------------------------------------
set "PROJECT_DIR=%~dp0"
set "PROJECT_DIR=%PROJECT_DIR:~0,-1%"
cd /d "%PROJECT_DIR%"

set "BACKEND_DIR=%PROJECT_DIR%\backend"
set "VENV_PY=%PROJECT_DIR%\venv\Scripts\python.exe"

echo  Proyecto : %PROJECT_DIR%
echo  Backend  : %BACKEND_DIR%
echo  Python   : %VENV_PY%
echo.

REM ----------------------------------------------------------
REM Verificar que existe el venv y python
REM ----------------------------------------------------------
if not exist "%VENV_PY%" (
    echo  ERROR: No se encontro el entorno virtual.
    echo         Ejecuta primero: instalar.bat
    echo.
    pause
    exit /b 1
)

REM ----------------------------------------------------------
REM Verificar NSSM
REM ----------------------------------------------------------
where nssm >nul 2>&1
if %ERRORLEVEL% neq 0 (
    if exist "%PROJECT_DIR%\nssm\nssm.exe" (
        set "PATH=%PROJECT_DIR%\nssm;%PATH%"
    ) else (
        echo  ERROR: NSSM no esta instalado.
        echo         Descarga nssm.exe desde https://nssm.cc/download
        echo         y copialo a C:\Windows\System32\ o a %PROJECT_DIR%\nssm\
        echo.
        pause
        exit /b 1
    )
)

echo  NSSM encontrado. OK.
echo.

REM ----------------------------------------------------------
REM Leer puerto desde backend\.env (SERVER_PORT)
REM Por defecto 8007
REM ----------------------------------------------------------
set "SERVER_PORT=8007"
if exist "%BACKEND_DIR%\.env" (
    for /f "usebackq tokens=1,2 delims==" %%a in ("%BACKEND_DIR%\.env") do (
        if /i "%%a"=="SERVER_PORT" set "SERVER_PORT=%%b"
    )
)
echo  Puerto del servicio: %SERVER_PORT%
echo.

REM ----------------------------------------------------------
REM Crear carpetas de logs y archivos si no existen
REM ----------------------------------------------------------
if not exist "%PROJECT_DIR%\logs" mkdir "%PROJECT_DIR%\logs"
if not exist "%PROJECT_DIR%\archivos\fotos" mkdir "%PROJECT_DIR%\archivos\fotos"
if not exist "%PROJECT_DIR%\archivos\pdfs" mkdir "%PROJECT_DIR%\archivos\pdfs"
if not exist "%PROJECT_DIR%\archivos\evidencias" mkdir "%PROJECT_DIR%\archivos\evidencias"

REM ----------------------------------------------------------
REM Si el servicio ya existe, detenerlo y removerlo
REM ----------------------------------------------------------
nssm status RCAService >nul 2>&1
if %ERRORLEVEL% equ 0 (
    echo  El servicio RCAService ya existe. Deteniendolo...
    nssm stop RCAService >nul 2>&1
    timeout /t 2 /nobreak >nul
    nssm remove RCAService confirm >nul 2>&1
    echo  Servicio anterior removido.
    echo.
)

REM ----------------------------------------------------------
REM Instalar el servicio
REM ----------------------------------------------------------
echo  Instalando servicio RCAService...
nssm install RCAService "%VENV_PY%" "-m uvicorn main:app --host 0.0.0.0 --port %SERVER_PORT%"
if %ERRORLEVEL% neq 0 (
    echo  ERROR: No se pudo instalar el servicio.
    pause
    exit /b 1
)

REM Directorio de trabajo = backend (CRITICO para los imports)
nssm set RCAService AppDirectory "%BACKEND_DIR%" >nul 2>&1

REM Descripcion y arranque automatico
nssm set RCAService DisplayName "RCA - Sistema de Analisis de Causa Raiz" >nul 2>&1
nssm set RCAService Description "API FastAPI del sistema RCA (puerto %SERVER_PORT%)" >nul 2>&1
nssm set RCAService Start SERVICE_AUTO_START >nul 2>&1

REM Logs (stdout/stderr)
nssm set RCAService AppStdout "%PROJECT_DIR%\logs\stdout.log" >nul 2>&1
nssm set RCAService AppStderr "%PROJECT_DIR%\logs\stderr.log" >nul 2>&1
nssm set RCAService AppRotateFiles 1 >nul 2>&1
nssm set RCAService AppRotateBytes 10485760 >nul 2>&1

REM Reinicio automatico ante caida
nssm set RCAService AppExit Default Restart >nul 2>&1
nssm set RCAService AppRestartDelay 5000 >nul 2>&1

echo  Servicio instalado y configurado.
echo.

REM ----------------------------------------------------------
REM Abrir puerto en el firewall
REM ----------------------------------------------------------
echo  Configurando firewall (puerto %SERVER_PORT%)...
netsh advfirewall firewall delete rule name="RCA API %SERVER_PORT%" >nul 2>&1
netsh advfirewall firewall add rule name="RCA API %SERVER_PORT%" dir=in action=allow protocol=TCP localport=%SERVER_PORT% >nul 2>&1
echo  OK.
echo.

REM ----------------------------------------------------------
REM Iniciar el servicio
REM ----------------------------------------------------------
echo  Iniciando servicio RCAService...
nssm start RCAService
timeout /t 3 /nobreak >nul

nssm status RCAService >nul 2>&1
if %ERRORLEVEL% equ 0 (
    echo  SERVICIO INICIADO CORRECTAMENTE.
) else (
    echo  AVISO: El servicio no se inicio automaticamente.
    echo         Revisa los logs en: %PROJECT_DIR%\logs\
)

echo.
echo ========================================================
echo   INSTALACION COMPLETADA
echo ========================================================
echo.
echo   Servicio   : RCAService
echo   Puerto     : %SERVER_PORT%
echo   API        : http://localhost:%SERVER_PORT%
echo   Swagger    : http://localhost:%SERVER_PORT%\docs
echo   Health     : http://localhost:%SERVER_PORT%\health
echo   Logs       : %PROJECT_DIR%\logs\
echo.
echo   Comandos utiles:
echo     nssm status RCAService
echo     nssm restart RCAService
echo     nssm stop RCAService
echo     nssm remove RCAService confirm
echo.
pause