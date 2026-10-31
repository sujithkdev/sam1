# Phase 2 verification — 22 October 2026

## Result

The Docker/backend portion passed. The user's existing Windows 10 VMware VM was identified, snapshotted and started. Guest login and guest-to-server TLS connectivity remain open; no claim of complete endpoint or production validation is made.

Environment: Docker Desktop 4.94.0, Engine 29.8.2, Compose v5.5.1, Linux/amd64 containers on the Windows development host. Dedicated project: `behedr-phase2`. Existing unrelated containers were not changed.

## Executed checks

| Check | Result |
|---|---|
| Clean backend image build from server.lock | Passed |
| Compose validation | Passed |
| Non-root application and read-only application filesystem | Passed |
| Health/readiness and SQLite integrity | Passed |
| Local HTTPS with explicit CA and hostname verification | Passed |
| Anonymous status access denied | Passed |
| Login, Secure/HttpOnly/SameSite cookie and authenticated status | Passed |
| CSRF rejection and authenticated test enrollment | Passed |
| Duplicate HTTPS event delivery stored once | Passed |
| Server restart preserves database and session | Passed |
| Container recreation preserves data volume | Passed |
| Online backup, restore to fresh temporary directory, restored app readiness and event integrity | Passed |
| Weak session secret rejected on startup | Passed |
| Container dependency consistency | Passed |
| Fresh Linux Python 3.12 virtual environment from dev.lock | 87 tests passed in 11.45 seconds; pip check and Ruff passed |
| Local lint of three Phase 2 tooling scripts | Passed |
| Final Windows regression after shutdown fix | 88 passed in 57.98 seconds; lint passed |
| Rebuilt-image deployment workflow | All 12 checks passed again after shutdown fix |
| Final Docker stop after shutdown fix | Server exit code 0; volumes preserved |

Machine-readable Docker check results: `var/phase2/results.json` relative to the project root. That runtime file has no session secret or test password. Configuration and generated CA material remain in the runtime directory and must not be published as production configuration.

An early verifier attempt ran before Caddy created its CA. A bounded wait for the CA was added. A clean-test attempt encountered a no-execute temporary filesystem; execution was enabled only on the disposable test container's temporary mount. Neither correction disables production TLS or changes the deployed server's filesystem policy.

Final shutdown inspection initially found exit code 137 after Docker's grace period. `manage.py` now handles SIGTERM through Waitress shutdown and asks the analysis worker to stop taking new work and finish its current item. A regression covers in-flight worker shutdown. The image was rebuilt, the deployment workflow rerun, and a separate stop returned exit code 0. The verifier now includes this exit-code assertion for future runs.

## VMware inventory

VM: `Windows 10 x64`, at `C:\Users\ASUS\Documents\Virtual Machines\Windows 10 x64\Windows 10 x64.vmx`. Initially powered off, 2 vCPUs, 2048 MB RAM, NAT networking, no snapshots. Created and verified `BehEDR-phase2-baseline-20261022`, then powered on with `vmrun start ... nogui`. Configuration was not changed. VMware Tools reports installed; initial IP query reported Tools not yet running. Guest OS build, login, available disk, time sync and server reachability are not verified by VMX metadata. No guest credentials were requested or recorded.

## Boundaries

The restored application was exercised in a new temporary directory inside the lab container, not by overwriting or taking over the live volume. It verifies application startup and retained event data, not an independent-host disaster recovery exercise. Restarts were tested with accepted inert telemetry; deterministic detector-state recovery and crash-under-load remain future work.

The fresh Linux run validates the current Phase 1/2 source, not the exact archived Phase 0 ZIP; do not retroactively label that old snapshot independently reproduced. Source was mounted read-only in the disposable test container. No private configuration was copied into the application image.

Public certificate issuance/renewal, external Windows-agent connectivity, service/reboot behavior, malware efficacy, load limits and vulnerability scanning were not tested. Lab services are stopped after validation with named volumes and backups preserved. Use the runbook to restart; no production administrator was created.

See [deployment runbook](../operations/phase2-deployment.md) for commands, trust handling, remaining Windows VM requirements and cleanup boundaries.
