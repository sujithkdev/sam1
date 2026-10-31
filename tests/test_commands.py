import time

import pytest


def test_command_poll_ownership_and_lease(client, admin_headers, agent_headers):
    from server.auth import enroll_agent
    data = {'system_id': 'test-host', 'action': 'collect_info'}
    result = client.post('/api/command', json=data, headers=admin_headers)
    assert result.status_code == 201
    cid = result.json['id']
    poll = client.get('/commands/test-host', headers=agent_headers)
    assert poll.json['commands'][0]['id'] == cid
    assert poll.json['commands'][0]['expires_at'] > time.time()
    assert client.get('/commands/test-host', headers=agent_headers).json['commands'] == []
    wrong = {'API-Key': enroll_agent('other-host')}
    assert client.post('/commands/result', json={'system_id':'other-host', 'id':cid, 'result':'spoof'}, headers=wrong).status_code == 404
    assert client.post('/commands/result', json={'system_id':'test-host', 'id':cid, 'result':'done'}, headers=agent_headers).status_code == 200


@pytest.mark.parametrize('action,params', [('isolate_network',{}), ('kill_process',{'target':'notepad.exe'}), ('kill_process',{'pid':0,'create_time':1,'sha256':'a'*64}), ([],{})])
def test_unsafe_commands_rejected(client, admin_headers, agent_headers, action, params):
    response = client.post('/api/command', headers=admin_headers, json={'system_id':'test-host', 'action':action, 'params':params})
    assert response.status_code == 400


def test_viewer_cannot_command(client, agent_headers):
    from server.auth import create_user, authenticate
    create_user('viewer', 'long-enough-test-password', 'viewer')
    headers = {'Authorization':'Bearer '+authenticate('viewer','long-enough-test-password')[1]}
    assert client.post('/api/command', json={'system_id':'test-host','action':'collect_info'}, headers=headers).status_code == 403


def test_expired_command_never_delivered(client, agent_headers):
    from server.database.storage import _conn, queue_cmd
    cid = queue_cmd('test-host', 'collect_info')
    _conn().execute('UPDATE commands SET expires_at=1 WHERE command_uuid=?', (cid,))
    assert client.get('/commands/test-host', headers=agent_headers).json['commands'] == []
