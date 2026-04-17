[CmdletBinding()]
param(
    [switch]$Check,
    [string[]]$ChangedPath
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

. (Join-Path $PSScriptRoot "_governance.ps1")

$commandTokens = @(".\scripts\sync-project.ps1")
$normalizedArgs = @()
if ($Check) {
    $commandTokens += "-Check"
    $normalizedArgs += "--check"
}
foreach ($path in $ChangedPath) {
    if (-not [string]::IsNullOrWhiteSpace($path)) {
        $commandTokens += @("-ChangedPath", $path)
        $normalizedArgs += @("--changed-path", $path)
    }
}

Invoke-GovernedCommand `
    -CommandId "sync_project" `
    -CommandTokens $commandTokens `
    -NormalizedArgs $normalizedArgs `
    -ArtifactsUpdated @(
        "BITACORA_ENTORNO.md",
        "docs/generated/README.md",
        "docs/generated/official-commands.md",
        "docs/generated/project-status.md",
        "docs/notebooks/README.md",
        "requirements.txt"
    ) `
    -Action {
        $projectRoot = Split-Path -Parent $PSScriptRoot
        $venvPython = Join-Path $projectRoot ".venv\Scripts\python.exe"
        $srcPath = Join-Path $projectRoot "src"

        if (-not (Test-Path $venvPython)) {
            throw "No existe '$venvPython'. Ejecuta primero '.\scripts\bootstrap.ps1'."
        }

        if ([string]::IsNullOrWhiteSpace($env:PYTHONPATH)) {
            $env:PYTHONPATH = $srcPath
        } else {
            $env:PYTHONPATH = "$srcPath;$($env:PYTHONPATH)"
        }

        $arguments = @("-m", "football_ml.sync_project")
        if ($Check) {
            $arguments += "--check"
        }
        foreach ($path in $ChangedPath) {
            if (-not [string]::IsNullOrWhiteSpace($path)) {
                $arguments += @("--changed-path", $path)
            }
        }

        & $venvPython @arguments
        if ($LASTEXITCODE -ne 0) {
            throw "La sincronizacion del proyecto fallo. Revisa la salida previa para el detalle."
        }
    }
