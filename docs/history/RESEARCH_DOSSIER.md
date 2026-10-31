# BehEDR — Research Dossier and Comparative Project Assessment

**Prepared:** 16 October 2026  
**Project:** Windows behavior-based malware detection (`C:\projects\newmalware`)  
**Document role:** A standalone research companion to PROJECT_MASTER_PLAN.md. It consolidates the complete existing research and code-evaluation records and adds direct comparisons, claim boundaries, research gaps and an evidence-completion plan.

## 1. What is included and what is not yet established

This dossier preserves the research findings gathered in this conversation. It is not an exhaustive systematic review of every GitHub repository or IEEE publication. There is no defensible guarantee that no related work has been missed.

Included:

- Current project capabilities, limitations, test results and confirmed defects.
- Related tools, original repository links, relevant papers and official publication guidance.
- A direct comparison of BehEDR with the closest operational and research alternatives.
- Research questions, candidate contributions, experiment design and publication milestones.
- AI-assisted development as a workload category without changing the project's central topic.
- An explicit register of missing evidence and the work required to close it.
- Complete snapshots of the prior code evaluation and phase-one research documents, including their sources and access limitations.

Not established: malware accuracy, superiority over Wazuh/Fibratus, real-world production readiness, proven novelty, guaranteed IEEE acceptance or universal zero-day detection. No third-party detector was executed for this comparison. This document creation did not perform new experiments or fix code.

### Evidence notation

| Label | Meaning |
|---|---|
| Local observation | Code inspection or a specific isolated check recorded in the local evaluation |
| Documented capability | Described by the original tool's repository or official documentation; not independently benchmarked here |
| Paper claim | Described in a paper/abstract; applies to that study's assumptions and datasets |
| Proposal | Work or experiment recommended for this project; not an implemented result |
| Unknown | Evidence unavailable or insufficient; never treated as absence of a capability |

The previously reported 63 passing regression tests establish the behavior covered by those tests. They do not measure malware accuracy. The isolated false-positive and session checks demonstrate particular defects, not a complete penetration test.

## 2. Direct project comparison

The following is a qualitative comparison, not a performance ranking. Sources are the linked original repositories and the detailed research register in section 8.

