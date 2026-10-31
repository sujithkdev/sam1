"""Synthetic pipeline qualification, not malware accuracy or live collection."""
import json
import time

import pytest

from server.core import detector, graph, recovery, temporal
from server.database.storage import _conn
from server.ingestion import process_one


@pytest.mark.parametrize('case', ['positive', 'benign', 'unknown_writer'])
def test_file_evidence_survives_replay(client, agent_headers, admin_headers, case):
    now = time.time() - 10
    events = []
    for i in range(5):
        event = dict(system_id='test-host', event_id=f'workflow-{case}-{i:016}',
                     event='file_event', time=now+i, process='lab-writer.exe',
                     action='modify', file_path=f'C:/lab/{i}.locked')
        if case != 'unknown_writer':
            event['process_guid'] = 'lab-writer-instance'
        if case == 'benign':
            event['file_path'] = f'C:/lab/{i}.txt'
        events.append(event)
    response = client.post('/file_events', headers=agent_headers, json={'events': events})
    assert response.status_code == 200
    assert set(response.json['accepted']) == {e['event_id'] for e in events}
    for _ in events:
        assert process_one()
    assert not process_one()
    rows = _conn().execute('SELECT event_id,status,assessment FROM telemetry').fetchall()
    assert len(rows) == 5 and all(r['status'] == 'done' for r in rows)
    assessments = {r['event_id']: json.loads(r['assessment']) for r in rows}
    last = assessments[events[-1]['event_id']]
    alerts = _conn().execute('SELECT id FROM alerts').fetchall()
    if case == 'positive':
        assert alerts
        assert set(last['evidence_ids']) == {e['event_id'] for e in events}
        detail = client.get(f"/api/console/alerts/{alerts[-1]['id']}", headers=admin_headers)
        assert detail.status_code == 200 and detail.json['evidence'] is not None
    else:
        assert not alerts
    if case == 'unknown_writer':
        assert last['state'] == 'unattributed' and last['actor'] is None
    # Re-delivery must not insert or analyze a second copy.
    assert client.post('/file_events', headers=agent_headers, json={'events': events}).status_code == 200
    assert not process_one()
    count = len(alerts)
    graph._graphs.clear()
    temporal._windows.clear()
    recovery.restore(detector._file_rules)
    assert _conn().execute('SELECT COUNT(*) FROM alerts').fetchone()[0] == count
    assert _conn().execute('SELECT COUNT(*) FROM telemetry').fetchone()[0] == 5
    assert _conn().execute('SELECT COUNT(*) FROM commands').fetchone()[0] == 0
    assert temporal.assess(events[-1], detector._file_rules, time.time())[0] == (85 if case == 'positive' else 0)
