import pytest


def test_no_default_user(client):
    assert client.post('/auth/login', json={'username': 'admin', 'password': 'change-me-now'}).status_code == 401
    assert client.get('/api/status').status_code == 401
    assert client.get('/stream?apikey=123456789').status_code == 401


def test_cookie_csrf_and_logout(client, admin_headers):
    result = client.post('/auth/login', json={'username': 'operator', 'password': 'a-test-password-of-sufficient-length'})
    assert result.status_code == 200
    assert 'HttpOnly' in result.headers['Set-Cookie'] and 'SameSite=Strict' in result.headers['Set-Cookie']
    assert client.post('/auth/logout', json={}).status_code == 403
    assert client.post('/auth/logout', json={}, headers={'X-CSRF-Token': result.json['csrf']}).status_code == 200
    assert client.get('/api/status', headers=admin_headers).status_code == 401


def test_agent_host_binding_and_revocation(client, agent_headers):
    from server.auth import revoke_agent
    assert client.post('/register', headers=agent_headers, json={'system_id': 'another-host'}).status_code == 403
    assert client.get('/commands/another-host', headers=agent_headers).status_code == 403
    assert client.post('/register', headers=agent_headers, json={'system_id': 'test-host'}).status_code == 200
    revoke_agent('test-host')
    assert client.get('/commands/test-host', headers=agent_headers).status_code == 401


def test_rotation_invalidates_old_key(client, agent_headers):
    from server.auth import enroll_agent
    new_key = enroll_agent('test-host')
    assert client.get('/commands/test-host', headers=agent_headers).status_code == 401
    assert client.get('/commands/test-host', headers={'API-Key': new_key}).status_code == 200


def test_deleted_user_token_invalid(client, admin_headers):
    from server.auth import authenticate, create_user, delete_user
    create_user('viewer', 'long-viewer-test-password', 'viewer')
    token = authenticate('viewer', 'long-viewer-test-password')[1]
    assert delete_user('viewer')
    assert client.get('/api/status', headers={'Authorization': 'Bearer ' + token}).status_code == 401
    assert not delete_user('operator')


@pytest.mark.parametrize('payload', [[], None, {'username': []}, {'username': 'x', 'password': {}}])
def test_malformed_login(client, payload):
    assert client.post('/auth/login', json=payload).status_code in (400, 401)


def test_dashboard_has_no_shared_secret(client):
    response = client.get('/')
    assert response.status_code == 200
    assert b'API_KEY' not in response.data
    assert "script-src 'self'" in response.headers['Content-Security-Policy']
    assert client.get('/static/dashboard.js').status_code == 200
