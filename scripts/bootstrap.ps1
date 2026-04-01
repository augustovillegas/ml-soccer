[CmdletBinding()]
param()

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

$projectRoot = Split-Path -Parent $PSScriptRoot
$venvDir = Join-Path $projectRoot ".venv"
$venvPython = Join-Path $venvDir "Scripts\\python.exe"
$srcPath = Join-Path $projectRoot "src"

if (-not (Test-Path $venvPython)) {
    if (Test-Path $venvDir) {
        throw "'.venv' existe, pero no contiene '$venvPython'. Recreate el entorno antes de continuar."
    }

    $pyCommand = Get-Command py -ErrorAction SilentlyContinue
    if (-not $pyCommand) {
        throw "No se encontro el lanzador 'py'. Instala Python 3.13 o crea '.venv' manualmente."
    }

    & py -3.13 -m venv $venvDir
}

New-Item -ItemType Directory -Force -Path `
    (Join-Path $projectRoot "data\\bronze\\matchhistory\\raw"), `
    (Join-Path $projectRoot "data\\bronze\\matchhistory\\inbox"), `
    (Join-Path $projectRoot "data\\bronze\\matchhistory\\manifests"), `
    (Join-Path $projectRoot "data\\silver"), `
    (Join-Path $projectRoot "data\\gold"), `
    (Join-Path $projectRoot "logs\\ingestion"), `
    (Join-Path $projectRoot "models"), `
    (Join-Path $projectRoot "notebooks") | Out-Null

& $venvPython -m pip install --upgrade pip
if ($LASTEXITCODE -ne 0) {
    throw "Fallo la actualizacion de pip dentro del entorno virtual."
}

& $venvPython -m pip install -r (Join-Path $projectRoot "requirements.txt")
if ($LASTEXITCODE -ne 0) {
    throw "Fallo la instalacion de dependencias desde requirements.txt."
}

& $venvPython -m ipykernel install --prefix $venvDir --name football-ml --display-name "football-ml (.venv)"
if ($LASTEXITCODE -ne 0) {
    throw "Fallo el registro del kernel 'football-ml (.venv)'."
}

if ([string]::IsNullOrWhiteSpace($env:PYTHONPATH)) {
    $env:PYTHONPATH = $srcPath
} else {
    $env:PYTHONPATH = "$srcPath;$($env:PYTHONPATH)"
}

& (Join-Path $PSScriptRoot "validate-project.ps1")
if ($LASTEXITCODE -ne 0) {
    throw "La validacion final del proyecto fallo."
}
