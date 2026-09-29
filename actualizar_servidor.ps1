<#
.SYNOPSIS
    Actualiza un servidor RCA existente con el código de esta carpeta.
.DESCRIPTION
    Ejecutar en el servidor como Administrador, desde la carpeta descomprimida
    (no dentro de la instalación). Detecta la instalación del servicio NSSM,
    verifica la compatibilidad sin detener nada, respalda código, adjuntos y
    MySQL, copia el código nuevo conservando .env, venv, archivos, logs y
    respaldos, reinicia el servicio y comprueba la API. Si la comprobación
    final falla, restaura el código anterior y vuelve a iniciar el servicio.
.EXAMPLE
    .\actualizar_servidor.ps1 -SoloVerificar
.EXAMPLE
    .\actualizar_servidor.ps1
#>
[CmdletBinding()]
param(
    # Solo comprobaciones de lectura; no detiene ni modifica nada.
    [switch]$SoloVerificar,
    # Omite mysqldump porque la base ya se respaldó por otro medio.
    [switch]$RespaldoBDManual,
    # Ejecuta pip install -r requirements.txt si faltan dependencias.
    [switch]$InstalarDependencias,
    [string]$Servicio = 'RCAService',
    # Carpeta instalada (la que contiene backend\.env). Por defecto, la del servicio.
    [string]$Destino,
    # python.exe del entorno del servicio. Por defecto, el configurado en NSSM.
    [string]$Python
)

