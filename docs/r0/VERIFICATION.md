# R0 verification

Status: local consolidation and server installation checks passed; guest validation remains open. Implementation inventory and source ownership are documented
in ../CURRENT_STATUS.md. R0 does not claim live guest validation or malware accuracy.

The immutable Phase 0 and Phase 1 archives are checked against their original
manifest and archive member hashes. Differences between their historical source
and today's working source are expected; they are not baseline corruption.

New inventory: inventory.json records source and existing distribution hashes,
root Git availability, literal agent version, interpreter identity, baseline
integrity and explicit unknown deployed versions. No environment values,
credentials, runtime databases or logs are collected.

A clean dependency installation and package smoke check will be recorded below.
## R0 local results — 2026-10-24

- Authoritative register created: docs/CURRENT_STATUS.md. README and the historical
  master plan now point to it. No archive, baseline or runtime evidence was removed.
- Baseline integrity: Phase 0 and Phase 1 archive SHA256 and every archived member
  match their original manifests. Current source drift is expected.
- Generated-package inventory precheck: zero manifest mismatches across inspected
  server/agent copies. Package matches are integrity checks, not deployment proof.
- Fresh server environment: var/r0-clean-verified, created without system site
  packages; installed requirements/server.lock successfully. pip check passed.
- Standalone package: dist/behedr-r0-2026-10-24. Packaged application initialization,
  health/readiness in test mode, anonymous rejection, login, all console read APIs,
  operations API, dashboard assets, logout and revoked-session rejection passed.
- Background worker disabled during this smoke test. No collectors, malware,
  firewall changes, external uploads or live guest tests were executed.
- Ruff passed for the two R0 tools. No detector implementation changed, so the
  prior 186-test regression result is historical, not presented as rerun by R0.
- A sandboxed venv creation initially failed in ensurepip. A fresh environment
  outside that sandbox completed successfully; the failed directory is not used.

Evidence logs: var/r0-clean-install-pip.log, var/r0-clean-smoke.log.
Reproduction: create a fresh Python 3.12 venv; install requirements/server.lock;
run pip check; then run tools/verify_r0_install.py with an absolute server-package
folder argument. The script creates disposable state under var and does not use
production credentials. Run tools/inventory_r0.py --output NEW_REPORT.json to
create a non-overwriting inventory. Compare hashes rather than editing old reports.

## Open gates and next action

Local R0 is complete when inventory.json and the dependency checks below are
recorded. Independent clean Kali installation and deployed guest versions remain
open; these are explicit R1 prerequisites, not implied passes. The live delivery
timeout remains the first operational investigation. No GitHub update was made.

## Agent installation result

Fresh var/r0-agent-clean installation of requirements/endpoint.txt passed; pip
check passed; all 9 packaged endpoint Python modules compiled; psutil, requests
and win32evtlog imported. Collectors were not started. This is not full live agent
execution verification. The resolved pywin32 was 312; the declared >=311 range
and unpinned transitive dependencies remain reproducibility work for R2/R6.

Resolved environment records: server-environment.json and agent-environment.json.
Source inventory covers 156 allowlisted files; excludes nested R0 output artifacts
so recording verification cannot recursively change its own identity. Both old
baselines passed integrity checks, and inspected package manifests had zero
mismatches. R0 local deliverables are complete. Live guest/deployment qualification
is explicitly pending, not a completed global installation claim.
