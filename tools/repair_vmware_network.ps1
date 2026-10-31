$ErrorActionPreference = 'Stop'
$outputDirectory = Join-Path $PSScriptRoot '..\var\vmware-repair'
New-Item -ItemType Directory -Force -Path $outputDirectory | Out-Null
try {
    $names = @('VMnetDHCP', 'VMware NAT Service')
    Get-Service -Name $names | Select-Object Name,Status,StartType |
        ConvertTo-Json | Set-Content (Join-Path $outputDirectory 'before.json')
    foreach ($name in $names) {
        Set-Service -Name $name -StartupType Automatic
        Start-Service -Name $name
    }
    Get-Service -Name $names | Select-Object Name,Status,StartType |
        ConvertTo-Json | Set-Content (Join-Path $outputDirectory 'after.json')
    'Completed' | Set-Content (Join-Path $outputDirectory 'status.txt')
} catch {
    $_.Exception.Message | Set-Content (Join-Path $outputDirectory 'status.txt')
    exit 1
}
