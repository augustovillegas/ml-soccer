[CmdletBinding()]
param()

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

$script:ProjectRoot = Split-Path -Parent $PSScriptRoot
$script:GovernanceConfigPath = Join-Path $script:ProjectRoot "config\project_governance.toml"
$script:CommandLedgerPath = Join-Path $script:ProjectRoot "logs\governance\command-ledger.jsonl"
$script:VenvPython = Join-Path $script:ProjectRoot ".venv\Scripts\python.exe"

function ConvertTo-CommandLine {
    param(
        [string[]]$Tokens
    )

    $formattedTokens = foreach ($token in $Tokens) {
        if ($token -match '\s') {
            '"' + $token.Replace('"', '\"') + '"'
        } else {
            $token
        }
    }
    return ($formattedTokens -join " ").Trim()
}

function Get-TomlStringArrayValue {
    param(
        [string]$Body,
        [string]$Key
    )

    $match = [regex]::Match($Body, "(?m)^\s*$([regex]::Escape($Key))\s*=\s*\[(?<items>[^\]]*)\]\s*$")
    if (-not $match.Success) {
        return @()
    }

    $itemsText = $match.Groups["items"].Value.Trim()
    if ([string]::IsNullOrWhiteSpace($itemsText)) {
        return @()
    }

    $values = New-Object System.Collections.Generic.List[string]
    foreach ($rawValue in ($itemsText -split ",")) {
        $value = $rawValue.Trim()
        if ($value.StartsWith('"') -and $value.EndsWith('"')) {
            $value = $value.Substring(1, $value.Length - 2)
        }
        if (-not [string]::IsNullOrWhiteSpace($value)) {
            $values.Add($value)
        }
    }
    return $values.ToArray()
}

function Get-TomlStringValue {
    param(
        [string]$Body,
        [string]$Key
    )

    $match = [regex]::Match($Body, "(?m)^\s*$([regex]::Escape($Key))\s*=\s*""([^""]+)""\s*$")
    if (-not $match.Success) {
        return ""
    }
    return $match.Groups[1].Value
}

function Get-TomlBoolValue {
    param(
        [string]$Body,
        [string]$Key
    )

    $match = [regex]::Match($Body, "(?m)^\s*$([regex]::Escape($Key))\s*=\s*(true|false)\s*$")
    if (-not $match.Success) {
        return $false
    }
    return $match.Groups[1].Value -eq "true"
}

function Get-OfficialCommandDefinitionFromGovernance {
    param(
        [Parameter(Mandatory = $true)]
        [string]$CommandId
    )

    if (-not (Test-Path $script:GovernanceConfigPath)) {
        throw "No existe '$script:GovernanceConfigPath'."
    }

    $content = Get-Content -LiteralPath $script:GovernanceConfigPath -Raw -Encoding UTF8
    $matches = [regex]::Matches($content, "(?ms)^\[\[official_commands\]\]\s*(?<body>.*?)(?=^\[\[official_commands\]\]|\z)")

    foreach ($entry in $matches) {
        $body = $entry.Groups["body"].Value
        $candidateId = Get-TomlStringValue -Body $body -Key "command_id"
        if ($candidateId -ne $CommandId) {
            continue
        }

        return [pscustomobject]@{
            CommandId = $candidateId
            Purpose = Get-TomlStringValue -Body $body -Key "purpose"
            Verification = Get-TomlStringValue -Body $body -Key "verification"
            ImpactedArtifacts = @(Get-TomlStringArrayValue -Body $body -Key "impacted_artifacts")
            DocumentInBitacora = Get-TomlBoolValue -Body $body -Key "document_in_bitacora"
        }
    }

    throw "No se encontro una entrada [[official_commands]] para '$CommandId'."
}

