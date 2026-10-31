# Phase 1: security, identities and failure visibility

## Changes

- Users receive an immutable random UUID identity, persisted separately from username. JWTs must carry the matching identity as well as the existing version and role. Recreating a username cannot revive its earlier token. Tokens issued before this migration lack the identity claim and are rejected.
- Commands retain internal SQLite row IDs but expose random UUID identities through queue, polling, history and result APIs. Resetting SQLite sequences cannot collide with retained endpoint execution reservations.
- Existing commands without UUIDs receive identities for history; pending/leased legacy commands are cancelled rather than reissued under new identities. The migration is repeatable after partial completion.
- Endpoint UUID reservations use a separate TEXT-keyed `command_results_v2` table. Old integer results remain preserved in their original table but are not submitted automatically. Integer commands are refused before execution.
- Alert deduplication uses source event identity when supplied. Different source events are preserved even if the process name and reason match. Without event IDs, bounded suppression requires matching PID and positive creation time; completely unattributed records are not silently merged. This may increase alert volume and requires later incident correlation/calibration.
- Hash storage now follows configured `EDR_DATA_DIR`. Importing the hash module no longer creates a database. Missing storage is not silently provisioned during lookup; explicit initialization remains available. Lookup failures are logged, and authenticated `/api/status` reports missing/empty/error/ready hash status and local IOC load status.
- Misleading hash module claims of bundled hundreds of thousands of signatures and automatic daily coverage were removed. Neural models, automatic response and the Wazuh bridge remain unsupported; no active modules were deleted merely because they are experimental.

## Upgrade and recovery

1. Stop command issuance and back up the server database and endpoint spools. Preserve the Phase 0 source archive.
2. Stop server and agents before replacing code. Upgrade them together: integer command protocol compatibility is deliberately not supported by the new endpoint.
3. Start the server to perform additive schema migrations. Usernames, passwords and roles are retained. Existing browser sessions require a new login.
4. Review cancelled legacy commands and any old endpoint result records. An earlier leased command may already have executed: inspect its outcome before manually issuing a new command.
5. Restart upgraded agents and verify enrollment, polling and results using a read-only information request.
6. Provision any reviewed hash database into the configured runtime data directory explicitly. The legacy backend/data database is not silently copied or treated as a validated corpus. A missing/empty feed means no hash coverage.

Restoring a backup can restore revoked users or credentials. Rotate the JWT signing secret after restore and review/revoke restored agent credentials as needed; UUIDs do not invalidate authorization state restored from an older backup. Retain endpoint reservations when restoring server state. Restored commands with the same UUID should return the saved execution outcome, not execute again. Restoring an endpoint spool to an older snapshot can erase reservations and remains an operational hazard: cancel/reconcile outstanding commands before resuming response.

Do not run old code against migrated operational data as a rollback shortcut. Restore a coordinated backup in a stopped environment, rotate sessions, and reconcile commands first. The migrations add columns/indexes without dropping user or command history; repeatability is tested, but power-loss durability of every schema transition has not been independently fault-injected.

## Validation and limits

Three regression tests reproduced failures before modification: username-session revival, integer command collision after sequence reset, and suppression of distinct source events. All three failed on the original implementation.

Additional regressions cover repeatable user migration, legacy command cancellation and migration identity preservation, missing/corrupt/empty intel status, configured intel paths, legacy-command refusal, and authenticated status output. Existing endpoint tests verify execution reservation across spool reopen using UUIDs; existing command tests cover host ownership, leases and expiry.

The first post-fix suite passed 81 tests. Expanded tests caught a read-only SQLite health-check handle left open on Windows; this was corrected using explicit connection closing. The final full suite passed **87 tests in 38.37 seconds**. Ruff checks on backend, endpoint, manage.py and tests passed. Tests used isolated temporary databases and inert/mocked operations; no live commands were issued.

This phase does not add automatic threat-feed refresh, validate an IOC corpus, finish a feed ingestion pipeline, measure detection accuracy, or perform Docker/Windows service deployment. Hash health reports availability/count, not feed freshness or quality. Errors in optional intelligence remain nonfatal to behavioral detection. Telemetry timing, collector bookmarks, graph recovery and source attribution remain later-phase work.
