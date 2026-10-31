import copy
import json
import sqlite3
import time

import pytest

from server.core import detector, graph, recovery, temporal
from server.database.storage import _conn
from server.ingestion import accept, process_one
from server.retention import maintain


def event(i=0):
    return dict(system_id='retention-host', event_id=f'retention-event-{i:016}', event='file_event',
                process='writer', process_guid='writer-guid', time=1000+i, action='modify',
                file_path=f'C:/docs/{i}.txt')


def old_event():
    accept([{**event(), 'process_guid': ''}])
    assert process_one()
    _conn().execute('UPDATE telemetry SET received=?', (time.time()-40*86400,))


def test_checkpoint_prune_restore_and_retry(tmp_path):
    old_event()
    accept([event(1)])
    assert process_one()
    before = copy.deepcopy(temporal._windows)
    result = maintain(30, 1, tmp_path / 'backup.db')
    assert result['deleted_completed_rows'] == 1
    assert _conn().execute('SELECT COUNT(*) FROM recovery_journal').fetchone()[0] == 1
    assert _conn().execute('SELECT COUNT(*) FROM telemetry').fetchone()[0] == 1
    recovery.restore(detector._file_rules)
    assert temporal._windows == before
    accept([event()])
    assert not process_one()
    accept([event(2)])
    assert process_one()
    expected = copy.deepcopy(temporal._windows)
    recovery.restore(detector._file_rules)
    assert temporal._windows == expected
    assert recovery.STATE['replayed'] == 1
    with sqlite3.connect(tmp_path / 'backup.db') as backup:
        assert backup.execute('SELECT COUNT(*) FROM telemetry').fetchone()[0] == 2


def test_failed_retention_transaction_rolls_back(tmp_path):
    old_event()
    _conn().execute("CREATE TRIGGER block_retention BEFORE DELETE ON telemetry BEGIN SELECT RAISE(ABORT,'test failure'); END")
    try:
        with pytest.raises(sqlite3.IntegrityError):
            maintain(30, 1, tmp_path / 'backup.db')
        for table in ('recovery_checkpoint', 'telemetry_tombstones'):
            assert _conn().execute('SELECT COUNT(*) FROM '+table).fetchone()[0] == 0
        assert _conn().execute('SELECT COUNT(*) FROM telemetry').fetchone()[0] == 1
        assert _conn().execute('SELECT COUNT(*) FROM recovery_journal').fetchone()[0] == 1
    finally:
        _conn().execute('DROP TRIGGER block_retention')


def test_alert_host_is_held_and_pending_is_kept(tmp_path):
    old_event()
    _conn().execute("INSERT INTO alerts(system_id,process,risk_level,risk_score,reason,timestamp) VALUES('retention-host','writer','HIGH',70,'test',1)")
    accept([event(1)])
    assert maintain(30, 10, tmp_path / 'backup.db')['deleted_completed_rows'] == 0
    assert _conn().execute('SELECT COUNT(*) FROM telemetry').fetchone()[0] == 2


def test_corrupt_checkpoint_fails_closed(tmp_path):
    old_event()
    maintain(30, 1, tmp_path / 'backup.db')
    _conn().execute("UPDATE recovery_checkpoint SET payload='{}'")
    with pytest.raises(RuntimeError, match='checksum'):
        recovery.restore(detector._file_rules)
    assert recovery.STATE['state'] == 'failed'


def test_existing_backup_is_not_overwritten(tmp_path):
    backup = tmp_path / 'backup.db'
    backup.write_text('preserve')
    with pytest.raises(FileExistsError):
        maintain(30, 1, backup)
    assert backup.read_text() == 'preserve'


def test_graph_checkpoint_roundtrip():
    from server.core import checkpoint
    parent = dict(system_id='g', event_id='p', child='parent', pid=1, process_guid='parent')
    child = {**parent, 'event_id': 'c', 'child': 'child', 'pid': 2,
             'process_guid': 'child', 'parent_process_guid': 'parent'}
    graph.add_event(child)
    graph.add_event(parent)
    expected = graph.to_json('g')
    payload, checksum = checkpoint.capture()
    graph._graphs.clear()
    checkpoint.restore(payload, checksum)
    assert graph.to_json('g') == expected


def test_worker_stall_and_dead_thread(monkeypatch):
    from server import config, ingestion
    monkeypatch.setattr(config, 'BACKGROUND_ENABLED', True)
    class Thread:
        def is_alive(self):
            return True
    monkeypatch.setattr(ingestion, '_thread', Thread())
    monkeypatch.setattr(ingestion, '_worker_state', dict(heartbeat=100, last_error=None))
    assert ingestion.worker_health(now=110)['healthy']
    assert not ingestion.worker_health(now=221)['healthy']
    monkeypatch.setattr(ingestion, '_thread', None)
    assert not ingestion.worker_health(now=110)['healthy']


def test_checkpoint_restores_in_another_process(tmp_path):
    import os
    import subprocess
    import sys
    from pathlib import Path
    old_event()
    accept([event(1)])
    assert process_one()
    maintain(30, 1, tmp_path / 'before.db')
    with sqlite3.connect(tmp_path / 'edr.db') as target:
        _conn().backup(target)
    code = """from server import create_app
from server.core import temporal
from server.ingestion import accept, process_one
app=create_app()
assert len(temporal._windows)==1
assert app.test_client().get('/ready').status_code==200
""" + f"accept([{event()!r}])\nassert not process_one()\n"
    result = subprocess.run([sys.executable, '-c', code], capture_output=True, text=True, timeout=30,
                            env={**os.environ, 'PYTHONPATH': str(Path(__file__).resolve().parents[1]/'backend'),
                                 'EDR_DATA_DIR': str(tmp_path), 'EDR_BACKGROUND': 'false'})
    assert result.returncode == 0, result.stderr


def test_active_temporal_evidence_not_pruned(tmp_path):
    accept([event()])
    assert process_one()
    _conn().execute('UPDATE telemetry SET received=?', (time.time()-40*86400,))
    assert maintain(30, 1, tmp_path / 'backup.db')['deleted_completed_rows'] == 0
    assert _conn().execute('SELECT COUNT(*) FROM telemetry').fetchone()[0] == 1


def test_optional_compaction_and_retired_evidence_status(tmp_path, client, admin_headers):
    old_event()
    result = maintain(30, 1, tmp_path/'before.db', compact=True)
    assert result['compaction'] == 'completed'
    response = client.get('/api/telemetry/'+event()['event_id']+'?system_id=retention-host', headers=admin_headers)
    assert response.status_code == 410
    assert _conn().execute('PRAGMA integrity_check').fetchone()[0] == 'ok'
