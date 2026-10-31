import time
from unittest.mock import Mock

import pytest
from spool import Spool


def test_spool_survives_reopen_and_ack(tmp_path):
    path = tmp_path / 'spool.db'
    first = Spool(path)
    identity = first.put('/dll_events', {'event':'dll_load'})
    first.conn.close()
    second = Spool(path)
    route, events = second.peek()
    assert route == '/dll_events' and events[0]['event_id'] == identity
    second.acknowledge([identity])
    assert second.peek() == (None, [])
    second.conn.close()


def test_command_executes_once_across_restart(tmp_path):
    path = tmp_path / 'spool.db'
    spool = Spool(path)
    execute = Mock(return_value={'status':'done'})
    cmd = {'id':'a'*32, 'expires_at':time.time()+100}
    spool.execute_once(cmd, execute)
    spool.conn.close()
    spool = Spool(path)
    assert spool.execute_once(cmd, execute) == {'status':'done'}
    assert execute.call_count == 1
    assert spool.pending_results() == [('a'*32, {'status':'done'})]
    spool.acknowledge_result('a'*32)
    assert spool.pending_results() == []
    spool.conn.close()


def test_spool_capacity_and_rejected_record(tmp_path):
    spool = Spool(tmp_path / 'spool.db', max_records=1)
    identity = spool.put('/events', {'test':1})
    with pytest.raises(OverflowError):
        spool.put('/events', {'test':2})
    spool.reject([identity], 'invalid')
    assert spool.stats() == {'queued':0, 'rejected':1}
    assert spool.peek() == (None, [])
    spool.conn.close()


def test_kill_refuses_reused_pid(monkeypatch):
    import response
    process = Mock()
    process.name.return_value = 'test.exe'
    process.create_time.return_value = 20
    monkeypatch.setattr(response.psutil, 'Process', lambda _: process)
    with pytest.raises(ValueError, match='reused'):
        response.execute({'action':'kill_process','params':{'pid':1234567,'create_time':10,'sha256':'a'*64}})
    process.kill.assert_not_called()


def test_kill_checks_hash(monkeypatch, tmp_path):
    import response
    executable = tmp_path / 'test.bin'
    executable.write_bytes(b'inert test data')
    process = Mock()
    process.name.return_value = 'test.exe'
    process.create_time.return_value = 20
    process.exe.return_value = str(executable)
    monkeypatch.setattr(response.psutil, 'Process', lambda _: process)
    with pytest.raises(ValueError, match='identity'):
        response.execute({'action':'kill_process','params':{'pid':1234567,'create_time':20,'sha256':'a'*64}})
    process.kill.assert_not_called()


def test_eventlog_xml():
    from eventlog import parse_xml
    import etw_consumer
    xml = '''<Events><Event xmlns="http://schemas.microsoft.com/win/2004/08/events/event"><System><EventID>4688</EventID><EventRecordID>42</EventRecordID><Execution ProcessID="100"/><TimeCreated SystemTime="2026-01-01T00:00:00.000Z"/></System><EventData><Data Name="NewProcessId">0x100</Data><Data Name="NewProcessName">C:\\Windows\\test.exe</Data><Data Name="CommandLine">test &amp; argument</Data></EventData></Event></Events>'''
    record = parse_xml(xml)[0]
    assert record['Event']['System']['EventRecordID'] == 42
    event = etw_consumer._parse_evtlog_record(record)
    assert event['pid'] == 256 and event['cmdline'] == 'test & argument'


def test_no_entity_expansion():
    from eventlog import parse_xml
    with pytest.raises(ValueError):
        parse_xml('<!DOCTYPE test><Events/>')
