# Phase 2 deployment and lab runbook

## Scope

The Docker lab validates the central server only. It does not replace a Windows endpoint VM and does not establish detection accuracy. No malware or live endpoint response is used by the automated verifier.

The production Dockerfile and Compose proxy now pin immutable Python and Caddy digests. Update these deliberately with rebuild and vulnerability review; pinning is reproducibility, not a security guarantee. The lab uses its own project name, network and named volumes. Only `127.0.0.1:8443` is published. The server remains private to Docker. Application code runs as UID 10001 on a read-only root filesystem, with writable data volume, temporary directory, dropped capabilities and no-new-privileges.

## Start and verify

Run from the project root with Docker Desktop's Linux engine running:

```powershell
.\.venv\Scripts\python.exe tools/prepare_phase2.py
docker compose --env-file var/phase2/lab.env -f deploy/compose.lab.yaml config --quiet
docker compose --env-file var/phase2/lab.env -f deploy/compose.lab.yaml up --build -d --wait --wait-timeout 180
.\.venv\Scripts\python.exe tools/verify_phase2.py
```

Do not print full resolved Compose configuration in shared logs: it contains the session secret. `config --quiet` validates without printing it. The generated `var/phase2/lab.env` is local runtime data; restrict access and never publish it. The script preserves it on repeat runs.

The verifier creates a random lab-only administrator and rotates the `phase2-inert` test agent credential. It submits an inert file observation twice, checks database deduplication, restarts/recreates the server, creates an online backup, and restores it into a separate temporary directory. Finally it stops the lab and requires server exit code zero. It does not enroll a real endpoint or execute remote commands. Repeated runs accumulate lab users and backups intentionally; use a fresh separately named environment for independent experiments rather than treating accumulated test data as real telemetry.

Results are saved in `var/phase2/results.json`. A failed check stops execution; earlier PASS records are not evidence that later checks ran. `tools/phase2_probe.py` is executed inside the container by the verifier.

## HTTPS

Caddy issues a localhost certificate using its lab-only internal CA. The verifier copies only the public CA certificate to `var/phase2/root.crt` and trusts it explicitly, with hostname validation enabled. It does not disable verification or add a certificate to the Windows trust store. A browser may show an untrusted issuer until you explicitly trust that lab certificate. Do not reuse the lab CA for production.

For public deployment, use `deploy/compose.yaml`, a real DNS name and production configuration. Public ACME issuance, DNS, inbound firewall rules and certificate renewal are not tested by the localhost lab.

## Persistence, shutdown and backup

```powershell
docker compose --env-file var/phase2/lab.env -f deploy/compose.lab.yaml stop
docker compose --env-file var/phase2/lab.env -f deploy/compose.lab.yaml up -d --wait
```

Stopping retains volumes. Do not use `down -v` on data you need. The server has a 40-second stop grace period; persistent inbox data must survive even when in-memory state does not. This deployment exercise does not implement graph/window reconstruction, which is a later phase.

Backups created by verification remain in the lab server volume. They are not an off-host disaster-recovery strategy. Operational backups must be copied to protected independent storage. Follow Phase 1's restore rules: rotate session secrets and reconcile credentials/commands after restoring old authorization state. The verifier's restore target is never the live database.

## Windows VM setup gate

VMware was subsequently found outside PATH at `C:\Program Files\VMware\VMware Workstation\vmrun.exe`. The user's existing `Windows 10 x64` VM has a verified `BehEDR-phase2-baseline-20261022` snapshot and was started headlessly. It uses NAT, 2 vCPUs and 2 GB RAM. No configuration changes or guest installations were made. Guest login and connectivity validation remain necessary; a snapshot alone is not evidence of guest readiness.

Prepare a disposable Windows VM on a supported hypervisor with a clean snapshot, dedicated lab account, isolated networking and a documented OS build. Avoid personal folders, clipboard sharing and production credentials during behavior evaluation. Size resources according to host capacity and record the actual allocation. For initial benign collection tests, provide a narrowly scoped route to the server; the loopback-only Docker binding deliberately cannot serve a remote VM until a separate reviewed lab network configuration is supplied.

Record VM name, OS/build, virtual CPU/RAM/disk, snapshot ID, network topology, server address and time-sync settings. Confirm server TLS trust and basic agent enrollment before Sysmon integration in Phase 3. Agent reboot/service tests and behavioral emulations remain Windows VM work, not Docker test results.

## Remaining gates

Production DNS/ACME renewal, Windows VM provisioning, controlled network access from that VM, crash-under-load recovery, image vulnerability scanning and long-duration capacity tests are not implied by a successful Docker smoke test. The latter stress/security items belong to subsequent validation phases; Windows lab availability remains a Phase 2 prerequisite for starting live endpoint work.
