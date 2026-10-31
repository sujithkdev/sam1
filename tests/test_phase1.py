import pytest


def test_recreated_username_cannot_revive_session():
    from server.auth import create_user, authenticate, delete_user, _decode_jwt
    create_user('recreated', 'long-password-for-testing')
    token = authenticate('recreated', 'long-password-for-testing')[1]
    assert delete_user('recreated')
    create_user('recreated', 'long-password-for-testing')
    with pytest.raises(ValueError):
        _decode_jwt(token)


def test_command_identity_survives_sequence_reset():
    from server.database.storage import _conn, queue_cmd
    first = queue_cmd('host', 'collect_info')
    _conn().execute('DELETE FROM commands')
    _conn().execute("DELETE FROM sqlite_sequence WHERE name='commands'")
    second = queue_cmd('host', 'collect_info')
    assert first != second


def test_distinct_source_events_are_not_suppressed():
    from server.database.storage import save_alert
    alert = dict(system_id='host', process='same.exe', risk_level='HIGH', risk_score=70,
                 reason='same finding', event_id='first-event', pid=42, create_time=1)
    assert save_alert(alert)
    assert not save_alert(alert)
    assert save_alert({**alert, 'event_id': 'second-event', 'create_time': 2})


def test_user_migration_preserves_identity(monkeypatch):
    import sqlite3
    from server import auth
    conn = sqlite3.connect(':memory:', isolation_level=None)
    conn.row_factory = sqlite3.Row
    conn.execute('CREATE TABLE users(username TEXT PRIMARY KEY,password TEXT,role TEXT,created INTEGER,version INTEGER DEFAULT 1)')
    conn.execute("INSERT INTO users VALUES('old','hash','viewer',1,1)")
    monkeypatch.setattr(auth, '_conn', lambda: conn)
    auth.init_auth()
    identity = conn.execute('SELECT user_id FROM users').fetchone()[0]
    auth.init_auth()
    assert conn.execute('SELECT user_id FROM users').fetchone()[0] == identity
    assert len(identity) == 32
    conn.close()


def test_legacy_commands_cancelled_and_migration_repeatable(monkeypatch):
    import sqlite3
    from server.database import storage
    conn = sqlite3.connect(':memory:', isolation_level=None)
    conn.row_factory = sqlite3.Row
    monkeypatch.setattr(storage, '_conn', lambda: conn)
    storage.init_db()
    conn.execute("INSERT INTO commands(system_id,action,created_at,status) VALUES('host','collect_info',1,'leased')")
    storage.init_db()
    row = conn.execute('SELECT * FROM commands').fetchone()
    assert row['status'] == 'cancelled'
    identity = row['command_uuid']
    storage.init_db()
    assert conn.execute('SELECT command_uuid FROM commands').fetchone()[0] == identity
    conn.close()


def test_hash_health_missing_corrupt_and_empty(monkeypatch, tmp_path):
    import sqlite3
    from server.core import hash_db
    path = tmp_path / 'intel.db'
    monkeypatch.setattr(hash_db, 'HASH_DB_FILE', path)
    monkeypatch.setattr(hash_db, '_last_error', None)
    assert hash_db.health_status()['state'] == 'missing'
    assert not path.exists()
    path.write_bytes(b'not a database')
    assert hash_db.health_status()['state'] == 'error'
    path.unlink()
    with sqlite3.connect(path) as conn:
        conn.execute('CREATE TABLE malware_hashes(sha256 TEXT)')
    assert hash_db.health_status()['state'] == 'empty'


def test_status_exposes_intel_health(client, admin_headers):
    response = client.get('/api/status', headers=admin_headers)
    assert response.status_code == 200
    assert response.json['hash_intelligence']['state'] in {'missing', 'empty', 'ready', 'error'}
    assert 'state' in response.json['ioc_intelligence']


def test_hash_path_uses_configured_data_directory():
    from pathlib import Path
    from server.config import DATA_DIR
    from server.core.hash_db import HASH_DB_FILE
    assert HASH_DB_FILE.parent == Path(DATA_DIR)


def test_endpoint_refuses_legacy_command_without_execution(tmp_path):
    from spool import Spool
    spool = Spool(tmp_path / 'spool.db')
    try:
        with pytest.raises(ValueError, match='legacy'):
            spool.execute_once({'id': 1}, lambda _: pytest.fail('must not execute'))
    finally:
        spool.conn.close()
