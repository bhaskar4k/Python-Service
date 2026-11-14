# Install data-processing as a Windows Service using NSSM.
# Usage (run in an elevated PowerShell):
#   .\install_service.ps1 -AppDir "C:\Services\data-processing" -Nssm "C:\tools\nssm.exe"
param(
    [string]$ServiceName = "data-processing",
    [Parameter(Mandatory = $true)][string]$AppDir,
    [string]$Nssm = "nssm.exe",
    [string]$LogDir = "$env:ProgramData\data-processing\logs"
)

$ErrorActionPreference = "Stop"

if (-not (Test-Path $AppDir)) {
    throw "AppDir '$AppDir' does not exist. Copy the project there first."
}

$venv = Join-Path $AppDir "venv"
if (-not (Test-Path $venv)) {
    Write-Host "Creating venv..."
    python -m venv $venv
    & "$venv\Scripts\pip.exe" install --upgrade pip
    & "$venv\Scripts\pip.exe" install -r (Join-Path $AppDir "requirements.txt")
}

New-Item -ItemType Directory -Force $LogDir | Out-Null

$python = Join-Path $venv "Scripts\python.exe"
$main   = Join-Path $AppDir "main.py"

# Remove any previous install, then install fresh.
try { & $Nssm stop     $ServiceName | Out-Null } catch {}
try { & $Nssm remove   $ServiceName confirm | Out-Null } catch {}

& $Nssm install $ServiceName $python $main
& $Nssm set $ServiceName AppDirectory $AppDir
& $Nssm set $ServiceName AppEnvironmentExtra "PYTHONUNBUFFERED=1" "SERVICE_LOG_DIR=$LogDir"
& $Nssm set $ServiceName AppStdout (Join-Path $LogDir "service.out.log")
& $Nssm set $ServiceName AppStderr (Join-Path $LogDir "service.err.log")
& $Nssm set $ServiceName AppRotateFiles 1
& $Nssm set $ServiceName AppRotateBytes 5242880
& $Nssm set $ServiceName Start SERVICE_AUTO_START
& $Nssm set $ServiceName AppExit Default Restart
& $Nssm set $ServiceName AppRestartDelay 5000

& $Nssm start $ServiceName
& $Nssm status $ServiceName
