@echo off
title RCA Server - Sistema de Confiabilidad
color 0A
cls
echo.
echo ========================================
echo   RCA SERVER - INICIANDO...
echo ========================================
echo.
echo Documentacion: http://localhost:8007/docs
echo.
echo Presione Ctrl+C para detener el servidor
echo.
echo ========================================
echo.

cd /d %~dp0backend
python main.py

echo.
echo ========================================
echo   SERVIDOR DETENIDO
echo ========================================
echo.
pause