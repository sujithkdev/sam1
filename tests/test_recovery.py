import json
import time
import pytest

from server.core import detector, graph, recovery, temporal
from server.database.storage import _conn
from server.ingestion import accept, process_one


def sample(i):
    return dict(system_id='test-host', event_id=f'recovery-event-{i:016}', event='file_event',
                process='writer', process_guid='writer-guid', time=1000+i, action='modify',
                file_path=f'C:/docs/{i}.locked')


def test_restart_mid_window_matches_uninterrupted_and_no_side_effects(monkeypatch):
    for i in range(4):
        accept([sample(i)])
        assert process_one()
    before = _conn().execute('SELECT COUNT(*) FROM alerts').fetchone()[0]
    temporal._windows.clear()
    monkeypatch.setattr(detector, '_emit', lambda _: pytest.fail('Replay emitted alert'))
    recovery.restore(detector._file_rules)
    assert _conn().execute('SELECT COUNT(*) FROM alerts').fetchone()[0] == before
    assert _conn().execute('SELECT COUNT(*) FROM commands').fetchone()[0] == 0
    score, _, assessment = temporal.assess(sample(4), detector._file_rules, time.time())
    assert score == 85 and len(assessment['evidence_ids']) == 5
    recovery.restore(detector._file_rules)
    assert temporal.assess(sample(4), detector._file_rules, time.time())[0] == score


def test_rebuild_preserves_late_parent_graph(event):
    child = {**event, 'process_guid': 'child', 'parent_process_guid': 'parent'}
    parent = {**event, 'event_id': 'parent-recovery-000000', 'process_guid': 'parent',
              'parent_process_guid': '', 'parent_create_time': 0}
    accept([child, parent])
    assert process_one() and process_one()
    before = graph.to_json('test-host')
    graph._graphs.clear()
    recovery.restore(detector._file_rules)
    assert graph.to_json('test-host') == before


def test_pending_not_replayed():
    accept([sample(0)])
    recovery.restore(detector._file_rules)
    assert not temporal._windows
    assert process_one()
    assert _conn().execute('SELECT COUNT(*) FROM recovery_journal').fetchone()[0] == 1


def test_rule_mismatch_blocks_readiness(client):
    accept([sample(0)])
    process_one()
    _conn().execute("UPDATE recovery_journal SET rules_hash='other-version'")
    with pytest.raises(RuntimeError, match='mismatch'):
        recovery.restore(detector._file_rules)
    assert client.get('/ready').status_code == 503


def test_legacy_completed_data_is_marked_inferred():
    accept([sample(0)])
    _conn().execute("UPDATE telemetry SET status='done'")
    recovery.restore(detector._file_rules)
    assert recovery.STATE['legacy_inferred'] == 1
    assert temporal._windows


def test_corrupt_journal_fails_closed(client):
    _conn().execute('INSERT INTO recovery_journal(system_id,event_id,payload,received,rules_hash) VALUES(?,?,?,?,?)',
                    ('test-host', 'broken', '{', time.time(), recovery.fingerprint()))
    with pytest.raises(json.JSONDecodeError):
        recovery.restore(detector._file_rules)
    assert client.get('/ready').status_code == 503


def test_backup_restores_in_fresh_process(tmp_path):
    import os
    import sqlite3
    import subprocess
    import sys
    from pathlib import Path
    accept([sample(0)])
    assert process_one()
    target = sqlite3.connect(tmp_path / 'edr.db')
    try:
        _conn().backup(target)
    finally:
        target.close()
    backend = str(Path(__file__).resolve().parents[1] / 'backend')
    code = f"""import sys
sys.path.insert(0, {backend!r})
from server import create_app
app = create_app()
from server.core import temporal, recovery
from server.database.storage import _conn
assert app.test_client().get('/ready').status_code == 200
assert len(temporal._windows) == 1
assert recovery.STATE['replayed'] == 1
assert _conn().execute('SELECT COUNT(*) FROM commands').fetchone()[0] == 0
print('RECOVERY_OK')
"""
    result = subprocess.run([sys.executable, '-c', code], capture_output=True, text=True, timeout=30,
                            env={**os.environ, 'EDR_DATA_DIR': str(tmp_path), 'EDR_BACKGROUND': 'false'})
    assert result.returncode == 0, result.stderr
    assert 'RECOVERY_OK' in result.stdout
