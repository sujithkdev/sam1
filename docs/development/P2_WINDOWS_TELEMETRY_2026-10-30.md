# P2 — Windows telemetry qualification

Added 30 October 2026. Status: checklist prepared; live execution pending.
P0 remains deferred. P1 has not been closed: no guest results have been received.
This is P2 in the publication plan, not the historical Phase 2 deployment work.

## Objective and prerequisites

Measure which independently recorded Windows activities reach Sysmon, the agent
and the server, with correct process identity and timestamps. Report missed,
duplicate and unresolved observations. This is collection qualification, not a
malware accuracy experiment.

Read-only inventory can begin now. End-to-end measurements require working P1
delivery, identified installed versions and a known queue/backlog baseline.
Use the Windows lab guest, preserving its configuration, spool and event logs.

## P2.1 — Inventory the guest and source

Run in Windows guest PowerShell from the installed agent folder:

```powershell
(Get-Date).ToUniversalTime().ToString('o')
Get-CimInstance Win32_OperatingSystem | Select-Object Caption,Version,BuildNumber
Get-Service -Name Sysmon,Sysmon64 -ErrorAction SilentlyContinue |
    Select-Object Name,Status
Get-WinEvent -ListLog 'Microsoft-Windows-Sysmon/Operational' |
    Select-Object LogName,IsEnabled,RecordCount,MaximumSizeInBytes,LogMode
Get-FileHash endpoint\agent.py,endpoint\sysmon_collector.py -Algorithm SHA256
Get-WinEvent -FilterHashtable @{
    LogName='Microsoft-Windows-Sysmon/Operational'; Id=1
} -MaxEvents 5 | Select-Object TimeCreated,Id,RecordId
```

Record missing service/channel, access errors and absent process events as findings.
These checks do not install Sysmon, change permissions or enable a collector.
Record the installed Sysmon executable version and the applied configuration's
identity from the actual installation. A hash of deploy/sysmon-lab.xml alone does
not prove that configuration is applied. Record Python/dependency versions too.

Record the agent's actual startup/service settings for EDR_SYSMON and
EDR_PROCESS_SOURCE, without sharing credentials. Values in a newly opened shell
do not establish the running agent's environment. Verify fresh collector health
and effective source alongside those settings. Sysmon-primary mode requires
EDR_SYSMON=true and EDR_PROCESS_SOURCE=sysmon; do not change them mid-measurement.

## P2.2 — Independently record benign process activity

After P1 delivery is working, run a small benign smoke trial in the Windows guest.
From the agent folder, this creates a uniquely named local evidence directory:

```powershell
$p2RunId = [guid]::NewGuid().ToString('N')
$p2RunDir = Join-Path (Get-Location) ('p2-evidence-' + $p2RunId)
New-Item -ItemType Directory -Path $p2RunDir | Out-Null
$p2Started = [DateTime]::UtcNow
$p2Runs = @(1..10 | ForEach-Object {
    $begin = [DateTime]::UtcNow
    $proc = Start-Process -FilePath "$env:WINDIR\System32\cmd.exe" `
        -ArgumentList '/d /c exit 0' -PassThru -Wait -WindowStyle Hidden
    [pscustomobject]@{
        run_id=$p2RunId; trial=$_; pid=$proc.Id
        image="$env:WINDIR\System32\cmd.exe"
        arguments='/d /c exit 0'; started_utc=$begin.ToString('o')
        ended_utc=[DateTime]::UtcNow.ToString('o'); exit_code=$proc.ExitCode
    }
})
$p2Runs | ConvertTo-Json -Depth 4 |
    Set-Content -LiteralPath (Join-Path $p2RunDir 'launches.json') -Encoding UTF8
