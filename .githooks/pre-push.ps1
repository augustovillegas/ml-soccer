[CmdletBinding()]
param()

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

$projectRoot = Split-Path -Parent $PSScriptRoot
$validateScript = Join-Path $projectRoot "scripts\validate-project.ps1"
$venvPython = Join-Path $projectRoot ".venv\Scripts\python.exe"

& $validateScript -Scope project
& $venvPython -m pytest
exit $LASTEXITCODE
