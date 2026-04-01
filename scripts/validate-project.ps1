[CmdletBinding()]
param(
    [ValidateSet("project", "runtime")]
    [string]$Scope = "project"
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

$projectRoot = Split-Path -Parent $PSScriptRoot
$venvPython = Join-Path $projectRoot ".venv\\Scripts\\python.exe"
$srcPath = Join-Path $projectRoot "src"

if (-not (Test-Path $venvPython)) {
    throw "No existe '$venvPython'. Ejecuta primero '.\\scripts\\bootstrap.ps1'."
}

if ([string]::IsNullOrWhiteSpace($env:PYTHONPATH)) {
    $env:PYTHONPATH = $srcPath
} else {
    $env:PYTHONPATH = "$srcPath;$($env:PYTHONPATH)"
}

& $venvPython -m football_ml.validate --scope $Scope
if ($LASTEXITCODE -ne 0) {
    throw "La validacion del proyecto fallo. Revisa la salida previa para el detalle."
}
