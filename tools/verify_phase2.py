"""Validate only the dedicated behedr-phase2 lab; never target production volumes."""
import http.cookiejar
import json
from pathlib import Path
import secrets
import ssl
import subprocess
import time
import urllib.error
import urllib.request

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / 'var/phase2'
COMPOSE = ['docker', 'compose', '--env-file', 'var/phase2/lab.env', '-f', 'deploy/compose.lab.yaml']
results = []


def run(args, input=None, check=True):
    result = subprocess.run(args, input=input, capture_output=True, text=True, cwd=ROOT)
    if check and result.returncode:
        raise RuntimeError('Command failed: ' + ' '.join(args[:4]) + '\n' + result.stderr[-2000:])
    return result


def record(name, detail=True):
    results.append({'check': name, 'result': detail})
    (OUT / 'results.json').write_text(json.dumps(results, indent=2), encoding='utf-8')
    print(name + ': PASS', flush=True)


def py(code):
    return run(COMPOSE + ['exec', '-T', 'server', 'python', '-'], input=code).stdout


def main():
    run(COMPOSE + ['config', '--quiet'])
    record('compose_valid')
    probe = (ROOT / 'tools/phase2_probe.py').read_text()
    record('container_probe', json.loads(py(probe)))
    for _ in range(30):
        copied = run(COMPOSE + ['cp', 'proxy:/data/caddy/pki/authorities/local/root.crt',
                                str(OUT / 'root.crt')], check=False)
        if copied.returncode == 0:
            break
        time.sleep(1)
    else:
        raise RuntimeError('Proxy CA not available; start the lab stack first')
    ctx = ssl.create_default_context(cafile=str(OUT / 'root.crt'))
    opener = urllib.request.build_opener(urllib.request.HTTPSHandler(context=ctx),
                                        urllib.request.HTTPCookieProcessor(http.cookiejar.CookieJar()))

    def request(path, data=None, headers=None, expected=200):
        req = urllib.request.Request('https://localhost:8443' + path,
              data=json.dumps(data).encode() if data is not None else None,
              headers={'Content-Type': 'application/json', **(headers or {})})
        try:
            response = opener.open(req, timeout=10)
        except urllib.error.HTTPError as exc:
            response = exc
        assert response.code == expected, (path, response.code, expected)
        body = json.load(response)
        return body, response.headers

    request('/ready')
    record('https_with_explicit_ca_and_hostname_validation')
    request('/api/status', expected=401)
    request('/api/operations', expected=401)
    record('anonymous_status_denied')
    password = secrets.token_urlsafe(32)
    username = 'lab-' + secrets.token_hex(4)
    code = "import sys; sys.path.insert(0,'/app/backend')\nfrom server.auth import create_user\n"
    code += f"assert create_user({username!r}, {password!r}, 'admin')\n"
    py(code)
    body, headers = request('/auth/login', {'username': username, 'password': password})
    cookie = headers.get('Set-Cookie', '')
    assert all(flag in cookie for flag in ('Secure', 'HttpOnly', 'SameSite=Strict'))
    request('/api/status')
    record('login_secure_cookie_and_authenticated_status')
    operations, _ = request('/api/operations')
    assert operations['worker']['enabled'] and operations['worker']['healthy']
    assert operations['storage']['available']
    record('authenticated_operational_health_and_worker_liveness')
    retention_output = py((ROOT / 'tools/phase8_container_probe.py').read_text())
    retention_result = next(line.split('=', 1)[1] for line in retention_output.splitlines()
                            if line.startswith('RETENTION_RESULT='))
    record('isolated_container_retention_checkpoint_and_retry', json.loads(retention_result))
    request('/api/agents/enroll', {'system_id': 'phase2-inert'}, expected=403)
    token, _ = request('/api/agents/enroll', {'system_id': 'phase2-inert'},
                       {'X-CSRF-Token': body['csrf']}, expected=201)
    record('csrf_and_agent_enrollment')
    event_id = secrets.token_hex(16)
    event = {'system_id': 'phase2-inert', 'event': 'file_event', 'event_id': event_id,
             'file_path': 'C:/phase2/inert.txt', 'process': 'unknown', 'action': 'modify'}
    for _ in range(2):
        request('/file_events', {'events': [event]}, {'API-Key': token['token']})
    count_code = "import sqlite3\nc=sqlite3.connect('/app/var/server/edr.db')\n"
    count_code += f"print(c.execute('SELECT COUNT(*) FROM telemetry WHERE event_id=?', ({event_id!r},)).fetchone()[0])\n"
    assert py(count_code).strip() == '1'
    record('https_ingestion_deduplicates_retries')
    # Inert event documents exercise the running worker; no Windows command executes.
    sigma_id = secrets.token_hex(16)
    sigma_event = {'system_id': 'phase2-inert', 'event': 'process_spawn', 'event_id': sigma_id,
                   'parent': 'cmd.exe', 'child': 'vssadmin.exe', 'pid': 60123, 'ppid': 60122,
                   'time': time.time(), 'create_time': time.time(),
                   'exe_path': r'C:\Windows\System32\vssadmin.exe',
                   'cmdline': 'vssadmin delete shadows /all'}
    request('/events', {'events': [sigma_event]}, {'API-Key': token['token']})
    sigma_query = "import sqlite3,json\nc=sqlite3.connect('/app/var/server/edr.db')\n"
    sigma_query += f"r=c.execute('SELECT status,assessment FROM telemetry WHERE event_id=?',({sigma_id!r},)).fetchone()\n"
    sigma_query += "print(json.dumps(list(r)))\n"
    for _ in range(30):
        status, assessment = json.loads(py(sigma_query))
        if status == 'done':
            break
        time.sleep(1)
    assert status == 'done', status
    matches = json.loads(assessment)['sigma']['matches']
    assert len(matches) == 1 and len(matches[0]['sha256']) == 64
    import hashlib
    source = ROOT / 'backend/server/sigma_rules/shadow_deletion.yml'
    assert matches[0]['sha256'] == hashlib.sha256(source.read_bytes()).hexdigest()
    record('sigma_https_worker_evidence_and_packaged_rule_hash')
    run(COMPOSE + ['restart', 'server'])
    for _ in range(30):
        try:
            request('/ready')
            break
        except Exception:
            time.sleep(1)
    else:
        raise AssertionError('Restart readiness timed out')
    request('/api/status')
    assert py(count_code).strip() == '1'
    record('restart_preserves_database_and_session')
    assert json.loads(py(sigma_query))[1] == assessment
    record('sigma_evidence_survives_restart')
    run(COMPOSE + ['up', '-d', '--force-recreate', '--wait', '--wait-timeout', '120', 'server'])
    assert json.loads(py(probe))['marker_survived']
    assert py(count_code).strip() == '1'
    record('container_recreation_preserves_volume')
    backup = '/app/var/server/phase2-backup-' + secrets.token_hex(4) + '.db'
    run(COMPOSE + ['exec', '-T', 'server', 'python', 'manage.py', 'backup', backup])
    # Restore into a new temporary data directory, never over the live database.
    restore = f"""import os, shutil, sqlite3, tempfile, sys
sys.path.insert(0,'/app/backend')
with tempfile.TemporaryDirectory(prefix='phase2-restore-') as target:
    shutil.copyfile({backup!r}, target+'/edr.db')
    os.environ['EDR_DATA_DIR']=target
    os.environ['EDR_BACKGROUND']='false'
    from server import create_app
    app=create_app()
    assert app.test_client().get('/ready').status_code == 200
    c=sqlite3.connect(target+'/edr.db')
    assert c.execute('PRAGMA integrity_check').fetchone()[0]=='ok'
    assert c.execute('SELECT COUNT(*) FROM telemetry WHERE event_id=?',({event_id!r},)).fetchone()[0]==1
    c.close()
print('restore passed')
"""
    py(restore)
    record('online_backup_and_fresh_directory_application_restore')
    bad = run(COMPOSE + ['run', '--rm', '--no-deps', '-e', 'EDR_JWT_SECRET=short',
                         'server', 'python', 'manage.py', 'serve'], check=False)
    assert bad.returncode != 0 and 'random secret' in bad.stderr
    record('invalid_secret_startup_rejected')
    run(COMPOSE + ['exec', '-T', 'server', 'python', '-m', 'pip', 'check'])
    record('container_dependency_consistency')
    run(COMPOSE + ['stop'])
    cid = run(COMPOSE + ['ps', '-a', '-q', 'server']).stdout.strip()
    state = json.loads(run(['docker', 'inspect', '--format', '{{json .State}}', cid]).stdout)
    assert not state['Running'] and state['ExitCode'] == 0, state
    record('graceful_server_shutdown', {'exit_code': state['ExitCode']})


if __name__ == '__main__':
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument('--output', type=Path, default=OUT)
    args = parser.parse_args()
    OUT = args.output.resolve()
    OUT.mkdir(parents=True, exist_ok=True)
    main()
