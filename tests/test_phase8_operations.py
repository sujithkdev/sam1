import time

import pytest

from server import ingestion, operations
from server.database.storage import _conn
from spool import Spool


def test_full_inbox_accepts_duplicate_only(event, monkeypatch):
    monkeypatch.setattr(ingestion, 'MAX_PENDING', 1)
    ingestion.accept([event, event])
    monkeypatch.setattr(operations, 'storage_status', lambda *a: {'available': False})
    assert ingestion.accept([event]) == [event['event_id']]
    with pytest.raises(OverflowError):
        ingestion.accept([event, {**event, 'event_id': 'b'*32}])
    assert _conn().execute('SELECT COUNT(*) FROM telemetry').fetchone()[0] == 1


def test_storage_pressure_rolls_back_batch(event, monkeypatch):
    monkeypatch.setattr(operations, 'storage_status', lambda *a: {'available': False})
    with pytest.raises(OverflowError, match='Storage'):
        ingestion.accept([event])
    assert _conn().execute('SELECT COUNT(*) FROM telemetry').fetchone()[0] == 0


def test_storage_limits_and_probe_failure(monkeypatch):
    from collections import namedtuple
    Usage = namedtuple('Usage', 'total used free')
    monkeypatch.setattr(operations.shutil, 'disk_usage', lambda p: Usage(1000, 990, 10))
    monkeypatch.setattr(operations, 'MIN_FREE_BYTES', 20)
    assert not operations.storage_status()['available']
    monkeypatch.setattr(operations, 'MIN_FREE_BYTES', 0)
    monkeypatch.setattr(operations, 'MAX_DATABASE_BYTES', 1)
    assert 'database_budget_reached' in operations.storage_status()['reasons']
    def fail(path):
        raise OSError('unavailable')
    monkeypatch.setattr(operations.shutil, 'disk_usage', fail)
    assert operations.storage_status()['reasons'] == ['storage_probe_failed']


def test_retention_report_preserves_rows(event):
    ingestion.accept([event])
    _conn().execute("UPDATE telemetry SET received=?,status='done'", (time.time()-40*86400,))
    result = operations.report(30)
    assert result['retention']['old_completed_rows'] == 1
    assert result['retention']['automatic_deletion'] is False
    assert _conn().execute('SELECT COUNT(*) FROM telemetry').fetchone()[0] == 1
    with pytest.raises(ValueError):
        operations.report(0)


def test_operations_requires_auth_and_pressure_readiness(client, admin_headers, monkeypatch):
    assert client.get('/api/operations').status_code == 401
    assert client.get('/api/operations', headers=admin_headers).status_code == 200
    monkeypatch.setattr(operations, 'storage_status', lambda *a: {'available': False})
    assert client.get('/ready').status_code == 503


def test_endpoint_full_duplicate_and_atomic_bookmark(tmp_path):
    spool = Spool(tmp_path / 'outbox.db', max_records=1)
    try:
        event = {'event_id': 'a'*32}
        spool.put('/events', event)
        assert spool.put('/events', event) == event['event_id']
        spool.commit_source('sysmon', {'record_id': 2}, [('/events', event)])
        with pytest.raises(OverflowError):
            spool.commit_source('sysmon', {'record_id': 3}, [('/events', {'event_id': 'b'*32})])
        assert spool.source_state('sysmon')['record_id'] == 2
        assert spool.stats()['queued'] == 1
    finally:
        spool.conn.close()
