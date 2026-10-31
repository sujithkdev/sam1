# Local verification — 2026-09-26

## Development-tool monitoring follow-up

After adding bounded ancestor snapshots, development-tool intent rules, server-side workspace policy and persisted assessment evidence, the expanded suite passed **63 tests in 27.57 seconds**. Ruff checks passed. New cases cover normal builds, credential references, security changes, persistence, elevation, download/execution indicators, missing/malformed ancestry, PID identity validation, exact and expired approvals, workspace path boundaries, retained sensitive alerts despite approval, end-to-end evidence retrieval, access-denied collectors and ancestry depth limits. These use synthetic telemetry and mocked collection; no coding-tool permissions were changed and no real suspicious command was executed. The original deployment and Windows integration limitations below still apply.

## Original hardening verification

Environment: Windows, Python 3.12.14, project-local `.venv`.

| Check | Result |
| --- | --- |
| `python -m pytest -q` | 46 passed in 15.87 seconds |
| Ruff checks: syntax and selected runtime-error rules | Passed across backend, endpoint, launcher and tests |
| `python -m compileall -q backend endpoint manage.py` | Passed |
| Node `--check backend/server/static/dashboard.js` | Passed |
| Server dependency audit | 17 locked packages; no known vulnerabilities reported |
| Isolated HTTP preview server | Started successfully and shut down after its time limit |
| Browser visual/interaction check | Not completed: browser tool stalled, then connection was refused after preview expired |
| Container build and Compose startup | Not run; Docker executable unavailable in this environment |
| Windows service installation, reboot and real collectors | Not run |
| Hosted Windows/Linux CI | Configured, not run in this session |

The test suite exercises no-default-user behavior, cookie CSRF, role enforcement, token revocation/rotation, host impersonation rejection, malformed batches, durable deduplication, concurrent acceptance, failure retries, first-alert persistence, parent-rule constraints, evidence retention, independent stream subscribers, process-instance graphs, heartbeat metadata, command leases/expiry/ownership, endpoint spool recovery, command execution reservations, PID/hash mismatch refusal, literal signature paths, XML parsing, record-ID queries, configuration validation, a single-server lock and SQLite backup consistency.

Tests use temporary databases and synthetic events. Process-termination checks use mocks and inert test files; they do not terminate real processes. No live agent, firewall change, external alert notification, service installation or production deployment was performed.

See `dependency-audit.json` for the machine-readable server audit. This is an advisory-database snapshot, not a guarantee of security; it does not cover optional endpoint packages, container images or untested inherited modules. Locks pin versions without artifact hashes.

The implementation is a release candidate. Windows integration, load/soak testing, detection-quality evaluation, visual browser testing, disaster-recovery exercises and independent security review remain necessary before a production rating is justified.
