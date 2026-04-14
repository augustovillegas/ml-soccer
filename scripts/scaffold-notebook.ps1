[CmdletBinding()]
param(
    [Parameter(Mandatory = $true)]
    [string]$Stage,
    [Parameter(Mandatory = $true)]
    [string]$Topic,
    [string]$NotebookId,
    [string]$TemplateProfile = "official_v1",
    [string[]]$SourceDatasetIds = @(),
    [string[]]$OutputDatasetIds = @()
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

$arguments = @(
    "-m", "football_ml.scaffold_notebook",
    "--stage", $Stage,
    "--topic", $Topic,
    "--template-profile", $TemplateProfile
)

if (-not [string]::IsNullOrWhiteSpace($NotebookId)) {
    $arguments += @("--notebook-id", $NotebookId)
}

foreach ($datasetId in $SourceDatasetIds) {
    if (-not [string]::IsNullOrWhiteSpace($datasetId)) {
        $arguments += @("--source-dataset-id", $datasetId)
    }
}

foreach ($datasetId in $OutputDatasetIds) {
    if (-not [string]::IsNullOrWhiteSpace($datasetId)) {
        $arguments += @("--output-dataset-id", $datasetId)
    }
}

& $venvPython @arguments
if ($LASTEXITCODE -ne 0) {
    throw "La creacion del notebook oficial fallo. Revisa la salida previa para el detalle."
}
