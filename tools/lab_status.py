"""Read-only guest diagnostics. Never reads credentials or exports event payloads."""
import argparse
import hashlib
import json
from pathlib import Path
import platform
import sqlite3
import time
from urllib.parse import urlsplit


def inspect_database(path, role):
    result = {}
    with sqlite3.connect(Path(path).resolve().as_uri() + '?mode=ro', uri=True, timeout=3) as conn:
        if role == 'agent':
            result['queued'] = conn.execute("SELECT COUNT(*) FROM outbox WHERE error=''").fetchone()[0]
            result['rejected'] = conn.execute("SELECT COUNT(*) FROM outbox WHERE error!=''").fetchone()[0]
            columns = {r[1] for r in conn.execute('PRAGMA table_info(outbox)')}
            result['queue_age_supported'] = 'enqueued_at' in columns
            if result['queue_age_supported']:
                oldest, unknown = conn.execute("SELECT MIN(enqueued_at),SUM(enqueued_at IS NULL) FROM outbox WHERE error=''").fetchone()
                result['oldest_known_age_seconds'] = max(0, time.time()-oldest) if oldest else None
                result['unknown_enqueue_count'] = unknown or 0
            row = conn.execute("SELECT state FROM source_state WHERE name='transport'").fetchone()
            state = json.loads(row[0]) if row else {}
            result['transport'] = {k:state[k] for k in ('state','observed_at','last_ack_at','last_ack_count','http_status') if k in state}
        else:
            result['telemetry_by_status'] = dict(conn.execute('SELECT status,COUNT(*) FROM telemetry GROUP BY status'))
            result['latest_receipt'] = conn.execute('SELECT MAX(received) FROM telemetry').fetchone()[0]
            result['alerts'] = conn.execute('SELECT COUNT(*) FROM alerts').fetchone()[0]
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--role', choices=['agent','server'], required=True)
    parser.add_argument('--database', type=Path, required=True)
    parser.add_argument('--url', help='Optional existing server origin; no credentials sent')
    parser.add_argument('--ca', help='Private CA certificate for HTTPS')
    args = parser.parse_args()
    root = Path(__file__).resolve().parents[1]
    files = ['endpoint/agent.py','endpoint/spool.py','endpoint/transport.py'] if args.role == 'agent' else ['manage.py','backend/server/ingestion.py','backend/server/core/temporal.py']
    report = dict(observed_at=time.time(), role=args.role, python=platform.python_version(),
                  platform=platform.system(), hashes={name:hashlib.sha256((root/name).read_bytes()).hexdigest() if (root/name).is_file() else None for name in files})
    try:
        report['database'] = inspect_database(args.database, args.role)
    except (sqlite3.Error, OSError, ValueError) as exc:
        report['database'] = {'error_type':type(exc).__name__}
    if args.url:
        import requests
        origin = urlsplit(args.url)
        if (origin.username or origin.password or origin.query or origin.fragment or origin.path not in ('','/')
                or not origin.hostname or not (origin.scheme == 'https' or
                origin.scheme == 'http' and origin.hostname in ('localhost','127.0.0.1'))):
            parser.error('Use HTTPS or existing loopback HTTP origin, without credentials')
        report['probes'] = {}
        for route in ('health','ready'):
            try:
                with requests.get(args.url.rstrip('/')+'/'+route, timeout=5, verify=args.ca or True, allow_redirects=False) as response:
                    report['probes'][route] = {'http_status':response.status_code}
            except requests.RequestException as exc:
                report['probes'][route] = {'error_type':type(exc).__name__}
    print(json.dumps(report, indent=2))


if __name__ == '__main__':
    main()
