# Phase 0 baseline and research contract

Date: 2026-10-22. Scope: Windows behavior-based threat monitoring, one central server, constrained manual response. This phase changes documentation and reproducibility tooling, not application behavior.

## Research question

Does process-instance-aware, event-time behavioral correlation reduce false alerts while preserving scenario-level recall under delayed and out-of-order Windows telemetry?

Hypotheses, not findings: instance identity reduces unrelated-process aggregation; event-time windows reduce delivery-induced false alerts; corroborated file evidence reduces benign alert burden. Improvements must be measured against the frozen baseline.

## Baseline

No Git repository exists in this checkout. A SHA-256 manifest and source ZIP provide the baseline identity; do not describe it as a Git commit. `baseline-manifest.json` identifies each included file and the archive. `environment.json` records the interpreter and installed package versions without environment variables or secrets.

Included: active backend source/assets, endpoint source, rules, dependency declarations/locks, tests, deployment templates, CI, launcher and project documentation. Excluded: .env, credentials, runtime databases/logs, .venv, caches, downloaded third-party projects, original archives, and earlier nested baseline archives. The legacy hash database is deliberately excluded; any experiment requiring intel must separately identify and provision its dataset. The source snapshot is not a runtime backup.

Run `tools/freeze_phase0.py` with the project Python to create the artifacts once. It refuses to overwrite an existing freeze. Run it with `--verify` to compare included source files and archive members against the manifest; verify reports later source drift instead of replacing the baseline. Phase 0 output files are excluded from the snapshot to avoid recursion.

## Requirements and acceptance criteria

| ID | Requirement | Verification |
|---|---|---|
| R01 | Sessions belong to immutable user identities | Old token rejected after username recreation |
| R02 | Commands remain distinct across restores | Restore and endpoint-reservation regression |
| R03 | Preserve trustworthy source identities and timestamps | Schema and missing-field tests; retain unknown attribution |
| R04 | Observe declared Windows event sources | VM coverage matrix with independent ground truth |
| R05 | Correlate with bounded event-time lateness | Ordered/delayed/reordered replay equivalence within declared policy |
| R06 | Recover graphs and windows without duplicate effects | Crash/restart/restore comparison |
| R07 | Explain each finding using source evidence and rule version | Alert-to-event traceability tests |
| R08 | Distinguish absent telemetry from quiet endpoints | Source health, queue age, loss and permission metrics |
| R09 | Evaluate effectiveness on held-out workloads | Defined labels, splits, baseline and ablation reports |
| R10 | Declare supported deployment capacity | Resource, backlog and recovery measurements |
| R11 | Keep response operator-controlled | Authorization, expiry, identity and replay tests |
| R12 | Reproduce code, configuration and experiments | Checksummed source, dependencies and scenario manifests |

## Feature register

| Feature | Status | Evidence / qualification |
|---|---|---|
| Process/network polling and Windows file notifications | Active code | endpoint/agent.py; live coverage not established by unit tests |
| Windows log / optional SilkETW collection | Conditional | endpoint/eventlog.py, etw_consumer.py; permissions/configuration required |
| Durable outbox and inbox | Active, regression-tested paths | endpoint/spool.py, backend/server/ingestion.py; not universal exactly-once semantics |
| Rule, parent-child, sequence and graph detection | Active | core/detector.py, graph.py, sequence_ml.py; accuracy unmeasured |
| Externalized file scorer | Active, regression-tested | core/file_behavior.py, rules/file_behavior.json |
| Development ancestry advisory | Active | development_guard.py; not OS permission enforcement |
| Authentication and constrained commands | Active with known gaps | auth.py, commands.py, endpoint/response.py |
| Hash/IOC support | Partial | Data path/update/health work required; no coverage claim |
| YARA | Optional | Reviewed corpus and scanner deployment not established |
| Neural models and experimental anomaly ML | Disabled | Startup rejects experimental flag |
| Automatic containment, isolation, notifications, old Wazuh bridge | Unsupported active release features | Do not advertise as working |
| Graph reconstruction helper | Partial | Exists in graph.py; startup/replay/order correctness incomplete |
| Docker/Caddy and CI | Templates present | Target execution still requires validation |
| Sysmon adapter and Sigma integration | Planned | Not implemented by Phase 0 |

