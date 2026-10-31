# BehEDR current status and completion roadmap

Navigation: [documentation index](README.md) · [current P0–P9 roadmap](development/ROADMAP.md)
· [publication workspace](publication/README.md). Documentation reorganized on
30 October; historical baseline identities and test results remain preserved.

30 October follow-up: P0 publication scope is deferred at the user's request.
P1 guest checks will be run by the user; see the
[live transport checkpoint](development/P1_LIVE_TRANSPORT_2026-10-30.md).
The attempted new P1 distribution failed due to an OS security block on
reading endpoint/yara_scanner.py. Its incomplete output was removed during the
[30 October cleanup](evidence/CLEANUP_2026-10-30.md). Live qualification remains open.

P2 Windows telemetry qualification has been added as a
[guest checklist and evidence matrix](development/P2_WINDOWS_TELEMETRY_2026-10-30.md).
It is prepared, not live-verified; P1 delivery remains a prerequisite for
end-to-end collection measurements.

Updated 2026-10-25. Latest local verification: [results](evidence/verification-2026-10-25.md)
and [guest verification protocol](operations/verification-workflow.md). Live guest delivery
remains unverified; native HTTPS deployment prototypes remain unqualified.
This is the authoritative current status entry point. Older
plans and phase reports are historical evidence, not cumulative completion claims.

## Source of truth

Edit backend/server/, endpoint/, rules/, tests/, tools/, requirements/ and deploy/
in the project root. manage.py is the server launcher. docs/ contains evidence.
The root is not currently a Git repository; do not invent a root commit identity.

dist/ contains generated distributions, not independently maintained source.
dist/github-upload-behdr is the publication checkout for the earlier public
sujithkdev/behdr package release, not the source of truth for current development.
archive/ preserves legacy implementations. gthb/ contains third-party reference
code and must not be deployed or copied without provenance/license review.
var/ contains private runtime/test evidence and is excluded from distributions.
Do not upload the project directory wholesale.

## Version and deployment register

| Component | Identity | Deployment evidence |
|---|---|---|
| Authoritative source | R0 source SHA256 inventory in r0/inventory.json | Local development only |
| Agent reported version | 4.1.0-rc1, literal in endpoint/agent.py | Version string alone does not identify source bytes |
| Server | No existing canonical runtime semantic version | Use package manifest/source digest; do not assume agent version applies |
| Updated dashboard distribution | dist/behedr-dashboard-2026-10-24 | Built and tested locally; Kali installation unconfirmed |
| R0 verification distribution | dist/behedr-r0-2026-10-24 | Fresh server dependency installation and package smoke check passed on Windows host |
| Earlier public package | packages-2026-10-24 release in sujithkdev/behdr | Publication confirmed earlier; not re-fetched during R0 |
| Windows 11 host | User-reported platform | Not a supported malware-execution test target |
| Windows 10 VMware endpoint | User-reported guest | Installed source hashes, build and Sysmon version not yet collected |
| Kali VMware server | User-reported guest | OS build, installed source hashes and dependency inventory unknown |

Current operational incident: heartbeat and telemetry HTTP read timeouts to
Windows localhost:5000 were reported. Collection failure is not established by
that traceback. SSH forwarding, VM connectivity and server responsiveness must
be distinguished in R1. No remote repair or new malware experiment occurred in R0.

## Feature register

“Implemented” means source exists. “Conditional” means configuration/dependencies
are required. Historical tests are not proof that the user's deployed copy works.