$ErrorActionPreference = 'Stop'
$VersionNueva = '1.2.0'
$origen = $PSScriptRoot.TrimEnd('\')
$marca = Get-Date -Format 'yyyyMMdd_HHmmss'
$excluir = @('venv', '.venv', '.venv-test', 'env', 'archivos', 'logs', 'respaldos', '.git',
             '__pycache__', '.pytest_cache')
$script:transcripcion = $false
try { [Console]::OutputEncoding = [Text.Encoding]::UTF8 } catch { }
$env:PYTHONIOENCODING = 'utf-8'

function Paso($texto) { Write-Host ''; Write-Host "== $texto" -ForegroundColor Cyan }
function Ok($texto) { Write-Host "   OK     $texto" -ForegroundColor Green }
function Aviso($texto) { Write-Host "   AVISO  $texto" -ForegroundColor Yellow }
function Detener($texto) {
    Write-Host ''
    Write-Host "DETENIDO: $texto" -ForegroundColor Red
    if ($script:transcripcion) { Stop-Transcript | Out-Null }
    exit 1
}

function Invoke-Nativo([string]$Exe, [string[]]$Argumentos, [string]$Carpeta) {
    $ErrorActionPreference = 'Continue'
    if ($Carpeta) { Push-Location $Carpeta }
    try {
        $salida = & $Exe @Argumentos 2>&1 | ForEach-Object { "$_" }
        $codigo = $LASTEXITCODE
    } finally {
        if ($Carpeta) { Pop-Location }
    }
    [pscustomobject]@{ Codigo = $codigo; Salida = ($salida -join [Environment]::NewLine) }
}

function Copiar-Carpeta([string]$De, [string]$A, [string[]]$ExcluirDirs, [string[]]$ExcluirArchivos) {
    $argumentos = @($De.TrimEnd('\'), $A.TrimEnd('\'), '/E', '/R:1', '/W:1', '/NFL', '/NDL', '/NJH', '/NJS', '/NP')
    if ($ExcluirDirs) { $argumentos += '/XD'; $argumentos += $ExcluirDirs }
    if ($ExcluirArchivos) { $argumentos += '/XF'; $argumentos += $ExcluirArchivos }
    $r = Invoke-Nativo 'robocopy.exe' $argumentos
    # Robocopy: 0-7 son resultados correctos; 8 o más indica fallos.
    if ($r.Codigo -ge 8) { throw "robocopy falló ($($r.Codigo)) al copiar $De en $A`n$($r.Salida)" }
}

function Leer-Env([string]$Ruta) {
    $valores = @{}
    foreach ($linea in Get-Content -LiteralPath $Ruta -Encoding UTF8) {
        $t = $linea.Trim()
        if (-not $t -or $t.StartsWith('#')) { continue }
        $i = $t.IndexOf('=')
        if ($i -lt 1) { continue }
        $v = $t.Substring($i + 1).Trim()
        if ($v.Length -ge 2 -and (($v[0] -eq '"' -and $v[-1] -eq '"') -or ($v[0] -eq "'" -and $v[-1] -eq "'"))) {
            $v = $v.Substring(1, $v.Length - 2)
        }
        $valores[$t.Substring(0, $i).Trim()] = $v
    }
    $valores
}

function Version-Instalada([string]$Carpeta) {
    $m = Select-String -LiteralPath (Join-Path $Carpeta 'backend\main.py') -Pattern 'version="([0-9.]+)"' | Select-Object -First 1
    if ($m) { $m.Matches[0].Groups[1].Value } else { 'desconocida' }
}

function Hash-Normalizado([string]$Ruta) {
    # Mismo criterio que versiones_conocidas.txt: UTF-8 sin BOM y saltos de línea LF.
    $texto = [IO.File]::ReadAllText($Ruta, [Text.Encoding]::UTF8).Replace("`r`n", "`n")
    $sha = [Security.Cryptography.SHA256]::Create()
    -join ($sha.ComputeHash([Text.Encoding]::UTF8.GetBytes($texto)) | ForEach-Object { $_.ToString('x2') })
}

function Buscar-Mysqldump {
    $candidatos = New-Object System.Collections.Generic.List[string]
    foreach ($nombre in 'mysqldump.exe', 'mariadb-dump.exe') {
        $c = Get-Command $nombre -ErrorAction SilentlyContinue
        if ($c) { $candidatos.Add($c.Source) }
    }
    Get-CimInstance Win32_Service -ErrorAction SilentlyContinue | Where-Object { $_.PathName -match 'mysqld|mariadbd' } | ForEach-Object {
        if ($_.PathName -match '^"?(.+\\)(mysqld|mariadbd)[^\\]*\.exe') {
            $candidatos.Add((Join-Path $Matches[1] 'mysqldump.exe'))
            $candidatos.Add((Join-Path $Matches[1] 'mariadb-dump.exe'))
        }
    }
    $candidatos.Add('C:\xampp\mysql\bin\mysqldump.exe')
    foreach ($patron in 'C:\Program Files\MySQL\*\bin\mysqldump.exe', 'C:\Program Files\MariaDB*\bin\mysqldump.exe',
                        'C:\wamp64\bin\mysql\*\bin\mysqldump.exe') {
        Get-ChildItem $patron -ErrorAction SilentlyContinue | ForEach-Object { $candidatos.Add($_.FullName) }
    }
    $candidatos | Where-Object { Test-Path -LiteralPath $_ } | Select-Object -First 1
}

function Esperar-Api([string]$Puerto, [int]$Segundos) {
    $limite = (Get-Date).AddSeconds($Segundos)
    do {
        try {
            $h = Invoke-RestMethod "http://127.0.0.1:$Puerto/health" -TimeoutSec 5
            if ($h.status -eq 'healthy') { return $true }
        } catch { }
        Start-Sleep -Seconds 3
    } while ((Get-Date) -lt $limite)
    $false
}

function Verificar-Api([string]$Puerto) {
    if (-not (Esperar-Api $Puerto 90)) { return 'La API no respondió /health correctamente en 90 segundos' }
    $raiz = Invoke-RestMethod "http://127.0.0.1:$Puerto/" -TimeoutSec 10
    if ($raiz.version -ne $VersionNueva) { return "La API informa la versión $($raiz.version)" }
    $openapi = Invoke-RestMethod "http://127.0.0.1:$Puerto/openapi.json" -TimeoutSec 10
    $rutas = $openapi.paths.PSObject.Properties.Name
    foreach ($ruta in '/rca/{rca_id}/historial', '/archivo/{archivo_id}/contenido') {
        if ($rutas -notcontains $ruta) { return "Falta la ruta $ruta" }
    }
    $null
}

# ---------------------------------------------------------------------------
Paso 'Instalación existente'
if (-not (Test-Path -LiteralPath (Join-Path $origen 'backend\main.py'))) {
    Detener "Este script debe estar en la carpeta descomprimida del paquete (no se encontró backend\main.py)."
}
if ((Version-Instalada $origen) -ne $VersionNueva) { Detener "El paquete no contiene la versión $VersionNueva." }

$stderrLog = $null
$appParams = ''
$registro = "HKLM:\SYSTEM\CurrentControlSet\Services\$Servicio\Parameters"
$servicioExiste = [bool](Get-Service -Name $Servicio -ErrorAction SilentlyContinue)
if ($servicioExiste -and (Test-Path $registro)) {
    $nssm = Get-ItemProperty $registro
    if (-not $Destino) { $Destino = Split-Path $nssm.AppDirectory.TrimEnd('\') -Parent }
    if (-not $Python) { $Python = $nssm.Application }
    $appParams = [string]$nssm.AppParameters
    $stderrLog = $nssm.AppStderr
}
if (-not $Destino -or -not $Python) {
    Detener "No se encontró la configuración NSSM de $Servicio. Indica -Destino y -Python."
}
$Destino = (Resolve-Path -LiteralPath $Destino).Path.TrimEnd('\')
$envInstalado = Join-Path $Destino 'backend\.env'
if (-not (Test-Path -LiteralPath (Join-Path $Destino 'backend\main.py'))) { Detener "No existe $Destino\backend\main.py" }
if (-not (Test-Path -LiteralPath $envInstalado)) { Detener "No existe $envInstalado" }
if (-not (Test-Path -LiteralPath $Python)) { Detener "No existe el Python del servicio: $Python" }
if ($Destino -eq $origen) {
    Detener 'El paquete se descomprimió sobre la instalación. Descomprímelo en otra carpeta (por ejemplo, el Escritorio).'
}
$config = Leer-Env $envInstalado
if ($appParams -match '--port\s+(\d+)') { $puerto = $Matches[1] }
elseif ($config['SERVER_PORT']) { $puerto = $config['SERVER_PORT'] }
else { $puerto = '8007' }
$archivosDir = if ($config['ARCHIVOS_PATH']) { $config['ARCHIVOS_PATH'] } else { 'archivos' }
if (-not [IO.Path]::IsPathRooted($archivosDir)) { $archivosDir = Join-Path $Destino $archivosDir }
$versionActual = Version-Instalada $Destino

Ok "Servicio: $Servicio (existe: $servicioExiste)"
Ok "Instalación: $Destino"
Ok "Python del servicio: $Python"
Ok "Puerto: $puerto | Adjuntos: $archivosDir"
Ok "Versión instalada: $versionActual -> nueva: $VersionNueva"
if (Test-Path -LiteralPath (Join-Path $Destino '.git')) {
    Aviso 'La instalación es un repositorio Git. Tras copiar el paquete, git status mostrará archivos modificados; no uses git pull sin revisar antes.'
}

# ---------------------------------------------------------------------------
Paso 'Cambios locales en el servidor'
$manifiesto = Join-Path $origen 'versiones_conocidas.txt'
$modificados = @()
if (Test-Path -LiteralPath $manifiesto) {
    $conocidos = @{}
    foreach ($linea in Get-Content -LiteralPath $manifiesto) {
        $partes = $linea -split "`t"
        if ($partes.Count -eq 2) {
            if (-not $conocidos.ContainsKey($partes[0])) { $conocidos[$partes[0]] = New-Object System.Collections.Generic.HashSet[string] }
            [void]$conocidos[$partes[0]].Add($partes[1])
        }
    }
    foreach ($relativo in $conocidos.Keys) {
        $ruta = Join-Path $Destino ($relativo -replace '/', '\')
        if ((Test-Path -LiteralPath $ruta) -and -not $conocidos[$relativo].Contains((Hash-Normalizado $ruta))) {
            $modificados += $relativo
        }
    }
    if ($modificados) {
        Aviso 'Estos archivos del servidor no coinciden con ninguna versión publicada en GitHub:'
        $modificados | Sort-Object | ForEach-Object { Write-Host "          $_" -ForegroundColor Yellow }
        Aviso 'Se guardarán en el respaldo antes de reemplazarlos.'
    } else {
        Ok 'El código instalado coincide con versiones publicadas; no hay cambios locales.'
    }
} else {
    Aviso 'No se incluyó versiones_conocidas.txt; se omite esta comprobación.'
}

# ---------------------------------------------------------------------------
Paso 'Compatibilidad del código nuevo con el Python del servidor'
$verificador = Join-Path $origen 'backend\verificar_despliegue.py'
$r = Invoke-Nativo $Python @($verificador, 'importar') (Join-Path $origen 'backend')
Write-Host $r.Salida
if ($r.Codigo -ne 0) {
    if (-not $InstalarDependencias) {
        Detener 'El código nuevo no se puede importar con ese entorno. Revisa el mensaje; si faltan dependencias, vuelve a ejecutar con -InstalarDependencias (requiere Internet).'
    }
    Paso 'Instalando dependencias fijadas en requirements.txt'
    $pip = Invoke-Nativo $Python @('-m', 'pip', 'install', '-r', (Join-Path $origen 'requirements.txt'))
    Write-Host $pip.Salida
    if ($pip.Codigo -ne 0) { Detener 'pip install falló. El servicio sigue funcionando con la versión anterior.' }
    $r = Invoke-Nativo $Python @($verificador, 'importar') (Join-Path $origen 'backend')
    Write-Host $r.Salida
    if ($r.Codigo -ne 0) { Detener 'El código nuevo sigue sin importarse. El servicio no se modificó.' }
}

Paso 'Esquema de MySQL (solo lectura)'
$r = Invoke-Nativo $Python @($verificador, 'bd', '--env', $envInstalado) (Join-Path $origen 'backend')
Write-Host $r.Salida
if ($r.Codigo -ne 0) { Detener 'El esquema de la base de datos no es compatible. No se modificó nada.' }

$mysqldump = $null
if (-not $RespaldoBDManual) {
    $mysqldump = Buscar-Mysqldump
    if ($mysqldump) { Ok "mysqldump: $mysqldump" }
    else { Aviso 'No se encontró mysqldump. Para actualizar, respalda la base por otro medio y usa -RespaldoBDManual.' }
}

if ($SoloVerificar) {
    Write-Host ''
    Write-Host 'Verificación terminada. No se detuvo ni modificó nada.' -ForegroundColor Green
    exit 0
}

# ---------------------------------------------------------------------------
$admin = ([Security.Principal.WindowsPrincipal][Security.Principal.WindowsIdentity]::GetCurrent()).IsInRole(
    [Security.Principal.WindowsBuiltInRole]::Administrator)
if (-not $admin) { Detener 'Ejecuta como Administrador (clic derecho > Ejecutar como administrador).' }
if (-not $servicioExiste) { Detener "No existe el servicio $Servicio para detenerlo y reiniciarlo." }
if (-not $RespaldoBDManual -and -not $mysqldump) { Detener 'Falta el respaldo de la base de datos (ver aviso anterior).' }
if ($modificados) {
    $respuesta = Read-Host 'Hay archivos con cambios locales. ¿Continuar y reemplazarlos? (S/N)'
    if ($respuesta -notmatch '^[sS]') { Detener 'Cancelado por el usuario. No se modificó nada.' }
}

$respaldo = Join-Path $Destino "respaldos\actualizacion_${VersionNueva}_$marca"
New-Item -ItemType Directory -Force -Path $respaldo | Out-Null
Start-Transcript -LiteralPath (Join-Path $respaldo 'actualizacion.log') | Out-Null
$script:transcripcion = $true

Paso 'Respaldo'
$tamanioAdjuntos = 0
if (Test-Path -LiteralPath $archivosDir) {
    $tamanioAdjuntos = (Get-ChildItem -LiteralPath $archivosDir -Recurse -File -ErrorAction SilentlyContinue | Measure-Object Length -Sum).Sum
}
$libre = (Get-PSDrive -Name $Destino.Substring(0, 1)).Free
if ($libre -lt ($tamanioAdjuntos * 2 + 1GB)) { Detener 'No hay espacio libre suficiente para el respaldo.' }

Copiar-Carpeta $Destino (Join-Path $respaldo 'codigo') $excluir @('*.pyc')
Ok 'Código anterior respaldado (incluye .env)'
if (Test-Path -LiteralPath $archivosDir) {
    Copiar-Carpeta $archivosDir (Join-Path $respaldo 'archivos') @() @()
    Ok ("Adjuntos respaldados ({0:N0} MB)" -f ($tamanioAdjuntos / 1MB))
} else {
    Aviso "No existe la carpeta de adjuntos $archivosDir"
}
if ($mysqldump) {
    # Mismos valores por defecto que backend\config.py; la clave no va en la línea de comandos.
    function Valor($clave, $defecto) { if ($config[$clave]) { $config[$clave] } else { $defecto } }
    function Citar($texto) { '"' + ([string]$texto).Replace('\', '\\').Replace('"', '\"') + '"' }
    $opciones = Join-Path $env:TEMP "rca_mysql_$marca.cnf"
    $contenido = "[client]`nuser=$(Citar (Valor 'DB_USER' 'root'))`npassword=$(Citar (Valor 'DB_PASSWORD' ''))`n" +
                 "host=$(Citar (Valor 'DB_HOST' 'localhost'))`nport=$(Valor 'DB_PORT' '3306')`nprotocol=tcp`n"
    [IO.File]::WriteAllText($opciones, $contenido, (New-Object Text.UTF8Encoding $false))
    $baseDatos = Valor 'DB_NAME' 'rca_database'
    $sql = Join-Path $respaldo "$baseDatos.sql"
    try {
        $d = Invoke-Nativo $mysqldump @("--defaults-extra-file=$opciones", '--single-transaction', '--quick',
            '--routines', '--triggers', '--no-tablespaces', '--default-character-set=utf8mb4',
            "--result-file=$sql", $baseDatos)
    } finally {
        Remove-Item -LiteralPath $opciones -Force -ErrorAction SilentlyContinue
    }
    if ($d.Codigo -ne 0 -or -not (Test-Path -LiteralPath $sql) -or (Get-Item -LiteralPath $sql).Length -lt 1024) {
        Write-Host $d.Salida
        Detener 'mysqldump falló. El servicio no se detuvo ni se modificó el código.'
    }
    Ok ("Base de datos respaldada: {0} ({1:N1} MB)" -f $sql, ((Get-Item -LiteralPath $sql).Length / 1MB))
} else {
    Aviso 'Respaldo de la base de datos indicado como manual (-RespaldoBDManual).'
}

# ---------------------------------------------------------------------------
Paso "Actualización $versionActual -> $VersionNueva"
$fallo = $null
try {
    Stop-Service -Name $Servicio -Force
    (Get-Service -Name $Servicio).WaitForStatus('Stopped', [TimeSpan]::FromSeconds(60))
    Ok 'Servicio detenido'
    Copiar-Carpeta $origen $Destino $excluir @('.env', '*.pyc', 'versiones_conocidas.txt')
    Ok 'Código nuevo copiado (se conservan .env, venv, archivos, logs y respaldos)'
    Start-Service -Name $Servicio
    Ok 'Servicio iniciado; esperando la API...'
    $fallo = Verificar-Api $puerto
    if (-not $fallo) {
        $r = Invoke-Nativo $Python @((Join-Path $Destino 'backend\verificar_despliegue.py'), 'bd', '--env', $envInstalado) (Join-Path $Destino 'backend')
        Write-Host $r.Salida
        if ($r.Codigo -ne 0 -or $r.Salida -notmatch 'rca_historial ya existe') { $fallo = 'La comprobación posterior del esquema falló' }
    }
} catch {
    $fallo = "$_"
}

if ($fallo) {
    Write-Host ''
    Write-Host "FALLÓ LA ACTUALIZACIÓN: $fallo" -ForegroundColor Red
    if ($stderrLog -and (Test-Path -LiteralPath $stderrLog)) {
        Write-Host "Últimas líneas de ${stderrLog}:" -ForegroundColor Yellow
        Get-Content -LiteralPath $stderrLog -Tail 40 | ForEach-Object { Write-Host "   $_" }
    }
    Paso 'Restaurando el código anterior'
    try { Stop-Service -Name $Servicio -Force -ErrorAction SilentlyContinue } catch { }
    Copiar-Carpeta (Join-Path $respaldo 'codigo') $Destino $excluir @()
    Start-Service -Name $Servicio
    if (Esperar-Api $puerto 90) { Ok "Versión anterior restaurada y en línea ($(Version-Instalada $Destino))" }
    else { Aviso 'La versión anterior no responde. Revisa el servicio y los logs.' }
    Detener "Actualización revertida. Respaldo en $respaldo"
}

Write-Host ''
Write-Host "ACTUALIZACIÓN COMPLETADA: API $VersionNueva en http://127.0.0.1:$puerto" -ForegroundColor Green
Write-Host "Respaldo: $respaldo"
Write-Host 'Instala la APK nueva en las tablets: la app anterior no puede guardar con esta API.'
Stop-Transcript | Out-Null
