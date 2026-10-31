from pathlib import Path
import pytest
from server.core import temporal
from server.core.file_behavior import load_rules


@pytest.fixture
def rules():
    temporal._windows.clear()
    return load_rules(Path(__file__).resolve().parents[1] / 'rules/file_behavior.json')


def event(i, timestamp, **extra):
    return dict(system_id='host', event='file_event', event_id=f'event{i:020}', time=timestamp,
                process='same.exe', pid=10, create_time=1, file_path=f'C:/docs/{i}.locked', action='modify', **extra)


def test_delayed_batch_uses_original_time(rules):
    scores = [temporal.assess(event(i, 1000+i*600), rules, 10000)[0] for i in range(5)]
    assert max(scores) == 0


def test_reordering_within_lateness_has_same_final_score(rules):
    for order in ([0,1,2,3,4], [4,1,3,0,2]):
        temporal._windows.clear()
        for i in order:
            result = temporal.assess(event(i, 1000+i*10), rules, 10000)
        assert result[0] == 85
        assert len(result[2]['evidence_ids']) == 5


def test_reused_pid_and_unknown_writer_do_not_merge(rules):
    for i in range(5):
        e = event(i, 1000+i)
        e['create_time'] = i+1
        assert temporal.assess(e, rules, 10000)[0] == 0
    e = event(6, 1006)
    e.pop('create_time')
    assert temporal.assess(e, rules, 10000)[2]['state'] == 'unattributed'


def test_lateness_skew_and_missing_time_visible(rules):
    temporal.assess(event(1, 1000), rules, 1000)
    assert temporal.assess(event(2, 879), rules, 1000)[2]['state'] == 'too_late'
    assert temporal.assess(event(3, 1400), rules, 1000)[2]['state'] == 'future_clock_skew'
    e = event(4, 1000)
    e.pop('time')
    assert temporal.assess(e, rules, 1000)[2]['state'] == 'missing_or_invalid_time'


def test_same_timestamp_network_batch_not_beacon(rules):
    for i in range(5):
        e = event(i, 1000)
        e.update(event='network_connect', remote_ip='8.8.8.8', remote_port=443, is_internal=False)
        assert temporal.assess(e, rules, 10000)[0] == 0


def test_periodic_same_destination_network(rules):
    for i in range(5):
        e = event(i, 1000+i*20)
        e.update(event='network_connect', remote_ip='8.8.8.8', remote_port=443, is_internal=False)
        score, _, _ = temporal.assess(e, rules, 10000)
    assert score == 70


def test_retry_recomputes_without_duplicate_evidence(rules):
    for i in range(5):
        temporal.assess(event(i, 1000+i), rules, 10000)
    score, _, assessment = temporal.assess(event(4, 1004), rules, 10000)
    assert score == 85 and len(assessment['evidence_ids']) == 5


def test_identical_actor_names_on_other_hosts_are_separate(rules):
    for i in range(5):
        e = event(i, 1000+i)
        e['system_id'] = f'host{i}'
        assert temporal.assess(e, rules, 10000)[0] == 0


def test_evidence_endpoint_requires_authentication(client):
    assert client.get('/api/telemetry/anything?system_id=host').status_code == 401


def test_late_parent_guid_reconciled_without_cycles():
    from server.core import graph
    graph._graphs.clear()
    graph.add_event(dict(system_id='host', pid=2, child='child', event_id='child', process_guid='child', parent_process_guid='parent'))
    assert graph.to_json('host')['edges'] == []
    graph.add_event(dict(system_id='host', pid=1, child='parent', event_id='parent', process_guid='parent'))
    assert graph.to_json('host')['edges'] == [{'source': 'guid:parent', 'target': 'guid:child', 'weight': 1}]


def test_assessment_persisted_for_unknown_actor(client, agent_headers):
    from server.ingestion import process_one
    from server.database.storage import _conn
    e = event(1, 1000)
    e['system_id'] = 'test-host'
    e.pop('create_time')
    assert client.post('/file_events', headers=agent_headers, json={'events': [e]}).status_code == 200
    assert process_one()
    import json
    assessment = json.loads(_conn().execute('SELECT assessment FROM telemetry').fetchone()[0])
    assert assessment['state'] == 'unattributed'
    assert assessment['received_at'] > 0 and assessment['processed_at'] > 0
