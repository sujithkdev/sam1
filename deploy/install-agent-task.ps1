#Requires -RunAsAdministrator
[CmdletBinding()]
param(
    [Parameter(Mandatory=$true)][string]$ServerUrl,
    [Parameter(Mandatory=$true)][string]$SystemId,
    [string]$CaCert = '',
    [switch]$Sysmon
)
$ErrorActionPreference = 'Stop'
$root = Split-Path -Parent $PSScriptRoot
$python = Join-Path $root '.venv\Scripts\python.exe'
if (!(Test-Path -LiteralPath $python)) { throw 'Install Python 3.12 dependencies in .venv first.' }
if (Get-ScheduledTask -TaskName 'BehEDR-Agent' -ErrorAction SilentlyContinue) {
    throw 'Task already exists. Stop it and review the existing configuration before replacing it.'
}
# A SYSTEM task must never execute code writable by ordinary users.
if (!$root.StartsWith(($env:ProgramFiles + '\'), [StringComparison]::OrdinalIgnoreCase)) {
    throw 'Place the agent package under Program Files before installing the SYSTEM task.'
}
& icacls.exe $root /inheritance:r /grant:r '*S-1-5-18:(OI)(CI)F' '*S-1-5-32-544:(OI)(CI)F' /T /Q
if ($LASTEXITCODE -ne 0) { throw 'Could not protect the agent installation.' }
$private = Join-Path $env:ProgramData 'BehEDR'
New-Item -ItemType Directory -Path $private -Force | Out-Null
& icacls.exe $private /inheritance:r /grant:r '*S-1-5-18:(OI)(CI)F' '*S-1-5-32-544:(OI)(CI)F' /T /Q
if ($LASTEXITCODE -ne 0) { throw 'Could not protect private agent configuration.' }
$config = Join-Path $private 'agent.json'
if (Test-Path -LiteralPath $config) { throw 'Existing configuration preserved; use it instead of re-enrolling.' }
if ($CaCert) {
    $targetCa = Join-Path $private 'server-root.crt'
    Copy-Item -LiteralPath $CaCert -Destination $targetCa
    $CaCert = $targetCa
}
$secureKey = Read-Host 'Enrollment key (hidden)' -AsSecureString
$pointer = [Runtime.InteropServices.Marshal]::SecureStringToBSTR($secureKey)
try {
    $settings = @{
        server_url=$ServerUrl; system_id=$SystemId
        api_key=[Runtime.InteropServices.Marshal]::PtrToStringBSTR($pointer)
        data_dir=(Join-Path $private 'data'); ca_cert=$CaCert; sysmon=[bool]$Sysmon
    }
    $settings | ConvertTo-Json | Set-Content -LiteralPath $config -Encoding UTF8
} finally {
    [Runtime.InteropServices.Marshal]::ZeroFreeBSTR($pointer)
    if ($settings) { $settings.api_key = $null }
}
& $python (Join-Path $root 'endpoint\run_configured.py') --config $config --check
if ($LASTEXITCODE -ne 0) { throw 'Configuration invalid. No task was registered; correct the private JSON file.' }
$action = New-ScheduledTaskAction -Execute $python -Argument ('"' + (Join-Path $root 'endpoint\run_configured.py') + '" --config "' + $config + '"') -WorkingDirectory $root
$trigger = New-ScheduledTaskTrigger -AtStartup
$principal = New-ScheduledTaskPrincipal -UserId 'SYSTEM' -LogonType ServiceAccount -RunLevel Highest
$options = New-ScheduledTaskSettingsSet -RestartCount 3 -RestartInterval (New-TimeSpan -Minutes 1) -ExecutionTimeLimit ([TimeSpan]::Zero) -MultipleInstances IgnoreNew -AllowStartIfOnBatteries -DontStopIfGoingOnBatteries
Register-ScheduledTask -TaskName 'BehEDR-Agent' -Action $action -Trigger $trigger -Principal $principal -Settings $options | Out-Null
Start-ScheduledTask -TaskName 'BehEDR-Agent'
Write-Host 'Task started. Verify logs and server acknowledgments; task state alone does not prove delivery.'
