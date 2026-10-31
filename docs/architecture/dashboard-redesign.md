# Investigation console redesign — 2026-10-24

## Delivered

The existing Flask and vanilla JavaScript interface now has Overview, Alerts,
Endpoints, Rules and System Health navigation. No frontend framework or CDN is
required. Data comes from authenticated APIs; the shipped UI contains no seeded
alerts, sample counts or fake collection status.

- Server-side alert search, severity/endpoint/status filtering, bounded pagination
  and 1-hour/24-hour/7-day/30-day windows.
- Alert evidence: recorded reason, matched rule metadata when available, command
  line, source identity, observed bounded ancestry, three separately labelled
  timestamps, raw evidence and assessment.
- Persistent alert triage: open, acknowledged, investigating, resolved and false
  positive. Decisions and notes have a per-alert history and administrative audit.
  Optimistic versions reject conflicting analyst updates (409). This is an analyst
  workflow, not automatic suppression, retraining or independent ground truth.
- Endpoint inventory includes enrolled-but-never-connected agents, last heartbeat,
  last telemetry receipt, retained event count, agent version and reported collector
  health. Missing/stale health is unknown. Quiet telemetry is not automatically loss.
- Commands target the selected endpoint. Queue/result history distinguishes pending,
  leased, expired and returned results; leased does not establish running execution.
  Recognized error results are labelled failed; other returned results require review.
- Separate new-enrollment and rotation flows. Rotation requires typing the exact
  endpoint identity; accidental enroll-over-existing is rejected. Old API/CLI
  enrollment semantics are retained for compatibility.
- Credential, identity and evidence DOM state clears on logout/session expiry.
  Abort controllers and session generations reject late responses. Logout clears
  local data immediately and reports if server revocation cannot be confirmed.
- Refresh, timeout/retry, stale-data messages, keyboard focus, narrow-screen layout
  and explicit no-alerts-does-not-mean-safe notices.

## Storage and compatibility

Startup adds alert_triage and alert_history tables and supporting indexes without
rewriting existing evidence. Back up the database before upgrading. SQLite backups
include the new tables. History shown per alert is the latest 100 decisions;
endpoint inventory is capped at 1,000 and command history at 30. This is a
single-server interface, not a fleet-scale performance claim. Existing alert and
agent endpoints remain available. The Rules view is the loaded Sigma subset only,
not an inventory of every heuristic. Unknown collector fields stay explicitly
unknown; full ancestry cannot be recovered when it was not collected or was evicted.

## Verification

- 186 Python regression tests passed with a fresh workspace basetemp. An earlier
  suite run hit Windows permissions on the existing pytest temporary directory;
  no product assertions failed in that run, and the rerun completed successfully.
- Focused API tests cover authorization, CSRF, SQL-like search text, pagination
  bounds, triage conflict/history/audit, enrollment versus rotation, invalidated
  credentials and empty metrics/unknown collection.
- Node session regression checks pass: immediate logout cleanup, expired-session
  cleanup, late-response rejection and original logout CSRF preservation.
- JavaScript syntax and Ruff checks pass. Existing inactive uba.py has a pre-existing
  invalid-escape SyntaxWarning in the package test.
- Browser checked login, overview, alert investigation, persisted decision history,
  endpoint missing-collector state, rules, logout and empty sensitive DOM content.
  Desktop and 390-pixel narrow viewport inspected. No browser console errors recorded.
- Browser fixtures exist only in var/ui-preview, explicitly labelled SYNTHETIC UI
  TEST; no commands or malware were executed. They are excluded from source packages.

## Install on the existing Kali server without Docker

1. Stop the server normally. Preserve the current code and make an offline backup
   of its var/server directory (or the configured EDR_DATA_DIR), including SQLite
   sidecar files if present. Do not remove configuration or credentials.
2. Extract the new server.zip into a separate directory. Copy your existing private
   configuration and state into the corresponding location, or point EDR_DATA_DIR
   at the existing backed-up state. Retain a rollback copy of the old source.
3. Use Python 3.12 and the packaged requirements/server.lock as before.
4. Start with the existing environment and `.venv/bin/python manage.py serve`.
   Do not run init, create replacement users or re-enroll existing agents just to
   upgrade the UI. Schema additions run at application startup.
5. Hard-refresh the browser. Verify existing endpoints and alerts, then test an
   analyst decision. The endpoint agent does not need an upgrade for these UI changes.

## Still outside this change

Real Windows collection/recovery experiments, independently labelled attack/benign
trials, external-tool comparisons, statistical evaluation, long-duration production
qualification and independent security review remain pending. This redesign does
not establish malware accuracy, publication readiness or a production certification.
