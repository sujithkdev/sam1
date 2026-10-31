# Phase 0 verification — 22 October 2026

## Local results

| Check | Result |
|---|---|
| Existing regression suite | 78 passed in 30.35 seconds |
| Ruff: backend, endpoint, manage.py, tests | All checks passed |
| Ruff: tools/freeze_phase0.py | All checks passed |
| pip check | No broken requirements found |
| Baseline freeze | 100 source files archived |
| Baseline verification | Archive SHA-256, every archived member and current included source matched |

Archive SHA-256: `e8a9b2b652fdcd5a6f24bae07417838ba5aa03e72ac650397f81c211d784390e`.

Commands used from the project root:

```powershell
.\.venv\Scripts\python.exe -m pytest -q -p no:cacheprovider --basetemp=var/phase0-tests-20261022
.\.venv\Scripts\python.exe -m ruff check --no-cache backend endpoint manage.py tests
.\.venv\Scripts\python.exe -m pip check
.\.venv\Scripts\python.exe -m ruff check --no-cache tools/freeze_phase0.py
.\.venv\Scripts\python.exe tools/freeze_phase0.py
.\.venv\Scripts\python.exe tools/freeze_phase0.py --verify
```

The regression command used approved execution because prior sandboxed runs had temporary-directory permission failures. Tests used the existing project virtual environment and isolated temporary databases. No live agent, behavior emulation, process termination, Docker deployment, or external notification was executed.

## Deliverables

- `PLAN.md`: research question, scope, requirements, feature register, issue priorities, evaluation protocol and reproduction instructions.
- `baseline-source.zip` and `baseline-manifest.json`: immutable source snapshot and checksums; no Git commit is claimed.
- `environment.json`: interpreter/platform/package inventory; not a fresh environment installation record.
- `experiment-template.json`: explicit not-run manifest with null measurements.
- `results-template.csv`: header-only results schema; no invented detection metrics.
- `../../tools/freeze_phase0.py`: creation and integrity-check tooling. Phase 0 documentation/output itself is excluded from the source archive to avoid recursion.

## Remaining acceptance gate

**Independent clean-environment reproduction has not been executed.** The current environment passes dependency consistency and regression checks, but this does not prove that a new installation from the lock file succeeds. Follow the clean-environment procedure in PLAN.md and retain that installation/test output before declaring the full reproducibility gate passed.

The local Phase 0 baseline package is complete. Critical security fixes, telemetry improvements, measured detection effectiveness, Docker validation and Windows VM testing remain future phases. `pip check` is dependency consistency checking, not a vulnerability scan; no fresh vulnerability audit was performed in this phase.
