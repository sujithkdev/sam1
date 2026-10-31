import sqlite3
import time
from concurrent.futures import ThreadPoolExecutor
from unittest.mock import Mock

import pytest


def test_batch_capacity_returns_retry(client, agent_headers, event, monkeypatch):
    from server import ingestion
    monkeypatch.setattr(ingestion, 'MAX_PENDING', 0)
    response = client.post('/events', json=event, headers=agent_headers)
    assert response.status_code == 503 and response.headers['Retry-After'] == '10'
    assert ingestion.backlog() == {}


def test_concurrent_acceptance_and_recovery(event):
    from server.ingestion import accept, backlog
    from server.database.storage import close_thread_connection, _conn
    def send(index):
        try:
            accept([{**event, 'event_id':f'{index:032d}'}])
        finally:
            close_thread_connection()
    with ThreadPoolExecutor(max_workers=8) as workers:
        list(workers.map(send, range(40)))
    assert backlog() == {'pending':40}
    _conn().close()
    from server.database.storage import _local
    _local.conn = None
    assert backlog() == {'pending':40}


def test_graph_does_not_join_same_name_instances(event):
    from server.core import graph
    graph._graphs.clear()
    graph.add_event(event)
    graph.add_event({**event,'event_id':'b'*32,'pid':event['pid']+1})
    result = graph.to_json(event['system_id'])
    assert len(result['nodes']) == 2 and result['edges'] == []
    graph.add_event({**event,'event_id':'c'*32,'pid':event['pid']+2,'ppid':event['pid'], 'parent_create_time':event['create_time']})
    assert len(graph.to_json(event['system_id'])['edges']) == 1


def test_heartbeat_preserves_registration(client, agent_headers):
    from server.database.storage import get_systems
    client.post('/register', headers=agent_headers, json={'system_id':'test-host','hostname':'actual-host','agent_ver':'4.1'})
    client.post('/heartbeat', headers=agent_headers, json={'system_id':'test-host'})
    assert get_systems()[0]['hostname'] == 'actual-host'
    assert get_systems()[0]['agent_ver'] == '4.1'


def test_sse_independent_cursors(client, admin_headers):
    from server.database.storage import save_alert
    aid = save_alert({'system_id':'test-host','process':'test.exe','risk_level':'HIGH','reason':'test','risk_score':80})
    first = client.get('/stream', headers=admin_headers, buffered=False)
    assert f'id: {aid}'.encode() in next(iter(first.response))
    first.close()
    second = client.get('/stream', headers=admin_headers, buffered=False)
    assert f'id: {aid}'.encode() in next(iter(second.response))
    second.close()


def test_attributed_file_events_trigger_without_process_spawn(client, agent_headers):
    from server import ingestion
    from server.database.storage import get_alerts
    events = [{'system_id': 'test-host', 'event': 'file_event', 'event_id': f'file-regression-{i:016}',
               'file_path': f'C:/docs/{i}.locked', 'process': 'writer.exe',
               'process_guid': 'writer-instance', 'time': time.time()} for i in range(5)]
    response = client.post('/file_events', headers=agent_headers, json={'events': events})
    assert response.status_code == 200
    for _ in events:
        assert ingestion.process_one()
    assert get_alerts()[0]['process'] == 'writer.exe'


def test_literal_signature_path(monkeypatch):
    import agent
    import subprocess
    run = Mock(return_value=Mock(returncode=0, stdout='NotSigned'))
    monkeypatch.setattr(subprocess, 'run', run)
    monkeypatch.setattr(agent.os, 'name', 'nt')
    path = "C:\\test'quoted.dll"
    assert agent._is_dll_signed(path) is False
    args, kwargs = run.call_args
    assert path not in args[0][-1]
    assert kwargs['env']['BEHEDR_SIGNATURE_PATH'] == path


def test_wevtutil_uses_xml_and_record_cursor(monkeypatch):
    import etw_consumer
    run = Mock(return_value=Mock(returncode=0, stdout='<Events/>'))
    monkeypatch.setattr(etw_consumer.subprocess, 'run', run)
    assert etw_consumer._wevtutil_query('Security', [4688], 42) == []
    args = run.call_args[0][0]
    assert '/f:xml' in args and any('EventRecordID>42' in arg for arg in args)


def test_configuration_rejects_missing_secret(monkeypatch):
    from server import config
    monkeypatch.setattr(config, 'JWT_SECRET', '')
    with pytest.raises(RuntimeError):
        config.validate_configuration()


def test_single_instance_lock(tmp_path):
    from server.runtime_lock import exclusive_instance
    with exclusive_instance(tmp_path / 'server.lock'):
        with pytest.raises(RuntimeError):
            with exclusive_instance(tmp_path / 'server.lock'):
                pass


def test_backup_preserves_wal_commits(tmp_path, event):
    from server.config import DB_PATH
    from server.ingestion import accept
    accept([event])
    with sqlite3.connect(DB_PATH) as source, sqlite3.connect(tmp_path/'backup.db') as target:
        source.backup(target)
        assert target.execute('PRAGMA integrity_check').fetchone()[0] == 'ok'
        assert target.execute('SELECT event_id FROM telemetry').fetchone()[0] == event['event_id']
