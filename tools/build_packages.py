"""Build separate GitHub-ready source packages without runtime data or Docker."""
import argparse
import hashlib
import json
from pathlib import Path
import shutil
import zipfile

ROOT = Path(__file__).resolve().parents[1]
ALLOWED = {'.py', '.html', '.css', '.js', '.json', '.yaml', '.yml', '.md', '.yar', '.yara'}
IGNORE = '''.venv/
.env
.env.*
!.env.example
__pycache__/
*.py[cod]
var/
*.db
*.db-*
*.log
*.key
*.pem
'''

SERVER_README = r'''# BehEDR Server — Kali/Linux

This folder is a standalone server source package. No Docker is required.
Python 3.12 is the tested interpreter. Windows endpoint files are in the separate
agent package. No credentials, administrator account or database is bundled.

## Install and run (development lab via SSH)

Run from this folder:

```bash
python3.12 -m venv .venv
.venv/bin/python -m pip install -r requirements/server.lock
.venv/bin/python manage.py init
export EDR_ENV=development
export EDR_HOST=127.0.0.1
export EDR_PORT=5000
.venv/bin/python manage.py create-user labadmin
.venv/bin/python manage.py enroll-agent win10-lab
.venv/bin/python manage.py serve
```

Run init only once. Save the enrollment credential privately. Enrolling the
same endpoint again rotates its key. Keep the server window open. Set the three
environment variables again in a new shell. The development server must remain
bound to loopback; connect from Windows using the SSH instructions in agent/README.md
from the separate package. Production requires a properly configured HTTPS proxy.

Dashboard: http://127.0.0.1:5000 on Kali, or through the Windows SSH tunnel.
Kali needs an SSH server reachable from the Windows guest for tunnel access.
Use Ctrl+C to stop. Runtime data defaults to var/server; never upload it to GitHub.

## Files

- manage.py: launcher, users, enrollment, backups and maintenance.
- backend/server/: API, dashboard and detection code (including inactive historical modules).
- rules/: detector configuration; keep beside backend and manage.py.
- requirements/server.lock: pinned server dependencies.
- docs/: operational and implementation limitations.
- MANIFEST.json: packaged file hashes, not a cryptographic publisher signature.

This is a behavior-monitoring research project, not a validated enterprise EDR.
Real Windows detection accuracy and external comparisons remain unmeasured.
Do not enable unsupported ML, automatic containment or legacy integrations.
The root project's source remains authoritative; regenerate packages after edits.
'''

AGENT_README = r'''# BehEDR Agent — Windows 10/11

This standalone source package runs on Windows. The server package runs on Kali/Linux.
No API key or data is bundled. Use Python 3.12 and an Administrator PowerShell for
Windows event collection. Docker is not required.

## Install

From this folder:

```powershell
py -3.12 -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements/endpoint.txt
```

## Connect to the Kali development server

In a separate PowerShell window, replace the username and IP:

```powershell
ssh -N -o ExitOnForwardFailure=yes -L 127.0.0.1:5000:127.0.0.1:5000 kaliuser@KALI_IP
```

Leave that window open. Kali must have its SSH server running. Verify the SSH
host fingerprint on first connection. Do not expose the development HTTP server
directly to the network.

In the agent PowerShell window:

```powershell
$env:EDR_ENV = 'development'
$env:EDR_SERVER_URL = 'http://127.0.0.1:5000'
$env:EDR_SYSTEM_ID = 'win10-lab'
$env:EDR_API_KEY = 'PASTE-KEY-FROM-SERVER-ENROLLMENT'
$env:EDR_AGENT_DATA = 'C:\ProgramData\BehEDR-Lab'
.\.venv\Scripts\python.exe endpoint/agent.py
```

Replace the key privately; never commit it to GitHub. Variables apply only to
this shell. Open http://127.0.0.1:5000 in the Windows browser for the dashboard.
Use Ctrl+C to stop the agent, then the SSH tunnel.

## Sysmon (optional until installed, recommended for event coverage)

Download Sysmon from Microsoft Sysinternals. In Administrator PowerShell install
it using deploy/sysmon-lab.xml; if already installed, update its configuration
instead. See docs/architecture/phase3-sysmon.md. Confirm the Operational log receives events.
Before starting the agent, enable the installed/configured source:

```powershell
$env:EDR_SYSMON = 'true'
$env:EDR_PROCESS_SOURCE = 'sysmon'
```

The agent falls back to polling when appropriate; polling can miss short-lived
processes. Optional YARA dependencies are not installed by this package.

## Harmless test

Start Notepad and create a text file under C:\BehEDRLab. Check actual telemetry,
not merely whether alerts appear. Inside a VMware Windows guest with Sysmon:

```powershell
powershell.exe -NoProfile -ExecutionPolicy Bypass -File tools/phase6_guest_collect.ps1
```

This collects evidence from read-only commands; it does not prove malware accuracy.
Do not run recovery-disabling commands or real malware on the host.

Keep endpoint/ intact: agent.py imports neighboring modules. Runtime credentials,
spool databases and logs must stay private. Regenerate from the main project
after source changes. MANIFEST.json records source hashes, not a publisher signature.
'''


