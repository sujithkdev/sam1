import pytest


def test_durable_idempotent_ingestion(client, agent_headers, event):
    from server.ingestion import process_one, backlog
    from server.database.storage import get_events, get_alerts
    for _ in range(2):
        response = client.post('/events', json={'events': [event]}, headers=agent_headers)
        assert response.status_code == 200
        assert response.json['accepted'] == [event['event_id']]
    assert backlog() == {'pending': 1}
    assert process_one()
    assert backlog() == {'done': 1}
    assert len(get_events()) == 1
    assert get_events()[0]['exe_path'] == event['exe_path']
    alerts = get_alerts()
    assert alerts, 'First real detection must be persisted'
    assert all(a['event_id'] == event['event_id'] for a in alerts)
    assert not process_one()


@pytest.mark.parametrize('field,value', [('pid','invalid'), ('pid',True), ('time',-1), ('sha256','broken'), ('child',{}), ('event','dll_load')])
def test_bad_events_are_rejected_atomically(client, agent_headers, event, field, value):
    from server.ingestion import backlog
    invalid = {**event, field: value}
    response = client.post('/events', json={'events': [event, invalid]}, headers=agent_headers)
    assert response.status_code == 400
    assert backlog() == {}


def test_same_second_different_pid_survives(event):
    from server.core.processor import normalize
    event.pop('event_id')
    other = {**event, 'pid': event['pid']+1}
    assert normalize(event)['event_id'] != normalize(other)['event_id']


def test_retry_visible_after_failure(monkeypatch, client, agent_headers, event):
    from server import ingestion
    client.post('/events', json=event, headers=agent_headers)
    monkeypatch.setattr(ingestion, 'analyze_telemetry', lambda _: (_ for _ in ()).throw(RuntimeError('failure')))
    ingestion.process_one()
    from server.database.storage import _conn
    row = _conn().execute('SELECT status,attempts,error FROM telemetry').fetchone()
    assert dict(row) == {'status': 'pending', 'attempts': 1, 'error': 'failure'}


def test_rule_requires_parent(monkeypatch, event):
    from server.core import detector
    monkeypatch.setattr(detector, '_chains_rules', [{'name':'strict', 'description':'test', 'pattern':[{'parent':['winword.exe'], 'child':['powershell.exe'], 'cmdline_contains':['-enc']}]}])
    assert detector._l1_chain_rules({**event, 'parent': 'unrelated.exe'}) == []
    assert detector._l1_chain_rules(event)


def test_first_alert_not_a_storm():
    from server.alert_storm_protection import reset_storm, check_alert_storm
    reset_storm()
    assert check_alert_storm('new-host', {}) == (True, '')
