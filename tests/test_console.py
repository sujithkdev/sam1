import time

from server.database import storage as db


def seed():
    db._conn().execute("INSERT INTO alerts(system_id,process,risk_level,risk_score,reason,timestamp,event_id) VALUES(?,?,?,?,?,?,?)", ('test-host','cmd.exe','HIGH',70,'Simulation rule',int(time.time()),'event-demo'))
    return db._conn().execute('SELECT MAX(id) FROM alerts').fetchone()[0]


def test_alert_filter_triage_conflict_and_audit(client, admin_headers):
    aid = seed()
    response = client.get('/api/console/alerts?severity=HIGH&q=Simulation&size=1', headers=admin_headers)
    assert response.status_code == 200
    assert response.json['total'] == 1
    assert client.get('/api/console/alerts?q=%27%20OR%201=1', headers=admin_headers).json['total'] == 0
    assert client.get('/api/console/alerts?size=10000', headers=admin_headers).status_code == 400
    path = f'/api/console/alerts/{aid}/triage'
    assert client.post(path, headers=admin_headers, json={'status':'investigating','version':0,'note':'Reviewed evidence'}).status_code == 200
    assert client.post(path, headers=admin_headers, json={'status':'resolved','version':0}).status_code == 409
    data = client.get(f'/api/console/alerts/{aid}', headers=admin_headers).json
    assert data['triage']['version'] == 1
    assert len(data['history']) == 1
    assert data['evidence'] is None
    assert client.get('/api/console/alerts?status=investigating', headers=admin_headers).json['total'] == 1
    assert db._conn().execute("SELECT COUNT(*) FROM audit_log WHERE action='alert_triage'").fetchone()[0] == 1


def test_roles_and_cookie_csrf(client, admin_headers):
    from server.auth import create_user, authenticate
    aid = seed()
    create_user('reader','reader-password-long-enough','viewer')
    headers = {'Authorization':'Bearer '+authenticate('reader','reader-password-long-enough')[1]}
    assert client.get('/api/console/alerts', headers=headers).status_code == 200
    assert client.post(f'/api/console/alerts/{aid}/triage', headers=headers,json={'status':'resolved','version':0}).status_code == 403
    assert client.post('/api/console/credentials', headers=headers,json={'system_id':'new','mode':'enroll'}).status_code == 403
    assert client.get('/api/console/endpoints').status_code == 401
    login = client.post('/auth/login',json={'username':'operator','password':'a-test-password-of-sufficient-length'})
    assert login.status_code == 200
    assert client.post(f'/api/console/alerts/{aid}/triage',json={'status':'resolved','version':0}).status_code == 403
    assert client.post(f'/api/console/alerts/{aid}/triage',headers={'X-CSRF-Token':login.json['csrf']},json={'status':'resolved','version':0}).status_code == 200


def test_enroll_rotate_inventory_and_metrics(client, admin_headers):
    path = '/api/console/credentials'
    first = client.post(path, headers=admin_headers,json={'mode':'enroll','system_id':'new-host'})
    assert first.status_code == 201
    assert client.post(path,headers=admin_headers,json={'mode':'enroll','system_id':'new-host'}).status_code == 409
    assert client.post(path,headers=admin_headers,json={'mode':'rotate','system_id':'new-host'}).status_code == 400
    second = client.post(path,headers=admin_headers,json={'mode':'rotate','system_id':'new-host','confirm':'new-host'})
    assert second.status_code == 201
    assert first.json['token'] != second.json['token']
    assert client.post('/heartbeat',headers={'API-Key':first.json['token']},json={'system_id':'new-host'}).status_code == 401
    item = client.get('/api/console/endpoints',headers=admin_headers).json['endpoints'][0]
    assert item['status'] == 'not connected' and item['health_stale']
    assert item['health'] is None
    summary = client.get('/api/console/summary',headers=admin_headers).json
    assert summary['enrolled'] == 1 and summary['received_events'] == 0
    assert client.get('/api/console/summary?hours=0',headers=admin_headers).status_code == 400
    assert len(client.get('/api/console/rules',headers=admin_headers).json['rules']) == 2
    db.upsert_system({'system_id':'new-host'})
    assert client.get('/api/console/summary',headers=admin_headers).json['online'] == 1
    from server.auth import revoke_agent
    revoke_agent('new-host')
    summary = client.get('/api/console/summary',headers=admin_headers).json
    assert summary['online'] == 0 and summary['enrolled'] == 0