| Feature | Implementation / configuration | Evidence | Deployment / remaining gap |
|---|---|---|---|
| Process polling | endpoint/agent.py | tests/test_endpoint.py | Live coverage unknown; brief processes may be missed |
| Sysmon collection and bookmarks | endpoint/sysmon_collector.py; EDR_SYSMON / EDR_PROCESS_SOURCE; deploy/sysmon-lab.xml | tests/test_sysmon.py; docs/phase3-sysmon.md | Conditional; live version/configuration and loss measurements missing |
| Windows event logs / optional ETW | endpoint/eventlog.py; endpoint/etw_consumer.py | Source inspection; deployment prerequisites | Conditional; channel permissions and complete live coverage unverified |
| File/network/DLL observations | endpoint/agent.py | Component regressions | Source-dependent attribution and monitored scope; not full packet capture |
| Durable outbox/inbox and dedup | endpoint/spool.py; backend/server/ingestion.py | Endpoint, ingestion and recovery regressions | Live timeout open; finite queue capacity |
| Identity / event-time correlation | core/graph.py; core/temporal.py under backend/server | Phase 4 and 5 reports/tests | Effectiveness unmeasured; bounded graph and missing identity limitations |
| Behavioral rules / heuristics | core/detector.py; core/sequence_heuristics.py; rules/ | Detection regressions | Not calibrated malware probability or validated accuracy |
| Sigma subset | core/sigma_subset.py; backend/server/sigma_rules/ | tests/test_sigma_subset.py; phase6-rules.md | Two local rules; not full Sigma compatibility |
| Development ancestry context | core/development_guard.py; rules/development_policy.json | tests/test_development_guard.py | Observe-only; not AI authorship proof or OS enforcement |
| Hash/IOC intelligence | core/hash_db.py; threatintel.py | Phase 1 health tests | Data/corpus/update effectiveness not demonstrated |
| YARA | core/yara_engine.py; endpoint support; rules/yara/ | Optional implementation | No validated reviewed corpus/remote file scanning claim |
| Authentication / authorization | auth.py; routes/api.py | Security regressions | Requires private secrets/TLS or controlled loopback SSH lab |
| Manual constrained response | commands.py; endpoint/response.py | Endpoint identity/command regressions | Admin kill API; UI exposes read-only information requests; live qualification pending |
| Investigation console | routes/console.py; templates/dashboard.html; static/dashboard.* | tests/test_console.py; tests/test_dashboard_session.cjs; dashboard-redesign.md | Local implementation verified; Kali deployment unconfirmed |
| Backup / retention / recovery | retention.py; core/recovery.py; manage.py | phase8-verification-2026-10-23.md | Offline maintenance constraints; fleet/long-duration limits unqualified |
| Metrics / dataset integrity | tools/phase7_evaluate.py; tools/phase9_dataset.py | Evaluation regressions with synthetic fixtures | Real labelled dataset, full replay, external baseline and ablations incomplete |
| ML / automatic containment / network isolation / notifications / legacy Wazuh bridge | Unsupported release capabilities | Existing phase reports and capability flags | Do not advertise as active or validated |

## Evidence hierarchy

1. Actual deployment measurements tied to source/configuration identity.
2. Reproducible isolated experiments with independent ground truth.
3. Regression and package tests (software behavior only).
4. Source implementation.
5. Proposal or historical documentation.

The dashboard update recorded 186 passing Python tests plus JavaScript session
checks. Phase 8 recorded bounded Docker and failure/load checks. Neither result
establishes malware accuracy, production readiness or IEEE acceptance. R0-specific
validation and remaining gates are in r0/VERIFICATION.md.

## Remaining phases and exit gates

| Phase | Deliverable | Completion evidence |
|---|---|---|
| R0 | Current register, source/package identity, preserved baseline, installation check | Inventory integrity and explicit verification limits |
| R1 | Reliable live transport and diagnostics | Normal/disconnected/reconnected/restarted delivery reconciled |
| R2 | Qualified Windows telemetry | Independently measured capture/attribution and visible loss |
| R3 | Specified correlation method and closest-work review | Algorithm, assumptions, novelty go/no-go decision |
| R4 | Labelled dataset and frozen protocol | Independent labels, leakage controls, execution verification |
| R5 | Calibrated supported detections | Positive/negative/missing-data cases; frozen thresholds |
| R6 | Full replay, ablations and external baseline | Verified feature switches, pinned fair comparison |
| R7 | Empirical evaluation | Recall, precision, benign alert burden, delay, cost, uncertainty |
| R8 | Qualified release and bounded pilot | Security/usability/upgrade/restore/sustained-workload evidence |
| R9 | Manuscript and reproduction bundle | Independent reproduction, claim audit and venue compliance |

Each phase records problem, change, tests, evidence and remaining limits. A 9/10
assessment is earned within a stated scope, not assigned automatically at phase
completion. Detection accuracy stays unmeasured until R7 supplies valid results.

## Deferred scope

No new ML model, kernel driver, automated sandbox, automatic destructive response,
public exposure or distributed database is required for R0. Docker remains
optional; the user's first deployment path is non-Docker Windows + Kali.

## Immediate handoff to R1

Collect installed package hashes and Python/dependency versions inside both guests;
verify Kali /health and /ready locally and Windows /health through the tunnel;
record queue depth/age and acknowledgment progression. Preserve spool and server
state. Do not fix a timeout by deleting evidence, re-enrolling agents or merely
raising the timeout. Establish a failing reproduction before changing behavior.

Dependency reproducibility gap: requirements/server.lock is pinned, but endpoint.txt uses pywin32>=311 and leaves transitive dependency resolution open. The R0 resolved agent environment is evidence for this run, not a fully pinned future Windows installation. Resolve deliberately in R2/R6.
