# Phase 5: graph and temporal-window recovery

Date: 23 October 2026.

## Design

Successful inbox analysis now writes a recovery journal entry and marks the telemetry row done in one SQLite transaction. Each entry contains host/event identity, source payload, original receipt time, rules/code fingerprint and an increasing completion sequence. Unique host/event identities prevent journal duplication on retries.

Startup initializes the inbox and detection rules, then restores the process graph and Phase 4 file/network windows before starting the analysis worker. Replay walks committed inputs in completion-sequence order, retaining the same bounded graph/window behavior as normal execution. It calls only graph construction and temporal assessment, never the general detector, alert emitter, command queue, or external notification code. Scores calculated during replay are discarded.

`/ready` returns 503 unless recovery has reached ready and backlog capacity is available. During synchronous application startup the HTTP listener is not yet open. A recovery exception prevents startup; it is not silently treated as empty state.

The journal is append-only in this version. No partial checkpoint format or unsafe deserialization is introduced. Replay streams database rows, but total startup time and journal disk usage grow with history. Checkpoint compaction, retention and large-fleet performance need further work.

## Version handling

The fingerprint covers the rules directory and graph, temporal and file-scoring source. Journal version changes are fail-closed. If fingerprints differ, startup stops with a recovery mismatch. Do not edit journal hashes or delete the journal merely to bypass this gate. Preserve backups and use a reviewed migration or an explicitly separate new dataset when changing replay semantics. An automated version-migration CLI is not included.

Pre-Phase-5 completed telemetry has no recorded completion order or rules version. On first recovery it is journaled in inbox ID order with `origin=legacy_inferred`; the count is exposed in the internal recovery state. This provides best-effort context for old data but cannot reconstruct its historical processing semantics exactly. Pending and failed rows are not promoted to completed by replay.

## Crash and retry boundaries

- Crash before journal/done commit: the input remains pending and normal ingestion retries it.
- Crash after journal/done commit: startup reconstructs its supported graph/window contribution without re-emitting its alerts.
- Alert writes can precede journal commit. Existing source-event alert deduplication protects identical persisted findings on retry, but this is not a single atomic transaction spanning all detector side effects.
- Failed attempts can have modified memory before failing. Replay includes committed completions only; it deliberately does not promise reconstruction of those incomplete mutations.
- UUID command reservations remain governed by Phase 1. Recovery does not execute or recreate commands.

Only process graphs and Phase 4 temporal file/network state are recovered. DLL history, inherited sequence/frequency models, UBA, development advisory context and other legacy caches are not covered. This is not a claim of whole-engine exactly-once processing or complete EDR recovery.

## Operations

Back up with the existing SQLite backup command; the journal is inside the same database. Restore into a fresh stopped data directory using matching code/rules, then verify readiness and counts before reconnecting agents. Restore-time credential/session and command reconciliation from Phase 1 still applies. The startup lock in manage.py remains required; do not scale server replicas against one data directory.

Malformed journal data and version mismatch cause visible startup failure. Preserve the database for diagnosis rather than dropping malformed entries automatically. Recovery is intended for trusted server-owned data, not importing arbitrary user-supplied journals.

## Verification

The full suite passed **115 tests in 39.62 seconds** before the final separate-process restore test was added. All **7 focused recovery tests then passed in 16.95 seconds**, including backup restoration and application startup in a fresh Python process. Ruff passed. Recovery regressions check replay without alert/command side effects, repeated replay, continuation of a partial window, late-parent graph equality, exclusion of pending inputs, rule mismatch/readiness failure, legacy provenance and corrupted data failure.

No live VM, Docker image rebuild, power-loss experiment or sustained-load recovery run was performed in this phase. Existing deployment images must be rebuilt to include these changes.
