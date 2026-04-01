[CmdletBinding()]
param(
    [switch]$Force,
    [string[]]$Seasons
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

$projectRoot = Split-Path -Parent $PSScriptRoot
$venvPython = Join-Path $projectRoot ".venv\\Scripts\\python.exe"
$srcPath = Join-Path $projectRoot "src"

if (-not (Test-Path $venvPython)) {
    throw "No existe '$venvPython'. Ejecuta primero '.\\scripts\\bootstrap.ps1'."
}

if ($null -ne $Seasons -and $Seasons.Count -eq 1 -and $Seasons[0] -like "*,*") {
    $Seasons = $Seasons[0] -split ","
}

if ([string]::IsNullOrWhiteSpace($env:PYTHONPATH)) {
    $env:PYTHONPATH = $srcPath
} else {
    $env:PYTHONPATH = "$srcPath;$($env:PYTHONPATH)"
}

$pythonArgs = @("-m", "football_ml.ingest.matchhistory")
if ($Force) {
    $pythonArgs += "--force"
}
if ($null -ne $Seasons -and $Seasons.Count -gt 0) {
    $pythonArgs += "--seasons"
    $pythonArgs += $Seasons
}

& $venvPython @pythonArgs
if ($LASTEXITCODE -ne 0) {
    throw "La ingesta de MatchHistory fallo. Revisa la salida previa para el detalle."
}