Start-Sleep -Seconds 5
$p2Ended = [DateTime]::UtcNow
$p2Events = @(Get-WinEvent -FilterHashtable @{
    LogName='Microsoft-Windows-Sysmon/Operational'; Id=1
    StartTime=$p2Started; EndTime=$p2Ended
} -ErrorAction Stop)
$p2Xml = '<Events>' + (($p2Events | ForEach-Object { $_.ToXml() }) -join "`n") + '</Events>'
$p2Xml | Set-Content -LiteralPath (Join-Path $p2RunDir 'sysmon-process-events.xml') -Encoding UTF8
Get-FileHash -LiteralPath (Join-Path $p2RunDir 'launches.json'),(Join-Path $p2RunDir 'sysmon-process-events.xml') |
    Select-Object Path,Hash | ConvertTo-Json |
    Set-Content -LiteralPath (Join-Path $p2RunDir 'hashes.json') -Encoding UTF8
Write-Output "Evidence directory: $p2RunDir"
```

Ten launches are a smoke trial, not a statistically sufficient coverage study.
The saved UTC intervals bracket launch/wait; they are not exact OS creation times.
If event retrieval fails, retain launches.json and record the error. Do not count
all events in the interval as matches: unrelated background processes may appear.
The five-second wait is an observation window, not a performance requirement.
Preserve late observations separately instead of silently excluding misses.
Raw Sysmon XML can contain unrelated private command lines; review before sharing.

## P2.3 — Reconcile source and server evidence

For each launch, match PID, image and bounded creation time against Sysmon Event 1.
Use ProcessGuid, ParentProcessGuid, EventRecordID and source UTC time for subsequent
agent/server matching. PID alone is insufficient because Windows reuses PIDs.
Retain the server's event identity and receipt time. Record missing identities as
unresolved rather than guessing. Use existing authenticated telemetry views or a
reviewed read-only export; alerts alone are not proof of process capture.

| Trial | Launch succeeded | Sysmon record/GUID | Server event ID | Identity correct/incorrect/unresolved | Delay or missing reason |
|---|---|---|---|---|---|
| Fill per launch | Pending | Pending | Pending | Pending | Pending |

Capture P1 lab_status reports before and after. Separate source capture misses,
agent collection misses, queued delivery and server processing delays. Record
clock offsets before reporting latency across machines. A quiet alert dashboard
is expected for ordinary benign activity and does not establish collector failure.

## P2.4 — Qualification matrix

All live rows are pending. Schedule disruptive cases separately in the disposable
guest after preserving evidence; the first checkpoint does not execute them.

| Case | Evidence required |
|---|---|
| Normal and short-lived processes | Independent launches matched to source and server; misses counted |
| Parent/child identity | Correct parent GUID/identity or explicit unresolved state |
| Sysmon unavailable or denied | Visible fresh error/fallback; effective polling source identified |
| Agent/collector restart | Bookmark continuity; gaps and duplicate IDs reconciled |
| Guest reboot | Collector startup, source identity and post-reboot delivery verified |
| Log rollover/reset | Visible gap/reset evidence; unrecoverable records explicitly counted/unknown |
| Queue exhaustion | Bookmark not advanced past uncommitted events; visible pressure and recovery |
| Source/receipt timing | UTC timestamps preserved; clock uncertainty and delayed delivery recorded |
| Network/file/DNS sources | Separate bounded tests only for enabled Event IDs 3/11/22 |

Do not clear the live event log or fill its queue as part of the smoke check.
FileCreate observations do not establish complete file-write or encryption coverage.
Existing synthetic regression coverage is described in phase3-sysmon.md; it does
not replace these live measurements.

## Exit gate and handoff

Retain installed source/configuration identities, OS/Sysmon/Python versions,
effective collector settings, launch records, source records, server matches,
queue/health reports and explicit missing/duplicate/incorrect/unresolved counts.
Report source capture and end-to-end coverage separately with their denominators.
Every matrix case needs an outcome or a documented scope exclusion; exclusions
narrow the qualification claim. No broad telemetry or detection claim follows
from the ten-process smoke trial.

Proceed to P3 detector contracts with the measured source limitations. P2 is not
complete until the live evidence is reviewed. No guest commands were executed
when this checklist was added.
