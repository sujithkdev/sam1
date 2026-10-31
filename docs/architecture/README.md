# Architecture and implementation

These records describe implementation at their recorded dates. Current capability
limits are in [CURRENT_STATUS](../CURRENT_STATUS.md).

- [Implementation overview](implementation.md)
- [Development-tool observation](development-tool-monitoring.md)
- [Console design](dashboard-redesign.md)
- [Sysmon collection](phase3-sysmon.md)
- [Identity and temporal correlation](phase4-correlation.md)
- [Recovery](phase5-recovery.md)
- [Sigma subset and heuristics](phase6-rules.md)
- [Reference integration and provenance](reference-integration-2026-10-22.md)

Supported conceptual flow: Windows collection → durable endpoint outbox →
authenticated delivery → server inbox/deduplication → asynchronous analysis →
process/rule/temporal evidence → alerts and investigation console. Acceptance
acknowledgment does not mean analysis has completed. Trace the final publication
diagram against the selected frozen source.
