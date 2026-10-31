"""Investigation views. Metrics describe observed records, never protection guarantees."""
import hashlib
import json
import secrets
import time

from flask import Blueprint, g, jsonify, request
from server import auth
from server.config import OFFLINE_THRESHOLD
from server.database import storage as db

console_bp = Blueprint('console', __name__)
STATES = ('open', 'acknowledged', 'investigating', 'resolved', 'false_positive')


def init_console():
    db._conn().executescript('''
        CREATE TABLE IF NOT EXISTS alert_triage (
            alert_id INTEGER PRIMARY KEY, status TEXT NOT NULL, version INTEGER NOT NULL,
            updated REAL NOT NULL, username TEXT NOT NULL);
        CREATE TABLE IF NOT EXISTS alert_history (
            id INTEGER PRIMARY KEY AUTOINCREMENT, alert_id INTEGER NOT NULL,
            status TEXT NOT NULL, note TEXT NOT NULL, username TEXT NOT NULL, timestamp REAL NOT NULL);
        CREATE INDEX IF NOT EXISTS alert_history_id ON alert_history(alert_id,id);
        CREATE INDEX IF NOT EXISTS telemetry_host_received ON telemetry(system_id,received);
        CREATE INDEX IF NOT EXISTS telemetry_received ON telemetry(received);
    ''')


def hours():
    value = int(request.args.get('hours', 24))
    if value not in (1, 24, 168, 720):
        raise ValueError('Choose 1, 24, 168 or 720 hours')
    return value


@console_bp.get('/api/console/summary')
@auth.require_jwt()
def summary():
    from server.ingestion import backlog, worker_health
    window = hours()
    now = time.time()
    c = db._conn()
    cutoff = now - window * 3600
    events = c.execute('SELECT COUNT(*),MAX(received) FROM telemetry WHERE received>=?', (cutoff,)).fetchone()
    alerts = c.execute('SELECT COUNT(*) FROM alerts WHERE timestamp>=?', (cutoff,)).fetchone()[0]
    return jsonify(hours=window, generated_at=now, received_events=events[0], last_received=events[1],
                   recorded_alerts=alerts, backlog=backlog(), worker=worker_health(),
                   online=c.execute('SELECT COUNT(*) FROM systems s JOIN agent_credentials a ON a.system_id=s.system_id WHERE a.revoked=0 AND s.last_seen>=?', (now-OFFLINE_THRESHOLD,)).fetchone()[0],
                   enrolled=c.execute('SELECT COUNT(*) FROM agent_credentials WHERE revoked=0').fetchone()[0],
                   definitions={'received_events': 'Retained telemetry received by server within selected window',
                                'recorded_alerts': 'Retained alerts by recorded timestamp; not confirmed malware',
                                'online': 'Recent heartbeat/registration; not proof of complete collection'})


@console_bp.get('/api/console/alerts')
@auth.require_jwt()
def alerts():
    page, size = int(request.args.get('page', 1)), int(request.args.get('size', 25))
    if not 1 <= page <= 100000 or not 1 <= size <= 100:
        raise ValueError('Invalid pagination')
    where, args = ['a.timestamp>=?'], [time.time()-hours()*3600]
    for key, column in (('severity', 'a.risk_level'), ('system_id', 'a.system_id'), ('status', "COALESCE(t.status,'open')")):
        value = request.args.get(key, '')
        if value:
            if len(value) > 128 or (key == 'status' and value not in STATES):
                raise ValueError('Invalid filter')
            where.append(column+'=?')
            args.append(value)
    query = request.args.get('q', '').strip()
    if len(query) > 200:
        raise ValueError('Search exceeds 200 characters')
    if query:
        where.append('(instr(lower(a.reason),lower(?))>0 OR instr(lower(a.process),lower(?))>0)')
        args.extend([query, query])
    source = ' FROM alerts a LEFT JOIN alert_triage t ON t.alert_id=a.id WHERE '+' AND '.join(where)
    c = db._conn()
    total = c.execute('SELECT COUNT(*)'+source, args).fetchone()[0]
    rows = c.execute("SELECT a.*,COALESCE(t.status,'open') triage_status,COALESCE(t.version,0) version"+source+
                     ' ORDER BY a.timestamp DESC,a.id DESC LIMIT ? OFFSET ?', [*args, size, (page-1)*size])
    return jsonify(alerts=[dict(r) for r in rows], total=total, page=page, size=size)


@console_bp.get('/api/console/alerts/<int:alert_id>')
@auth.require_jwt()
def detail(alert_id):
    alert = db.get_alert_by_id(alert_id)
    if not alert:
        return jsonify(error='Alert not found'), 404
    c = db._conn()
    row = c.execute('SELECT payload,assessment,received,status FROM telemetry WHERE system_id=? AND event_id=?',
                    (alert['system_id'], alert['event_id'])).fetchone()
    triage = c.execute('SELECT * FROM alert_triage WHERE alert_id=?', (alert_id,)).fetchone()
    history = [dict(r) for r in c.execute('SELECT * FROM alert_history WHERE alert_id=? ORDER BY id DESC LIMIT 100', (alert_id,))]
    evidence = json.loads(row['payload']) if row else None
    from server.core.graph import to_json
    from server.core.temporal import instance
    graph = to_json(alert['system_id'])
    nodes = {n['id']: n for n in graph['nodes']}
    identity = instance(evidence) if evidence else None
    ancestry, visited = [], set()
    while identity in nodes and identity not in visited and len(ancestry) < 32:
        visited.add(identity)
        ancestry.append(nodes[identity])
        identity = nodes[identity].get('parent_identity')
    return jsonify(alert=alert, triage=dict(triage) if triage else {'status': 'open', 'version': 0}, history=history,
                   evidence=evidence, ancestry=list(reversed(ancestry)),
                   ancestry_scope='Observed bounded process graph; missing or evicted ancestors are not inferred',
                   assessment=json.loads(row['assessment']) if row else None,
                   received=row['received'] if row else None)


