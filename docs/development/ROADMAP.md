# Current development roadmap — P0–P9

Updated 30 October 2026. This roadmap implements the
[publication plan](../publication/IEEE_PUBLICATION_AND_MALWARE_EVALUATION_PLAN.md).
Historical Phase 0–9 implementation reports and the R0–R9 status register use
different numbering; their test results do not automatically close these gates.

| Phase | Deliverable | Current state | Exit evidence |
|---|---|---|---|
| P0 | Scope, venue and manuscript claims | Deferred by user | Venue/revision constraints and bounded claims established |
| P1 | Frozen source and reliable live transport | Local tests recorded; guest results pending | Installed hashes, route fairness, ACK/retry/restart counts reconciled |
| P2 | Qualified Windows telemetry | Checklist prepared; live execution pending | Independent launch/source/server matches, loss and identity limits |
| P3 | Detector contracts | Existing implementation; qualification pending | Positive, benign, incomplete, late and skewed cases with specified outcomes |
| P4 | Live investigation console | Local implementation; guest qualification pending | Roles, evidence views, stale state and session behavior verified live |
| P5 | Deployment and security | Existing tools; selected installation unqualified | Repeatable startup, secrets, restore, upgrade and resource-pressure evidence |
| P6 | Frozen experiment protocol | Evaluation tooling exists; dataset/protocol pending | Independent labels, tuning/held-out splits and leakage checks frozen |
| P7 | Comparative evaluation | Pending | Rules-only/full/ablations/external baseline with reproducible metrics |
| P8 | Revised manuscript | Outline and correction plan prepared | Claims and figures trace to frozen results; venue-compliant revision |
| P9 | Reproduction and independent review | Pending | Sanitized artifact bundle, clean rerun and reviewed limitations |

## Active work

- [P1 live transport](P1_LIVE_TRANSPORT_2026-10-30.md): waiting for user-run VM outputs.
- [P2 telemetry](P2_WINDOWS_TELEMETRY_2026-10-30.md): read-only inventory may begin;
  end-to-end measurements depend on verified delivery.
- No fresh distribution is qualified; the failed P1 output was removed.

## Phase closeout record

Each phase report must identify the problem, exact source/configuration,
changes, commands/checks, evidence paths, result, remaining limits and next step.
Use one of: proposed, implemented, locally tested, live qualified, experimentally
supported. Do not replace a missing measurement with a subjective readiness score.
