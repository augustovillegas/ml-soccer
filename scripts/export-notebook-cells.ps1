[CmdletBinding()]
param()

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

. (Join-Path $PSScriptRoot "_governance.ps1")

Invoke-GovernedCommand `
    -CommandId "export_notebook_cells" `
    -CommandTokens @(".\scripts\export-notebook-cells.ps1") `
    -ArtifactsUpdated @("docs/notebooks/01_explorer_matchhistory_cells.md", "docs/notebooks/02_silver_matchhistory_cells.md") `
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

        & $venvPython -m football_ml.export_notebook_cells --all
        if ($LASTEXITCODE -ne 0) {
            throw "La exportacion del notebook a Markdown fallo. Revisa la salida previa para el detalle."
        }
    }
