# BehEDR: A Behavioral Endpoint Detection Prototype with Process-Aware Temporal Correlation

Working title only. Manuscript status: outline, not submission-ready.
Venue and permitted changes to the previously submitted paper are unresolved;
P0 is deferred. No empirical numbers are supplied by this template.

## Abstract

To write after evaluation: problem, specific contribution, evaluated scope,
baseline, measured outcomes with uncertainty and principal limitation.

## 1. Introduction

Research question: does process-aware temporal correlation improve detection of
evaluated malicious behaviors over the same rules alone, particularly under
delayed or incomplete telemetry, without excessive benign alerts?

Pending: establish the specific contribution against closest related work.
Separate delivery reliability from intrinsic detector improvement.

## 2. Related work

Pending: version-specific comparison of telemetry, identity, temporal method,
evaluation and reproducibility. Verify primary references and citation metadata.
Do not infer novelty from feature count or integration alone.

## 3. Threat model and assumptions

Specify Windows guest, privileges, sources, loss/retention, timing, attacker
capabilities and operator trust. Exclude unsupported prevention, family
identification, kernel protection and enterprise-scale claims.

## 4. Design and method

Describe event/process identity, ancestry, rules, temporal semantics, missing
evidence, bounded state and scoring. Severity is not calibrated probability.
Define assumptions and algorithms against the frozen implementation.

## 5. Implementation

Record code/rule/configuration digests, dependencies and effective collectors.
Describe durable delivery, acceptance acknowledgment, analysis, recovery and
console separately. Link each capability to its implementation and qualification.

## 6. Evaluation protocol

Specify independent labels, scenario eligibility, benign exposure, tuning and
held-out splits, baseline versions, actual ablation switches, repetitions,
exclusions, alert matching, clock uncertainty and hardware/VM configuration.
Freeze before held-out runs. Use the evaluation tooling's actual supported contract.

## 7. Results

Pending experiments. Planned tables: collection coverage; delivery/recovery;
recall/precision; false alerts per benign endpoint-hour/day; correct/incorrect/
unresolved attribution; latency distributions; resource cost; ablation comparison.
All tables need run IDs, denominators, exclusions and evidence locations.

## 8. Discussion and limitations

Report failure cases, scope, missing telemetry, lab realism, sample diversity,
label uncertainty, dependency reproducibility and operational limits. Distinguish
emulated behavior from real malware and behavior detection from family attribution.

## 9. Reproducibility

Follow [the artifact specification](REPRODUCIBILITY.md). Artifact creation,
sanitization, licensing and independent reproduction remain pending.

## 10. Conclusion

Write only after results: answer the bounded question with measured evidence.

## References and figures

Maintain a verified bibliography when the venue is selected. Planned figures:
source-traced architecture, identity/time example and experimental flow. Venue
formatting, author information and final export are deferred until constraints
are known. This outline is not an official IEEE template.