@console_bp.post('/api/console/alerts/<int:alert_id>/triage')
@auth.require_jwt('analyst')
def triage(alert_id):
    data = request.get_json()
    state, note, version = data.get('status'), data.get('note', ''), data.get('version')
    if state not in STATES or not isinstance(note, str) or len(note) > 2000 or type(version) is not int:
        raise ValueError('Invalid triage fields')
    with db._write_lock:
        c = db._conn()
        c.execute('BEGIN IMMEDIATE')
        try:
            if not db.get_alert_by_id(alert_id):
                c.rollback()
                return jsonify(error='Alert not found'), 404
            old = c.execute('SELECT version FROM alert_triage WHERE alert_id=?', (alert_id,)).fetchone()
            if version != (old[0] if old else 0):
                c.rollback()
                return jsonify(error='Another analyst updated this alert. Reopen it before saving.'), 409
            now = time.time()
            c.execute('INSERT INTO alert_triage VALUES(?,?,?,?,?) ON CONFLICT(alert_id) DO UPDATE SET status=excluded.status,version=excluded.version,updated=excluded.updated,username=excluded.username',
                      (alert_id, state, version+1, now, g.user))
            c.execute('INSERT INTO alert_history(alert_id,status,note,username,timestamp) VALUES(?,?,?,?,?)', (alert_id, state, note, g.user, now))
            c.execute('INSERT INTO audit_log(username,action,detail,ip,timestamp) VALUES(?,?,?,?,?)', (g.user, 'alert_triage', f'{alert_id}:{state}', request.remote_addr, now))
            c.commit()
        except Exception:
            c.rollback()
            raise
    return jsonify(status=state, version=version+1)


@console_bp.get('/api/console/endpoints')
@auth.require_jwt()
def endpoints():
    rows = db._conn().execute('''SELECT a.system_id,a.revoked,s.hostname,s.agent_ver,s.last_seen,s.platform,
        h.payload health,h.received health_received,t.last_event,t.event_count,t.pending,t.failed,t.oldest_pending
        FROM agent_credentials a LEFT JOIN systems s ON s.system_id=a.system_id
        LEFT JOIN collector_health h ON h.system_id=a.system_id
        LEFT JOIN (SELECT system_id,MAX(received) last_event,COUNT(*) event_count,
        SUM(status='pending') pending,SUM(status='failed') failed,
        MIN(CASE WHEN status='pending' THEN received END) oldest_pending FROM telemetry GROUP BY system_id) t
        ON t.system_id=a.system_id ORDER BY a.system_id LIMIT 1000''')
    result = []
    for row in rows:
        item = dict(row)
        item['health'] = json.loads(item['health']) if item['health'] else None
        item['status'] = ('revoked' if item['revoked'] else 'not connected' if not item['last_seen'] else
                          'online' if item['last_seen'] >= time.time()-OFFLINE_THRESHOLD else 'offline')
        item['health_stale'] = not item['health_received'] or item['health_received'] < time.time()-OFFLINE_THRESHOLD
        item['analysis_pending_age_seconds'] = max(0, time.time()-item['oldest_pending']) if item['oldest_pending'] else None
        result.append(item)
    return jsonify(endpoints=result, limit=1000)


@console_bp.get('/api/console/rules')
@auth.require_jwt()
def rules():
    from server.core.sigma_subset import RULES
    return jsonify(rules=[{k: v for k, v in r.items() if not k.startswith('_')} for r in RULES],
                   scope='Loaded Sigma subset catalog only. Behavioral heuristics are separate; these rules do not prove malicious intent.')


@console_bp.post('/api/console/credentials')
@auth.require_jwt('admin')
def credentials():
    from server.core.processor import valid_system_id
    data = request.get_json()
    sid, mode = data.get('system_id'), data.get('mode')
    if not valid_system_id(sid) or mode not in ('enroll', 'rotate'):
        raise ValueError('Invalid identity or credential operation')
    if mode == 'rotate' and data.get('confirm') != sid:
        raise ValueError('Confirm the exact endpoint identity to rotate')
    token = secrets.token_urlsafe(48)
    with db._write_lock:
        c = db._conn()
        exists = c.execute('SELECT 1 FROM agent_credentials WHERE system_id=?', (sid,)).fetchone()
        if bool(exists) != (mode == 'rotate'):
            return jsonify(error='Identity exists; use Rotate.' if exists else 'Identity not found; use Enroll.'), 409
        c.execute('BEGIN IMMEDIATE')
        try:
            c.execute('INSERT INTO agent_credentials VALUES(?,?,?,0) ON CONFLICT(system_id) DO UPDATE SET token_hash=excluded.token_hash,created=excluded.created,revoked=0',
                      (sid, hashlib.sha256(token.encode()).hexdigest(), int(time.time())))
            c.execute('INSERT INTO audit_log(username,action,detail,ip,timestamp) VALUES(?,?,?,?,?)', (g.user, mode+'_credential', sid, request.remote_addr, int(time.time())))
            c.commit()
        except Exception:
            c.rollback()
            raise
    return jsonify(system_id=sid, token=token), 201
