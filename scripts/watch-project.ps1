[CmdletBinding()]
param(
    [switch]$SkipInitialSync,
    [double]$DebounceSeconds
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

. (Join-Path $PSScriptRoot "_governance.ps1")

$commandTokens = @(".\scripts\watch-project.ps1")
$normalizedArgs = @()

if ($SkipInitialSync) {
    $commandTokens += "-SkipInitialSync"
    $normalizedArgs += "--skip-initial-sync"
}
if ($PSBoundParameters.ContainsKey("DebounceSeconds")) {
    $commandTokens += @("-DebounceSeconds", $DebounceSeconds.ToString())
    $normalizedArgs += @("--debounce-seconds", $DebounceSeconds.ToString())
}

Invoke-GovernedCommand `
    -CommandId "watch_project" `
    -CommandTokens $commandTokens `
    -NormalizedArgs $normalizedArgs `
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

        $arguments = @("-m", "football_ml.watch_project")
        if ($SkipInitialSync) {
            $arguments += "--skip-initial-sync"
        }
        if ($PSBoundParameters.ContainsKey("DebounceSeconds")) {
            $arguments += @("--debounce-seconds", $DebounceSeconds.ToString())
        }

        & $venvPython @arguments
        if ($LASTEXITCODE -ne 0) {
            throw "El watcher del proyecto fallo. Revisa la salida previa para el detalle."
        }
    }
