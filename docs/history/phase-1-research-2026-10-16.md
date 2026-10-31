# Phase 1 research assessment and publication plan

Research date: 16 October 2026. Project: behavior-based malware detection on Windows.

## Decision

Continue as a research prototype, with a narrower hypothesis and an empirical study. Do not claim a novel general malware detector, zero-day protection, production readiness, or a validated accuracy percentage. Keep AI-assisted development as one workload category, not a replacement research topic.

Recommended candidate question: **How can a Windows behavioral detector maintain attack recall and useful evidence while controlling false alerts under delayed/incomplete telemetry and legitimate high-volume activity?**

This question is not yet certified novel. Event-time handling, provenance, uncertainty and false-positive reduction all have prior art. A defensible contribution must be a specific method or new measurement finding demonstrated beyond existing implementations. Merely correcting this project's bugs is engineering work, not sufficient research novelty.

## Scope and evidence limits

This is a targeted scoping review, not an exhaustive review of all GitHub repositories or all IEEE publications. Search covered IEEE publisher pages, official journal guidelines, USENIX proceedings, author-hosted manuscripts, arXiv records and original repositories. Query families included behavior-based malware detection, provenance and temporal graphs, Windows ETW/Sysmon, false positives, out-of-order/incomplete telemetry, evaluation bias and coding-agent security. Foundational work from 2018 onward and recent 2024–2026 work were considered.

Included: host behavioral methods, relevant evaluation methodology, operational comparators and agent-workload studies. Excluded from core comparisons: unrelated network-only classifiers, static-PE-only classifiers, marketing accuracy claims, and repositories without an identifiable relevant implementation. These exclusions are scope choices, not claims those fields are unimportant.

Evidence depth: selected method/evaluation/threat-model sections of KAIROS and the 2025 comparative study were inspected; other paper entries below were screened through publisher/author abstracts or records. Repository inspection covered documentation and selected Fibratus parser code, not complete code audits or executions. Some IEEE full texts were inaccessible. No new detection experiments, malware runs or third-party installations were performed in this phase. Earlier local findings remain in evaluation-2026-10-16.md.

Full-text extraction, forward/backward citation screening, exact release pinning and execution-based comparator validation remain necessary before making a formal novelty claim. No absence-of-prior-work claim follows from an unsuccessful search.

## Tool and repository comparison

