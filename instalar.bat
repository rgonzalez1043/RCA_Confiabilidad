@echo off
REM Instalador compatible con el paquete offline; preserva .env y MySQL.
call "%~dp0PREPARAR_ENTORNO.bat" %*
exit /b %ERRORLEVEL%
