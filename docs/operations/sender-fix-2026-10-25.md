# Telemetry route starvation fix

## Confirmed source defect

Previously Spool.peek always selected the route of the oldest unacknowledged
record. If that route returned a persistent retryable error, every sender cycle
selected it again. Other routes could never progress. A large backlog on that
route also delayed other telemetry even when deliveries succeeded.

The sender now rotates across queued routes. FIFO order is retained within each
route. Failed records remain on disk and are retried on later cycles; successful
routes progress independently. Transport status records the attempted route.
The displayed latest transport result describes that attempt, not every route.
Queue depth/age and rejection counts still need to be inspected.

Tests cover a file route returning 503 while process delivery succeeds, subsequent
recovery of the file route, and fairness with more than two batches on one route.
Existing lost-response, restart, invalid-acknowledgment and duplicate tests remain.

This is a verified code-level cause of apparent stalled delivery, not a confirmed
diagnosis of the user's live VM incident. A dead SSH tunnel, server-wide outage,
collector failure or insufficient throughput still needs separate diagnosis.

## Update the Windows lab agent

1. Stop the agent normally (Ctrl+C in its existing console). Keep its startup
   configuration and credentials. Do not delete outbox.db or its companion files.
2. Preserve a copy of the old endpoint directory for rollback.
3. Copy the complete endpoint directory from the new agent package over the
   deployed endpoint directory. Do not replace the .venv or private runtime data.
4. Restart with the same existing command and environment. Keep the existing SSH
   tunnel running if EDR_SERVER_URL uses loopback HTTP. No re-enrollment is needed.
5. Inspect Transport log entries and read-only queue diagnostics. During normal
   service, acknowledgments should advance as new events are generated and an
   outage backlog should drain. An empty queue can legitimately be idle.
6. Launch Notepad once in the guest and verify its collected event on the server.
   Process polling reports new processes, not a repeated copy of every running
   process. Silence between new observations is not proof of failure.

If stopping persists, provide the final 30 agent log lines and corresponding
server errors with secrets removed, plus before/after lab_status.py reports from
verification-workflow.md. Do not raise the timeout or clear evidence to mask it.

This package is built locally; it is not automatically deployed or uploaded.
