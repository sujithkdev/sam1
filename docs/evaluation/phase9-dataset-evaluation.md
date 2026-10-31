# Phase 9 — Dataset integrity and comparative evaluation

Started 2026-10-23. This implements the dataset groundwork and one executable
rule-only replay adapter for the master plan's Phase 9. It extends Phase 7's
metric evaluator. Actual labeled Windows datasets and comparative experiments
remain pending; this document does not mark the research gate complete.

## Implemented tool

`tools/phase9_dataset.py` provides three commands:

```powershell
.\.venv\Scripts\python.exe tools/phase9_dataset.py freeze registry.json --root C:\BehEDRLab\dataset --output frozen-manifest.json
.\.venv\Scripts\python.exe tools/phase9_dataset.py verify frozen-manifest.json --root C:\BehEDRLab\dataset
.\.venv\Scripts\python.exe tools/phase9_dataset.py replay-sigma frozen-manifest.json --root C:\BehEDRLab\dataset --output sigma-findings.json
```

Use actual paths and new output filenames. The tool never overwrites output
artifacts, runs telemetry command lines, imports remote code, or contacts an
endpoint. It reads local evidence and evaluates literal rule predicates.

Freeze records SHA256 values for the protocol, raw traces, ground-truth artifacts
and collector configurations, plus formatting/order-independent trace hashes.
It rejects file paths outside the dataset root (including resolved links), missing
metadata, empty traces, oversized traces/events, duplicate scenario/event IDs,
mixed hosts and declared split leakage. Groups, canonical traces and overlapping
event identities cannot cross tuning/held-out splits. The raw trace hash still
preserves original event ordering for replay provenance.

Verify reconstructs the manifest and rejects changed artifacts. Hashes are
integrity evidence, not proof of trustworthy labels or authenticity. Store the
frozen manifest separately with controlled access; anyone able to replace both
the data and manifest can forge consistent hashes. The tool does not discover
all semantic duplicates or validate the quality of an investigator's labels.

## Dataset registry

Top-level required fields:

| Field | Meaning |
|---|---|
| schema_version | Integer 1 |
| evidence_kind | `live_lab` or `synthetic_test`; never mix the two |
| dataset_id | Stable study identifier |
| protocol | Relative path to reviewed protocol |
| label_method | How independent truth was established |
| reviewer | Responsible reviewer identifier |
| matching_policy | Predetermined alert-to-scenario matching policy |
| scenarios | Nonempty list of scenario records |

Each scenario requires `scenario_id`, `leakage_group`, `host_id`,
`collector_version`, `ground_truth_method`, `split` (`tuning` or `held_out`),
`label` (`benign` or `malicious`), Boolean `execution_succeeded`, and relative
paths `trace`, `ground_truth_artifact`, `collector_configuration`.
Failed executions also require `invalidity_reason` and are excluded from replay.

Trace format is UTF-8 JSONL, one normalized event object per line. Every event
requires string `event`, `system_id` and `event_id`. Sigma mappings consume
`exe_path`, `cmdline`, and optional `parent_exe_path`, all strings. Limits are
64 MiB per trace and 64 KiB per event. Preserve raw Windows evidence separately
and record conversion details in the protocol. Avoid merging unrelated hosts or
scenarios into the same trace; establish scenario boundaries independently.

Group related scenarios, families, hosts and collection periods before tuning.
Explicitly document the grouping decision: the validator cannot infer it.

## Executable baseline and its limits

`replay-sigma` uses the existing **BehEDR strict Sigma subset** with the two
reviewed local rules. It is not SigmaHQ's complete engine, Sysmon+Sigma with an
external backend, Wazuh, or Fibratus. Only normalized `process_spawn` events are
supported. Other types are counted as unsupported rather than silently treated
as coverage. Missing mapped fields cannot match. The source adapter hash and
exact rule hashes are recorded with every replay report.

Findings contain event identity and rule provenance. They are not automatically
true positives: authorized administration can match a rule. Independently
adjudicate findings, supply measured exposure/latency and matched event counts,
then build the run records documented in [Phase 7](phase7-evaluation.md).
The tool intentionally does not invent a metric denominator or convert replay
runtime into online detection delay.

## Validation

Initial focused suite: **10 tests passed in 7.51 seconds** on 2026-10-23.
Tests cover freeze/verify/replay, modified protocol/trace/truth/configuration,
path traversal, reserialized duplicate leakage, failed execution exclusion,
wrong-host and duplicate events, and unsupported telemetry visibility.
All fixtures are synthetic and do not constitute malware-detection results.

## Research completion gates still open

1. Collect the deferred Phase 6 Windows evidence and broader labeled benign and
   authorized attack traces. Use a disposable isolated VM, dummy credentials,
   controlled destinations, and verified snapshot recovery. Do not run real
   malware on the host. Review artifacts for private command-line data before
   sharing; the tool does not sanitize secrets or configure filesystem ACLs.
2. Independently review labels and freeze the protocol/splits before evaluating
   the held-out set. Record exact collector and detector configurations.
3. Implement isolated full-system and frozen-Phase-0 replay adapters. Implement
   and verify identity/time/corroboration ablation switches before labeling any
   experiment as such. The current adapter is only the rule baseline.
4. Integrate one actual pinned external baseline with comparable input and tuning
   budgets; do not report existing local rules as an external-tool comparison.
5. Run repeated paired experiments, adjudicate findings, and use Phase 7 metrics.
   Select a defensible independent sampling unit and add grouped uncertainty
   estimates; neither novelty nor statistical significance is established here.
6. Independently reproduce the experiment bundle before manuscript claims.

Phase 9 is started, not empirically complete. No accuracy numbers, superiority
claim, journal-readiness score or fabricated dataset is supplied.
