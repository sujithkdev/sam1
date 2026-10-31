import pytest
from spool import Spool
from sysmon_collector import normalize, poll


def record(number=1, kind=1, **fields):
    data = dict(UtcTime='2026-01-01 12:00:00.123', ProcessId='12', ProcessGuid='{process-guid}',
                ParentProcessGuid='{parent-guid}', Image='C:\\Windows\\test.exe',
                ParentImage='C:\\Windows\\parent.exe', ParentProcessId='8')
    data.update(fields)
    return {'Event': {'System': {'EventID': kind, 'EventRecordID': number, 'TimeCreated': {}},
                      'EventData': {'Data': [{'Name': k, '#text': v} for k, v in data.items()]}}}


def reader_for(records):
    def read(xpath='*', reverse=False, count=200):
        selected = records
        if 'EventRecordID>' in xpath:
            cursor = int(xpath.split('EventRecordID>')[1].split(']')[0])
            selected = [r for r in records if r['Event']['System']['EventRecordID'] > cursor]
        elif 'EventRecordID=' in xpath:
            cursor = int(xpath.split('EventRecordID=')[1].split(']')[0])
            selected = [r for r in records if r['Event']['System']['EventRecordID'] == cursor]
        return selected[:count]
    return read


def test_process_source_preserved_through_normalization():
    from server.core.processor import normalize as server_normalize
    route, event = normalize(record(), 'test-host')
    normalized = server_normalize(event)
    assert route == '/events'
    assert normalized['process_guid'] == '{process-guid}'
    assert normalized['parent_process_guid'] == '{parent-guid}'
    assert normalized['parent_exe_path'] == r'C:\Windows\parent.exe'
    assert normalized['time'] == event['time']
    assert normalized['raw_source'] == record()


def test_process_fallback_requires_recent_observed_source():
    from sysmon_collector import process_source_ready
    state = {'state': 'available', 'last_poll': 100, 'observed_event_ids': [1]}
    assert process_source_ready(state, now=110)
    assert not process_source_ready(state, now=120)
    assert not process_source_ready({**state, 'state': 'error'}, now=110)
    assert not process_source_ready({**state, 'observed_event_ids': []}, now=110)


@pytest.mark.parametrize('kind,fields,route', [
    (3, {'DestinationIp': '2001:db8::1', 'DestinationPort': '443'}, '/net_events'),
    (11, {'TargetFilename': 'C:\\test.txt'}, '/file_events'),
    (22, {'QueryName': 'example.test'}, '/etw_events'),
])
def test_supported_routes(kind, fields, route):
    assert normalize(record(kind=kind, **fields), 'test-host')[0] == route


def test_bookmark_survives_restart(tmp_path):
    path = tmp_path / 'outbox.db'
    spool = Spool(path)
    poll(spool, 'host', reader_for([record()]))
    spool.conn.close()
    spool = Spool(path)
    try:
        poll(spool, 'host', reader_for([record(), record(2)]))
        assert spool.stats()['queued'] == 2
        assert spool.source_state('sysmon')['record_id'] == 2
    finally:
        spool.conn.close()


def test_full_spool_does_not_advance_bookmark(tmp_path):
    spool = Spool(tmp_path / 'outbox.db', max_records=1)
    try:
        with pytest.raises(OverflowError):
            poll(spool, 'host', reader_for([record(), record(2)]))
        assert spool.source_state('sysmon') == {}
        assert spool.stats()['queued'] == 0
    finally:
        spool.conn.close()


def test_reset_record_id_does_not_hide_new_event(tmp_path):
    spool = Spool(tmp_path / 'outbox.db')
    try:
        poll(spool, 'host', reader_for([record()]))
        poll(spool, 'host', reader_for([record(UtcTime='2026-01-02 12:00:00')]))
        assert spool.stats()['queued'] == 2
        assert spool.source_state('sysmon')['gaps'] == 1
    finally:
        spool.conn.close()


def test_unsupported_events_advance_with_visible_count(tmp_path):
    spool = Spool(tmp_path / 'outbox.db')
    try:
        poll(spool, 'host', reader_for([record(kind=5)]))
        assert spool.source_state('sysmon')['unsupported'] == 1
        assert spool.source_state('sysmon')['record_id'] == 1
        assert spool.stats()['queued'] == 0
    finally:
        spool.conn.close()


def test_health_is_host_bound_and_visible(client, agent_headers, admin_headers):
    assert client.post('/heartbeat', headers=agent_headers, json={
        'system_id': 'test-host', 'collector_health': {'sysmon': {'state': 'error'}}}).status_code == 200
    entries = client.get('/api/status', headers=admin_headers).json['collector_health']
    assert any(e['system_id'] == 'test-host' and e['sources']['sysmon']['state'] == 'error' for e in entries)
    assert client.post('/heartbeat', headers=agent_headers, json={
        'system_id': 'other', 'collector_health': {}}).status_code == 403
