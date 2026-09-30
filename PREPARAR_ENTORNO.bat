@echo off
chcp 65001 >nul
powershell.exe -NoProfile -File "%~dp0preparar_entorno.ps1" %*
set "RCA_EXIT=%ERRORLEVEL%"
pause
exit /b %RCA_EXIT%
