# Phase 7 — Evaluation foundation

Started 2026-10-23. Phase numbering follows `docs/phase0/PLAN.md` I11, which is
the contract used by the recent implementation phases. The older master plan
uses a different numbering scheme. Phase 6 live-lab gates remain open.

## Implemented

`tools/phase7_evaluate.py` consumes independently labeled and adjudicated JSON
run records. It does not execute malware, derive truth from detector alerts,
or run external baseline tools. It validates measured counts, provenance
identifiers, split membership and identical input across variants; then computes
scenario recall, adjudicated-alert precision, alert burden per benign endpoint
day, collection recall, attribution completeness and detected-only latency
median/p95. Failed emulations are excluded and counted. Undefined denominators
produce null, not zero. Unadjudicated alerts are counted explicitly.

Run input and output paths must be supplied. Output creation is exclusive to
preserve previous reports. The output contains the input SHA256, protocol hash
and variant fingerprints. `synthetic_test` remains explicitly marked throughout.
No dataset or empirical result is bundled as real evidence.

Validation on 2026-10-23: all 14 evaluator regression tests passed (7.53 seconds
on the final run), Ruff passed, and CLI help was verified. Fixtures are explicitly
synthetic. The existing application code was not changed by this phase.

```powershell
.\.venv\Scripts\python.exe tools/phase7_evaluate.py path/to/adjudicated-runs.json --output path/to/new-report.json
```

## Freeze the protocol before collecting held-out data

1. Assign a protocol ID and SHA256 of the reviewed protocol file. Record the
   label unit as scenario and specify alert matching policy in advance: host,
   process/evidence relationship, scenario start/end and permitted delay.
   Count only independently adjudicated matches as true alerts. Determine
   operation success independently of the detector.
2. Assign leakage groups before tuning. Group related scenario variants,
   repeated traces and relevant host/time/family dependencies together. The
   evaluator rejects a group or exact trace hash appearing in both tuning and
   held-out data. It cannot discover undeclared semantic duplicates.
3. Freeze code, rule and configuration artifacts per variant. Hash actual
   artifacts; do not insert placeholder hashes into experiment records.
4. Record collector version/configuration and preserve immutable raw traces.
   Variants must process identical collected inputs for detector comparisons.
   Evaluate collector improvements separately.
5. Record nonoverlapping benign endpoint-hours. Count expected events using
   independent instrumentation; observed counts are matched unique expected
   events, not the total volume of arbitrary telemetry. Attribution is the
   correctly attributed subset of those observed events.
6. For detection delay, use scenario reference time and the first adjudicated
   alert with an explicit clock-alignment policy. Offline replay latency must
   not be represented as live endpoint-to-alert latency.

## Input contract

Top level:

- `schema_version`: 1; `evidence_kind`: `live_lab` or `synthetic_test`.
- `protocol_id`, `protocol_sha256`, `matching_policy`.
- `variants`: mapping from name to description, `code_sha256`, `rules_sha256`,
  `configuration_sha256`, and explicit `feature_switches` mapping.
- `runs`: list of records. Empty runs produces `not_run` with no metrics.

Each record requires:

- Identity: `run_id`, `variant`, `scenario_id`, `host_id`, `leakage_group`,
  `trace_sha256`, `split` (`tuning` or `held_out`). Repeated experiments need
  distinct run IDs; variants of the same experiment share a run ID.
- Truth: `label` (`benign` or `malicious`), `ground_truth_method`, `reviewer`,
  Boolean `execution_succeeded`, and `invalidity_reason` for unsuccessful runs.
- Collection: `collector_version`, `collector_configuration_sha256`, integer
  `expected_events`, `observed_events`, `attributed_events`.
- Results: Boolean `detected`, integer `alert_count`, `true_alerts`,
  `false_alerts`, `unadjudicated_alerts`. Detection means at least one adjudicated
  true attack alert, not simply any alert in a scenario window.
- Exposure: `benign_endpoint_hours` (zero for attacks), `latency_seconds`
  (null for undetected runs). Successful benign scenarios need positive exposure.

All hashes are lowercase SHA256. Counts are finite nonnegative integers and
must reconcile. Precision excludes unadjudicated alerts: publish that count
beside precision, and resolve it before making final performance claims.
The report marks whether all variants have the same valid run IDs per split.
Incomplete comparisons are not evidence of superiority.

## Baseline and ablation registration — execution still pending

| Variant | Purpose | Required artifact |
|---|---|---|
| A: frozen Phase 0 | Original implementation | Existing baseline archive, isolated environment/config |
| B: rules only | Rule baseline on matched telemetry | Exact engine and curated catalog |
| C: full current system | Candidate behavior detector | Frozen source/config and all enabled features |
| C without identity | Test attribution contribution | Implemented, tested experimental replay switch |
| C without event time | Test time-window contribution | Implemented, tested experimental replay switch |
| C without corroboration | Test independent-signal contribution | Implemented, tested experimental replay switch |
| External baseline | Sigma/Wazuh/Fibratus comparison | Actual pinned engine, configuration and matched inputs |

The evaluator accepts explicit variant records but does not implement these
ablation switches or external adapters. Do not label runs as ablations unless
the corresponding code paths exist and have been verified. Do not alter live
production correlation semantics merely to perform an experiment.

## Remaining work before Phase 7 is complete

- Run the deferred Phase 6 guest collector and broader benign/attack calibration.
- Build isolated replay adapters for the frozen/current systems and validate
  proposed feature ablations; register one fair external baseline first.
- Independently review labels and artifacts; freeze tuning/held-out groups.
- Run repeated experiments and adjudicate alerts. Collect CPU, memory, disk and
  network budgets separately; these are not implemented by this evaluator.
- Add grouped uncertainty estimates and paired comparisons after choosing the
  sampling unit and collecting enough independent runs. Current point estimates
  are not statistical significance tests.
- Audit calibration, failure cases and source hashes before publication claims.

This phase starts the evaluation infrastructure. It establishes neither
malware accuracy, research novelty nor production readiness.
