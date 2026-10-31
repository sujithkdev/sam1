# Phase 6 closeout review — 2026-10-23

Status: code and deployment verification completed; live Windows calibration
deferred at the user's request. Phase 7 has not started. This document does not
mark unexecuted experiments as passed.

## Fixes made during review

- Sysmon ParentImage now survives endpoint and server normalization as
  `parent_exe_path`. Other collectors may still lack this field; missing data
  never matches a ParentImage condition.
- Sigma YAML rejects duplicate mapping keys, nonstring mapping keys and rule
  files above 64 KiB. Unsupported syntax remains fail-closed at startup.
- Deployment verifier now sends an inert process event through authenticated
  HTTPS, waits for worker completion, compares the recorded rule hash with the
  source catalog, and verifies evidence survives restart. No captured command
  line is executed by the test.
- Added a real-event guest collector and a checksum-verifying offline reviewer.
  The reviewer matches scenario PID, image and event time, and treats failed
  commands or missing observations as inconclusive. It reports no malware
  accuracy metric.

## Evidence and scope

The full regression suite after the core fixes passed 137 tests in 58.75 seconds.
All 3 additional offline-review tests passed in 9.58 seconds, covering benign
observation, failed commands and modified evidence. Ruff passed. PowerShell syntax was checked without running the guest
collector on the host. These are software checks, not live malware experiments.

The dedicated Docker lab was rebuilt from the revised source with the existing
pinned base images. Deployment results are saved in
`var/phase6/deployment/results.json`; earlier Phase 2 results are preserved.
The verifier checks non-root execution, read-only application filesystem,
database integrity, TLS hostname/CA validation, anonymous rejection, secure
login cookies, CSRF, enrollment, ingestion deduplication, Sigma evidence,
restart/recreation, backup restore, weak-secret rejection, dependency consistency
and graceful shutdown. Existing lab data and backup files are retained.
All deployment checks passed; the Docker lab was stopped cleanly with server
exit code 0 after verification.

## Run the Windows guest check later

The existing VMware snapshot was verified: `BehEDR-phase2-baseline-20261022`.
The VM was started, but VMware Tools was not running. The user chose to run the
prepared script later; no guest execution or live results are claimed.

1. Sign in to the disposable Windows 10 VMware guest. Ensure Sysmon is installed
   and its Operational channel records process-create events with command lines.
   This script does not install Sysmon or change audit settings.
2. Copy `tools/phase6_guest_collect.ps1` into the guest, for example
   `C:\BehEDRLab\phase6_guest_collect.ps1`.
3. Open an elevated PowerShell **inside the guest** and run:

   ```powershell
   powershell.exe -NoProfile -ExecutionPolicy Bypass -File C:\BehEDRLab\phase6_guest_collect.ps1
   ```

   Bypass applies to this process only; it does not change the machine policy.
   Review the script before running it. It requires a VMware guest and runs only
   `cmd /d /c ver`, `vssadmin list shadows` and `bcdedit /enum`. These query state;
   they do not delete shadow copies, disable recovery or execute malware.
4. Copy the generated run directory from `C:\BehEDRLab\phase6\<run-id>` back
   into the host project, for example `var\phase6\guest\<run-id>`.
   Review it first: Sysmon command lines may contain private information.
5. From the project root on the host:

   ```powershell
   .\.venv\Scripts\python.exe tools/phase6_review_bundle.py var/phase6/guest/<run-id> --output var/phase6/guest-review.json
   ```

   Replace `<run-id>` with the actual directory name. The output path must be
   new; the reviewer will not overwrite an earlier report. Preserve stdout and
   stderr files to investigate nonzero exit codes. The script leaves evidence
   in place and performs no automatic upload.

## Gates still open

| Gate | Current status | Required evidence |
|---|---|---|
| Live Windows process collection | Prepared; user deferred execution | Guest bundle with observed successful scenarios |
| Broad benign calibration | Not run | Builds, installers, backups, browser and administrator workload traces with independent labels |
| Attack behavior calibration | Not run | Authorized isolated emulation, independent execution verification, snapshot recovery |
| Frozen tuning/held-out split | Not run | Scenario/host/time separation and catalog hashes frozen before held-out evaluation |
| Existing detector versus added rules | Not measured | Identical traces, adjudicated alerts, coverage and timing denominators |
| Suppression tuning | No new suppressions introduced | Validate any future suppression against malicious and benign held-out traces |
| Upstream catalog expansion | Deferred scope, not a broken dependency | Review specific rule license/provenance, semantics and paired test cases before import |

The current two rules identify suspicious command text and can also match
authorized maintenance. No test can establish “perfect” malware prediction.
Do not close these empirical gates or claim production/publication readiness
from the Docker and regression results alone.
