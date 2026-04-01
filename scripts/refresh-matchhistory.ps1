[CmdletBinding()]
param()

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

$projectRoot = Split-Path -Parent $PSScriptRoot
$validateScript = Join-Path $PSScriptRoot "validate-project.ps1"
$ingestScript = Join-Path $PSScriptRoot "ingest-matchhistory.ps1"

& $validateScript -Scope runtime
& $ingestScript