## Prioritized issue register

Each item requires a failing reproduction before a fix and retained regression afterward. Earlier audit findings are hypotheses to reproduce unless the current source directly establishes the behavior.

| ID | Priority / phase | Change and acceptance test |
|---|---|---|
| I01 | P0 / 1 | auth.py username/version reuse: immutable identity; old session stays invalid after recreation |
| I02 | P0 / 1 | Restore-safe command identity: new commands never collide with retained endpoint reservations |
| I03 | P1 / 1 | Intel failures/path: missing DB, empty data and failed refresh visible; writable configured data location |
| I04 | P1 / 1 | Alert dedup: separate process instances remain visible; retry duplicates do not multiply |
| I05 | P1 / 2 | Validate Docker/service deployment, secrets, persistent storage, TLS and rollback |
| I06 | P1 / 3 | Event-based collection and durable bookmarks; measure short-lived events, rollover and gaps |
| I07 | P1 / 4 | Source-time windows, skew and lateness policy; delayed normal traffic does not become an artificial burst |
| I08 | P1 / 4 | Process-instance grouping and unknown writers; unrelated actors cannot merge into attributed evidence |
| I09 | P1 / 4–5 | Late-parent reconciliation and restart recovery; replay agrees with uninterrupted supported behavior |
| I10 | P1 / 6 | Curated rule semantics, calibration and benign look-alikes; reject unsupported Sigma constructs |
| I11 | P1 / 7 | Ground truth, baselines and ablations; no accuracy claims based on unit tests |
| I12 | P2 / 8 | Queue exhaustion, storage retention and resource budgets; publish measured supported limits |
| I13 | P2 / 6 | Rename rule-only sequence module and archive unused experiments after import checks |

## Evaluation protocol

Preserve baseline A (current source). Compare B (rules-only on matched telemetry), C (improved full system), and C with identity, event-time and corroboration individually disabled. Record feature switches explicitly. Collector changes are a separate experimental factor: do not attribute their gains solely to the detector. External comparisons require named versions, configuration and equivalent workloads.

Use benign browsing, builds, installers, backups, extraction, package installation and development-tool descendants. Use selected authorized emulations only in an isolated VM lab. Test execution success independently from detector output. Failed emulation is invalid/inconclusive, not a false negative. Never derive labels from BehEDR's alerts.

Split tuning and held-out workloads by scenario/host/time as appropriate; prevent duplicate traces crossing splits. Freeze thresholds before held-out evaluation. Define label unit and alert-to-scenario matching window in advance. Report scenario recall, alert precision with adjudication, alerts per benign endpoint-day, latency median/p95, collection loss, attribution completeness, CPU/RAM/disk/network costs and repeated-run uncertainty. No initial accuracy or capacity target is asserted without a pilot; choose operational budgets before the final evaluation.

`experiment-template.json` is deliberately unexecuted. Copy it to a per-run record, supply actual versions, labels, expected observations, ground-truth artifacts and hashes. `results-template.csv` contains headers only. Do not populate example metrics as real measurements.

## Clean-environment reproduction

1. Verify baseline archive and extract into a new directory. Do not overlay a live deployment.
2. Install Python 3.12 and create a fresh virtual environment.
3. Install `requirements/dev.lock`; record installation output and resolved versions.
4. Run `python -m pip check`, then `python -m ruff check backend endpoint manage.py tests`.
5. Run `python -m pytest -q -p no:cacheprovider` with writable temporary directories.
6. Save command outputs and environment inventory with the run record.

The test fixture creates isolated temporary SQLite databases, sets test-only credentials and disables the background worker. Regression tests do not establish live Windows telemetry or real-malware effectiveness. Docker is planned for Phase 2 and is not a prerequisite for this baseline.

## Completion rules

The local baseline package is complete when source integrity verifies, tests/lint results are recorded, features/issues/requirements are mapped, and blank experiment artifacts exist. Independent clean-environment reproduction remains a separately reported gate until actually executed. Phase 1 must not be described as implemented merely because it is planned here.
