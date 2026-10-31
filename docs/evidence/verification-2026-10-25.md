# Verification results - 25 October 2026

## Scope and outcome

Local Windows-host qualification using isolated temporary databases and synthetic
events. No real malware, guest collector execution, production credentials or
live endpoint database was used. No accuracy or production-readiness claim.

Initial full suite: 200 passed, 1 failed, 1 warning (155.14 seconds).
The failure expected connection_error while Windows returned connect_timeout for
a stopped localhost listener. The test now accepts either outage classification
and explicitly requires the queued event to remain before restart.

After that correction and new checks: 21 targeted tests passed, 1 warning (41.22
seconds). This is not a second full-suite run; the 21 include repeated tests.
JUnit evidence: var/latest-verification.xml and var/workflow-verification.xml.
Ruff passed for the inspected transport/configuration/diagnostic/test modules.
JavaScript session test passed logout clearing, expiry clearing, rejection of
late responses and preservation of the original logout CSRF token.

## New verification coverage

- Five synthetic file events produce an evidence-linked alert when attributable
  and matching the configured file rule. The authenticated console returns evidence.
- Ordinary .txt file modifications in the same small workload do not alert.
- Missing writer identity remains unattributed and does not trigger that rule.
- Duplicate submission does not create another analysis job or evidence record.
- Replay preserves alert counts, reconstructs correlation, and issues no commands.
- The real HTTP restart test retains an event after a deliberately lost response,
  survives server and spool reopening, and delivers once after recovery using the
  same enrollment credential. No re-enrollment workaround is needed.
- Read-only diagnostics fail without creating a missing database and do not export
  private event payloads or arbitrary transport-state fields.
- Standalone package smoke tests and SHA256/ZIP integrity checks pass.

## Known warning

An existing invalid escape in an inactive uba.py docstring emits a SyntaxWarning
during package compilation. It did not fail tests. No ML capability was enabled.

## Live deployment status

VMware confirms both Windows 10 and Linux VMs running. Host localhost:5000 refuses
connection. Earlier guest discovery returned Linux 192.168.71.128 and Windows
192.168.71.129; addresses can change. SSH host trust/authenticated guest access is
not established, so these local results do not confirm guest collection/delivery.

Next action: run the read-only commands in verification-workflow.md inside both
guests and compare source hashes, queue progression, health and readiness. Follow
with independently recorded benign process launches and controlled reconnects.

Native HTTPS/systemd/Windows-task prototypes remain unqualified and are not
promoted as the tested installation path by this verification. Existing SSH lab
configuration remains documented. No public release was uploaded.