| Dimension | BehEDR today | Closest comparison | Implication |
|---|---|---|---|
| Windows behavioral collection | Polling plus conditional Windows event paths | [Fibratus](https://github.com/rabbitstack/fibratus), [WHIDS](https://github.com/0xrawsec/whids) | Live collection completeness must be measured; a custom agent is not novelty by itself |
| Event correlation | Rules, behavior windows, ancestry and sequence logic; identified timing/identity defects | Fibratus sequence rules; HOLMES information-flow correlation | Compare against corrected correlation, not just the project's buggy baseline |
| Graph analysis | Partial process-instance context | [KAIROS](https://github.com/ubc-provenance/kairos) | A process tree does not provide whole-system information-flow provenance |
| Broad security coverage | Narrow behavioral prototype | [Wazuh](https://github.com/wazuh/wazuh) | Wazuh is the broader operational comparator; BehEDR need not clone every feature for a focused paper |
| Detection rules | Custom heuristics and YAML content | [Sigma](https://github.com/SigmaHQ/sigma) | A new rule collection alone needs stronger evaluation and contribution justification |
| Investigation | Alerts, graphs and dashboard paths | [Chainsaw](https://github.com/WithSecureOpenSource/chainsaw), WHIDS | Distinguish offline hunting from continuous detection and evidence collection |
| Dynamic malware analysis | No equivalent full sandbox established | [CAPE](https://github.com/kevoreilly/CAPEv2) | CAPE is supporting lab infrastructure, not an interchangeable endpoint baseline |
| Model-based detection | Advanced experimental models unsupported by active configuration | KAIROS / [PIDSMaker](https://github.com/ubc-provenance/PIDSMaker) | Do not advertise LSTM/GNN protection based on dormant files |
| Known-hash evidence | Inspected malware-hash database was empty | Optional signature/intelligence components in other tools | Evaluate populated/available feeds separately from behavioral logic |
| Response | Limited guarded operator commands | Wazuh active response; other EDR response features vary | Evaluate only matched actions/configurations; no automatic-isolation claim for BehEDR |
| Timing/loss robustness | Known gaps; proposed improvement area | Comparator behavior under these exact conditions is unknown | Inspect and test before claiming competitors lack the feature |
| Explanation quality | Reasons and labels, sometimes stronger than evidence | HOLMES/KAIROS attack reconstruction | Evidence attribution and analyst usefulness need evaluation |
| Production readiness | Unqualified operational envelope | Operational tool deployment guidance is more extensive | Repository activity is not evidence of superior accuracy or a security guarantee |
| Accuracy/overhead | Not measured on representative data | Published results use differing setups | No valid numerical ranking exists from this review |

### Where BehEDR has useful foundations

The code has durable spool/inbox structures, explicit host credentials, role controls, guarded response parameters, a dashboard and regression tests. These make it a plausible experimentation platform. They are engineering assets, not proven comparative advantages.

### Where BehEDR is presently weaker

Confirmed benign false-positive examples, incomplete collection evidence, session lifecycle correctness, empty hash intelligence, in-memory correlation recovery and unmeasured operational behavior are substantive weaknesses. Resolve these before treating comparative experiment results as reliable.

### What should remain unknown until tested

Whether BehEDR is faster, lighter, more accurate, more explainable, or more robust than Fibratus/Wazuh cannot be inferred from implementation size or architecture. Likewise, absence of a documented competitor feature is not proof that it is absent from code.

## 3. Contribution and claim boundaries

| Candidate statement | Present verdict | Evidence needed |
|---|---|---|
| We built a Windows behavioral monitoring prototype | Supported by implementation review | A reproducible build and documented deployment strengthen it |
| We invented process ancestry detection | Unsupported; extensive prior art | Do not make this broad claim |
| Our corrected version avoids the observed batch/README defects | Not yet implemented/verified | Corrective changes and regressions |
| Our method improves detection under delayed/incomplete telemetry | Candidate hypothesis | Defined method, fair baselines, holdout evaluation and uncertainty |
| Our detector handles AI-assisted development well | Unknown | Paired benign/malicious-behavior workload evidence across configurations |
| Our system detects unknown malware | Not established | Explicit family/time holdout and bounded claims; not universal zero-day protection |
| Our system predicts future attacks | Not current demonstrated task | Separate forecasting definition and time-valid evaluation |
| Our system prevents ransomware damage | Not established by alerts | Before-damage timing and controlled prevention evaluation |
| Our results justify an IEEE submission | Conditional | Contribution, valid experiments, reproducibility and venue fit |

Recommended research focus: **behavior-based detection under telemetry imperfections and realistic benign activity**. A possible method could combine event-time handling, process-instance identity and explicit evidence completeness. Those ingredients are established ideas; novelty must lie in a specific justified method or substantial new measurement finding.

If the candidate method adds no meaningful advantage over corrected simple logic, report that honestly and revise the research question. A rigorous measurement paper may be possible, but merely demonstrating this project's own bugs is insufficient.

## 4. Evaluation blueprint

### Research questions

- RQ1: At a declared benign-alert budget, does the candidate method retain or improve attack-execution recall over corrected rules and selected operational baselines?
- RQ2: How do delivery delay, reordering, duplicates, clock error, missing parents and sensor loss affect decisions and evidence?
- RQ3: How does legitimate high-volume activity, including AI-assisted development, affect false alerts?
- RQ4: What are collection/analysis costs, recovery behavior and the proportion of insufficient-evidence decisions?

### Experimental arms

| Arm | Purpose | Required boundary |
|---|---|---|
| Original BehEDR | Diagnostic reference | Do not use known defects to manufacture the claimed research gain |
| Corrected simple rules | Strong transparent baseline | Same available inputs and declared threshold selection |
| Corrected correlation without proposed component | Isolate contribution | Match other settings or disclose retuning |
| Proposed method | Test hypothesis | Freeze before final holdout evaluation |
| Fibratus and Wazuh | Operational comparison | Pin versions, inputs, configuration, rules and tuning effort |
| KAIROS/PIDSMaker if feasible | Research comparison | Validate telemetry mapping and common output granularity |

Run both equivalent-input detector experiments and separate end-to-end product experiments. Do not hide collector differences or compare offline hunting latency with online alert latency. Separate signature-assisted and behavior-only results.

### Dataset strata

1. Benign office/browsing activity.
2. Authorized administration, backups, installers and synchronization.
3. Manual development and conventional automation.
4. AI-assisted development with recorded permission modes and tool versions.
5. Controlled technique emulations, labeled as emulations.
6. Authorized isolated real-malware runs, if available, labeled separately.
7. Public provenance datasets where schema and labels are compatible.

Ground truth comes from independent execution records, reviewed scenario outcomes and reliable labels, not from the detector firing. A sandbox report or LLM judgment alone is not sufficient to settle every label. Record uncertain labels and assess their impact.

### Metrics and analysis

- Define the evaluation unit first: event, process instance, execution, attack scenario or incident.
- Primary result: attack-execution recall at a declared false-alert budget.
- Secondary results: precision, per-category recall, false alerts per endpoint-day, PR curves where meaningful, evidence attribution, abstention/coverage, source-to-alert and receipt-to-alert latency, CPU/RAM/storage, telemetry loss and backlog.
- Use held-out host/time/task/family groups appropriate to the claim. Do not randomly split near-identical events from one execution across train and test.
- Use grouped uncertainty estimates and paired comparisons where justified; related events are not independent samples.
- Count insufficient-evidence cases visibly. Do not remove hard cases to raise apparent accuracy.
- Predeclare tuning budgets, exclusions, stopping rules and primary outcomes.

### Component and robustness studies

Remove or vary event-time handling, process-instance correlation, ancestry, completeness handling and each signal family. Include delayed bursts, lost sensor channels, duplicates, restart, PID reuse and clock uncertainty. Stress levels must be labeled as experimental settings unless supported by field measurements.

A benign field pilot measures false-alert burden and stability. It does not estimate malware recall without independently known malicious executions. All live harmful scenarios belong in an authorized isolated lab, with disposable data and controlled destinations.

## 5. Real-world and AI-assisted development assessment

The intended initial deployment is a small, consenting, alert-only Windows pilot alongside existing protection. LAN deployment is simpler to qualify first; cloud hosting adds access, exposure and privacy work without creating scientific novelty.

Real-world suitability requires measured collection coverage, acceptable alert burden, resource costs, secure administration, visible failures, retention and successful restore/rollback. Detection is not remediation: an alert after data loss does not demonstrate prevention.

AI-assisted development remains a workload category. Use paired tasks such as builds, tests, dependency installation, refactoring and authorized repository operations. Record tool/model version, task authorization, repository revision, permission settings, dependencies and repeated-run variation. Use dummy secrets for controlled misuse scenarios.

The endpoint detector may observe a harmful action but cannot generally infer whether it was caused by prompt injection or determine human intent solely from process ancestry. Legitimate signed tools can be misused; generated code is not automatically malware. Secure code review, sandboxing, prompt-injection prevention and behavioral malware detection address different problems.

## 6. Missing-evidence register and closure plan

| ID | Missing evidence | Closure action | Blocks which claim? |
|---|---|---|---|
| G01 | Exhaustive related-work coverage | Full-text screening, backward/forward citations, documented search exports and exclusions | Strong novelty claim |
| G02 | Exact comparator versions | Record release/tag/commit, dependency versions and rules | Reproducible comparison |
| G03 | Competitor timing/loss behavior | Inspect relevant implementation and run matched traces | Robustness superiority |
| G04 | Baseline defects resolved | Implement and verify the recorded regression cases | Reliable experimental baseline |
| G05 | Windows collection completeness | Compare controlled actions with independent observations | End-to-end detection coverage |
| G06 | Representative ground truth | Dataset provenance, label review, uncertain-label policy | Accuracy/generalization |
| G07 | Fair tuning and holdout separation | Frozen development/test split, declared tuning budgets | Unbiased result claims |
| G08 | Integrated security assessment | Scope, authorization, findings, fixes and retests | Pilot/production readiness |
| G09 | Sustained operational evidence | Load, recovery, restore and benign pilot records | Real-world suitability |
| G10 | Reproduction by another person | Independent build and representative result reproduction | Artifact reliability |
| G11 | Venue-specific fit and requirements | Recheck current official guidance against finished contribution | Submission readiness |
| G12 | Latest IEEE journal leads fully verified | Obtain canonical full text/metadata; resolve inaccessible records | Complete related-work treatment |

### Structured review worksheet

For every retained paper record: title, authors, year, venue, DOI/URL, paper version, peer-review status, full-text availability, task, assumptions, OS/telemetry, dataset, labels, split, baseline, metrics, code/data availability, limitations, overlap and exact difference from the proposed method.

For every tool record: repository, chosen release/commit, license, supported platform, input schema, enabled collectors, rule configuration, state persistence, ordering behavior, resource limits, output schema, tested scenarios and unresolved questions.

Do not fill unknown fields by guessing. This is the mechanism for improving research completeness; the phrase “all research” is not evidence of completeness.

## 7. Development and publication handoff

Use the 13-phase SDLC in [PROJECT_MASTER_PLAN.md](C:/projects/newmalware/PROJECT_MASTER_PLAN.md), including architecture/workflow diagrams and functional/security acceptance gates.

Research-critical ordering:

1. Freeze current code and record known defects.
2. Complete closest-work comparison and specify the exact candidate contribution.
3. Correct baseline security, timing, identity and collection behavior.
4. Build the experiment harness and obtain independent labels.
5. Freeze evaluation protocol and baseline configurations.
6. Run holdout comparisons, ablations, robustness and cost studies.
7. Perform a consenting benign pilot if making operational claims.
8. Package code/data manifests and independently reproduce results.
9. Write and review the paper; submit only claims supported by evidence.

Possible manuscript title: **Evaluating Behavior-Based Malware Detection on Windows under Delayed Telemetry and High-Volume Benign Workloads**. Change it to match the demonstrated contribution.

IEEE submission requires a suitable contribution and technically credible evidence, not a predetermined accuracy number. The target journal should follow the completed study. Acceptance is not guaranteed, and publication does not certify the product. Follow current authorship, attribution and AI-content disclosure requirements.

The following two sections preserve the complete prior source documents, with heading levels adjusted only for inclusion. They are dated evidence snapshots; their “no code changed” statements describe those review activities. Some overlap is retained deliberately so findings and limitations are not lost.


## 8. Complete phase-one research record


Research date: 16 October 2026. Project: behavior-based malware detection on Windows.

### Decision

Continue as a research prototype, with a narrower hypothesis and an empirical study. Do not claim a novel general malware detector, zero-day protection, production readiness, or a validated accuracy percentage. Keep AI-assisted development as one workload category, not a replacement research topic.

Recommended candidate question: **How can a Windows behavioral detector maintain attack recall and useful evidence while controlling false alerts under delayed/incomplete telemetry and legitimate high-volume activity?**

This question is not yet certified novel. Event-time handling, provenance, uncertainty and false-positive reduction all have prior art. A defensible contribution must be a specific method or new measurement finding demonstrated beyond existing implementations. Merely correcting this project's bugs is engineering work, not sufficient research novelty.

### Scope and evidence limits

This is a targeted scoping review, not an exhaustive review of all GitHub repositories or all IEEE publications. Search covered IEEE publisher pages, official journal guidelines, USENIX proceedings, author-hosted manuscripts, arXiv records and original repositories. Query families included behavior-based malware detection, provenance and temporal graphs, Windows ETW/Sysmon, false positives, out-of-order/incomplete telemetry, evaluation bias and coding-agent security. Foundational work from 2018 onward and recent 2024–2026 work were considered.

Included: host behavioral methods, relevant evaluation methodology, operational comparators and agent-workload studies. Excluded from core comparisons: unrelated network-only classifiers, static-PE-only classifiers, marketing accuracy claims, and repositories without an identifiable relevant implementation. These exclusions are scope choices, not claims those fields are unimportant.

Evidence depth: selected method/evaluation/threat-model sections of KAIROS and the 2025 comparative study were inspected; other paper entries below were screened through publisher/author abstracts or records. Repository inspection covered documentation and selected Fibratus parser code, not complete code audits or executions. Some IEEE full texts were inaccessible. No new detection experiments, malware runs or third-party installations were performed in this phase. Earlier local findings remain in evaluation-2026-10-16.md.

Full-text extraction, forward/backward citation screening, exact release pinning and execution-based comparator validation remain necessary before making a formal novelty claim. No absence-of-prior-work claim follows from an unsuccessful search.

### Tool and repository comparison

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

### Related-work matrix

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

### What IEEE editors and reviewers assess

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

### Candidate contribution and go/no-go decision

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

### Experiment design

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

### AI-assisted development without changing the topic

Treat AI-assisted development as a workload stratum alongside manual development and conventional automation. Avoid treating all model-generated code as malicious, an approved action as necessarily safe, or an AI process name as proof of attribution.

Suggested paired benign tasks: dependency installation, building/testing, bulk refactoring, local web-server startup and authorized repository publishing. Suggested harmful-behavior tests: controlled unauthorized access to synthetic secrets, unexpected persistence in a disposable environment, or unexpected outbound transfer to a lab-owned sink. These are proposals only; none were executed in this phase.

Record task authorization independently, tool/model version, permission mode, repository revision, dependency lockfiles, task/prompt hash, OS image and repeat count. Use dummy credentials. Preserve actual workload traces rather than trusting an LLM's description of what happened. Repeated runs may differ.

An endpoint monitor can observe some consequences of an agent action; it generally cannot infer the user's intent, prove prompt injection, or inspect encrypted content merely from process and network events. Prompt-injection prevention, secure code analysis, sandboxing and malware detection are separate controls. Full user permissions do not eliminate the need for independent monitoring, but a user-space monitor cannot guarantee protection from an equally privileged attacker who disables it. Trust assumptions must state this explicitly.

### Real-world suitability and deployment boundary

First intended deployment: monitored Windows workstations in a small controlled LAN pilot, with an authenticated server and alert-only operation. A cloud backend is an optional transport/deployment choice, not a novelty claim. Public exposure, multi-tenant operation, high availability and large fleets add separate engineering work.

Before a pilot: fix the confirmed session and detection defects; persistent collection cursors; bounded queues with visible loss; collector health; retention; secure configuration; restore tests; clock handling and independent verification. Observe performance under actual builds and backups. Current 63 passing tests do not establish accuracy or operational readiness.

Detection is not prevention. For destructive activity, define whether an alert arrives before or after damage; later process termination does not undo file loss. Maintain existing protection during a pilot and evaluate the prototype as an additional sensor. Root/kernel compromise, unobserved activity and disabled logging are outside any claim unless separately addressed and tested.

### Development and publication milestones

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

### Venue and manuscript strategy

[IEEE Access](https://ieeeaccess.ieee.org/about/) is a possible fit for a rigorous applied systems/measurement paper. [IEEE TDSC](https://www.computer.org/digital-library/journals/tq/tdsc-topics) explicitly includes intrusion detection, benchmarking and dependability. [IEEE TIFS](https://signalprocessingsociety.org/index.php/publications-resources/ieee-transactions-information-forensics-and-security) is another possible security-method venue. My mentoring judgment is to consider Access first for the proposed applied study; TDSC/TIFS would require a contribution and evaluation convincing to their specialist readership. No venue is a guaranteed or easy acceptance, and the target should follow the finished contribution.

Working title: **Evaluating Behavior-Based Malware Detection on Windows under Delayed Telemetry and High-Volume Benign Workloads**. If a genuinely distinct method emerges, revise the title to identify that method. AI-assisted workloads can be a subsection rather than the entire title.

Paper assets: architecture diagram, algorithm/pseudocode, threat model, related-work table, dataset table, fair-comparison table, PR/alert-budget plots, delay/loss sensitivity curves, resource measurements, ablations and failure-case studies. Every numerical claim must map to an experiment output and versioned configuration.

Follow current [submission requirements](https://ieeeaccess.ieee.org/authors/submission-guidelines/) and [article preparation guidance](https://ieeeaccess.ieee.org/authors/preparing-your-article/), including applicable AI-content disclosure. Human authors must verify sources, methods and results. Record reused code/rule provenance, attribution and license terms. Do not fabricate experimental data or imply abstract screening was full-paper review.

### Immediate next actions

1. Freeze and identify the current source snapshot and its known defects.
2. Complete full-text comparison of KAIROS, HOLMES, SIGL and the PIDSMaker evaluation; verify the recent IEEE journal leads.
3. Pin Fibratus/Wazuh versions and inspect how each handles the specific timing/attribution conditions; record unknowns until tested.
4. Write the exact candidate method and predeclare an alert-budget/recall trade-off using a small pilot to estimate variability.
5. Correct baseline defects before collecting headline comparative results.

Research-only changes in this phase: this document. No implementation fixes, live collector changes or publication submissions were made.

## 9. Complete current-project evaluation record


### Verdict and scope

This is a behavior-based Windows endpoint detection prototype with useful engineering foundations. It is not a validated malware classifier, not ready for broad production deployment, and not yet supported by enough experimental evidence for an IEEE journal submission claiming detection effectiveness.

Subjective engineering assessment: prototype 6/10; production readiness 3/10; journal submission readiness 3/10. These are readiness judgments, not accuracy measurements. Malware precision, recall, false-positive rate and generalization are unknown. A research prototype need not be production-ready to produce a publishable paper.

Review covered the active endpoint, server, ingestion, authentication, detection, storage, response, dashboard, rules, deployment and test code, plus inactive/experimental feature modules. Archived implementations are reference material, not delivered capabilities. No live malware, endpoint collector, destructive response or production deployment was run. No Wazuh instance was benchmarked; the comparison is against official documentation.

### Verification performed

- Current regression suite: **63 passed in 30.33 seconds** using `.venv/Scripts/python.exe -m pytest -q -p no:cacheprovider --basetemp=var/review-tests-20261016b`.
- Earlier runs encountered Windows temporary-directory permissions. One reached 56 passing tests and seven fixture errors; the fresh-directory run resolved that environmental issue.
- Separate inert probes executed the actual selected function definitions extracted from source, using isolated dictionaries and an in-memory authentication database. These are focused function checks, not endpoint-to-dashboard integration tests or accuracy benchmarks.
- Five rapidly processed external HTTPS records for the same process name, each to a different address, returned score **70**, reason `C2 beaconing pattern (0.0s avg interval, external IPs only)`.
- Five ordinary documentation modifications, including `C:/Docs/README.txt`, returned score **80**, reason `Ransom note: C:/Docs/README.txt`.
- A viewer account was created, authenticated, deleted and recreated with a different password. Its original unexpired session was accepted. No real account was touched and no tokens were printed.
- Read-only inspection of `backend/data/malware_hashes.db` found **zero malware_hashes rows and zero hash_stats rows**. This does not establish that every optional IOC/YARA source is empty.

### Feature assessment

| Feature | Current assessment |
|---|---|
| Process collection | Implemented Windows polling; short-lived processes between polls and initially running processes can be missed. |
| Event Log / ETW collection | Implementation exists; requires providers, permissions and configuration. Event Log cursors are in memory and startup begins at current time; restart recovery is incomplete. |
| Process ancestry graph | Process-instance identity is useful. Missing/out-of-order parents and restart recovery limit completeness. |
| Command-line / parent-child / LOLBin rules | Active heuristic detection, useful for triage; legitimate administrative activity can match. |
| Behavioral chains / sequences | Implemented rule and lightweight sequence logic; no representative effectiveness study. |
| Network behavior | Active but arrival-time windows and grouping by process name can mix instances and unrelated destinations. IPv6 handling needs correction. |
| File behavior / ransomware | Active heuristics; watcher reports writer as unknown, filename checks overclaim maliciousness, rates combine unrelated writers. |
| DLL monitoring / masquerading | Implemented checks; visibility and legitimate exceptions require live validation. |
| YARA | Optional scanner capability, dependent on installation and rule quality; not proof of general malware coverage. |
| Hash / threat intelligence | Hash lookup code exists but inspected DB is empty; updater is not wired into active startup. Hash DB path ignores configured data directory. Other IOC loading is separate. |
| Deep learning / advanced anomaly models | Experimental modules are not supported by this release; enabling experimental ML causes startup validation to reject it. Do not advertise trained LSTM/GNN/autoencoder protection. |
| Risk / explanation / MITRE labels | Useful investigation output, not calibrated probabilities or proof of compromise. Some wording is stronger than the evidence. |
| Durable endpoint spool / server inbox | Useful persistence, acknowledgements and retry handling. Capacity, poison records, retention and restart semantics need operational tests. |
| Dashboard / investigation | Implemented alerts, telemetry and operator workflows; this review did not validate the rendered UI end to end. |
| Identity / authorization | Scrypt passwords, roles, JWT validation, CSRF protection and host-bound agent tokens are strengths. Account recreation revives old sessions. |
| Response commands | Guarded administrative process termination and limited commands exist; process identity/hash checks and replay reservation improve safety. |
| Automatic containment / isolation | Not available in active advertised capabilities. Do not treat dormant playbook code as delivered protection. |
| Notifications / Wazuh bridge | Not registered as active application capabilities. Source-file presence is insufficient. |
| Development-tool context | Optional additional context/policy checks; not an OS sandbox and not the central malware research contribution. |
| UBA / memory forensics / active learning | Source modules do not establish supported, integrated or validated production features. |
| Deployment / availability | Single-process server, SQLite persistence, memory-based correlation. Container/reverse-proxy files are useful but do not demonstrate HA or enterprise capacity. |
| Backup / monitoring / audit | Components exist; recovery, tamper resistance, retention and collector health need realistic validation. |

### Priority findings and fixes

1. **High: false beaconing detections.** `backend/server/core/detector.py:695` stores server wall-clock time; line 741 groups by process name, across destinations. Use validated source event time, bounded late-event handling, process identity `(host, pid, creation_time)` and destination identity. Require meaningful duration/interval evidence; reject zero-duration batching artifacts.
2. **High: ransomware overclaiming.** `detector.py:788` and `:828` aggregate file events by name, while `endpoint/agent.py:581` reports unknown writer. README alone should not establish a ransom note. Combine independent signals and retain unknown attribution explicitly; obtain writer evidence where supported. Distinguish suspicious activity from confirmed maliciousness. Ensure displayed scores obey their documented range.
3. **High: revoked sessions can revive.** `backend/server/auth.py:38`, `:53`, `:75`: recreated usernames reset version to 1. Use immutable account IDs or a fresh random session generation that cannot recur on recreation; add a regression test for this exact lifecycle.
4. **High: telemetry completeness is unproven.** Persist Event Log bookmarks and handle log reset; cover transient processes and IPv6; measure dropped events. File watcher clears its queue above 2,000 records. Its Win32 ctypes calls lack explicit function signatures; validate pointer/handle correctness on 64-bit Windows. That last item is a source-level concern, not a reproduced collector crash.
5. **High: threat-intelligence capability mismatch.** The hash DB is empty. `backend/server/core/hash_db.py:36` writes under backend/data rather than EDR_DATA_DIR. The read-only non-root container arrangement does not provide that location as writable, and detection catches lookup failures. Move state to the configured volume, expose feed age/count/errors and verify update wiring before claiming protection.
6. **Medium: state and evidence continuity.** Restore or reconstruct correlation after restart; repair late parent edges; assess duplicate contributions when inbox processing retries. Alert deduplication can suppress separate process instances sharing a name/reason within the suppression window.
7. **Medium: command replay namespace.** Endpoint command results are keyed by integer command ID. Server restore/replacement can reuse IDs. Include a durable server identity/generation and globally unique command IDs.
8. **Medium: operational maturity.** Add collector/worker health and alerting, bounded retention, recovery drills, signed release/update procedures, sustained load tests and explicit service-level targets. SQLite alone is not disqualifying, but this implementation's scaling and recovery envelope is unmeasured.

### Comparison with Wazuh

| Dimension | This project | Wazuh documented capability |
|---|---|---|
| Purpose | Focused experimental Windows behavioral detection | Broader endpoint security and SIEM platform |
| Malware detection | Custom behavior rules plus optional signatures/IOCs | Rules, suspicious-behavior analysis and signature/intelligence integrations |
| Behavioral detection | Custom ancestry and sequence logic | Configured telemetry and rules can detect behavior; it is incorrect to describe Wazuh as signature-only |
| File monitoring | Directory-change events and heuristics | Integrity baselines, checksums/attributes, scheduled and real-time monitoring |
| YARA | Optional scanner integration | Documented FIM/YARA integration requiring setup |
| Platforms | Windows-focused | Windows, Linux, macOS and additional supported agent platforms |
| Vulnerability / configuration assessment | No equivalent integrated coverage demonstrated | Software inventory/CVE correlation and security configuration assessment |
| Response | Limited guarded manual commands; no active network isolation | Configurable active-response scripts triggered by rules |
| Fleet management | Basic enrollment and per-host credentials | Centralized agent configuration and grouping |
| Availability / scale | Single server process and SQLite | Documented distributed server/indexer architecture and clustered deployment options |
| Detection accuracy | Unknown | Cannot rank against this project without the same labeled workload and declared configurations |

Operationally, Wazuh is the stronger starting point for the breadth of features above. This project can still be valuable for evaluating a narrowly defined behavioral method. Neither tool should be claimed to detect all malware. No measured performance or detection superiority is asserted here.

Primary sources:

- [Wazuh malware detection](https://documentation.wazuh.com/current/user-manual/capabilities/malware-detection/index.html)
- [Wazuh architecture](https://documentation.wazuh.com/current/getting-started/architecture.html)
- [Wazuh file integrity monitoring](https://documentation.wazuh.com/current/user-manual/capabilities/file-integrity/)
- [Wazuh FIM/YARA integration](https://documentation.wazuh.com/current/user-manual/capabilities/malware-detection/fim-yara.html)
- [Wazuh active response](https://documentation.wazuh.com/current/user-manual/capabilities/active-response/)
- [Wazuh agent platforms](https://documentation.wazuh.com/current/getting-started/components/wazuh-agent.html)
- [Wazuh vulnerability detection](https://documentation.wazuh.com/current/user-manual/capabilities/vulnerability-detection/index.html)
- [Wazuh configuration assessment](https://documentation.wazuh.com/current/user-manual/capabilities/sec-config-assessment/index.html)
- [Wazuh centralized configuration](https://documentation.wazuh.com/current/user-manual/reference/centralized-configuration.html)

### IEEE journal readiness and research plan

The missing elements are a defensible contribution and reproducible empirical evidence, not a larger dashboard or simply more algorithms. IEEE Access explicitly asks reviewers to assess sufficient benchmarking/validation and whether conclusions follow from data; individual IEEE journals have their own scope and standards. Acceptance cannot be promised.

Keep the topic behavior-based malware detection. A possible research question is whether event-time, process-instance-aware correlation reduces false alerts without sacrificing attack detection compared with simple rule aggregation. Novelty must be established through a literature review; this question is a proposal, not a verified novel contribution.

Before submission:

1. Fix the confirmed correctness/security issues and freeze a versioned implementation.
2. Build labeled malicious-behavior and benign workloads, including browsers, installers, backup/sync, development tools and authorized administration. Evaluate malware in an isolated authorized lab. Distinguish simulations from real malware observations.
3. Use held-out hosts/time periods/families as appropriate; prevent training/tuning/test leakage. Do not label alerts as malicious simply because a rule fired.
4. Compare simple rules, current correlation, improved correlation and Wazuh with declared versions/configurations. Separate equal-telemetry detector comparison from full endpoint-to-alert comparison. Include both default and responsibly tuned baselines where feasible.
5. Report precision, recall, F1, false alerts per endpoint-day, detection latency, telemetry loss, CPU/RAM/storage costs and uncertainty intervals. Define whether each metric counts events, executions or attack scenarios.
6. Run ablations for ancestry, sequence, file and network signals; separately report signatures/IOCs so behavioral performance is not credited with known-hash detections.
7. Publish reproducible experiment scripts, configuration, sanitized traces where permitted, data provenance, limitations and negative results. Include restart/offline/backlog tests and benign look-alike cases.

Possible working title: **Behavior-Based Malware Detection on Windows Using Process and Event Correlation: Design and Empirical Evaluation**. Use it only if the implemented and measured contribution matches it.

Sources: [IEEE Access reviewer best practices](https://ieeeaccess.ieee.org/reviewers/reviewer-best-practices/), [submission guidelines](https://ieeeaccess.ieee.org/authors/submission-guidelines/), [reproducibility guidance](https://ieeeaccess.ieee.org/authors/reproducibility/).

No product code was changed as part of this review. The correct next milestone is a trustworthy, measured laboratory release, followed by a monitored pilot; a 9/10 production label is not supported by the current evidence.

## 10. Document integrity and update policy

This dossier adds comparison and planning analysis to preserved source records. It is a new document, not a new software implementation or a submitted paper. Existing files remain unchanged.

When updating it, date new observations, distinguish documented capabilities from executed tests, attach evidence for resolved gaps, and retain limitations that affect claims. Numerical results from external papers must not be transferred to BehEDR or ranked across incompatible datasets.

Supporting consolidated handbook: [PROJECT_MASTER_PLAN.md](C:/projects/newmalware/PROJECT_MASTER_PLAN.md). Original dated sources: [phase-one research](C:/projects/newmalware/docs/phase-1-research-2026-10-16.md) and [code evaluation](C:/projects/newmalware/docs/evaluation-2026-10-16.md).
