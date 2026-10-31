"""Clean-environment package smoke test; temporary state only, no live collectors."""
import json
import os
from pathlib import Path
import secrets
import sys
import tempfile

root = Path(__file__).resolve().parents[1]
package = Path(sys.argv[1]).resolve() if len(sys.argv)>1 else root/'dist/behedr-r0-2026-10-24/server'
state = tempfile.TemporaryDirectory(prefix='r0-smoke-',dir=root/'var')
os.environ.update(EDR_ENV='test', EDR_BACKGROUND='false', EDR_JWT_SECRET=secrets.token_hex(32),
                  EDR_DATA_DIR=state.name)
sys.path.insert(0,str(package/'backend'))
from server import create_app
from server.auth import create_user
app=create_app()
client=app.test_client()
password=secrets.token_urlsafe(32)
assert create_user('r0-smoke',password,'admin')
assert client.get('/health').status_code==200
assert client.get('/ready').status_code==200
assert client.get('/api/console/summary').status_code==401
login=client.post('/auth/login',json={'username':'r0-smoke','password':password})
assert login.status_code==200
for route in ('/api/console/summary','/api/console/alerts','/api/console/endpoints','/api/console/rules','/api/operations'):
    assert client.get(route).status_code==200, route
assert client.get('/').status_code==200
assert client.get('/static/dashboard.js').status_code==200
assert client.post('/auth/logout',json={},headers={'X-CSRF-Token':login.json['csrf']}).status_code==200
assert client.get('/api/console/summary').status_code==401
print(json.dumps({'result':'passed','scope':'Fresh server dependencies; isolated packaged app creation, auth, console APIs, assets and logout. Background worker disabled; no live collector or network qualification.'}))

from server.database import storage
storage._local.conn.close()
storage._local.conn=None
state.cleanup()
