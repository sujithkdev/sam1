# Reliable detection workflow: verification protocol

Updated 2026-10-25. This protocol separates synthetic software tests from actual
Windows collection. No malware or destructive behavior is required.

## 1. Preserve and identify the installation

Keep credentials, agent spool and server database. Do not initialize a new server,
re-enroll the endpoint, or clear queues to hide a timeout. Record package MANIFEST.json
and configured collector source. Do not publish private configuration.

Copy tools/lab_status.py from the authoritative project into tools/ in each existing
package. It uses read-only SQLite and exports selected counters, not payloads.
Use the actual configured database path if different from these examples.

Kali, from the server package:

```bash
.venv/bin/python tools/lab_status.py --role server --database var/server/edr.db --url http://127.0.0.1:5000 > server-before.json
```

Windows guest, from the agent package (example lab data path):

```powershell
.\.venv\Scripts\python.exe tools\lab_status.py --role agent --database C:\ProgramData\BehEDR-Lab\outbox.db --url http://127.0.0.1:5000 > agent-before.json
```

For a qualified direct HTTPS deployment, use its origin and --ca with the trusted
private CA if applicable. Do not disable certificate verification. Existing
loopback HTTP requires the existing SSH tunnel. Native deployment files remain
unqualified until installed and tested inside the guests.

## 2. Diagnose delivery before testing detection

| Observation | Interpretation / next check |
|---|---|
| Kali local health fails | Check server process, configured port and startup logs |
| Kali works; Windows loopback fails | Check Windows SSH forward and its destination |
| HTTP 401/403 on delivery | Check endpoint identity and existing credential; do not blindly rotate |
| HTTP 429/503 | Check rate/storage/backlog limits and readiness |
| Queue grows, acknowledgment is stale | Transport or server acceptance is failing |
| Server pending grows after acknowledgments | Delivery works; analysis is falling behind |
| No events and no queue growth | Check collector scope, permissions and source activity |

Health probes alone do not authenticate an agent or prove ingestion. Readiness is
not a malware-free verdict. Older packages may report queue age unsupported.

## 3. Verify real collection separately

In the Windows guest, record UTC start/end times and launch Notepad once. Record
its PID and creation time, then compare its source process-creation record with
the BehEDR event. For Sysmon, preserve EventRecordID, ProcessGuid and source UTC
timestamp. Record installed Sysmon configuration and whether Event ID 1 is enabled.
Do not expect an alert merely for launching Notepad.

Repeat with a small independently recorded set of short-lived benign processes.
Count observed executions and matching collected events. Report misses and the
source used, including polling fallback. Do not manufacture attribution for file
events lacking a writer identity.

## 4. Exercise transport interruption and recovery

After normal delivery is confirmed, stop only the lab tunnel or lab server briefly.
Generate the same benign activity and capture queue counters. Restore the same
connection/server and credentials; verify queues drain and event identities do not
create duplicate stored records. Preserve before/after reports and relevant logs.
Then restart the agent and server separately and repeat. Coordinate these actions
with the operator; do not disrupt unrelated services.

## 5. Reproduce detector behavior locally

```powershell
.\.venv\Scripts\python.exe -m pytest tests/test_verified_workflow.py tests/test_transport.py tests/test_recovery.py tests/test_temporal.py tests/test_phase1.py -q
```

These are synthetic tests, not OS collection tests: an alert-producing file-event
sequence, ordinary text-file modifications and unattributed writers. Verify
evidence IDs, console detail retrieval, duplicate suppression, unchanged alert
counts during replay and no response commands. Existing recovery tests cover
late-parent reconstruction and mismatch refusal. The HTTP test restarts actual
localhost server processes while preserving the test enrollment credential.

## 6. Exit gate and reporting

For each scenario record: source/package hashes, configuration, independent label,
submitted IDs, acknowledged IDs, queued/rejected IDs, server pending/done/failed
IDs, alert evidence, and timestamps. Reconcile controlled IDs individually; broad
database counters can include unrelated background activity.

Report latency and resource use only when measured. Do not turn these synthetic
cases into a general recall/precision claim. Real detection evaluation still needs
frozen independent labels, benign endpoint-days, held-out scenarios and baselines.
