[CmdletBinding()]
param(
    [switch]$Force,
    [string[]]$Seasons
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

. (Join-Path $PSScriptRoot "_governance.ps1")

if ($null -ne $Seasons -and $Seasons.Count -eq 1 -and $Seasons[0] -like "*,*") {
    $Seasons = $Seasons[0] -split ","
}

$commandTokens = @(".\scripts\ingest-matchhistory.ps1")
$normalizedArgs = @()
if ($Force) {
    $commandTokens += "-Force"
    $normalizedArgs += "--force"
}
foreach ($season in $Seasons) {
    $commandTokens += @("-Seasons", $season)
    $normalizedArgs += @("--seasons", $season)
}

Invoke-GovernedCommand `
    -CommandId "ingest_matchhistory" `
    -CommandTokens $commandTokens `
    -NormalizedArgs $normalizedArgs `
    -ArtifactsUpdated @(
        "data/bronze/matchhistory/raw",
        "data/bronze/matchhistory/manifests",
        "docs/generated/project-status.md",
        "BITACORA_ENTORNO.md"
    ) `
    -AutoSyncChangedPaths @(
        "data/bronze/matchhistory/raw",
        "data/bronze/matchhistory/manifests"
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
    }
