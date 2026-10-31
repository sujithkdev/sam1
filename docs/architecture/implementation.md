# Implementation and verification

## Changes

- Established a single active backend/endpoint layout and archived both original implementations.
- Replaced default credentials and the JSON user store with SQLite users, scrypt passwords, verified JWTs, revocation, role checks, HttpOnly cookies and CSRF protection.
- Added per-agent credential enrollment, hashing, rotation, revocation and host binding.
- Added atomic telemetry acceptance, stable-ID deduplication, durable analysis retries and an inspectable failure queue.
- Preserved PID, parent PID, creation time, executable path, user, hash and alert-to-source-event identity.
- Corrected initial alert-rate calculation, parent constraints in exact rules, whitelist bypass and broad development-command suppression. Persisted alerts are returned to subscribers; independent stream cursors replace a shared consuming queue.
- Removed server-side scanning of endpoint-local executable paths. Network/file observations trigger their analysis immediately.
- Replaced process-name graph nodes with process-instance nodes. Missing parent-instance evidence is left unresolved rather than inventing ancestry.
- Restricted commands, added expiration and leases, checked result ownership, and added endpoint execution reservations and durable result acknowledgement.
- Added a disk-backed endpoint outbox, corrected DLL routing, used literal-path signature checking, and removed guessed file-to-process attribution.
- Corrected Windows Event Log XML parsing and record-ID progression; unified service and console lifecycle.
- Replaced the incompatible dashboard with a cookie-authenticated console, safe text rendering, evidence inspection, enrollment and information requests.
- Added production configuration checks, a single-instance Waitress launcher, online SQLite backup, separate dependency sets, container/TLS examples, CI and regression tests.

## Supported scope

This version supports a single-server pilot of telemetry collection, behavioral-rule detection, alert review and constrained manual response. It does not claim validated neural detection, automated containment, complete Windows telemetry, notification delivery, large-fleet scale or high availability. Advanced inherited modules are not evidence that those capabilities work.

## Verification

See `verification.md` for the final local check results. Automated tests use synthetic records and mocked process operations. Passing them demonstrates the checked behavior, not real-world detection accuracy. The supplied CI, container and Windows service configuration still require execution in their target environments.
