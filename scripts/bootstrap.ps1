[CmdletBinding()]
param()

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

$projectRoot = Split-Path -Parent $PSScriptRoot
$venvDir = Join-Path $projectRoot ".venv"
$venvPython = Join-Path $venvDir "Scripts\\python.exe"
$srcPath = Join-Path $projectRoot "src"
$refreshScript = Join-Path $projectRoot "scripts\\refresh-matchhistory.ps1"
$taskConfigJson = $null

if (-not (Test-Path $venvPython)) {
    if (Test-Path $venvDir) {
        throw "'.venv' existe, pero no contiene '$venvPython'. Recreate el entorno antes de continuar."
    }

    $pyCommand = Get-Command py -ErrorAction SilentlyContinue
    if (-not $pyCommand) {
        throw "No se encontro el lanzador 'py'. Instala Python 3.13 o crea '.venv' manualmente."
    }

    & py -3.13 -m venv $venvDir
}

New-Item -ItemType Directory -Force -Path `
    (Join-Path $projectRoot "data\\bronze\\matchhistory\\raw"), `
    (Join-Path $projectRoot "data\\bronze\\matchhistory\\inbox"), `
    (Join-Path $projectRoot "data\\bronze\\matchhistory\\manifests"), `
    (Join-Path $projectRoot "data\\silver"), `
    (Join-Path $projectRoot "data\\gold"), `
    (Join-Path $projectRoot "logs\\ingestion"), `
    (Join-Path $projectRoot "models"), `
    (Join-Path $projectRoot "notebooks") | Out-Null

& $venvPython -m pip install --upgrade pip
if ($LASTEXITCODE -ne 0) {
    throw "Fallo la actualizacion de pip dentro del entorno virtual."
}

& $venvPython -m pip install -r (Join-Path $projectRoot "requirements.txt")
if ($LASTEXITCODE -ne 0) {
    throw "Fallo la instalacion de dependencias desde requirements.txt."
}

& $venvPython -m pip install -e $projectRoot
if ($LASTEXITCODE -ne 0) {
    throw "Fallo la instalacion editable del paquete local 'football-ml'."
}

& $venvPython -m ipykernel install --prefix $venvDir --name football-ml --display-name "football-ml (.venv)"
if ($LASTEXITCODE -ne 0) {
    throw "Fallo el registro del kernel 'football-ml (.venv)'."
}

if ([string]::IsNullOrWhiteSpace($env:PYTHONPATH)) {
    $env:PYTHONPATH = $srcPath
} else {
    $env:PYTHONPATH = "$srcPath;$($env:PYTHONPATH)"
}

& (Join-Path $PSScriptRoot "validate-project.ps1") -Scope project
if ($LASTEXITCODE -ne 0) {
    throw "La validacion final del proyecto fallo."
}

$taskConfigJson = & $venvPython -c "from football_ml.config import load_automation_config; import json; cfg = load_automation_config(); print(json.dumps({'task_name': cfg.task_name, 'schedule_time': cfg.schedule_time}))"
if ($LASTEXITCODE -ne 0) {
    throw "No se pudo leer la configuracion de automatizacion desde 'config\\ingestion.toml'."
}

$taskConfig = $taskConfigJson | ConvertFrom-Json
$currentIdentity = [System.Security.Principal.WindowsIdentity]::GetCurrent()
$userId = $currentIdentity.User.Value
$author = "$env:USERDOMAIN\$env:USERNAME"
$scheduleDate = Get-Date
$scheduleTimeParts = $taskConfig.schedule_time -split ":"
$scheduleBoundary = Get-Date -Year $scheduleDate.Year -Month $scheduleDate.Month -Day $scheduleDate.Day -Hour ([int]$scheduleTimeParts[0]) -Minute ([int]$scheduleTimeParts[1]) -Second 0
$taskXmlPath = Join-Path ([System.IO.Path]::GetTempPath()) "$($taskConfig.task_name).xml"
$taskXml = @"
<?xml version="1.0" encoding="UTF-16"?>
<Task version="1.2" xmlns="http://schemas.microsoft.com/windows/2004/02/mit/task">
  <RegistrationInfo>
    <Date>$($scheduleBoundary.ToString("s"))</Date>
    <Author>$author</Author>
    <URI>\$($taskConfig.task_name)</URI>
  </RegistrationInfo>
  <Principals>
    <Principal id="Author">
      <UserId>$userId</UserId>
      <LogonType>InteractiveToken</LogonType>
      <RunLevel>LeastPrivilege</RunLevel>
    </Principal>
  </Principals>
  <Settings>
    <MultipleInstancesPolicy>IgnoreNew</MultipleInstancesPolicy>
    <DisallowStartIfOnBatteries>false</DisallowStartIfOnBatteries>
    <StopIfGoingOnBatteries>false</StopIfGoingOnBatteries>
    <AllowHardTerminate>true</AllowHardTerminate>
    <StartWhenAvailable>true</StartWhenAvailable>
    <AllowStartOnDemand>true</AllowStartOnDemand>
    <Enabled>true</Enabled>
    <Hidden>false</Hidden>
    <RunOnlyIfIdle>false</RunOnlyIfIdle>
    <WakeToRun>false</WakeToRun>
    <ExecutionTimeLimit>PT72H</ExecutionTimeLimit>
    <Priority>7</Priority>
  </Settings>
  <Triggers>
    <CalendarTrigger>
      <StartBoundary>$($scheduleBoundary.ToString("s"))</StartBoundary>
      <Enabled>true</Enabled>
      <ScheduleByDay>
        <DaysInterval>1</DaysInterval>
      </ScheduleByDay>
    </CalendarTrigger>
  </Triggers>
  <Actions Context="Author">
    <Exec>
      <Command>powershell.exe</Command>
      <Arguments>-NoProfile -ExecutionPolicy Bypass -File "$refreshScript"</Arguments>
      <WorkingDirectory>$projectRoot</WorkingDirectory>
    </Exec>
  </Actions>
</Task>
"@

Set-Content -LiteralPath $taskXmlPath -Value $taskXml -Encoding Unicode
& schtasks.exe /Create /TN $taskConfig.task_name /XML $taskXmlPath /F | Out-Null
if ($LASTEXITCODE -ne 0) {
    throw "No se pudo registrar la tarea programada '$($taskConfig.task_name)' con schtasks."
}

& schtasks.exe /Query /TN $taskConfig.task_name | Out-Null
if ($LASTEXITCODE -ne 0) {
    throw "No se pudo confirmar el registro de la tarea programada '$($taskConfig.task_name)'."
}

Remove-Item -LiteralPath $taskXmlPath -ErrorAction SilentlyContinue