function Write-CommandLedgerEvent {
    param(
        [string]$CommandId,
        [string]$CommandLine,
        [string[]]$NormalizedArgs,
        [string]$Goal,
        [string]$Status,
        [string]$Verification,
        [string[]]$ArtifactsUpdated,
        [string]$ErrorMessage
    )

    New-Item -ItemType Directory -Force -Path (Split-Path -Parent $script:CommandLedgerPath) | Out-Null

    $payload = [ordered]@{
        timestamp_utc = (Get-Date).ToUniversalTime().ToString("yyyy-MM-ddTHH:mm:ssZ")
        command_id = $CommandId
        command = $CommandLine
        normalized_args = @($NormalizedArgs)
        goal = $Goal
        status = $Status
        verification = $Verification
        artifacts_updated = @($ArtifactsUpdated)
    }

    if (-not [string]::IsNullOrWhiteSpace($ErrorMessage)) {
        $payload.error_message = $ErrorMessage
    }

    $maxAttempts = 10
    $attempt = 0
    $sleepMilliseconds = 100
    $serializedPayload = ($payload | ConvertTo-Json -Compress)
    $utf8NoBom = [System.Text.UTF8Encoding]::new($false)

    while ($attempt -lt $maxAttempts) {
        $attempt += 1
        $stream = $null
        $writer = $null
        try {
            $stream = [System.IO.FileStream]::new(
                $script:CommandLedgerPath,
                [System.IO.FileMode]::Append,
                [System.IO.FileAccess]::Write,
                [System.IO.FileShare]::ReadWrite
            )
            $writer = [System.IO.StreamWriter]::new($stream, $utf8NoBom)
            $writer.WriteLine($serializedPayload)
            $writer.Flush()
            return
        } catch [System.IO.IOException] {
            if ($attempt -ge $maxAttempts) {
                throw
            }
            Start-Sleep -Milliseconds $sleepMilliseconds
        } finally {
            if ($writer) {
                $writer.Dispose()
            } elseif ($stream) {
                $stream.Dispose()
            }
        }
    }
}

function Invoke-ProjectAutoSync {
    param(
        [string[]]$ChangedPaths
    )

    if (-not $ChangedPaths -or $ChangedPaths.Count -eq 0) {
        return
    }

    if ($env:FOOTBALL_ML_SUPPRESS_GOVERNED_SYNC -eq "1") {
        return
    }

    if (-not (Test-Path $script:VenvPython)) {
        return
    }

    $arguments = @("-m", "football_ml.sync_project")
    foreach ($changedPath in ($ChangedPaths | Sort-Object -Unique)) {
        $arguments += @("--changed-path", $changedPath)
    }

    $previousValue = $env:FOOTBALL_ML_SUPPRESS_GOVERNED_SYNC
    $env:FOOTBALL_ML_SUPPRESS_GOVERNED_SYNC = "1"
    try {
        & $script:VenvPython @arguments | Out-Null
        if ($LASTEXITCODE -ne 0) {
            throw "La resincronizacion automatica gobernada fallo."
        }
    } finally {
        if ($null -eq $previousValue) {
            Remove-Item Env:FOOTBALL_ML_SUPPRESS_GOVERNED_SYNC -ErrorAction SilentlyContinue
        } else {
            $env:FOOTBALL_ML_SUPPRESS_GOVERNED_SYNC = $previousValue
        }
    }
}

function Invoke-GovernedCommand {
    param(
        [Parameter(Mandatory = $true)]
        [string]$CommandId,
        [Parameter(Mandatory = $true)]
        [string[]]$CommandTokens,
        [string[]]$NormalizedArgs = @(),
        [string[]]$ArtifactsUpdated = @(),
        [string[]]$AutoSyncChangedPaths = @(),
        [Parameter(Mandatory = $true)]
        [scriptblock]$Action
    )

    $definition = Get-OfficialCommandDefinitionFromGovernance -CommandId $CommandId
    $commandLine = ConvertTo-CommandLine -Tokens $CommandTokens
    $effectiveArtifacts = if ($ArtifactsUpdated.Count -gt 0) { $ArtifactsUpdated } else { $definition.ImpactedArtifacts }

    Write-CommandLedgerEvent `
        -CommandId $CommandId `
        -CommandLine $commandLine `
        -NormalizedArgs $NormalizedArgs `
        -Goal $definition.Purpose `
        -Status "started" `
        -Verification $definition.Verification `
        -ArtifactsUpdated $effectiveArtifacts `
        -ErrorMessage ""

    $completed = $false
    $capturedError = ""
    try {
        & $Action
        $completed = $true
    } catch {
        $capturedError = $_.Exception.Message
        throw
    } finally {
        $status = if ($completed) { "ok" } else { "failed" }
        Write-CommandLedgerEvent `
            -CommandId $CommandId `
            -CommandLine $commandLine `
            -NormalizedArgs $NormalizedArgs `
            -Goal $definition.Purpose `
            -Status $status `
            -Verification $definition.Verification `
            -ArtifactsUpdated $effectiveArtifacts `
            -ErrorMessage $capturedError

        if ($completed) {
            $syncPaths = New-Object System.Collections.Generic.List[string]
            foreach ($path in $AutoSyncChangedPaths) {
                if (-not [string]::IsNullOrWhiteSpace($path)) {
                    $syncPaths.Add($path.Replace("\", "/"))
                }
            }
            if ($definition.DocumentInBitacora) {
                $syncPaths.Add("logs/governance/command-ledger.jsonl")
            }
            if ($syncPaths.Count -gt 0) {
                Invoke-ProjectAutoSync -ChangedPaths $syncPaths.ToArray()
            }
        }
    }
}
