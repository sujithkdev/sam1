# Evaluation workspace

No real malware-detection accuracy result is established by this directory.

- [Metric evaluator and input contract](phase7-evaluation.md)
- [Dataset integrity and replay tooling](phase9-dataset-evaluation.md)
- [Proposed experimental design](../publication/IEEE_PUBLICATION_AND_MALWARE_EVALUATION_PLAN.md#9-experimental-design)
- [Claim evidence requirements](../publication/CLAIMS.md)

Before held-out evaluation, freeze the protocol, scenario eligibility, independent
labels, alert matching, splits, exclusions and configurations. Compare rules-only,
the supported full system, ancestry/temporal ablations and an external baseline.
Verify switches affect their intended execution paths.

Keep private raw captures under a controlled evidence location, not committed
here. Use tools/phase9_dataset.py to freeze/verify eligible manifests and
tools/phase7_evaluate.py for the documented metric contract. Synthetic fixtures
remain labelled synthetic and are not substituted for live results.
