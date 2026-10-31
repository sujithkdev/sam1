"""In-container inert deployment checks; no endpoint commands or live malware."""
import json
import os
import sqlite3
import urllib.request
from pathlib import Path

assert os.getuid() != 0, 'Server must run without root'
root = Path('/app/var/server')
assert root.is_dir()
try:
    Path('/app/phase2-unexpected-write').write_text('unexpected')
except OSError:
    pass
else:
    raise AssertionError('Application filesystem is writable')
for route in ('health', 'ready'):
    with urllib.request.urlopen('http://127.0.0.1:5000/' + route, timeout=5) as response:
        assert response.status == 200
        json.load(response)
with sqlite3.connect(root / 'edr.db') as conn:
    assert conn.execute('PRAGMA integrity_check').fetchone()[0] == 'ok'
marker = root / 'phase2-persistence-marker'
existed = marker.exists()
if not existed:
    marker.write_text('inert Phase 2 deployment marker')
print(json.dumps({'non_root': True, 'read_only_app': True, 'health': True,
                  'ready': True, 'database_integrity': True, 'marker_survived': existed}))
