[CmdletBinding()]
param()

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

. (Join-Path $PSScriptRoot "_governance.ps1")

Invoke-GovernedCommand `
    -CommandId "refresh_matchhistory" `
    -CommandTokens @(".\scripts\refresh-matchhistory.ps1") `
    -ArtifactsUpdated @(
        "data/bronze/matchhistory/raw",
        "data/bronze/matchhistory/manifests",
        "docs/generated/project-status.md",
        "BITACORA_ENTORNO.md"
    ) `
    -Action {
        $validateScript = Join-Path $PSScriptRoot "validate-project.ps1"
        $ingestScript = Join-Path $PSScriptRoot "ingest-matchhistory.ps1"

        & $validateScript -Scope runtime
        & $ingestScript
    }
