# Phase 8 verification — 23 October 2026

Phase 8's queue/storage controls, conservative offline retention, recovery
checkpointing, worker health and bounded operational tests are implemented.
This is not a declaration of production readiness or research completion.

## Verification outcomes

- Full regression suite: **172 passed in 78.41 seconds**.
- Ruff: passed for backend, endpoint, launcher, tests and Phase 8 probe tools.
- Docker deployment: all **17 recorded checks passed**, including worker health,
  isolated checkpoint/retention with compaction, HTTPS ingestion, restart,
  volume recreation, backup restore and graceful shutdown (exit code 0).
- Actual disk exhaustion in a disposable 16 MiB tmpfs: admission rejected input,
  no partial batch remained, processing recovered after releasing space, and
  SQLite integrity remained `ok`.
- Real SQLite page-limit exhaustion and abrupt termination during retention:
  passed regression tests; transaction rollback and subsequent application
  recovery were verified.
- Three final synthetic load scenarios completed with retry deduplication,
  committed replay and database integrity checks passing.

Docker image identity:
`sha256:4e7f13ec21c5f7fec4996d9209f740dae0181a172e179cb6616fcec829fdb284`

Final load source/rule fingerprint:
`78364da2d3350ca5e679107cd53babc343c38da8709a10a529e7d7e62dd6d217`

## Final local load observations

Windows 11, Python 3.12.14. Host resources were shared with desktop/Docker
activity; these short runs are exploratory measurements, not isolated benchmarks.

| Events | Simulated hosts | Batch | Admission events/s | Drain events/s | Processing p95 | Sampled RSS peak | Replay |
|---:|---:|---:|---:|---:|---:|---:|---:|
| 300 | 1 | 25 | 3960 | 163 | 11.4 ms | 150.0 MiB | 35 ms |
| 1000 | 4 | 50 | 4015 | 110 | 24.2 ms | 153.0 MiB | 76 ms |
| 2000 | 8 | 100 | 5920 | 66 | 61.4 ms | 157.8 MiB | 160 ms |

Admission uses in-process calls and concurrency across batch submissions.
Drain is sequential with the actual analysis path. The probes also resubmit all
inputs to simulate lost acknowledgements. Processing time is not end-to-end
endpoint alert latency. RSS sampling can miss peaks. These values do not justify
a maximum endpoint count or a promised sustained throughput. The declining
drain rate warrants longer representative profiling before scaling deployment.

## Artifacts and repeatability

- `var/phase8/load-final.json`: final measured values, environment, source hash.
- `var/phase8/load-results.json`: earlier exploratory run, preserved separately.
- `var/phase8/disk-results.json`: actual ENOSPC results.
- `var/phase8/deployment-final/results.json`: final deployment checks.
- `tools/phase8_load_probe.py`: fresh subprocess databases for every load case.
- `tools/phase8_disk_probe.py`: bounded disposable Docker tmpfs fault test.
- `tools/phase8_container_probe.py`: fresh in-container retention database.

The Docker lab was stopped cleanly after verification. Existing lab volumes,
backups and prior results were preserved. Retention tests used disposable
databases; no production telemetry was pruned.

See [operations runbook](../operations/phase8-operations.md) for offline maintenance and its
scope. Incident/evidence holds, permanent tombstones and retained backups mean
this is not complete privacy erasure. Sustained fleet load, physical power-loss
qualification and real Windows detection calibration remain outside these
bounded checks. Phase 6/7 empirical gates have not been marked complete.
