# Publication claim register

Updated 30 October 2026. Every final claim needs a frozen source/configuration,
evidence reference and scope. No pending row is an achieved result.

| Claim | Current support | Required before publication as a result |
|---|---|---|
| Durable queued delivery and retry | Implementation and synthetic tests | P1 guest counts, failures/restarts and installed identity |
| Fair delivery between routes | Sender implementation and regressions | Deployed fix and controlled live route evidence |
| Windows process collection | Sysmon adapter and polling implementation | P2 independent capture/miss measurements |
| Process-aware temporal correlation | Implemented method and regressions | Precise contract, closest-work review and empirical comparison |
| Improved detection over rules alone | Hypothesis | Matched inputs, baseline, real switches and uncertainty |
| Low benign alert burden | Unmeasured | Benign exposure, alert adjudication and denominators |
| Low end-to-end latency | Unmeasured | Source-to-alert measurement with clock uncertainty |
| Active unsupervised ML | Unsupported current release | Exclude from current-release claims |
| Automatic isolation or Wazuh bridge | Unsupported release capabilities | Exclude from current-release claims |
| Malware-family/zero-day recognition | Not established | Exclude; narrow scope to evaluated behavior |
| Production-qualified protection | Not established | Separate operational/security qualification |

Use the detailed [paper correction table](IEEE_PUBLICATION_AND_MALWARE_EVALUATION_PLAN.md#3-submitted-pdf-correction-plan)
when revising the historical manuscript. Earlier results may be retained only
when their exact implementation and evidence can be substantiated; do not transfer
them to a new release without the relevant rerun.
