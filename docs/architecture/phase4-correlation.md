# Phase 4: source-time and process-instance correlation

Implementation date: 23 October 2026. This phase changes the active file/network ingestion path and process graph. It does not supply live malware accuracy measurements or persistent correlation recovery.

## Identity and timestamps

`core/temporal.py` keys windows by host, actor instance and event family. A supplied process GUID takes precedence; otherwise a positive PID and finite positive process creation time are required. Executable names alone never establish identity. These are authenticated endpoint assertions, not cryptographic proof of a process's identity. Mixed GUID and PID/time representations are not automatically merged.

Network polling now includes observed process creation time where available. A process newer than the socket snapshot remains unattributed; this reduces but cannot eliminate races in polling-based attribution. Sysmon GUIDs provide the preferred source. Directory watchers still cannot identify writers.

Source time is preserved in `time`. Inbox `received` supplies server acceptance time, and each correlation assessment records `processed_at`. Incoming non-process time values must be finite nonnegative numbers; malformed values are rejected. Missing source time, missing actor and implausible future time are visible assessment states rather than silently substituted with arrival time.

## Window policy

- File width: `rules/file_behavior.json` (currently 120 seconds).
- Network width: 300 seconds.
- Maximum out-of-order lateness: 120 seconds behind the greatest observed source timestamp for that host/actor/family.
- Future skew tolerance: 300 seconds relative to original server receipt.
- Older offline batches are accepted if chronological within their own stream; elapsed transport delay alone does not discard them.
- Scoring uses the window ending at the greatest observed source timestamp. Records at the lower window boundary are excluded.
- Events beyond allowed lateness remain in durable telemetry with a `too_late` assessment but do not modify the window or emit a temporal alert.
- At most 2,000 buffered records per key and 4,000 active keys. Per-key capacity exhaustion is reported. Least-recently-used key eviction loses context and is not a persistence mechanism; capacity/loss instrumentation remains further work.

This is incremental reevaluation, not finalized event-time windows with delayed emission. Within a retained window the final evidence/score is order-independent for the tested permutations. Intermediate alert counts, trigger event IDs and timing can differ with arrival order. No claim of universal replay equivalence or alert retraction is made.

## Detection changes

The new active file/network branches in `ingestion.py` use source-time assessments, not legacy process-name tracking. Existing direct helper functions remain for compatibility; this change does not convert DLL, sequence, user-behavior or every inherited detector to the new temporal model.

File scoring retains distinct-path and corroborated-note logic. Unattributed records are stored with `unattributed` status and do not create a guessed process alert. This intentionally reduces directory-watcher detection coverage until reliable writer evidence is available.

Beacon evidence requires at least five distinct source timestamps for the same destination IP/port, average intervals of at least one and less than 60 seconds, and low interval variance. Simultaneous batch arrival cannot itself become a periodic beacon. Administrative-port evidence requires three distinct internal destination hosts. IP classification is derived server-side; private/reserved-address classification still depends on Python's address library and is not an enterprise network policy.

Scores are capped at 100 and remain heuristic priorities, not malware probabilities. Legitimate periodic clients and administration can still trigger these indicators.

## Graph reconciliation

Graph nodes prefer GUID identity and otherwise use PID/creation time. An event-specific node is used if no instance identity exists. Each node retains its requested parent identity. Adding a later parent reconciles waiting children without inventing a parent by name or PID alone. Self-links and edges that create cycles are refused. Graph retention remains bounded; evicted or unavailable ancestors remain unresolved. Cross-source identity aliasing is not implemented.

## Evidence and retry behavior

Assessments retain actor key, event/receive/process times, lateness allowance, greatest source time and contributing event IDs where evaluated. Authenticated `GET /api/telemetry/<event_id>?system_id=<host>` exposes source records and assessments even when no alert was emitted. Alert detail exposes a generic `assessment` field while retaining the existing compatibility field.

Retries reevaluate buffered evidence without counting a source event twice. Alert persistence still deduplicates the trigger event. This handles an immediate retry after a persistence failure, but it is not atomic exactly-once detection across restart, eviction or later stream advancement. Durable graph/window reconstruction and replay semantics remain Phase 5.

## Verification

Local results: the full suite passed **106 tests in 88.61 seconds**. After adding the final retry, host-isolation and authentication checks, all **11 focused temporal tests passed in 9.41 seconds**. Ruff passed for backend, endpoint, launcher and tests. These are isolated synthetic regressions, not measured live detection effectiveness.

Tests cover delayed offline batches, bounded reordering, same-name/PID reuse, cross-host isolation, unknown writers, skew/missing time/late records, identical-timestamp network observations, periodic same-destination traffic, late GUID parents, persisted assessment metadata, retry deduplication, and unauthenticated evidence denial. The old test that mocked legacy scoring for an unknown writer was replaced with real attributed-file ingestion evidence.

Live Windows/Sysmon validation remains unavailable from the previous phase. The Docker image must be rebuilt to deploy these source changes. No production data migration is required: assessments use the existing telemetry JSON column and receipt timestamp; graph and window changes are in memory.
