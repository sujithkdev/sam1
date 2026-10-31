# BehEDR

**Start here:** [Documentation index](docs/README.md), [current status](docs/CURRENT_STATUS.md)
and [P0–P9 research development roadmap](docs/development/ROADMAP.md).
Generated packages in `dist/` and older plans are not the authoritative development source.

An endpoint telemetry and behavioral detection project for Windows, with a Python API and browser console. This refactor is a **release candidate for an isolated pilot**, not a certified enterprise EDR or a demonstrated “9/10” production product.

## Layout

```text
backend/server/     API, authentication, storage, detection and dashboard
endpoint/           Windows collectors, persistent outbox and service entry point
rules/              Behavioral YAML rules and optional YARA rule directory
tests/              Isolated API, detection and endpoint regression tests
requirements/       Separate server, endpoint and development dependencies
deploy/             Container, TLS reverse proxy and Compose configuration
tools/              Maintenance tooling
docs/               Publication, development, architecture, operations and evidence
var/                Local runtime data; excluded from source control
archive/            Original edr_clean and edr-server snapshots; not deployed
manage.py           Server launcher and administration CLI
```

## Set up the server

Use Python 3.12. Run commands from the project root.

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements/server.lock
.\.venv\Scripts\python.exe manage.py init
.\.venv\Scripts\python.exe manage.py create-user admin
.\.venv\Scripts\python.exe manage.py serve
```

There is no default administrator or shared agent password. `init` creates `.env` with a random secret and refuses to overwrite an existing file. `create-user` prompts for a password of at least 14 characters.

Production uses HTTPS through a reverse proxy. The Python server binds to loopback by default; production session cookies require HTTPS. For local development only, set `EDR_ENV=development` in `.env` and browse `http://127.0.0.1:5000`. Do not expose that development listener.

For container deployment, configure `.env`, set `EDR_DOMAIN` to your DNS name, and use `docker compose --env-file .env -f deploy/compose.yaml up --build -d`. Create the initial administrator with `docker compose --env-file .env -f deploy/compose.yaml exec server python manage.py create-user admin`. The database lives in the `server-data` volume, not your host `var` directory. See [operations](docs/operations/operations.md) before deployment.

## Enroll an endpoint

Use the administrator console or `python manage.py enroll-agent HOST-ID`. This returns a unique credential once; repeating enrollment rotates it immediately. On the endpoint, set:

```powershell
$env:EDR_SERVER_URL = 'https://your-edr.example.com'
$env:EDR_SYSTEM_ID = 'HOST-ID'
$env:EDR_API_KEY = '<the-enrollment-credential>'
$env:EDR_AGENT_DATA = 'C:\ProgramData\BehEDR'
python -m pip install -r requirements/endpoint.txt
python endpoint/agent.py
```

Use a trusted CA, or set `EDR_TLS_CA_CERT` to your private CA bundle. Certificate validation is always enabled. Protect credentials and the spool directory with Windows ACLs. The console and Windows service use the same agent lifecycle. See [operations](docs/operations/operations.md) for service installation and collection prerequisites.

## Verify

Development-tool descendant monitoring and exact scoped approvals are documented in [development-tool monitoring](docs/architecture/development-tool-monitoring.md). This is observation, not an OS permission sandbox.

```powershell
.\.venv\Scripts\python.exe -m pip install -r requirements/dev.lock
.\.venv\Scripts\python.exe -m pytest -q
.\.venv\Scripts\python.exe -m ruff check backend endpoint manage.py tests
```

Tests use temporary SQLite databases and inert synthetic data. They do not run the endpoint agent, change firewall rules, kill real processes, or send alerts externally. CI defines Windows and Linux runs; local verification does not imply those hosted runs have completed.

Read [implemented changes and limits](docs/architecture/implementation.md) and [migration notes](docs/operations/migration.md). Experimental models, automatic response, network isolation, external notifications, and the old Wazuh bridge are not enabled in this release.
