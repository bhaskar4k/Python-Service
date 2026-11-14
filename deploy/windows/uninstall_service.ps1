param(
    [string]$ServiceName = "my_service",
    [string]$Nssm = "nssm.exe"
)
$ErrorActionPreference = "Continue"
& $Nssm stop   $ServiceName
& $Nssm remove $ServiceName confirm
