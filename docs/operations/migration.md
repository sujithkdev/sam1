# Migration from the original folders

The original `edr_clean` and `edr-server` directories were moved intact under `archive/`. Their databases, models, scripts and executable builds are preserved as reference snapshots. Active code was copied from `edr_clean` before refactoring; do not run both implementations against one database.

The active server starts with a new `var/server/edr.db`. Existing JSON users and shared API keys are **not imported**: create fresh users and enroll each endpoint. Do not copy the old default administrator or API key into the new configuration. Model pickle/joblib files are not automatically loaded in the supported configuration.

Storage adds process evidence columns and indexes when initialized. That is not a complete historical data migration contract. Validate an offline copy before attempting to carry over old telemetry. No historical database was modified during this implementation.

The old dashboard, public/shared-key stream, simulations, live database restore, arbitrary playbooks, isolation commands, notification integrations, Wazuh routes and experimental-model APIs are not registered in the active application. Their original implementations remain in the archive. Some inherited helper modules remain in the backend for reference but are not supported public interfaces. The root README and active route registrations define this release's surface.

The Windows agent now requires `EDR_SERVER_URL`, a per-host `EDR_API_KEY`, and matching `EDR_SYSTEM_ID`. Its results include host identity. Deploy server and agent together; the old agent/shared key protocol is incompatible. The old installer, GUI launcher and EXE must not be used for this version.

There is no Git repository in this folder, so changes were not committed and no pull request was created. Review the active files against the archived snapshot, then initialize version control and establish a controlled release process.
