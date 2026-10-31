# Verification and evidence register

Reports are bounded by their date, environment and scope. They are not cumulative
claims that all release or research gates have passed.

| Record | Scope |
|---|---|
| [Initial local verification](verification.md) | September hardening and development-tool regressions |
| [Phase 1 security](phase1-security-2026-10-22.md) | Dated security implementation and checks |
| [Deployment verification](phase2-verification-2026-10-22.md) | Docker/backend checks and open guest gates |
| [Phase 6 review](phase6-closeout.md) | Rule/review checks and unresolved live calibration |
| [Operational verification](phase8-verification-2026-10-23.md) | Bounded load/failure checks |
| [25 October verification](verification-2026-10-25.md) | Synthetic transport and workflow checks |
| [30 October P1 record](../development/P1_LIVE_TRANSPORT_2026-10-30.md) | 207 passing tests plus separately passing HTTP restart rerun; live pending |
| [Cleanup](CLEANUP_2026-10-30.md) | Removed disposable artifacts; retained evidence |
| [Cleanup machine record](cleanup-2026-10-30.json) | Exact removal paths and sizes |
| [Dependency audit](dependency-audit.json) | Historical machine-readable audit |
| [R0 verification](../r0/VERIFICATION.md) | Installation checks and preserved baseline integrity |

Private test outputs remain in var/. Do not upload that directory wholesale.
