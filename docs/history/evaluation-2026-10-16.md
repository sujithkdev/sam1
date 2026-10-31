# Project evaluation — 16 October 2026

## Verdict and scope

This is a behavior-based Windows endpoint detection prototype with useful engineering foundations. It is not a validated malware classifier, not ready for broad production deployment, and not yet supported by enough experimental evidence for an IEEE journal submission claiming detection effectiveness.

Subjective engineering assessment: prototype 6/10; production readiness 3/10; journal submission readiness 3/10. These are readiness judgments, not accuracy measurements. Malware precision, recall, false-positive rate and generalization are unknown. A research prototype need not be production-ready to produce a publishable paper.

Review covered the active endpoint, server, ingestion, authentication, detection, storage, response, dashboard, rules, deployment and test code, plus inactive/experimental feature modules. Archived implementations are reference material, not delivered capabilities. No live malware, endpoint collector, destructive response or production deployment was run. No Wazuh instance was benchmarked; the comparison is against official documentation.

## Verification performed

- Current regression suite: **63 passed in 30.33 seconds** using `.venv/Scripts/python.exe -m pytest -q -p no:cacheprovider --basetemp=var/review-tests-20261016b`.
- Earlier runs encountered Windows temporary-directory permissions. One reached 56 passing tests and seven fixture errors; the fresh-directory run resolved that environmental issue.
- Separate inert probes executed the actual selected function definitions extracted from source, using isolated dictionaries and an in-memory authentication database. These are focused function checks, not endpoint-to-dashboard integration tests or accuracy benchmarks.
- Five rapidly processed external HTTPS records for the same process name, each to a different address, returned score **70**, reason `C2 beaconing pattern (0.0s avg interval, external IPs only)`.
- Five ordinary documentation modifications, including `C:/Docs/README.txt`, returned score **80**, reason `Ransom note: C:/Docs/README.txt`.
- A viewer account was created, authenticated, deleted and recreated with a different password. Its original unexpired session was accepted. No real account was touched and no tokens were printed.
- Read-only inspection of `backend/data/malware_hashes.db` found **zero malware_hashes rows and zero hash_stats rows**. This does not establish that every optional IOC/YARA source is empty.

## Feature assessment

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

## Priority findings and fixes

1. **High: false beaconing detections.** `backend/server/core/detector.py:695` stores server wall-clock time; line 741 groups by process name, across destinations. Use validated source event time, bounded late-event handling, process identity `(host, pid, creation_time)` and destination identity. Require meaningful duration/interval evidence; reject zero-duration batching artifacts.
2. **High: ransomware overclaiming.** `detector.py:788` and `:828` aggregate file events by name, while `endpoint/agent.py:581` reports unknown writer. README alone should not establish a ransom note. Combine independent signals and retain unknown attribution explicitly; obtain writer evidence where supported. Distinguish suspicious activity from confirmed maliciousness. Ensure displayed scores obey their documented range.
3. **High: revoked sessions can revive.** `backend/server/auth.py:38`, `:53`, `:75`: recreated usernames reset version to 1. Use immutable account IDs or a fresh random session generation that cannot recur on recreation; add a regression test for this exact lifecycle.
4. **High: telemetry completeness is unproven.** Persist Event Log bookmarks and handle log reset; cover transient processes and IPv6; measure dropped events. File watcher clears its queue above 2,000 records. Its Win32 ctypes calls lack explicit function signatures; validate pointer/handle correctness on 64-bit Windows. That last item is a source-level concern, not a reproduced collector crash.
5. **High: threat-intelligence capability mismatch.** The hash DB is empty. `backend/server/core/hash_db.py:36` writes under backend/data rather than EDR_DATA_DIR. The read-only non-root container arrangement does not provide that location as writable, and detection catches lookup failures. Move state to the configured volume, expose feed age/count/errors and verify update wiring before claiming protection.
6. **Medium: state and evidence continuity.** Restore or reconstruct correlation after restart; repair late parent edges; assess duplicate contributions when inbox processing retries. Alert deduplication can suppress separate process instances sharing a name/reason within the suppression window.
7. **Medium: command replay namespace.** Endpoint command results are keyed by integer command ID. Server restore/replacement can reuse IDs. Include a durable server identity/generation and globally unique command IDs.
8. **Medium: operational maturity.** Add collector/worker health and alerting, bounded retention, recovery drills, signed release/update procedures, sustained load tests and explicit service-level targets. SQLite alone is not disqualifying, but this implementation's scaling and recovery envelope is unmeasured.

## Comparison with Wazuh

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

## IEEE journal readiness and research plan

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
