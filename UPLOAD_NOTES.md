# Source upload — 31 October 2026

Maintained BehEDR source, tests, configuration templates and research documentation.
P0 is deferred; P1/P2 live guest qualification is pending. This is not a validated
malware-accuracy or production release.

Windows entry point: endpoint/agent.py. Kali entry point: manage.py serve.
Follow README.md and docs/operations/verification-workflow.md for configuration.
Keep existing enrollment credentials and runtime queues during updates.

Excluded: private runtime data, credentials, virtual environments, caches,
generated distributions, third-party copies and historical binary archives.
Historical manifests remain documentation; referenced baseline ZIP archives are
retained locally and are not included in this source upload. Baseline verification
requires those original archives; do not recreate them under the same identity.

At upload preparation, endpoint/yara_scanner.py was absent from the working source.
Its optional import paths remain in agent.py. Do not claim this optional scanner
is bundled or qualified. No security protection was disabled to restore it.
