# BehEDR research documentation

Start with [current status](CURRENT_STATUS.md) and the
[P0–P9 development roadmap](development/ROADMAP.md). The publication workspace
organizes the work; it does not establish IEEE acceptance or completed evaluation.

## Reading order

1. [Current status and supported capabilities](CURRENT_STATUS.md).
2. [Publication, paper correction and evaluation plan](publication/IEEE_PUBLICATION_AND_MALWARE_EVALUATION_PLAN.md).
3. [Development phases and exit gates](development/ROADMAP.md).
4. [P1 live transport commands](development/P1_LIVE_TRANSPORT_2026-10-30.md).
5. [P2 Windows collection checklist](development/P2_WINDOWS_TELEMETRY_2026-10-30.md).
6. [Manuscript working outline](publication/MANUSCRIPT.md), [claim register](publication/CLAIMS.md)
   and [reproduction bundle specification](publication/REPRODUCIBILITY.md).

## Directory ownership

[Complete first-party Markdown catalog](CATALOG.md) lists every document in this
workspace, including the preserved baseline verification notes.

| Location | Purpose |
|---|---|
| [publication](publication/README.md) | Research question, manuscript, claims and reproducibility |
| [development](development/ROADMAP.md) | Current P0–P9 gates and guest execution checklists |
| [architecture](architecture/README.md) | Implemented components, data flow and limitations |
| [operations](operations/README.md) | Installation, transport, maintenance and troubleshooting |
| [evaluation](evaluation/README.md) | Protocol, dataset integrity and comparison tooling |
| [evidence](evidence/README.md) | Dated verification records and cleanup evidence |
| [history](history/README.md) | Earlier reviews, plans and implementation-paper draft |
| phase0/, phase1/, r0/ | Preserved baseline archives, manifests and original qualification records |

The legacy baseline directories retain their paths because verification tools
reference them. Their ZIPs, manifests and recorded inventories are historical;
do not regenerate them to hide source changes. Historical phase numbers do not
map one-to-one to the current P0–P9 roadmap.

## Maintenance rules

- Update CURRENT_STATUS.md and the roadmap after a phase gains reviewed evidence.
- Give empirical results a run ID, date, source/configuration identity and evidence link.
- Keep proposals, synthetic regressions, live qualification and measured effectiveness distinct.
- Keep private event payloads, credentials and runtime databases out of public documentation.
- Edit authoritative source, then regenerate dist packages. Do not edit generated copies.
- Preserve historical results; add a new dated report rather than rewriting an old outcome.

[Relocation manifest](relocation-2026-10-30.json) maps the previous paths to this
layout. Markdown bundled in third-party repositories, virtual environments,
historical releases and generated packages remains with its owning artifact.

## Reorganization verification

- 34 existing documents/sidecars relocated with a recorded mapping.
- Root README and all docs Markdown checked: zero missing local file-link targets.
- Phase 0 and Phase 1 baseline ZIP checksums and every member hash verified.
- Standalone server/agent package regression passed (49.05 seconds); existing
  inactive uba.py docstring escape warning remains. JUnit: var/docs-layout-check-20261030.xml.
- Package selection and source-inventory tools updated for nested documentation.
- No detector, agent collection or server runtime behavior changed by this work.

The catalog is maintained alongside new documentation. Reorganization began on
30 October 2026; filenames retain the dates of their original reports.
