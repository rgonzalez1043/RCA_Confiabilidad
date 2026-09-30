[CmdletBinding()]
param([string]$Python)
$ErrorActionPreference = 'Stop'
$projectPath = $PSScriptRoot
$venvPython = Join-Path $projectPath 'venv\Scripts\python.exe'

function Comprobar-Python([string]$Exe) {
    $info = & $Exe -c 'import sys,struct; print(sys.version_info.major, sys.version_info.minor, struct.calcsize(chr(80))*8)'
    if ($LASTEXITCODE -ne 0 -or "$info" -notmatch '^3 (10|11|12) 64$') {
        throw 'Se requiere Python 3.10, 3.11 o 3.12 de 64 bits. Python 3.13 no es compatible con estas dependencias fijadas.'
    }
    Write-Host "Python compatible: $info"
}

try {
    if (-not (Test-Path -LiteralPath (Join-Path $projectPath 'backend\main.py'))) {
        throw 'Ejecuta este script dentro del proyecto descomprimido.'
    }
    if (Test-Path -LiteralPath $venvPython) {
        Comprobar-Python $venvPython
    } else {
        if (-not $Python) {
            $launcher = Get-Command py -ErrorAction SilentlyContinue
            if ($launcher) {
                foreach ($version in @('3.10', '3.11', '3.12')) {
                    try {
                        $candidate = & $launcher.Source "-$version" -c 'import sys; print(sys.executable)' 2>$null
                    } catch { continue }
                    if ($LASTEXITCODE -eq 0 -and $candidate) { $Python = "$candidate"; break }
                }
            }
            if (-not $Python) {
                $command = Get-Command python -ErrorAction SilentlyContinue
                if ($command) { $Python = $command.Source }
            }
        }
        if (-not $Python) { throw 'Instala Python x64 3.10 a 3.12 o indica -Python con la ruta de python.exe.' }
        Comprobar-Python $Python
        & $Python -m venv (Join-Path $projectPath 'venv')
        if ($LASTEXITCODE -ne 0) { throw 'No se pudo crear el entorno virtual.' }
    }
    $wheels = Join-Path $projectPath 'wheels'
    $arguments = @('-m', 'pip', 'install', '--disable-pip-version-check', '-r', (Join-Path $projectPath 'requirements.txt'))
    if (Test-Path -LiteralPath $wheels) {
        Write-Host 'Instalando bibliotecas incluidas, sin utilizar Internet...'
        $arguments += @('--no-index', '--find-links', $wheels)
    } else {
        Write-Host 'No hay bibliotecas empaquetadas; pip utilizara Internet.'
    }
    & $venvPython @arguments
    if ($LASTEXITCODE -ne 0) { throw 'Fallo la instalacion de bibliotecas. El servicio no se ha modificado.' }
    & $venvPython -m pip check
    if ($LASTEXITCODE -ne 0) { throw 'Existen dependencias incompatibles.' }
    $envPath = Join-Path $projectPath 'backend\.env'
    if (-not (Test-Path -LiteralPath $envPath)) {
        Copy-Item -LiteralPath (Join-Path $projectPath 'backend\.env.example') -Destination $envPath
        Write-Host 'Se creo backend\.env. Configura la conexion MySQL antes de iniciar.'
    } else {
        Write-Host 'Se conserva el archivo backend\.env existente.'
    }
    & $venvPython (Join-Path $projectPath 'backend\verificar_despliegue.py') importar
    if ($LASTEXITCODE -ne 0) { throw 'No se pudo importar el backend con este entorno.' }
    Write-Host ''
    Write-Host 'Entorno preparado. No se modificaron servicios ni bases de datos.' -ForegroundColor Green
    Write-Host 'Instalacion nueva: configura backend\.env, prepara MySQL y ejecuta instalar_servicio.bat como Administrador.'
    Write-Host 'Servicio existente: usa VERIFICAR_SERVIDOR.bat y ACTUALIZAR_SERVIDOR.bat desde el paquete separado.'
} catch {
    Write-Host "ERROR: $_" -ForegroundColor Red
    exit 1
}
