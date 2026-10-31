"""Bounded real SQLite failures and abrupt process exit; never fill the host disk."""
import os
from pathlib import Path
import sqlite3
import subprocess
import sys


def run(code, directory):
    return subprocess.run([sys.executable, '-c', code], capture_output=True, text=True, timeout=60,
                          env={**os.environ, 'PYTHONPATH': str(Path(__file__).resolve().parents[1]/'backend'),
                               'EDR_DATA_DIR': str(directory), 'EDR_BACKGROUND': 'false', 'EDR_MIN_FREE_BYTES': '0'})


def test_sqlite_full_rejects_entire_batch(tmp_path):
    result = run("""from server import create_app
from server.ingestion import accept
from server.database.storage import _conn
import sqlite3
create_app()
c=_conn()
pages=c.execute('PRAGMA page_count').fetchone()[0]
c.execute('PRAGMA max_page_count='+str(pages+8))
events=[dict(system_id='fault',event_id=f'fault-{i:032}',event='file_event',file_path='x'*60000) for i in range(10)]
try:
    accept(events)
except sqlite3.OperationalError as exc:
    assert exc.sqlite_errorcode == sqlite3.SQLITE_FULL, exc
else:
    raise AssertionError('Expected SQLITE_FULL')
assert c.execute('SELECT COUNT(*) FROM telemetry').fetchone()[0]==0
assert c.execute('PRAGMA integrity_check').fetchone()[0]=='ok'
print('SQLITE_FULL_ROLLBACK_OK')
""", tmp_path)
    assert result.returncode == 0, result.stderr
    assert 'SQLITE_FULL_ROLLBACK_OK' in result.stdout


def test_abrupt_exit_during_retention_rolls_back(tmp_path):
    result = run("""import os,time
from server import create_app
from server.ingestion import accept,process_one
from server.retention import maintain
from server.database.storage import _conn
create_app()
accept([dict(system_id='crash',event_id='crash-0000000000000000',event='file_event',time=1)])
assert process_one()
c=_conn()
c.execute('UPDATE telemetry SET received=?',(time.time()-40*86400,))
c.create_function('crash_now',0,lambda: os._exit(42))
c.execute('CREATE TEMP TRIGGER crash_retention BEFORE DELETE ON telemetry BEGIN SELECT crash_now(); END')
maintain(30,1,os.path.join(os.environ['EDR_DATA_DIR'],'before.db'))
""", tmp_path)
    assert result.returncode == 42, result.stderr
    with sqlite3.connect(tmp_path/'edr.db') as c:
        assert c.execute('PRAGMA integrity_check').fetchone()[0] == 'ok'
        assert c.execute('SELECT COUNT(*) FROM telemetry').fetchone()[0] == 1
        assert c.execute('SELECT COUNT(*) FROM recovery_checkpoint').fetchone()[0] == 0
        assert c.execute('SELECT COUNT(*) FROM telemetry_tombstones').fetchone()[0] == 0
    restored = run("""from server import create_app
from server.core.recovery import STATE
app=create_app()
assert app.test_client().get('/ready').status_code==200
assert STATE['replayed']==1
""", tmp_path)
    assert restored.returncode == 0, restored.stderr
