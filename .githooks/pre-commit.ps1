[CmdletBinding()]
param()

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

$projectRoot = Split-Path -Parent $PSScriptRoot
$changedPaths = @(
    & git -C $projectRoot diff --cached --name-only --diff-filter=ACMR
) | Where-Object { -not [string]::IsNullOrWhiteSpace($_) } | ForEach-Object { $_.Trim() }

if ($changedPaths.Count -eq 0) {
    exit 0
}

$syncScript = Join-Path $projectRoot "scripts\sync-project.ps1"
$validateScript = Join-Path $projectRoot "scripts\validate-project.ps1"
& $syncScript -ChangedPath $changedPaths
& $validateScript -Scope project

& git -C $projectRoot add BITACORA_ENTORNO.md docs/generated docs/notebooks requirements.txt
exit $LASTEXITCODE
