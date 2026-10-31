# Research artifact specification

Status: specification only; no publication bundle or independent rerun is claimed.

```text
research-release/
  README.md                 setup, exact commands and limitations
  manifest.json             release, dependency, configuration and artifact digests
  configs/                  reviewed sensor/server/baseline configurations
  scenarios/                definitions and execution records
  labels/                   provenance, split/group IDs and adjudication
  evaluation/               versioned metric and figure generation scripts
  evidence/                 permitted sanitized traces and run summaries
  results/                  generated tables, figures and uncertainty
  limitations.md
  licences-and-provenance.md
```

Create this bundle only from reviewed artifacts. Do not copy the whole project:
.env, enrollment credentials, databases, personal command lines and malware
binaries do not belong in an ordinary public source release. Document redactions
and their effect on reproducibility. Preserve originals securely.

## Release checklist

- [ ] Venue/artifact requirements and permitted revisions established.
- [ ] Source, dependency, rule and configuration identities frozen.
- [ ] P1/P2 live evidence reviewed; remaining limits explicit.
- [ ] Independent labels, grouping/splits and protocol frozen.
- [ ] Baselines and ablations reproducible and fair within stated scope.
- [ ] Tables/figures regenerated from retained evidence.
- [ ] Secrets, private content and licences reviewed.
- [ ] Clean installation and independent rerun recorded.
- [ ] Manuscript claims audited against exact evidence.

Historical baseline archives under docs/phase0 and docs/phase1 stay immutable.
Create a new release identity rather than altering their recorded manifests.