| Project/source | Overlap and appropriate use | Important boundary |
|---|---|---|
| [Fibratus](https://github.com/rabbitstack/fibratus) and [sequence parser](https://github.com/rabbitstack/fibratus/blob/master/pkg/filter/ql/parser.go) | Closest operational comparator: Windows behavioral sensor; parser includes sequence time spans and join fields. | Time-window correlation itself is already implemented. Test a pinned release rather than inferring behavior from README or master. |
| [WHIDS](https://github.com/0xrawsec/whids) | Windows/Sysmon detection engine with alert-driven artifact collection. | README warns it lags beta changes. A possible secondary comparator, not an assumed production-quality reference. |
| [Wazuh](https://github.com/wazuh/wazuh) | Agent/manager monitoring and rule-based security platform; broader operational baseline. | Document telemetry configuration, rules and enabled integrations; do not call it signature-only. |
| [Sigma](https://github.com/SigmaHQ/sigma) | Detection-rule repository for a transparent rules baseline. | Requires a specified engine/backend; not a standalone EDR. Pin rule versions. |
| [Chainsaw](https://github.com/WithSecureOpenSource/chainsaw) | Windows artifact hunting and Sigma-based offline comparison. | Offline timing is not comparable to online alert latency. |
| [CAPE](https://github.com/kevoreilly/CAPEv2) | Dynamic malware-analysis infrastructure. | A sandbox, not a direct continuous endpoint comparator; reports alone are not independent ground truth. |
| [KAIROS](https://github.com/ubc-provenance/kairos) | Research implementation for graph-based intrusion detection/investigation. | Original telemetry/schema and evaluation granularity differ from this project; an adapter needs validation. |
| [PIDSMaker](https://github.com/ubc-provenance/PIDSMaker) | Framework for consistent provenance-detector experiments. | Use the publication-associated version, not an assumed equivalent current branch. May exceed a small project's compute budget. |
| [Atomic Red Team](https://github.com/redcanaryco/atomic-red-team) | Candidate source of controlled behavior tests. | Technique emulation is not a malware population or proof of malware recall. Review each test before lab execution. |
| [OpTC data](https://github.com/FiveDirections/OpTC-data) | Candidate public telemetry source for reproducible external validation. | Older workload distribution and schema differ from current developer endpoints; verify usable fields, labels and redistribution conditions. |

## Related-work matrix

Numbers reported by different papers are not ranked here: different datasets, labels and detection units make a leaderboard misleading.

| Work and publication status | What already exists | Consequence for this project |
|---|---|---|
| [HOLMES, IEEE S&P 2019](https://ieeexplore.ieee.org/document/8835390/), DOI 10.1109/SP.2019.00026; publisher abstract screened | Correlates suspicious information flows to identify campaigns and produce explanatory graphs. | Correlation plus an attack graph is not new by itself. This is a conference paper, not a journal requirement. |
| [KAIROS, IEEE S&P 2024](https://spg.cs.ubc.ca/publication/2024-sp/), DOI 10.1109/SP54263.2024.00005; [manuscript sections inspected](https://www.vanbastelaer.com/publication/kairos/kairos.pdf) | Temporal graph learning, anomaly detection and attack reconstruction. Assumes trustworthy OS/audit infrastructure; evaluated with public provenance datasets. | Compare detection granularity and data assumptions. A partial process tree is not equivalent to whole-system provenance. |
| [Nip in the Bud, IEEE TDSC, issue 2025](https://ieeexplore.ieee.org/document/10638171/), DOI 10.1109/TDSC.2024.3444781; publisher abstract screened | CTI-assisted forecasting and interpretation of post-exploitation activity. | Forecasting future activity is a separate task. Do not describe current event detection as attack prediction. |
| [Graph-Based Anomaly APT Attack Detection via Threat Intelligence, IEEE TETC 2026](https://ieeexplore.ieee.org/abstract/document/11410032/figures), DOI 10.1109/TETC.2026.3665235; indexed publisher abstract screened, full text unavailable | Combines provenance, threat intelligence and graph learning to address anomalous events/false alarms. | Combining those components or saying fewer false positives is not sufficient differentiation. |
| [SIGL, USENIX Security 2021](https://www.usenix.org/conference/usenixsecurity21/presentation/han-xueyuan); abstract and selected paper text | Graph learning for malicious behavior during software installation. | Supply-chain/install-time behavioral detection predates coding-agent workflows. Include legitimate installers in evaluation. |
| [Sometimes Simpler is Better, USENIX Security 2025](https://www.usenix.org/conference/usenixsecurity25/presentation/bilot); [selected full-text sections](https://www.usenix.org/system/files/usenixsecurity25-bilot.pdf) | Common framework comparing eight provenance systems; examines practical weaknesses, ground-truth problems and detection granularity. | Include strong simple baselines and measure actionable alerts; avoid inflating labels to entire neighborhoods. Pin the manuscript version: landing-page and PDF summaries differ in dataset counts. |
| [TESSERACT, USENIX Security 2019](https://www.usenix.org/conference/usenixsecurity19/presentation/pendlebury); publisher abstract | Demonstrates temporal/distributional evaluation bias in Android malware classification. | Apply its evaluation lessons, but do not treat it as Windows detector evidence. Split by time/group and declare deployment prevalence. |
| [AgentDojo, author preprint record 2024](https://arxiv.org/abs/2406.13352); abstract | Tool-agent prompt-injection evaluation environment. | Agent security is an existing field; tool-task outcomes differ from endpoint malware labels. Publication venue was not verified in this review. |
| [MalSkillBench, arXiv 2026](https://arxiv.org/abs/2606.07131); abstract, peer-review status not verified | Runtime-verified malicious agent-skill benchmark spanning code and instructions. | Agent-skill datasets/monitoring are not automatically novel; verify actual execution and labels, not only generated scenarios. |
| [IssueTrojanBench, arXiv 2026](https://arxiv.org/abs/2607.20759); abstract, peer-review status not verified | Evaluates coding agents against malicious issue requests. | Include this in adjacent work if discussing agent-induced execution. Its reported results are not evidence that this detector catches those behaviors. |

Additional lead, not relied on for a novelty verdict: an indexed IEEE staging abstract for "Reducing False Positives in Provenance-Based Intrusion Detection Systems" (SheepHunter), DOI 10.1109/TIFS.2026.3734778. Canonical page/DOI retrieval failed during this review; confirm the publication record and full text before citing in a submission.

## What IEEE editors and reviewers assess

IEEE is a publisher with many venues, not a single acceptance checklist. For IEEE Access, official [reviewer criteria](https://ieeeaccess.ieee.org/reviewers/reviewer-guidelines/) and [review guidance](https://ieeeaccess.ieee.org/reviewers/reviewer-best-practices/) emphasize contribution, technical quality, evidence and reproducibility. Translate that into the following evidence:

| Reviewer question | Evidence to prepare |
|---|---|
| What is new relative to the closest work? | Exact contribution statement and method-by-method related-work matrix. |
| Is the method technically correct? | Algorithm specification, assumptions, edge cases, regression tests and analysis. |
| Are labels and experiments credible? | Independent ground truth, provenance, frozen splits, declared exclusions and uncertainty. |
| Is comparison fair? | Pinned baseline versions/configuration, input coverage and tuning budget; comparable detection units. |
| Is the improvement useful? | Attack recall at an alert budget, false alerts per endpoint-day, delay and resource cost. |
| Does each component matter? | Ablations, sensitivity studies and failure examples. |
| Can someone reproduce it? | Versioned code, data/manifests, environments and scripts producing tables/figures. |
| Are claims appropriately bounded? | Explicit threat model, detection versus prevention distinction, limitations and negative results. |

No official universal minimum accuracy, sample count, number of references, feature count or production score applies. A UI, many algorithms, GitHub stars or "AI-powered" wording cannot substitute for evidence. The [Access reproducibility program](https://ieeeaccess.ieee.org/authors/reproducibility/) describes useful artifact expectations; its particular post-publication review program should not be misrepresented as mandatory for every IEEE submission.

## Candidate contribution and go/no-go decision

Candidate A (recommended): a specific correlation policy that uses source event time, process-instance identity and explicit evidence completeness, tested under delayed/incomplete telemetry and high-volume benign activity. **Engineering feasibility: plausible. Novelty: unresolved.**

Candidate B: an empirical benchmark documenting detector failures and trade-offs under these conditions. Useful if findings are broad, reproducible and extend existing evaluation studies; a small demonstration of this project's own bugs is insufficient.

Candidate C: a new deep graph model. Defer unless a concrete weakness of existing methods and sufficient data/compute justify it. Adding a GNN/LSTM module is not itself a contribution.

Research questions:

- RQ1: At a predefined benign-alert budget, does the candidate method improve attack recall relative to corrected rules and selected operational baselines?
- RQ2: How do delay, reordering, duplicates, clock error and structured sensor loss affect decisions, evidence and latency?
- RQ3: How do ordinary, automated and AI-assisted development workloads change false alerts? Does any gain hold beyond one tool/version?
- RQ4: What are collection and analysis costs, and how many alerts cannot be decided due to missing evidence?

Use abstention/insufficient-evidence as an explicit outcome, not a way to hide misses. Report coverage and attack outcomes for abstained cases. Missing telemetry must not increase confidence that a host is safe.

Go/no-go after feasibility work: proceed to a method paper only if the fully specified method differs materially from closest work and improves a declared trade-off beyond corrected baselines. Otherwise revise the method or pursue a sufficiently substantial measurement paper. Do not force a positive finding.

## Experiment design

Three complementary tracks are necessary:

1. **Controlled replay:** same source trace, original and perturbed delivery. Suggested initial stress points (design proposals, not production statistics): delays of 0/1/10/60 seconds; a five-minute backlog burst; random and contiguous loss at 0/1/5/10%; duplicate delivery; collector restart; PID reuse and concurrent same-name processes. Include one-sensor outages and bounded clock error. Report unrealistic stresses separately from measured field distributions.
2. **Live authorized laboratory workloads:** current Windows builds, ordinary activity, development tasks and independently labeled malicious executions/behavior emulations. Collect ground truth outside the detector. Keep real malware, emulations and synthetic records separate in results. Use snapshots, disposable data, isolated networking and test accounts for malicious runs.
3. **Consenting benign field pilot:** alert-only monitoring, ordinary work and investigator review. This measures stability and alert burden, not malware recall in the absence of known attacks. A lab VM is not proof of real-world deployment.

Baseline set: original implementation as a diagnostic reference; **corrected simple rules**; corrected correlation without the candidate mechanism; candidate method; Fibratus and Wazuh with pinned rules/configuration. Add KAIROS/PIDSMaker only when telemetry mapping, resources and comparable units are established. If a comparable feature is unavailable, report coverage rather than fabricate missing inputs. Distinguish replay detector comparison from end-to-end product comparison.

Do not let the original timing/README bugs create the apparent research improvement. Keep signature/YARA/IOC-assisted experiments separate from behavior-only experiments. Give baselines a documented development-set tuning budget. An out-of-box and tuned comparison can answer different questions.

Use independent executions/hosts/days as statistical groups, not millions of correlated events as independent samples. Keep host/task/repository/family groups and later-time test data separate from tuning. Retain realistic benign-only periods. Estimate required sample size from pilot variability and desired confidence; do not label a convenience sample as representative.

Primary endpoint: attack-execution recall at a declared false-alert budget. Secondary measures: alert precision, per-category recall, false alerts per endpoint-day, evidence attribution accuracy, decision coverage, PR curves where appropriate, CPU/RAM/storage, captured/dropped events and queue growth. Define an alert's unit and incident deduplication before evaluation.

Measure latency from both source action to alert and receipt to alert. For offline backlogs, report offline delay separately; an algorithm cannot alert on an event it has not received. Include time-to-first-alert and time-to-sufficient-evidence where useful. Report intervals with grouping-aware methods and paired comparisons on matching runs.

Ablations: remove evidence-completeness handling, event-time ordering, process-instance identity, ancestry and individual signal families. Keep thresholds fixed where the question requires it, or disclose retuning. Test legitimate look-alikes and document all failures.

## AI-assisted development without changing the topic

Treat AI-assisted development as a workload stratum alongside manual development and conventional automation. Avoid treating all model-generated code as malicious, an approved action as necessarily safe, or an AI process name as proof of attribution.

Suggested paired benign tasks: dependency installation, building/testing, bulk refactoring, local web-server startup and authorized repository publishing. Suggested harmful-behavior tests: controlled unauthorized access to synthetic secrets, unexpected persistence in a disposable environment, or unexpected outbound transfer to a lab-owned sink. These are proposals only; none were executed in this phase.

Record task authorization independently, tool/model version, permission mode, repository revision, dependency lockfiles, task/prompt hash, OS image and repeat count. Use dummy credentials. Preserve actual workload traces rather than trusting an LLM's description of what happened. Repeated runs may differ.

An endpoint monitor can observe some consequences of an agent action; it generally cannot infer the user's intent, prove prompt injection, or inspect encrypted content merely from process and network events. Prompt-injection prevention, secure code analysis, sandboxing and malware detection are separate controls. Full user permissions do not eliminate the need for independent monitoring, but a user-space monitor cannot guarantee protection from an equally privileged attacker who disables it. Trust assumptions must state this explicitly.

## Real-world suitability and deployment boundary

First intended deployment: monitored Windows workstations in a small controlled LAN pilot, with an authenticated server and alert-only operation. A cloud backend is an optional transport/deployment choice, not a novelty claim. Public exposure, multi-tenant operation, high availability and large fleets add separate engineering work.

Before a pilot: fix the confirmed session and detection defects; persistent collection cursors; bounded queues with visible loss; collector health; retention; secure configuration; restore tests; clock handling and independent verification. Observe performance under actual builds and backups. Current 63 passing tests do not establish accuracy or operational readiness.

Detection is not prevention. For destructive activity, define whether an alert arrives before or after damage; later process termination does not undo file loss. Maintain existing protection during a pilot and evaluate the prototype as an additional sensor. Root/kernel compromise, unobserved activity and disabled logging are outside any claim unless separately addressed and tested.

## Development and publication milestones

| Phase | Work and deliverable | Exit condition |
|---|---|---|
| 1: scope, current report | Related-work matrix, hypothesis, threat model and proposed protocol | Conditional research direction established; novelty remains provisional until closest full texts and implementations are checked. |
| 2: baseline correction | Fix confirmed defects and telemetry loss; preserve original snapshot | Known false-positive/session reproductions resolved; collection gaps quantified. |
| 3: feasibility | Specify candidate method and replay prototype; audit closest comparable implementations | Observable improvement beyond corrected baseline, or documented decision to revise the hypothesis. |
| 4: dataset | Independent labels, benign workloads, frozen development/test split and manifests | No known leakage; labels and scope reviewed; sample-size rationale documented. |
| 5: main evaluation | Operational baselines, ablations, uncertainty and robustness | Claims supported by reproducible results, including negative outcomes. |
| 6: field evidence | Consenting alert-only pilot and operational measurements | Pilot limitations and remaining deployment risks documented. |
| 7: manuscript/artifacts | Method, results, limitations, bibliography and reproduction package | Independent reproduction of representative tables/figures and mentor review. |
| 8: submission | Journal-specific template, disclosures, authorship and submission checks | Submit only to one venue at a time; address review comments with evidence. |

A provisional 16–24-week effort is possible only with suitable expertise, lab access and scope control; dataset acquisition and external validation may take longer. These are milestones, not promises of completion or acceptance.

## Venue and manuscript strategy

[IEEE Access](https://ieeeaccess.ieee.org/about/) is a possible fit for a rigorous applied systems/measurement paper. [IEEE TDSC](https://www.computer.org/digital-library/journals/tq/tdsc-topics) explicitly includes intrusion detection, benchmarking and dependability. [IEEE TIFS](https://signalprocessingsociety.org/index.php/publications-resources/ieee-transactions-information-forensics-and-security) is another possible security-method venue. My mentoring judgment is to consider Access first for the proposed applied study; TDSC/TIFS would require a contribution and evaluation convincing to their specialist readership. No venue is a guaranteed or easy acceptance, and the target should follow the finished contribution.

Working title: **Evaluating Behavior-Based Malware Detection on Windows under Delayed Telemetry and High-Volume Benign Workloads**. If a genuinely distinct method emerges, revise the title to identify that method. AI-assisted workloads can be a subsection rather than the entire title.

Paper assets: architecture diagram, algorithm/pseudocode, threat model, related-work table, dataset table, fair-comparison table, PR/alert-budget plots, delay/loss sensitivity curves, resource measurements, ablations and failure-case studies. Every numerical claim must map to an experiment output and versioned configuration.

Follow current [submission requirements](https://ieeeaccess.ieee.org/authors/submission-guidelines/) and [article preparation guidance](https://ieeeaccess.ieee.org/authors/preparing-your-article/), including applicable AI-content disclosure. Human authors must verify sources, methods and results. Record reused code/rule provenance, attribution and license terms. Do not fabricate experimental data or imply abstract screening was full-paper review.

## Immediate next actions

1. Freeze and identify the current source snapshot and its known defects.
2. Complete full-text comparison of KAIROS, HOLMES, SIGL and the PIDSMaker evaluation; verify the recent IEEE journal leads.
3. Pin Fibratus/Wazuh versions and inspect how each handles the specific timing/attribution conditions; record unknowns until tested.
4. Write the exact candidate method and predeclare an alert-budget/recall trade-off using a small pilot to estimate variability.
5. Correct baseline defects before collecting headline comparative results.

Research-only changes in this phase: this document. No implementation fixes, live collector changes or publication submissions were made.