def build(destination, root=ROOT):
    destination = Path(destination)
    destination.mkdir(parents=True, exist_ok=False)
    packages = {'server': [('backend/server', None), ('rules', None),
                           ('manage.py', 'manage.py'), ('requirements/server.lock', None),
                           ('requirements/server.txt', None), ('docs/operations/operations.md', None),
                           ('docs/operations/phase8-operations.md', None), ('docs/architecture/dashboard-redesign.md', None),
                           ('tools/lab_status.py', None), ('docs/operations/verification-workflow.md', None)],
                'agent': [('endpoint', None), ('rules/yara', None), ('requirements/endpoint.txt', None),
                          ('deploy/sysmon-lab.xml', None), ('tools/phase6_guest_collect.ps1', None),
                          ('docs/architecture/phase3-sysmon.md', None), ('tools/lab_status.py', None),
                          ('docs/operations/verification-workflow.md', None)]}
    for name, sources in packages.items():
        target = destination / name
        target.mkdir()
        for relative, renamed in sources:
            source = root / relative
            files = sorted(source.rglob('*')) if source.is_dir() else [source]
            for path in files:
                if not path.is_file() or '__pycache__' in path.parts:
                    continue
                if path.is_symlink() or not path.resolve().is_relative_to(root.resolve()):
                    raise ValueError('Source link escapes package policy')
                if source.is_dir() and path.suffix not in ALLOWED and path.name != 'LICENSE':
                    continue
                dest = target / (renamed if renamed else path.relative_to(root))
                dest.parent.mkdir(parents=True, exist_ok=True)
                shutil.copyfile(path, dest)
        readme = SERVER_README if name == 'server' else AGENT_README.replace('\\\\', '\\')
        (target/'README.md').write_text(readme, encoding='utf-8')
        (target/'.gitignore').write_text(IGNORE, encoding='utf-8')
        manifest = {p.relative_to(target).as_posix(): hashlib.sha256(p.read_bytes()).hexdigest()
                    for p in sorted(target.rglob('*')) if p.is_file()}
        (target/'MANIFEST.json').write_text(json.dumps({'package': name, 'files': manifest}, indent=2), encoding='utf-8')
        with zipfile.ZipFile(destination / (name+'.zip'), 'x', compression=zipfile.ZIP_DEFLATED) as archive:
            for path in sorted(target.rglob('*')):
                if path.is_file():
                    archive.write(path, path.relative_to(destination).as_posix())
    (destination/'README.md').write_text('''# BehEDR split distribution

Upload server/ and agent/ to one new GitHub repository, or put each folder in a
separate repository. Each folder has its own README and dependencies. Attach
server.zip and agent.zip as GitHub Release assets for separate downloads.
Do not upload the original project wholesale: it contains runtime/research data.
Nothing is published automatically. No Docker is required by these packages.
The main source tree remains authoritative; run tools/build_packages.py again
with a fresh output directory after changing it. No project-wide license is
invented here; review ownership/licenses before public distribution.
''', encoding='utf-8')
    return destination


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, default=ROOT/'dist/github-packages')
    args = parser.parse_args()
    print('Created:', build(args.output).resolve())
