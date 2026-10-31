# P1 live transport qualification — 30 October 2026

P0 is deferred at the user's request. P1 live qualification is open; the user
will run guest commands. No guest deployment or delivery result is assumed.

## First checkpoint: read-only diagnostics

Run in the existing package directory on each guest. Replace example paths with
the actual installation paths. Keep the server, agent and existing tunnel running.
Do not print .env, API keys or private JSON configuration. Do not initialize,
re-enroll, delete queues or change timeouts.

### Kali server

```bash
cd /actual/path/to/server
date -u
hostname -I
.venv/bin/python --version
sha256sum manage.py backend/server/ingestion.py backend/server/core/temporal.py
curl --max-time 5 -sS -w '\nHTTP %{http_code}\n' http://127.0.0.1:5000/health
curl --max-time 5 -sS -w '\nHTTP %{http_code}\n' http://127.0.0.1:5000/ready
.venv/bin/python tools/lab_status.py --role server --database var/server/edr.db --url http://127.0.0.1:5000 | tee server-p1-before.json
```

Use the actual database location if EDR_DATA_DIR was customized. The URL assumes
the existing documented port-5000 SSH lab deployment; use the configured origin
for another deployment. A failing curl is evidence, not a reason to initialize.

### Windows guest

Open PowerShell in the existing agent package directory:

```powershell
Get-Date -AsUTC -Format o
.\.venv\Scripts\python.exe --version
Get-FileHash endpoint\agent.py,endpoint\spool.py,endpoint\transport.py -Algorithm SHA256
Select-String -Path endpoint\spool.py,endpoint\transport.py -Pattern 'after_path|_last_path'
Test-NetConnection 127.0.0.1 -Port 5000
curl.exe --max-time 5 -sS -w '\nHTTP %{http_code}\n' http://127.0.0.1:5000/health
curl.exe --max-time 5 -sS -w '\nHTTP %{http_code}\n' http://127.0.0.1:5000/ready
.\.venv\Scripts\python.exe tools\lab_status.py --role agent --database C:\ProgramData\BehEDR-Lab\outbox.db --url http://127.0.0.1:5000 | Tee-Object agent-p1-before.json
```

On Windows PowerShell 5.1 replace Get-Date -AsUTC with:

```powershell
(Get-Date).ToUniversalTime().ToString('o')
```

Use the actual agent database path from the existing startup configuration.
The loopback URL assumes the existing SSH lab tunnel. For configured HTTPS use
that URL and the trusted CA option from verification-workflow.md.

If tools/lab_status.py is absent, copy only the authoritative tools/lab_status.py
into tools/ in that guest package, or report it missing. It opens SQLite read-only.
Missing database errors do not create a replacement database.

Return the console outputs and both before JSON reports, excluding secrets.
The hash and source-string checks identify deployment differences; matching
strings alone do not prove the entire installed package matches.

Expected authoritative sender hashes measured on 30 October:

```text
endpoint/spool.py      5E5B13CCA02F0983D5C91A6133E19C1B26BC19DC804424BEF88F893F1AB7CC20
endpoint/transport.py  6754DD92CF21277DF546A00209FE5E3CAE3CE334DCAADB89FB5B07908D41A8BD
```

## Next checkpoints, after reviewing baseline results

1. Diagnose health/readiness and identify exact deployed source differences.
2. Update the fixed endpoint source with a rollback copy, retaining credentials,
   configuration, virtual environment and outbox. Confirm installed hashes.
3. Record a benign process launch independently and match its event on the server.
4. Record before/after IDs and queue counters for a brief lab-only disconnect and
   reconnect, then agent and server restarts separately.
5. Reconcile unique submitted, accepted, pending, rejected and processed IDs.
   Aggregate counters alone are insufficient when background collection continues.

| Scenario | Local regression | Live guest evidence |
|---|---|---|
| Normal delivery | Existing transport tests | Pending |
| Failed route while another route progresses | Existing fairness tests | Pending |
| Lost acknowledgment and deduplication | Existing transport tests | Pending |
| Invalid/partial acknowledgment | Existing transport tests | Pending |
| Disconnect, reopen and restart recovery | Existing HTTP restart test | Pending |

## Local preparation limitations

Full local regression on 30 October: 207 passed, 1 failed, 3 warnings in 170.80s.
JUnit: var/p01-20261030-retry.xml. The failed HTTP restart test encountered
WinError 10013 in Waitress's local trigger socket. The initial attempt also hit
temporary-directory access restrictions; the full run used project-local TEMP/TMP.
Ruff passed for backend, endpoint, manage.py, tests and diagnostic/package tools.
The isolated HTTP restart test then passed outside the sandbox in 20.64s;
JUnit: var/p1-http-20261030.xml. This was a one-test rerun, not another full suite.
The split-package regression passed, although the separate distribution build
below encountered an OS security read block. No complete new distributable is claimed.

An attempted fresh split package at dist/behedr-p1-2026-10-30 failed while reading
endpoint/yara_scanner.py. Windows reported that the file contains a virus or
potentially unwanted software. This is an OS security report, not an independent
determination that the source is malicious. No protection was disabled or bypassed.
The incomplete destination was removed during the 30 October cleanup; no new
qualified distribution was produced.

P1 is complete only after the deployed versions and live scenario evidence are
recorded. Local regression success cannot close the live gate.

Next: [P2 Windows telemetry qualification](P2_WINDOWS_TELEMETRY_2026-10-30.md).
Read-only P2 inventory can begin before P1 closes; end-to-end measurements require
working delivery and a known backlog baseline.
